# Banco de Dados

> Schema PostgreSQL, migrations, queries. Todas as queries SQL estão centralizadas em `infrastructure/database/queries_pg.py`.

## Estrutura

### Tabelas

#### contacts (`cnts_` prefix)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| cnts_id | SERIAL PK | ID interno |
| cnts_name | VARCHAR(255) | Nome do contato |
| cnts_phone | VARCHAR(50) | Telefone |
| cnts_bird | VARCHAR(255) UNIQUE | ID do contato na MessageBird |
| cnts_custom1-4 | VARCHAR(255) | Campos customizados |
| cnts_created/updated | TIMESTAMP | Controle de tempo |

#### agents (`agnt_` prefix)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| agnt_id | SERIAL PK | ID interno |
| agnt_name | VARCHAR(255) | Nome do agente |
| agnt_bird | VARCHAR(255) UNIQUE | ID do agente na MessageBird |
| agnt_grp | VARCHAR(100) | Grupo/Departamento |
| cnts_created/updated | TIMESTAMP | Controle de tempo |

#### conversations (`cnvs_` prefix)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| cnvs_id | SERIAL PK | ID interno |
| cnvs_msgcount | INTEGER | Total de mensagens |
| cnvs_cnts | FK → contacts | Contato |
| cnvs_agnt | FK → agents | Agente responsável |
| cnvs_status | VARCHAR(50) | Status (open/closed) |
| cnvs_channel | VARCHAR(255) | Canal (WhatsApp, Web, etc.) |
| cnvs_bird | VARCHAR(255) UNIQUE | ID na MessageBird |
| cnvs_created/updated/last | TIMESTAMP | Tempos |
| cnvs_lang | INTEGER | Idioma |
| cnvs_software | VARCHAR(255) | Software relacionado |
| cnvs_tax_id | VARCHAR(50) | CNPF/CNPJ |
| cnvs_dept | INTEGER | Departamento |
| cnvs_rating_agent | INTEGER | Nota do agente (1-5) |
| cnvs_rating_nps | INTEGER | NPS (1-10) |
| cnvs_reopened_count | INTEGER | Reaberturas |
| cnvs_contact_reason | INTEGER | Motivo do contato |
| cnvs_occurrence | INTEGER | Ocorrência |
| cnvs_description | TEXT | Descrição |

#### messages (`msgs_` prefix)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| msgs_id | SERIAL PK | ID interno |
| msgs_cnvs | FK → conversations | Conversa |
| msgs_agnt | FK → agents | Agente |
| msgs_direction | VARCHAR(20) | sent/received |
| msgs_status | VARCHAR(50) | Status |
| msgs_type | VARCHAR(50) | Tipo |
| msgs_content | TEXT | Conteúdo |
| msgs_bird | VARCHAR(255) UNIQUE | ID na MessageBird |
| msgs_created/updated | TIMESTAMP | Tempos |

#### sync (`sync_` prefix)
Histórico de sincronização: recurso, timestamp, duração, records, cursor, offset.

#### sync_errors (`err_` prefix)
Log de erros: resource, código, mensagem, contexto, timestamp, retry_count, resolved_at.

### Materialized View: `vw_survey_data`
JOIN de 4 tabelas (messages + conversations + agents × 2 + contacts) com índice único para refresh concorrente. Usada por todas as queries de dashboard.

## Migrations

As migrations são arquivos SQL puros em `infrastructure/database/migrations/`:

| Arquivo | Descrição |
|---------|-----------|
| `001_initial.sql` | Schema inicial (todas as tabelas + índices) |
| `002_materialized_view.sql` | Cria vw_survey_data |
| `003_cleanup_unused_columns.sql` | Remove colunas não utilizadas |
| `004_add_agnt_grp_to_view.sql` | Recria MV com agnt_grp |

As migrations são aplicadas automaticamente na inicialização da API (`_init_schema` em `api/main.py`), na ordem numérica, de forma idempotente (IF NOT EXISTS).

## Índices Importantes

- `idx_messages_cnvs_created` — composto (cnvs_id, created) para queries de mensagens por conversa
- `idx_conversations_created` — para filtros por data no dashboard
- `idx_sync_resource_created` — para consultar histórico de sync
- Todos os `_bird` têm índice UNIQUE

## Padrões de Query

- SQL usa placeholders `$1, $2` (asyncpg parameterized)
- Nomes de coluna snake_case com prefixo da tabela
- Todas as queries em `queries_pg.py`, nunca inline nos repositories

## Conexão

- Pool de conexões gerenciado por `PostgresPool` (asyncpg)
- URL: `postgresql+asyncpg://user:pass@host:port/dbname`
- Pool é iniciado no lifespan da FastAPI e parado no shutdown