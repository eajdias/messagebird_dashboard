"""PostgreSQL sync engine (asyncpg).

Replaces the legacy SQLite sync pipeline (infrastructure.api.sync).
The structure mirrors SyncManager but uses asyncpg-compatible SQL ($N params).

API methods called by trigger_sync_pg delegate to the MessageBirdClient
and persist data via PostgresSyncConnection.
"""

import asyncio
import json
import logging
import re
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from infrastructure.api import config
from infrastructure.api.client import MessageBirdClient
from infrastructure.database.sync_connection_pg import PostgresSyncConnection

logger = logging.getLogger("m_bird.sync_pg")


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


def _parse_dt(value: str | datetime | None) -> datetime | None:
    """Convert an ISO datetime string (with 'Z' suffix) to a naive UTC datetime.

    The DB columns use ``TIMESTAMP`` (without timezone), so we strip tzinfo
    after parsing to avoid ``offset-naive vs offset-aware`` errors in asyncpg.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    s = str(value).strip()
    if not s:
        return None
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    return dt.replace(tzinfo=None)


class PgSyncManager:
    def __init__(self):
        self.client = MessageBirdClient()
        self._agent_cache: dict[str, int] = {}
        self._contact_cache: dict[str, int] = {}

    # ── Cache & Seed ──────────────────────────────────────────────

    async def _load_caches(self, conn: PostgresSyncConnection):
        """Load agents and contacts into memory to avoid per-row SELECTs."""
        rows = await conn.fetch_all("SELECT agnt_id, agnt_bird FROM agents")
        self._agent_cache = {r["agnt_bird"]: r["agnt_id"] for r in rows}
        rows = await conn.fetch_all("SELECT cnts_id, cnts_bird FROM contacts")
        self._contact_cache = {r["cnts_bird"]: r["cnts_id"] for r in rows}
        logger.info(f"Caches loaded: {len(self._agent_cache)} agents, {len(self._contact_cache)} contacts")

    async def seed_known_agents(self, conn: PostgresSyncConnection):
        """Pre-seed known agents from configuration."""
        known_agents = config.get_known_agents()
        if not known_agents:
            return
        agents_data = [(name.strip() if name else name, bird_id) for bird_id, name in known_agents.items()]
        await conn.execute_many(
            "INSERT INTO agents (agnt_name, agnt_bird) VALUES ($1, $2) "
            "ON CONFLICT (agnt_bird) DO UPDATE SET agnt_name = EXCLUDED.agnt_name, agnt_updated = NOW()",
            agents_data,
        )

    # ── Entity Resolution ─────────────────────────────────────────

    async def get_or_create_contact(
        self, conn: PostgresSyncConnection, bird_id: str, name: str, phone: str
    ) -> int | None:
        if bird_id in self._contact_cache:
            return self._contact_cache[bird_id]
        safe_name = name if name and str(name).strip() else None
        await conn.execute_query(
            "INSERT INTO contacts (cnts_bird, cnts_name, cnts_phone) VALUES ($1, $2, $3) "
            "ON CONFLICT (cnts_bird) DO NOTHING",
            (bird_id, safe_name, phone),
        )
        row = await conn.fetch_one("SELECT cnts_id FROM contacts WHERE cnts_bird = $1", (bird_id,))
        if row:
            self._contact_cache[bird_id] = row["cnts_id"]
            return row["cnts_id"]
        return None

    async def get_or_create_agent(self, conn: PostgresSyncConnection, bird_id: str, name: str) -> int | None:
        if bird_id in self._agent_cache:
            return self._agent_cache[bird_id]
        name = name.strip() if name else name
        await conn.execute_query(
            "INSERT INTO agents (agnt_bird, agnt_name) VALUES ($1, $2) ON CONFLICT (agnt_bird) DO NOTHING",
            (bird_id, name),
        )
        row = await conn.fetch_one("SELECT agnt_id FROM agents WHERE agnt_bird = $1", (bird_id,))
        if row:
            self._agent_cache[bird_id] = row["agnt_id"]
            return row["agnt_id"]
        return None

    # ── Sync State Persistence ────────────────────────────────────

    async def get_last_sync_time(self, conn: PostgresSyncConnection, resource: str):
        row = await conn.fetch_one(
            "SELECT sync_created, sync_cursor, sync_offset "
            "FROM sync WHERE sync_resource = $1 ORDER BY sync_id DESC LIMIT 1",
            (resource,),
        )
        if row:
            return row["sync_created"], row["sync_cursor"], row["sync_offset"] or 0
        return None, None, 0

    async def save_sync_progress(self, conn: PostgresSyncConnection, resource: str, cursor=None, offset=0):
        await conn.execute_query(
            "INSERT INTO sync (sync_resource, sync_cursor, sync_offset) VALUES ($1, $2, $3)",
            (resource, cursor, offset),
        )

    async def update_sync_state(
        self, conn: PostgresSyncConnection, resource: str, duration=None, records_count=None, cursor=None, offset=0
    ):
        await conn.execute_query(
            "INSERT INTO sync "
            "(sync_resource, sync_duration, sync_records_count, sync_cursor, sync_offset) "
            "VALUES ($1, $2, $3, $4, $5)",
            (resource, duration, records_count, cursor, offset),
        )

    async def log_sync_error(
        self, conn: PostgresSyncConnection, resource: str, error_msg: str, code=None, context=None
    ):
        context_json = json.dumps(context) if context else None
        await conn.execute_query(
            "INSERT INTO sync_errors (err_resource, err_code, err_message, err_context) VALUES ($1, $2, $3, $4)",
            (resource, str(code) if code else None, error_msg, context_json),
        )
        logger.error(f"Sync error logged for {resource}: {error_msg}")

    # ── Contacts Sync ─────────────────────────────────────────────

    async def sync_contacts(self, conn: PostgresSyncConnection):
        logger.info("Starting contacts sync...")
        offset = 0
        limit = 20
        processed_count = 0
        while True:
            response = await self.client.list_contacts(limit=limit, offset=offset)
            if "error" in response:
                await self.log_sync_error(conn, "contacts", str(response["error"]), context={"offset": offset})
                break
            items: list[dict[str, Any]] = response.get("items", [])  # type: ignore[assignment]
            if not items:
                break
            contacts_data = []
            for c in items:
                phone = c.get("phone") or str(c.get("msisdn", ""))
                if phone in ("None", "null", ""):
                    phone = None
                contact_name = c.get("displayName") or None
                if contact_name and str(contact_name).strip().lower() in ("none", "null", ""):
                    contact_name = None
                contacts_data.append(
                    (contact_name, phone, c.get("id"), _parse_dt(c.get("createdAt")), _parse_dt(c.get("updatedAt")))
                )
            if contacts_data:
                async with conn.transaction():
                    await conn.execute_many(
                        "INSERT INTO contacts (cnts_name, cnts_phone, cnts_bird, cnts_created, cnts_updated) "
                        "VALUES ($1, $2, $3, $4, $5) "
                        "ON CONFLICT (cnts_bird) DO UPDATE SET cnts_name = EXCLUDED.cnts_name, "
                        "cnts_phone = EXCLUDED.cnts_phone, cnts_updated = EXCLUDED.cnts_updated",
                        contacts_data,
                    )
                processed_count += len(contacts_data)
                bird_ids = [c[2] for c in contacts_data]
                if bird_ids:
                    rows = await conn.fetch_all(
                        "SELECT cnts_id, cnts_bird FROM contacts WHERE cnts_bird = ANY($1::varchar[])", (bird_ids,)
                    )
                    for row in rows:
                        self._contact_cache[row["cnts_bird"]] = row["cnts_id"]
            if len(items) < limit:
                break
            offset += len(items)
        await self.update_sync_state(conn, "contacts")
        logger.info(f"Contacts sync completed. Total: {processed_count}")

    # ── Conversations Sync ────────────────────────────────────────

    async def sync_conversations(
        self,
        conn: PostgresSyncConnection,
        lookback_minutes=60,
        full_sync=False,
        min_date=None,
        max_date=None,
    ):
        """Sync conversation metadata with reopen detection.

        The Bird Conversations API does NOT support date-filter query params
        (updatedDatetimeAfter is silently ignored).  We use ``reverse=true``
        to get conversations newest-first and filter client-side, stopping
        early once we hit a conversation older than the cutoff window.
        """
        logger.info(f"Starting conversations sync (full={full_sync}, min_date={min_date}, max_date={max_date})...")
        last_sync, resume_cursor, resume_offset = await self.get_last_sync_time(conn, "conversations")

        cutoff_dt: datetime | None = None
        if not full_sync and min_date is None and lookback_minutes:
            cutoff_dt = (datetime.now(UTC) - timedelta(minutes=lookback_minutes)).replace(tzinfo=None)
            min_date = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            logger.info(f"  Incremental: will stop at conversations older than {min_date}")
        elif min_date:
            cutoff_dt = _parse_dt(min_date)

        page_token = resume_cursor if full_sync else None
        offset = resume_offset or 0 if full_sync else 0
        limit = 20
        count = 0
        start_time = time.time()

        for status in ["active", "archived"]:
            if full_sync:
                offset = resume_offset if status == "active" else 0
                page_token = resume_cursor if status == "active" else None
            else:
                offset = 0
                page_token = None

            while True:
                conv_params: dict[str, Any] = {"limit": limit, "status": status, "reverse": not full_sync}
                if page_token:
                    conv_params["page_token"] = str(page_token)
                elif offset:
                    conv_params["offset"] = offset
                if max_date:
                    conv_params["createdDatetimeBefore"] = max_date

                response = await self.client.list_conversations(**conv_params)
                if "error" in response:
                    error_msg = response["error"]
                    await self.log_sync_error(conn, f"conversations_{status}", str(error_msg), context=conv_params)
                    break

                items: list[Any] = list(response.get("data", response.get("items", [])))
                if not items:
                    break

                pagination: dict[str, Any] = response.get("pagination", {})
                next_page_token = pagination.get("nextPageToken") or response.get("nextPageToken")
                page_token = str(next_page_token) if next_page_token else None
                offset += len(items)

                should_stop = False
                batch_data = []

                bird_ids_in_batch = [str(c["id"]) for c in items]
                existing_rows = await conn.fetch_all(
                    "SELECT cnvs_id, cnvs_bird, cnvs_status, cnvs_agnt, cnvs_reopened_count "
                    "FROM conversations WHERE cnvs_bird = ANY($1::varchar[])",
                    (bird_ids_in_batch,),
                )
                existing_map = {
                    r["cnvs_bird"]: {
                        "id": r["cnvs_id"],
                        "status": r["cnvs_status"],
                        "agnt": r["cnvs_agnt"],
                        "reopened": r["cnvs_reopened_count"],
                    }
                    for r in existing_rows
                }

                contacts_to_resolve: dict[str, tuple[str | None, str]] = {}
                for c in items:
                    c_id = c.get("contactId")
                    if c_id and c_id not in self._contact_cache:
                        contact_data = c.get("contact", {})
                        contact_name = contact_data.get("displayName") or None
                        if contact_name and str(contact_name).strip().lower() in ("none", "null", ""):
                            contact_name = None
                        contacts_to_resolve[c_id] = (
                            contact_name,
                            str(contact_data.get("msisdn", "")),
                        )

                if contacts_to_resolve:
                    new_contacts_data = [(bid, name, phone) for bid, (name, phone) in contacts_to_resolve.items()]
                    async with conn.transaction():
                        await conn.execute_many(
                            "INSERT INTO contacts (cnts_bird, cnts_name, cnts_phone) VALUES ($1, $2, $3) "
                            "ON CONFLICT (cnts_bird) DO NOTHING",
                            new_contacts_data,
                        )
                    bids = list(contacts_to_resolve.keys())
                    rows = await conn.fetch_all(
                        "SELECT cnts_id, cnts_bird FROM contacts WHERE cnts_bird = ANY($1::varchar[])", (bids,)
                    )
                    for r in rows:
                        self._contact_cache[r["cnts_bird"]] = r["cnts_id"]

                for c in items:
                    updated_at_str = c.get("updatedDatetime")
                    updated_dt = _parse_dt(updated_at_str) if updated_at_str else None

                    if max_date and updated_at_str and updated_at_str >= max_date:
                        continue

                    if not full_sync and cutoff_dt and updated_dt:
                        if updated_dt < cutoff_dt:
                            should_stop = True
                            break

                    cnvs_bird = c["id"]
                    cnts_id = self._contact_cache.get(c.get("contactId"))
                    cnvs_msgcount = c.get("messages", {}).get("totalCount", 0)
                    cnvs_status = c.get("status")
                    cnvs_channel = c.get("lastUsedChannelId")
                    cnvs_created = _parse_dt(c.get("createdDatetime"))
                    cnvs_updated = updated_dt
                    cnvs_last = _parse_dt(c.get("lastReceivedDatetime"))

                    old_data = existing_map.get(cnvs_bird)
                    reopened_increment = 0
                    if (
                        old_data
                        and old_data["status"] != cnvs_status
                        and old_data["status"] == "archived"
                        and cnvs_status == "active"
                    ):
                        reopened_increment = 1

                    assigned = c.get("assignedTo") or {}
                    new_agnt_bird = assigned.get("id") if isinstance(assigned, dict) else None
                    new_agnt_id = self._agent_cache.get(new_agnt_bird) if new_agnt_bird else None

                    batch_data.append(
                        (
                            cnvs_bird,
                            cnts_id,
                            new_agnt_id,
                            cnvs_status,
                            cnvs_channel,
                            cnvs_created,
                            cnvs_updated,
                            cnvs_last,
                            cnvs_msgcount,
                            reopened_increment,
                        )
                    )

                if batch_data:
                    async with conn.transaction():
                        await conn.execute_many(
                            "INSERT INTO conversations "
                            "(cnvs_bird, cnvs_cnts, cnvs_agnt, cnvs_status, cnvs_channel, "
                            "cnvs_created, cnvs_updated, cnvs_last, cnvs_msgcount, cnvs_reopened_count) "
                            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) "
                            "ON CONFLICT (cnvs_bird) DO UPDATE SET "
                            "cnvs_msgcount = EXCLUDED.cnvs_msgcount, "
                            "cnvs_status = EXCLUDED.cnvs_status, "
                            "cnvs_channel = EXCLUDED.cnvs_channel, "
                            "cnvs_updated = EXCLUDED.cnvs_updated, "
                            "cnvs_last = EXCLUDED.cnvs_last, "
                            "cnvs_reopened_count = conversations.cnvs_reopened_count + EXCLUDED.cnvs_reopened_count, "
                            "cnvs_agnt = COALESCE(EXCLUDED.cnvs_agnt, conversations.cnvs_agnt)",
                            batch_data,
                        )
                    count += len(batch_data)

                if should_stop:
                    logger.info(f"  Stopped at conversation older than cutoff (status={status}, fetched={count})")
                    break

                if not next_page_token and len(items) < limit:
                    break

                if full_sync and status == "active":
                    await self.save_sync_progress(conn, "conversations", cursor=page_token, offset=offset)

        duration = time.time() - start_time
        await self.update_sync_state(
            conn, "conversations", duration=duration, records_count=count, cursor=None, offset=0
        )
        logger.info(f"Conversations sync completed. Total: {count}")

    # ── Message Sync ──────────────────────────────────────────────

    async def sync_messages(
        self, conn: PostgresSyncConnection, conversation_bird_id: str, date_from: str | None = None
    ) -> int:
        """Fetch messages for a conversation, extract agents, then run survey extraction."""
        res = await self._sync_messages_internal(conn, conversation_bird_id, date_from)
        if res > 0:
            await self.update_conversation_surveys(conn, conversation_bird_id)
        return res

    async def _sync_messages_internal(
        self, conn: PostgresSyncConnection, conversation_bird_id: str, date_from: str | None = None
    ) -> int:
        cnvs_row = await conn.fetch_one(
            "SELECT cnvs_id FROM conversations WHERE cnvs_bird = $1",
            (conversation_bird_id,),
        )
        if not cnvs_row:
            logger.error(f"Conversation {conversation_bird_id} not found in DB")
            return 0

        cnvs_id = cnvs_row["cnvs_id"]

        if date_from is None:
            last_msg = await conn.fetch_one(
                "SELECT msgs_created FROM messages WHERE msgs_cnvs = $1 ORDER BY msgs_created DESC LIMIT 1",
                (cnvs_id,),
            )
            if last_msg and last_msg["msgs_created"]:
                df = last_msg["msgs_created"]
                date_from = df.isoformat() if isinstance(df, datetime) else str(df)
                if "+" in date_from:
                    date_from = date_from.split("+")[0] + "Z"
                elif not date_from.endswith("Z"):
                    date_from += "Z"

        offset = 0
        limit = 20
        total_messages = 0

        while True:
            response = await self.client.get_messages(
                conversation_bird_id, limit=limit, offset=offset, date_from=date_from
            )

            if "error" in response:
                await self.log_sync_error(
                    conn,
                    "messages",
                    str(response["error"]),
                    context={"cnvs_bird": conversation_bird_id, "offset": offset},
                )
                break

            items: list[dict[str, Any]] = response.get("items", [])  # type: ignore[assignment]
            if not items:
                break

            agents_to_resolve: dict[str, str] = {}
            all_messages = []

            for m in items:
                direction = m.get("direction")
                content_obj = m.get("content")
                content_text = ""
                if isinstance(content_obj, dict):
                    content_text = content_obj.get("text", "") or content_obj.get("hsm", {}).get("elementName", "")
                else:
                    content_text = str(content_obj) if content_obj else ""

                if direction == "sent":
                    source = m.get("source", {})
                    agent = source.get("inboxAgent")
                    if agent and agent.get("id"):
                        agent_bid = agent["id"]
                        if agent_bid not in self._agent_cache:
                            agents_to_resolve[agent_bid] = agent.get("fullName") or agent.get("firstName") or "Unknown"

                all_messages.append(
                    {
                        "id": m.get("id"),
                        "direction": direction,
                        "status": m.get("status"),
                        "type": m.get("type"),
                        "content": content_text,
                        "created": m.get("createdDatetime"),
                        "updated": m.get("updatedDatetime"),
                        "source": m.get("source", {}),
                    }
                )

            for bid, name in agents_to_resolve.items():
                await self.get_or_create_agent(conn, bid, name)

            batch_params = []
            last_agent_id = None

            for m_data in all_messages:
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
                        _parse_dt(m_data["created"]),
                        _parse_dt(m_data["updated"]),
                    )
                )

            if batch_params:
                async with conn.transaction():
                    await conn.execute_many(
                        "INSERT INTO messages "
                        "(msgs_cnvs, msgs_agnt, msgs_direction, msgs_status, msgs_type, "
                        "msgs_content, msgs_bird, msgs_created, msgs_updated) "
                        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) "
                        "ON CONFLICT (msgs_bird) DO UPDATE SET "
                        "msgs_status = EXCLUDED.msgs_status, "
                        "msgs_updated = EXCLUDED.msgs_updated",
                        batch_params,
                    )
                    if last_agent_id:
                        await conn.execute_query(
                            "UPDATE conversations SET cnvs_agnt = $1 WHERE cnvs_id = $2",
                            (last_agent_id, cnvs_id),
                        )
                total_messages += len(batch_params)

            if len(items) < limit:
                break
            offset += len(items)

        return total_messages

    async def sync_all_messages(self, conn: PostgresSyncConnection):
        """Sync messages for ALL conversations with smart skip and delta sync."""
        rows = await conn.fetch_all("SELECT cnvs_bird, cnvs_msgcount FROM conversations ORDER BY cnvs_updated DESC")
        total = len(rows)
        logger.info(f"Syncing messages for {total} conversations...")
        start_time = time.time()
        semaphore = asyncio.Semaphore(30)

        async def fetch_with_limit(row):
            async with semaphore:
                try:
                    bird_id = row["cnvs_bird"]
                    remote_count = row["cnvs_msgcount"]
                    local_count_row = await conn.fetch_one(
                        "SELECT COUNT(*) as count, MAX(msgs_created) as last_msg_date "
                        "FROM messages WHERE msgs_cnvs = (SELECT cnvs_id FROM conversations WHERE cnvs_bird = $1)",
                        (bird_id,),
                    )
                    local_count = local_count_row["count"] if local_count_row else 0
                    last_msg_date = local_count_row["last_msg_date"] if local_count_row else None

                    if remote_count is not None and local_count == remote_count and remote_count > 0:
                        return 0

                    date_from = None
                    if local_count > 0 and last_msg_date:
                        if isinstance(last_msg_date, datetime):
                            date_from = last_msg_date.isoformat()
                        else:
                            date_from = str(last_msg_date)

                    return await self.sync_messages(conn, bird_id, date_from=date_from)
                except Exception as e:
                    logger.error(f"Error syncing messages for {row['cnvs_bird']}: {e}")
                    return 0

        tasks = [fetch_with_limit(row) for row in rows]
        msg_count = 0
        chunk_size = 1000

        for i in range(0, len(tasks), chunk_size):
            chunk = tasks[i : i + chunk_size]
            results = await asyncio.gather(*chunk)
            msg_count += sum(results)

        elapsed = time.time() - start_time
        await self.update_sync_state(conn, "messages", duration=elapsed, records_count=msg_count)
        logger.info(f"All messages sync completed. {total} conversations, {msg_count} messages.")

    async def sync_messages_for_month(self, conn: PostgresSyncConnection, year: int, month: int) -> int:
        """Sync messages for conversations updated in a specific calendar month."""
        month_start, next_month_start = month_bounds_utc(year, month)
        start_iso = to_bird_iso(month_start)
        end_iso = to_bird_iso(next_month_start)

        rows = await conn.fetch_all(
            "SELECT cnvs_bird FROM conversations "
            "WHERE cnvs_updated >= $1::timestamp AND cnvs_updated < $2::timestamp "
            "ORDER BY cnvs_updated DESC",
            (start_iso, end_iso),
        )
        total = len(rows)
        logger.info(f"Syncing messages for {total} conversations updated in {year:04d}-{month:02d}...")
        semaphore = asyncio.Semaphore(10)

        async def fetch_with_limit(row):
            async with semaphore:
                try:
                    return await self.sync_messages(conn, row["cnvs_bird"], date_from=start_iso)
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
            f"Monthly messages sync completed. {total} conversations, "
            f"{msg_count} messages from {year:04d}-{month:02d} onward."
        )
        return msg_count

    async def sync_messages_for_recent(self, conn: PostgresSyncConnection, days: int = 30):
        """Sync messages only for conversations updated in the last N days."""
        rows = await conn.fetch_all(
            "SELECT cnvs_bird FROM conversations "
            "WHERE cnvs_updated >= (NOW() - ($1 || ' days')::interval) "
            "ORDER BY cnvs_updated DESC",
            (str(days),),
        )
        total = len(rows)
        logger.info(f"Syncing messages for {total} conversations updated in last {days} days...")
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

        logger.info(f"Recent messages sync completed. {total} conversations, {msg_count} messages.")

    # ── Survey Extraction ─────────────────────────────────────────

    async def update_conversation_surveys(self, conn: PostgresSyncConnection, conversation_bird_id: str):
        """Extract survey and screening data from conversation messages via regex patterns."""
        from domain import constants

        cnvs_row = await conn.fetch_one(
            "SELECT cnvs_id, cnvs_status, cnvs_rating_agent, cnvs_rating_nps FROM conversations WHERE cnvs_bird = $1",
            (conversation_bird_id,),
        )
        if not cnvs_row:
            return
        cnvs_id = cnvs_row["cnvs_id"]

        questions = {
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
            "SELECT msgs_id, msgs_content, msgs_direction, msgs_created "
            "FROM messages WHERE msgs_cnvs = $1 ORDER BY msgs_created ASC",
            (cnvs_id,),
        )

        updates: dict[str, int | str] = {}
        for i, msg in enumerate(messages):
            content = msg["msgs_content"] or ""

            if msg["msgs_direction"] == "sent" and config.PHRASE_TICKET_HEADER in content:
                lines = [ln.strip() for ln in content.split("\n")]
                try:
                    idx = next(j for j, ln in enumerate(lines) if config.PHRASE_TICKET_HEADER in ln)
                    ticket_lines = [ln for ln in lines[idx + 1 :] if ln and not ln.startswith("===")]
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
            for key, pattern in questions.items():
                if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                    matched_key = key
                    break

            if matched_key:
                timestamp = msg["msgs_created"]
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                for j in range(i + 1, min(i + 10, len(messages))):
                    next_msg = messages[j]
                    if next_msg["msgs_direction"] != "received":
                        continue
                    next_ts = next_msg["msgs_created"]
                    if isinstance(next_ts, str):
                        next_ts = datetime.fromisoformat(next_ts.replace("Z", "+00:00"))
                    if next_ts - timestamp > timedelta(minutes=60):
                        break
                    resp = (next_msg["msgs_content"] or "").strip()
                    if not resp:
                        continue

                    found = False
                    if matched_key == "tax_id":
                        val = re.sub(r"\D", "", resp)
                        if val:
                            updates["cnvs_tax_id"] = val
                            found = True
                    elif matched_key == "software":
                        m = re.search(r"(\d+)", resp)
                        num = int(m.group(1)) if m else None
                        for name in config.SOFTWARE_NAMES:
                            if (num is not None and str(num) in resp) or name.upper() in resp.upper():
                                updates["cnvs_software"] = name
                                found = True
                                break
                        if not found:
                            updates["cnvs_software"] = config.DEFAULT_SOFTWARE
                            found = True
                    else:
                        m = re.search(r"(\d+)", resp)
                        num = int(m.group(1)) if m else None
                        if num is not None:
                            if matched_key == "lang" and 1 <= num <= 3:
                                updates["cnvs_lang"] = num
                                found = True
                            elif matched_key == "dept" and 1 <= num <= 5:
                                updates["cnvs_dept"] = num
                                found = True
                            elif matched_key == "contact_reason" and 1 <= num <= 6:
                                updates["cnvs_contact_reason"] = num
                                found = True
                            elif matched_key == "occurrence" and 1 <= num <= 6:
                                updates["cnvs_occurrence"] = num
                                found = True
                            elif matched_key == "rating_agent" and 1 <= num <= 5:
                                updates["cnvs_rating_agent"] = num
                                found = True
                            elif matched_key == "rating_nps" and 0 <= num <= 10:
                                updates["cnvs_rating_nps"] = num
                                found = True
                    if found:
                        break

        if updates:
            set_parts = []
            params = []
            for idx, (k, v) in enumerate(updates.items(), 1):
                set_parts.append(f"{k} = ${idx}")
                params.append(v)
            set_clause = ", ".join(set_parts)
            params.append(cnvs_id)
            await conn.execute_query(
                f"UPDATE conversations SET {set_clause} WHERE cnvs_id = ${len(params)}",
                tuple(params),
            )

    async def backfill_surveys(self, conn: PostgresSyncConnection) -> int:
        """Re-extract survey data for conversations missing NPS/rating values."""
        rows = await conn.fetch_all(
            "SELECT DISTINCT cv.cnvs_bird "
            "FROM conversations cv "
            "JOIN messages m ON m.msgs_cnvs = cv.cnvs_id "
            "WHERE m.msgs_direction = 'sent' "
            "AND ("
            "  m.msgs_content LIKE '%Avalie%' "
            "  OR m.msgs_content LIKE '%avalia o atendimento%' "
            "  OR m.msgs_content LIKE '%Qual o motivo do contato%' "
            "  OR m.msgs_content LIKE '%Selecione o departamento%'"
            ") "
            "AND ("
            "  cv.cnvs_rating_nps IS NULL "
            "  OR cv.cnvs_rating_agent IS NULL "
            "  OR cv.cnvs_contact_reason IS NULL "
            "  OR cv.cnvs_dept IS NULL"
            ") "
            "ORDER BY cv.cnvs_id"
        )
        total = len(rows)
        logger.info(f"Survey backfill: {total} conversations to process...")
        for i, row in enumerate(rows):
            await self.update_conversation_surveys(conn, row["cnvs_bird"])
            if (i + 1) % 200 == 0:
                logger.info(f"  ...{i + 1}/{total} conversations processed")
        logger.info(f"Survey backfill completed: {total} conversations processed.")
        return total

    # ── High-Level Sync Orchestrators ─────────────────────────────

    async def full_sync(self, conn: PostgresSyncConnection):
        await self._load_caches(conn)
        await self.seed_known_agents(conn)
        await self.sync_contacts(conn)
        await self.sync_conversations(conn, full_sync=True)

    async def full_sync_with_messages(self, conn: PostgresSyncConnection):
        await self.full_sync(conn)
        await self.sync_all_messages(conn)


async def trigger_sync_pg(
    pool,
    full_sync: bool = False,
    sync_messages: bool = False,
    messages_days: int | None = None,
    lookback_minutes: int = 60,
    year: int | None = None,
    month: int | None = None,
    backfill_surveys: bool = False,
) -> str:
    from infrastructure.database.postgres_connection import PostgresPool

    raw_pool = pool.pool if isinstance(pool, PostgresPool) else pool
    manager = PgSyncManager()
    conn = PostgresSyncConnection(raw_pool)

    await manager._load_caches(conn)
    await manager.seed_known_agents(conn)

    if backfill_surveys:
        count = await manager.backfill_surveys(conn)
        return f"Survey backfill concluído: {count} conversas processadas."

    if (year is None) != (month is None):
        raise ValueError("Use year and month together for monthly sync.")

    if year is not None and month is not None:
        month_start, next_month_start = month_bounds_utc(year, month)
        start_iso = to_bird_iso(month_start)
        end_iso = to_bird_iso(next_month_start)
        await manager.sync_conversations(conn, full_sync=False, min_date=start_iso, max_date=end_iso)
        synced_messages = await manager.sync_messages_for_month(conn, year, month)
        return f"Monthly sync completed for {year:04d}-{month:02d} ({synced_messages} messages)."

    if full_sync and sync_messages:
        await manager.full_sync_with_messages(conn)
        return "Full sync with messages completed."
    elif full_sync:
        await manager.full_sync(conn)
        return "Full structural sync completed."
    else:
        if messages_days is not None:
            effective_lookback = max(lookback_minutes, messages_days * 24 * 60)
            await manager.sync_contacts(conn)
            await manager.sync_conversations(conn, lookback_minutes=effective_lookback)
            await manager.sync_messages_for_recent(conn, days=messages_days)
            return f"Incremental sync completed with messages for last {messages_days} days."
        else:
            await manager.sync_contacts(conn)
            await manager.sync_conversations(conn, lookback_minutes=lookback_minutes)
            return "Incremental sync completed."
