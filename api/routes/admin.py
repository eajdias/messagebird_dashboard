"""
Admin Routes
"""

from typing import Any

from fastapi import APIRouter, Depends

from api.auth import get_current_user
from api.schemas.admin import (
    AgentItem,
    AgentListResponse,
    DepartmentItem,
    DepartmentListResponse,
    HealthResponse,
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from domain.constants import AGENTS, DEPT_MAP

router = APIRouter()


@router.get("/sync/status", response_model=SyncStatusResponse)
async def get_sync_status(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get last sync status."""
    # TODO: Read from sync table in PG
    return SyncStatusResponse()


@router.post("/sync/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(
    request: SyncTriggerRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Trigger manual sync."""
    from api.main import _refresh_mv
    from application.use_cases.sync_database import SyncDatabaseUseCase

    use_case = SyncDatabaseUseCase()
    await use_case.execute(
        full_sync=request.full_sync,
        sync_messages=request.sync_messages,
        messages_days=request.messages_days,
        backfill_surveys=request.backfill_surveys,
        year=request.year,
        month=request.month,
    )
    await _refresh_mv()
    return SyncTriggerResponse(status="completed", message="Sync and MV refresh completed")


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """List all agents."""
    items = [
        AgentItem(bird_id=bird_id, name=info["name"], group=info.get("group", "")) for bird_id, info in AGENTS.items()
    ]
    return AgentListResponse(agents=items)


@router.get("/departments", response_model=DepartmentListResponse)
async def list_departments(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """List all departments."""
    items = [DepartmentItem(dept_id=dept_id, label=label) for dept_id, label in DEPT_MAP.items()]
    return DepartmentListResponse(departments=items)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint (no auth required)."""
    return HealthResponse(status="healthy", version="2.0.0")
