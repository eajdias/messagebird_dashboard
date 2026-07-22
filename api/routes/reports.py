"""
Reports Routes — wired to GenerateReportUseCase + ExcelExporter.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.auth import get_current_user
from api.dependencies import get_reports_dir, get_repository
from api.schemas.reports import (
    AvailableReportItem,
    AvailableReportsResponse,
    DownloadReportResponse,
    GenerateReportResponse,
    ReportRequest,
)
from application.interfaces.repository import ReportRepository
from application.use_cases.generate_report import GenerateReportUseCase
from infrastructure.exporters.excel_exporter import ExcelExporter

logger = logging.getLogger("api.reports")

router = APIRouter()

MANIFEST_FILE = "manifest.json"


def _manifest_path(reports_dir: str) -> str:
    return os.path.join(reports_dir, MANIFEST_FILE)


def _load_manifest(reports_dir: str) -> list[dict[str, Any]]:
    path = _manifest_path(reports_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []


def _save_manifest(reports_dir: str, manifest: list[dict[str, Any]]):
    os.makedirs(reports_dir, exist_ok=True)
    with open(_manifest_path(reports_dir), "w") as f:
        json.dump(manifest, f, indent=2, default=str)


def _build_exporter():
    return ExcelExporter()


@router.post("/generate", response_model=GenerateReportResponse)
async def generate_report(
    request: ReportRequest,
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
    reports_dir: str = Depends(get_reports_dir),
):
    exporter = _build_exporter()
    use_case = GenerateReportUseCase(repository=repo, exporter=exporter)

    report_id = str(uuid.uuid4())[:8]
    output_dir = os.path.join(reports_dir, report_id)

    try:
        await use_case.execute(
            year=request.year,
            month=request.month,
            output_dir=output_dir,
            report_type=request.type,
            sector=request.group,
        )
    except Exception as e:
        logger.exception("Report generation failed")
        return GenerateReportResponse(status="error", message=str(e), report_id="")

    entry = {
        "report_id": report_id,
        "type": request.type,
        "year": request.year,
        "month": request.month,
        "group": request.group,
        "path": output_dir,
        "created_at": datetime.now().isoformat(),
    }

    manifest = _load_manifest(reports_dir)
    manifest.append(entry)
    _save_manifest(reports_dir, manifest)

    return GenerateReportResponse(status="completed", message="Relatório gerado com sucesso", report_id=report_id)


@router.get("/available", response_model=AvailableReportsResponse)
async def list_available_reports(
    _current_user: dict[str, Any] = Depends(get_current_user),
    reports_dir: str = Depends(get_reports_dir),
):
    manifest = _load_manifest(reports_dir)
    items = []
    for entry in manifest:
        items.append(
            AvailableReportItem(
                report_id=entry["report_id"],
                type=entry.get("type", ""),
                year=entry.get("year", 0),
                month=entry.get("month"),
                group=entry.get("group"),
                filename=entry.get("path", ""),
                created_at=entry.get("created_at", ""),
            )
        )
    items.reverse()
    return AvailableReportsResponse(reports=items)


@router.get("/{report_id}/download", response_model=DownloadReportResponse)
async def download_report(
    report_id: str,
    _current_user: dict[str, Any] = Depends(get_current_user),
    reports_dir: str = Depends(get_reports_dir),
):
    manifest = _load_manifest(reports_dir)
    entry = next((e for e in manifest if e["report_id"] == report_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    report_path = entry.get("path", "")

    candidate = None
    for root, _dirs, files in os.walk(report_path):
        for f in files:
            if f.startswith("Dashboard") and f.endswith(".xlsx"):
                candidate = os.path.relpath(os.path.join(root, f), report_path)
                break
        if candidate:
            break

    if not candidate:
        raise HTTPException(status_code=404, detail="Arquivo do relatório não encontrado")

    filename = f"relatorio_{entry['type']}_{entry['year']}"
    month_val = entry.get("month")
    if month_val is not None:
        filename += f"_{month_val:02d}"
    filename += ".xlsx"

    return DownloadReportResponse(download_url=f"/api/v1/reports/{report_id}/file/{candidate}")


@router.get("/{report_id}/file/{filename:path}")
async def serve_report_file(
    report_id: str,
    filename: str,
    _current_user: dict[str, Any] = Depends(get_current_user),
    reports_dir: str = Depends(get_reports_dir),
):
    manifest = _load_manifest(reports_dir)
    entry = next((e for e in manifest if e["report_id"] == report_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    file_path = os.path.normpath(os.path.join(entry["path"], filename.replace("/", os.sep)))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    safe_base = os.path.normpath(os.path.abspath(reports_dir))
    if not file_path.startswith(safe_base):
        raise HTTPException(status_code=403, detail="Acesso negado")

    display_name = f"relatorio_{entry['type']}_{entry['year']}"
    month_val = entry.get("month")
    if month_val is not None:
        display_name += f"_{month_val:02d}"
    display_name += ".xlsx"

    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=display_name,
    )
