import json
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


def parse_dt(value: str | datetime | None) -> datetime | None:
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

    async def load_caches(self, conn: PostgresSyncConnection):
        rows = await conn.fetch_all("SELECT agnt_id, agnt_bird FROM agents")
        self._agent_cache = {r["agnt_bird"]: r["agnt_id"] for r in rows}
        rows = await conn.fetch_all("SELECT cnts_id, cnts_bird FROM contacts")
        self._contact_cache = {r["cnts_bird"]: r["cnts_id"] for r in rows}
        logger.info("Caches loaded: %d agents, %d contacts", len(self._agent_cache), len(self._contact_cache))

    async def seed_known_agents(self, conn: PostgresSyncConnection):
        known_agents = config.get_known_agents()
        if not known_agents:
            return
        agents_data = [
            (info["name"].strip() if info["name"] else info["name"], info.get("group", "OUTROS"), bird_id)
            for bird_id, info in known_agents.items()
        ]
        await conn.execute_many(
            "INSERT INTO agents (agnt_name, agnt_grp, agnt_bird) VALUES ($1, $2, $3) "
            "ON CONFLICT (agnt_bird) DO UPDATE SET "
            "agnt_name = EXCLUDED.agnt_name, agnt_grp = EXCLUDED.agnt_grp, agnt_updated = NOW()",
            agents_data,
        )

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
            "INSERT INTO agents (agnt_name, agnt_grp, agnt_bird) VALUES ($1, $2, $3) "
            "ON CONFLICT (agnt_bird) DO NOTHING",
            (name, "OUTROS", bird_id),
        )
        row = await conn.fetch_one("SELECT agnt_id FROM agents WHERE agnt_bird = $1", (bird_id,))
        if row:
            self._agent_cache[bird_id] = row["agnt_id"]
            return row["agnt_id"]
        return None

    async def get_last_sync_time(self, conn: PostgresSyncConnection, resource: str):
        row = await conn.fetch_one(
            "SELECT sync_created, sync_cursor, sync_offset "
            "FROM sync WHERE sync_resource = $1 ORDER BY sync_id DESC LIMIT 1",
            (resource,),
        )
        if row:
            return row["sync_created"], row["sync_cursor"], row["sync_offset"] or 0
        return None, None, 0

    async def should_skip(self, conn: PostgresSyncConnection, resource: str, minutes: int = 60) -> bool:
        last_time, _, _ = await self.get_last_sync_time(conn, resource)
        if not last_time:
            return False
        if isinstance(last_time, str):
            try:
                last_dt = datetime.fromisoformat(last_time.replace(" ", "T"))
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=UTC)
            except ValueError:
                return False
        else:
            last_dt = last_time
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=UTC)
        return datetime.now(UTC) - last_dt < timedelta(minutes=minutes)

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
        logger.error("Sync error logged for %s: %s", resource, error_msg)
