"""Dashboard Routes — wired to ReportAggregator + PostgresReportRepository."""

from __future__ import annotations

import asyncio
import calendar
import logging
from collections import Counter
from datetime import date, datetime, timedelta
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
    BSCAgentValue,
    BSCMetricRow,
    BSCResponse,
    BSCScorecardCategory,
    BSCScorecardResponse,
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
from application.services.bsc_kpi import compute_kpi_score
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
    """Return billing period: 25th of previous month → 25th of current month.
    If today is before the 25th, both dates shift one month back."""
    now = datetime.now()
    if now.day >= 25:
        end_year, end_month = now.year, now.month
    else:
        end_month = now.month - 1
        end_year = now.year
        if end_month <= 0:
            end_month += 12
            end_year -= 1

    start_month = end_month - 1
    start_year = end_year
    if start_month <= 0:
        start_month += 12
        start_year -= 1

    return f"{start_year}-{start_month:02d}-25", f"{end_year}-{end_month:02d}-25"


def _make_aggregator() -> ReportAggregator:
    return ReportAggregator(strategies=[FRTCalculator(), DurationCalculator(), ARTCalculator()])


_fetch_pending: dict[str, asyncio.Task] = {}


async def _fetch_and_process(
    repo: ReportRepository,
    start_date: str,
    end_date: str,
) -> tuple[list[RawConversationData], list[Any]]:
    """Fetch raw data for a date range and process it through the aggregator.

    Uses request coalescing: when multiple endpoints request the same data
    simultaneously, only one computes it and the others await the result.
    """
    from infrastructure.cache import processed_cache as _pc

    cache_key = f"proc:{start_date}:{end_date}"
    cached = await _pc.get(cache_key)
    if cached is not None:
        return cached

    if cache_key in _fetch_pending:
        try:
            return await _fetch_pending[cache_key]
        except Exception:
            pass

    async def _compute():
        try:
            raw = await repo.fetch_raw_data_range(start_date, end_date)
            agg = _make_aggregator()
            processed = await asyncio.to_thread(agg.process_all, raw)
            result = (raw, processed)
            await _pc.set(cache_key, result)
            return result
        finally:
            _fetch_pending.pop(cache_key, None)

    task = asyncio.ensure_future(_compute())
    _fetch_pending[cache_key] = task
    return await task


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


# ── GET /dashboard/bsc/scorecard ────────────────────────────────────────


@router.get("/bsc/scorecard", response_model=BSCScorecardResponse)
async def get_bsc_scorecard(
    department: str = Query(...),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Structured BSC data with per-agent metrics and KPI scores.

    Returns empty categories with has_config=False when:
    - department is empty (no filter selected)
    - department has no BSC config in business_bsc.yaml
    """
    dept = department.strip()
    if not dept:
        return BSCScorecardResponse(
            department="",
            start_date=start_date or "",
            end_date=end_date or "",
            has_config=False,
        )

    kpi_cfg = constants.KPI_CONFIG.get(dept)
    if not kpi_cfg:
        return BSCScorecardResponse(
            department=dept,
            start_date=start_date or "",
            end_date=end_date or "",
            has_config=False,
        )

    start, end = (start_date, end_date) if start_date and end_date else _default_date_range()
    _, processed = await _fetch_and_process(repo, start, end)

    processed = _filter_processed(processed, set(), None, dept)

    # Build agent map — only agents whose group matches the department
    agent_map: dict[str, list] = {}
    for p in processed:
        if constants.get_agent_group(p.agent) == dept:
            agent_map.setdefault(p.agent, []).append(p)

    agents = sorted(agent_map.keys())

    def _pct_compliments(agent_name):
        p_list = agent_map.get(agent_name, [])
        elogios = sum(1 for p in p_list if p.rating is not None and p.rating >= 4)
        if not p_list:
            return None
        return round(elogios / len(p_list) * 100, 1)

    def _pct_negatives(agent_name):
        p_list = agent_map.get(agent_name, [])
        ratings = [p.rating for p in p_list if p.rating is not None]
        neg = sum(1 for r in ratings if r <= 2)
        if not ratings:
            return None
        return round(neg / len(ratings) * 100, 1)

    def _nps_score(agent_name):
        p_list = agent_map.get(agent_name, [])
        nps_scores = [p.nps for p in p_list if p.nps is not None]
        from domain.services.metrics_calculator import MetricsCalculator

        return MetricsCalculator.calculate_nps(nps_scores)

    def _count(agent_name):
        return len(agent_map.get(agent_name, []))

    # Auto-compute map
    _auto_computers = {
        "Elogios de atendimento / Feedback": _pct_compliments,
        "NPS (Net Promoter Score)": _nps_score,
        "Feedback Negativo (Penalidade)": _pct_negatives,
        "Atendimentos Finalizados": _count,
    }

    # Get manual values from DB (aggregated by date range)
    from api.dependencies import get_pool

    pool = await get_pool()
    parsed_start = date.fromisoformat(start)
    parsed_end = date.fromisoformat(end)
    manual_rows = await pool.fetch_all(
        "SELECT agent_name, metric_name, SUM(value) as value FROM agent_manual_entries "
        "WHERE department = $1 AND entry_date >= $2 AND entry_date <= $3 "
        "GROUP BY agent_name, metric_name",
        dept,
        parsed_start,
        parsed_end,
    )
    manual_map: dict[str, dict[str, float]] = {}
    for row in manual_rows:
        metric = row["metric_name"]
        agent = row["agent_name"]
        if metric not in manual_map:
            manual_map[metric] = {}
        manual_map[metric][agent] = float(row["value"])

    # T1 metrics
    t1_defs = kpi_cfg.get("t1", [])
    categories: list[BSCScorecardCategory] = []

    # Group T1 metrics by logical category
    cat_metrics: list[dict] = []
    cat_names = [
        "Qualidade e Satisfação",
        "Produtividade e Volume",
        "Operacional e Comercial",
    ]
    cat_idx = 0

    for i, m_def in enumerate(t1_defs):
        name = str(m_def.get("name", ""))
        # Determine category transitions
        if i == 3 or i == 7:
            if cat_metrics:
                categories.append(
                    BSCScorecardCategory(
                        name=cat_names[cat_idx], metrics=_build_metric_rows(cat_metrics, agents, manual_map)
                    )
                )
            cat_metrics = []
            cat_idx += 1

        auto_computer = _auto_computers.get(name)
        is_manual = name not in _auto_computers

        metric_info = {
            "name": name,
            "meta": str(m_def.get("meta", "")),
            "peso": int(m_def.get("peso", 0)),
            "tipo": str(m_def.get("tipo", "")),
            "description": str(m_def.get("description", "")),
            "metric": str(m_def.get("metric", "")),
            "is_manual": is_manual,
            "m_def": m_def,
            "auto_computer": auto_computer,
        }
        cat_metrics.append(metric_info)

    # Append last category
    if cat_metrics:
        categories.append(
            BSCScorecardCategory(name=cat_names[cat_idx], metrics=_build_metric_rows(cat_metrics, agents, manual_map))
        )

    # T2 metrics as separate category
    t2_defs = kpi_cfg.get("t2", [])
    t2_metrics = []
    for m_def in t2_defs:
        name = str(m_def.get("name", ""))
        t2_metrics.append(
            {
                "name": name,
                "meta": str(m_def.get("meta", "")),
                "peso": int(m_def.get("peso", 0)),
                "tipo": str(m_def.get("tipo", "")),
                "description": str(m_def.get("description", "")),
                "metric": "",
                "is_manual": True,
                "m_def": m_def,
                "auto_computer": None,
            }
        )
    if t2_metrics:
        categories.append(
            BSCScorecardCategory(name="Tarefas", metrics=_build_metric_rows(t2_metrics, agents, manual_map))
        )

    # Penalidades setoriais
    penalidades_defs = kpi_cfg.get("penalidades_setoriais", [])
    penalidades = _build_metric_rows(
        [
            {
                "name": str(p.get("name", "")),
                "meta": str(p.get("meta", "")),
                "peso": int(p.get("peso", 0)),
                "tipo": str(p.get("tipo", "")),
                "description": str(p.get("description", "")),
                "metric": "",
                "is_manual": True,
                "m_def": p,
                "auto_computer": None,
            }
            for p in penalidades_defs
        ],
        agents,
        manual_map,
    )

    return BSCScorecardResponse(
        department=dept,
        start_date=start,
        end_date=end,
        agents=agents,
        has_config=True,
        categories=categories,
        penalidades=penalidades,
    )


def _build_metric_rows(
    metric_infos: list[dict],
    agents: list[str],
    manual_map: dict[str, dict[str, float]],
) -> list[BSCMetricRow]:
    rows = []
    for info in metric_infos:
        per_agent = []
        is_setorial = info.get("tipo") == "penalidade" and info["is_manual"] and info["auto_computer"] is None

        if is_setorial and info["is_manual"] and info["auto_computer"] is None:
            agent_vals = manual_map.get(info["name"], {})
            sector_val = sum(v for v in agent_vals.values() if v is not None) if agent_vals else None
            for agent in agents:
                raw_value = sector_val
                kpi_score = compute_kpi_score(raw_value, info["m_def"]) if raw_value is not None else None
                per_agent.append(
                    BSCAgentValue(
                        agent_name=agent,
                        raw_value=raw_value,
                        kpi_score=kpi_score,
                        is_manual=True,
                    )
                )
        else:
            for agent in agents:
                if info["is_manual"] and info["auto_computer"] is None:
                    manual_val = manual_map.get(info["name"], {}).get(agent)
                    raw_value = manual_val
                else:
                    raw_value = info["auto_computer"](agent) if info["auto_computer"] else 0.0

                kpi_score = compute_kpi_score(raw_value, info["m_def"]) if raw_value is not None else None

                per_agent.append(
                    BSCAgentValue(
                        agent_name=agent,
                        raw_value=raw_value,
                        kpi_score=kpi_score,
                        is_manual=info["is_manual"] and info["auto_computer"] is None,
                    )
                )

        rows.append(
            BSCMetricRow(
                name=info["name"],
                meta=info["meta"],
                peso=info["peso"],
                tipo=info["tipo"],
                description=info["description"],
                is_manual=info["is_manual"] and info["auto_computer"] is None,
                metric=info["metric"],
                per_agent=per_agent,
            )
        )
    return rows


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

    # Build month list (oldest to newest)
    month_list: list[tuple[int, int]] = []
    for i in range(months - 1, -1, -1):
        m = now.month - i
        y = now.year
        while m <= 0:
            m += 12
            y -= 1
        month_list.append((m, y))

    # Compute the full date range spanning all months
    first_m, first_y = month_list[0]
    last_m, last_y = month_list[-1]
    _, last_day = calendar.monthrange(last_y, last_m)
    range_start = f"{first_y}-{first_m:02d}-01"
    range_end = f"{last_y}-{last_m:02d}-{last_day}"

    # Fetch entire range once, process in Python
    from infrastructure.cache import processed_cache

    cache_key = f"evo_monthly:{range_start}:{range_end}"
    processed_cache_entry = await processed_cache.get_or_set(
        cache_key,
        lambda: asyncio.ensure_future(_fetch_and_process(repo, range_start, range_end)),
    )
    _, processed = await processed_cache_entry

    # Split processed data by month
    def _month_key(p: Any) -> tuple[int, int]:
        raw_str = getattr(p, "raw_created", None) or ""
        if raw_str:
            try:
                dt = datetime.strptime(str(raw_str)[:19], "%Y-%m-%d %H:%M:%S")
                return (dt.month, dt.year)
            except ValueError, TypeError:
                pass
        return (0, 0)

    from collections import defaultdict

    month_buckets: dict[tuple[int, int], list[Any]] = defaultdict(list)
    for p in processed:
        mk = _month_key(p)
        month_buckets[mk].append(p)

    evolution: list[EvolutionMonth] = []
    for m, y in month_list:
        bucket = month_buckets.get((m, y), [])
        stats = agg.aggregate_statistics(bucket) if bucket else {}
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


def _build_month_range(start_date: date, end_date: date) -> list[tuple[str, str, int, int, str]]:
    """Build month buckets between two dates (inclusive)."""
    months: list[tuple[str, str, int, int, str]] = []
    y, m = start_date.year, start_date.month
    while (y, m) <= (end_date.year, end_date.month):
        mb_start = f"{y}-{m:02d}-01"
        _, last_day = calendar.monthrange(y, m)
        mb_end = f"{y}-{m:02d}-{last_day}"
        label = f"{MONTH_NAMES[m]}/{y}"
        months.append((mb_start, mb_end, y, m, label))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months


def _build_day_range(start_date: date, end_date: date) -> list[tuple[str, str, str]]:
    """Build daily buckets between two dates (inclusive)."""
    days: list[tuple[str, str, str]] = []
    d = start_date
    while d <= end_date:
        iso = d.isoformat()
        days.append((iso, iso, d.strftime("%d/%m")))
        d += timedelta(days=1)
    return days


def _build_week_range(start_date: date, end_date: date) -> list[tuple[date, date, str]]:
    """Build ISO week buckets covering the date range (inclusive)."""
    # Align start to Monday of that week
    ws = start_date - timedelta(days=start_date.weekday())
    weeks: list[tuple[date, date, str]] = []
    while ws <= end_date:
        we = ws + timedelta(days=6)
        # Clamp to actual range
        eff_start = max(ws, start_date)
        eff_end = min(we, end_date)
        label = f"{eff_start.strftime('%d/%m')}–{eff_end.strftime('%d/%m')}"
        weeks.append((eff_start, eff_end, label))
        ws += timedelta(days=7)
    return weeks


def _build_bucket(
    period_start: str,
    label: str,
    stats: dict,
    year: int = 0,
    month: int = 0,
) -> EvolutionBucket:
    return EvolutionBucket(
        period_start=period_start,
        label=label,
        year=year,
        month=month,
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


@router.get("/evolution/granular", response_model=GranularEvolutionResponse)
async def get_evolution_granular(
    granularity: str = Query("month", pattern="^(day|week|month)$"),
    count: int = Query(12, ge=1, le=90),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    department: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Evolution data with selectable granularity (day, week, month).

    Fetches the entire range once and splits into buckets in Python,
    instead of N separate DB queries per bucket.
    """
    now = datetime.now()
    today = now.date()
    agg = _make_aggregator()

    use_range = start_date is not None and end_date is not None
    range_start: date | None = date.fromisoformat(start_date) if use_range and start_date else None
    range_end: date | None = date.fromisoformat(end_date) if use_range and end_date else None

    # Determine the full date range to fetch and build bucket lists
    fetch_start = ""
    fetch_end = ""
    month_list_data: list[tuple[str, str, int, int, str]] = []
    day_list_data: list[tuple[str, str, str]] = []
    week_list_data: list[tuple[date, date, str]] = []

    if granularity == "month":
        if use_range and range_start and range_end:
            month_list_data = _build_month_range(range_start, range_end)
        else:
            m = now.month - (count - 1)
            y = now.year
            while m <= 0:
                m += 12
                y -= 1
            month_list_data = _build_month_range(date(y, m, 1), today)
        fetch_start = month_list_data[0][0]
        fetch_end_date = date.fromisoformat(month_list_data[-1][0])
        _, last_day = calendar.monthrange(fetch_end_date.year, fetch_end_date.month)
        fetch_end = f"{fetch_end_date.year}-{fetch_end_date.month:02d}-{last_day}"
    elif granularity == "day":
        if use_range and range_start and range_end:
            day_list_data = _build_day_range(range_start, range_end)
        else:
            day_list_data = [
                (d.isoformat(), d.isoformat(), d.strftime("%d/%m"))
                for i in range(count - 1, -1, -1)
                for d in [today - timedelta(days=i)]
            ]
        fetch_start = day_list_data[0][0]
        fetch_end = day_list_data[-1][0]
    else:  # week
        if use_range and range_start and range_end:
            week_list_data = _build_week_range(range_start, range_end)
        else:
            week_list_data = _build_week_range(today - timedelta(days=count * 7 - 1), today)
        fetch_start = week_list_data[0][0].isoformat()
        fetch_end = week_list_data[-1][1].isoformat()  # end of last bucket, not start

    # Fetch entire range once using SQL-level filtering
    # Use cache to avoid re-processing for repeated calls
    from infrastructure.cache import processed_cache as _pc

    proc_cache_key = f"evo_proc:{fetch_start}:{fetch_end}:{department or ''}"
    processed = await _pc.get(proc_cache_key)
    if processed is None:
        raw_data = await repo.fetch_raw_data_range_filtered(
            fetch_start,
            fetch_end,
            agent_group=department,
        )
        processed = agg.process_all(raw_data)
        await _pc.set(proc_cache_key, processed)

    # Build date-range lookup for week buckets to avoid ISO week mismatch
    week_date_to_key: dict[str, str] = {}
    if granularity == "week":
        for i, (ws, we, _label) in enumerate(week_list_data):
            d = ws
            while d <= we:
                week_date_to_key[d.isoformat()] = str(i)
                d += timedelta(days=1)

    # Split into buckets by granularity
    def _bucket_key(p: Any) -> str:
        raw_str = getattr(p, "raw_created", None) or ""
        if not raw_str:
            return ""
        # raw_created already has timezone offset applied by _format_dt_direct
        try:
            dt = datetime.strptime(str(raw_str)[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError, TypeError:
            return ""
        if granularity == "day":
            return dt.strftime("%Y-%m-%d")
        elif granularity == "week":
            # Use the pre-computed date-to-bucket mapping
            return week_date_to_key.get(dt.strftime("%Y-%m-%d"), "")
        else:  # month
            return f"{dt.year}-{dt.month:02d}"

    from collections import defaultdict

    buckets_map: dict[str, list[Any]] = defaultdict(list)
    for p in processed:
        bk = _bucket_key(p)
        if bk:
            buckets_map[bk].append(p)

    # Build bucket list in order
    if granularity == "month":
        buckets = []
        for start, _, y, m, label in month_list_data:
            key = f"{y}-{m:02d}"
            bucket = buckets_map.get(key, [])
            stats = agg.aggregate_statistics(bucket) if bucket else {}
            buckets.append(_build_bucket(start, label, stats, year=y, month=m))
    elif granularity == "day":
        buckets = []
        for start, _, label in day_list_data:
            bucket = buckets_map.get(start, [])
            stats = agg.aggregate_statistics(bucket) if bucket else {}
            buckets.append(_build_bucket(start, label, stats))
    else:  # week
        buckets = []
        for i, (start_d, _, label) in enumerate(week_list_data):
            key = str(i)
            bucket = buckets_map.get(key, [])
            stats = agg.aggregate_statistics(bucket) if bucket else {}
            buckets.append(_build_bucket(start_d.isoformat(), label, stats))

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


_exec_pending: dict[str, asyncio.Task] = {}


async def _load_executive_processed(
    repo: ReportRepository,
    start_date: str,
    end_date: str,
    agent_ids: set[str],
    group: str | None,
    department: str | None = None,
) -> list[Any]:
    """Fetch + process + filter for executive endpoints.

    Uses request coalescing: when multiple endpoints request the same data
    simultaneously, only one computes it and the others await the result.
    """
    from infrastructure.cache import processed_cache as _pc

    cache_key = f"exec:{start_date}:{end_date}:{department or ''}:{group or ''}:{','.join(sorted(agent_ids))}"

    # Check cache first
    cached = await _pc.get(cache_key)
    if cached is not None:
        return cached

    # If another request is already computing this key, wait for it
    if cache_key in _exec_pending:
        try:
            return await _exec_pending[cache_key]
        except Exception:
            pass  # If it failed, we'll recompute

    # We are the first — compute and store as a Task
    async def _compute():
        try:
            raw, processed = await _fetch_and_process(repo, start_date, end_date)
            result = _filter_processed(processed, agent_ids, group, department)
            await _pc.set(cache_key, result)
            return result
        finally:
            _exec_pending.pop(cache_key, None)

    task = asyncio.ensure_future(_compute())
    _exec_pending[cache_key] = task
    return await task


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
        acceptable_art = sum(1 for a in arts if 10 < a <= 30)
        bad_art = sum(1 for a in arts if a > 30)

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
                acceptable_art_chats=acceptable_art,
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
    total_chats = len(processed)
    art_qualified = sum(1 for p in processed if isinstance(p.art_min, (int, float)) and 0 < p.art_min <= 10)
    total_with_art = sum(1 for p in processed if isinstance(p.art_min, (int, float)) and p.art_min > 0)
    pct_art_10min = round(art_qualified / total_with_art * 100, 1) if total_with_art > 0 else None
    return ExecutiveMeta(
        start_date=s,
        end_date=e,
        granularity=granularity,
        agent_ids=sorted(aid),
        group=group,
        total_chats=total_chats,
        total_messages=sum(p.msg_count for p in processed),
        pct_art_10min=pct_art_10min,
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
