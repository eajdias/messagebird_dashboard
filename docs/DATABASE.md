# Database — PostgreSQL Schema

Banco: `mbird_reports` | Engine: PostgreSQL 18 | Driver: asyncpg

## Tabelas

### `contacts`

| Coluna | Tipo | Constraints |
|--------|------|-------------|
| `cnts_id` | SERIAL | **PK** |
| `cnts_name` | VARCHAR(255) | nullable |
| `cnts_phone` | VARCHAR(50) | nullable |
| `cnts_bird` | VARCHAR(255) | **UNIQUE NOT NULL** |
| `cnts_created` | TIMESTAMP | DEFAULT now() |
| `cnts_updated` | TIMESTAMP | DEFAULT now() |
| `cnts_custom1-4` | VARCHAR(255) | nullable |

**Índices:** `idx_contacts_bird` (cnts_bird), `idx_contacts_phone` (cnts_phone)

### `agents`

| Coluna | Tipo | Constraints |
|--------|------|-------------|
| `agnt_id` | SERIAL | **PK** |
| `agnt_name` | VARCHAR(255) | nullable |
| `agnt_bird` | VARCHAR(255) | **UNIQUE NOT NULL** |
| `agnt_created` | TIMESTAMP | DEFAULT now() |
| `agnt_updated` | TIMESTAMP | DEFAULT now() |
| `agnt_grp` | VARCHAR(100) | nullable |

**Índices:** `idx_agents_bird` (agnt_bird), `idx_agents_grp` (agnt_grp)

### `conversations`

| Coluna | Tipo | Constraints |
|--------|------|-------------|
| `cnvs_id` | SERIAL | **PK** |
| `cnvs_bird` | VARCHAR(255) | **UNIQUE NOT NULL** |
| `cnvs_cnts` | INTEGER | **FK → contacts.cnts_id** |
| `cnvs_agnt` | INTEGER | **FK → agents.agnt_id** |
| `cnvs_status` | VARCHAR(50) | nullable |
| `cnvs_channel` | VARCHAR(255) | nullable |
| `cnvs_created` | TIMESTAMP | nullable |
| `cnvs_updated` | TIMESTAMP | nullable |
| `cnvs_last` | TIMESTAMP | nullable |
| `cnvs_dept` | INTEGER | nullable (resolve via DEPT_MAP) |
| `cnvs_contact_reason` | INTEGER | nullable (resolve via REASON_MAP) |
| `cnvs_occurrence` | INTEGER | nullable (resolve via OCCURRENCE_MAP) |
| `cnvs_lang` | INTEGER | nullable (resolve via LANG_MAP) |
| `cnvs_rating_agent` | INTEGER | nullable |
| `cnvs_rating_nps` | INTEGER | nullable |
| `cnvs_reopened_count` | INTEGER | DEFAULT 0 |
| `cnvs_msgcount` | INTEGER | DEFAULT 0 |
| `cnvs_software` | VARCHAR(255) | nullable |
| `cnvs_tax_id` | VARCHAR(50) | nullable |
| `cnvs_description` | TEXT | nullable |

**Índices:** `idx_conversations_bird`, `idx_conversations_status`, `idx_conversations_created`, `idx_conversations_updated`

### `messages`

| Coluna | Tipo | Constraints |
|--------|------|-------------|
| `msgs_id` | SERIAL | **PK** |
| `msgs_bird` | VARCHAR(255) | **UNIQUE NOT NULL** |
| `msgs_cnvs` | INTEGER | **FK → conversations.cnvs_id** NOT NULL |
| `msgs_agnt` | INTEGER | **FK → agents.agnt_id** nullable |
| `msgs_direction` | VARCHAR(20) | nullable |
| `msgs_status` | VARCHAR(50) | nullable |
| `msgs_type` | VARCHAR(50) | nullable |
| `msgs_content` | TEXT | nullable |
| `msgs_created` | TIMESTAMP | nullable |
| `msgs_updated` | TIMESTAMP | nullable |

**Índices:** `idx_messages_bird`, `idx_messages_cnvs`, `idx_messages_created`, `idx_messages_direction`, `idx_messages_cnvs_created` (composite)

### `sync`

| Coluna | Tipo | Constraints |
|--------|------|-------------|
| `sync_id` | SERIAL | **PK** |
| `sync_resource` | VARCHAR(50) | NOT NULL |
| `sync_created` | TIMESTAMP | DEFAULT now() |
| `sync_duration` | REAL | nullable |
| `sync_records_count` | INTEGER | nullable |
| `sync_cursor` | VARCHAR(255) | nullable |
| `sync_offset` | INTEGER | DEFAULT 0 |

**Índice:** `idx_sync_resource_created` (composite)

### `sync_errors`

| Coluna | Tipo | Constraints |
|--------|------|-------------|
| `err_id` | SERIAL | **PK** |
| `err_resource` | VARCHAR(50) | nullable |
| `err_code` | VARCHAR(50) | nullable |
| `err_message` | TEXT | nullable |
| `err_context` | TEXT | nullable |
| `err_at` | TIMESTAMP | DEFAULT now() |
| `err_retry_count` | INTEGER | DEFAULT 0 |
| `err_resolved_at` | TIMESTAMP | nullable |

## Materialized View: `vw_survey_data`

View que faz JOIN de 4 tabelas (messages + conversations + agents + contacts). Reduz query time de ~900ms para ~50ms.

```sql
SELECT
  ca.agnt_name AS conversation_agent_name,
  ma.agnt_name AS message_agent_name,
  c.cnts_id, c.cnts_name, c.cnts_phone,
  cv.cnvs_id, cv.cnvs_created, cv.cnvs_updated, cv.cnvs_status,
  cv.cnvs_lang, cv.cnvs_software, cv.cnvs_tax_id, cv.cnvs_dept,
  cv.cnvs_rating_agent, cv.cnvs_rating_nps,
  cv.cnvs_contact_reason, cv.cnvs_occurrence,
  cv.cnvs_channel, cv.cnvs_description,
  m.msgs_id, m.msgs_created, m.msgs_direction, m.msgs_agnt
FROM messages m
JOIN conversations cv ON m.msgs_cnvs = cv.cnvs_id
LEFT JOIN agents ca ON cv.cnvs_agnt = ca.agnt_id
LEFT JOIN agents ma ON m.msgs_agnt = ma.agnt_id
JOIN contacts c ON cv.cnvs_cnts = c.cnts_id
ORDER BY cv.cnvs_id, m.msgs_created ASC;
```

**Índices na MV:**
- `idx_vw_survey_data_pk` (cnvs_id, msgs_id) — **UNIQUE** (requerido para REFRESH CONCURRENTLY)
- `idx_vw_survey_created_updated` (cnvs_created, cnvs_updated) — filtro data OR
- `idx_vw_survey_updated_created` (cnvs_updated, cnvs_created) — filtro data OR reverso

**Refresh:** `REFRESH MATERIALIZED VIEW CONCURRENTLY vw_survey_data` (após cada sync)

## Relationships

```
contacts (1) ──< (N) conversations (N) >── (1) agents
                           │
                           │
conversations (1) ──< (N) messages (N) >── agents
```

| Origem | Coluna | Destino | Cardinalidade |
|--------|--------|---------|---------------|
| conversations | cnvs_cnts | contacts.cnts_id | N:1 (nullable) |
| conversations | cnvs_agnt | agents.agnt_id | N:1 (nullable) |
| messages | msgs_cnvs | conversations.cnvs_id | N:1 (NOT NULL) |
| messages | msgs_agnt | agents.agnt_id | N:1 (nullable) |

## Colunas Resolvidas via Python (sem FK)

| Coluna | Resolve via | Fonte |
|--------|-------------|-------|
| `cnvs_dept` | `constants.resolve_dept()` | `business_config.yaml` → DEPT_MAP |
| `cnvs_contact_reason` | `constants.resolve_reason()` | `business_config.yaml` → REASON_MAP |
| `cnvs_occurrence` | `constants.resolve_occurrence()` | `business_config.yaml` → OCCURRENCE_MAP |
| `cnvs_lang` | `constants.resolve_lang()` | `business_config.yaml` → LANG_MAP |
| `cnvs_channel` | `constants.resolve_channel()` | `business_config.yaml` → CHANNEL_MAP |

## Migrations

Aplicadas automaticamente na inicialização da API (`_init_schema()` em `api/main.py`):

1. `infrastructure/database/migrations/001_initial.sql` — schema inicial (tabelas)
2. `infrastructure/database/migrations/002_materialized_view.sql` — materialized view para dashboard rápido

## Conexão

- **DSN:** `DATABASE_URL` env var
- **Pool:** min=2, max=10 (asyncpg)
- **Docker:** `postgres:18-alpine`, porta 5432, user `mbird`
