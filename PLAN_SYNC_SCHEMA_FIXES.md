# Plano: Correção de Sync + Schema + Config

> Criado em 2026-07-21. Execute este plano para corrigir o pipeline de sincronização,
> limpar o schema, usar toda a config dos `.env`/`*.yaml`, e popular `agnt_grp`.

---

## Contexto

### Dados atuais (problemáticos)

| Tabela | Legado (SQLite, Jun 2026) | Nosso PG (atual) | Esperado |
|--------|---------------------------|------------------|----------|
| contacts | 645 | 14.891 (histórico completo) | ~645 (Jun+Jul 2026) |
| conversations | 1.048 | 13.998 (histórico desde 2020) | ~1.100 (Jun+Jul 2026) |
| messages | 53.869 | 1.344 (9.6%) | ~55.000+ |

### Problema raiz

1. **Profile "daily" tem `messages_days=None`** → incremental nunca sincroniza mensagens
2. **Full sync baixa TODO o histórico** (14K conversas desde 2020) — incorreto, foco é Jun 2026 em diante
3. **Colunas `cnts_custom1-4`** definidas no schema mas nunca escritas/lidas
4. **`agnt_grp`** definido no schema mas nunca populado (groups resolvidos via Python)
5. **Config morta** em `.env` e `*.yaml` (vars não lidas, valores não usados)

### Conceito corrigido

**Todos os syncs são full estrutural** (contacts + TODAS conversations). A única diferença entre profiles é `messages_days` (quantos dias de mensagens puxar).

| Profile | Intervalo | Messages Days | Full Sync Agendado |
|---------|-----------|---------------|-------------------|
| "debug" | 15min | 1 | Nunca |
| "short" | 30min | 2 | Nunca |
| "hourly" | 60min | 3 | Nunca |
| "daily" | 60min | 3 | 03:00 (reforço) |
| "weekly" | 60min | 7 | 04:00 (reforço) |
| "monthly" | Nunca | — | 05:00 (mensal completo) |

---

## Fase 1: Schema — Limpar e corrigir

### 1.1 Remover colunas não usadas

Criar `infrastructure/database/migrations/003_cleanup_unused_columns.sql`:

```sql
-- Remove colunas placeholders nunca escritas/lidas
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom1;
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom2;
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom3;
ALTER TABLE contacts DROP COLUMN IF EXISTS cnts_custom4;
```

### 1.2 Popular `agnt_grp`

**`infrastructure/api/config.py`** — alterar `get_known_agents()`:

```python
# ANTES:
def get_known_agents():
    return {bird_id: info["name"] for bird_id, info in constants.AGENTS.items()}

# DEPOIS:
def get_known_agents():
    return {bird_id: {"name": info["name"], "group": info["group"]}
            for bird_id, info in constants.AGENTS.items()}
```

**`infrastructure/sync/pg_sync_engine.py`** — alterar `seed_known_agents()`:

```python
# ANTES:
agents_data = [(name.strip() if name else name, bird_id)
               for bird_id, name in known_agents.items()]
await conn.execute_many(
    "INSERT INTO agents (agnt_name, agnt_bird) VALUES ($1, $2) "
    "ON CONFLICT (agnt_bird) DO UPDATE SET agnt_name = EXCLUDED.agnt_name, "
    "agnt_updated = NOW()",
    agents_data,
)

# DEPOIS:
agents_data = [
    (info["name"].strip() if info["name"] else info["name"],
     info["group"], bird_id)
    for bird_id, info in known_agents.items()
]
await conn.execute_many(
    "INSERT INTO agents (agnt_name, agnt_grp, agnt_bird) VALUES ($1, $2, $3) "
    "ON CONFLICT (agnt_bird) DO UPDATE SET "
    "agnt_name = EXCLUDED.agnt_name, agnt_grp = EXCLUDED.agnt_grp, "
    "agnt_updated = NOW()",
    agents_data,
)
```

**`infrastructure/sync/pg_sync_engine.py`** — alterar `get_or_create_agent()`:

```python
# ANTES:
await conn.execute_many(
    "INSERT INTO agents (agnt_name, agnt_bird) VALUES ($1, $2) "
    "ON CONFLICT (agnt_bird) DO UPDATE SET agnt_name = EXCLUDED.agnt_name",
    [(name, bird_id)],
)

# DEPOIS:
await conn.execute_many(
    "INSERT INTO agents (agnt_name, agnt_grp, agnt_bird) VALUES ($1, $2, $3) "
    "ON CONFLICT (agnt_bird) DO UPDATE SET "
    "agnt_name = EXCLUDED.agnt_name, agnt_grp = EXCLUDED.agnt_grp",
    [(name, "OUTROS", bird_id)],
)
```

### 1.3 Atualizar materialized view

Criar `infrastructure/database/migrations/004_add_agnt_grp_to_view.sql`:

```sql
DROP MATERIALIZED VIEW IF EXISTS vw_survey_data;

CREATE MATERIALIZED VIEW vw_survey_data AS
SELECT
    ca.agnt_name AS conversation_agent_name,
    ma.agnt_name AS message_agent_name,
    ca.agnt_grp  AS agent_group,
    ct.cnts_id,
    ct.cnts_name,
    ct.cnts_phone,
    cv.cnvs_id,
    cv.cnvs_created,
    cv.cnvs_updated,
    cv.cnvs_status,
    cv.cnvs_lang,
    cv.cnvs_software,
    cv.cnvs_tax_id,
    cv.cnvs_dept,
    cv.cnvs_rating_agent,
    cv.cnvs_rating_nps,
    cv.cnvs_contact_reason,
    cv.cnvs_occurrence,
    cv.cnvs_channel,
    cv.cnvs_description,
    m.msgs_id,
    m.msgs_created,
    m.msgs_direction,
    m.msgs_agnt
FROM messages m
JOIN conversations cv ON m.msgs_cnvs = cv.cnvs_id
LEFT JOIN agents ca ON cv.cnvs_agnt = ca.agnt_id
LEFT JOIN agents ma ON m.msgs_agnt = ma.agnt_id
LEFT JOIN contacts ct ON cv.cnvs_cnts = ct.cnts_id;

CREATE UNIQUE INDEX IF NOT EXISTS idx_vw_survey_data_pk
    ON vw_survey_data (cnvs_id, msgs_id);
```

> **Nota:** Após criar a view, rodar `REFRESH MATERIALIZED VIEW CONCURRENTLY vw_survey_data`.

---

## Fase 2: Config — Usar todo .env e *.yaml

### 2.1 Limpar .env morto

Remover de `.env.example` (nunca lidos):
- `DATABASE_ECHO`
- `APP_DEBUG`
- `APP_PORT`

Documentar em `.env.example` (usados mas não documentados):
```bash
# --- Hidden config (used by sync engine) ---
MESSAGEBIRD_API_KEY_TEST=           # Fallback para MESSAGEBIRD_API_KEY_LIVE
MESSAGEBIRD_WORKSPACE_ID_TEST=      # Fallback para MESSAGEBIRD_WORKSPACE_ID_LIVE
MESSAGEBIRD_BASE_URL_BIRD=          # URL base Bird API (legado)
MESSAGEBIRD_PHRASE_TICKET_HEADER=   # Frase para detectar ticket de triagem
MESSAGEBIRD_SOFTWARE_NAMES=         # Nomes de software para detectar
MESSAGEBIRD_DEFAULT_SOFTWARE=       # Software padrão quando não detectado
```

### 2.2 Usar `workspace_id` no client

**`infrastructure/api/client.py`** — incluir workspace_id nos headers (se aplicável à Bird API):

```python
# No __init__ ou nos headers das requisições:
headers["X-Workspace-Id"] = self.workspace_id
```

> **Nota:** Verificar se a Bird API aceita esse header. Se não, remover `workspace_id` do client.

### 2.3 Usar `LANG_MAP`

**`domain/constants.py`** — adicionar função:

```python
def resolve_lang(lang_id: int | None) -> str:
    """Resolve language ID to human-readable label."""
    if lang_id is None:
        return "N/A"
    return LANG_MAP.get(lang_id, "Desconhecido")
```

Usar em:
- `postgres_report_repository.py` — `_rows_to_conversations()` para resolver `cnvs_lang`
- Frontend — conversations detail para exibir idioma

### 2.4 Limpar dead config

**`business_bsc.yaml`** — remover `sla_frt_seconds`:
```yaml
# ANTES:
METRIC_THRESHOLDS:
  sla_frt_minutes: 60
  sla_frt_seconds: 3600    # ← REMOVER (nunca lido)
  max_art_minutes: 480
  max_duration_minutes: 630

# DEPOIS:
METRIC_THRESHOLDS:
  sla_frt_minutes: 60
  max_art_minutes: 480
  max_duration_minutes: 630
```

**`domain/constants.py`** — remover `NPS_CONFIG` dict morto:
```python
# ANTES:
NPS_CONFIG: dict[str, int] = {}

# DEPOIS: remover a linha (valores já estão em MetricsCalculator)
```

**`infrastructure/api/config.py`** — remover `PHRASE_TRIAGEM_HEADER` se não for usar:
```python
# ANTES:
PHRASE_TRIAGEM_HEADER = os.getenv("MESSAGEBIRD_PHRASE_TRIAGEM_HEADER", "...")

# DEPOIS: remover se não há referência em nenhum outro arquivo
```

### 2.5 Mover `REOPEN_GAP_HOURS` para YAML

**`business_config.yaml`** — adicionar seção:
```yaml
SYNC_CONFIG:
  reopen_gap_hours: 24
```

**`infrastructure/config/config_loader.py`** — ler:
```python
SYNC_CONFIG = data.get("SYNC_CONFIG", {})
REOPEN_GAP_HOURS = SYNC_CONFIG.get("reopen_gap_hours", 24)
```

**`domain/constants.py`** — usar:
```python
# ANTES:
REOPEN_GAP_HOURS = 24

# DEPOIS:
from infrastructure.config.config_loader import REOPEN_GAP_HOURS
```

---

## Fase 3: Sync — Todos os syncs são full estrutural

### 3.1 Atualizar sync profiles

**`infrastructure/config/sync_profiles.py`**:

```python
@dataclass(frozen=True)
class SyncProfile:
    name: str
    incremental_minutes: int | None
    messages_days: int | None        # ← REMOVER incremental_lookback
    full_sync_hour: int | None
    full_sync_minute: int
    sync_messages: bool
    backfill_surveys: bool

PROFILES: dict[str, SyncProfile] = {
    "debug": SyncProfile(
        name="debug",
        incremental_minutes=15,
        messages_days=1,             # ← ANTES era None ou 1
        full_sync_hour=None,
        full_sync_minute=0,
        sync_messages=True,
        backfill_surveys=True,
    ),
    "short": SyncProfile(
        name="short",
        incremental_minutes=30,
        messages_days=2,             # ← ANTES era None ou 2
        full_sync_hour=None,
        full_sync_minute=0,
        sync_messages=True,
        backfill_surveys=True,
    ),
    "hourly": SyncProfile(
        name="hourly",
        incremental_minutes=60,
        messages_days=3,             # ← ANTES era None ou 3
        full_sync_hour=None,
        full_sync_minute=0,
        sync_messages=True,
        backfill_surveys=True,
    ),
    "daily": SyncProfile(
        name="daily",
        incremental_minutes=60,
        messages_days=3,             # ← ANTES era None
        full_sync_hour=3,
        full_sync_minute=0,
        sync_messages=True,
        backfill_surveys=True,
    ),
    "weekly": SyncProfile(
        name="weekly",
        incremental_minutes=60,
        messages_days=7,             # ← ANTES era 90
        full_sync_hour=4,
        full_sync_minute=0,
        sync_messages=True,
        backfill_surveys=True,
    ),
    "monthly": SyncProfile(
        name="monthly",
        incremental_minutes=None,
        messages_days=30,            # ← ANTES era 365
        full_sync_hour=5,
        full_sync_minute=0,
        sync_messages=True,
        backfill_surveys=True,
    ),
}
```

### 3.2 Simplificar `_make_incremental_handler`

**`api/main.py`**:

```python
# ANTES:
def _make_incremental_handler(lookback: int, messages_days: int | None):
    async def _run():
        use_case = SyncDatabaseUseCase()
        await use_case.execute(
            full_sync=False,
            sync_messages=messages_days is not None,
            messages_days=messages_days,
            lookback_minutes=lookback,
        )
        ...

# DEPOIS:
def _make_incremental_handler(messages_days: int | None):
    async def _run():
        use_case = SyncDatabaseUseCase()
        await use_case.execute(
            full_sync=False,
            sync_messages=messages_days is not None,
            messages_days=messages_days,
        )
        ...
```

### 3.3 Simplificar `trigger_sync_pg`

**`infrastructure/sync/pg_sync_engine.py`** — na seção incremental:

```python
# ANTES (linhas 970-975):
# Default incremental: skip contacts if recent, sync conversations with lookback
if await manager._should_skip(conn, "contacts"):
    logger.info("Contacts synced recently, skipping.")
else:
    await manager.sync_contacts(conn)
await manager.sync_conversations(conn, lookback_minutes=lookback_minutes)
return "Incremental sync completed."

# DEPOIS:
# Incremental: full structural sync + scoped messages
if await manager._should_skip(conn, "contacts"):
    logger.info("Contacts synced recently, skipping.")
else:
    await manager.sync_contacts(conn)
await manager.sync_conversations(conn, full_sync=True)
if messages_days is not None:
    msg_count = await manager.sync_messages_for_recent(conn, days=messages_days)
    return f"Incremental sync completed ({msg_count} messages for last {messages_days} days)."
return "Incremental sync completed (no messages)."
```

Remover parâmetro `lookback_minutes` de `trigger_sync_pg`:
```python
async def trigger_sync_pg(
    pool,
    full_sync: bool = False,
    sync_messages: bool = False,
    messages_days: int | None = None,
    year: int | None = None,
    month: int | None = None,
    backfill_surveys: bool = False,
    sync_today: bool = False,
) -> str:
```

### 3.4 Atualizar admin endpoint

**`api/routes/admin.py`** — remover `lookback_minutes` do request body:

```python
# ANTES:
class SyncTriggerRequest(BaseModel):
    full_sync: bool = False
    sync_messages: bool = False
    messages_days: int | None = None
    lookback_minutes: int = 60
    ...

# DEPOIS:
class SyncTriggerRequest(BaseModel):
    full_sync: bool = False
    sync_messages: bool = False
    messages_days: int | None = None
    ...
```

### 3.5 Atualizar `SyncDatabaseUseCase`

**`application/use_cases/sync_database.py`** — remover `lookback_minutes`:

```python
# ANTES:
async def execute(self, full_sync=False, sync_messages=False,
                  messages_days=None, lookback_minutes=60, ...):

# DEPOIS:
async def execute(self, full_sync=False, sync_messages=False,
                  messages_days=None, ...):
```

### 3.6 Atualizar testes

Remover todas as referências a `lookback_minutes` nos testes:
- `tests/infrastructure/test_pg_sync_engine.py` — remover `lookback_minutes` dos mocks
- `tests/application/test_sync_database_use_case.py` — remover `lookback_minutes` dos args

---

## Fase 4: Queries — Usar agnt_grp

### 4.1 Adicionar agnt_grp às queries principais

**`infrastructure/database/queries_pg.py`**:

```sql
-- SURVEY_DATA_METADATA_QUERY: adicionar ca.agnt_grp
SELECT
    ...,
    ca.agnt_name AS conversation_agent_name,
    ca.agnt_grp  AS agent_group,       -- ← ADICIONAR
    ...

-- CONVERSATION_LIST_QUERY: adicionar a.agnt_grp
SELECT
    ...,
    a.agnt_name AS agent_name,
    a.agnt_grp  AS agent_group,        -- ← ADICIONAR
    ...

-- OS_DATA_QUERY: adicionar ca.agnt_grp
SELECT
    ...,
    ca.agnt_name AS agent_name,
    ca.agnt_grp  AS agent_group,       -- ← ADICIONAR
    ...
```

### 4.2 Usar agnt_grp no materialized view

Já coberto pela Fase 1.3 (view `vw_survey_data` inclui `ca.agnt_grp`).

### 4.3 Simplificar agrupamento Python

Em `postgres_report_repository.py`, onde `constants.get_agent_group(name)` é usado pós-query:

```python
# ANTES:
for row in rows:
    agent = row["agnt_name"]
    group = constants.get_agent_group(agent)

# DEPOIS:
for row in rows:
    group = row.get("agnt_grp") or constants.get_agent_group(row["agnt_name"])
```

Manter fallback Python para agentes não seedados.

---

## Fase 5: Backfill Jun 2026

### 5.1 Via admin trigger

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresa.com","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Backfill Jun 2026
curl -X POST http://localhost:8050/api/v1/admin/sync/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 6}'
```

### 5.2 Validação

```sql
-- Conversations Jun 2026 (esperado: ~1.048)
SELECT COUNT(*) FROM conversations
WHERE cnvs_created >= '2026-06-01' AND cnvs_created < '2026-07-01';

-- Messages Jun 2026 (esperado: ~53.000+)
SELECT COUNT(*) FROM messages m
JOIN conversations c ON m.msgs_cnvs = c.cnvs_id
WHERE c.cnvs_created >= '2026-06-01' AND c.cnvs_created < '2026-07-01';

-- agnt_grp populated (esperado: todos com grupo)
SELECT agnt_name, agnt_grp FROM agents ORDER BY agnt_grp, agnt_name;

-- cnts_custom* removed (esperado: erro se tentar acessar)
-- (não aplicável — colunas removidas)
```

### 5.3 Verificar frontend

- Abrir `http://localhost:3050`
- Dashboard KPIs devem refletir dados reais
- Conversations list deve mostrar conversas com mensagens
- Agent ranking deve mostrar grupos corretos

---

## Fase 6: Testes

### 6.1 Rodar testes

```bash
# Copiar testes para container
docker compose cp tests/. api:/app/tests/

# Rodar pytest
docker compose exec api python -m pytest tests/ -v --tb=short

# Rodar lint
docker compose exec api python -m ruff check . && \
docker compose exec api python -m ruff format --check .

# Frontend build
docker compose build --no-cache frontend
docker compose up -d frontend
```

### 6.2 Verificar erros conhecidos

- `ModuleNotFoundError: No module named 'respx'` → `docker compose exec api pip install respx`
- TypeScript errors no frontend → verificar types em `frontend/types/index.ts`
- Pydantic validation errors → verificar `api/schemas/*.py`

---

## Arquivos modificados (resumo)

| Arquivo | Mudança | Fase |
|---------|---------|------|
| `infrastructure/database/migrations/003_cleanup_unused_columns.sql` | **Novo** — DROP cnts_custom* | 1 |
| `infrastructure/database/migrations/004_add_agnt_grp_to_view.sql` | **Novo** — Recriar view | 1 |
| `infrastructure/api/config.py` | `get_known_agents()` retorna name+group | 1 |
| `infrastructure/sync/pg_sync_engine.py` | seed agnt_grp; simplificar trigger_sync_pg | 1, 3 |
| `infrastructure/config/sync_profiles.py` | Todos profiles com messages_days | 3 |
| `api/main.py` | Remover lookback_minutes do handler | 3 |
| `api/routes/admin.py` | Remover lookback_minutes do request | 3 |
| `application/use_cases/sync_database.py` | Remover lookback_minutes | 3 |
| `infrastructure/database/queries_pg.py` | agnt_grp nos SELECTs | 4 |
| `domain/constants.py` | resolve_lang(); remover NPS_CONFIG morto | 2, 4 |
| `infrastructure/api/client.py` | Usar workspace_id se aplicável | 2 |
| `.env.example` | Limpar vars mortas, documentar ocultas | 2 |
| `business_config.yaml` | Adicionar SYNC_CONFIG.reopen_gap_hours | 2 |
| `business_bsc.yaml` | Remover sla_frt_seconds | 2 |
| `tests/infrastructure/test_pg_sync_engine.py` | Remover lookback_minutes | 6 |
| `tests/application/test_sync_database_use_case.py` | Remover lookback_minutes | 6 |
