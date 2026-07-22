# Checklist de Desenvolvimento — new_bird

> Atualizado em: 2026-07-22

---

## Status Geral

| Fase | Estado | Bloqueador Principal |
|------|--------|---------------------|
| Fase 0: Setup e Infraestrutura | ✅ Concluída | — |
| Fase 1: Backend Core (domain + app + infra) | ✅ Concluída | — |
| Fase 2: Backend API (endpoints) | ✅ Concluída | — |
| Fase 3: Frontend Dashboard | ✅ Concluída | — |
| Fase 4: Integração e Deploy | 🟡 Parcial | Testes com MessageBird API real pendentes |

> **PostgreSQL é o único banco — SQLite removido (Julho 2026):**
> - SQLite e todo código legado removidos
> - Sync pipeline usa asyncpg + PgSyncManager
> - Schema gerenciado via migrations SQL (001-004)

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
- [x] Criar esqueleto React: `layout.tsx`, `page.tsx`, `globals.css`
- [x] Criar `lib/api.ts` (Axios client) e `lib/utils.ts` (cn)
- [x] Criar esqueleto FastAPI: `main.py`, `auth.py`, `middleware.py`, `dependencies.py`
- [x] Criar route stubs: auth, dashboard, conversations, reports, admin
- [x] Criar migration SQL: `001_initial.sql` (6 tabelas PostgreSQL)
- [x] Copiar `business_config.yaml` + `business_bsc.yaml`
- [x] Copiar testes básicos: `conftest.py`, `test_health.py`
- [x] Criar `README.md`

---

## Fase 1: Backend Core ✅

### Domain Layer
- [x] Copiar `domain/entities/report_data.py` (RawMessageData, RawConversationData, ProcessedReportData)
- [x] Copiar `domain/metrics/` (ARTCalculator, FRTCalculator, DurationCalculator)
- [x] Copiar `domain/services/metrics_calculator.py` (NPS, SLA, FRT, distribuições)
- [x] Copiar `domain/constants.py` (headers, maps, KPI config)
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
- [x] Copiar `infrastructure/config/config_loader.py` (loaders de YAML)
- [x] Copiar `infrastructure/database/queries_pg.py` (SQL queries PostgreSQL)
- [x] Copiar `infrastructure/database/migrations/001_initial.sql` ao `004_add_agnt_grp_to_view.sql`
- [x] Copiar `infrastructure/exporters/` (excel, pdf, markdown, metrics_cache, _bsc_writer)
- [x] Criar `infrastructure/repositories/postgres_report_repository.py` (asyncpg, 340+ linhas)

### Sync Pipeline
- [x] `pg_sync_engine.py` — orquestrador
- [x] `sync_core.py` — PgSyncManager, parse_dt, seed_known_agents
- [x] `sync_contacts.py` — contact sync
- [x] `sync_conversations.py` — conversation sync (full structural)
- [x] `sync_messages.py` — message sync (por período ou recente)
- [x] `sync_surveys.py` — survey extraction

### Testes
- [x] `tests/domain/` (test_logic, test_dept_routing, test_metrics_calculator, test_annual_aggregation)
- [x] `tests/exporters/` (test_exporter_style, test_metrics_cache, test_metrics_cache_annual)
- [x] `tests/integration/` (test_report_flow, test_dept_routing_flow)
- [x] `tests/infrastructure/test_pg_sync_engine.py` (sync unit tests)
- [x] `tests/infrastructure/test_client.py` (HTTP client mocks)

---

## Fase 2: Backend API ✅

### Auth
- [x] Implementar `POST /api/v1/auth/login` — body `LoginRequest`, retorna `TokenResponse` JWT
- [x] Implementar `POST /api/v1/auth/refresh` (renovar token) — sliding session
- [x] Implementar middleware de autenticação JWT (`get_current_user` dependency)

### Dashboard (6 endpoints)
- [x] `GET /api/v1/dashboard/summary` — `response_model=DashboardSummaryResponse`
- [x] `GET /api/v1/dashboard/bsc` — `response_model=BSCResponse`
- [x] `GET /api/v1/dashboard/kpis` — `response_model=KPIResponse`
- [x] `GET /api/v1/dashboard/evolution` — `response_model=EvolutionResponse`
- [x] `GET /api/v1/dashboard/agents` — `response_model=AgentRankingResponse`
- [x] `GET /api/v1/dashboard/channels` — `response_model=ChannelResponse`

### Conversations (3 endpoints)
- [x] `GET /api/v1/conversations/` — 11 filtros, paginação
- [x] `GET /api/v1/conversations/{id}` — detalhe com mensagens
- [x] `GET /api/v1/conversations/{id}/messages` — mensagens da conversa

### Reports (3 endpoints)
- [x] `POST /api/v1/reports/generate` — geração sob demanda
- [x] `GET /api/v1/reports/{id}/download` — download do arquivo
- [x] `GET /api/v1/reports/available` — lista relatórios disponíveis

### Admin (5 endpoints)
- [x] `GET /api/v1/admin/health` — health check (sem auth)
- [x] `GET /api/v1/admin/sync/status` — status da sync
- [x] `POST /api/v1/admin/sync/trigger` — trigger manual (full_sync, sync_messages, messages_days, backfill_surveys, sync_today)
- [x] `GET /api/v1/admin/agents` — agentes do business_config.yaml
- [x] `GET /api/v1/admin/departments` — departamentos do business_config.yaml

### Pydantic Schemas ✅
- [x] `api/schemas/auth.py`, `dashboard.py`, `conversations.py`, `reports.py`, `admin.py`
- [x] `api/schemas/__init__.py` — exports centralizados com `_base.list_response()`

---

## Fase 3: Frontend Dashboard ✅

### Layout e Navegação
- [x] Componentes UI base: `Button`, `Card`, `Table`, `Input`, `Badge`
- [x] `Sidebar.tsx` (navegação lateral)
- [x] `TopBar.tsx` (título + theme toggle + user menu)
- [x] Layout autenticado (`(dashboard)/layout.tsx`)

### Auth
- [x] Página `/login/page.tsx` (formulário + chamada API)
- [x] Hook `useAuth.ts` (context + JWT management)
- [x] Proteção de rotas (redirect se não autenticado)

### Dashboard Home
- [x] `KPICard.tsx` (NPS, FRT, ART, Volume com trend)
- [x] `BSCTable.tsx` (tabela BSC com cores verde/amarelo/vermelho)
- [x] `EvolutionChart.tsx` (line chart evolução mensal - Recharts)
- [x] `AgentRanking.tsx` (top agentes por métrica)
- [x] `ChannelBreakdown.tsx` (pie chart por canal)
- [x] Página `(dashboard)/page.tsx` com todos os componentes

### Conversations
- [x] Página `/conversations/page.tsx` (TanStack Table, filtros, paginação inline)
- [x] Página `/conversations/[id]/page.tsx` (message thread)

### Reports
- [x] Página `/reports/page.tsx` (formulário: período, tipo, grupo + listagem inline)

### Hooks e Types
- [x] `hooks/useDashboard.ts`, `useConversations.ts`
- [x] `types/index.ts` (interfaces TypeScript)

### Dark/Light Mode
- [x] next-themes configurado
- [x] Toggle no TopBar com persistência

---

## Fase 4: Integração e Deploy 🔲

### Docker
- [x] Criar `Dockerfile` (Python 3.14-slim)
- [x] Criar `frontend/Dockerfile` (Node 22 Alpine, multi-stage)
- [x] Completar `docker-compose.yml` com 3 serviços
- [x] Testar `docker compose up` completo — 3/3 serviços healthy

### Cloudflare Tunnel
- [x] Portas definidas: API `:8050`, Frontend `:3050`

### Dados
- [ ] Testar sync automático com MessageBird API real (requer API key válida)

### Testes Finais
- [x] Rodar todos os testes: `pytest -v` (108/112 passando)
- [ ] Testar fluxo completo: login → dashboard → conversas → relatório
- [ ] Testar exportação Excel/PDF via API
- [ ] Testar dark/light mode no frontend

### Documentação
- [x] Criar `docs/deploy.md` (guia de deploy na VPS)
- [x] Revisar docs existentes (API, DATABASE, ARCHITECTURE, CHECKLIST)

---

## Itens Adicionais Implementados

### Backend (auth)
- [x] `POST /api/v1/auth/register` — implementado (MVP sem tabela users)
- [x] `POST /api/v1/auth/refresh` — sliding session (renova JWT expirado)

### Frontend
- [x] `Settings` page — info da conta, status do sistema, sync manual
- [x] Exportação CSV nas conversas — botão na página de listagem
- [x] Página de Agents já existia (não documentada no checklist)

### Infra
- [x] `bcrypt==4.0.1` pinado no `pyproject.toml` e `Dockerfile` (compatibilidade passlib)
- [x] `NEXT_PUBLIC_API_URL` adicionado ao frontend no `docker-compose.yml`
- [x] Doc de deploy criada em `docs/deploy.md`

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Concluído |
| 🔲 | Pendente |
| 🔄 | Em andamento |
