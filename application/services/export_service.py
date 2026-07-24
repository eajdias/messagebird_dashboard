"""Export Service — generates CSV, XLSX, and ZIP (OS) files from conversation data."""

from __future__ import annotations

import io
import logging
import os
import uuid
import zipfile
from datetime import datetime
from typing import Any

from infrastructure.exporters.csv_exporter import CSVExporter
from infrastructure.exporters.pdf_exporter import PDFExporter
from infrastructure.exporters.xlsx_exporter import XLSXExporter

logger = logging.getLogger("m_bird.export_service")

EXPORT_DIRS: dict[str, str] = {
    "csv": "exports/csv",
    "xlsx": "exports/xlsx",
    "pdf_zip": "exports/zip",
}


class ExportService:
    def __init__(self, reports_dir: str):
        self._reports_dir = reports_dir
        self._csv = CSVExporter()
        self._xlsx = XLSXExporter()
        self._pdf = PDFExporter()

    def save_csv(self, rows: list[dict[str, Any]], start_date: str, end_date: str, created_by: str) -> dict[str, Any]:
        data = self._csv.generate(rows)
        return self._save_file("csv", "csv", data, start_date, end_date, rows, created_by)

    def save_xlsx(self, rows: list[dict[str, Any]], start_date: str, end_date: str, created_by: str) -> dict[str, Any]:
        data = self._xlsx.generate(rows)
        return self._save_file("xlsx", "xlsx", data, start_date, end_date, rows, created_by)

    def save_zip_os(
        self,
        rows: list[dict[str, Any]],
        msgs_map: dict[int, list[dict[str, Any]]],
        start_date: str,
        end_date: str,
        created_by: str,
    ) -> dict[str, Any]:
        zip_buf = io.BytesIO()
        count = 0
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for r in rows:
                cnvs_id = r.get("cnvs_id") or r.get("id")
                if not cnvs_id:
                    continue
                cnvs_id = int(cnvs_id)
                detail = self._row_to_detail(r)
                msgs = msgs_map.get(cnvs_id, [])
                pdf_bytes = self._pdf.generate_single_os_pdf_bytes(detail, msgs)
                protocol = detail.get("cnvs_bird") or str(cnvs_id)
                zf.writestr(f"OS_{protocol}.pdf", pdf_bytes)
                count += 1

        zip_buf.seek(0)
        data = zip_buf.getvalue()
        return self._save_file("pdf_zip", "zip", data, start_date, end_date, [{"_count": count}], created_by)

    def _save_file(
        self,
        format: str,
        ext: str,
        data: bytes,
        start_date: str,
        end_date: str,
        rows: list[dict[str, Any]],
        created_by: str,
    ) -> dict[str, Any]:
        report_id = f"{format}_{uuid.uuid4().hex[:8]}"
        safe_ts = datetime.now().strftime("%H%M%S")
        filename = f"conversas_{start_date}_{end_date}_{safe_ts}.{ext}"

        rel_dir = EXPORT_DIRS[format]
        abs_dir = os.path.join(self._reports_dir, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)

        filepath = os.path.join(abs_dir, filename)
        with open(filepath, "wb") as f:
            f.write(data)

        size_bytes = os.path.getsize(filepath)

        return {
            "report_id": report_id,
            "type": "export",
            "format": format,
            "start_date": start_date,
            "end_date": end_date,
            "filename": filename,
            "path": os.path.relpath(filepath, self._reports_dir),
            "size_bytes": size_bytes,
            "record_count": len(rows),
            "created_by": created_by,
            "created_at": datetime.now().isoformat(),
        }

    def _row_to_detail(self, r: dict[str, Any]) -> dict[str, Any]:
        return {
            "cnvs_id": r.get("cnvs_id") or r.get("id", 0),
            "cnvs_created": r.get("cnvs_created") or r.get("start_time", ""),
            "cnvs_updated": r.get("cnvs_updated") or r.get("end_time", ""),
            "cnvs_status": r.get("cnvs_status", ""),
            "cnvs_dept": r.get("cnvs_dept"),
            "cnvs_rating_agent": r.get("cnvs_rating_agent"),
            "cnvs_rating_nps": r.get("cnvs_rating_nps"),
            "cnvs_msgcount": r.get("cnvs_msgcount") or r.get("msg_count", 0),
            "cnvs_reopened_count": r.get("cnvs_reopened_count", 0),
            "cnvs_channel": r.get("cnvs_channel", ""),
            "cnvs_description": r.get("cnvs_description", ""),
            "cnvs_bird": r.get("cnvs_bird", ""),
            "cnvs_tax_id": r.get("cnvs_tax_id", ""),
            "cnvs_software": r.get("cnvs_software", ""),
            "cnvs_contact_reason": r.get("cnvs_contact_reason"),
            "cnvs_occurrence": r.get("cnvs_occurrence"),
            "agnt_name": r.get("agnt_name") or r.get("agent", ""),
            "cnts_name": r.get("cnts_name") or r.get("contact", ""),
            "cnts_phone": r.get("cnts_phone") or r.get("phone", ""),
        }
