"""Dashboard Routes with Rollup Support — for large date ranges."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from api.auth import get_current_user
from api.dependencies import get_repository
from api.schemas.dashboard import EvolutionBucket, GranularEvolutionResponse
from application.services.report_aggregator import ReportAggregator
from application.services.rollup_selector import build_rollup_query, select_granularity
from domain.metrics.art import ARTCalculator
from domain.metrics.duration import DurationCalculator
from domain.metrics.frt import FRTCalculator
from infrastructure.database.postgres_connection import PostgresPool

logger = logging.getLogger("api.dashboard_rollup")

router = APIRouter()

MONTH_NAMES = [
    "",
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
]


def _make_aggregator() -> ReportAggregator:
    return ReportAggregator(strategies=[FRTCalculator(), DurationCalculator(), ARTCalculator()])


async def _get_pool() -> PostgresPool:
    from api.dependencies import get_pool

    return await get_pool()


@router.get("/evolution/rollup", response_model=GranularEvolutionResponse)
async def get_evolution_rollup(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    channel: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
) -> GranularEvolutionResponse:
    """Evolution data using pre-aggregated rollup tables for large date ranges.

    Automatically selects the appropriate granularity (daily/weekly/monthly)
    based on the date range size.
    """
    pool = await _get_pool()
    granularity = select_granularity(start_date, end_date)
    query, params = build_rollup_query(granularity, start_date, end_date, channel, department)

    try:
        rows = await pool.fetch_all(query, *params)
    except Exception as e:
        logger.warning(f"Rollup query failed, falling back to raw data: {e}")
        return await _fallback_evolution(start_date, end_date, granularity)

    from datetime import date as _date

    try:
        req_start = _date.fromisoformat(start_date)
        req_end = _date.fromisoformat(end_date)
    except ValueError, TypeError:
        req_start = None
        req_end = None

    detail_map = await _fetch_notes_breakdown(pool, start_date, end_date, granularity, channel, department)

    buckets = []
    for row in rows:
        bucket = row["bucket"]
        if req_start and req_end and hasattr(bucket, "year") and (bucket < req_start or bucket > req_end):
            continue
        label = _format_bucket_label(bucket, granularity)
        bucket_key = bucket.isoformat() if hasattr(bucket, "isoformat") else str(bucket)[:10]
        detail = detail_map.get(bucket_key, {})

        buckets.append(
            EvolutionBucket(
                period_start=str(bucket),
                label=label,
                year=bucket.year if hasattr(bucket, "year") else 0,
                month=bucket.month if hasattr(bucket, "month") else 0,
                total_conversations=int(row.get("total_conversations", 0)),
                nps_score=float(row["nps_score"]) if row.get("nps_score") else None,
                art_avg_minutes=float(row["avg_art"]) if row.get("avg_art") else None,
                sla_compliance_pct=float(row["sla_compliance"]) if row.get("sla_compliance") else None,
                rating_avg=float(row["avg_rating"]) if row.get("avg_rating") else None,
                rated_chats=int(row.get("rated_conversations", 0)),
                nps_rated_chats=int(row.get("nps_rated_conversations", 0)),
                both_rated_chats=0,
                high_notes=detail.get("high_notes", 0),
                low_notes=detail.get("low_notes", 0),
                neutral_notes=detail.get("neutral_notes", 0),
                art_bucket_0_5=0,
                art_bucket_5_10=0,
                art_bucket_10_30=0,
                art_bucket_30_60=0,
                art_bucket_60_120=0,
                art_bucket_120_plus=0,
            )
        )

    return GranularEvolutionResponse(granularity=granularity, buckets=buckets)


async def _fetch_notes_breakdown(
    pool: PostgresPool,
    start_date: str,
    end_date: str,
    granularity: str,
    channel: str | None = None,
    department: str | None = None,
) -> dict[str, dict[str, int]]:
    """Fetch notes breakdown (high/low/neutral) from raw conversations table.

    Uses the same bucket expression as rollup tables for consistent matching.
    """
    if granularity == "monthly":
        bucket_expr = "date_trunc('month', cnvs_created)::date"
    elif granularity == "weekly":
        bucket_expr = "(cnvs_created - ((EXTRACT(DOW FROM cnvs_created)::int + 6) % 7) * INTERVAL '1 day') ::date"
    else:
        bucket_expr = "cnvs_created::date"

    conditions = ["cnvs_created >= $1", "cnvs_created <= $2::timestamp + interval '1 day'"]
    from datetime import date as _date

    try:
        params: list[_date | str] = [_date.fromisoformat(start_date), _date.fromisoformat(end_date)]
    except (ValueError, TypeError):
        params = [start_date, end_date]

    if channel:
        params.append(channel)
        conditions.append(f"cnvs_channel = ${len(params)}")

    if department:
        params.append(department)
        conditions.append(f"cnvs_dept = ${len(params)}")

    where = " AND ".join(conditions)

    sql = f"""
        SELECT
            {bucket_expr} AS bucket,
            COUNT(*) FILTER (WHERE cnvs_rating_agent >= 4) AS high_notes,
            COUNT(*) FILTER (WHERE cnvs_rating_agent <= 2) AS low_notes,
            COUNT(*) FILTER (WHERE cnvs_rating_agent = 3) AS neutral_notes
        FROM conversations
        WHERE {where}
        GROUP BY bucket
        ORDER BY bucket
    """

    try:
        rows = await pool.fetch_all(sql, *params)
        result: dict[str, dict[str, int]] = {}
        for row in rows:
            b = row["bucket"]
            key = b.isoformat() if hasattr(b, "isoformat") else str(b)[:10]
            result[key] = {
                "high_notes": row["high_notes"],
                "low_notes": row["low_notes"],
                "neutral_notes": row["neutral_notes"],
            }
        return result
    except Exception as e:
        logger.warning(f"Notes breakdown query failed: {e}")
        return {}


def _format_bucket_label(bucket: Any, granularity: str) -> str:
    """Format a bucket date into a human-readable label."""
    if hasattr(bucket, "strftime"):
        if granularity == "monthly":
            return f"{MONTH_NAMES[bucket.month]}/{bucket.year}"
        elif granularity == "weekly":
            return str(bucket.strftime("%d/%m"))
        else:
            return str(bucket.strftime("%d/%m"))
    return str(bucket)


async def _fallback_evolution(
    start_date: str,
    end_date: str,
    granularity: str,
) -> GranularEvolutionResponse:
    """Fallback to raw data processing when rollup is not available."""

    repo = await get_repository()
    agg = _make_aggregator()

    raw = await repo.fetch_raw_data_range(start_date, end_date)
    processed = agg.process_all(raw)

    # Group by month/week/day
    from collections import defaultdict

    buckets_map: dict[str, list[Any]] = defaultdict(list)
    for p in processed:
        raw_str = getattr(p, "raw_created", None) or ""
        if raw_str:
            try:
                dt = datetime.strptime(str(raw_str)[:19], "%Y-%m-%d %H:%M:%S")
                if granularity == "monthly":
                    key = f"{dt.year}-{dt.month:02d}"
                elif granularity == "weekly":
                    key = dt.strftime("%Y-W%W")
                else:
                    key = dt.strftime("%Y-%m-%d")
                buckets_map[key].append(p)
            except ValueError, TypeError:
                pass

    buckets = []
    for key in sorted(buckets_map.keys()):
        bucket = buckets_map[key]
        stats = agg.aggregate_statistics(bucket)
        buckets.append(
            EvolutionBucket(
                period_start=key,
                label=key,
                year=0,
                month=0,
                total_conversations=stats.get("total_chats", 0),
                nps_score=stats.get("real_nps"),
                art_avg_minutes=stats.get("avg_art"),
                sla_compliance_pct=stats.get("sla_compliance"),
                rating_avg=stats.get("avg_rating"),
                rated_chats=stats.get("rated_chats", 0),
                nps_rated_chats=stats.get("nps_rated_chats", 0),
                both_rated_chats=stats.get("both_rated_chats", 0),
                high_notes=stats.get("high_notes", 0),
                low_notes=stats.get("low_notes", 0),
                neutral_notes=stats.get("neutral_notes", 0),
                art_bucket_0_5=stats.get("art_bucket_0_5", 0),
                art_bucket_5_10=stats.get("art_bucket_5_10", 0),
                art_bucket_10_30=stats.get("art_bucket_10_30", 0),
                art_bucket_30_60=stats.get("art_bucket_30_60", 0),
                art_bucket_60_120=stats.get("art_bucket_60_120", 0),
                art_bucket_120_plus=stats.get("art_bucket_120_plus", 0),
            )
        )

    return GranularEvolutionResponse(granularity=granularity, buckets=buckets)
