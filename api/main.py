import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from api.dependencies import stop_pool
from api.middleware import setup_middleware
from api.routes import admin, auth, conversations, dashboard, dashboard_rollup, reports
from infrastructure.config.config_loader import load_and_configure_business, load_bsc_config

logger = logging.getLogger("m_bird.scheduler")


def _make_incremental_handler(
    messages_days: int | None, backfill_incomplete: bool = False, backfill_metrics: bool = False
):
    """Create an incremental sync handler bound to profile parameters."""

    async def _run():
        from application.use_cases.sync_database import SyncDatabaseUseCase

        try:
            use_case = SyncDatabaseUseCase()
            await use_case.execute(
                full_sync=False,
                sync_messages=messages_days is not None,
                messages_days=messages_days,
                backfill_incomplete=backfill_incomplete,
                backfill_metrics=backfill_metrics,
            )
            from api.sync_utils import refresh_materialized_view

            await refresh_materialized_view()
            logger.info("Sync completed (messages_days=%s, backfill=%s)", messages_days, backfill_incomplete)
        except Exception:
            logger.exception("Sync failed")

    return _run


def _make_full_handler(
    messages_days: int | None,
    backfill_surveys: bool,
    backfill_incomplete: bool = False,
    backfill_metrics: bool = False,
):
    """Create a full sync handler bound to profile parameters."""

    async def _run():
        from application.use_cases.sync_database import SyncDatabaseUseCase

        try:
            use_case = SyncDatabaseUseCase()
            await use_case.execute(
                full_sync=True,
                sync_messages=True,
                messages_days=messages_days,
                backfill_surveys=backfill_surveys,
                backfill_incomplete=backfill_incomplete,
                backfill_metrics=backfill_metrics,
            )
            from api.sync_utils import refresh_materialized_view

            await refresh_materialized_view()
            logger.info(
                "Full sync completed (messages_days=%s, surveys=%s, backfill=%s)",
                messages_days,
                backfill_surveys,
                backfill_incomplete,
            )
        except Exception:
            logger.exception("Full sync failed")

    return _run


scheduler = AsyncIOScheduler()

# Track whether scheduler was auto-started or user-started
_scheduler_started_by_user: bool = False


def scheduler_running() -> bool:
    return scheduler.running


def scheduler_jobs() -> list[dict[str, Any]]:
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
        }
        for job in scheduler.get_jobs()
    ]


def _configure_scheduler_jobs() -> int:
    from infrastructure.config.sync_profiles import get_active_profile

    profile = get_active_profile()
    jobs_registered = 0

    if profile.has_incremental:
        assert profile.incremental_minutes is not None
        handler = _make_incremental_handler(
            messages_days=profile.messages_days,
            backfill_incomplete=True,
            backfill_metrics=profile.backfill_metrics,
        )
        scheduler.add_job(
            handler,
            trigger=IntervalTrigger(minutes=profile.incremental_minutes),
            id="incremental_sync",
            name=f"Sync ({profile.incremental_minutes}min, msgs={profile.messages_days}d)",
            replace_existing=True,
        )
        jobs_registered += 1

    if profile.has_full_sync:
        assert profile.full_sync_hour is not None
        handler = _make_full_handler(
            messages_days=profile.messages_days,
            backfill_surveys=profile.backfill_surveys,
            backfill_incomplete=True,
            backfill_metrics=profile.backfill_metrics,
        )
        full_hour = f"{profile.full_sync_hour:02d}:{profile.full_sync_minute:02d}"
        scheduler.add_job(
            handler,
            trigger=CronTrigger(hour=profile.full_sync_hour, minute=profile.full_sync_minute),
            id="full_sync",
            name=f"Full sync ({full_hour}, messages_days={profile.messages_days})",
            replace_existing=True,
        )
        jobs_registered += 1

    return jobs_registered


def start_scheduler() -> str:
    global _scheduler_started_by_user
    if scheduler.running:
        jobs = scheduler.get_jobs()
        if jobs:
            return f"Scheduler already running ({len(jobs)} jobs)"
        scheduler.remove_all_jobs()
    _configure_scheduler_jobs()
    scheduler.start()
    _scheduler_started_by_user = True
    jobs = scheduler.get_jobs()
    return f"Scheduler started ({len(jobs)} jobs)"


def stop_scheduler() -> str:
    global _scheduler_started_by_user
    if not scheduler.running:
        return "Scheduler already stopped"
    scheduler.shutdown(wait=False)
    _scheduler_started_by_user = False
    return "Scheduler stopped"


async def _init_schema():
    """Create tables + materialized view if they don't exist (idempotent).

    Uses a schema_migrations table to track applied migrations so destructive
    operations (DROP MATERIALIZED VIEW) only run once instead of on every startup.
    """
    from api.dependencies import get_pool

    pool = await get_pool()

    # Ensure migration tracking table exists
    await pool.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version VARCHAR(50) PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    applied_rows = await pool.fetch_all("SELECT version FROM schema_migrations")
    applied = {row["version"] for row in applied_rows}

    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "infrastructure", "database", "migrations")
    for sql_file in (
        "001_initial.sql",
        "002_materialized_view.sql",
        "003_cleanup_unused_columns.sql",
        "004_add_agnt_grp_to_view.sql",
        "005_bsc_manual_values.sql",
        "006_agent_manual_entries.sql",
        "007_users.sql",
        "008_performance_indexes.sql",
        "009_stats_rollups.sql",
        "010_messages_bird_constraint.sql",
        "011_fk_indexes.sql",
    ):
        version = sql_file.replace(".sql", "")
        if version in applied:
            continue
        path = os.path.join(migrations_dir, sql_file)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            sql = f.read()
        try:
            for statement in _split_sql(sql):
                stmt = statement.strip()
                if stmt:
                    await pool.execute(stmt)
            await pool.execute(
                "INSERT INTO schema_migrations (version) VALUES ($1) ON CONFLICT DO NOTHING",
                version,
            )
            logger.info("Applied %s", sql_file)
        except Exception:
            logger.exception("Failed to apply %s", sql_file)


def _split_sql(sql: str) -> list[str]:
    """Split SQL by semicolons, respecting dollar-quoted strings."""
    statements: list[str] = []
    current: list[str] = []
    in_dollar_quote = False
    dollar_tag = ""
    i = 0
    n = len(sql)

    while i < n:
        ch = sql[i]

        if in_dollar_quote:
            current.append(ch)
            if ch == "$":
                end_tag = "$" + dollar_tag + "$"
                tail = "".join(current[-(len(end_tag)) :])
                if tail == end_tag:
                    in_dollar_quote = False
                    dollar_tag = ""
            i += 1
            continue

        if ch == "$":
            j = i + 1
            tag_chars: list[str] = []
            while j < n and sql[j] != "$" and sql[j] != ";":
                tag_chars.append(sql[j])
                j += 1
            if j < n and sql[j] == "$":
                dollar_tag = "".join(tag_chars)
                in_dollar_quote = True
                current.append(sql[i : j + 1])
                i = j + 1
                continue

        if ch == ";":
            statements.append("".join(current))
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    remainder = "".join(current).strip()
    if remainder:
        statements.append(remainder)
    return statements


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    from api.logging_config import setup_logging

    setup_logging()

    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    # Ensure YAML config is loaded BEFORE any endpoint handler runs
    # (FastAPI lifespan can race with uvicorn --reload)
    config_path = os.path.join(os.path.dirname(__file__), "..", "business_config.yaml")
    bsc_path = os.path.join(os.path.dirname(__file__), "..", "business_bsc.yaml")
    load_and_configure_business(config_path)
    load_bsc_config(bsc_path)

    await _init_schema()

    sync_enabled = os.getenv("SYNC_ENABLED", "true").lower() in ("true", "1", "yes")
    if sync_enabled:
        jobs = _configure_scheduler_jobs()
        scheduler.start()
        logger.info("APScheduler auto-started (%d jobs, SYNC_ENABLED=true)", jobs)
    else:
        logger.info("APScheduler paused (SYNC_ENABLED=false) — start via API or set SYNC_ENABLED=true")

    yield

    scheduler.shutdown(wait=False)
    await stop_pool()


def create_app() -> FastAPI:
    # Load .env BEFORE any middleware or config reads os.getenv()
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    app = FastAPI(
        title="MBird Reporting API",
        description="Omnichannel Reporting Tool - API REST",
        version="2.0.0",
        lifespan=lifespan,
    )

    setup_middleware(app)

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
    app.include_router(dashboard_rollup.router, prefix="/api/v1/dashboard", tags=["dashboard-rollup"])
    app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

    return app


app = create_app()
