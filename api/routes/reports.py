"""
Reports Routes
"""

from typing import Any

from fastapi import APIRouter, Depends

from api.auth import get_current_user
from api.schemas.reports import (
    AvailableReportsResponse,
    DownloadReportResponse,
    GenerateReportResponse,
    ReportRequest,
)

router = APIRouter()


@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: ReportRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Generate report on demand."""
    # TODO: Wire to GenerateReportUseCase
    return GenerateReportResponse(status="processing", report_id="pending")


@router.get("/{report_id}/download", response_model=DownloadReportResponse)
async def download_report(
    report_id: str,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Download generated report."""
    # TODO: Serve file from reports directory
    return DownloadReportResponse(download_url=f"/reports/{report_id}.xlsx")


@router.get("/available", response_model=AvailableReportsResponse)
async def list_available_reports(
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """List available reports."""
    # TODO: Scan reports directory
    return AvailableReportsResponse()
