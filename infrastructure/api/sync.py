"""LEGACY — SQLite sync pipeline (used by CLI only).
Deprecated: use infrastructure.sync.pg_sync_engine for PostgreSQL."""
import asyncio
import logging
from datetime import UTC, datetime

from infrastructure.database.init_db import init_database
from infrastructure.database.sync_connection import SyncConnection

from . import config
from .client import MessageBirdClient
from .config import (
    DEFAULT_SOFTWARE,
    PHRASE_TICKET_HEADER,
    SOFTWARE_NAMES,
)

logger = logging.getLogger("m_bird.sync")


def month_bounds_utc(year: int, month: int) -> tuple[datetime, datetime]:
    """Return the inclusive start and exclusive end for a UTC calendar month."""
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")

    start = datetime(year, month, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC) if month == 12 else datetime(year, month + 1, 1, tzinfo=UTC)
    return start, end


def to_bird_iso(value: datetime) -> str:
    """Format UTC datetimes the way the MessageBird API expects."""
    return value.isoformat().replace("+00:00", "Z")


class SyncManager:
    def __init__(self):
        self.client = MessageBirdClient()
        self._agent_cache = {}
        self._contact_cache = {}

    async def initialize(self, conn, db_path: str):
        """Ensure DB is initialized and seed known agents."""
        await init_database(db_path)
        await self.seed_known_agents(conn)
        await self._load_caches(conn)

    def _print_progress(self, current, total, description, start_time):
        """Draw an ASCII progress bar with ETA."""
        import time

        elapsed = time.time() - start_time
        # Use a minimum rate to avoid division by zero or negative ETA
        remaining = max(0, total - current)
        if current > 0 and elapsed > 0:
            rate = current / elapsed
            remaining_seconds = remaining / rate
        else:
            remaining_seconds = 0

        eta_str = time.strftime("%H:%M:%S", time.gmtime(remaining_seconds))
        percent = min(100.0, (current / total) * 100) if total > 0 else 0
        bar_length = 30
        filled_length = int(bar_length * current // total) if total > 0 else 0
        filled_length = min(bar_length, filled_length)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)

        # Clear line and overwrite using ANSI escape code \033[K
        output = f"\r\033[K{description}: [{bar}] {percent:.1f}% ({current}/{total}) ETA: {eta_str}"
        print(output, end="", flush=True)

    async def _load_caches(self, conn):
        """Load agents and contacts into memory to avoid per-row SELECTs."""
        logger.info("Loading caches...")

        # Load Agents
        rows = await conn.fetch_all("SELECT agnt_id, agnt_bird FROM agents")
        self._agent_cache = {r["agnt_bird"]: r["agnt_id"] for r in rows}

        # Load Contacts
        # Only cache map of bird_id -> internal_id for resolution
        rows = await conn.fetch_all("SELECT cnts_id, cnts_bird FROM contacts")
        self._contact_cache = {r["cnts_bird"]: r["cnts_id"] for r in rows}

        logger.info(
            f"Caches loaded: {len(self._agent_cache)} agents, {len(self._contact_cache)} contacts"
        )

    async def seed_known_agents(self, conn):
        """Pre-seed known agents from configuration."""
        known_agents = config.get_known_agents()
        if not known_agents:
            return

        logger.info(f"Seeding {len(known_agents)} known agents...")
        agents_data = []
        for bird_id, name in known_agents.items():
            # Proteger contra espaços em branco
            agents_data.append((name.strip() if name else name, bird_id))

        await conn.execute_many(
            """
            INSERT INTO agents (agnt_name, agnt_bird)
            VALUES (?, ?)
            ON CONFLICT(agnt_bird) DO UPDATE SET
                agnt_name = excluded.agnt_name,
                agnt_updated = CURRENT_TIMESTAMP
            """,
            agents_data,
        )

    async def get_last_sync_time(self, conn, resource):
        """Get the last sync timestamp and cursor/offset for a resource."""
        row = await conn.fetch_one(
            "SELECT sync_created, sync_cursor, sync_offset FROM sync WHERE sync_resource = ? ORDER BY sync_id DESC LIMIT 1",
            (resource,),
        )
        if row:
            cursor = row.get("sync_cursor", None)
            offset = row.get("sync_offset", 0)
            return row["sync_created"], cursor, offset
        return None, None, 0

    async def save_sync_progress(self, conn, resource, cursor=None, offset=0):
        """Persist the current pagination cursor/offset so sync can be resumed."""
        await conn.execute_query(
            """
            INSERT INTO sync (sync_resource, sync_cursor, sync_offset)
            VALUES (?, ?, ?)
            """,
            (resource, cursor, offset),
        )

    async def update_sync_state(self, conn, resource, duration=None, records_count=None, cursor=None, offset=0):
        """Update last sync timestamp and stats."""
        await conn.execute_query(
            "INSERT INTO sync (sync_resource, sync_duration, sync_records_count, sync_cursor, sync_offset) VALUES (?, ?, ?, ?, ?)",
            (resource, duration, records_count, cursor, offset),
        )

    async def log_sync_error(self, conn, resource, error_msg, code=None, context=None):
        """Log a synchronization error to the database."""
        import json
        context_json = json.dumps(context) if context else None
        await conn.execute_query(
            """
            INSERT INTO sync_errors (err_resource, err_code, err_message, err_context)
            VALUES (?, ?, ?, ?)
            """,
            (resource, str(code) if code else None, error_msg, context_json),
        )
        logger.error(f"Sync error logged for {resource}: {error_msg}")

    async def get_or_create_contact(self, conn, bird_id, name, phone):
        """Get internal ID for contact, creating if needed (using cache)."""
        if bird_id in self._contact_cache:
            return self._contact_cache[bird_id]

        # Create new (or ignore if already exists)
        # Tratar None e strings inválidas
        safe_name = name if name and str(name).strip() else None
        await conn.execute_query(
            """
            INSERT OR IGNORE INTO contacts (cnts_bird, cnts_name, cnts_phone)
            VALUES (?, ?, ?)
            """,
            (bird_id, safe_name, phone),
        )

        # Fetch back ID (SQLite autoincrement)
        row = await conn.fetch_one(
            "SELECT cnts_id FROM contacts WHERE cnts_bird = ?", (bird_id,)
        )
        if row:
            new_id = row["cnts_id"]
            self._contact_cache[bird_id] = new_id
            return new_id
        return None

    async def get_or_create_agent(self, conn, bird_id, name):
        """Get internal ID for agent, creating if needed (using cache)."""
        if bird_id in self._agent_cache:
            return self._agent_cache[bird_id]

        # Proteger contra espaços em branco
        name = name.strip() if name else name

        await conn.execute_query(
            """
            INSERT OR IGNORE INTO agents (agnt_bird, agnt_name)
            VALUES (?, ?)
            """,
            (bird_id, name),
        )

        row = await conn.fetch_one(
            "SELECT agnt_id FROM agents WHERE agnt_bird = ?", (bird_id,)
        )
        if row:
            new_id = row["agnt_id"]
            self._agent_cache[bird_id] = new_id
            return new_id
        return None

    async def sync_contacts(self, conn):
        """Fetch and store contacts using batch transactions."""
        print("🔍 Buscando contatos...", end="", flush=True)
        logger.info("Starting contacts sync...")
        offset = 0
        limit = 20
        processed_count = 0
        expected_total = 0
        import time

        start_time = time.time()

        while True:
            response = await self.client.list_contacts(limit=limit, offset=offset)
            if "error" in response:
                await self.log_sync_error(
                    conn, "contacts", response["error"], context={"offset": offset}
                )
                break

            items = response.get("items", [])
            if not items:
                break

            # Progress handling
            if expected_total == 0:
                expected_total = response.get("pagination", {}).get("totalCount", 0)

            if expected_total > 0:
                self._print_progress(
                    offset + len(items), expected_total, "Syncing Contacts", start_time
                )

            contacts_data = []
            for c in items:
                phone = c.get("phone") or str(c.get("msisdn", ""))
                # Proteger contra "None" string
                if phone in ("None", "null", ""):
                    phone = None
                contact_name = c.get("displayName") or None
                # Tratar "None" string e nomes vazios
                if contact_name and str(contact_name).strip().lower() in ("none", "null", ""):
                    contact_name = None
                contacts_data.append(
                    (
                        contact_name,
                        phone,
                        c.get("id"),
                        c.get("createdAt"),
                        c.get("updatedAt"),
                    )
                )

            if contacts_data:
                async with conn.transaction():
                    await conn.execute_many(
                        """
                        INSERT INTO contacts (
                            cnts_name, cnts_phone, cnts_bird, cnts_created, cnts_updated
                        )
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(cnts_bird) DO UPDATE SET
                            cnts_name = excluded.cnts_name,
                            cnts_phone = excluded.cnts_phone,
                            cnts_updated = excluded.cnts_updated
                        """,
                        contacts_data,
                    )
                processed_count += len(contacts_data)

                # Update cache for new contacts
                bird_ids = [c[2] for c in contacts_data]
                if bird_ids:
                    placeholders = ",".join("?" * len(bird_ids))
                    rows = await conn.fetch_all(
                        f"SELECT cnts_id, cnts_bird FROM contacts WHERE cnts_bird IN ({placeholders})",
                        tuple(bird_ids),
                    )
                    for row in rows:
                        self._contact_cache[row["cnts_bird"]] = row["cnts_id"]

            if len(items) < limit:
                break
            offset += len(items)

        await self.update_sync_state(conn, "contacts")
        print()  # Newline after progress bar
        logger.info(f"Contacts sync completed. Total: {processed_count}")

    async def sync_conversations(
        self,
        conn,
        lookback_minutes=60,
        full_sync=False,
        min_date=None,
        max_date=None,
    ):
        """Sync conversation metadata only (no messages).

        `min_date` is inclusive and `max_date` is exclusive when provided.
        """
        logger.info(
            "Starting conversations sync "
            f"(full={full_sync}, min_date={min_date}, max_date={max_date})..."
        )

        last_sync, resume_cursor, resume_offset = await self.get_last_sync_time(conn, "conversations")
        if not last_sync:
            full_sync = True

        if not full_sync and min_date is None and lookback_minutes:
            from datetime import datetime, timedelta

            cutoff = datetime.now(UTC) - timedelta(minutes=lookback_minutes)
            min_date = cutoff.isoformat().replace("+00:00", "Z")
            logger.info(f"  Syncing conversations updated after {min_date}")

        print("🔍 Buscando conversas...", end="", flush=True)
        count = 0
        limit = 20

        import time

        start_time = time.time()
        total_convs = 0  # Will be fetched from pagination

        # Use last-seen conversation to know where to stop
        last_bird_id = None
        if not full_sync and max_date is None:
            last_row = await conn.fetch_one(
                "SELECT cnvs_bird FROM conversations ORDER BY cnvs_id DESC LIMIT 1"
            )
            if last_row:
                last_bird_id = last_row["cnvs_bird"]
                logger.info(
                    f"  Will stop sync if existing conversation is found: {last_bird_id}"
                )

        for status in ["active", "archived"]:
            # Resume from last saved cursor/offset if doing a full sync restart
            offset = resume_offset if (full_sync and status == "active") else 0
            page_token = resume_cursor if (full_sync and status == "active") else None
            total_convs = 0  # Reset for each status group

            while True:
                response = await self.client.list_conversations(
                    limit=limit, offset=offset, status=status, page_token=page_token
                )
                if "error" in response:
                    await self.log_sync_error(
                        conn, f"conversations_{status}", response["error"], context={"offset": offset}
                    )
                    break

                items = response.get("items", [])
                if not items:
                    break

                # Get total count
                pagination = response.get("pagination", {})
                if total_convs == 0:
                    total_convs = pagination.get("totalCount", 0)

                # Support for next page token if API uses it
                next_page_token = pagination.get("nextPageToken")

                stop_sync = False
                batch_data = []
                contacts_to_resolve = {}

                # Pre-fetch existing status to detect changes
                bird_ids_in_batch = [c["id"] for c in items]
                placeholders = ",".join("?" * len(bird_ids_in_batch))
                existing_rows = await conn.fetch_all(
                    f"SELECT cnvs_id, cnvs_bird, cnvs_status, cnvs_agnt, cnvs_reopened_count FROM conversations WHERE cnvs_bird IN ({placeholders})",
                    tuple(bird_ids_in_batch)
                )
                existing_map = {r["cnvs_bird"]: {"id": r["cnvs_id"], "status": r["cnvs_status"], "agnt": r["cnvs_agnt"], "reopened": r["cnvs_reopened_count"]} for r in existing_rows}

                # 1. Prepare data and identify missing contacts
                for c in items:
                    bird_id = c.get("id")
                    updated_at_str = c.get("updatedDatetime")

                    # USER REQUEST: Optimization - stop if we hit the last synced bird_id
                    if not full_sync and last_bird_id and bird_id == last_bird_id:
                        logger.info(
                            f"Reached last synced conversation {bird_id}. Stopping scan."
                        )
                        stop_sync = True
                        break

                    if max_date and updated_at_str and updated_at_str >= max_date:
                        continue

                    if min_date and updated_at_str and updated_at_str < min_date:
                        logger.info(
                            f"Stopping sync at {updated_at_str} (min_date={min_date})"
                        )
                        stop_sync = True
                        break

                    # Resolve Contact FK
                    c_id = c["contactId"]
                    if c_id not in self._contact_cache:
                        contact_data = c.get("contact", {})
                        contact_name = contact_data.get("displayName") or None
                        # Tratar "None" string e nomes vazios
                        if contact_name and str(contact_name).strip().lower() in ("none", "null", ""):
                            contact_name = None
                        contacts_to_resolve[c_id] = (
                            contact_name,
                            str(contact_data.get("msisdn", "")),
                        )

                # 2. Batch create new contacts
                if contacts_to_resolve:
                    async with conn.transaction():
                        new_contacts_data = []
                        for bid, (name, phone) in contacts_to_resolve.items():
                            new_contacts_data.append((bid, name, phone))

                        if new_contacts_data:
                            # Use INSERT OR IGNORE to avoid race conditions if needed, though simple here
                            await conn.execute_many(
                                """
                                INSERT OR IGNORE INTO contacts (cnts_bird, cnts_name, cnts_phone)
                                VALUES (?, ?, ?)
                                """,
                                new_contacts_data,
                            )

                    # Update cache
                    bids = list(contacts_to_resolve.keys())
                    if bids:
                        placeholders = ",".join("?" * len(bids))
                        rows = await conn.fetch_all(
                            f"SELECT cnts_id, cnts_bird FROM contacts WHERE cnts_bird IN ({placeholders})",
                            tuple(bids),
                        )
                        for r in rows:
                            self._contact_cache[r["cnts_bird"]] = r["cnts_id"]

                # 3. Process conversations
                for c in items:
                    updated_at_str = c.get("updatedDatetime")
                    if max_date and updated_at_str and updated_at_str >= max_date:
                        continue
                    if stop_sync and updated_at_str and updated_at_str < min_date:
                        break  # Duplicate check, ensuring we don't add

                    cnts_id = self._contact_cache.get(c["contactId"])

                    cnvs_bird = c["id"]
                    cnvs_msgcount = c.get("messages", {}).get("totalCount", 0)
                    cnvs_status = c.get("status")
                    cnvs_channel = c.get("lastUsedChannelId")
                    cnvs_created = c.get("createdDatetime")
                    cnvs_updated = c.get("updatedDatetime")
                    cnvs_last = c.get("lastReceivedDatetime")

                    # Detect lifecycle events
                    old_data = existing_map.get(cnvs_bird)
                    reopened_increment = 0

                    # Resolve new agent from API response
                    assigned = c.get("assignedTo") or {}
                    new_agnt_bird = assigned.get("id") if isinstance(assigned, dict) else None
                    new_agnt_id = self._agent_cache.get(new_agnt_bird) if new_agnt_bird else None

                    if old_data:
                        old_status = old_data["status"]
                        if old_status != cnvs_status:
                            event_type = None
                            if old_status == "archived" and cnvs_status == "active":
                                event_type = "reopened"
                                reopened_increment = 1
                            elif cnvs_status == "archived":
                                event_type = "archived"

                            if event_type:
                                # event_type is determined but not stored to keep DB as pure data provider
                                pass

                        # Detect agent transfer
                        old_agnt_id = old_data.get("agnt")
                        if new_agnt_id and old_agnt_id and new_agnt_id != old_agnt_id:
                            # Transfer detected but not stored to keep DB as pure data provider
                            pass
                    else:
                        # New conversation — event inserted after UPSERT below
                        pass

                    batch_data.append(
                        (
                            cnvs_msgcount,
                            cnts_id,
                            cnvs_status,
                            cnvs_channel,
                            cnvs_bird,
                            cnvs_created,
                            cnvs_updated,
                            cnvs_last,
                            reopened_increment
                        )
                    )

                if batch_data:
                    async with conn.transaction():
                        await conn.execute_many(
                            """
                            INSERT INTO conversations (
                                cnvs_msgcount, cnvs_cnts, cnvs_status, cnvs_channel,
                                cnvs_bird, cnvs_created, cnvs_updated, cnvs_last,
                                cnvs_reopened_count
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(cnvs_bird) DO UPDATE SET
                                cnvs_msgcount = excluded.cnvs_msgcount,
                                cnvs_status = excluded.cnvs_status,
                                cnvs_channel = excluded.cnvs_channel,
                                cnvs_updated = excluded.cnvs_updated,
                                cnvs_last = excluded.cnvs_last,
                                cnvs_reopened_count = conversations.cnvs_reopened_count + excluded.cnvs_reopened_count
                            """,
                            batch_data,
                        )

                        # Handle events for NEW conversations
                        for c_data in batch_data:
                            bird_id = c_data[4]
                            if bird_id not in existing_map:
                                # New conversation detected but 'opened' event not stored to keep DB as pure data provider
                                pass
                    count += len(batch_data)
                    if count % 100 == 0:
                        pass  # logger.info(f"  ...{count} conversations processed")

                    if total_convs > 0:
                        # Current progress within this status loop
                        # Not perfect for 'active + archived' combined total but better than nothing
                        current_batch_end = offset + len(items)
                        self._print_progress(
                            current_batch_end,
                            total_convs,
                            f"Syncing {status}",
                            start_time,
                        )

                # Handle pagination: Prefer pageToken if available, else offset
                if next_page_token:
                    page_token = next_page_token
                    offset += len(items)
                else:
                    if len(items) < limit or stop_sync:
                        break
                    offset += len(items)

                # Save resumable cursor after each page
                if full_sync and status == "active":
                    await self.save_sync_progress(conn, "conversations", cursor=page_token, offset=offset)

        duration = time.time() - start_time
        await self.update_sync_state(conn, "conversations", duration=duration, records_count=count, cursor=None, offset=0)
        print()  # Newline
        logger.info(f"Conversations sync completed. Total: {count}")

    async def sync_messages_for_month(self, conn, year: int, month: int) -> int:
        """Sync messages for conversations updated in a specific calendar month.

        MessageBird exposes `dateFrom` for messages. This mode backfills from the
        first instant of the requested month for conversations updated in that
        month, relying on UPSERTs to keep reruns safe.
        """
        month_start, next_month_start = month_bounds_utc(year, month)
        start_iso = to_bird_iso(month_start)
        end_iso = to_bird_iso(next_month_start)

        rows = await conn.fetch_all(
            """
            SELECT cnvs_bird FROM conversations
            WHERE cnvs_updated >= ? AND cnvs_updated < ?
            ORDER BY cnvs_updated DESC
            """,
            (start_iso, end_iso),
        )
        total = len(rows)
        logger.info(
            f"Syncing messages for {total} conversations updated in {year:04d}-{month:02d}..."
        )
        print(
            f"🔍 Buscando mensagens de {year:04d}-{month:02d}...",
            end="",
            flush=True,
        )

        semaphore = asyncio.Semaphore(10)

        async def fetch_with_limit(row):
            async with semaphore:
                try:
                    return await self.sync_messages(
                        conn, row["cnvs_bird"], date_from=start_iso
                    )
                except Exception as e:
                    logger.error(f"Error syncing {row['cnvs_bird']}: {e}")
                    return 0

        tasks = [fetch_with_limit(row) for row in rows]
        msg_count = 0
        chunk_size = 1000

        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i : i + chunk_size]
            results = await asyncio.gather(*chunk)
            msg_count += sum(results)
            logger.info(f"  ...processed {min(i + chunk_size, total)}/{total} convs")

        logger.info(
            "Monthly messages sync completed. "
            f"{total} conversations, {msg_count} messages from {year:04d}-{month:02d} onward."
        )
        return msg_count

    async def sync_messages(self, conn, conversation_bird_id, date_from=None) -> int:
        """Fetch messages for a conversation and extract agents using batch transactions."""
        # ... (rest of the code will be kept, just adding the trigger at the end)
        res = await self._sync_messages_internal(conn, conversation_bird_id, date_from)
        if res > 0:
            await self.update_conversation_surveys(conn, conversation_bird_id)
        return res

    async def _sync_messages_internal(self, conn, conversation_bird_id, date_from=None) -> int:
        # Renaming the original sync_messages to _internal
        # Get internal conversation ID
        cnvs_row = await conn.fetch_one(
            "SELECT cnvs_id FROM conversations WHERE cnvs_bird = ?",
            (conversation_bird_id,),
        )
        if not cnvs_row:
            logger.error(f"Conversation {conversation_bird_id} not found in DB")
            return 0

        cnvs_id = cnvs_row["cnvs_id"]

        # USER REQUEST: Auto-detect date_from if not provided
        if date_from is None:
            last_msg = await conn.fetch_one(
                "SELECT msgs_created FROM messages WHERE msgs_cnvs = ? ORDER BY msgs_created DESC LIMIT 1",
                (cnvs_id,),
            )
            if last_msg and last_msg["msgs_created"]:
                date_from = last_msg["msgs_created"]
                # Ensure it's in a format MessageBird likes (usually needs Z)
                if "+" in date_from:
                    date_from = date_from.split("+")[0] + "Z"
                elif not date_from.endswith("Z"):
                    date_from += "Z"
                # logger.debug(f"  Resuming sync from {date_from}")
        offset = 0
        limit = 20
        total_messages = 0

        while True:
            response = await self.client.get_messages(
                conversation_bird_id, limit=limit, offset=offset, date_from=date_from
            )

            if "error" in response:
                await self.log_sync_error(
                    conn, "messages", response["error"],
                    context={"cnvs_bird": conversation_bird_id, "offset": offset}
                )
                break

            items = response.get("items", [])
            if not items:
                break

            all_messages_data = []
            agents_to_resolve = {}  # bird_id -> name

            # 1. Prepare data and identify missing agents
            for m in items:
                direction = m.get("direction")
                content_obj = m.get("content")
                content_text = ""

                if isinstance(content_obj, dict):
                    content_text = content_obj.get("text", "") or content_obj.get(
                        "hsm", {}
                    ).get("elementName", "")
                else:
                    content_text = str(content_obj)

                # Extract Agent from Source if Outbound
                agnt_id = None
                if direction == "sent":
                    source = m.get("source", {})
                    agent = source.get("inboxAgent")
                    if agent and agent.get("id"):
                        agent_bid = agent["id"]
                        if agent_bid not in self._agent_cache:
                            agents_to_resolve[agent_bid] = (
                                agent.get("fullName")
                                or agent.get("firstName")
                                or "Unknown"
                            )

                # Check cache for existing agent
                # If newly resolved, will be in cache after step 2

                all_messages_data.append(
                    {
                        "data": m,
                        "content": content_text,
                        "direction": direction,
                        "status": m.get("status"),
                        "type": m.get("type"),
                        "id": m.get("id"),
                        "created": m.get("createdDatetime"),
                        "updated": m.get("updatedDatetime"),
                        "source": m.get("source", {}),
                    }
                )

            # 2. Batch create new agents
            if agents_to_resolve:
                # We can't really do batch "insert or ignore" easily with fetching IDs back in one go
                # for agents if they might exist but not be in cache (though cache initialization covers existing).
                # But parallel syncs might race.
                # Simplest is loop for resolution if map is small (usually 1 agent).
                for bid, name in agents_to_resolve.items():
                    await self.get_or_create_agent(conn, bid, name)

            # 3. Process messages
            batch_params = []
            last_agent_id = None

            for m_data in all_messages_data:
                direction = m_data["direction"]
                agnt_id = None

                if direction == "sent":
                    agent = m_data["source"].get("inboxAgent")
                    if agent and agent.get("id"):
                        agnt_id = self._agent_cache.get(agent["id"])
                        last_agent_id = agnt_id

                batch_params.append(
                    (
                        cnvs_id,
                        agnt_id,
                        direction,
                        m_data["status"],
                        m_data["type"],
                        m_data["content"],
                        m_data["id"],
                        m_data["created"],
                        m_data["updated"],
                    )
                )

            # Detect reopen: archived conversation receiving new messages

            if batch_params:
                async with conn.transaction():
                    await conn.execute_many(
                        """
                        INSERT INTO messages (
                            msgs_cnvs, msgs_agnt, msgs_direction, msgs_status, msgs_type,
                            msgs_content, msgs_bird, msgs_created, msgs_updated
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(msgs_bird) DO UPDATE SET
                            msgs_status = excluded.msgs_status,
                            msgs_updated = excluded.msgs_updated
                        """,
                        batch_params,
                    )

                    # Update cnvs_agnt logic - done per batch or per conversation?
                    # Probably better to do it once at the end of sync for this convo
                    # But here we do it per batch to be safe
                    if last_agent_id:
                        await conn.execute_query(
                            "UPDATE conversations SET cnvs_agnt = ? WHERE cnvs_id = ?",
                            (last_agent_id, cnvs_id),
                        )
                total_messages += len(batch_params)

            if len(items) < limit:
                break
            offset += len(items)

        return total_messages

    async def sync_all_messages(self, conn):
        """Sync messages for ALL conversations ensuring concurrency."""
        rows = await conn.fetch_all(
            "SELECT cnvs_bird, cnvs_msgcount FROM conversations ORDER BY cnvs_updated DESC"
        )
        total = len(rows)
        logger.info(f"Syncing messages for {total} conversations...")

        semaphore = asyncio.Semaphore(30)  # Increased concurrency to 30 (limit 500 RPS)
        import time

        start_time = time.time()
        self._print_progress(0, total, "Syncing Messages", start_time)

        async def fetch_with_limit(row):
            async with semaphore:
                try:
                    # SMART SKIP: Check if message count matches
                    bird_id = row["cnvs_bird"]
                    remote_count = row["cnvs_msgcount"]

                    # Check DB for actual count of messages we have
                    local_count_row = await conn.fetch_one(
                        """
                        SELECT COUNT(*) as count, MAX(msgs_created) as last_msg_date
                        FROM messages
                        WHERE msgs_cnvs = (SELECT cnvs_id FROM conversations WHERE cnvs_bird = ?)
                        """,
                        (bird_id,),
                    )

                    local_count = local_count_row["count"] if local_count_row else 0
                    last_msg_date = (
                        local_count_row["last_msg_date"] if local_count_row else None
                    )

                    # If counts match, skip entirely!
                    if (
                        remote_count is not None
                        and local_count == remote_count
                        and remote_count > 0
                    ):
                        return 0

                    # Delta Sync: If we have messages, pass dateFrom to only fetch new ones
                    date_from = None
                    if local_count > 0 and last_msg_date:
                        date_from = last_msg_date

                    return await self.sync_messages(conn, bird_id, date_from=date_from)
                except Exception as e:
                    logger.error(f"Error syncing messages for {row['cnvs_bird']}: {e}")
                    return 0

        tasks = [fetch_with_limit(row) for row in rows]
        # Process in chunks to avoid queuing too many tasks
        # But asyncio.gather with semaphore is fine for reasonably sized lists.
        # If total is huge (>10k), chunking tasks list is better.

        chunk_size = 1000
        msg_count = 0

        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i : i + chunk_size]
            results = await asyncio.gather(*chunk)
            msg_count += sum(results)

            processed = min(i + chunk_size, total)
            self._print_progress(processed, total, "Syncing Messages", start_time)

            # logger.info(
            #     f"  ...processed {min(i + chunk_size, total)}/{total} convs ({msg_count} msgs)"
            # )

        print()  # Newline
        logger.info(
            f"All messages sync completed. {total} conversations, {msg_count} messages."
        )

    async def sync_messages_for_recent(self, conn, days: int = 30):
        """Sync messages only for conversations updated in the last N days."""
        rows = await conn.fetch_all(
            """
            SELECT cnvs_bird FROM conversations
            WHERE cnvs_updated >= datetime('now', ?)
            ORDER BY cnvs_updated DESC
            """,
            (f"-{days} days",),
        )
        total = len(rows)
        logger.info(
            f"Syncing messages for {total} conversations updated in last {days} days..."
        )
        print(f"🔍 Buscando mensagens dos últimos {days} dias...", end="", flush=True)

        semaphore = asyncio.Semaphore(10)

        async def fetch_with_limit(row):
            async with semaphore:
                try:
                    return await self.sync_messages(conn, row["cnvs_bird"])
                except Exception as e:
                    logger.error(f"Error syncing {row['cnvs_bird']}: {e}")
                    return 0

        tasks = [fetch_with_limit(row) for row in rows]
        msg_count = 0
        chunk_size = 1000

        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i : i + chunk_size]
            results = await asyncio.gather(*chunk)
            msg_count += sum(results)
            logger.info(f"  ...processed {min(i + chunk_size, total)}/{total} convs")

        logger.info(
            f"Recent messages sync completed. {total} conversations, {msg_count} messages."
        )

    async def update_conversation_surveys(self, conn, conversation_bird_id: str):
        """Extract survey and screening data from conversation messages."""
        # Use existing logic from backfill but specialized for one conversation
        import re
        from datetime import datetime, timedelta

        from domain import constants

        cnvs_row = await conn.fetch_one(
            "SELECT cnvs_id, cnvs_status, cnvs_rating_agent, cnvs_rating_nps FROM conversations WHERE cnvs_bird = ?",
            (conversation_bird_id,),
        )
        if not cnvs_row: return
        cnvs_id = cnvs_row["cnvs_id"]
        cnvs_row["cnvs_status"]

        # Question patterns — order matters: more specific patterns first
        # rating_nps uses "Avalie nosso atendimento" (NOT "até 10" — bot uses 🔟 emoji, not text)
        QUESTIONS = {
            "lang": r"(?:Escolha|Selecione) seu idioma",
            "software": r"Qual seria o sistema",
            "tax_id": r"Informe por favor o CNPJ de sua empresa ou CPF",
            "dept": r"Selecione o departamento desejado",
            "contact_reason": r"Qual o motivo do contato",
            "occurrence": r"Qual seria a ocorrência",
            "rating_agent": r"como você avalia o atendimento do técnico",
            "rating_nps": r"Avalie.*(?:nosso atendimento|a nossa Empresa)",
        }

        messages = await conn.fetch_all(
            "SELECT msgs_id, msgs_content, msgs_direction, msgs_created FROM messages WHERE msgs_cnvs = ? ORDER BY msgs_created ASC",
            (cnvs_id,)
        )

        updates = {}
        for i, msg in enumerate(messages):
            content = msg["msgs_content"] or ""

            # Extract data from triagem summary (sent by bot)
            if msg["msgs_direction"] == "sent" and PHRASE_TICKET_HEADER in content:
                lines = [l.strip() for l in content.split("\n")]
                try:
                    idx = next(j for j, l in enumerate(lines) if PHRASE_TICKET_HEADER in l)
                    ticket_lines = [l for l in lines[idx + 1:] if l and not l.startswith("===")]
                    # ticket_lines format: [system, dept, contact_reason, description...]
                    if len(ticket_lines) >= 4:
                        if "cnvs_contact_reason" not in updates:
                            reason_text = ticket_lines[2]
                            for _dept_id, reasons in constants.REASON_MAP.items():
                                for reason_id, reason_label in reasons.items():
                                    if reason_label.lower() == reason_text.lower():
                                        updates["cnvs_contact_reason"] = int(reason_id)
                                        break
                        updates["cnvs_description"] = " ".join(ticket_lines[3:])
                    elif ticket_lines:
                        updates["cnvs_description"] = ticket_lines[-1]
                except StopIteration:
                    pass

            if msg["msgs_direction"] != "sent":
                continue

            matched_key = None
            for key, pattern in QUESTIONS.items():
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    matched_key = key
                    break

            if matched_key:
                timestamp = datetime.fromisoformat(msg["msgs_created"].replace("Z", "+00:00"))
                for j in range(i + 1, min(i + 10, len(messages))):
                    next_msg = messages[j]
                    if next_msg["msgs_direction"] != "received":
                        continue
                    next_ts = datetime.fromisoformat(next_msg["msgs_created"].replace("Z", "+00:00"))
                    if next_ts - timestamp > timedelta(minutes=60):
                        break
                    resp = (next_msg["msgs_content"] or "").strip()
                    if not resp:
                        continue  # skip empty messages, keep looking

                    found = False
                    if matched_key == "tax_id":
                        val = re.sub(r"\D", "", resp)
                        if val:
                            updates["cnvs_tax_id"] = val
                            found = True
                    elif matched_key == "software":
                        m = re.search(r"(\d+)", resp)
                        num = int(m.group(1)) if m else None
                        for name in SOFTWARE_NAMES:
                            if (num is not None and str(num) in resp) or name.upper() in resp.upper():
                                updates["cnvs_software"] = name
                                found = True
                                break
                        if not found:
                            updates["cnvs_software"] = DEFAULT_SOFTWARE
                            found = True
                    else:
                        m = re.search(r"(\d+)", resp)
                        num = int(m.group(1)) if m else None
                        if num is not None:
                            if matched_key == "lang" and 1 <= num <= 3:
                                updates["cnvs_lang"] = num; found = True
                            elif matched_key == "dept" and 1 <= num <= 5:
                                updates["cnvs_dept"] = num; found = True
                            elif matched_key == "contact_reason" and 1 <= num <= 6:
                                updates["cnvs_contact_reason"] = num; found = True
                            elif matched_key == "occurrence" and 1 <= num <= 6:
                                updates["cnvs_occurrence"] = num; found = True
                            elif matched_key == "rating_agent" and 1 <= num <= 5:
                                updates["cnvs_rating_agent"] = num; found = True
                            elif matched_key == "rating_nps" and 0 <= num <= 10:
                                updates["cnvs_rating_nps"] = num; found = True
                    if found:
                        break

        if updates:
            set_clause = ", ".join([f"{k} = ?" for k in updates])
            params = list(updates.values()) + [cnvs_id]
            await conn.execute_query(
                f"UPDATE conversations SET {set_clause} WHERE cnvs_id = ?",
                tuple(params)
            )

    async def full_sync(self, conn, db_path: str):
        """Full STRUCTURAL sync: contacts + conversations (no messages)."""
        await self.initialize(conn, db_path)
        await self.sync_contacts(conn)
        await self.sync_conversations(conn, full_sync=True)

    async def full_sync_with_messages(self, conn, db_path: str):
        """Full sync including ALL messages (heavy operation)."""
        await self.full_sync(conn, db_path)
        await self.sync_all_messages(conn)

    async def backfill_surveys(self, conn) -> int:
        """Re-extract NPS and rating survey data for all conversations that have survey questions
        but are missing captured values. Safe to run multiple times (idempotent)."""
        rows = await conn.fetch_all(
            """
            SELECT DISTINCT cv.cnvs_bird
            FROM conversations cv
            JOIN messages m ON m.msgs_cnvs = cv.cnvs_id
            WHERE m.msgs_direction = 'sent'
              AND (
                m.msgs_content LIKE '%Avalie%'
                OR m.msgs_content LIKE '%avalia o atendimento%'
                OR m.msgs_content LIKE '%Qual o motivo do contato%'
                OR m.msgs_content LIKE '%Selecione o departamento%'
              )
              AND (
                cv.cnvs_rating_nps IS NULL
                OR cv.cnvs_rating_agent IS NULL
                OR cv.cnvs_contact_reason IS NULL
                OR cv.cnvs_dept IS NULL
              )
            ORDER BY cv.cnvs_id
            """
        )
        total = len(rows)
        logger.info(f"Survey backfill: {total} conversations to process...")
        for i, row in enumerate(rows):
            await self.update_conversation_surveys(conn, row["cnvs_bird"])
            if (i + 1) % 200 == 0:
                logger.info(f"  ...{i + 1}/{total} conversations processed")
        logger.info(f"Survey backfill completed: {total} conversations processed.")
        return total


async def trigger_sync_tool(
    full_sync: bool = False,
    sync_messages: bool = False,
    messages_days: int | None = None,
    lookback_minutes: int = 60,
    year: int | None = None,
    month: int | None = None,
    backfill_surveys: bool = False,
    db_path: str = "m_bird.db",
) -> str:
    """
    Trigger a synchronization of data from MessageBird to the local database.

    Use backfill_surveys=True to re-extract NPS and agent ratings from existing
    conversation messages. Run this once if reports show N/A for agents that
    clearly received evaluations.
    """
    manager = SyncManager()  # Client created here, but connection managed via context

    async with SyncConnection(db_path=db_path) as conn:
        # Initialize (DB schemas, seed agents, load caches)
        await manager.initialize(conn, db_path)

        if backfill_surveys:
            count = await manager.backfill_surveys(conn)
            return f"Survey backfill concluído: {count} conversas processadas."

        if (year is None) != (month is None):
            raise ValueError("Use year and month together for monthly sync.")

        if year is not None and month is not None:
            month_start, next_month_start = month_bounds_utc(year, month)
            start_iso = to_bird_iso(month_start)
            end_iso = to_bird_iso(next_month_start)

            await manager.sync_conversations(
                conn,
                full_sync=False,
                min_date=start_iso,
                max_date=end_iso,
            )
            synced_messages = await manager.sync_messages_for_month(conn, year, month)
            return (
                "Monthly synchronization completed for "
                f"{year:04d}-{month:02d} ({synced_messages} messages processed)."
            )

        if full_sync and sync_messages:
            await manager.full_sync_with_messages(conn, db_path)
            return "Full synchronization with messages completed."
        elif full_sync:
            await manager.full_sync(conn, db_path)
            return "Full structural synchronization completed (no messages)."
        else:
            # OPTIMIZATION: Skip structural sync if done recently (last 60 mins)
            from datetime import timedelta

            async def should_skip(resource, minutes=60):
                last_time, _, _offset = await manager.get_last_sync_time(conn, resource)
                if not last_time:
                    return False
                # Conver last_time to datetime object if it's a string
                if isinstance(last_time, str):
                    try:
                        # SQLite might store as YYYY-MM-DD HH:MM:SS
                        last_dt = datetime.fromisoformat(last_time.replace(" ", "T"))
                        if last_dt.tzinfo is None:
                            last_dt = last_dt.replace(tzinfo=UTC)
                    except ValueError:
                        return False
                else:
                    last_dt = last_time

                return datetime.now(UTC) - last_dt < timedelta(minutes=minutes)

            # Sync contacts only if needed
            if await should_skip("contacts"):
                logger.info(
                    "Contacts synced recently, skipping structural contact check."
                )
            else:
                await manager.sync_contacts(conn)

            # Determine lookback based on messages_days if set
            effective_lookback = lookback_minutes
            if messages_days is not None:
                required = messages_days * 24 * 60
                if effective_lookback < required:
                    effective_lookback = required

            # Sync conversations only if needed
            if await should_skip("conversations"):
                logger.info(
                    "Conversation list synced recently, skipping structural check."
                )
            else:
                await manager.sync_conversations(
                    conn, lookback_minutes=effective_lookback
                )

            if messages_days is not None:
                await manager.sync_messages_for_recent(conn, days=messages_days)
                return f"Incremental sync completed with messages for last {messages_days} days."

            return "Incremental synchronization completed (no messages)."


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Trigger sync process.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full structural sync: contacts + all conversations (no messages)",
    )
    parser.add_argument(
        "--full-messages",
        action="store_true",
        help="Full sync including ALL messages (heavy operation)",
    )
    parser.add_argument(
        "--messages-days",
        type=int,
        default=None,
        help="Sync messages for conversations updated in last N days",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=60,
        help="Lookback minutes for incremental sync (default: 60)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        help="Calendar year for a monthly backfill (use with --month)",
    )
    parser.add_argument(
        "--month",
        type=int,
        default=None,
        help="Calendar month for a monthly backfill, 1-12 (use with --year)",
    )

    args = parser.parse_args()

    # --full-messages implies --full
    is_full = args.full or args.full_messages

    result = asyncio.run(
        trigger_sync_tool(
            full_sync=is_full,
            sync_messages=args.full_messages,
            messages_days=args.messages_days,
            lookback_minutes=args.lookback,
            year=args.year,
            month=args.month,
        )
    )
    print(result)
