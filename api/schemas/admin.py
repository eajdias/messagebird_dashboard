from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, model_validator

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


class SyncRangeRequest(BaseModel):
    """Sync a date range of conversations + messages.

    - If both dates are omitted, defaults to today (UTC, 1 day).
    - Maximum range: 30 days.
    - Minimum range: 1 day.
    """

    start_date: str | None = None
    end_date: str | None = None

    @model_validator(mode="after")
    def _apply_defaults_and_validate(self) -> SyncRangeRequest:
        now = datetime.now(UTC)
        if not self.end_date:
            self.end_date = now.strftime("%Y-%m-%d")
        if not self.start_date:
            start = now - timedelta(days=1)
            self.start_date = start.strftime("%Y-%m-%d")

        try:
            start_dt = datetime.fromisoformat(self.start_date)
            end_dt = datetime.fromisoformat(self.end_date)
        except ValueError as e:
            raise ValueError(f"Invalid date format (use YYYY-MM-DD): {e}") from e

        if end_dt < start_dt:
            raise ValueError("end_date must be on or after start_date.")
        delta_days = (end_dt.date() - start_dt.date()).days + 1
        if delta_days > 30:
            raise ValueError(f"Range cannot exceed 30 days (got {delta_days} days).")
        if delta_days < 1:
            raise ValueError("Range must be at least 1 day.")
        return self


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
