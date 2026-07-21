import os

import yaml

from domain import constants
from domain.services.metrics_calculator import MetricsCalculator


def _load_file(path: str):
    """Carrega YAML ou JSON (YAML é superconjunto do JSON)."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_and_configure_business(config_path: str):
    """Carrega configuração de negócio (mapas) e injeta no Domínio."""
    if not os.path.exists(config_path):
        return

    try:
        custom_config = _load_file(config_path)

        # Helper para converter chaves string para int onde necessário
        def _keys_to_int(d):
            if not isinstance(d, dict):
                return d
            return {int(k) if isinstance(k, str) and k.isdigit() else k: _keys_to_int(v) for k, v in d.items()}

        if "DEPT_MAP" in custom_config:
            constants.DEPT_MAP = _keys_to_int(custom_config["DEPT_MAP"])
        if "REASON_MAP" in custom_config:
            constants.REASON_MAP = _keys_to_int(custom_config["REASON_MAP"])
        if "OCCURRENCE_MAP" in custom_config:
            constants.OCCURRENCE_MAP = _keys_to_int(custom_config["OCCURRENCE_MAP"])
        if "LANG_MAP" in custom_config:
            constants.LANG_MAP = _keys_to_int(custom_config["LANG_MAP"])
        if "CHANNEL_MAP" in custom_config:
            constants.CHANNEL_MAP = custom_config["CHANNEL_MAP"]
        if "AGENTS" in custom_config:
            constants.AGENTS = custom_config["AGENTS"]
        if "KPI_CONFIG" in custom_config:
            constants.KPI_CONFIG = custom_config["KPI_CONFIG"]
        if "DEPT_ROUTING" in custom_config:
            constants.DEPT_ROUTING = custom_config["DEPT_ROUTING"]

    except Exception as e:
        print(f"Erro ao carregar configuração: {e}")


def load_bsc_config(bsc_path: str):
    """Carrega configuração de BSC/NPS e thresholds de métricas e injeta no Domínio."""
    if not os.path.exists(bsc_path):
        return

    try:
        bsc_config = _load_file(bsc_path)

        if "KPI_CONFIG" in bsc_config:
            constants.KPI_CONFIG = bsc_config["KPI_CONFIG"]

        nps = bsc_config.get("NPS_CONFIG", {})
        if "promoter_min" in nps:
            MetricsCalculator.nps_promoter_min = int(nps["promoter_min"])
        if "passive_min" in nps:
            MetricsCalculator.nps_passive_min = int(nps["passive_min"])

        thresholds = bsc_config.get("METRIC_THRESHOLDS", {})
        if "sla_frt_minutes" in thresholds:
            constants.SLA_FRT_THRESHOLD_MINUTES = int(thresholds["sla_frt_minutes"])
            MetricsCalculator.sla_threshold_minutes = int(thresholds["sla_frt_minutes"])
        if "max_art_minutes" in thresholds:
            constants.MAX_ART_MINUTES = int(thresholds["max_art_minutes"])
        if "max_duration_minutes" in thresholds:
            constants.MAX_DURATION_MINUTES = int(thresholds["max_duration_minutes"])

    except Exception as e:
        print(f"Erro ao carregar configuração BSC: {e}")
