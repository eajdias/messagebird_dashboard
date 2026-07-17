# Checklist de Desenvolvimento — new_bird

> Atualizado em: 2026-07-17

---

## Status Geral

| Fase | Estado | Bloqueador Principal |
|------|--------|---------------------|
| Fase 0: Setup e Infraestrutura | ✅ Concluída | — |
| Fase 1: Backend Core (domain + app + infra) | ✅ Concluída | — |
| Fase 2: Backend API (endpoints) | 🔲 Pendente | Sync messages (PG) + surveys |
| Fase 3: Frontend Dashboard | 🔲 Pendente | — |
| Fase 4: Integração e Deploy | 🔲 Pendente | — |

> **Migração SQLite → PostgreSQL concluída (estrutural):**
> - Schema Postgres (`001_initial.sql`, `models.py`, migration Alembic `001_initial.py`) — ✅
> - `PostgresReportRepository` com colunas `cnvs_*` reais — ✅
> - `queries_pg.py` com queries asyncpg — ✅
> - `PostgresSyncConnection` (asyncpg) — ✅
> - `pg_sync_engine.py` (PgSyncManager para sync estrutural) — ✅
> - `api/dependencies.py` injeta pool asyncpg — ✅
> - Sync de *messages* e *surveys* no PG pendente — 🔲

---

## Fase 0: Setup e Infraestrutura ✅

- [x] Criar estrutura de diretórios (`new_bird/`)
- [x] Criar `AGENTS.md` para todos os módulos (8 arquivos)
- [x] Criar `pyproject.toml` com dependências Python 3.14
- [x] Criar `.env.example` com template de variáveis
- [x] Criar `.gitignore` (Python + Node.js + Docker)
- [x] Criar `docker-compose.yml` (PostgreSQL 18 + API + Frontend)
- [x] Criar `Dockerfile` (Python 3.14-slim)
- [x] Pesquisar e documentar versões de todas as dependências
- [x] Configurar frontend: `package.json`, `tsconfig.json`, `next.config.ts`, `postcss.config.mjs`
- [x] Criar esqueleto React: `layout.tsx`, `page.tsx`, `globals.css`, `theme-provider.tsx`
- [x] Criar `lib/api.ts` (Axios client) e `lib/utils.ts` (cn)
- [x] Criar esqueleto FastAPI: `main.py`, `auth.py`, `middleware.py`, `dependencies.py`
- [x] Criar route stubs: auth, dashboard, conversations, reports, admin
- [x] Criar migration SQL: `001_initial.sql` (6 tabelas PostgreSQL)
- [x] Configurar Alembic: `alembic.ini`, `alembic/env.py`, `models.py` (SQLAlchemy)
- [x] Copiar `business_config.yaml` + `business_bsc.yaml`
- [x] Copiar testes básicos: `conftest.py`, `test_health.py`
- [x] Adicionar `LICENSE` (MIT)
- [x] Criar `README.md`

---

## Fase 1: Backend Core ✅

### Domain Layer
- [x] Copiar `domain/entities/report_data.py` (RawMessageData, RawConversationData, ProcessedReportData)
- [x] Copiar `domain/metrics/` (ARTCalculator, FRTCalculator, DurationCalculator)
- [x] Copiar `domain/strategies/metrics_strategy.py` (MetricStrategy ABC)
- [x] Copiar `domain/services/metrics_calculator.py` (NPS, SLA, FRT, distribuições)
- [x] Copiar `domain/constants.py` (headers, maps, KPI config, NPS config)
- [x] Copiar `domain/logic.py` (parse_datetime, business_duration, reopen detection)

### Application Layer
- [x] Copiar `application/interfaces/repository.py` (ReportRepository ABC)
- [x] Copiar `application/interfaces/exporter.py` (ReportExporter ABC + DashboardDTO)
- [x] Copiar `application/services/report_aggregator.py` (agente, departamento, BSC)
- [x] Copiar `application/services/sub_aggregators.py` (temporal, topic, rating)
- [x] Copiar `application/services/auditoria_*.py` (contatos, demanda, OS)
- [x] Copiar `application/use_cases/` (generate_report, data_quality_report, sync_database)

### Infrastructure Layer
- [x] Copiar `infrastructure/api/client.py` (MessageBirdClient httpx async)
- [x] Copiar `infrastructure/api/config.py` (env vars, agent lookup)
- [x] Copiar `infrastructure/api/sync.py` (engine de sincronização 1253 linhas)
- [x] Copiar `infrastructure/config/config_loader.py` (loaders de YAML)
- [x] Copiar `infrastructure/database/sqlite_repository.py` (referência legado)
- [x] Copiar `infrastructure/database/queries.py` (queries SQLite — referência)
- [x] Copiar `infrastructure/database/connection.py` + `sync_connection.py` + `init_db.py`
- [x] Copiar `infrastructure/exporters/` (excel, pdf, markdown, metrics_cache, _bsc_writer, mappers)
- [x] Criar `infrastructure/repositories/postgres_report_repository.py` (asyncpg, 250+ linhas)

### Testes
- [x] Copiar `tests/domain/` (test_logic, test_dept_routing, test_metrics_calculator, test_annual_aggregation)
- [x] Copiar `tests/exporters/` (test_exporter_style, test_metrics_cache, test_metrics_cache_annual)
- [x] Copiar `tests/integration/` (test_report_flow, test_dept_routing_flow)

---

## Fase 2: Backend API 🔲

> **Bloqueador principal:** O pipeline de sync (`sync.py`, 1253 linhas) é 100% SQLite.
> Precisa ser reescrito para PostgreSQL (asyncpg) antes de qualquer endpoint funcionar com dados reais.

### ⚠️ Migração Sync Pipeline SQLite → PostgreSQL (CRÍTICO)

> Itens nesta seção são PREREQUISITOS para os endpoints de sync/admin.

- [ ] Criar `PostgresSyncConnection` — equivalente asyncpg de `SyncConnection` (aiosqlite)
  - Substituir `aiosqlite.connect()` por `asyncpg.create_pool()`
  - Remover PRAGMAs (WAL, synchronous, foreign_keys)
  - Manter interface `transaction()`, `execute_query()`, `execute_many()`
- [ ] Criar queries PostgreSQL compatíveis (`queries_pg.py`)
  - Substituir `?` placeholders por `$1, $2, ...` (estilo asyncpg)
  - Substituir `datetime('now', ?)` por `NOW() - INTERVAL '...'`
  - Substituir `INSERT OR IGNORE` por `ON CONFLICT DO NOTHING`
  - Substituir `INSERT OR REPLACE` por `ON CONFLICT ... DO UPDATE SET`
- [ ] Adaptar `sync.py` para usar `PostgresSyncConnection`
  - `SyncManager.initialize()` → usar asyncpg pool em vez de aiosqlite
  - `SyncManager._upsert_contacts()` → queries PostgreSQL
  - `SyncManager._upsert_conversations()` → queries PostgreSQL
  - `SyncManager._upsert_messages()` → queries PostgreSQL
  - `SyncManager._sync_surveys()` → queries PostgreSQL
  - Todas as 1253 linhas precisam de revisão
- [ ] Adaptar `infrastructure/api/config.py`
  - Substituir `DB_FILENAME = "m_bird.db"` por `DATABASE_URL` (env var)
  - Manter `API_KEY`, `LOOKBACK_MINUTES` etc. inalterados
- [ ] Adaptar `application/use_cases/sync_database.py`
  - Substituir `db_path="m_bird.db"` por conexão PostgreSQL via DI
- [ ] Marcar `sqlite_repository.py`, `connection.py`, `sync_connection.py`, `init_db.py` como "legado — apenas CLI"
- [ ] Renomear `domain/logic.py:to_utc_sqlite_string()` → `to_utc_string()`

### Configuração

- [ ] Integrar APScheduler no `api/main.py` (sync incremental a cada 15 min)
- [ ] Configurar CORS dinâmico via `CORS_ORIGINS` do `.env`
- [ ] Garantir que `config_loader.py` funciona com PostgreSQL (verificar: YAML loaders são DB-agnostic, mas `KPI_CONFIG` e `DEPT_MAP` precisam ser carregados antes dos endpoints)

### Auth

- [ ] Implementar `POST /api/v1/auth/login` (validar credenciais, retornar JWT)
- [ ] Implementar `POST /api/v1/auth/refresh` (renovar token)
- [ ] Implementar middleware de autenticação JWT

### Dashboard

- [ ] Implementar `GET /api/v1/dashboard/summary` (métricas gerais)
- [ ] Implementar `GET /api/v1/dashboard/bsc` (dados BSC T1 + T2)
- [ ] Implementar `GET /api/v1/dashboard/evolution` (evolução mensal 12 meses)
- [ ] Implementar `GET /api/v1/dashboard/agents` (ranking de agentes)
- [ ] Implementar `GET /api/v1/dashboard/channels` (métricas por canal)

### Conversations

- [ ] Implementar `GET /api/v1/conversations` (lista paginada + filtros)
- [ ] Implementar `GET /api/v1/conversations/{id}` (detalhe da conversa)
- [ ] Implementar `GET /api/v1/conversations/{id}/messages` (mensagens)

### Reports

- [ ] Implementar `POST /api/v1/reports/generate` (gerar relatório sob demanda)
- [ ] Implementar `GET /api/v1/reports/{id}/download` (download do arquivo)
- [ ] Implementar `GET /api/v1/reports/available` (listar relatórios)

### Admin

- [ ] Implementar `GET /api/v1/admin/sync/status` (status da última sync)
- [ ] Implementar `POST /api/v1/admin/sync/trigger` (disparar sync manual)
- [ ] Implementar `GET /api/v1/admin/agents` (lista de agentes)
- [ ] Implementar `GET /api/v1/admin/departments` (departamentos)

### Pydantic Schemas

- [ ] Criar `api/schemas/auth.py` (LoginRequest, TokenResponse)
- [ ] Criar `api/schemas/dashboard.py` (DashboardSummary, BSCEvolution, etc.)
- [ ] Criar `api/schemas/conversations.py` (ConversationList, ConversationDetail, Message)
- [ ] Criar `api/schemas/reports.py` (ReportRequest, ReportResponse)

### Migração SQLite → PostgreSQL (dados)

- [ ] Criar script `scripts/migrate_sqlite_to_pg.py`
  - Ler `m_bird.db` (SQLite) via aiosqlite
  - Inserir no PostgreSQL via asyncpg
  - Handle denormalização: SQLite usa FKs inteiros, PG usa colunas legíveis
- [ ] Testar migração com banco existente (`m_bird.db`)
- [ ] Validar integridade dos dados migrados

---

## Fase 3: Frontend Dashboard 🔲

### Layout e Navegação
- [ ] Criar componentes UI base: `Button`, `Card`, `Table`, `Input`, `Badge`
- [ ] Criar `Sidebar.tsx` (navegação lateral)
- [ ] Criar `TopBar.tsx` (título + theme toggle + user menu)
- [ ] Criar layout autenticado (`/dashboard/layout.tsx`)

### Auth
- [ ] Criar página `/login/page.tsx` (formulário + chamada API)
- [ ] Criar hook `useAuth.ts` (context + JWT management)
- [ ] Criar proteção de rotas (redirect se não autenticado)

### Dashboard Home
- [ ] Criar `KPICard.tsx` (NPS, FRT, ART, Volume com trend)
- [ ] Criar `BSCChart.tsx` (tabela BSC com cores verde/amarelo/vermelho)
- [ ] Criar `EvolutionChart.tsx` (line chart evolução mensal - Recharts)
- [ ] Criar `AgentRanking.tsx` (top agentes por métrica)
- [ ] Criar `ChannelBreakdown.tsx` (pie chart por canal)
- [ ] Criar `HeatmapChart.tsx` (distribuição horária)
- [ ] Montar página `/dashboard/page.tsx` com todos os componentes

### Conversations
- [ ] Criar `ConversationTable.tsx` (TanStack Table, paginação, sort)
- [ ] Criar `ConversationFilters.tsx` (filtros laterais)
- [ ] Criar `MessageThread.tsx` (timeline de mensagens)
- [ ] Criar página `/conversations/page.tsx`

### Reports
- [ ] Criar `ReportForm.tsx` (React Hook Form + Zod: período, tipo, grupo)
- [ ] Criar `ReportList.tsx` (relatórios gerados para download)
- [ ] Criar página `/reports/page.tsx`

### Hooks e Types
- [ ] Criar `hooks/useDashboard.ts` (fetch de métricas)
- [ ] Criar `hooks/useConversations.ts` (fetch de conversas)
- [ ] Criar `types/index.ts` (interfaces TypeScript)

### Dark/Light Mode
- [ ] Configurar temas (dark: slate-900, light: white)
- [ ] Toggle no TopBar com persistência localStorage

---

## Fase 4: Integração e Deploy 🔲

### Docker
- [ ] Criar `frontend/Dockerfile` (Node 22 Alpine, multi-stage)
- [ ] Completar `docker-compose.yml` com serviço frontend
- [ ] Testar `docker compose up` completo

### Cloudflare Tunnel
- [ ] Configurar `app.empresa.com` → `localhost:3000`
- [ ] Configurar `api.empresa.com` → `localhost:8000`
- [ ] Testar acesso externo via HTTPS

### Migração de Dados
- [ ] Executar script de migração SQLite → PostgreSQL
- [ ] Validar integridade dos dados migrados
- [ ] Testar sync automático com MessageBird API

### Testes Finais
- [ ] Rodar todos os testes: `pytest -v`
- [ ] Testar fluxo completo: login → dashboard → conversas → relatório
- [ ] Testar exportação Excel/PDF via API
- [ ] Testar dark/light mode no frontend

### Documentação
- [ ] Criar `docs/deploy.md` (guia de deploy na VPS)
- [ ] Atualizar README do new_bird

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Concluído |
| 🔲 | Pendente |
| 🔄 | Em andamento |
| ⚠️ | Bloqueado |
