from __future__ import annotations

from pydantic import BaseModel, Field

from api.schemas._base import StatusResponse, list_response


class ReportRequest(BaseModel):
    type: str = Field(..., pattern=r"^(monthly|annual)$")
    year: int
    month: int | None = None
    group: str | None = None


class ExportConversationsRequest(BaseModel):
    format: str = Field(..., pattern=r"^(csv|xlsx|pdf_zip)$")
    start_date: str
    end_date: str
    department: str | None = None
    agent: str | None = None
    channel: str | None = None
    status: str | None = None
    search: str | None = None
    save_to_history: bool = False


class ExportConversationsResponse(StatusResponse):
    report_id: str = ""
    download_url: str = ""
    size_bytes: int = 0
    record_count: int = 0


class DownloadReportResponse(BaseModel):
    download_url: str


class AvailableReportItem(BaseModel):
    report_id: str
    type: str
    year: int | None = 0
    month: int | None = None
    group: str | None = None
    format: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    filename: str = ""
    path: str = ""
    size_bytes: int | None = None
    record_count: int | None = None
    created_by: str = ""
    created_at: str = ""


AvailableReportsResponse = list_response(AvailableReportItem, "reports")


class GenerateReportResponse(StatusResponse):
    report_id: str
