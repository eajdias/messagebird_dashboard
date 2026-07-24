"""
Reports Routes — export, generate, list, download, delete reports.
"""

import json
import logging
import os
import shutil
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from api.auth import get_current_user
from api.dependencies import get_reports_dir, get_repository
from api.schemas._base import StatusResponse
from api.schemas.reports import (
    AvailableReportItem,
    AvailableReportsResponse,
    DownloadReportResponse,
    ExportConversationsRequest,
    ExportConversationsResponse,
    GenerateReportResponse,
    ReportRequest,
)
from application.interfaces.repository import ReportRepository
from application.services.export_service import ExportService
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


def _manifest_to_item(entry: dict[str, Any]) -> AvailableReportItem:
    return AvailableReportItem(
        report_id=entry.get("report_id", ""),
        type=entry.get("type", ""),
        year=entry.get("year"),
        month=entry.get("month"),
        group=entry.get("group"),
        format=entry.get("format"),
        start_date=entry.get("start_date"),
        end_date=entry.get("end_date"),
        filename=entry.get("filename", ""),
        path=entry.get("path", ""),
        size_bytes=entry.get("size_bytes"),
        record_count=entry.get("record_count"),
        created_by=entry.get("created_by", ""),
        created_at=entry.get("created_at", ""),
    )


# ── POST /reports/export ────────────────────────────────────────────────


@router.post("/export", response_model=ExportConversationsResponse)
async def export_conversations_data(
    request: ExportConversationsRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
    reports_dir: str = Depends(get_reports_dir),
):
    """Generate CSV/XLSX/ZIP from conversation filters and optionally save to history."""
    user_email = current_user.get("sub", "unknown")

    rows = await repo.export_conversations(
        start_date=request.start_date,
        end_date=request.end_date,
        department=request.department,
        agent=request.agent,
        channel=request.channel,
        status=request.status,
        search=request.search,
        sort_by="start_time",
        sort_order="desc",
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Nenhuma conversa encontrada")

    svc = ExportService(reports_dir)

    if request.format == "csv":
        entry = svc.save_csv(rows, request.start_date, request.end_date, user_email)
        content_type = "text/csv; charset=utf-8"
    elif request.format == "xlsx":
        entry = svc.save_xlsx(rows, request.start_date, request.end_date, user_email)
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif request.format == "pdf_zip":
        ids = [int(r.get("cnvs_id", r.get("id", 0))) for r in rows if r.get("cnvs_id") or r.get("id")]
        msgs_map = await repo.fetch_messages_for_conversations(ids)
        entry = svc.save_zip_os(rows, msgs_map, request.start_date, request.end_date, user_email)
        content_type = "application/zip"
    else:
        raise HTTPException(status_code=400, detail=f"Formato inválido: {request.format}")

    manifest = _load_manifest(reports_dir)
    manifest.append(entry)
    _save_manifest(reports_dir, manifest)

    filepath = os.path.join(reports_dir, entry["path"])
    if not request.save_to_history:
        return StreamingResponse(
            open(filepath, "rb"),
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{entry["filename"]}"',
                "X-Report-Id": entry["report_id"],
            },
        )

    return ExportConversationsResponse(
        status="ok",
        message="Relatório salvo no histórico",
        report_id=entry["report_id"],
        download_url=f"/api/v1/reports/{entry['report_id']}/download",
        size_bytes=entry["size_bytes"],
        record_count=entry["record_count"],
    )


# ── POST /reports/generate ──────────────────────────────────────────────


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
        "path": os.path.relpath(output_dir, reports_dir),
        "created_at": datetime.now().isoformat(),
    }

    manifest = _load_manifest(reports_dir)
    manifest.append(entry)
    _save_manifest(reports_dir, manifest)

    return GenerateReportResponse(status="completed", message="Relatório gerado com sucesso", report_id=report_id)


# ── GET /reports/available ──────────────────────────────────────────────


@router.get("/available", response_model=AvailableReportsResponse)
async def list_available_reports(
    _current_user: dict[str, Any] = Depends(get_current_user),
    reports_dir: str = Depends(get_reports_dir),
):
    manifest = _load_manifest(reports_dir)
    items = [_manifest_to_item(e) for e in manifest]
    items.reverse()
    return AvailableReportsResponse(reports=items)


# ── GET /reports/{report_id}/download ───────────────────────────────────


@router.get("/{report_id}/download")
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

    # New export entries: path is relative to reports_dir and points to the file directly
    if entry.get("type") == "export":
        abs_path = os.path.join(reports_dir, report_path)
        if not os.path.isfile(abs_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        return FileResponse(
            abs_path,
            filename=entry.get("filename", f"{report_id}.bin"),
            media_type="application/octet-stream",
        )

    # Legacy periodic reports: path points to a directory, walk to find Dashboard*.xlsx
    abs_report_path = os.path.join(reports_dir, report_path)
    candidate = None
    if os.path.isdir(abs_report_path):
        for root, _dirs, files in os.walk(abs_report_path):
            for f in files:
                if f.startswith("Dashboard") and f.endswith(".xlsx"):
                    candidate = os.path.relpath(os.path.join(root, f), abs_report_path)
                    break
            if candidate:
                break

    if not candidate:
        raise HTTPException(status_code=404, detail="Arquivo do relatório não encontrado")

    return FileResponse(
        os.path.join(abs_report_path, candidate),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=candidate,
    )


# ── GET /reports/{report_id}/file/{filename:path} ───────────────────────


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

    report_path = entry.get("path", "")
    abs_report_path = os.path.join(reports_dir, report_path)

    if not os.path.isdir(abs_report_path):
        raise HTTPException(status_code=404, detail="Diretório do relatório não encontrado")

    file_path = os.path.normpath(os.path.join(abs_report_path, filename.replace("/", os.sep)))
    safe_base = os.path.normpath(os.path.abspath(reports_dir))

    if not file_path.startswith(safe_base):
        raise HTTPException(status_code=403, detail="Acesso negado")

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

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


# ── DELETE /reports/{report_id} ────────────────────────────────────────


@router.delete("/{report_id}", response_model=StatusResponse)
async def delete_report(
    report_id: str,
    _current_user: dict[str, Any] = Depends(get_current_user),
    reports_dir: str = Depends(get_reports_dir),
):
    manifest = _load_manifest(reports_dir)
    entry = next((e for e in manifest if e["report_id"] == report_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")

    report_path = entry.get("path", "")
    abs_path = os.path.join(reports_dir, report_path)

    if os.path.isdir(abs_path):
        shutil.rmtree(abs_path)
    elif os.path.isfile(abs_path):
        os.remove(abs_path)

    manifest = [e for e in manifest if e["report_id"] != report_id]
    _save_manifest(reports_dir, manifest)

    return StatusResponse(status="ok", message="Relatório removido")
