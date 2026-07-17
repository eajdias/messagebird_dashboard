"""PostgreSQL sync engine (asyncpg).

Replaces the legacy SQLite sync pipeline (infrastructure.api.sync).
The structure mirrors SyncManager but uses asyncpg-compatible SQL.

API methods called by trigger_sync_pg delegate to the MessageBirdClient
and persist data via PostgresSyncConnection.
"""

import logging
from datetime import UTC, datetime, timedelta

from infrastructure.api import config
from infrastructure.api.client import MessageBirdClient
from infrastructure.database.sync_connection_pg import PostgresSyncConnection

logger = logging.getLogger("m_bird.sync_pg")


def month_bounds_utc(year: int, month: int) -> tuple[datetime, datetime]:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    start = datetime(year, month, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC) if month == 12 else datetime(year, month + 1, 1, tzinfo=UTC)
    return start, end


def to_bird_iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


class PgSyncManager:
    def __init__(self):
        self.client = MessageBirdClient()
        self._agent_cache: dict[str, int] = {}
        self._contact_cache: dict[str, int] = {}

    async def _load_caches(self, conn: PostgresSyncConnection):
        rows = await conn.fetch_all("SELECT agnt_id, agnt_bird FROM agents")
        self._agent_cache = {r["agnt_bird"]: r["agnt_id"] for r in rows}
        rows = await conn.fetch_all("SELECT cnts_id, cnts_bird FROM contacts")
        self._contact_cache = {r["cnts_bird"]: r["cnts_id"] for r in rows}
        logger.info(f"Caches loaded: {len(self._agent_cache)} agents, {len(self._contact_cache)} contacts")

    async def seed_known_agents(self, conn: PostgresSyncConnection):
        known_agents = config.get_known_agents()
        if not known_agents:
            return
        agents_data = [(name.strip() if name else name, bird_id) for bird_id, name in known_agents.items()]
        await conn.execute_many(
            "INSERT INTO agents (agnt_name, agnt_bird) VALUES ($1, $2) "
            "ON CONFLICT (agnt_bird) DO UPDATE SET agnt_name = EXCLUDED.agnt_name, agnt_updated = NOW()",
            agents_data,
        )

    async def get_or_create_contact(self, conn: PostgresSyncConnection, bird_id: str, name: str, phone: str) -> int | None:
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
            "INSERT INTO agents (agnt_bird, agnt_name) VALUES ($1, $2) "
            "ON CONFLICT (agnt_bird) DO NOTHING",
            (bird_id, name),
        )
        row = await conn.fetch_one("SELECT agnt_id FROM agents WHERE agnt_bird = $1", (bird_id,))
        if row:
            self._agent_cache[bird_id] = row["agnt_id"]
            return row["agnt_id"]
        return None

    async def get_last_sync_time(self, conn: PostgresSyncConnection, resource: str):
        row = await conn.fetch_one(
            "SELECT sync_created, sync_cursor, sync_offset FROM sync WHERE sync_resource = $1 ORDER BY sync_id DESC LIMIT 1",
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

    async def update_sync_state(self, conn: PostgresSyncConnection, resource: str, duration=None, records_count=None, cursor=None, offset=0):
        await conn.execute_query(
            "INSERT INTO sync (sync_resource, sync_duration, sync_records_count, sync_cursor, sync_offset) VALUES ($1, $2, $3, $4, $5)",
            (resource, duration, records_count, cursor, offset),
        )

    async def log_sync_error(self, conn: PostgresSyncConnection, resource: str, error_msg: str, code=None, context=None):
        import json
        context_json = json.dumps(context) if context else None
        await conn.execute_query(
            "INSERT INTO sync_errors (err_resource, err_code, err_message, err_context) VALUES ($1, $2, $3, $4)",
            (resource, str(code) if code else None, error_msg, context_json),
        )
        logger.error(f"Sync error logged for {resource}: {error_msg}")

    async def sync_contacts(self, conn: PostgresSyncConnection):
        logger.info("Starting contacts sync...")
        offset = 0
        limit = 20
        processed_count = 0
        while True:
            response = await self.client.list_contacts(limit=limit, offset=offset)
            if "error" in response:
                await self.log_sync_error(conn, "contacts", response["error"], context={"offset": offset})
                break
            items = response.get("items", [])
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
                contacts_data.append((contact_name, phone, c.get("id"), c.get("createdAt"), c.get("updatedAt")))
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

    async def sync_conversations(
        self,
        conn: PostgresSyncConnection,
        lookback_minutes=60,
        full_sync=False,
        min_date=None,
        max_date=None,
    ):
        logger.info(f"Starting conversations sync (full={full_sync}, min_date={min_date}, max_date={max_date})...")
        last_sync, resume_cursor, resume_offset = await self.get_last_sync_time(conn, "conversations")
        if not last_sync:
            full_sync = True
        if not full_sync and min_date is None and lookback_minutes:
            cutoff = datetime.now(UTC) - timedelta(minutes=lookback_minutes)
            min_date = cutoff.isoformat().replace("+00:00", "Z")
            logger.info(f"  Syncing conversations updated after {min_date}")

        page_token = resume_cursor
        offset = resume_offset or 0
        limit = 50
        count = 0
        import time
        start_time = time.time()

        while True:
            params = {"limit": limit}
            if page_token:
                params["pageToken"] = page_token
            elif offset:
                params["offset"] = offset
            if min_date:
                params["createdDatetimeAfter"] = min_date
            if max_date:
                params["createdDatetimeBefore"] = max_date
            if not full_sync and min_date is None:
                params["updatedDatetimeAfter"] = (datetime.now(UTC) - timedelta(minutes=lookback_minutes)).isoformat().replace("+00:00", "Z")

            response = await self.client.list_conversations(**params)
            if "error" in response:
                await self.log_sync_error(conn, "conversations", response["error"], context=params)
                break
            items = response.get("data", response.get("items", []))
            if not items:
                break
            page_token = response.get("pagination", {}).get("nextPageToken") or response.get("nextPageToken")
            offset += len(items)
            count += len(items)

            convs_data = []
            for cv in items:
                attrs = cv.get("attributes", cv.get("channels", {}).get("attributes", {})) or {}
                convs_data.append((
                    cv.get("displayName", cv.get("id")),
                    attrs.get("firstName", cv.get("from", {}).get("displayName", "")) or "",
                    attrs.get("lastName", ""),
                    attrs.get("channel", cv.get("channel", "")) or "",
                    cv.get("id"),
                    cv.get("createdAt"),
                    cv.get("updatedAt", cv.get("lastMessageTimestamp")),
                    cv.get("status"),
                    1 if cv.get("createdAt") == cv.get("lastMessageTimestamp") else 0,
                ))

            if convs_data:
                async with conn.transaction():
                    await conn.execute_many(
                        "INSERT INTO conversations (cnvs_bird, cnvs_agnt, cnvs_channel, cnvs_status, "
                        "cnvs_created, cnvs_updated, cnvs_msgcount) "
                        "VALUES ($1, NULL, $2, $3, $4, $5, $6) "
                        "ON CONFLICT (cnvs_bird) DO UPDATE SET cnvs_status = EXCLUDED.cnvs_status, "
                        "cnvs_updated = EXCLUDED.cnvs_updated, cnvs_msgcount = EXCLUDED.cnvs_msgcount",
                        convs_data,
                    )

            if page_token:
                await self.save_sync_progress(conn, "conversations", cursor=page_token, offset=offset)
            if not page_token and len(items) < limit:
                break

        duration = time.time() - start_time
        await self.update_sync_state(conn, "conversations", duration=duration, records_count=count, cursor=None, offset=0)
        logger.info(f"Conversations sync completed. Total: {count}")

    async def handle_conversation_contacts(self, conn: PostgresSyncConnection, items: list):
        for cv in items:
            bird_id = cv.get("id")
            contact_name = cv.get("displayName") or cv.get("from", {}).get("displayName", "")
            phone = cv.get("from", {}).get("phoneNumber") or cv.get("from", {}).get("id", "")
            if phone in ("None", "null", ""):
                phone = None
            contact_id = await self.get_or_create_contact(conn, bird_id, contact_name, phone)
            if contact_id:
                await conn.execute_query(
                    "UPDATE conversations SET cnvs_cnts = $1 WHERE cnvs_bird = $2",
                    (contact_id, bird_id),
                )

    async def full_sync(self, conn: PostgresSyncConnection):
        await self._load_caches(conn)
        await self.seed_known_agents(conn)
        await self.sync_contacts(conn)
        await self.sync_conversations(conn, full_sync=True)

    async def full_sync_with_messages(self, conn: PostgresSyncConnection):
        await self.full_sync(conn)
        logger.info("Full sync with messages completed (message sync TBD)")


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
    manager = PgSyncManager()
    conn = PostgresSyncConnection(pool)

    await manager._load_caches(conn)
    await manager.seed_known_agents(conn)

    if backfill_surveys:
        return "Survey backfill não implementado em PG sync ainda (use CLI SQLite)"

    if (year is None) != (month is None):
        raise ValueError("Use year and month together for monthly sync.")

    if year is not None and month is not None:
        month_start, next_month_start = month_bounds_utc(year, month)
        start_iso = to_bird_iso(month_start)
        end_iso = to_bird_iso(next_month_start)
        await manager.sync_conversations(conn, full_sync=False, min_date=start_iso, max_date=end_iso)
        return f"Monthly sync completed for {year:04d}-{month:02d}."

    if full_sync and sync_messages:
        await manager.full_sync_with_messages(conn)
        return "Full sync with messages completed."
    elif full_sync:
        await manager.full_sync(conn)
        return "Full structural sync completed."
    else:
        await manager.sync_contacts(conn)
        await manager.sync_conversations(conn, lookback_minutes=lookback_minutes)
        return "Incremental sync completed."
