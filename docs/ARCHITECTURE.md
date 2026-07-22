# Arquitetura

> Visão geral da arquitetura do MessageBird Dashboard: camadas, fluxo de dados, padrões.

## Visão Geral

O projeto segue **Clean Architecture / DDD-like** com 4 camadas principais:

```
┌──────────────────────────────────────────────────────────┐
│                      api/ (Interface Adapters)            │
│  FastAPI routes, Pydantic schemas, auth, middleware       │
├──────────────────────────────────────────────────────────┤
│                  application/ (Application Services)      │
│  Use cases (sync, report), services (aggregation), ABCs   │
├──────────────────────────────────────────────────────────┤
│                    domain/ (Enterprise Logic)              │
│  Entities, metrics calculators, constants, strategies     │
├──────────────────────────────────────────────────────────┤
│              infrastructure/ (Frameworks & Drivers)        │
│  PostgreSQL, MessageBird HTTP client, sync, exporters     │
└──────────────────────────────────────────────────────────┘
```

**Regra de dependência:** As dependências apontam para dentro: `api` → `application` → `domain`. A `infrastructure` implementa interfaces definidas em `application/interfaces/`.

## Fluxo de Dados Principal

```
MessageBird API ──▶ Sync Pipeline ──▶ PostgreSQL ──▶ FastAPI ──▶ Next.js Dashboard
  (Bird)          (infrastructure/     (database)     (api/)      (frontend/)
                    sync/)
```

1. **Sync Pipeline** (`infrastructure/sync/`) busca dados da API MessageBird
2. Dados são armazenados no PostgreSQL via `asyncpg`
3. **FastAPI** (`api/routes/`) consulta o banco via `PostgresReportRepository`
4. **ReportAggregator** processa e agrega as métricas
5. **Frontend** Next.js consome a API REST e exibe no dashboard

## Camada API (`api/`)

- **Rotas:** auth, dashboard, conversations, reports, admin (prefixo `/api/v1/`)
- **Autenticação:** JWT bearer tokens (HS256), 8h de expiração
- **Middleware:** CORS configurável + logging de requests
- **Validação:** Pydantic v2 schemas
- **DI:** Repositórios injetados via `Depends`
- **Scheduler:** APScheduler in-process para sincronização automática

## Camada de Domínio (`domain/`)

- **Entities:** `RawConversationData`, `ProcessedReportData` (dataclasses)
- **Metrics:** `ARTCalculator`, `FRTCalculator`, `DurationCalculator`, `MetricsCalculator`
- **Constants:** Mapas de departamento/motivo/ocorrência, configurações KPI/BSC
- **Strategies:** Strategy pattern para cálculo de métricas
- **Logic:** Timezone handling (offset -3 Brasília), duração, detecção de reabertura

## Camada de Aplicação (`application/`)

- **Use Cases:** `SyncDatabaseUseCase`, `GenerateReportUseCase`, `DataQualityReportUseCase`
- **Services:** `ReportAggregator` (processamento + agregação), serviços de auditoria
- **Interfaces:** `ReportRepository` ABC (17 métodos abstratos), `ReportExporter` ABC

## Camada de Infraestrutura (`infrastructure/`)

- **Database:** PostgreSQL com asyncpg, pool de conexões, queries centralizadas em `queries_pg.py`
- **API Client:** MessageBird HTTP client com retry e rate limiting
- **Sync:** Pipeline contact→conversation→message com modos incremental/full/backfill
- **Exporters:** Excel (xlsxwriter), PDF (fpdf2), Markdown
- **Config:** Loader para `business_config.yaml` e `business_bsc.yaml`

## Decisões Arquiteturais Importantes

### Materialized View
Uma view materializada `vw_survey_data` com 4 tabelas JOIN é usada para performance das queries de dashboard. É atualizada concorrentemente após cada sync.

### Cache de Métricas
Métricas computadas são cacheadas em disco (`reports/_metrics_cache.json`) para evitar recálculo em relatórios recorrentes.

### Sincronização
- Perfis configuráveis: debug (15min), short (30min), hourly, daily, weekly, monthly
- APScheduler roda in-process com a FastAPI
- Erros de sync são registrados na tabela `sync_errors` para debugging

### Relatórios
- Gerados sob demanda via API e salvos em `reports/{report_id}/`
- Formatos: Excel (principal), PDF (ordens de serviço), Markdown (resumos)
- Manifesto em JSON (`reports/manifest.json`) rastreia relatórios gerados