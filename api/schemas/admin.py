from __future__ import annotations

from pydantic import BaseModel

from api.schemas._base import StatusResponse, list_response


class SyncStatusResponse(BaseModel):
    last_sync: str | None = None
    status: str = "idle"
    records_synced: int = 0
    duration_seconds: float | None = None
    error: str | None = None


class SyncTriggerRequest(BaseModel):
    full_sync: bool = False
    sync_messages: bool = False
    messages_days: int | None = None
    year: int | None = None
    month: int | None = None
    backfill_surveys: bool = False
    sync_today: bool = False


SyncTriggerResponse = StatusResponse


class AgentItem(BaseModel):
    bird_id: str
    name: str
    group: str = ""


AgentListResponse = list_response(AgentItem, "agents")


class DepartmentItem(BaseModel):
    dept_id: int
    label: str


DepartmentListResponse = list_response(DepartmentItem, "departments")


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str = "unknown"


class SyncProfileResponse(BaseModel):
    active_profile: str
    sync_enabled: bool
    available_profiles: list[dict[str, object]]


class JobInfo(BaseModel):
    id: str
    name: str
    next_run_time: str | None = None


class SchedulerStatusResponse(BaseModel):
    running: bool
    jobs: list[JobInfo]
    started_by_user: bool = False
