"""
Admin Routes
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends

from api.auth import get_current_user
from api.schemas.admin import (
    AgentItem,
    AgentListResponse,
    DepartmentItem,
    DepartmentListResponse,
    HealthResponse,
    SyncProfileResponse,
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from domain.constants import AGENTS, DEPT_MAP

logger = logging.getLogger("m_bird.admin")

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
    from api.sync_utils import refresh_materialized_view
    from application.use_cases.sync_database import SyncDatabaseUseCase

    logger.info(
        "Manual sync triggered: full=%s messages=%s days=%s surveys=%s",
        request.full_sync,
        request.sync_messages,
        request.messages_days,
        request.backfill_surveys,
    )
    use_case = SyncDatabaseUseCase()
    await use_case.execute(
        full_sync=request.full_sync,
        sync_messages=request.sync_messages,
        messages_days=request.messages_days,
        lookback_minutes=request.lookback_minutes,
        backfill_surveys=request.backfill_surveys,
        year=request.year,
        month=request.month,
    )
    await refresh_materialized_view()
    logger.info("Manual sync completed")
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


@router.get("/sync/profile", response_model=SyncProfileResponse)
async def get_sync_profile(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get current sync profile configuration."""
    import os

    from infrastructure.config.sync_profiles import get_active_profile, list_profiles

    sync_enabled = os.getenv("SYNC_ENABLED", "true").lower() in ("true", "1", "yes")
    profile = get_active_profile()
    return SyncProfileResponse(
        active_profile=profile.name,
        sync_enabled=sync_enabled,
        available_profiles=list_profiles(),
    )
