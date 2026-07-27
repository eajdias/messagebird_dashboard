"""
Admin Routes
"""

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

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
from api.schemas.dashboard import (
    AgentDetailResponse,
    AgentManualEntryCreate,
    AgentManualEntryResponse,
    AgentManualEntryUpdate,
    AvailableMetric,
    ManualMetricsListResponse,
)
from domain.constants import AGENTS, DEPT_MAP, KPI_CONFIG

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


# ── Agent Detail & Manual Entries ─────────────────────────────────────


def _resolve_agent(agent_name: str) -> dict[str, str]:
    """Find agent by name in YAML config. Returns {bird_id, name, group} or raises 404."""
    for bird_id, info in AGENTS.items():
        if info["name"] == agent_name:
            return {"bird_id": bird_id, "name": info["name"], "group": info.get("group", "")}
    raise HTTPException(status_code=404, detail=f"Agente '{agent_name}' não encontrado")


def _get_available_metrics(department: str) -> list[dict[str, object]]:
    """Return manual-only metrics available for a department from KPI config."""
    auto_computers = {
        "Elogios de atendimento / Feedback",
        "NPS (Net Promoter Score)",
        "Feedback Negativo (Penalidade)",
        "Atendimentos Finalizados",
    }
    kpi_cfg = KPI_CONFIG.get(department, {})
    metrics: list[dict[str, object]] = []

    for m in kpi_cfg.get("t1", []):
        if m.get("is_automatic_sum"):
            continue
        name = str(m.get("name", ""))
        if name in auto_computers:
            continue
        metrics.append(
            {
                "name": name,
                "meta": str(m.get("meta", "")),
                "peso": int(m.get("peso", 0)),
                "tipo": str(m.get("tipo", "")),
                "description": str(m.get("description", "")),
            }
        )

    for m in kpi_cfg.get("t2", []):
        metrics.append(
            {
                "name": str(m.get("name", "")),
                "meta": str(m.get("meta", "")),
                "peso": int(m.get("peso", 0)),
                "tipo": str(m.get("tipo", "")),
                "description": str(m.get("description", "")),
            }
        )

    for m in kpi_cfg.get("penalidades_setoriais", []):
        metrics.append(
            {
                "name": str(m.get("name", "")),
                "meta": str(m.get("meta", "")),
                "peso": int(m.get("peso", 0)),
                "tipo": str(m.get("tipo", "")),
                "description": str(m.get("description", "")),
            }
        )

    return metrics


@router.get("/agents/{agent_name}", response_model=AgentDetailResponse)
async def get_agent_detail(
    agent_name: str = Path(..., description="Nome do agente"),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get agent details and available manual metrics for their department."""
    agent = _resolve_agent(agent_name)
    dept = agent["group"]
    metrics = _get_available_metrics(dept)
    return AgentDetailResponse(
        bird_id=agent["bird_id"],
        name=agent["name"],
        group=agent["group"],
        available_metrics=[AvailableMetric(**m) for m in metrics],
    )


@router.get("/agents/{agent_name}/manual-entries", response_model=list[AgentManualEntryResponse])
async def list_agent_manual_entries(
    agent_name: str = Path(..., description="Nome do agente"),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    metric_name: str | None = Query(None),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """List manual metric entries for an agent. Optional date/metric filters."""
    agent = _resolve_agent(agent_name)
    dept = agent["group"]

    from api.dependencies import get_pool
    from infrastructure.repositories.postgres_report_repository import PostgresReportRepository

    pool = await get_pool()
    repo = PostgresReportRepository(pool)
    entries = await repo.get_agent_manual_entries(agent_name, dept, start_date, end_date, metric_name)
    return [AgentManualEntryResponse(**e) for e in entries]


@router.post("/agents/{agent_name}/manual-entries", response_model=AgentManualEntryResponse, status_code=201)
async def create_agent_manual_entry(
    payload: AgentManualEntryCreate,
    agent_name: str = Path(..., description="Nome do agente"),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Create a manual metric entry for an agent."""
    _resolve_agent(agent_name)

    from api.dependencies import get_pool
    from infrastructure.repositories.postgres_report_repository import PostgresReportRepository

    pool = await get_pool()
    repo = PostgresReportRepository(pool)
    entry = await repo.create_agent_manual_entry(
        agent_name=agent_name,
        department=payload.department,
        metric_name=payload.metric_name,
        entry_date=payload.entry_date,
        value=payload.value,
        notes=payload.notes,
    )
    return AgentManualEntryResponse(**entry)


@router.put("/agents/{agent_name}/manual-entries/{entry_id}", response_model=AgentManualEntryResponse)
async def update_agent_manual_entry(
    entry_id: int = Path(..., ge=1),
    agent_name: str = Path(..., description="Nome do agente"),
    payload: AgentManualEntryUpdate | None = Body(default=None),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Update an agent's manual metric entry."""
    _resolve_agent(agent_name)

    if not payload or (payload.value is None and payload.notes is None):
        raise HTTPException(status_code=400, detail="Nada para atualizar")

    from api.dependencies import get_pool
    from infrastructure.repositories.postgres_report_repository import PostgresReportRepository

    pool = await get_pool()
    repo = PostgresReportRepository(pool)
    entry = await repo.update_agent_manual_entry(entry_id, payload.value, payload.notes)
    if not entry:
        raise HTTPException(status_code=404, detail="Entrada não encontrada")
    return AgentManualEntryResponse(**entry)


@router.delete("/agents/{agent_name}/manual-entries/{entry_id}", status_code=204)
async def delete_agent_manual_entry(
    entry_id: int = Path(..., ge=1),
    agent_name: str = Path(..., description="Nome do agente"),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Delete an agent's manual metric entry."""
    _resolve_agent(agent_name)

    from api.dependencies import get_pool
    from infrastructure.repositories.postgres_report_repository import PostgresReportRepository

    pool = await get_pool()
    repo = PostgresReportRepository(pool)
    deleted = await repo.delete_agent_manual_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrada não encontrada")


@router.get("/manual-metrics", response_model=ManualMetricsListResponse)
async def list_manual_metrics(
    department: str = Query(..., description="Nome do departamento"),
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """List all manual metrics available for a department (for dropdown in agent form)."""
    raw = _get_available_metrics(department)
    return ManualMetricsListResponse(metrics=[AvailableMetric(**m) for m in raw])


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
