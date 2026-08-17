"""Shared sync utilities for the API layer."""

import logging

logger = logging.getLogger("m_bird.scheduler")


async def refresh_materialized_view():
    """Refresh materialized view, rollup tables, and invalidate cache after sync."""
    from api.dependencies import get_pool
    from infrastructure.cache import repo_cache
    from infrastructure.database import queries_pg

    try:
        pool = await get_pool()
        await pool.execute(queries_pg.REFRESH_MV)
        await repo_cache.clear()
        logger.info("Materialized view refreshed, cache cleared")
    except Exception:
        logger.exception("MV refresh failed")

    try:
        pool = await get_pool()
        await pool.execute("SELECT refresh_stats_rollups()")
        logger.info("Stats rollup tables refreshed")
    except Exception:
        logger.exception("Rollup refresh failed")
