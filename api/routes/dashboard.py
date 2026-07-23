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
    AgentRow,
    AgentsResponse,
    ARTDistributionBucket,
    ARTDistributionResponse,
    BSCResponse,
    ChannelItem,
    ChannelResponse,
    CountedItem,
    DashboardSummaryResponse,
    DepartmentRow,
    DepartmentsResponse,
    DOWResponse,
    EvolutionBucket,
    EvolutionMonth,
    EvolutionResponse,
    ExecutiveBSCResponse,
    ExecutiveMeta,
    GranularEvolutionResponse,
    HeatmapCell,
    HeatmapResponse,
    KPIItem,
    KPIResponse,
    MotivesResponse,
    NPSBreakdown,
    OccurrencesResponse,
    QualityDistribution,
    QualityResponse,
    ReturnerBucket,
    ReturnersResponse,
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
                    rated_chats=stats.get("rated_chats", 0),
                    nps_rated_chats=stats.get("nps_rated_chats", 0),
                    high_notes=stats.get("high_notes", 0),
                    low_notes=stats.get("low_notes", 0),
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
                    rated_chats=stats.get("rated_chats", 0),
                    nps_rated_chats=stats.get("nps_rated_chats", 0),
                    high_notes=stats.get("high_notes", 0),
                    low_notes=stats.get("low_notes", 0),
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
                rated_chats=stats.get("rated_chats", 0),
                nps_rated_chats=stats.get("nps_rated_chats", 0),
                high_notes=stats.get("high_notes", 0),
                low_notes=stats.get("low_notes", 0),
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


# ── Executive Dashboard (granular endpoints, period-driven) ────────────────


def _parse_agent_ids(agent_ids: str | None) -> set[str]:
    """Parse `?agent_ids=alice&agent_ids=bob` or `?agent_ids=alice,bob`."""
    if not agent_ids:
        return set()
    return {a.strip() for a in agent_ids.split(",") if a.strip()}


def _granularity_window(granularity: str, custom_start: str | None, custom_end: str | None) -> tuple[str, str]:
    """Return (start_date, end_date) ISO strings for the granularity window.

    - `day`:   last 1 day (today)
    - `week`:  last 7 days
    - `month`: last 30 days
    - Custom: use provided range if any
    """
    if custom_start and custom_end:
        return custom_start, custom_end
    from datetime import date, timedelta

    today = date.today()
    if granularity == "day":
        return today.isoformat(), today.isoformat()
    if granularity == "week":
        return (today - timedelta(days=6)).isoformat(), today.isoformat()
    return (today - timedelta(days=29)).isoformat(), today.isoformat()


def _filter_processed(
    processed: list[Any],
    agent_ids: set[str],
    group: str | None,
    department: str | None = None,
) -> list[Any]:
    """Filter processed data by agent_ids and/or group (sector) and/or department."""
    out = processed
    if department:
        out = [p for p in out if p.dept_label == department or constants.get_agent_group(p.agent) == department]
    elif group:
        out = [p for p in out if constants.resolve_conversation_group(p.agent, p.dept_label) == group]
    if agent_ids:
        out = [p for p in out if p.agent in agent_ids]
    return out


def _pct(part: int, total: int) -> float:
    return round(part / total * 100, 2) if total > 0 else 0.0


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


async def _load_executive_processed(
    repo: ReportRepository,
    start_date: str,
    end_date: str,
    agent_ids: set[str],
    group: str | None,
    department: str | None = None,
) -> list[Any]:
    """Fetch + process + filter for executive endpoints."""
    raw, processed = await _fetch_and_process(repo, start_date, end_date)
    return _filter_processed(processed, agent_ids, group, department)


@router.get("/executive/quality", response_model=QualityResponse)
async def get_executive_quality(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None, description="Comma-separated agent names"),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Quality overview: rating distribution (1-5), NPS score distribution (1-10), NPS breakdown."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    from application.services.sub_aggregators import RatingAggregator

    dist = RatingAggregator().aggregate_distributions(processed)

    # Rating 1-5
    rating_counts = dist.get("rating_distribution", {})
    rating_total = sum(int(rating_counts.get(str(i), 0)) for i in range(1, 6))

    # NPS 1-10 (manual — the aggregator returns {promoters, passives, detractors}, not 1-10)
    nps_raw: dict[str, int] = {str(i): 0 for i in range(1, 11)}
    for p in processed:
        if p.nps is not None and 1 <= p.nps <= 10:
            nps_raw[str(int(p.nps))] += 1
    nps_total = sum(nps_raw.values())

    # NPS breakdown (from aggregator distribution)
    nps_dist = dist.get("nps_distribution", {})
    promoters = int(nps_dist.get("promoters", 0))
    neutrals = int(nps_dist.get("passives", 0))
    detractors = int(nps_dist.get("detractors", 0))

    from domain.services.metrics_calculator import MetricsCalculator

    return QualityResponse(
        rating=QualityDistribution(
            counts={str(i): int(rating_counts.get(str(i), 0)) for i in range(1, 6)},
            total=rating_total,
        ),
        nps_score=QualityDistribution(
            counts=nps_raw,
            total=nps_total,
        ),
        nps_breakdown=NPSBreakdown(
            promoters=promoters,
            neutrals=neutrals,
            detractors=detractors,
            total=promoters + neutrals + detractors,
            real_nps=MetricsCalculator.calculate_nps([p.nps for p in processed if p.nps is not None]),
        ),
    )


@router.get("/executive/heatmap", response_model=HeatmapResponse)
async def get_executive_heatmap(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Heatmap of conversations by weekday (0=Mon..6=Sun) × hour (0..23)."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    from application.services.sub_aggregators import TemporalAggregator

    raw_cells = TemporalAggregator().aggregate_heatmap(processed)
    cells = [HeatmapCell(day=int(c["day"]), hour=int(c["hour"]), value=int(c["value"])) for c in raw_cells]
    return HeatmapResponse(
        cells=cells,
        max_value=max((c.value for c in cells), default=0),
        total=sum(c.value for c in cells),
    )


@router.get("/executive/motives", response_model=MotivesResponse)
async def get_executive_motives(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Top motivos de contato no período."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    from application.services.sub_aggregators import TopicAggregator

    raw = TopicAggregator().aggregate_reasons(processed)
    total = sum(int(r["value"]) for r in raw)
    items = [
        CountedItem(
            label=str(r["label"]),
            value=int(r["value"]),
            pct=_pct(int(r["value"]), total),
        )
        for r in raw[:limit]
    ]
    return MotivesResponse(items=items, total=total)


@router.get("/executive/occurrences", response_model=OccurrencesResponse)
async def get_executive_occurrences(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Top ocorrências no período."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    from application.services.sub_aggregators import TopicAggregator

    raw = TopicAggregator().aggregate_occurrences(processed)
    total = sum(int(r["value"]) for r in raw)
    items = [
        CountedItem(
            label=str(r["label"]),
            value=int(r["value"]),
            pct=_pct(int(r["value"]), total),
        )
        for r in raw[:limit]
    ]
    return OccurrencesResponse(items=items, total=total)


@router.get("/executive/dow", response_model=DOWResponse)
async def get_executive_dow(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Distribuição por dia da semana no período."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    from application.services.sub_aggregators import TemporalAggregator

    raw = TemporalAggregator().aggregate_dow(processed)
    total = sum(int(r["value"]) for r in raw)
    items = [
        CountedItem(
            label=str(r["day"]),
            value=int(r["value"]),
            pct=_pct(int(r["value"]), total),
        )
        for r in raw
    ]
    return DOWResponse(items=items, total=total, days=_dow_labels())


def _dow_labels() -> list[str]:
    return ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


@router.get("/executive/departments", response_model=DepartmentsResponse)
async def get_executive_departments(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Breakdown por departamento no período (sem filtro de grupo, sempre global)."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    dept_map: dict[str, list[Any]] = {}
    for p in processed:
        dept_map.setdefault(p.dept_label or "N/A", []).append(p)

    total_chats = len(processed)
    from application.services.report_aggregator import ReportAggregator

    agg = ReportAggregator()
    items: list[DepartmentRow] = []
    for dept, plist in sorted(dept_map.items(), key=lambda kv: -len(kv[1])):
        stats = agg.aggregate_statistics(plist)
        items.append(
            DepartmentRow(
                name=dept,
                chats=stats.get("total_chats", 0),
                pct_total=_pct(stats.get("total_chats", 0), total_chats),
                art_avg=stats.get("avg_art"),
                sla_pct=stats.get("sla_compliance"),
                returners=stats.get("returners", 0),
                pct_returning=_pct(stats.get("returners", 0), stats.get("unique_clients", 0)),
                avg_rating=stats.get("avg_rating"),
                nps_real=stats.get("real_nps"),
            )
        )
    return DepartmentsResponse(items=items, total_chats=total_chats)


@router.get("/executive/agents", response_model=AgentsResponse)
async def get_executive_agents(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Breakdown por agente no período (rating + NPS por agente)."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    agent_map: dict[str, list[Any]] = {}
    for p in processed:
        agent_map.setdefault(p.agent, []).append(p)

    from application.services.report_aggregator import ReportAggregator
    from application.services.sub_aggregators import RatingAggregator

    agg = ReportAggregator()
    rating_agg = RatingAggregator()
    items: list[AgentRow] = []
    for agent, plist in sorted(agent_map.items(), key=lambda kv: -len(kv[1])):
        stats = agg.aggregate_statistics(plist)
        depts = Counter(p.dept_label for p in plist)
        main_dept = depts.most_common(1)[0][0] if depts else "N/A"
        dist = rating_agg.aggregate_distributions(plist)

        nps_scores = [p.nps for p in plist if p.nps is not None]
        nps_dist: dict[str, int] = {str(i): 0 for i in range(1, 11)}
        for n in nps_scores:
            key = str(int(n))
            if key in nps_dist:
                nps_dist[key] += 1

        arts = [p.art_min for p in plist if isinstance(p.art_min, (int, float)) and p.art_min > 0]
        total_arts = len(arts)
        good_art = sum(1 for a in arts if a <= 10)
        bad_art = sum(1 for a in arts if a >= 15)

        items.append(
            AgentRow(
                name=agent,
                department=main_dept,
                chats=stats.get("total_chats", 0),
                total_messages=stats.get("total_msgs", 0),
                art_avg=stats.get("avg_art"),
                sla_pct=stats.get("sla_compliance"),
                real_nps=stats.get("real_nps"),
                avg_rating=stats.get("avg_rating"),
                compliments=stats.get("compliments", 0),
                negatives=stats.get("negatives", 0),
                returners=stats.get("returners", 0),
                unique_contacts=stats.get("unique_clients", 0),
                rating_distribution={
                    str(i): int(dist.get("rating_distribution", {}).get(str(i), 0)) for i in range(1, 6)
                },
                nps_score_distribution=nps_dist,
                good_art_chats=good_art,
                bad_art_chats=bad_art,
                total_art_chats=total_arts,
            )
        )
    return AgentsResponse(
        items=items,
        total_chats=sum(c.chats for c in items),
    )


@router.get("/executive/bsc", response_model=ExecutiveBSCResponse)
async def get_executive_bsc(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    group: str = Query("Suporte Tecnico"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """BSC scorecard (T1/T2) para o grupo (sector) — apenas 'Suporte Tecnico' tem config."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, group)

    from application.services.report_aggregator import ReportAggregator

    agg = ReportAggregator()
    dto = agg.aggregate_dashboard(processed, title=f"BSC {group}", start_date=s, end_date=e)
    return ExecutiveBSCResponse(
        group=group,
        header=dto.bsc_header or [],
        data_t1=dto.bsc_data_t1 or [],
        data_t2=dto.bsc_data_t2 or [],
        kpi_config=dto.bsc_kpi_config,
        total_chats=len(processed),
    )


@router.get("/executive/meta", response_model=ExecutiveMeta)
async def get_executive_meta(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    group: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Metadata for current executive view: period, total counts, filters."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)
    return ExecutiveMeta(
        start_date=s,
        end_date=e,
        granularity=granularity,
        agent_ids=sorted(aid),
        group=group,
        total_chats=len(processed),
        total_messages=sum(p.msg_count for p in processed),
    )


@router.get("/executive/art-distribution", response_model=ARTDistributionResponse)
async def get_executive_art_distribution(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """ART distribution: conversations grouped by response time buckets."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    buckets_def = [
        ("≤ 3 min", lambda a: a is not None and a <= 3),
        ("3 - 5 min", lambda a: a is not None and 3 < a <= 5),
        ("5 - 10 min", lambda a: a is not None and 5 < a <= 10),
        ("10 - 15 min", lambda a: a is not None and 10 < a <= 15),
        ("> 15 min", lambda a: a is not None and a > 15),
        ("Sem resposta", lambda a: a is None),
    ]

    buckets = []
    for label, pred in buckets_def:
        count = sum(1 for p in processed if pred(p.art_min))
        buckets.append(
            ARTDistributionBucket(
                label=label,
                count=count,
                pct=_pct(count, len(processed)),
            )
        )

    return ARTDistributionResponse(
        buckets=buckets,
        total=len(processed),
        total_messages=sum(p.msg_count for p in processed),
    )


@router.get("/executive/returners", response_model=ReturnersResponse)
async def get_executive_returners(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    agent_ids: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Returning-customer frequency: per-client with same-day dedup + outlier capping."""
    s, e = _granularity_window(granularity, start_date, end_date)
    aid = _parse_agent_ids(agent_ids)
    processed = await _load_executive_processed(repo, s, e, aid, None, department)

    total_chats = len(processed)

    contact_days: dict[int, set[str]] = {}
    for p in processed:
        if p.contact_id:
            day = p.raw_created[:10]
            contact_days.setdefault(p.contact_id, set()).add(day)

    effective: dict[int, int] = {}
    for cid, days in contact_days.items():
        effective[cid] = min(len(days), 5)

    unique = len(effective)
    returners = sum(1 for v in effective.values() if v > 1)
    pct_returning = _pct(returners, unique)

    returner_contacts = {cid for cid, v in effective.items() if v > 1}
    returner_chats = sum(1 for p in processed if p.contact_id and p.contact_id in returner_contacts)

    freq = Counter(v for cid, v in effective.items() if v > 1)

    buckets = [
        ReturnerBucket(label="2 visitas", count=freq.get(2, 0), pct=_pct(freq.get(2, 0), returners)),
        ReturnerBucket(label="3 visitas", count=freq.get(3, 0), pct=_pct(freq.get(3, 0), returners)),
        ReturnerBucket(
            label="4-5 visitas",
            count=freq.get(4, 0) + freq.get(5, 0),
            pct=_pct(freq.get(4, 0) + freq.get(5, 0), returners),
        ),
    ]

    return ReturnersResponse(
        buckets=buckets,
        total_unique=unique,
        total_returners=returners,
        pct_returning=pct_returning,
        total_chats=total_chats,
        returner_chats=returner_chats,
    )
