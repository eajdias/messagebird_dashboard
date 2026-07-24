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


class CSVExporter:
    def generate(self, rows: list[dict[str, Any]]) -> bytes:
        buf = io.StringIO()
        buf.write("\ufeff")

        fieldnames = [col[0] for col in CSV_COLUMNS]
        labels = [col[1] for col in CSV_COLUMNS]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writerow(dict(zip(fieldnames, labels, strict=True)))

        for r in rows:
            flattened = dict(r)
            flattened["start_time"] = self._fmt(r.get("cnvs_created") or r.get("start_time"))
            writer.writerow(flattened)

        return buf.getvalue().encode("utf-8")

    def _fmt(self, val: Any) -> str:
        if not val:
            return ""
        try:
            from datetime import datetime

            if isinstance(val, datetime):
                return val.strftime("%d/%m/%Y %H:%M")
            return str(val)[:19]
        except Exception:
            return str(val)
