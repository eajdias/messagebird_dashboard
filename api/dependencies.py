from functools import lru_cache

from application.interfaces.repository import ReportRepository
from infrastructure.database.postgres_connection import PostgresPool
from infrastructure.repositories.postgres_report_repository import PostgresReportRepository


@lru_cache
def get_database_url() -> str:
    import os

    return os.getenv("DATABASE_URL", "postgresql://mbird:mbird_dev_2024@localhost:5432/mbird_reports")


_pool: PostgresPool | None = None


async def get_pool() -> PostgresPool:
    global _pool
    if _pool is None:
        pool = PostgresPool(dsn=get_database_url())
        try:
            await pool.start()
        except Exception:
            _pool = None
            raise
        _pool = pool
    return _pool


async def stop_pool():
    global _pool
    if _pool:
        await _pool.stop()
        _pool = None


async def get_repository() -> ReportRepository:
    pool = await get_pool()
    return PostgresReportRepository(pool)
