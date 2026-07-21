from __future__ import annotations

from pydantic import BaseModel, Field

from api.schemas._base import StatusResponse, list_response


class ReportRequest(BaseModel):
    type: str = Field(..., pattern=r"^(monthly|annual)$")
    year: int
    month: int | None = None
    group: str | None = None


class DownloadReportResponse(BaseModel):
    download_url: str


class AvailableReportItem(BaseModel):
    report_id: str
    type: str
    year: int
    month: int | None = None
    group: str | None = None
    filename: str = ""
    created_at: str = ""


AvailableReportsResponse = list_response(AvailableReportItem, "reports")


class GenerateReportResponse(StatusResponse):
    report_id: str
