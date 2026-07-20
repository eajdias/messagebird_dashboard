import logging
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


async def _run_incremental_sync():
    """Background job: incremental sync (contacts + conversations, last 60 min)."""
    from application.use_cases.sync_database import SyncDatabaseUseCase

    try:
        use_case = SyncDatabaseUseCase()
        await use_case.execute(full_sync=False, sync_messages=False, lookback_minutes=60)
        logger.info("Incremental sync completed successfully")
    except Exception:
        logger.exception("Incremental sync failed")


async def _run_full_sync():
    """Background job: full sync with messages (daily at 3:00 AM)."""
    from application.use_cases.sync_database import SyncDatabaseUseCase

    try:
        use_case = SyncDatabaseUseCase()
        await use_case.execute(full_sync=True, sync_messages=True, backfill_surveys=True)
        logger.info("Full sync completed successfully")
    except Exception:
        logger.exception("Full sync failed")


scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    import os

    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

    config_path = os.path.join(os.path.dirname(__file__), "..", "business_config.yaml")
    bsc_path = os.path.join(os.path.dirname(__file__), "..", "business_bsc.yaml")
    load_and_configure_business(config_path)
    load_bsc_config(bsc_path)

    scheduler.add_job(
        _run_incremental_sync,
        trigger=IntervalTrigger(minutes=15),
        id="incremental_sync",
        name="Incremental sync (contacts + conversations)",
        replace_existing=True,
    )
    scheduler.add_job(
        _run_full_sync,
        trigger=CronTrigger(hour=3, minute=0),
        id="full_sync",
        name="Full sync with messages (daily 3:00 AM)",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started: incremental every 15min, full daily 03:00")

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
