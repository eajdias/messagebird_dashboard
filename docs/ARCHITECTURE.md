# Architecture — MBird Dashboard

Clean Architecture com separação estrita de dependências.

## Fluxo de Dependências

```
domain/ ← application/ ← api/ ← infrastructure/
   ↑           ↑                      ↑
   └───────────┴──────────────────────┘
   (nenhuma dependência deve "voltar")
```

| Camada | Pode importar | NÃO pode importar |
|--------|---------------|-------------------|
| `domain/` | stdlib Python apenas | application/, infrastructure/, api/ |
| `application/` | domain/ | infrastructure/, api/ |
| `infrastructure/` | application/, domain/ | api/ |
| `api/` | application/, infrastructure/, domain/ | — |
| `frontend/` | HTTP client (api.ts) | qualquer coisa Python |

## Camadas

### domain/ — Lógica Pura

Zero dependências externas. Contém:

- **entities/** — `RawConversationData`, `ProcessedReportData`
- **metrics/** — `ARTCalculator`, `FRTCalculator`, `DurationCalculator`
- **services/** — `MetricsCalculator` (NPS, SLA, scoring)
- **constants.py** — Mapas de negócio (DEPT_MAP, REASON_MAP, CHANNEL_MAP, LANG_MAP, AGENTS)
- **logic.py** — `parse_datetime`, `business_duration`, `reopen`

### application/ — Orchestration

Use cases e interfaces:

- **interfaces/** — `ReportRepository` (ABC), `ReportExporter` (ABC), `DashboardDTO`
- **services/** — `ReportAggregator`, `SubAggregators`, `AuditoriaContatosService`
- **use_cases/** — `GenerateReport`, `DataQualityReport`, `SyncDatabase`

### infrastructure/ — Detalhes Técnicos

- **api/** — `MessageBirdClient` (httpx), config
- **config/** — `config_loader.py` (YAML), `sync_profiles.py`
- **database/** — PostgreSQL (asyncpg), queries, connection pool, migrations
- **repositories/** — `PostgresReportRepository`
- **sync/** — `pg_sync_engine.py`, `sync_core.py`, `sync_contacts.py`, `sync_conversations.py`, `sync_messages.py`, `sync_surveys.py`
- **exporters/** — Excel, PDF, Markdown, metrics_cache, _bsc_writer

### api/ — HTTP Layer

FastAPI endpoints:

- **main.py** — App factory, lifespan (APScheduler)
- **auth.py** — JWT: create, verify, password hashing
- **routes/** — auth, dashboard, conversations, reports, admin
- **schemas/** — Pydantic models (request/response)
- **dependencies.py** — DI container (db session, repository)
- **middleware.py** — CORS config

### frontend/ — Next.js

App Router com route groups:

- **app/** — Pages (auth, dashboard)
- **components/** — UI primitives + dashboard widgets
- **hooks/** — useAuth, useDashboard, useConversations
- **lib/** — api.ts (Axios), utils.ts (cn)
- **types/** — TypeScript interfaces

## Data Flow

```
Bird API → MessageBirdClient (httpx)
         → SyncDatabaseUseCase
         → PostgresReportRepository (asyncpg)
         → Materialized View (vw_survey_data)
         → DashboardDTO
         → FastAPI endpoints
         → Next.js frontend
```

## Background Jobs

APScheduler no startup da API:

| Job | Frequência | Ação |
|-----|-----------|------|
| Sync automático | Configurável via `SYNC_PROFILE` (default: 60min) | Sync full structural contacts+conversations + messages (últimos `messages_days` dias) |
| Full + messages | Configurável via `SYNC_PROFILE` (default: 03:00 AM) | Sync full structural + todas as messages + surveys |

Todos os syncs são **full structural** (buscam todas as páginas de contacts e conversations ativas/arquivadas, sem lookback incremental). A diferença entre perfis inclui `incremental_minutes`, `full_sync_hour`, `messages_days`, e `backfill_surveys`.

Ambos terminam com `REFRESH MATERIALIZED VIEW CONCURRENTLY vw_survey_data`.

## Performance

- **Materialized View** reduz queries de ~900ms para ~50ms
- **Connection Pool** asyncpg: min=2, max=10
- **In-memory cache** no repository para `fetch_raw_data_range`
- **Índices** otimizados para filtros de data e JOINs
