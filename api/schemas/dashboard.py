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
