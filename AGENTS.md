# new_bird — Omnichannel Reporting Dashboard (Web)

> Dashboard web para relatórios omnichannel Bird API.
> Backend: FastAPI (Python 3.14) | Frontend: Next.js 16 (TypeScript 7.0) | DB: PostgreSQL 18

---

## Estrutura do Projeto

```
new_bird/
├── api/                    # FastAPI — endpoints REST, auth JWT, scheduler
│   ├── main.py             # App factory, lifespan (APScheduler)
│   ├── auth.py             # JWT: create, verify, password hashing
│   ├── dependencies.py     # DI container (db session, repository)
│   ├── middleware.py        # CORS config
│   ├── schemas/            # Pydantic models (request/response)
│   └── routes/             # auth, dashboard, conversations, reports, admin
│
├── frontend/               # Next.js 16 — dashboard interativo
│   ├── app/                # App Router (layout, pages)
│   ├── components/         # React components (ui, dashboard, layout)
│   ├── lib/                # api.ts (Axios), utils.ts (cn)
│   ├── hooks/              # useAuth, useDashboard, useConversations
│   ├── types/              # TypeScript interfaces
│   ├── package.json        # React 19, Tailwind 4, Recharts, shadcn/ui
│   └── tsconfig.json       # TypeScript 7.0 strict
│
├── domain/                 # Lógica pura de negócio (ZERO deps externas)
│   ├── constants.py        # Maps, KPI config, NPS config, headers
│   ├── logic.py            # parse_datetime, business_duration, reopen
│   ├── entities/           # RawConversationData, ProcessedReportData
│   ├── metrics/            # ARTCalculator, FRTCalculator, DurationCalculator
│   ├── strategies/         # MetricStrategy (ABC)
│   └── services/           # MetricsCalculator (NPS, SLA, scoring)
│
├── application/            # Orquestração e use cases
│   ├── interfaces/         # ReportRepository (ABC), ReportExporter (ABC), DashboardDTO
│   ├── services/           # ReportAggregator, SubAggregators, Auditoria*
│   └── use_cases/          # GenerateReport, DataQualityReport, SyncDatabase
│
├── infrastructure/         # Detalhes técnicos
│   ├── api/                # MessageBirdClient (httpx), config, sync.py (1253 loc)
│   ├── config/             # config_loader.py (YAML loaders)
│   ├── database/           # SQLite (legado), queries, connection, init_db
│   ├── repositories/       # PostgresReportRepository (asyncpg)
│   ├── exporters/          # Excel, PDF, Markdown, metrics_cache, _bsc_writer
│   └── sync/               # (reservado para sync engine async)
│
├── tests/                  # Pytest
│   ├── domain/             # test_logic, test_dept_routing, test_metrics_calculator
│   ├── exporters/          # test_exporter_style, test_metrics_cache
│   └── integration/        # test_report_flow, test_dept_routing_flow
│
├── docs/                   # Documentação
│   ├── plano_web_dashboard.md  # Plano completo CLI → Web
│   └── CHECKLIST.md            # Checklist de desenvolvimento
│
├── business_config.yaml    # Mapas de negócio (dept, motivos, agentes, canais)
├── business_bsc.yaml       # KPIs, thresholds NPS/BSC, scoring BSC
├── docker-compose.yml      # PostgreSQL 18 + API + Frontend
├── Dockerfile              # Python 3.14-slim
├── pyproject.toml          # Dependências Python
├── main.py                 # CLI legado (ponto de entrada original)
└── .env.example            # Template de variáveis de ambiente
```

---

## Fluxo de Dependências (Clean Architecture)

```
domain/ ← application/ ← api/ ← infrastructure/
   ↑           ↑                      ↑
   │           │                      │
   └───────────┴──────────────────────┘
   (nenhuma dependência deve voltar)
```

| Camada | Pode importar | NÃO pode importar |
|--------|---------------|-------------------|
| `domain/` | stdlib Python apenas | application/, infrastructure/, api/ |
| `application/` | domain/ | infrastructure/, api/ |
| `infrastructure/` | application/, domain/ | api/ |
| `api/` | application/, infrastructure/, domain/ | — |
| `frontend/` | (HTTP client) | qualquer coisa Python |

---

## Guias por Módulo

Cada diretório tem seu próprio `AGENTS.md` com regras detalhadas:

| Módulo | Arquivo | Foco |
|--------|---------|------|
| API | [`api/AGENTS.md`](api/AGENTS.md) | FastAPI, rotas, schemas, auth JWT |
| Frontend | [`frontend/AGENTS.md`](frontend/AGENTS.md) | Next.js, React, Tailwind, shadcn/ui |
| Domain | [`domain/AGENTS.md`](domain/AGENTS.md) | Lógica pura, entidades, métricas |
| Application | [`application/AGENTS.md`](application/AGENTS.md) | Use cases, interfaces, aggregators |
| Infrastructure | [`infrastructure/AGENTS.md`](infrastructure/AGENTS.md) | PostgreSQL, exporters, API client |
| Tests | [`tests/AGENTS.md`](tests/AGENTS.md) | Pytest, fixtures, cobertura |
| Docs | [`docs/AGENTS.md`](docs/AGENTS.md) | Documentação do projeto |

---

## Tech Stack

| Componente | Tecnologia | Versão |
|------------|------------|--------|
| Backend | FastAPI + Uvicorn | 0.139.0 / 0.51.0 |
| DB | PostgreSQL (asyncpg) | 18.4 / 0.31.0 |
| ORM/Validation | Pydantic | 2.13.4 |
| Auth | python-jose + passlib | 3.5.0 / 1.7.4 |
| HTTP Client | httpx | 0.27.0 |
| Scheduler | APScheduler | 3.10.0 |
| Frontend | Next.js + React | 16.2.10 / 19.2.7 |
| TypeScript | TypeScript | 7.0.2 |
| Styling | Tailwind CSS + shadcn/ui | 4.3.3 / 4.13.0 |
| Charts | Recharts | 3.9.2 |
| Tables | TanStack Table | 8.21.3 |
| Forms | React Hook Form + Zod | 7.81.0 / 3.25.0 |
| Infra | Docker Compose + Cloudflare Tunnels | — |

---

## Comandos

### Backend
```bash
cd new_bird
pip install -e ".[dev]"
uvicorn api.main:app --reload --port 8000
pytest -v
ruff check . && ruff format .
```

### Frontend
```bash
cd new_bird/frontend
npm install
npm run dev        # → localhost:3000
npm run build
npm run lint
```

### Docker
```bash
cd new_bird
docker compose up -d       # PostgreSQL + API + Frontend
docker compose logs -f api
docker compose down
```

---

## Regras Críticas

1. **NUNCA** colocar lógica de negócio em `api/` ou `infrastructure/`
2. **NUNCA** importar de `infrastructure/` em `domain/`
3. **SEMPRE** usar DTOs (DashboardDTO) para transferir dados entre camadas
4. **SEMPRE** usar `async/await` para operações de banco e I/O
5. **SEMPRE** validar com Pydantic (backend) ou Zod (frontend)
6. **NUNCA** expor secrets no frontend — usar variáveis de ambiente
7. **SEMPRE** usar `response_model=` nas rotas FastAPI

---

## Status do Desenvolvimento

| Fase | Estado | Ref |
|------|--------|-----|
| Fase 0: Setup e Infraestrutura | ✅ Concluída | [CHECKLIST.md](docs/CHECKLIST.md) |
| Fase 1: Backend Core (domain + app + infra) | ✅ Concluída | [CHECKLIST.md](docs/CHECKLIST.md) |
| Fase 2: Backend API (endpoints) | ✅ Concluída | [CHECKLIST.md](docs/CHECKLIST.md) |
| Fase 3: Frontend Dashboard | ✅ Concluída | [CHECKLIST.md](docs/CHECKLIST.md) |
| Fase 4: Integração e Deploy | 🔲 Pendente | [CHECKLIST.md](docs/CHECKLIST.md) |

---

## Deploy

- **Docker Compose**: PostgreSQL + API + Frontend orquestrados
- **Cloudflare Tunnels**: exposição HTTPS sem nginx
  - `app.empresa.com` → Frontend (:3000)
  - `api.empresa.com` → API (:8000)
- Portas expostas apenas em `127.0.0.1` (acesso local via Tunnel)
