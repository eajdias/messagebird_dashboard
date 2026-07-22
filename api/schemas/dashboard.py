from __future__ import annotations

from pydantic import BaseModel

from api.schemas._base import list_response


class DashboardSummaryResponse(BaseModel):
    total_conversations: int = 0
    nps_score: float | None = None
    frt_avg_minutes: float | None = None
    art_avg_minutes: float | None = None
    rating_avg: float | None = None
    sla_compliance_pct: float | None = None
    total_messages: int = 0
    unique_contacts: int = 0
    returning_contacts: int = 0


class BSCResponse(BaseModel):
    header: list[str] = []
    data_t1: list[list[str | int | float | None]] = []
    data_t2: list[list[str | int | float | None]] = []
    kpi_config: dict[str, object] | None = None


class KPIItem(BaseModel):
    name: str
    value: float | None = None
    meta: str | int | None = None
    peso: int = 0
    score: float | None = None
    tipo: str = ""


class KPIResponse(BaseModel):
    department: str
    kpis: list[KPIItem] = []


class EvolutionMonth(BaseModel):
    year: int
    month: int
    label: str
    total_conversations: int = 0
    nps_score: float | None = None
    art_avg_minutes: float | None = None
    frt_avg_minutes: float | None = None
    sla_compliance_pct: float | None = None
    rating_avg: float | None = None


EvolutionResponse = list_response(EvolutionMonth, "evolution")


class EvolutionBucket(BaseModel):
    """Generic evolution bucket — supports month, week, or day granularity.

    `period_start` is an ISO date (YYYY-MM-DD) marking the bucket start.
    `year`/`month` are only populated for monthly buckets (0 otherwise).
    `label` is human-readable and tailored to the granularity.
    """

    period_start: str
    label: str
    year: int = 0
    month: int = 0
    total_conversations: int = 0
    nps_score: float | None = None
    art_avg_minutes: float | None = None
    frt_avg_minutes: float | None = None
    sla_compliance_pct: float | None = None
    rating_avg: float | None = None


class GranularEvolutionResponse(BaseModel):
    granularity: str
    buckets: list[EvolutionBucket] = []


class AgentRankingItem(BaseModel):
    rank: int = 0
    agent_name: str
    department: str = ""
    group: str = ""
    total_chats: int = 0
    nps_score: float | None = None
    rating_avg: float | None = None
    art_avg_minutes: float | None = None
    frt_avg_minutes: float | None = None
    sla_compliance_pct: float | None = None
    total_messages: int = 0


AgentRankingResponse = list_response(AgentRankingItem, "agents")


class ChannelItem(BaseModel):
    channel_id: str
    channel_name: str
    total_conversations: int = 0
    total_messages: int = 0
    nps_score: float | None = None
    rating_avg: float | None = None


ChannelResponse = list_response(ChannelItem, "channels")


# ── Executive Dashboard (granular endpoints, period-driven) ────────────────


class CountedItem(BaseModel):
    """Generic counted item: `{label, value, pct}`."""

    label: str
    value: int = 0
    pct: float = 0.0


class QualityDistribution(BaseModel):
    """Distribution counts for a 1..N range (e.g. NPS 1-10 or rating 1-5)."""

    counts: dict[str, int] = {}
    total: int = 0


class NPSBreakdown(BaseModel):
    """NPS category counts (promoters 9-10, neutrals 7-8, detractors 1-6)."""

    promoters: int = 0
    neutrals: int = 0
    detractors: int = 0
    total: int = 0
    real_nps: float | None = None


class HeatmapCell(BaseModel):
    day: int  # 0 = Mon, 6 = Sun
    hour: int  # 0..23
    value: int = 0


class HeatmapResponse(BaseModel):
    cells: list[HeatmapCell] = []
    max_value: int = 0
    total: int = 0


class MotivesResponse(BaseModel):
    items: list[CountedItem] = []
    total: int = 0


class OccurrencesResponse(BaseModel):
    items: list[CountedItem] = []
    total: int = 0


class DOWResponse(BaseModel):
    items: list[CountedItem] = []
    total: int = 0
    days: list[str] = []


class DepartmentRow(BaseModel):
    name: str
    chats: int = 0
    pct_total: float = 0.0
    art_avg: float | None = None
    sla_pct: float | None = None
    returners: int = 0
    pct_returning: float = 0.0
    avg_rating: float | None = None
    nps_real: float | None = None


class DepartmentsResponse(BaseModel):
    items: list[DepartmentRow] = []
    total_chats: int = 0


class AgentRow(BaseModel):
    name: str
    department: str = ""
    chats: int = 0
    total_messages: int = 0
    art_avg: float | None = None
    sla_pct: float | None = None
    real_nps: float | None = None
    avg_rating: float | None = None
    compliments: int = 0
    negatives: int = 0
    returners: int = 0
    unique_contacts: int = 0
    rating_distribution: dict[str, int] = {}
    nps_score_distribution: dict[str, int] = {}


class AgentsResponse(BaseModel):
    items: list[AgentRow] = []
    total_chats: int = 0


class QualityResponse(BaseModel):
    """Quality overview: rating + NPS distributions + category breakdown."""

    rating: QualityDistribution = QualityDistribution()
    nps_score: QualityDistribution = QualityDistribution()
    nps_breakdown: NPSBreakdown = NPSBreakdown()


class ExecutiveBSCResponse(BaseModel):
    """BSC scorecard for a specific group (sector) — only 'Suporte Tecnico' has config."""

    group: str
    header: list[str] = []
    data_t1: list[list[str | int | float | None]] = []
    data_t2: list[list[str | int | float | None]] = []
    kpi_config: dict[str, object] | None = None
    total_chats: int = 0


class ExecutiveMeta(BaseModel):
    start_date: str
    end_date: str
    granularity: str
    agent_ids: list[str] = []
    group: str | None = None
    total_chats: int = 0
    total_messages: int = 0
