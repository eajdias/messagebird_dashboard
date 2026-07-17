"""
Dashboard Routes
"""

from typing import Any

from fastapi import APIRouter, Depends

from api.auth import get_current_user
from api.schemas.dashboard import (
    AgentRankingResponse,
    BSCResponse,
    ChannelResponse,
    DashboardSummaryResponse,
    EvolutionResponse,
    KPIResponse,
)

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_summary(
    start_date: str | None = None,
    end_date: str | None = None,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get dashboard summary metrics."""
    # TODO: Wire to application layer (ReportAggregator)
    return DashboardSummaryResponse()


@router.get("/bsc", response_model=BSCResponse)
async def get_bsc(
    start_date: str | None = None,
    end_date: str | None = None,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get BSC data (T1 + T2)."""
    # TODO: Wire to application layer
    return BSCResponse()


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    department: str | None = None,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get KPIs by department."""
    # TODO: Wire to application layer
    return KPIResponse(department=department or "")


@router.get("/evolution", response_model=EvolutionResponse)
async def get_evolution(
    months: int = 12,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get monthly evolution (last N months)."""
    # TODO: Wire to application layer
    return EvolutionResponse()


@router.get("/agents", response_model=AgentRankingResponse)
async def get_agents_ranking(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get agent ranking."""
    # TODO: Wire to application layer
    return AgentRankingResponse()


@router.get("/channels", response_model=ChannelResponse)
async def get_channels(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get metrics by channel."""
    # TODO: Wire to application layer
    return ChannelResponse()
