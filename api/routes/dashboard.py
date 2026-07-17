"""
Dashboard Routes
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
async def get_summary(start_date: str = None, end_date: str = None):
    """Get dashboard summary metrics."""
    # TODO: Implement
    return {
        "total_conversations": 0,
        "nps_score": 0,
        "frt_avg_minutes": 0,
        "art_avg_minutes": 0,
    }


@router.get("/bsc")
async def get_bsc(start_date: str = None, end_date: str = None):
    """Get BSC data (T1 + T2)."""
    # TODO: Implement
    return {"header": [], "data_t1": [], "data_t2": []}


@router.get("/kpis")
async def get_kpis(department: str = None):
    """Get KPIs by department."""
    # TODO: Implement
    return {"kpis": []}


@router.get("/evolution")
async def get_evolution(months: int = 12):
    """Get monthly evolution (last N months)."""
    # TODO: Implement
    return {"evolution": []}


@router.get("/agents")
async def get_agents_ranking():
    """Get agent ranking."""
    # TODO: Implement
    return {"agents": []}


@router.get("/channels")
async def get_channels():
    """Get metrics by channel."""
    # TODO: Implement
    return {"channels": []}
