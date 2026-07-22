"""Dashboard Routes — wired to ReportAggregator + PostgresReportRepository."""

from __future__ import annotations

import calendar
import logging
from collections import Counter
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query

from api.auth import get_current_user
from api.dependencies import get_repository
from api.schemas.dashboard import (
    AgentRankingItem,
    AgentRankingResponse,
    BSCResponse,
    ChannelItem,
    ChannelResponse,
    DashboardSummaryResponse,
    EvolutionBucket,
    EvolutionMonth,
    EvolutionResponse,
    GranularEvolutionResponse,
    KPIItem,
    KPIResponse,
)
from application.interfaces.repository import ReportRepository
from application.services.report_aggregator import ReportAggregator
from domain import constants
from domain.entities.report_data import RawConversationData
from domain.metrics.art import ARTCalculator
from domain.metrics.duration import DurationCalculator
from domain.metrics.frt import FRTCalculator

logger = logging.getLogger("api.dashboard")

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


def _default_date_range() -> tuple[str, str]:
    """Return current month bounds (local time)."""
    now = datetime.now()
    first = f"{now.year}-{now.month:02d}-01"
    _, last_day = calendar.monthrange(now.year, now.month)
    last = f"{now.year}-{now.month:02d}-{last_day}"
    return first, last


def _make_aggregator() -> ReportAggregator:
    return ReportAggregator(strategies=[FRTCalculator(), DurationCalculator(), ARTCalculator()])


async def _fetch_and_process(
    repo: ReportRepository,
    start_date: str,
    end_date: str,
) -> tuple[list[RawConversationData], list[Any]]:
    """Fetch raw data for a date range and process it through the aggregator."""
    raw = await repo.fetch_raw_data_range(start_date, end_date)
    agg = _make_aggregator()
    return raw, agg.process_all(raw)


# ── GET /dashboard/summary ──────────────────────────────────────────────


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    start, end = (start_date, end_date) if start_date and end_date else _default_date_range()
    raw, processed = await _fetch_and_process(repo, start, end)

    agg = _make_aggregator()
    stats = agg.aggregate_statistics(processed)

    # Unique contacts across all conversations
    contacts = Counter(p.contact_id for p in processed if p.contact_id)

    return DashboardSummaryResponse(
        total_conversations=stats.get("total_chats", 0),
        nps_score=stats.get("real_nps"),
        frt_avg_minutes=None,  # FRT requires per-conversation first-response timestamps
        art_avg_minutes=stats.get("avg_art"),
        rating_avg=stats.get("avg_rating"),
        sla_compliance_pct=stats.get("sla_compliance"),
        total_messages=stats.get("total_msgs", 0),
        unique_contacts=len(contacts),
        returning_contacts=stats.get("returners", 0),
    )


# ── GET /dashboard/bsc ──────────────────────────────────────────────────


@router.get("/bsc", response_model=BSCResponse)
async def get_bsc(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    start, end = (start_date, end_date) if start_date and end_date else _default_date_range()
    _, processed = await _fetch_and_process(repo, start, end)

    agg = _make_aggregator()
    dto = agg.aggregate_dashboard(processed, title="BSC", start_date=start, end_date=end)

    return BSCResponse(
        header=dto.bsc_header or [],
        data_t1=dto.bsc_data_t1 or [],
        data_t2=dto.bsc_data_t2 or [],
        kpi_config=dto.bsc_kpi_config,
    )


# ── GET /dashboard/kpis ─────────────────────────────────────────────────


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    dept = department or ""
    kpi_cfg = constants.KPI_CONFIG.get(dept, next(iter(constants.KPI_CONFIG.values()), {}))
    t1_items = kpi_cfg.get("t1", [])

    kpis: list[KPIItem] = []
    for item in t1_items:
        kpis.append(
            KPIItem(
                name=str(item.get("name", "")),
                meta=item.get("meta"),
                peso=int(item.get("peso", 0)),
                tipo=str(item.get("tipo", "")),
            )
        )

    return KPIResponse(department=dept, kpis=kpis)


# ── GET /dashboard/evolution ────────────────────────────────────────────


@router.get("/evolution", response_model=EvolutionResponse)
async def get_evolution(
    months: int = Query(12, ge=1, le=24),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    import asyncio

    now = datetime.now()
    agg = _make_aggregator()

    async def _month_stats(m: int, y: int):
        _, last_day = calendar.monthrange(y, m)
        start = f"{y}-{m:02d}-01"
        end = f"{y}-{m:02d}-{last_day}"
        _, processed = await _fetch_and_process(repo, start, end)
        return agg.aggregate_statistics(processed)

    # Build month list (oldest to newest)
    month_list: list[tuple[int, int]] = []
    for i in range(months - 1, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        month_list.append((m, y))

    # Fetch all months in parallel (cache hits are instant)
    results = await asyncio.gather(*[_month_stats(m, y) for m, y in month_list])

    evolution: list[EvolutionMonth] = []
    for (m, y), stats in zip(month_list, results, strict=True):
        evolution.append(
            EvolutionMonth(
                year=y,
                month=m,
                label=f"{MONTH_NAMES[m]}/{y}",
                total_conversations=stats.get("total_chats", 0),
                nps_score=stats.get("real_nps"),
                art_avg_minutes=stats.get("avg_art"),
                frt_avg_minutes=None,
                sla_compliance_pct=stats.get("sla_compliance"),
                rating_avg=stats.get("avg_rating"),
            )
        )

    return EvolutionResponse(evolution=evolution)


# ── GET /dashboard/evolution/granular ───────────────────────────────────


@router.get("/evolution/granular", response_model=GranularEvolutionResponse)
async def get_evolution_granular(
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    count: int = Query(12, ge=1, le=90),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Evolution data with selectable granularity (day, week, month).

    - `day`: last `count` days (max 90)
    - `week`: last `count` ISO weeks (max 90)
    - `month`: last `count` months (max 24)
    """
    import asyncio
    from datetime import date, timedelta

    now = datetime.now()
    today = now.date()
    agg = _make_aggregator()

    if granularity == "month":
        month_list: list[tuple[str, str, int, int, str]] = []
        for i in range(count - 1, -1, -1):
            m = now.month - i
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            start = f"{y}-{m:02d}-01"
            _, last_day = calendar.monthrange(y, m)
            end = f"{y}-{m:02d}-{last_day}"
            label = f"{MONTH_NAMES[m]}/{y}"
            month_list.append((start, end, y, m, label))

        async def _stats(start: str, end: str):
            _, processed = await _fetch_and_process(repo, start, end)
            return agg.aggregate_statistics(processed)

        results = await asyncio.gather(*[_stats(s, e) for s, e, _, _, _ in month_list])

        buckets: list[EvolutionBucket] = []
        for (start, _, y, m, label), stats in zip(month_list, results, strict=True):
            buckets.append(
                EvolutionBucket(
                    period_start=start,
                    label=label,
                    year=y,
                    month=m,
                    total_conversations=stats.get("total_chats", 0),
                    nps_score=stats.get("real_nps"),
                    art_avg_minutes=stats.get("avg_art"),
                    sla_compliance_pct=stats.get("sla_compliance"),
                    rating_avg=stats.get("avg_rating"),
                )
            )
        return GranularEvolutionResponse(granularity=granularity, buckets=buckets)

    if granularity == "day":
        day_list: list[tuple[str, str, str]] = []
        for i in range(count - 1, -1, -1):
            d = today - timedelta(days=i)
            iso = d.isoformat()
            day_list.append((iso, iso, d.strftime("%d/%m")))

        async def _day_stats(d_iso: str):
            _, processed = await _fetch_and_process(repo, d_iso, d_iso)
            return agg.aggregate_statistics(processed)

        results = await asyncio.gather(*[_day_stats(d) for d, _, _ in day_list])

        buckets = []
        for (start, _, label), stats in zip(day_list, results, strict=True):
            buckets.append(
                EvolutionBucket(
                    period_start=start,
                    label=label,
                    total_conversations=stats.get("total_chats", 0),
                    nps_score=stats.get("real_nps"),
                    art_avg_minutes=stats.get("avg_art"),
                    sla_compliance_pct=stats.get("sla_compliance"),
                    rating_avg=stats.get("avg_rating"),
                )
            )
        return GranularEvolutionResponse(granularity=granularity, buckets=buckets)

    # week
    week_list: list[tuple[date, date, str]] = []
    for i in range(count - 1, -1, -1):
        week_end = today - timedelta(days=i * 7)
        week_start = week_end - timedelta(days=6)
        label = f"{week_start.strftime('%d/%m')}–{week_end.strftime('%d/%m')}"
        week_list.append((week_start, week_end, label))

    async def _week_stats(start_d: date, end_d: date):
        start = start_d.isoformat()
        end = end_d.isoformat()
        _, processed = await _fetch_and_process(repo, start, end)
        return agg.aggregate_statistics(processed)

    results = await asyncio.gather(*[_week_stats(s, e) for s, e, _ in week_list])

    buckets = []
    for (start_d, _, label), stats in zip(week_list, results, strict=True):
        buckets.append(
            EvolutionBucket(
                period_start=start_d.isoformat(),
                label=label,
                total_conversations=stats.get("total_chats", 0),
                nps_score=stats.get("real_nps"),
                art_avg_minutes=stats.get("avg_art"),
                sla_compliance_pct=stats.get("sla_compliance"),
                rating_avg=stats.get("avg_rating"),
            )
        )
    return GranularEvolutionResponse(granularity=granularity, buckets=buckets)


# ── GET /dashboard/agents ───────────────────────────────────────────────


@router.get("/agents", response_model=AgentRankingResponse)
async def get_agents_ranking(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    start, end = (start_date, end_date) if start_date and end_date else _default_date_range()
    _, processed = await _fetch_and_process(repo, start, end)

    # Group by agent
    agent_map: dict[str, list[Any]] = {}
    for p in processed:
        agent_map.setdefault(p.agent, []).append(p)

    agg = _make_aggregator()
    items: list[AgentRankingItem] = []

    for agent, p_list in agent_map.items():
        stats = agg.aggregate_statistics(p_list)
        depts = Counter(p.dept_label for p in p_list)
        main_dept = depts.most_common(1)[0][0] if depts else "N/A"

        items.append(
            AgentRankingItem(
                agent_name=agent,
                department=main_dept,
                group=constants.resolve_conversation_group(agent, main_dept),
                total_chats=stats.get("total_chats", 0),
                nps_score=stats.get("real_nps"),
                rating_avg=stats.get("avg_rating"),
                art_avg_minutes=stats.get("avg_art"),
                sla_compliance_pct=stats.get("sla_compliance"),
                total_messages=stats.get("total_msgs", 0),
            )
        )

    items.sort(key=lambda x: x.total_messages, reverse=True)
    for idx, item in enumerate(items):
        item.rank = idx + 1

    return AgentRankingResponse(agents=items)


# ── GET /dashboard/channels ─────────────────────────────────────────────


@router.get("/channels", response_model=ChannelResponse)
async def get_channels(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    start, end = (start_date, end_date) if start_date and end_date else _default_date_range()
    raw, _ = await _fetch_and_process(repo, start, end)

    # Aggregate by channel from raw metadata
    channel_map: dict[str, dict[str, Any]] = {}
    for conv in raw:
        ch_id = conv.metadata.get("channel") or "unknown"
        ch_name = conv.metadata.get("channel_name") or ch_id
        if ch_id not in channel_map:
            channel_map[ch_id] = {
                "channel_id": ch_id,
                "channel_name": ch_name,
                "convs": [],
                "total_msgs": 0,
            }
        channel_map[ch_id]["convs"].append(conv)
        channel_map[ch_id]["total_msgs"] += len(conv.msgs)

    items: list[ChannelItem] = []
    for ch_id, ch_data in channel_map.items():
        convs = ch_data["convs"]
        ratings = [c.rating for c in convs if c.rating is not None]
        nps_scores = [c.nps for c in convs if c.nps is not None]

        from domain.services.metrics_calculator import MetricsCalculator

        items.append(
            ChannelItem(
                channel_id=ch_id,
                channel_name=ch_data["channel_name"],
                total_conversations=len(convs),
                total_messages=ch_data["total_msgs"],
                nps_score=MetricsCalculator.calculate_nps(nps_scores),
                rating_avg=MetricsCalculator.calculate_rating_average(ratings),
            )
        )

    items.sort(key=lambda x: x.total_conversations, reverse=True)
    return ChannelResponse(channels=items)
