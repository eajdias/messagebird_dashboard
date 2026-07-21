from xlsxwriter.utility import xl_rowcol_to_cell

_META_COL = 1
_PESO_COL = 2
_TIPO_COL = 3
_FIRST_AGENT_COL = 4

_TIPO_LABELS = {
    "proporcional": "Proporcional",
    "sim_nao_nps": "SIM ou Não",
    "sim_nao_assiduidade": "SIM ou Não",
    "penalidade": "Penalidade",
    "escalonado_nps": "Escalonado NPS",
    "escalonado_percentual": "Escalonado %",
    "penalidade_taxa": "Penalidade Taxa",
    "penalidade_percentual": "Penalidade %",
    "binaria": "Binária",
}


def _is_empty(val) -> bool:
    return val in ("", "N/D", "N/A", None)


def _kpi_excel_formula(real_cell: str, kpi_def: dict) -> str:
    tipo = kpi_def.get("tipo")
    meta = kpi_def.get("meta")
    peso = kpi_def.get("peso")
    cap = kpi_def.get("cap")

    if tipo in (None, "-") or meta == "-" or peso == "-":
        return "-"

    guard = f'OR({real_cell}="", {real_cell}="-")'

    try:
        if tipo == "proporcional":
            m = float(meta) if meta is not None else 0
            if m > 0:
                inner = f"ROUND(({real_cell}/{m})*{peso},1)"
                if cap is not None:
                    inner = f"MIN({cap},{inner})"
                return f'=IF({guard},"",{inner})'
            return f'=IF({guard},"",0)'

        elif tipo == "escalonado_percentual":
            niveis = kpi_def.get("niveis", [])
            if not niveis:
                return f'=IF({guard},"",0)'
            inner = "0"
            for nivel in sorted(niveis, key=lambda n: n["min"]):
                pts = nivel["pts"]
                extra = nivel.get("extra_per_unit", 0)
                calc_pts = f"{pts} + ({real_cell}-{nivel['min']})*{extra}" if extra > 0 else str(pts)
                inner = f"IF({real_cell}>={nivel['min']},{calc_pts},{inner})"
            if cap is not None:
                inner = f"MIN({cap},{inner})"
            return f'=IF({guard},"",{inner})'

        elif tipo == "escalonado_nps":
            niveis = kpi_def.get("niveis", [])
            if not niveis:
                return f'=IF({guard},"",0)'
            inner = "0"
            for nivel in sorted(niveis, key=lambda n: n["min"]):
                inner = f"IF({real_cell}>={nivel['min']},{nivel['pts']},{inner})"
            return f'=IF({guard},"",{inner})'

        elif tipo == "sim_nao_assiduidade":
            return f'=IF({guard},"",IF(OR(UPPER(TRIM({real_cell}))="SIM",{real_cell}=0),{peso},0))'

        elif tipo == "penalidade":
            return f'=IF({guard},"",{real_cell}*{peso})'

        elif tipo == "penalidade_taxa":
            m = kpi_def.get("threshold", 10)
            extra_p = kpi_def.get("extra_peso", -1)
            base = abs(peso) if peso is not None else 5
            inner = f"IF({real_cell}>={m}, -{base} + ({real_cell}-{m})*{extra_p}, 0)"
            if cap is not None:
                inner = f"MAX({cap},{inner})"
            return f'=IF({guard},"",{inner})'

        elif tipo == "penalidade_percentual":
            penal = kpi_def.get("penalidade", {})
            base_thresh = penal.get("base_threshold", 5.5)
            base_pts = penal.get("base_pts", -5)
            extra = penal.get("extra_per_unit", -5)
            min_limit = penal.get("min_limit")
            value_pct = f"({real_cell}*100)"
            inner = f"IF({value_pct}<={base_thresh},{base_pts},{base_pts}+(({value_pct}-{base_thresh})*{extra}))"
            if min_limit is not None:
                inner = f"MAX({min_limit},{inner})"
            return f'=IF({guard},"",{inner})'

        elif tipo == "binaria":
            return f'=IF({guard},"",IF({real_cell}={meta},{peso},0))'

    except ValueError, TypeError:
        return "-"
    return "-"


def write_bsc_kpi_table(
    ws,
    start_row: int,
    title: str,
    bsc_header: list,
    bsc_data: list,
    kpi_config: list,
    fmts: dict,
    add_total_row: bool = True,
) -> int:
    agents = bsc_header[1:]
    n_agents = len(agents)

    ws.set_column(0, 0, 35)
    ws.set_column(_META_COL, _PESO_COL, 10)
    ws.set_column(_TIPO_COL, _TIPO_COL, 18)
    for i in range(n_agents):
        ws.set_column(_FIRST_AGENT_COL + 2 * i, _FIRST_AGENT_COL + 2 * i, 18)
        ws.set_column(_FIRST_AGENT_COL + 2 * i + 1, _FIRST_AGENT_COL + 2 * i + 1, 12)

    ws.write(start_row, 0, title, fmts["title"])
    h_row = start_row + 1
    ws.write(h_row, 0, "Métrica", fmts["header"])
    ws.write(h_row, _META_COL, "Meta", fmts["header"])
    ws.write(h_row, _PESO_COL, "Peso", fmts["header"])
    ws.write(h_row, _TIPO_COL, "Tipo", fmts["header"])
    for i, agent in enumerate(agents):
        ws.write(h_row, _FIRST_AGENT_COL + 2 * i, agent, fmts["header"])
        ws.write(h_row, _FIRST_AGENT_COL + 2 * i + 1, "KPI", fmts["header_kpi"])

    first_data_row = start_row + 2
    for r, row in enumerate(bsc_data):
        excel_row = first_data_row + r
        kpi_def = kpi_config[r] if r < len(kpi_config) else None

        row_fmt = fmts["cell_alt"] if r % 2 == 0 else fmts["cell"]
        k_fmt = fmts["kpi_alt"] if r % 2 == 0 else fmts["kpi"]

        ws.write(excel_row, 0, row[0], fmts["label"])
        ws.write(excel_row, _META_COL, kpi_def["meta"] if kpi_def else "-", row_fmt)
        ws.write(excel_row, _PESO_COL, kpi_def["peso"] if kpi_def else "-", row_fmt)
        ws.write(excel_row, _TIPO_COL, _TIPO_LABELS.get(kpi_def["tipo"], "-") if kpi_def else "-", row_fmt)

        for i, val in enumerate(row[1:]):
            real_col = _FIRST_AGENT_COL + 2 * i
            kpi_col = _FIRST_AGENT_COL + 2 * i + 1
            real_cell = xl_rowcol_to_cell(excel_row, real_col)

            ws.write(excel_row, real_col, "-" if _is_empty(val) else val, row_fmt)
            if kpi_def:
                ws.write_formula(excel_row, kpi_col, _kpi_excel_formula(real_cell, kpi_def), k_fmt)
            else:
                ws.write(excel_row, kpi_col, "-", k_fmt)

    last_data_row = first_data_row + len(bsc_data) - 1
    if add_total_row and bsc_data:
        t_row = last_data_row + 1
        ws.write(t_row, 0, "TOTAL KPI", fmts["total"])
        for i in range(n_agents):
            kpi_col = _FIRST_AGENT_COL + 2 * i + 1
            f_cell = xl_rowcol_to_cell(first_data_row, kpi_col)
            l_cell = xl_rowcol_to_cell(last_data_row, kpi_col)
            formula = f'=SUMIF({f_cell}:{l_cell},"<>"&"",{f_cell}:{l_cell})'
            ws.write_formula(t_row, kpi_col, formula, fmts["total_kpi"])
        return t_row + 1
    return last_data_row + 1
