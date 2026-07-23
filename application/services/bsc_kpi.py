from typing import Any


def compute_kpi_score(raw_value: float | None, kpi_def: dict[str, Any]) -> float | None:
    """Compute KPI score from raw value using the same logic as Excel formulas.

    Returns None if no raw value (manual metric not filled in).
    """
    if raw_value is None:
        return None

    tipo = kpi_def.get("tipo")
    meta = kpi_def.get("meta")
    peso = kpi_def.get("peso")
    cap = kpi_def.get("cap")

    if tipo in (None, "-") or meta == "-" or peso == "-":
        return None

    try:
        if tipo == "proporcional":
            m = float(meta) if meta is not None else 0
            if m <= 0:
                return 0.0
            score = (raw_value / m) * peso
            if cap is not None:
                score = min(float(cap), score)
            return round(score, 1)

        elif tipo == "escalonado_percentual":
            niveis = kpi_def.get("niveis", [])
            if not niveis:
                return 0.0
            score = 0.0
            for nivel in sorted(niveis, key=lambda n: n["min"]):
                if raw_value >= nivel["min"]:
                    pts = float(nivel["pts"])
                    extra = float(nivel.get("extra_per_unit", 0))
                    score = pts + (raw_value - nivel["min"]) * extra if extra > 0 else pts
            if cap is not None:
                score = min(float(cap), score)
            return round(score, 1)

        elif tipo == "escalonado_nps":
            niveis = kpi_def.get("niveis", [])
            if not niveis:
                return 0.0
            score = 0.0
            for nivel in sorted(niveis, key=lambda n: n["min"]):
                if raw_value >= nivel["min"]:
                    score = float(nivel["pts"])
            return round(score, 1)

        elif tipo == "sim_nao_assiduidade":
            return float(peso) if raw_value == 0 else 0.0

        elif tipo == "penalidade":
            return round(raw_value * peso, 1)

        elif tipo == "penalidade_taxa":
            m = float(kpi_def.get("threshold", 10))
            extra_p = float(kpi_def.get("extra_peso", -1))
            base = abs(float(peso)) if peso is not None else 5
            if raw_value >= m:
                score = -base + (raw_value - m) * extra_p
            else:
                score = 0.0
            if cap is not None:
                score = max(float(cap), score)
            return round(score, 1)

        elif tipo == "penalidade_percentual":
            penal = kpi_def.get("penalidade", {})
            base_thresh = float(penal.get("base_threshold", 5.5))
            base_pts = float(penal.get("base_pts", -5))
            extra = float(penal.get("extra_per_unit", -5))
            min_limit = penal.get("min_limit")
            value_pct = raw_value  # raw_value is already a percentage (0-100)
            if value_pct <= base_thresh:
                score = base_pts
            else:
                score = base_pts + ((value_pct - base_thresh) * extra)
            if min_limit is not None:
                score = max(float(min_limit), score)
            return round(score, 1)

        elif tipo == "binaria":
            return float(peso) if raw_value == meta else 0.0

    except ValueError, TypeError:
        return None

    return None
