"""CSV Exporter — generates conversation CSV files with BOM for Excel compatibility."""

from __future__ import annotations

import csv
import io
from typing import Any

CSV_COLUMNS = [
    ("contact", "Contato"),
    ("phone", "Telefone"),
    ("agent", "Agente"),
    ("department", "Departamento"),
    ("msg_count", "Mensagens"),
    ("rating", "Nota (Agente)"),
    ("nps", "NPS"),
    ("art_minutes", "ART (min)"),
    ("start_time", "Data"),
]


def _normalize_row(r: dict[str, Any]) -> dict[str, Any]:
    from domain import constants

    dept_id = r.get("cnvs_dept")
    dept_label = ""
    if "department" in r and r["department"] and isinstance(r["department"], str) and not r["department"].isdigit():
        dept_label = r["department"]
    elif dept_id is not None:
        dept_label = constants.resolve_dept(int(dept_id) if isinstance(dept_id, str) else dept_id)

    return {
        "contact": r.get("cnts_name") or r.get("contact", ""),
        "phone": r.get("cnts_phone") or r.get("phone", ""),
        "agent": r.get("agnt_name") or r.get("agent", ""),
        "department": dept_label,
        "msg_count": r.get("cnvs_msgcount") or r.get("msg_count", 0),
        "rating": r.get("cnvs_rating_agent") if r.get("cnvs_rating_agent") is not None else r.get("rating"),
        "nps": r.get("cnvs_rating_nps") if r.get("cnvs_rating_nps") is not None else r.get("nps"),
        "art_minutes": r.get("cnvs_art_minutes") if r.get("cnvs_art_minutes") is not None else r.get("art_minutes"),
        "start_time": _fmt_ts(r.get("cnvs_created") or r.get("start_time")),
    }


def _fmt_ts(val: Any) -> str:
    if not val:
        return ""
    try:
        from datetime import datetime

        if isinstance(val, datetime):
            return val.strftime("%d/%m/%Y %H:%M")
        return str(val)[:19]
    except Exception:
        return str(val)


class CSVExporter:
    def generate(self, rows: list[dict[str, Any]]) -> bytes:
        buf = io.StringIO()
        buf.write("\ufeff")

        fieldnames = [col[0] for col in CSV_COLUMNS]
        labels = [col[1] for col in CSV_COLUMNS]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writerow(dict(zip(fieldnames, labels, strict=True)))

        for r in rows:
            writer.writerow(_normalize_row(r))

        return buf.getvalue().encode("utf-8")
