"""PostgreSQL sync engine — orchestrator.

Sync pipeline with clear separation of responsibilities:

  1. sync_conversations_full    — Fetch ALL conversations from Bird API
  2. sync_conversations_month   — Fetch conversations for a specific month
  3. sync_messages_month        — Fetch messages for conversations already in DB (by month)
  4. sync_messages_range        — Fetch messages for conversations already in DB (by date range)

Usage:
  - Backfill month:   sync_conversations_month + sync_messages_month
  - Backfill range:   (conversations must exist in DB) + sync_messages_range
  - Full initial:     sync_conversations_full + sync_messages_month/range
  - Daily incremental: handled by APScheduler (sync_today path)
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
    sync_incomplete_conversations,
    sync_messages_for_month,
    sync_messages_for_range,
    sync_messages_for_recent,
)
from infrastructure.sync.sync_surveys import backfill_surveys as survey_backfill_fn

logger = logging.getLogger("m_bird.sync_pg")


# ── 1. Sync ALL conversations from Bird API ──────────────────────────────


async def sync_conversations_full(pool) -> str:
    """Fetch ALL conversations from Bird API (no date/status filter).

    This is the slowest operation (~15-25min for 60k+ conversations).
    Run once for initial setup, then use monthly sync for backfill.
    """
    raw_pool = pool.pool if isinstance(pool, PostgresPool) else pool
    manager = PgSyncManager()
    conn = PostgresSyncConnection(raw_pool)
    try:
        await manager.load_caches(conn)
        await manager.seed_known_agents(conn)

        await sync_contacts(manager, conn)
        await sync_conversations(manager, conn)

        return "Full conversations sync completed (all conversations from Bird API)."
    finally:
        await manager.client.close()


# ── 2. Sync conversations for a specific month ───────────────────────────


async def sync_conversations_month(pool, year: int, month: int) -> str:
    """Fetch conversations for a specific month from Bird API.

    Duration: ~2-5min depending on volume (~1000 conversations/month).
    """
    raw_pool = pool.pool if isinstance(pool, PostgresPool) else pool
    manager = PgSyncManager()
    conn = PostgresSyncConnection(raw_pool)
    try:
        await manager.load_caches(conn)
        await manager.seed_known_agents(conn)

        month_start, next_month_start = month_bounds_utc(year, month)
        start_iso = to_bird_iso(month_start)
        end_iso = to_bird_iso(next_month_start)

        await sync_conversations(manager, conn, min_date=start_iso, max_date=end_iso)

        return f"Conversations sync completed for {year:04d}-{month:02d}."
    finally:
        await manager.client.close()


# ── 3. Sync messages for conversations in DB (by month) ──────────────────


async def sync_messages_month(pool, year: int, month: int, backfill_surveys: bool = False) -> str:
    """Fetch messages for conversations already in DB for a specific month.

    This does NOT fetch conversations from Bird API — it only syncs messages
    for conversations that already exist in the database.

    Duration: ~3-5min (depends on number of conversations and messages).
    """
    raw_pool = pool.pool if isinstance(pool, PostgresPool) else pool
    manager = PgSyncManager()
    conn = PostgresSyncConnection(raw_pool)
    try:
        await manager.load_caches(conn)

        msg_count = await sync_messages_for_month(manager, conn, year, month)

        result = f"Messages sync completed for {year:04d}-{month:02d}: {msg_count} messages."

        if backfill_surveys:
            count = await survey_backfill_fn(manager, conn)
            result += f" Survey backfill: {count} conversations processed."

        return result
    finally:
        await manager.client.close()


# ── 4. Sync messages for conversations in DB (by date range) ─────────────


async def sync_messages_range(pool, start_date: str, end_date: str, backfill_surveys: bool = False) -> str:
    """Fetch messages for conversations already in DB for a date range.

    This does NOT fetch conversations from Bird API — it only syncs messages
    for conversations that already exist in the database.

    Duration: ~1-3min (depends on date range and conversation count).
    """
    raw_pool = pool.pool if isinstance(pool, PostgresPool) else pool
    manager = PgSyncManager()
    conn = PostgresSyncConnection(raw_pool)
    try:
        await manager.load_caches(conn)

        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
        except ValueError as e:
            raise ValueError(f"Invalid date format (use ISO 8601 YYYY-MM-DD): {e}") from e

        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=UTC)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=UTC)

        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        msg_count = await sync_messages_for_range(manager, conn, start_dt, end_dt)

        result = f"Messages sync completed for {start_date} → {end_date}: {msg_count} messages."

        if backfill_surveys:
            count = await survey_backfill_fn(manager, conn)
            result += f" Survey backfill: {count} conversations processed."

        return result
    finally:
        await manager.client.close()


# ── Legacy / Daily sync (used by scheduler) ──────────────────────────────


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
    backfill_incomplete: bool = False,
) -> str:
    """Legacy sync trigger — kept for backward compatibility with scheduler."""
    raw_pool = pool.pool if isinstance(pool, PostgresPool) else pool
    manager = PgSyncManager()
    conn = PostgresSyncConnection(raw_pool)

    try:
        await manager.load_caches(conn)
        await manager.seed_known_agents(conn)

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
            # Monthly: sync conversations for month + messages for month
            month_start, next_month_start = month_bounds_utc(year, month)
            start_iso = to_bird_iso(month_start)
            end_iso = to_bird_iso(next_month_start)
            await sync_conversations(manager, conn, min_date=start_iso, max_date=end_iso)
            synced_messages = await sync_messages_for_month(manager, conn, year, month)
            if backfill_incomplete:
                incomplete_count = await sync_incomplete_conversations(manager, conn)
                return (
                    f"Monthly sync completed for {year:04d}-{month:02d} "
                    f"({synced_messages} messages). "
                    f"Incomplete backfill: {incomplete_count} messages."
                )
            return f"Monthly sync completed for {year:04d}-{month:02d} ({synced_messages} messages)."

        if backfill_incomplete:
            inc_count = await sync_incomplete_conversations(manager, conn)
            return f"Incomplete backfill completed: {inc_count} new messages."

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

                count, _ = await sync_msgs(manager, conn, row["cnvs_bird"], date_from=today_start_iso)
                msg_count += count

            if backfill_surveys:
                count = await survey_backfill_fn(manager, conn)
                return (
                    f"Today sync + survey backfill completed: {len(rows)} conversations,"
                    f" {msg_count} messages, {count} surveys."
                )

            return f"Today sync completed: {len(rows)} conversations, {msg_count} messages."

        # Full structural sync always — only messages_days varies
        if await manager.should_skip(conn, "contacts"):
            logger.info("Contacts synced recently, skipping.")
        else:
            await sync_contacts(manager, conn)
        await sync_conversations(manager, conn)

        if full_sync and sync_messages:
            await sync_all_messages(manager, conn)
            if backfill_surveys:
                count = await survey_backfill_fn(manager, conn)
                return f"Full sync + survey backfill completed: {count} surveys processed."
            return "Full sync with all messages completed."

        if messages_days is not None:
            msg_count = await sync_messages_for_recent(manager, conn, days=messages_days)
            if backfill_surveys:
                count = await survey_backfill_fn(manager, conn)
                return (
                    f"Sync + survey backfill completed: {msg_count} messages"
                    f" for last {messages_days} days, {count} surveys."
                )
            return f"Sync completed ({msg_count} messages for last {messages_days} days)."

        if backfill_surveys:
            count = await survey_backfill_fn(manager, conn)
            return f"Structural sync + survey backfill completed: {count} surveys."

        return "Structural sync completed (no messages)."
    finally:
        await manager.client.close()
