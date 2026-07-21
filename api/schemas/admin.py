from __future__ import annotations

from pydantic import BaseModel


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
    lookback_minutes: int = 60
    year: int | None = None
    month: int | None = None
    backfill_surveys: bool = False


class SyncTriggerResponse(BaseModel):
    status: str
    message: str = ""


class AgentItem(BaseModel):
    bird_id: str
    name: str
    group: str = ""


class AgentListResponse(BaseModel):
    agents: list[AgentItem] = []


class DepartmentItem(BaseModel):
    dept_id: int
    label: str


class DepartmentListResponse(BaseModel):
    departments: list[DepartmentItem] = []


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str = "unknown"


class SyncProfileResponse(BaseModel):
    active_profile: str
    sync_enabled: bool
    available_profiles: list[dict[str, object]]
