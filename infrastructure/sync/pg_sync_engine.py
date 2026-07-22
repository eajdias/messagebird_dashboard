"""PostgreSQL sync engine — orchestrator.

Delegates to specialized modules:
  - sync_core.py: PgSyncManager class + helpers
  - sync_contacts.py: contact sync
  - sync_conversations.py: conversation sync
  - sync_messages.py: message sync
  - sync_surveys.py: survey extraction
"""

import logging
from datetime import UTC, datetime

from infrastructure.database.postgres_connection import PostgresPool
from infrastructure.database.sync_connection_pg import PostgresSyncConnection
from infrastructure.sync.sync_contacts import sync_contacts
from infrastructure.sync.sync_conversations import sync_conversations
from infrastructure.sync.sync_core import PgSyncManager, month_bounds_utc, to_bird_iso
from infrastructure.sync.sync_messages import (
    sync_all_messages,
    sync_messages_for_month,
    sync_messages_for_range,
    sync_messages_for_recent,
)
from infrastructure.sync.sync_surveys import backfill_surveys as survey_backfill_fn

logger = logging.getLogger("m_bird.sync_pg")


async def trigger_sync_pg(
    pool,
    full_sync: bool = False,
    sync_messages: bool = False,
    messages_days: int | None = None,
    year: int | None = None,
    month: int | None = None,
    backfill_surveys: bool = False,
    sync_today: bool = False,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    raw_pool = pool.pool if isinstance(pool, PostgresPool) else pool
    manager = PgSyncManager()
    conn = PostgresSyncConnection(raw_pool)

    await manager.load_caches(conn)
    await manager.seed_known_agents(conn)

    if backfill_surveys:
        count = await survey_backfill_fn(manager, conn)
        return f"Survey backfill concluído: {count} conversas processadas."

    if start_date is not None or end_date is not None:
        if not start_date or not end_date:
            raise ValueError("start_date and end_date must be provided together.")

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError as e:
            raise ValueError(f"Invalid date format (use ISO 8601 YYYY-MM-DD): {e}") from e
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=UTC)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=UTC)
        if end_dt.date() < start_dt.date():
            raise ValueError("end_date must be on or after start_date.")
        delta_days = (end_dt.date() - start_dt.date()).days + 1
        if delta_days > 30:
            raise ValueError(f"Range cannot exceed 30 days (got {delta_days} days).")
        if delta_days < 1:
            raise ValueError("Range must be at least 1 day.")
        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        start_iso = to_bird_iso(start_dt)
        end_iso = to_bird_iso(end_dt)
        await sync_conversations(manager, conn, min_date=start_iso, max_date=end_iso)
        msg_count = await sync_messages_for_range(manager, conn, start_dt, end_dt)
        return f"Range sync completed for {start_date} → {end_date}: {msg_count} messages."

    if (year is None) != (month is None):
        raise ValueError("Use year and month together for monthly sync.")

    if year is not None and month is not None:
        month_start, next_month_start = month_bounds_utc(year, month)
        start_iso = to_bird_iso(month_start)
        end_iso = to_bird_iso(next_month_start)
        await sync_conversations(manager, conn, min_date=start_iso, max_date=end_iso)
        synced_messages = await sync_messages_for_month(manager, conn, year, month)
        return f"Monthly sync completed for {year:04d}-{month:02d} ({synced_messages} messages)."

    if sync_today:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_iso = to_bird_iso(today_start)
        now_iso = to_bird_iso(now)

        if await manager.should_skip(conn, "contacts"):
            logger.info("Contacts synced recently, skipping.")
        else:
            await sync_contacts(manager, conn)

        await sync_conversations(manager, conn, min_date=today_start_iso, max_date=now_iso)

        today_start_naive = today_start.replace(tzinfo=None)
        now_naive = now.replace(tzinfo=None)
        rows = await conn.fetch_all(
            "SELECT cnvs_bird FROM conversations "
            "WHERE cnvs_created >= $1::timestamp AND cnvs_created <= $2::timestamp "
            "ORDER BY cnvs_updated DESC",
            (today_start_naive, now_naive),
        )
        logger.info("Syncing messages for %d conversations created today...", len(rows))
        msg_count = 0
        for row in rows:
            from infrastructure.sync.sync_messages import sync_messages as sync_msgs

            msg_count += await sync_msgs(manager, conn, row["cnvs_bird"], date_from=today_start_iso)
        return f"Today sync completed: {len(rows)} conversations, {msg_count} messages."

    # Full structural sync always — only messages_days varies
    if await manager.should_skip(conn, "contacts"):
        logger.info("Contacts synced recently, skipping.")
    else:
        await sync_contacts(manager, conn)
    await sync_conversations(manager, conn)

    if full_sync and sync_messages:
        await sync_all_messages(manager, conn)
        return "Full sync with all messages completed."

    if messages_days is not None:
        msg_count = await sync_messages_for_recent(manager, conn, days=messages_days)
        return f"Sync completed ({msg_count} messages for last {messages_days} days)."

    return "Structural sync completed (no messages)."
