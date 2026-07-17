"""
Reports Routes
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ReportRequest(BaseModel):
    type: str  # "monthly" | "annual"
    year: int
    month: int = None
    group: str = None


@router.post("/generate")
async def generate_report(request: ReportRequest):
    """Generate report on demand."""
    # TODO: Implement
    return {
        "status": "processing",
        "report_id": "pending",
    }


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    """Download generated report."""
    # TODO: Implement
    return {"download_url": f"/reports/{report_id}.xlsx"}


@router.get("/available")
async def list_available_reports():
    """List available reports."""
    # TODO: Implement
    return {"reports": []}
