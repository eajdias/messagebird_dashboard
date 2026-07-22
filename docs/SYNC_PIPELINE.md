# Pipeline de Sincronização

> Como os dados são sincronizados da MessageBird API para o PostgreSQL.

## Visão Geral

O pipeline sincroniza dados da **MessageBird (Bird)** API para o PostgreSQL. A orquestração é feita pelo `PgSyncManager` em `infrastructure/sync/pg_sync_engine.py`.

## Fluxo de Sincronização

```
MessageBird API ──▶ 1. Contacts ──▶ 2. Conversations ──▶ 3. Messages ──▶ 4. Surveys
                          │                │                    │               │
                          ▼                ▼                    ▼               ▼
                      PostgreSQL ◀─────────────────────────────────────────────┘
                          │
                          ▼
                    Materialized View (vw_survey_data) refresh
```

## Modos de Sincronização

O pipeline suporta múltiplos modos:

| Modo | Flag CLI | Descrição |
|------|----------|-----------|
| **Estrutural** | (default) | Sincroniza contacts + conversations (sem mensagens) |
| **Incremental** | `--messages-days N` | Sync estrutural + mensagens dos últimos N dias |
| **Full** | `--full` | Sync completo de contacts + conversations |
| **Full+Messages** | `--full-messages` | Full sync + **todas** as mensagens |
| **Mensal** | `--year Y --month M` | Sync de conversas e mensagens de um mês específico |
| **Hoje** | (API) | Sync de contatos + conversas + mensagens do dia atual |
| **Backfill Surveys** | `--backfill-surveys` | Re-extrair NPS e avaliações de surveys |

## Perfis de Agendamento

Perfis configurados em `infrastructure/config/sync_profiles.py`:

| Perfil | Intervalo Incremental | Full Sync |
|--------|----------------------|-----------|
| debug | 15 min | A cada hora |
| short | 30 min | A cada 2 horas |
| hourly | 60 min | 1x ao dia |
| daily | — | 1x ao dia |
| weekly | — | 1x por semana |
| monthly | — | 1x por mês |

O perfil ativo é definido pela env var `SYNC_PROFILE` (default: daily).

## CLI (main.py)

```bash
# Sync estrutural (contacts + conversations)
python main.py sync

# Sync com mensagens dos últimos 7 dias
python main.py sync --messages-days 7

# Full sync completo
python main.py sync --full --full-messages

# Sync de um mês específico
python main.py sync --year 2026 --month 6

# Backfill de surveys
python main.py sync --backfill-surveys
```

## API de Sync

O scheduler APScheduler roda in-process com a FastAPI:

- **Auto-início:** Se `SYNC_ENABLED=true` (default), o scheduler inicia automático no lifespan
- **Controle via API:** `POST /api/v1/admin/scheduler/start|stop`
- **Trigger manual:** `POST /api/v1/admin/sync/trigger`

## Tratamento de Erros

- Erros são salvos na tabela `sync_errors` com código, mensagem, contexto e contagem de retry
- Sync de contacts pula se já foi feito recentemente (`should_skip`)
- Timeout configurável via `MESSAGEBIRD_HTTP_TIMEOUT` (default: 30s)
- Rate limiting: máximo 10 requests/segundo

## Cache

- `PgSyncManager` mantém caches em memória de agents e contacts conhecidos
- Caches são populados no início de cada sync (`load_caches`)
- Novo agents são registrados automaticamente (`seed_known_agents`)
