import logging
from datetime import datetime
from typing import Any

import xlsxwriter

from application.interfaces.exporter import DashboardDTO, ReportExporter

logger = logging.getLogger("excel_exporter")

DOW_LABELS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

COLOR_PRIMARY = "#1A3A5C"
COLOR_SECONDARY = "#2C6FBB"
COLOR_ACCENT = "#00A86B"
COLOR_ALERT = "#E74C3C"
COLOR_WARNING = "#F39C12"
COLOR_SURFACE = "#F5F7FA"
COLOR_TEXT = "#2D3748"
COLOR_TEXT_LIGHT = "#718096"

CATEGORY_QUALIDADE = "#D6E4F0"
CATEGORY_PRODUTIVIDADE = "#D5F5E3"
CATEGORY_OPERACIONAL = "#FEF9E7"
CATEGORY_PENALIDADE = "#FADBD8"


def auto_width(ws, header, data, padding=3):
    for col_idx in range(len(header)):
        max_len = len(str(header[col_idx]))
        for row in data:
            val = row[col_idx] if col_idx < len(row) else ""
            max_len = max(max_len, len(str(val)))
        ws.set_column(col_idx, col_idx, min(max_len + padding, 50))


class ExcelExporter(ReportExporter):
    def export_excel(self, filename: str, header: list[str], data: list[list[Any]], sheet_name: str = "Relatório", highlight_frt: bool = False):
        workbook = xlsxwriter.Workbook(filename)
        safe_sheet_name = sheet_name[:31]
        worksheet = workbook.add_worksheet(safe_sheet_name)

        header_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1, "font_size": 12, "align": "center", "valign": "vcenter"
        })
        cell_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left", "valign": "top"})
        alt_fmt = workbook.add_format({"border": 1, "bg_color": COLOR_SURFACE, "font_size": 11, "align": "left", "valign": "top"})
        num_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left", "valign": "top", "num_format": "0"})
        num_alt_fmt = workbook.add_format({"border": 1, "bg_color": COLOR_SURFACE, "font_size": 11, "align": "left", "valign": "top", "num_format": "0"})

        bad_frt = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006", "border": 1, "font_size": 11})
        acceptable_frt = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500", "border": 1, "font_size": 11})
        good_frt = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#006100", "border": 1, "font_size": 11})

        num_cols = {i for i, h in enumerate(header) if any(k in h for k in ["Documento", "Telefone"])}

        for col_num, col_name in enumerate(header):
            worksheet.write(0, col_num, col_name, header_fmt)

        for row_num, row_data in enumerate(data):
            is_alt = row_num % 2 == 0
            fmt = alt_fmt if is_alt else cell_fmt
            n_fmt = num_alt_fmt if is_alt else num_fmt
            for col_num, cell_value in enumerate(row_data):
                if col_num in num_cols:
                    try:
                        digits = "".join(filter(str.isdigit, str(cell_value)))
                        if digits: worksheet.write_number(row_num + 1, col_num, int(digits), n_fmt)
                        else: worksheet.write(row_num + 1, col_num, cell_value, n_fmt)
                    except: worksheet.write(row_num + 1, col_num, cell_value, n_fmt)
                else:
                    try:
                        if isinstance(cell_value, str) and cell_value.replace(".", "", 1).lstrip("-").isdigit():
                            val = float(cell_value) if "." in cell_value else int(cell_value)
                            worksheet.write(row_num + 1, col_num, val, fmt)
                        else: worksheet.write(row_num + 1, col_num, cell_value, fmt)
                    except: worksheet.write(row_num + 1, col_num, cell_value, fmt)

        if highlight_frt:
            for col_num, col_name in enumerate(header):
                if any(term in col_name for term in ["Média de Resposta", "Tempo médio", "FRT", "ART"]):
                    worksheet.conditional_format(1, col_num, len(data), col_num, {"type": "cell", "criteria": ">", "value": 30.0, "format": bad_frt})
                    worksheet.conditional_format(1, col_num, len(data), col_num, {"type": "cell", "criteria": "between", "minimum": 15.01, "maximum": 30.0, "format": acceptable_frt})
                    worksheet.conditional_format(1, col_num, len(data), col_num, {"type": "cell", "criteria": "<=", "value": 15.0, "format": good_frt})

        auto_width(worksheet, header, data)
        if data:
            worksheet.autofilter(0, 0, len(data), len(header) - 1)
            worksheet.freeze_panes(1, 0)
        workbook.close()

    def export_executive_dashboard(self, filename: str, dto: DashboardDTO):
        workbook = xlsxwriter.Workbook(filename)
        self._write_dashboard_tab(workbook, dto)
        if dto.bsc_header:
            self._write_bsc_tab(workbook, dto)
        self._write_quality_tab(workbook, dto)
        self._write_demand_tab(workbook, dto)
        self._write_data_sheet(workbook, dto)
        workbook.close()

    def export_annual_dashboard(self, filename: str, dto: DashboardDTO):
        workbook = xlsxwriter.Workbook(filename)
        self._write_dashboard_tab(workbook, dto)
        if dto.bsc_header:
            self._write_bsc_tab(workbook, dto)
        self._write_quality_tab(workbook, dto)
        self._write_demand_tab(workbook, dto)
        if dto.monthly_evolution:
            self._write_monthly_evolution_tab(workbook, dto)
        self._write_data_sheet(workbook, dto)
        workbook.close()

    def _write_bsc_tab(self, workbook: xlsxwriter.Workbook, dto: DashboardDTO):
        from infrastructure.exporters._bsc_writer import write_bsc_kpi_table
        bsc_ws = workbook.add_worksheet("BSC")

        fmts = {
            "title":      workbook.add_format({"bold": True, "font_size": 16, "font_color": COLOR_PRIMARY}),
            "header":     workbook.add_format({"bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1, "font_size": 11, "align": "center", "valign": "vcenter"}),
            "header_kpi": workbook.add_format({"bold": True, "bg_color": COLOR_SECONDARY, "font_color": "#FFFFFF", "border": 1, "font_size": 11, "align": "center", "valign": "vcenter"}),
            "label":      workbook.add_format({"bold": True, "bg_color": COLOR_SURFACE, "border": 1, "font_size": 11, "align": "left"}),
            "cell":       workbook.add_format({"border": 1, "font_size": 11, "align": "left"}),
            "cell_alt":   workbook.add_format({"border": 1, "font_size": 11, "align": "left", "bg_color": COLOR_SURFACE}),
            "kpi":        workbook.add_format({"bold": True, "border": 1, "font_size": 11, "align": "center", "font_color": COLOR_SECONDARY}),
            "kpi_alt":    workbook.add_format({"bold": True, "border": 1, "font_size": 11, "align": "center", "font_color": COLOR_SECONDARY, "bg_color": "#DDEEFF"}),
            "total":      workbook.add_format({"bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1, "font_size": 11, "align": "left"}),
            "total_kpi":  workbook.add_format({"bold": True, "bg_color": COLOR_ACCENT, "font_color": "#FFFFFF", "border": 2, "font_size": 12, "align": "center"}),
        }

        bsc_ws.write(0, 0, f"BALANCED SCORECARD — {dto.start_date} a {dto.end_date}", fmts["title"])

        kpi_cfg = next(iter(dto.bsc_kpi_config.values()), {"t1": [], "t2": []})

        next_row = write_bsc_kpi_table(
            bsc_ws, 2, "Desempenho dos Agentes",
            dto.bsc_header, dto.bsc_data_t1, kpi_cfg.get("t1", []),
            fmts, add_total_row=True
        )

        next_row = write_bsc_kpi_table(
            bsc_ws, next_row + 2, "Avaliações Extras",
            dto.bsc_header, dto.bsc_data_t2, kpi_cfg.get("t2", []),
            fmts, add_total_row=False
        )

        self._write_bsc_legend(bsc_ws, workbook, kpi_cfg, start_row=next_row + 1)

    def _write_bsc_legend(self, ws, workbook, kpi_cfg, start_row=36):
        legend_fmt = workbook.add_format({"bold": True, "font_size": 13, "font_color": COLOR_PRIMARY})
        cat_title_fmt = workbook.add_format({"bold": True, "font_size": 11, "font_color": COLOR_PRIMARY, "bg_color": COLOR_SURFACE, "border": 1})
        item_fmt = workbook.add_format({"bold": True, "font_size": 11, "font_color": COLOR_PRIMARY})
        desc_fmt = workbook.add_format({"font_size": 11, "text_wrap": True})

        # Legenda gerada a partir do KPI_CONFIG (genérica para qualquer empresa)
        legends = []
        for section_label, key in (
            ("QUALIDADE E SATISFAÇÃO", "t1"),
            ("AVALIAÇÕES EXTRAS", "t2"),
            ("PENALIDADES SETORIAIS", "penalidades_setoriais"),
        ):
            items = kpi_cfg.get(key, [])
            if not items:
                continue
            legends.append((f"CATEGORIA: {section_label}", "", True))
            for m in items:
                legends.append((m.get("name", "?"), m.get("description", "")))

        row = start_row
        ws.merge_range(row, 0, row, 10, "LEGENDA E EXPLICAÇÃO DAS MÉTRICAS (GUIA DIRETORIA)", legend_fmt)
        row += 2

        for entry in legends:
            name, desc, is_category = entry if len(entry) == 3 else (entry[0], entry[1], False)
            if is_category:
                ws.merge_range(row, 0, row, 10, f"  {name}", cat_title_fmt)
                row += 1
                continue
            ws.write(row, 0, name, item_fmt)
            ws.merge_range(row, 1, row, 10, desc, desc_fmt)
            row += 1

    def _write_dashboard_tab(self, workbook: xlsxwriter.Workbook, dto: DashboardDTO):
        ws = workbook.add_worksheet("Visão Geral")
        gm = dto.general_metrics

        def _safe_fmt(val, fmt=".2f"):
            if val is None: return "N/A"
            try: return f"{val:{fmt}}"
            except: return str(val)

        # ── Formatos ──────────────────────────────────────────────────────────
        title_fmt = workbook.add_format({"bold": True, "font_size": 22, "align": "center", "font_color": COLOR_PRIMARY})
        subtitle_fmt = workbook.add_format({"font_size": 11, "align": "center", "italic": True, "font_color": COLOR_TEXT_LIGHT})
        footer_fmt = workbook.add_format({"font_size": 9, "italic": True, "font_color": COLOR_TEXT_LIGHT})
        card_label_fmt = workbook.add_format({
            "bold": True, "font_size": 11, "border": 1, "align": "center", "valign": "vcenter",
            "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "text_wrap": True
        })
        card_val_fmt = workbook.add_format({
            "bold": True, "font_size": 24, "border": 1, "align": "center", "valign": "vcenter",
            "bg_color": "#F0F4FA", "font_color": COLOR_PRIMARY
        })
        workbook.add_format({
            "font_size": 10, "border": 1, "align": "center", "valign": "vcenter",
            "font_color": COLOR_ACCENT, "italic": True
        })
        section_fmt = workbook.add_format({
            "bold": True, "font_size": 13, "align": "left", "font_color": COLOR_PRIMARY, "bottom": 2
        })
        table_header_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "center", "valign": "vcenter", "text_wrap": True
        })
        table_cell_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left", "valign": "vcenter"})
        table_alt_fmt = workbook.add_format({"border": 1, "bg_color": COLOR_SURFACE, "font_size": 11, "align": "left", "valign": "vcenter"})
        table_num_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center", "valign": "vcenter"})
        table_alt_num_fmt = workbook.add_format({"border": 1, "bg_color": COLOR_SURFACE, "font_size": 11, "align": "center", "valign": "vcenter"})

        # ── Título + Período ─────────────────────────────────────────────────
        ws.merge_range(0, 0, 0, 14, dto.title, title_fmt)
        ws.merge_range(1, 0, 1, 14, f"Período: {dto.start_date} até {dto.end_date}", subtitle_fmt)

        # ── KPI Cards with MoM Trend ─────────────────────────────────────────
        prev = dto.prev_month_metrics or {}

        def _trend(current, previous, higher_is_better=True):
            if previous is None or previous == 0:
                return "", ""
            try:
                c = float(current) if current is not None else 0
                p = float(previous)
                if p == 0: return "", ""
                change = ((c - p) / p) * 100
                arrow = "↑" if change > 0 else ("↓" if change < 0 else "→")
                if higher_is_better:
                    color = COLOR_ACCENT if change >= 0 else COLOR_ALERT
                else:
                    color = COLOR_ALERT if change >= 0 else COLOR_ACCENT
                return f"{arrow} {abs(change):.1f}%", color
            except (TypeError, ValueError):
                return "", ""

        kpi_list = [
            ("Total de Chats", f"{gm.get('total_chats', 0)}", "total_chats", True),
            ("ART Médio (min)", _safe_fmt(gm.get('avg_art')), "avg_art", False),
            ("Duração Média (min)", _safe_fmt(gm.get('avg_duration')), "avg_duration", False),
            ("NPS Real", _safe_fmt(gm.get('real_nps'), ".1f"), "real_nps", True),
            ("SLA Compliance", (_safe_fmt(gm.get('sla_compliance')) + "%") if gm.get('sla_compliance') is not None else "N/A", "sla_compliance", True),
        ]

        for i, (label, val, prev_key, higher_better) in enumerate(kpi_list):
            col_start = i * 3
            ws.merge_range(3, col_start, 3, col_start + 2, label, card_label_fmt)
            ws.merge_range(4, col_start, 5, col_start + 2, val, card_val_fmt)
            trend_text, trend_color = _trend(gm.get(prev_key), prev.get(prev_key), higher_better)
            if trend_text:
                trend_fmt = workbook.add_format({
                    "font_size": 10, "border": 1, "align": "center", "valign": "vcenter",
                    "font_color": trend_color, "bold": True
                })
                ws.merge_range(6, col_start, 6, col_start + 2, f"vs mês anterior: {trend_text}", trend_fmt)

        # ── Seção: Distribuição por Departamento ─────────────────────────────
        dept_start = 8
        ws.merge_range(dept_start, 0, dept_start, 5, "DISTRIBUIÇÃO POR DEPARTAMENTO", section_fmt)
        dept_start += 1

        dept_header = ["Departamento", "Chats", "% Total", "ART Médio (min)", "SLA %", "Retornantes", "% Retornantes"]
        for j, h in enumerate(dept_header):
            ws.write(dept_start, j, h, table_header_fmt)

        dept_data = dto.department_data or []
        dept_data.sort(key=lambda r: r[1] if isinstance(r[1], (int, float)) else 0, reverse=True)

        pct_ret_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center", "valign": "vcenter", "num_format": "0.0%"})
        pct_ret_alt_fmt = workbook.add_format({"border": 1, "bg_color": COLOR_SURFACE, "font_size": 11, "align": "center", "valign": "vcenter", "num_format": "0.0%"})

        for idx, row_data in enumerate(dept_data):
            r = dept_start + 1 + idx
            is_alt = idx % 2 == 0
            c_fmt = table_alt_fmt if is_alt else table_cell_fmt
            n_fmt = table_alt_num_fmt if is_alt else table_num_fmt
            p_fmt = pct_ret_alt_fmt if is_alt else pct_ret_fmt
            ws.write(r, 0, row_data[0], c_fmt)
            ws.write(r, 1, row_data[1], n_fmt)
            ws.write(r, 2, row_data[2], n_fmt)
            ws.write(r, 3, row_data[4], n_fmt)
            ws.write(r, 4, row_data[5], n_fmt)
            ws.write(r, 5, row_data[11], n_fmt)
            total_chats_dept = row_data[1] if isinstance(row_data[1], (int, float)) else 0
            returners_dept = row_data[11] if isinstance(row_data[11], (int, float)) else 0
            pct_ret = returners_dept / total_chats_dept if total_chats_dept > 0 else 0
            ws.write(r, 6, pct_ret, p_fmt)

        dept_end = dept_start + 1 + len(dept_data)

        # ── Charts ────────────────────────────────────────────────────────────
        data_sheet = workbook.add_worksheet("_data_dash")
        data_sheet.hide()

        chart_title_font = {"bold": True, "size": 13, "color": COLOR_PRIMARY}

        # NPS Distribution → Donut (professional colors)
        data_sheet.write(0, 0, "NPS Category")
        data_sheet.write(0, 1, "Count")
        nps_order = {"promoters": "Promotores", "passives": "Neutros", "detractors": "Detratores"}
        row_idx = 1
        for key, label in nps_order.items():
            data_sheet.write(row_idx, 0, label)
            data_sheet.write(row_idx, 1, dto.nps_distribution.get(key, 0))
            row_idx += 1

        chart_nps = workbook.add_chart({"type": "doughnut"})
        chart_nps.add_series({
            "name": "NPS",
            "categories": "='_data_dash'!$A$2:$A$4",
            "values": "='_data_dash'!$B$2:$B$4",
            "points": [
                {"fill": {"color": COLOR_ACCENT}},
                {"fill": {"color": COLOR_WARNING}},
                {"fill": {"color": COLOR_ALERT}},
            ],
            "data_labels": {
                "percentage": True, "category": True,
                "position": "outside_end", "leader_lines": True,
                "font": {"bold": True, "size": 11, "color": COLOR_TEXT}
            }
        })
        chart_nps.set_title({"name": "Distribuição NPS", "name_font": chart_title_font})
        chart_nps.set_legend({"font": {"size": 11}})
        chart_nps.set_size({"width": 500, "height": 350})
        ws.insert_chart(dept_end + 2, 0, chart_nps, {"x_offset": 10, "y_offset": 10})

        # Topics → Bar (horizontal)
        data_sheet.write(0, 3, "Motivo")
        data_sheet.write(0, 4, "Count")
        for i, item in enumerate(dto.topic_data):
            data_sheet.write(i + 1, 3, item["label"])
            data_sheet.write(i + 1, 4, item["value"])

        if dto.topic_data:
            chart_topics = workbook.add_chart({"type": "bar"})
            chart_topics.add_series({
                "name": "Motivos",
                "categories": f"='_data_dash'!$D$2:$D${len(dto.topic_data)+1}",
                "values": f"='_data_dash'!$E$2:$E${len(dto.topic_data)+1}",
                "fill": {"color": COLOR_SECONDARY},
                "data_labels": {"value": True, "font": {"size": 10}}
            })
            chart_topics.set_title({"name": "Top Motivos de Contato", "name_font": chart_title_font})
            chart_topics.set_legend({"none": True})
            chart_topics.set_size({"width": 500, "height": 350})
            ws.insert_chart(dept_end + 2, 8, chart_topics, {"x_offset": 10, "y_offset": 10})

        # Rating Distribution → Column with gradient
        data_sheet.write(0, 6, "Rating")
        data_sheet.write(0, 7, "Count")
        for i, (cat, val) in enumerate(dto.rating_distribution.items()):
            data_sheet.write(i + 1, 6, f"Nota {cat}")
            data_sheet.write(i + 1, 7, val)

        chart_rating = workbook.add_chart({"type": "column"})
        chart_rating.add_series({
            "name": "Avaliações",
            "categories": "='_data_dash'!$G$2:$G$6",
            "values": "='_data_dash'!$H$2:$H$6",
            "fill": {"color": COLOR_ACCENT, "none": True},
            "line": {"color": COLOR_ACCENT, "width": 2},
            "data_labels": {"value": True, "font": {"size": 11, "bold": True}},
            "marker": {"type": "square", "size": 8, "fill": {"color": COLOR_ACCENT}},
        })
        chart_rating.set_title({"name": "Distribuição de Notas (CSAT)", "name_font": chart_title_font})
        chart_rating.set_legend({"none": True})
        chart_rating.set_y_axis({"major_gridlines": {"visible": True, "line": {"color": "#E0E0E0"}}})
        chart_rating.set_size({"width": 500, "height": 350})
        ws.insert_chart(dept_end + 22, 0, chart_rating, {"x_offset": 10})

        # Day-of-week → Column with data labels
        if dto.dow_data:
            data_sheet.write(0, 9, "Dia")
            data_sheet.write(0, 10, "Chats")
            for i, item in enumerate(dto.dow_data):
                data_sheet.write(i + 1, 9, item["day"])
                data_sheet.write(i + 1, 10, item["value"])

            chart_dow = workbook.add_chart({"type": "column"})
            chart_dow.add_series({
                "name": "Chats",
                "categories": "='_data_dash'!$J$2:$J$8",
                "values": "='_data_dash'!$K$2:$K$8",
                "fill": {"color": COLOR_ALERT},
                "data_labels": {"value": True, "font": {"size": 10, "bold": True}},
            })
            chart_dow.set_title({"name": "Chats por Dia da Semana", "name_font": chart_title_font})
            chart_dow.set_legend({"none": True})
            chart_dow.set_y_axis({"major_gridlines": {"visible": True, "line": {"color": "#E0E0E0"}}})
            chart_dow.set_size({"width": 500, "height": 350})
            ws.insert_chart(dept_end + 22, 8, chart_dow, {"x_offset": 10})

        # ── Rodapé ────────────────────────────────────────────────────────────
        gen_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        footer_row = dept_end + 42
        ws.merge_range(footer_row, 0, footer_row, 14,
                       f"Gerado em {gen_time} | Fonte: Omnichannel MCP | Período: {dto.start_date} a {dto.end_date}",
                       footer_fmt)

        # Column widths
        ws.set_column(0, 0, 28)
        for c in range(1, 10):
            ws.set_column(c, c, 16)

    def _write_quality_tab(self, workbook: xlsxwriter.Workbook, dto: DashboardDTO):
        ws = workbook.add_worksheet("Qualidade")

        title_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": COLOR_PRIMARY})
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "center", "valign": "vcenter"
        })
        cell_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left"})
        alt_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left", "bg_color": COLOR_SURFACE})
        num_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center"})
        alt_num_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center", "bg_color": COLOR_SURFACE})
        total_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "left"
        })
        total_num_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "center"
        })
        section_header_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_SECONDARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "left", "valign": "vcenter"
        })

        # ── Rating Distribution (1-5) ─────────────────────────────────────────
        ws.write(0, 0, "Distribuição de Avaliações Técnicas (1-5)", title_fmt)

        rating_header = ["Agente", "Nota 1", "Nota 2", "Nota 3", "Nota 4", "Nota 5", "TOTAL"]
        for j, h in enumerate(rating_header):
            ws.write(2, j, h, header_fmt)

        rows = dto.agent_rating_detail or []
        for idx, row_data in enumerate(rows):
            r = 3 + idx
            is_total = row_data[0] == "TOTAL"
            if is_total:
                c_fmt = total_fmt
                n_fmt = total_num_fmt
            else:
                is_alt = idx % 2 == 0
                c_fmt = alt_fmt if is_alt else cell_fmt
                n_fmt = alt_num_fmt if is_alt else num_fmt

            ws.write(r, 0, row_data[0], c_fmt)
            for j in range(1, len(row_data)):
                ws.write(r, j, row_data[j], n_fmt)

        # ── NPS Distribution (1-10) ───────────────────────────────────────────
        nps_title_row = 3 + len(rows) + 1
        ws.write(nps_title_row, 0, "Distribuição de Notas NPS (1-10)", title_fmt)

        nps_header = ["Agente"] + [f"NPS {i}" for i in range(1, 11)] + ["TOTAL"]
        h_row = nps_title_row + 1
        for j, h in enumerate(nps_header):
            ws.write(h_row, j, h, header_fmt)

        nps_rows = dto.agent_nps_detail or []
        for idx, row_data in enumerate(nps_rows):
            r = h_row + 1 + idx
            is_total = row_data[0] == "TOTAL"
            if is_total:
                c_fmt = total_fmt
                n_fmt = total_num_fmt
            else:
                is_alt = idx % 2 == 0
                c_fmt = alt_fmt if is_alt else cell_fmt
                n_fmt = alt_num_fmt if is_alt else num_fmt

            ws.write(r, 0, row_data[0], c_fmt)
            for j in range(1, len(row_data)):
                ws.write(r, j, row_data[j], n_fmt)

        # ── Feedback Summary ──────────────────────────────────────────────────
        gm = dto.general_metrics
        feedback_start = r + 2
        ws.merge_range(feedback_start, 0, feedback_start, 4, "Feedback de Atendimento (Categoria: Qualidade e Satisfação)", title_fmt)
        feedback_start += 1

        ws.merge_range(feedback_start, 0, feedback_start+1, 1, "Elogios (nota 4-5)", section_header_fmt)
        ws.merge_range(feedback_start, 2, feedback_start+1, 4, "Feedback Negativo (nota 1-2)", section_header_fmt)
        feedback_start += 1

        compliments = gm.get("compliments", 0)
        negatives = gm.get("negatives", 0)
        pct_compl = gm.get("pct_compliments", 0)
        pct_neg = gm.get("pct_negatives", 0)

        feedback_data = [
            ("TOTAL", compliments, "TOTAL", negatives),
            ("% Avaliados", f"{pct_compl}%" if pct_compl != "N/A" else "N/A", "% Avaliados", f"{pct_neg}%" if pct_neg != "N/A" else "N/A"),
        ]

        for idx, (l1, v1, l2, v2) in enumerate(feedback_data):
            ro = feedback_start + idx
            is_alt = idx % 2 == 0
            c_fmt = alt_fmt if is_alt else cell_fmt
            n_fmt = alt_num_fmt if is_alt else num_fmt
            ws.write(ro, 0, l1, c_fmt)
            ws.write(ro, 1, v1, n_fmt)
            ws.write(ro, 2, l2, c_fmt)
            ws.write(ro, 3, v2, n_fmt)

        # ── NPS Calculator (com fórmulas Excel) ───────────────────────────────
        from xlsxwriter.utility import xl_rowcol_to_cell as _xc

        calc_start = feedback_start + len(feedback_data) + 1
        ws.merge_range(calc_start, 0, calc_start, 4, "CALCULADORA DE NPS", title_fmt)
        calc_start += 1

        tr = h_row + len(nps_rows)
        t_cell = _xc(tr, 11)
        p9 = _xc(tr, 9)
        p10 = _xc(tr, 10)
        ne7 = _xc(tr, 7)
        ne8 = _xc(tr, 8)
        d_cells = [_xc(tr, i) for i in range(1, 7)]

        prom_f = f"={p9}+{p10}"
        neut_f = f"={ne7}+{ne8}"
        detr_f = f"={'+'.join(d_cells)}"
        nps_f = f"=ROUND(({p9}+{p10}-({' + '.join(d_cells)}))/{t_cell}*100,2)"

        calc_data = [
            ("Total de Respostas (Válidas)", f"={t_cell}"),
            ("Quantidade de Promotores (9-10)", prom_f),
            ("Quantidade de Neutros (7-8)", neut_f),
            ("Quantidade de Detratores (1-6)", detr_f),
            ("NPS CALCULADO", nps_f),
        ]

        nps_row = calc_start + 4
        nps_def_fmt = workbook.add_format({
            "bold": True, "border": 2, "font_size": 14, "align": "left", "bg_color": COLOR_TEXT_LIGHT, "font_color": "#FFFFFF"
        })
        nps_val_fmt = workbook.add_format({
            "bold": True, "border": 2, "font_size": 14, "align": "center", "bg_color": COLOR_TEXT_LIGHT, "font_color": "#FFFFFF"
        })
        ws.conditional_format(nps_row, 0, nps_row, 0, {
            "type": "cell", "criteria": ">=", "value": 70,
            "format": workbook.add_format({"bg_color": COLOR_ACCENT, "font_color": "#FFFFFF", "bold": True, "border": 2, "font_size": 14, "align": "left"})
        })
        ws.conditional_format(nps_row, 1, nps_row, 1, {
            "type": "cell", "criteria": ">=", "value": 70,
            "format": workbook.add_format({"bg_color": COLOR_ACCENT, "font_color": "#FFFFFF", "bold": True, "border": 2, "font_size": 14, "align": "center"})
        })
        ws.conditional_format(nps_row, 0, nps_row, 0, {
            "type": "cell", "criteria": "between", "minimum": 50, "maximum": 69.99,
            "format": workbook.add_format({"bg_color": COLOR_WARNING, "font_color": "#FFFFFF", "bold": True, "border": 2, "font_size": 14, "align": "left"})
        })
        ws.conditional_format(nps_row, 1, nps_row, 1, {
            "type": "cell", "criteria": "between", "minimum": 50, "maximum": 69.99,
            "format": workbook.add_format({"bg_color": COLOR_WARNING, "font_color": "#FFFFFF", "bold": True, "border": 2, "font_size": 14, "align": "center"})
        })
        ws.conditional_format(nps_row, 0, nps_row, 0, {
            "type": "cell", "criteria": "<", "value": 50,
            "format": workbook.add_format({"bg_color": COLOR_ALERT, "font_color": "#FFFFFF", "bold": True, "border": 2, "font_size": 14, "align": "left"})
        })
        ws.conditional_format(nps_row, 1, nps_row, 1, {
            "type": "cell", "criteria": "<", "value": 50,
            "format": workbook.add_format({"bg_color": COLOR_ALERT, "font_color": "#FFFFFF", "bold": True, "border": 2, "font_size": 14, "align": "center"})
        })

        for idx, (lbl, val) in enumerate(calc_data):
            ro = calc_start + idx
            is_nps = "NPS CALCULADO" in lbl
            if is_nps:
                c_fmt_f = nps_def_fmt
                n_fmt_f = nps_val_fmt
            else:
                is_alt = idx % 2 == 0
                c_fmt_f = alt_fmt if is_alt else cell_fmt
                n_fmt_f = alt_num_fmt if is_alt else num_fmt
            ws.write(ro, 0, lbl, c_fmt_f)
            ws.write_formula(ro, 1, val, n_fmt_f)

        # ── Agent Performance Table (moved from Desempenho Agentes) ──────────
        if dto.tabular_header and dto.tabular_data:
            agent_start = calc_start + 6
            ws.merge_range(agent_start, 0, agent_start, 16, "Desempenho dos Agentes", title_fmt)
            agent_start += 1

            ag_header = dto.tabular_header[2:]  # skip Dept e Grupo
            for j, h in enumerate(ag_header):
                ws.write(agent_start, j, h, header_fmt)

            ag_data = dto.tabular_data
            for row_idx, row_data in enumerate(ag_data):
                r = agent_start + 1 + row_idx
                is_alt = row_idx % 2 == 0
                c_fmt = alt_fmt if is_alt else cell_fmt
                n_fmt = alt_num_fmt if is_alt else num_fmt
                is_total = row_data[2] == "TOTAIS"
                if is_total:
                    t_fmt = total_fmt
                    t_n_fmt = total_num_fmt
                for j in range(2, len(row_data)):
                    fmt = t_fmt if (is_total and j == 2) else (t_n_fmt if is_total else (
                        n_fmt if isinstance(row_data[j], (int, float)) else c_fmt
                    ))
                    ws.write(r, j - 2, row_data[j], fmt)

            safe_row = agent_start + 1 + len(ag_data)
            for j, h in enumerate(ag_header):
                if "ART" in h or "FRT" in h:
                    ws.conditional_format(agent_start + 1, j, safe_row - 1, j,
                        {"type": "cell", "criteria": ">", "value": 30.0, "format": workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006", "border": 1})})
                if "SLA" in h:
                    ws.conditional_format(agent_start + 1, j, safe_row - 1, j,
                        {"type": "cell", "criteria": "<", "value": 90.0, "format": workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006", "border": 1})})

        # Column widths
        ws.set_column(0, 0, 36)
        for c in range(1, 20):
            ws.set_column(c, c, 14)

        # ── Charts ────────────────────────────────────────────────────────────
        data_sheet = workbook.add_worksheet("_data_qualidade")
        data_sheet.hide()

        chart_title_font = {"bold": True, "size": 13, "color": COLOR_PRIMARY}

        # NPS Distribution → Donut
        data_sheet.write(0, 0, "Categoria")
        data_sheet.write(0, 1, "Quantidade")
        nps_cats = {"promoters": "Promotores (9-10)", "passives": "Neutros (7-8)", "detractors": "Detratores (1-6)"}
        for i, (key, label) in enumerate(nps_cats.items()):
            data_sheet.write(i + 1, 0, label)
            data_sheet.write(i + 1, 1, dto.nps_distribution.get(key, 0))

        chart_nps = workbook.add_chart({"type": "doughnut"})
        chart_nps.add_series({
            "name": "NPS",
            "categories": "='_data_qualidade'!$A$2:$A$4",
            "values": "='_data_qualidade'!$B$2:$B$4",
            "points": [
                {"fill": {"color": COLOR_ACCENT}},
                {"fill": {"color": COLOR_WARNING}},
                {"fill": {"color": COLOR_ALERT}},
            ],
            "data_labels": {
                "percentage": True, "category": True,
                "position": "outside_end", "leader_lines": True,
                "font": {"bold": True, "size": 11, "color": COLOR_TEXT}
            }
        })
        chart_nps.set_title({"name": "Distribuição NPS", "name_font": chart_title_font})
        chart_nps.set_legend({"font": {"size": 11}})
        chart_nps.set_size({"width": 450, "height": 320})
        chart_row = safe_row + 3 if dto.tabular_data else calc_start + 8
        ws.insert_chart(chart_row, 0, chart_nps, {"x_offset": 10, "y_offset": 10})

        # Rating Distribution → Column chart
        data_sheet.write(0, 3, "Nota")
        data_sheet.write(0, 4, "Quantidade")
        for i, (cat, val) in enumerate(dto.rating_distribution.items()):
            data_sheet.write(i + 1, 3, f"Nota {cat}")
            data_sheet.write(i + 1, 4, val)

        chart_rating = workbook.add_chart({"type": "column"})
        chart_rating.add_series({
            "name": "Avaliações",
            "categories": "='_data_qualidade'!$D$2:$D$6",
            "values": "='_data_qualidade'!$E$2:$E$6",
            "fill": {"color": COLOR_SECONDARY},
            "data_labels": {"value": True, "font": {"size": 10, "bold": True}},
        })
        chart_rating.set_title({"name": "Distribuição de Notas Técnicas", "name_font": chart_title_font})
        chart_rating.set_legend({"none": True})
        chart_rating.set_y_axis({"major_gridlines": {"visible": True, "line": {"color": "#E0E0E0"}}})
        chart_rating.set_size({"width": 450, "height": 320})
        ws.insert_chart(chart_row, 8, chart_rating, {"x_offset": 10, "y_offset": 10})

    def _write_demand_tab(self, workbook: xlsxwriter.Workbook, dto: DashboardDTO):
        ws = workbook.add_worksheet("Demanda")
        dto.general_metrics.get("total_chats", 0)

        title_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": COLOR_PRIMARY})
        section_fmt = workbook.add_format({"bold": True, "font_size": 12, "font_color": COLOR_PRIMARY, "bottom": 2})
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "center", "valign": "vcenter"
        })
        cell_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left"})
        alt_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left", "bg_color": COLOR_SURFACE})
        num_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center"})
        alt_num_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center", "bg_color": COLOR_SURFACE})
        total_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "left", "valign": "vcenter"
        })
        total_num_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "center", "valign": "vcenter"
        })

        # ── Section 1: Heatmap ───────────────────────────────────────────────
        ws.merge_range(0, 0, 0, 3, f"Demanda — {dto.start_date} a {dto.end_date}", title_fmt)

        ws.write(2, 0, "Mapa de Calor (Chats por Dia / Hora)", section_fmt)

        # Header row
        ws.write(3, 0, "Dia / Hora", header_fmt)
        for h in range(24):
            ws.write(3, h + 1, f"{h}h", header_fmt)
        ws.write(3, 25, "TOTAL", header_fmt)

        heatmap_dict = {(item["day"], item["hour"]): item["value"] for item in dto.heatmap_data}
        total_by_day = [0] * 7
        total_by_hour = [0] * 24

        for d, day in enumerate(DOW_LABELS):
            ws.write(d + 4, 0, day, header_fmt)
            day_total = 0
            for h in range(24):
                val = heatmap_dict.get((d, h), 0)
                ws.write(d + 4, h + 1, val, cell_fmt)
                day_total += val
                total_by_hour[h] += val
            total_by_day[d] = day_total
            ws.write(d + 4, 25, day_total, num_fmt)

        ws.write(11, 0, "TOTAL", total_fmt)
        grand_total = 0
        for h in range(24):
            ws.write(11, h + 1, total_by_hour[h], total_num_fmt)
            grand_total += total_by_hour[h]
        ws.write(11, 25, grand_total, total_num_fmt)

        ws.conditional_format(4, 1, 10, 24, {
            "type": "2_color_scale",
            "min_color": "#FFFFFF",
            "max_color": COLOR_ALERT
        })

        ws.set_column(0, 0, 14)
        for col in range(1, 26):
            ws.set_column(col, col, 6)

        # ── Section 2: Top Motivos ────────────────────────────────────────────
        topics_start = 14
        ws.merge_range(topics_start, 0, topics_start, 3, "Principais Motivos de Contato", section_fmt)
        topics_start += 1

        topic_header = ["Motivo", "Atendimentos", "% do Total"]
        for j, h in enumerate(topic_header):
            ws.write(topics_start, j, h, header_fmt)

        topic_sum = sum(x["value"] for x in dto.topic_data) or 1
        for idx, item in enumerate(dto.topic_data):
            r = topics_start + 1 + idx
            is_alt = idx % 2 == 0
            c_fmt = alt_fmt if is_alt else cell_fmt
            n_fmt = alt_num_fmt if is_alt else num_fmt
            ws.write(r, 0, item["label"], c_fmt)
            ws.write(r, 1, item["value"], n_fmt)
            pct = round(item["value"] / topic_sum * 100, 1)
            ws.write(r, 2, f"{pct}%", n_fmt)

        t_row = topics_start + 1 + len(dto.topic_data)
        ws.write(t_row, 0, "TOTAL", total_fmt)
        ws.write(t_row, 1, topic_sum, total_num_fmt)
        ws.write(t_row, 2, "100%", total_num_fmt)

        # ── Section 3: Top Ocorrências ────────────────────────────────────────
        occ_start = t_row + 2
        ws.merge_range(occ_start, 0, occ_start, 3, "Principais Ocorrências", section_fmt)
        occ_start += 1

        occ_header = ["Ocorrência", "Atendimentos", "% do Total"]
        for j, h in enumerate(occ_header):
            ws.write(occ_start, j, h, header_fmt)

        occ_sum = sum(x["value"] for x in dto.occurrence_data) or 1
        for idx, item in enumerate(dto.occurrence_data):
            r = occ_start + 1 + idx
            is_alt = idx % 2 == 0
            c_fmt = alt_fmt if is_alt else cell_fmt
            n_fmt = alt_num_fmt if is_alt else num_fmt
            ws.write(r, 0, item["label"], c_fmt)
            ws.write(r, 1, item["value"], n_fmt)
            pct = round(item["value"] / occ_sum * 100, 1)
            ws.write(r, 2, f"{pct}%", n_fmt)

        o_row = occ_start + 1 + len(dto.occurrence_data)
        ws.write(o_row, 0, "TOTAL", total_fmt)
        ws.write(o_row, 1, occ_sum, total_num_fmt)
        ws.write(o_row, 2, "100%", total_num_fmt)

        # ── Section 4: Chats por Dia da Semana ───────────────────────────────
        dow_start = o_row + 2
        ws.merge_range(dow_start, 0, dow_start, 3, "Distribuição por Dia da Semana", section_fmt)
        dow_start += 1

        dow_header = ["Dia", "Chats"]
        for j, h in enumerate(dow_header):
            ws.write(dow_start, j, h, header_fmt)

        if dto.dow_data:
            for idx, item in enumerate(dto.dow_data):
                r = dow_start + 1 + idx
                is_alt = idx % 2 == 0
                c_fmt = alt_fmt if is_alt else cell_fmt
                n_fmt = alt_num_fmt if is_alt else num_fmt
                ws.write(r, 0, item["day"], c_fmt)
                ws.write(r, 1, item["value"], n_fmt)

        ws.set_column(0, 0, 35)
        ws.set_column(1, 1, 16)
        ws.set_column(2, 2, 14)

        # ── Charts ────────────────────────────────────────────────────────────
        data_sheet = workbook.add_worksheet("_data_demanda")
        data_sheet.hide()

        chart_title_font = {"bold": True, "size": 13, "color": COLOR_PRIMARY}

        # Top Motivos → Bar chart
        if dto.topic_data:
            data_sheet.write(0, 0, "Motivo")
            data_sheet.write(0, 1, "Atendimentos")
            for i, item in enumerate(dto.topic_data):
                data_sheet.write(i + 1, 0, item["label"])
                data_sheet.write(i + 1, 1, item["value"])

            chart_motivos = workbook.add_chart({"type": "bar"})
            chart_motivos.add_series({
                "name": "Atendimentos",
                "categories": f"='_data_demanda'!$A$2:$A${len(dto.topic_data)+1}",
                "values": f"='_data_demanda'!$B$2:$B${len(dto.topic_data)+1}",
                "fill": {"color": COLOR_SECONDARY},
                "data_labels": {"value": True, "font": {"size": 10, "bold": True}},
            })
            chart_motivos.set_title({"name": "Principais Motivos de Contato", "name_font": chart_title_font})
            chart_motivos.set_legend({"none": True})
            chart_motivos.set_x_axis({"reverse": True})
            chart_motivos.set_size({"width": 600, "height": 380})
            ws.insert_chart(o_row + 3, 0, chart_motivos, {"x_offset": 10, "y_offset": 10})

        # Top Ocorrências → Bar chart
        if dto.occurrence_data:
            data_sheet.write(0, 3, "Ocorrência")
            data_sheet.write(0, 4, "Atendimentos")
            for i, item in enumerate(dto.occurrence_data):
                data_sheet.write(i + 1, 3, item["label"])
                data_sheet.write(i + 1, 4, item["value"])

            chart_ocorr = workbook.add_chart({"type": "bar"})
            chart_ocorr.add_series({
                "name": "Atendimentos",
                "categories": f"='_data_demanda'!$D$2:$D${len(dto.occurrence_data)+1}",
                "values": f"='_data_demanda'!$E$2:$E${len(dto.occurrence_data)+1}",
                "fill": {"color": COLOR_WARNING},
                "data_labels": {"value": True, "font": {"size": 10, "bold": True}},
            })
            chart_ocorr.set_title({"name": "Principais Ocorrências", "name_font": chart_title_font})
            chart_ocorr.set_legend({"none": True})
            chart_ocorr.set_x_axis({"reverse": True})
            chart_ocorr.set_size({"width": 600, "height": 380})
            ws.insert_chart(o_row + 3, 8, chart_ocorr, {"x_offset": 10, "y_offset": 10})

        # Chats por Dia da Semana → Column chart
        if dto.dow_data:
            data_sheet.write(0, 6, "Dia")
            data_sheet.write(0, 7, "Chats")
            for i, item in enumerate(dto.dow_data):
                data_sheet.write(i + 1, 6, item["day"])
                data_sheet.write(i + 1, 7, item["value"])

            chart_dow = workbook.add_chart({"type": "column"})
            chart_dow.add_series({
                "name": "Chats",
                "categories": "='_data_demanda'!$G$2:$G$8",
                "values": "='_data_demanda'!$H$2:$H$8",
                "fill": {"color": COLOR_ACCENT},
                "data_labels": {"value": True, "font": {"size": 10, "bold": True}},
            })
            chart_dow.set_title({"name": "Chats por Dia da Semana", "name_font": chart_title_font})
            chart_dow.set_legend({"none": True})
            chart_dow.set_y_axis({"major_gridlines": {"visible": True, "line": {"color": "#E0E0E0"}}})
            chart_dow.set_size({"width": 600, "height": 380})
            ws.insert_chart(o_row + 28, 0, chart_dow, {"x_offset": 10, "y_offset": 10})

        # Heatmap overview → Column chart (total by hour)
        total_by_hour = [0] * 24
        for item in dto.heatmap_data:
            h = item["hour"]
            total_by_hour[h] += item["value"]

        data_sheet.write(0, 9, "Hora")
        data_sheet.write(0, 10, "Chats")
        for h in range(24):
            data_sheet.write(h + 1, 9, f"{h}h")
            data_sheet.write(h + 1, 10, total_by_hour[h])

        chart_hourly = workbook.add_chart({"type": "column"})
        chart_hourly.add_series({
            "name": "Chats",
            "categories": "='_data_demanda'!$J$2:$J$25",
            "values": "='_data_demanda'!$K$2:$K$25",
            "fill": {"color": COLOR_PRIMARY},
            "data_labels": {"value": True, "font": {"size": 9}},
        })
        chart_hourly.set_title({"name": "Distribuição por Hora do Dia", "name_font": chart_title_font})
        chart_hourly.set_legend({"none": True})
        chart_hourly.set_y_axis({"major_gridlines": {"visible": True, "line": {"color": "#E0E0E0"}}})
        chart_hourly.set_size({"width": 600, "height": 380})
        ws.insert_chart(o_row + 28, 8, chart_hourly, {"x_offset": 10, "y_offset": 10})

    def _write_data_sheet(self, workbook: xlsxwriter.Workbook, dto: DashboardDTO):
        data_sheet = workbook.add_worksheet("_data")
        data_sheet.write(0, 0, "Métrica")
        data_sheet.write(0, 1, "Valor")
        gm = dto.general_metrics
        for i, (key, val) in enumerate(gm.items()):
            data_sheet.write(i + 1, 0, str(key))
            data_sheet.write(i + 1, 1, val if val is not None else "")
        data_sheet.hide()

    def _write_monthly_evolution_tab(self, workbook: xlsxwriter.Workbook, dto: DashboardDTO):
        ws = workbook.add_worksheet("Evolução Mensal")

        title_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": COLOR_PRIMARY})
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": COLOR_PRIMARY, "font_color": "#FFFFFF", "border": 1,
            "font_size": 11, "align": "center", "valign": "vcenter"
        })
        cell_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center"})
        alt_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "center", "bg_color": COLOR_SURFACE})
        label_fmt = workbook.add_format({"border": 1, "font_size": 11, "align": "left", "bold": True})

        ws.merge_range(0, 0, 0, 11, f"Evolução Mensal — {dto.period_label}", title_fmt)

        keys_order = [
            ("total_chats", "Total de Chats"),
            ("total_msgs", "Total de Msgs"),
            ("avg_art", "ART Médio (min)"),
            ("sla_compliance", "SLA Compliance (%)"),
            ("avg_duration", "Duração Média (min)"),
            ("real_nps", "NPS Real"),
            ("avg_rating", "Nota Técnica Média"),
            ("compliments", "Elogios"),
            ("negatives", "Feedback Negativo"),
            ("unique_clients", "Clientes Únicos"),
            ("returners", "Retornantes"),
        ]

        month_labels = ["Mês"] + [k for k, _ in keys_order]
        for j, h in enumerate(month_labels):
            ws.write(2, j, h, header_fmt)

        for i, entry in enumerate(dto.monthly_evolution):
            r = 3 + i
            is_alt = i % 2 == 0
            c_fmt = alt_fmt if is_alt else cell_fmt
            ws.write(r, 0, entry.get("month", ""), label_fmt)
            for j, (key, _) in enumerate(keys_order):
                val = entry.get(key)
                if val is None:
                    ws.write(r, j + 1, "N/A", c_fmt)
                elif isinstance(val, float):
                    ws.write(r, j + 1, round(val, 2), c_fmt)
                else:
                    ws.write(r, j + 1, val, c_fmt)

        data_end = 3 + len(dto.monthly_evolution)

        chart_chats = workbook.add_chart({"type": "line"})
        chart_chats.add_series({
            "name": "Total de Chats",
            "categories": f"='Evolução Mensal'!$A$4:$A${data_end}",
            "values": f"='Evolução Mensal'!$B$4:$B${data_end}",
            "line": {"color": COLOR_SECONDARY, "width": 2.5},
            "marker": {"type": "circle", "size": 6, "fill": {"color": COLOR_SECONDARY}},
        })
        chart_chats.set_title({"name": "Evolução de Chats por Mês"})
        chart_chats.set_size({"width": 600, "height": 300})
        chart_chats.set_legend({"none": True})
        ws.insert_chart(2, 13, chart_chats)

        chart_art = workbook.add_chart({"type": "line"})
        chart_art.add_series({
            "name": "ART Médio",
            "categories": f"='Evolução Mensal'!$A$4:$A${data_end}",
            "values": f"='Evolução Mensal'!$D$4:$D${data_end}",
            "line": {"color": COLOR_ALERT, "width": 2.5},
            "marker": {"type": "diamond", "size": 6, "fill": {"color": COLOR_ALERT}},
        })
        chart_art.set_title({"name": "ART Médio por Mês"})
        chart_art.set_size({"width": 600, "height": 300})
        chart_art.set_legend({"none": True})
        ws.insert_chart(19, 13, chart_art)

        chart_nps = workbook.add_chart({"type": "line"})
        chart_nps.add_series({
            "name": "NPS Real",
            "categories": f"='Evolução Mensal'!$A$4:$A${data_end}",
            "values": f"='Evolução Mensal'!$G$4:$G${data_end}",
            "line": {"color": COLOR_ACCENT, "width": 2.5},
            "marker": {"type": "circle", "size": 6, "fill": {"color": COLOR_ACCENT}},
        })
        chart_nps.set_title({"name": "NPS Real por Mês"})
        chart_nps.set_size({"width": 600, "height": 300})
        chart_nps.set_legend({"none": True})
        ws.insert_chart(2, 25, chart_nps)

        ws.set_column(0, 0, 12)
        for c in range(1, 12):
            ws.set_column(c, c, 16)

    def export_agent_detailed(self, filename: str, agent_name: str, header: list[str], data: list[list[Any]]):
        self.export_excel(filename, header, data, "Atendimentos", highlight_frt=True)

    def export_summary(self, filename: str, title: str, start_date: str, end_date: str, summary_data: dict[str, Any], report_type: str = "monthly"):
        from infrastructure.exporters.markdown_exporter import MarkdownExporter
        md_exporter = MarkdownExporter()
        md_exporter.export_summary(filename, title, start_date, end_date, summary_data, report_type=report_type)
