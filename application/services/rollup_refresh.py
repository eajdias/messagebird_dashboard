"""Rollup refresh service — periodically refreshes stats rollup tables."""

from __future__ import annotations

import logging

from infrastructure.database.postgres_connection import PostgresPool

logger = logging.getLogger("rollup_refresh")


async def refresh_rollups(pool: PostgresPool) -> None:
    """Refresh all stats rollup tables and materialized views."""
    try:
        await pool.execute("SELECT refresh_stats_rollups()")
        logger.info("Rollup tables refreshed successfully")
    except Exception as e:
        logger.error(f"Failed to refresh rollups: {e}")
        raise


async def get_last_refresh(pool: PostgresPool) -> str | None:
    """Get the timestamp of the last rollup refresh."""
    try:
        result = await pool.fetch_one("SELECT created_at FROM stats_monthly ORDER BY created_at DESC LIMIT 1")
        return str(result["created_at"]) if result else None
    except Exception:
        return None
