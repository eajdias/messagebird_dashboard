# Plano de Simplificação Extrema — new_bird

> **Objetivo:** Remover boilerplate e abstrações desnecessárias mantendo 100% das funcionalidades atuais.

## 1. SQLite Removal ✅ (Concluído)

### Removido
- `scripts/migrate_sqlite_to_pg.py` — script de migração (não há mais SQLite para migrar)
- `infrastructure/database/sqlite_repository.py` — repositório SQLite legado
- `infrastructure/database/queries.py` — queries SQLite (substituído por `queries_pg.py`)
- `infrastructure/database/connection.py` — `DatabaseConnection` (SQLite/aiosqlite)
- `infrastructure/database/sync_connection.py` — `SyncConnection` (SQLite bulk)
- `infrastructure/database/init_db.py` — schema SQLite
- `infrastructure/api/sync.py` — pipeline de sync SQLite legado (1186 linhas)

### Alterado
- `main.py` — removidos comandos `report`, `total`, `quality` que dependiam de `SqliteReportRepository`
- `pyproject.toml` — removidas dependências `aiosqlite`, `sqlalchemy`, `alembic`
- `docs/CHECKLIST.md` — atualizado para refletir remoção
- `AGENTS.md` (root) — atualizado estrutura
- `infrastructure/AGENTS.md` — atualizado estrutura

### Por quê?
PostgreSQL (via asyncpg) é o banco primário desde a conclusão da Fase 2. SQLite era mantido como fallback legado, mas sem uso real — nem testes, nem produção, nem desenvolvimento.

---

## 2. Alembic/SQLAlchemy Removal ✅ (Concluído)

### Removido
- `alembic/` — diretório completo (env.py, script.py.mako, versions/001_initial.py)
- `alembic.ini` — configuração Alembic
- `infrastructure/database/migrations/models.py` — modelos SQLAlchemy (133 linhas)

### Por quê?
A aplicação aplica migrations automaticamente na inicialização via `_init_schema()` em `api/main.py`, lendo `001_initial.sql` e `002_materialized_view.sql` diretamente. Alembic e SQLAlchemy eram usados apenas para geração manual de migrations — nunca executados em produção.

---

## 3. API Schema Factory ✅ (Concluído)

### O que foi feito
- Criado `api/schemas/_base.py` com `StatusResponse` (status + message) e `list_response()` (factory para list wrappers)
- Wrappers repetitivos substituídos por aliases:
  - `SyncTriggerResponse = StatusResponse`
  - `GenerateReportResponse(StatusResponse)` + `report_id`
  - `AgentListResponse = list_response(AgentItem, "agents")`
  - `DepartmentListResponse = list_response(DepartmentItem, "departments")`
  - `AgentRankingResponse = list_response(AgentRankingItem, "agents")`
  - `ChannelResponse = list_response(ChannelItem, "channels")`
  - `AvailableReportsResponse = list_response(AvailableReportItem, "reports")`
  - `EvolutionResponse = list_response(EvolutionMonth, "evolution")`
- Interface da API inalterada — field names `agents`, `departments`, `channels`, etc. preservados

## 4. Sync Pipeline Modular ✅ (Concluído)

### O que foi feito
- `pg_sync_engine.py` (975 linhas) quebrado em 5 módulos:
  - `sync_core.py` (142 linhas) — PgSyncManager + helpers
  - `sync_contacts.py` (62 linhas) — sync de contatos
  - `sync_conversations.py` (206 linhas) — sync de conversas
  - `sync_messages.py` (276 linhas) — sync de mensagens
  - `sync_surveys.py` (172 linhas) — extração de surveys
  - `pg_sync_engine.py` (112 linhas) — orquestrador
- Interface pública (`trigger_sync_pg()`) inalterada
- Testes: 95/95 passando

## 5. Configuração Unificada
- **Status:** Análise concluída — sem mudanças necessárias
- **Justificativa:** A configuração já está bem separada por responsabilidade:
  - `infrastructure/api/config.py` → env vars da MessageBird API
  - `infrastructure/config/config_loader.py` → carregamento YAML (business config)
  - `infrastructure/config/sync_profiles.py` → perfis de sincronização
  - `domain/constants.py` → constantes de domínio
- Forçar a unificação num único arquivo aumentaria a complexidade (acoplamento de concerns diferentes) sem benefício real.

---

## Critérios de Sucesso

- Testes existentes continuam passando (100% cobertura mantida)
- Todos os endpoints da API funcionam exatamente como antes
- Frontend não percebe nenhuma mudança
- Build CI/CD não quebra