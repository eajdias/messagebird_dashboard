"""Rollup selector — determines the appropriate aggregation level based on date range."""

from __future__ import annotations

from datetime import date, timedelta


def select_granularity(start_date: str, end_date: str) -> str:
    """Select the appropriate rollup granularity based on the date range.

    Rules:
        - Range > 2 years → monthly
        - Range > 14 days → weekly
        - Range ≤ 14 days → daily
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError, TypeError:
        return "monthly"

    days = (end - start).days

    if days > 730:  # > 2 years
        return "monthly"
    elif days > 14:  # > 14 days
        return "weekly"
    else:
        return "daily"


def _snap_week_start(d: date) -> date:
    """Snap a date to the start of its ISO week (Monday)."""
    return d - timedelta(days=d.weekday())


def _snap_week_end(d: date) -> date:
    """Snap a date to the end of its ISO week (Sunday)."""
    return d + timedelta(days=6 - d.weekday())


def get_rollup_table(granularity: str) -> str:
    """Return the rollup table name for the given granularity."""
    tables = {
        "daily": "stats_daily",
        "weekly": "stats_weekly",
        "monthly": "stats_monthly",
    }
    return tables.get(granularity, "stats_monthly")


def get_bucket_column(granularity: str) -> str:
    """Return the bucket column name for the given granularity."""
    columns = {
        "daily": "bucket_day",
        "weekly": "bucket_week",
        "monthly": "bucket_month",
    }
    return columns.get(granularity, "bucket_month")


def build_rollup_query(
    granularity: str,
    start_date: str,
    end_date: str,
    channel: str | None = None,
    department: str | None = None,
) -> tuple[str, list[date | str]]:
    """Build a SQL query to fetch aggregated stats from rollup tables.

    For weekly granularity, expands the query range to cover full ISO weeks
    at the boundaries, ensuring no data is lost at the edges.

    Returns (query, params).
    """
    table = get_rollup_table(granularity)
    bucket_col = get_bucket_column(granularity)

    if granularity == "weekly":
        try:
            start = date.fromisoformat(start_date)
            end = date.fromisoformat(end_date)
            query_start: date | str = _snap_week_start(start)
            query_end: date | str = _snap_week_end(end)
        except (ValueError, TypeError):
            query_start = start_date
            query_end = end_date
    else:
        try:
            query_start = date.fromisoformat(start_date)
            query_end = date.fromisoformat(end_date)
        except (ValueError, TypeError):
            query_start = start_date
            query_end = end_date

    conditions = [f"{bucket_col} >= $1", f"{bucket_col} <= $2"]
    params: list[date | str] = [query_start, query_end]

    if channel:
        params.append(channel)
        conditions.append(f"channel = ${len(params)}")

    if department:
        params.append(department)
        conditions.append(f"dept = ${len(params)}")

    where_clause = " AND ".join(conditions)

    query = f"""
        SELECT
            {bucket_col} AS bucket,
            SUM(total_conversations) AS total_conversations,
            SUM(total_messages) AS total_messages,
            CASE WHEN SUM(rated_conversations) > 0
                THEN ROUND(SUM(avg_rating * rated_conversations) / SUM(rated_conversations), 2)
                ELSE NULL END AS avg_rating,
            SUM(rated_conversations) AS rated_conversations,
            CASE WHEN SUM(nps_rated_conversations) > 0
                THEN ROUND(SUM(nps_score * nps_rated_conversations) / SUM(nps_rated_conversations), 1)
                ELSE NULL END AS nps_score,
            SUM(nps_rated_conversations) AS nps_rated_conversations,
            CASE WHEN SUM(art_conversations) > 0
                THEN ROUND(SUM(avg_art * art_conversations) / SUM(art_conversations), 2)
                ELSE NULL END AS avg_art,
            SUM(art_conversations) AS art_conversations,
            CASE WHEN SUM(art_conversations) > 0
                THEN ROUND(SUM(sla_compliance * art_conversations) / SUM(art_conversations), 2)
                ELSE NULL END AS sla_compliance,
            SUM(returners) AS returners,
            SUM(unique_contacts) AS unique_contacts
        FROM {table}
        WHERE {where_clause}
        GROUP BY {bucket_col}
        ORDER BY {bucket_col}
    """

    return query, params
