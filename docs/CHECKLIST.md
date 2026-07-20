# Checklist de Desenvolvimento — new_bird

> Atualizado em: 2026-07-20

---

## Status Geral

| Fase | Estado | Bloqueador Principal |
|------|--------|---------------------|
| Fase 0: Setup e Infraestrutura | ✅ Concluída | — |
| Fase 1: Backend Core (domain + app + infra) | ✅ Concluída | — |
| Fase 2: Backend API (endpoints) | ✅ Concluída | — |
| Fase 3: Frontend Dashboard | ✅ Concluída | — |
| Fase 4: Integração e Deploy | 🔲 Pendente | — |

> **Migração SQLite → PostgreSQL (sync pipeline) concluída:**
> - `PostgresSyncConnection` (asyncpg) — ✅
> - `queries_pg.py` com `$1-$N` params — ✅
> - `pg_sync_engine.py` (PgSyncManager) — ✅
> - Message sync, survey extraction, reopen detection — ✅
> - `client.py` tipado com params de filtro — ✅

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

## Fase 2: Backend API ✅

### ⚠️ Migração Sync Pipeline SQLite → PostgreSQL ✅

- [x] Criar `PostgresSyncConnection` — asyncpg pool wrapper (`sync_connection_pg.py`)
- [x] Criar queries PostgreSQL compatíveis (`queries_pg.py`) — `$1-$N` params, `ON CONFLICT`, `NOW()`
- [x] Criar `pg_sync_engine.py` (PgSyncManager) — contact sync, conversation sync
- [x] Implementar message sync (`sync_messages`, `_sync_messages_internal`, `sync_all_messages`)
- [x] Implementar survey extraction (`update_conversation_surveys`, `backfill_surveys`)
- [x] Implementar reopen detection (`cnvs_reopened_count`)
- [x] Adaptar `infrastructure/api/client.py` — tipos + params de filtro (`createdDatetimeAfter`, etc.)
- [x] Adaptar `application/use_cases/sync_database.py` — delega para `trigger_sync_pg()`
- [x] Marcar `sqlite_repository.py`, `connection.py`, `sync_connection.py`, `init_db.py` como "legado"

### Configuração

- [x] Integrar APScheduler no `api/main.py` (sync incremental a cada 15 min, full diário 3:00 AM)
- [x] Configurar CORS dinâmico via `CORS_ORIGINS` do `.env` (middleware.py)
- [x] Garantir que `config_loader.py` funciona com PostgreSQL (YAML loaders são DB-agnostic)

### Auth

- [x] Implementar `POST /api/v1/auth/login` — body `LoginRequest`, retorna `TokenResponse` JWT
- [ ] Implementar `POST /api/v1/auth/refresh` (renovar token)
- [x] Implementar middleware de autenticação JWT (`get_current_user` dependency)

### Dashboard

- [x] Implementar `GET /api/v1/dashboard/summary` — `response_model=DashboardSummaryResponse`
- [x] Implementar `GET /api/v1/dashboard/bsc` — `response_model=BSCResponse`
- [x] Implementar `GET /api/v1/dashboard/kpis` — `response_model=KPIResponse`
- [x] Implementar `GET /api/v1/dashboard/evolution` — `response_model=EvolutionResponse`
- [x] Implementar `GET /api/v1/dashboard/agents` — `response_model=AgentRankingResponse`
- [x] Implementar `GET /api/v1/dashboard/channels` — `response_model=ChannelResponse`

### Conversations

- [x] Implementar `GET /api/v1/conversations/` — `response_model=ConversationListResponse`, 11 filtros
- [x] Implementar `GET /api/v1/conversations/{id}` — `response_model=ConversationDetailResponse`
- [x] Implementar `GET /api/v1/conversations/{id}/messages` — `response_model=ConversationMessagesResponse`

### Reports

- [x] Implementar `POST /api/v1/reports/generate` — body `ReportRequest`, `response_model=GenerateReportResponse`
- [x] Implementar `GET /api/v1/reports/{id}/download` — `response_model=DownloadReportResponse`
- [x] Implementar `GET /api/v1/reports/available` — `response_model=AvailableReportsResponse`

### Admin

- [x] Implementar `GET /api/v1/admin/sync/status` — `response_model=SyncStatusResponse`
- [x] Implementar `POST /api/v1/admin/sync/trigger` — body `SyncTriggerRequest`, `response_model=SyncTriggerResponse`
- [x] Implementar `GET /api/v1/admin/agents` — dados reais de `domain.constants.AGENTS`
- [x] Implementar `GET /api/v1/admin/departments` — dados reais de `domain.constants.DEPT_MAP`
- [x] Implementar `GET /api/v1/admin/health` — `response_model=HealthResponse`

### Pydantic Schemas ✅

- [x] Criar `api/schemas/auth.py` (LoginRequest, TokenResponse, UserResponse)
- [x] Criar `api/schemas/dashboard.py` (DashboardSummaryResponse, BSCResponse, KPIResponse, EvolutionResponse, AgentRankingResponse, ChannelResponse)
- [x] Criar `api/schemas/conversations.py` (ConversationListResponse, ConversationDetailResponse, ConversationMessagesResponse, MessageResponse)
- [x] Criar `api/schemas/reports.py` (ReportRequest, GenerateReportResponse, DownloadReportResponse, AvailableReportsResponse)
- [x] Criar `api/schemas/admin.py` (SyncStatusResponse, SyncTriggerRequest, SyncTriggerResponse, AgentListResponse, DepartmentListResponse, HealthResponse)
- [x] Criar `api/schemas/__init__.py` (exports centralizados)

### Migração SQLite → PostgreSQL (dados)

- [x] Criar script `scripts/migrate_sqlite_to_pg.py`
  - Ler `m_bird.db` (SQLite) via aiosqlite
  - Inserir no PostgreSQL via asyncpg
  - Handle denormalização: SQLite usa FKs inteiros, PG usa colunas legíveis
- [x] Testar migração com banco existente (`m_bird.db`)
- [x] Validar integridade dos dados migrados

---

## Fase 3: Frontend Dashboard ✅

### Layout e Navegação
- [x] Criar componentes UI base: `Button`, `Card`, `Table`, `Input`, `Badge`
- [x] Criar `Sidebar.tsx` (navegação lateral)
- [x] Criar `TopBar.tsx` (título + theme toggle + user menu)
- [x] Criar layout autenticado (`(dashboard)/layout.tsx`)

### Auth
- [x] Criar página `/login/page.tsx` (formulário + chamada API)
- [x] Criar hook `useAuth.ts` (context + JWT management)
- [x] Criar proteção de rotas (redirect se não autenticado)

### Dashboard Home
- [x] Criar `KPICard.tsx` (NPS, FRT, ART, Volume com trend)
- [x] Criar `BSCTable.tsx` (tabela BSC com cores verde/amarelo/vermelho)
- [x] Criar `EvolutionChart.tsx` (line chart evolução mensal - Recharts)
- [x] Criar `AgentRanking.tsx` (top agentes por métrica)
- [x] Criar `ChannelBreakdown.tsx` (pie chart por canal)
- [x] Montar página `(dashboard)/page.tsx` com todos os componentes

### Conversations
- [x] Criar `ConversationTable.tsx` (TanStack Table, paginação, sort)
- [x] Criar página `/conversations/page.tsx`
- [x] Criar página `/conversations/[id]/page.tsx` (message thread)

### Reports
- [x] Criar `ReportForm.tsx` (formulário: período, tipo, grupo)
- [x] Criar `ReportList.tsx` (relatórios gerados para download)
- [x] Criar página `/reports/page.tsx`

### Hooks e Types
- [x] Criar `hooks/useDashboard.ts` (fetch de métricas)
- [x] Criar `hooks/useConversations.ts` (fetch de conversas)
- [x] Criar `types/index.ts` (interfaces TypeScript)

### Dark/Light Mode
- [x] Configurar temas (next-themes)
- [x] Toggle no TopBar com persistência

---

## Fase 4: Integração e Deploy 🔲

### Docker
- [x] Criar `frontend/Dockerfile` (Node 22 Alpine, multi-stage)
- [x] Completar `docker-compose.yml` com serviço frontend
- [x] Testar `docker compose up` completo — 3/3 serviços healthy

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
