import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from api.dependencies import stop_pool
from api.middleware import setup_middleware
from api.routes import admin, auth, conversations, dashboard, reports
from infrastructure.config.config_loader import load_and_configure_business, load_bsc_config

logger = logging.getLogger("m_bird.scheduler")


def _make_incremental_handler(messages_days: int | None):
    """Create an incremental sync handler bound to profile parameters."""

    async def _run():
        from application.use_cases.sync_database import SyncDatabaseUseCase

        try:
            use_case = SyncDatabaseUseCase()
            await use_case.execute(
                full_sync=False,
                sync_messages=messages_days is not None,
                messages_days=messages_days,
            )
            from api.sync_utils import refresh_materialized_view

            await refresh_materialized_view()
            logger.info("Sync completed (messages_days=%s)", messages_days)
        except Exception:
            logger.exception("Sync failed")

    return _run


def _make_full_handler(messages_days: int | None, backfill_surveys: bool):
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
            )
            from api.sync_utils import refresh_materialized_view

            await refresh_materialized_view()
            logger.info("Full sync completed (messages_days=%s, surveys=%s)", messages_days, backfill_surveys)
        except Exception:
            logger.exception("Full sync failed")

    return _run


scheduler = AsyncIOScheduler()

# Track whether scheduler was auto-started or user-started
_scheduler_started_by_user: bool = False


def scheduler_running() -> bool:
    return scheduler.running


def scheduler_jobs() -> list[dict[str, object]]:
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
        handler = _make_incremental_handler(messages_days=profile.messages_days)
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
    """Create tables + materialized view if they don't exist (idempotent)."""
    migrations_dir = os.path.join(os.path.dirname(__file__), "..", "infrastructure", "database", "migrations")
    for sql_file in (
        "001_initial.sql",
        "002_materialized_view.sql",
        "003_cleanup_unused_columns.sql",
        "004_add_agnt_grp_to_view.sql",
    ):
        path = os.path.join(migrations_dir, sql_file)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            sql = f.read()
        from api.dependencies import get_pool

        pool = await get_pool()
        try:
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    await pool.execute(stmt)
            logger.info("Applied %s", sql_file)
        except Exception:
            logger.exception("Failed to apply %s", sql_file)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    from api.logging_config import setup_logging

    setup_logging()

    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

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
    app = FastAPI(
        title="MBird Reporting API",
        description="Omnichannel Reporting Tool - API REST",
        version="2.0.0",
        lifespan=lifespan,
    )

    setup_middleware(app)

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
    app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

    return app


app = create_app()
