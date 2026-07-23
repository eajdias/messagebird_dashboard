"""
Admin Routes
"""

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from api.auth import get_current_user
from api.schemas._base import StatusResponse
from api.schemas.admin import (
    AgentItem,
    AgentListResponse,
    DepartmentItem,
    DepartmentListResponse,
    HealthResponse,
    JobInfo,
    SchedulerStatusResponse,
    SyncProfileResponse,
    SyncRangeRequest,
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from domain.constants import AGENTS, DEPT_MAP

logger = logging.getLogger("m_bird.admin")

router = APIRouter()


@router.post("/sync/range", response_model=SyncTriggerResponse)
async def trigger_sync_range(
    request: SyncRangeRequest | None = Body(default=None),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Sync conversations + messages for a date range.

    - Default: today only (1 day)
    - Maximum range: 30 days
    - Date format: YYYY-MM-DD
    """
    from api.sync_utils import refresh_materialized_view
    from application.use_cases.sync_database import SyncDatabaseUseCase

    body = request or SyncRangeRequest()
    logger.info(
        "Range sync triggered: start=%s end=%s",
        body.start_date,
        body.end_date,
    )
    try:
        use_case = SyncDatabaseUseCase()
        await use_case.execute(start_date=body.start_date, end_date=body.end_date)
        await refresh_materialized_view()
    except ValueError as e:
        logger.warning("Range sync rejected: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    logger.info("Range sync completed for %s → %s", body.start_date, body.end_date)
    return SyncTriggerResponse(
        status="completed",
        message=f"Range sync completed for {body.start_date} → {body.end_date}",
    )


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
        "Manual sync triggered: full=%s messages=%s days=%s surveys=%s today=%s",
        request.full_sync,
        request.sync_messages,
        request.messages_days,
        request.backfill_surveys,
        request.sync_today,
    )
    use_case = SyncDatabaseUseCase()
    await use_case.execute(
        full_sync=request.full_sync,
        sync_messages=request.sync_messages,
        messages_days=request.messages_days,
        backfill_surveys=request.backfill_surveys,
        year=request.year,
        month=request.month,
        sync_today=request.sync_today,
    )
    await refresh_materialized_view()
    logger.info("Manual sync completed")
    return SyncTriggerResponse(status="completed", message="Sync and MV refresh completed")


@router.get("/agents", response_model=AgentListResponse)
async def list_agents(
    include_db: bool = Query(False),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """List all agents from YAML config. If include_db=true, also include DB agents not in YAML."""
    items = [
        AgentItem(bird_id=bird_id, name=info["name"], group=info.get("group", "")) for bird_id, info in AGENTS.items()
    ]
    if include_db:
        from api.dependencies import get_pool

        pool = await get_pool()
        db_agents = await pool.fetch_all(
            "SELECT agnt_id::text as bird_id, agnt_name as name, agnt_grp as group FROM agents ORDER BY agnt_name"
        )
        yaml_names = {info["name"] for info in AGENTS.values()}
        for row in db_agents:
            if row["name"] and row["name"] not in yaml_names:
                row.get("group") or ""
                items.append(
                    AgentItem(
                        bird_id=row["bird_id"],
                        name=row["name"],
                        group="Não categorizado",
                    )
                )
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


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    from api.main import _scheduler_started_by_user
    from api.main import scheduler_jobs as _jobs
    from api.main import scheduler_running as _running

    jobs_raw = _jobs()
    return SchedulerStatusResponse(
        running=_running(),
        jobs=[JobInfo(id=j["id"], name=j["name"], next_run_time=j.get("next_run_time")) for j in jobs_raw],
        started_by_user=_scheduler_started_by_user,
    )


@router.post("/scheduler/start", response_model=StatusResponse)
async def start_scheduler_endpoint(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    from api.main import start_scheduler as _start

    msg = _start()
    return StatusResponse(status="ok", message=msg)


@router.post("/scheduler/stop", response_model=StatusResponse)
async def stop_scheduler_endpoint(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    from api.main import stop_scheduler as _stop

    msg = _stop()
    return StatusResponse(status="ok", message=msg)
