from __future__ import annotations

from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    type: str = Field(..., pattern=r"^(monthly|annual)$")
    year: int
    month: int | None = None
    group: str | None = None


class GenerateReportResponse(BaseModel):
    status: str
    report_id: str


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


class AvailableReportsResponse(BaseModel):
    reports: list[AvailableReportItem] = []
