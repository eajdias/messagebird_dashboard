# ── ART / SLA ────────────────────────────────────────────────────────────────
import os

import yaml

SLA_FRT_THRESHOLD_SECONDS = 3600
SLA_FRT_THRESHOLD_MINUTES = 60
MAX_ART_MINUTES = 480  # 8 horas — máximo aceitável para Average Response Time
MAX_DURATION_MINUTES = 630  # 10h30 — máximo aceitável para duração total de chat
REOPEN_GAP_HOURS = 24  # Gap mínimo de inatividade para detectar reabertura por mensagens

# ── Agent report headers ──────────────────────────────────────────────────────

AGENTS_HEADER = [
    "Dept maior atendimento",
    "Grupo",
    "Nome do Agente",
    "Total de Chats",
    "% do Departamento",
    "Elogios (nota 4-5)",
    "% Elogios",
    "Feedback Negativo (nota 1-2)",
    "% Feedback Negativo",
    "Total de Msgs",
    "Msgs/Chat",
    "Nota Técnica Média",
    "NPS Médio",
    "NPS Real",
    "ART Técnico (min)",
    "SLA Compliance (%)",
    "Duração Média (min)",
    "Clientes Únicos",
    "Retornantes",
]

DEPARTMENTS_HEADER = [
    "Departamento",
    "Total de Chats",
    "% do Total",
    "Total de Msgs",
    "ART Médio (min)",
    "SLA Compliance (%)",
    "Duração Média (min)",
    "NPS Médio",
    "NPS Real",
    "Nota Técnica Média",
    "Clientes Únicos",
    "Retornantes",
    "Taxa de Avaliação (%)",
]

# ── Audit report headers ──────────────────────────────────────────────────────

CONTACTS_HEADER = [
    "Agente mais Participativo",
    "Cliente",
    "Telefone",
    "Chats no Mês",
    "Msgs no Mês",
    "Nota Média",
    "NPS Média",
    "Datas",
    "Atendimento pelos Agentes",
]

CHATS_HEADER = [
    "Dia",
    "Maior Demanda",
    "Chats Iniciados",
    "Chats Concluidos",
    "Chats Pendentes",
    "Mensagens Trocadas",
    "Agent Chat MVP",
    "Agent Msgs MVP",
    "Duração Média Chats (min)",
    "Msgs em Média por Chat",
    "ART Técnico (min)",
    "ART Cliente (min)",
    "NPS Médio",
    "Nota Técnica Média",
    "Dept maior atendimento",
    "Clientes Únicos",
    "Retornantes",
]

DEMAND_HEADER = [
    "Hora do dia",
    "Novos Chats",
    "Msgs Recebidas",
    "Msgs Enviadas",
    "Média de Novos Chats",
]

OS_HEADER = [
    "ID Bird",
    "Data de Início",
    "Agente",
    "Cliente",
    "Telefone",
    "Documento",
    "Sistema",
    "Departamento",
    "Motivo do Contato",
    "Ocorrência",
    "Nota Técnico",
    "Nota NPS",
    "Reaberturas",
    "Descrição do Problema",
    "Duração (min)",
    "ID BD",
    "Caminho PDF",
]

# ── Annual report headers ─────────────────────────────────────────────────────

ANNUAL_HEADER = [
    "Mês",
    "Total de Chats",
    "Total de Msgs",
    "ART Médio (min)",
    "SLA Compliance (%)",
    "Duração Média (min)",
    "NPS Real",
    "Nota Técnica Média",
    "Elogios",
    "Feedback Negativo",
    "Clientes Únicos",
    "Retornantes",
]

# ── Default Maps ─────────────────────────────────────────────────────────────
DEFAULT_DEPT_MAP = {
    1: "Suporte Tecnico",
    2: "Comercial",
    3: "Financeiro",
    4: "Ouvidoria",
    5: "Nova Instalacao | Migracao",
}

DEFAULT_REASON_MAP = {
    1: {1: "Problemas tecnicos", 2: "Duvidas sobre uso do sistema", 3: "Solicitacao de acesso remoto"},
    2: {1: "Falar com consultor comercial", 2: "Agendar demonstracao", 3: "Informacoes sobre produtos"},
    3: {1: "Boleto", 2: "Nota Fiscal", 3: "Sistema bloqueado", 4: "Mensagem de cobranca", 5: "Nao consta"},
    4: {1: "Reclamacao", 2: "Sugestao", 3: "Elogio"},
    5: {1: "Nova instalacao", 2: "Migracao de sistema", 3: "Instalacao em novo computador"},
}

DEFAULT_OCCURRENCE_MAP = {
    1: {
        1: {
            1: "Pedal Zscan",
            2: "Captura ou Ajustes de Imagens",
            3: "Criacao ou Ajustes de Laudos",
            4: "Arquivos indisponiveis em geral",
            5: "Vigencia ou Mensagens no Sistema",
            6: "Nao consta",
        },
        2: {1: "Duvidas sobre funcionalidades", 2: "Treinamento de uso", 3: "Nao consta"},
        3: {1: "Acesso ao servidor", 2: "Acesso remoto", 3: "Nao consta"},
    },
    2: {
        1: {1: "Informacoes sobre planos", 2: "Demonstracao do sistema", 3: "Nao consta"},
        2: {1: "Agendamento de demonstracao", 2: "Cancelamento de demonstracao", 3: "Nao consta"},
        3: {1: "Informacoes sobre produtos", 2: "Informacoes sobre precos", 3: "Nao consta"},
    },
    3: {
        1: {1: "Pagamento de boleto", 2: "Segunda via de boleto", 3: "Boleto nao encontrado", 4: "Nao consta"},
        2: {
            1: "Emissao de nota fiscal",
            2: "Cancelamento de nota fiscal",
            3: "Dados incorretos na nota",
            4: "Nao consta",
        },
        3: {1: "Desbloqueio de sistema", 2: "Problema de licenca", 3: "Nao consta"},
        4: {1: "Mensagem de cobranca indevida", 2: "Duvidas sobre cobranca", 3: "Nao consta"},
        5: {1: "Servico nao encontrado", 2: "Dados desatualizados", 3: "Nao consta"},
    },
    4: {
        1: {
            1: "Reclamacao sobre atendimento",
            2: "Reclamacao sobre produto",
            3: "Reclamacao sobre prazo",
            4: "Nao consta",
        },
        2: {1: "Sugestao de melhoria", 2: "Sugestao de novo recurso", 3: "Nao consta"},
        3: {1: "Elogio sobre atendimento", 2: "Elogio sobre produto", 3: "Nao consta"},
    },
    5: {
        1: {
            1: "Instalacao Zscan",
            2: "Instalacao Yoovet",
            3: "Instalacao em servidor",
            4: "Instalacao em estacao",
            5: "Nao consta",
        },
        2: {1: "Migracao de versao", 2: "Migracao de computador", 3: "Migracao de dados", 4: "Nao consta"},
        3: {
            1: "Instalacao em notebook novo",
            2: "Instalacao em desktop novo",
            3: "Transferencia de licenca",
            4: "Nao consta",
        },
    },
}

DEFAULT_LANG_MAP = {1: "Português", 2: "English", 3: "Español"}

DEFAULT_CHANNEL_MAP = {
    "3fa4639084614f7e9fbe121dea5a28e5": "WhatsApp",
    "79a46c93-19a2-4eed-8050-beea59b23528": "Templates/Sites",
}

DEFAULT_KPI_CONFIG = {
    "Suporte Tecnico": {
        "t1": [
            {
                "name": "Elogios de atendimento / Feedback",
                "description": "Notas 4 e 5 = Feedback positivo.",
                "metric": "% em cima do total de avaliados com nota",
                "meta": ">40%",
                "peso": 30,
                "tipo": "escalonado_percentual",
                "niveis": [
                    {"min": 40, "pts": 30, "extra_per_unit": 0.75},
                    {"min": 35, "pts": 15},
                    {"min": 30, "pts": 10},
                ],
                "cap": 50,
            },
            {
                "name": "NPS (Net Promoter Score)",
                "description": "NPS individual oficial. Cálculo: ((Promotores - Detratores) / Total) × 100",
                "metric": "NPS individual do agente",
                "meta": ">=90/70/63/50",
                "peso": 30,
                "tipo": "escalonado_nps",
                "niveis": [
                    {"min": 90, "pts": 50},
                    {"min": 70, "pts": 30},
                    {"min": 63, "pts": 15},
                    {"min": 50, "pts": 5},
                ],
            },
            {
                "name": "Feedback Negativo (Penalidade)",
                "description": "Notas 1 e 2 = Feedback negativo. 5,5% = -5 pts. A cada 1% adicional = -5 pts.",
                "metric": "% de feedbacks negativos (notas 1 e 2) sobre total avaliados",
                "meta": "<=5.5%",
                "peso": -5,
                "tipo": "penalidade_percentual",
                "penalidade": {"base_threshold": 5.5, "base_pts": -5, "extra_per_unit": -5, "min_limit": None},
            },
            {
                "name": "Atendimentos | Ligacoes Finalizados",
                "description": "Volume bruto: Meta de 150 chats. Peso 10 pts.",
                "metric": "Quantidade total de chats encerrados no mes",
                "meta": 150,
                "peso": 10,
                "tipo": "proporcional",
                "pontos_por_unidade": 0.0667,
            },
            {
                "name": "Instalacoes e Migracoes",
                "description": "Tickets finalizados. Meta de 10. Peso 30 pts. 3 pts por ticket.",
                "metric": "Tickets de instalacao/migracao finalizados no mes",
                "meta": 10,
                "peso": 30,
                "tipo": "proporcional",
                "pontos_por_unidade": 3,
            },
            {
                "name": "Assiduidade (sem faltas)",
                "description": "Metrica binaria: 0 faltas/atrasos no mes garante 35 pts.",
                "metric": "Faltas e atrasos no mes",
                "meta": 0,
                "peso": 35,
                "tipo": "binaria",
                "regra": "0_faltas_ganha_pontos",
            },
            {
                "name": "Indicacao Comercial",
                "description": "Proporcional: Meta de 10 indicacoes. Peso 50 pts. 5 pts por indicacao.",
                "metric": "Indicacoes comerciais realizadas no mes",
                "meta": 10,
                "peso": 50,
                "tipo": "proporcional",
                "pontos_por_unidade": 5,
            },
            {
                "name": "Indicacao Comercial - Vendida",
                "description": "Proporcional: Meta de 10 vendas. Peso 100 pts. 10 pts por venda.",
                "metric": "Vendas realizadas por indicacao no mes",
                "meta": 10,
                "peso": 100,
                "tipo": "proporcional",
                "pontos_por_unidade": 10,
            },
            {
                "name": "Updates, Treinamentos e Tarefas (N1 a N3)",
                "description": "Tarefas no geral do suporte. Meta 50 tarefas. Peso 50 pts.",
                "metric": "Tarefas realizadas",
                "meta": 50,
                "peso": 50,
                "tipo": "proporcional",
                "is_automatic_sum": True,
            },
        ],
        "t2": [
            {"name": "Updates", "meta": 50, "peso": 1, "tipo": "proporcional"},
            {"name": "Treinamentos", "meta": 50, "peso": 1, "tipo": "proporcional"},
            {"name": "Tarefa N1", "meta": 50, "peso": 2, "tipo": "proporcional"},
            {"name": "Tarefa N2", "meta": 50, "peso": 3, "tipo": "proporcional"},
            {"name": "Tarefa N3", "meta": 50, "peso": 5, "tipo": "proporcional"},
        ],
        "penalidades_setoriais": [
            {
                "name": "Ligacoes Perdidas (Setor)",
                "description": "Penalidade setorial: -2 pts por ligacao perdida. Nao e individual.",
                "metric": "Ligacoes perdidas pelo grupo no mes",
                "meta": 0,
                "peso": -2,
                "tipo": "penalidade",
            },
        ],
    },
}

DEFAULT_METRIC_THRESHOLDS = {
    "sla_frt_minutes": 60,
    "max_art_minutes": 480,
    "max_duration_minutes": 630,
}

# ── Dynamic Configuration ──────────────


def _load_business_yaml() -> tuple[dict, dict, dict, dict, dict, dict, dict, dict]:
    """Load business + BSC config from YAML files.

    Called at module import time so constants are always populated before
    any endpoint handler runs, regardless of FastAPI lifespan timing.
    """
    base = os.environ.get("CONFIG_DIR", os.path.join(os.path.dirname(__file__), ".."))
    business_path = os.path.join(base, "business_config.yaml")
    bsc_path = os.path.join(base, "business_bsc.yaml")

    dept_map = dict(DEFAULT_DEPT_MAP)
    reason_map = dict(DEFAULT_REASON_MAP)
    occurrence_map = dict(DEFAULT_OCCURRENCE_MAP)
    lang_map = dict(DEFAULT_LANG_MAP)
    channel_map = dict(DEFAULT_CHANNEL_MAP)
    agents: dict = {}
    kpi_config = dict(DEFAULT_KPI_CONFIG)
    dept_routing: dict = {}

    def _keys_to_int(d):
        if not isinstance(d, dict):
            return d
        return {int(k) if isinstance(k, str) and k.isdigit() else k: _keys_to_int(v) for k, v in d.items()}

    # Load business config
    if os.path.exists(business_path):
        try:
            with open(business_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            data = {}
        if "DEPT_MAP" in data:
            dept_map = _keys_to_int(data["DEPT_MAP"])
        if "REASON_MAP" in data:
            reason_map = _keys_to_int(data["REASON_MAP"])
        if "OCCURRENCE_MAP" in data:
            occurrence_map = _keys_to_int(data["OCCURRENCE_MAP"])
        if "LANG_MAP" in data:
            lang_map = _keys_to_int(data["LANG_MAP"])
        if "CHANNEL_MAP" in data:
            channel_map = data["CHANNEL_MAP"]
        if "AGENTS" in data:
            agents = data["AGENTS"]
        if "KPI_CONFIG" in data:
            kpi_config = data["KPI_CONFIG"]
        if "DEPT_ROUTING" in data:
            dept_routing = data["DEPT_ROUTING"]

    # Load BSC config (merges into KPI_CONFIG)
    if os.path.exists(bsc_path):
        try:
            with open(bsc_path, encoding="utf-8") as f:
                bsc_data = yaml.safe_load(f) or {}
        except Exception:
            bsc_data = {}
        if "KPI_CONFIG" in bsc_data:
            kpi_config = bsc_data["KPI_CONFIG"]

    return dept_map, reason_map, occurrence_map, lang_map, channel_map, agents, kpi_config, dept_routing


(
    DEPT_MAP,
    REASON_MAP,
    OCCURRENCE_MAP,
    LANG_MAP,
    CHANNEL_MAP,
    AGENTS,
    KPI_CONFIG,
    DEPT_ROUTING,
) = _load_business_yaml()

METRIC_THRESHOLDS = DEFAULT_METRIC_THRESHOLDS

# ── Helper functions ──────────────────────────────────────────────────────────


def get_agent_group(agent_name: str | None) -> str:
    if not agent_name:
        return "Não categorizado"
    norm_name = agent_name.strip().strip("'").strip('"').strip()

    # Procura pelo nome no novo dicionário AGENTS
    for _, info in AGENTS.items():
        if info["name"] == norm_name:
            return info["group"]

    return "Não categorizado"


def resolve_conversation_group(agent_name: str | None, dept_label: str) -> str:
    if DEPT_ROUTING and dept_label in DEPT_ROUTING:
        return DEPT_ROUTING[dept_label]
    if not DEPT_ROUTING:
        return get_agent_group(agent_name)
    if not dept_label or dept_label in ("N/A", "None", ""):
        return get_agent_group(agent_name)
    return get_agent_group(agent_name)


def _to_int(val) -> int | None:
    try:
        return int(val)
    except TypeError, ValueError:
        return None


def resolve_dept(dept_id, agent_name: str | None = None, agent_group: str | None = None) -> str:
    d = _to_int(dept_id)
    if d is not None:
        return DEPT_MAP.get(d, str(dept_id))
    if agent_name:
        grp = get_agent_group(agent_name)
        if grp != "Não categorizado":
            return grp
    if agent_group and agent_group not in ("", "OUTROS", "Não categorizado"):
        return agent_group
    return "Não categorizado"


def resolve_channel(channel_id) -> str:
    """Resolve UUID do canal para nome legível."""
    if not channel_id:
        return "Desconhecido"
    return CHANNEL_MAP.get(str(channel_id), "Outro Canal")


def resolve_lang(lang_id: int | None) -> str:
    """Resolve language ID to human-readable label."""
    if lang_id is None:
        return "Não categorizado"
    return LANG_MAP.get(lang_id, "Desconhecido")


def resolve_reason(dept_id, reason_id, agent_name: str | None = None) -> str:
    d = _to_int(dept_id)
    r = _to_int(reason_id)
    if r is None:
        return "Contato Direto"
    if d is not None:
        label = REASON_MAP.get(d, {}).get(r)
        if label is not None:
            return label
    # Fallback: try agent's department
    if d is None and agent_name:
        agent_dept = get_agent_group(agent_name)
        # Map agent group back to dept_id
        for dept_num, dept_label in DEPT_MAP.items():
            if dept_label == agent_dept:
                label = REASON_MAP.get(dept_num, {}).get(r)
                if label is not None:
                    return label
    return "Contato Direto"


def resolve_occurrence(dept_id, reason_id, occ_id, agent_name: str | None = None) -> str:
    d = _to_int(dept_id)
    r = _to_int(reason_id)
    o = _to_int(occ_id)
    if o is None:
        return "Outros"

    def _lookup(dept_num: int, reason_num: int | None) -> str | None:
        if reason_num is not None:
            reason_occs = OCCURRENCE_MAP.get(dept_num, {}).get(reason_num, {})
            if reason_occs:
                return reason_occs.get(o)
        # Try all reasons for this dept
        for reason_occs in OCCURRENCE_MAP.get(dept_num, {}).values():
            label = reason_occs.get(o)
            if label is not None:
                return label
        return None

    if d is not None:
        result = _lookup(d, r)
        if result is not None:
            return result
    # Fallback: try agent's department
    if d is None and agent_name:
        agent_dept = get_agent_group(agent_name)
        for dept_num, dept_label in DEPT_MAP.items():
            if dept_label == agent_dept:
                result = _lookup(dept_num, r)
                if result is not None:
                    return result
    return "Outros"
