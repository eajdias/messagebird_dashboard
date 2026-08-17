# API REST

> Rotas, autenticação, schemas. Prefixo base: `/api/v1`.

## Autenticação

- **Método:** JWT Bearer Token (HS256)
- **Login:** `POST /api/v1/auth/login` (credenciais → token)
- **Expiração:** 8 horas (configurável via `JWT_EXPIRATION_MINUTES`)
- **Proteção:** Rotas protegidas usam `Depends(get_current_user)`
- **Hash de senha:** bcrypt via passlib

## Endpoints

### Auth (`/api/v1/auth`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| POST | `/login` | Não | Login (retorna JWT token) |

### Dashboard (`/api/v1/dashboard`)

| Método | Rota | Descrição | Parâmetros |
|--------|------|-----------|-----------|
| GET | `/summary` | Métricas resumidas (total chats, NPS, ART, SLA, msgs, contatos) | start_date, end_date (YYYY-MM-DD) |
| GET | `/bsc` | Tabela BSC completa (header, data_t1, data_t2, kpi_config) | start_date, end_date |
| GET | `/kpis` | Configuração de KPIs por departamento | department |
| GET | `/evolution` | Evolução mensal (NPS, ART, SLA, rating) | months (1-24, default 12) |
| GET | `/agents` | Ranking de agentes (chats, NPS, ART, SLA) | start_date, end_date |
| GET | `/channels` | Distribuição por canal (chats, msgs, NPS) | start_date, end_date |

### Conversations (`/api/v1/conversations`)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Lista de conversas |
| GET | `/{id}` | Detalhe da conversa com mensagens |

### Reports (`/api/v1/reports`)

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/generate` | Gera novo relatório (year, month, type, group) |
| GET | `/available` | Lista relatórios disponíveis |
| GET | `/{report_id}/download` | URL para download |
| GET | `/{report_id}/file/{path}` | Servir arquivo do relatório |

### Admin (`/api/v1/admin`)

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/health` | Não | Health check (status + versão) |
| GET | `/sync/status` | Sim | Status da última sincronização |
| POST | `/sync/trigger` | Sim | Disparar sync manual |
| GET | `/agents` | Sim | Listar agentes |
| GET | `/departments` | Sim | Listar departamentos |
| GET | `/sync/profile` | Sim | Perfil de sync ativo |
| GET | `/scheduler/status` | Sim | Status do scheduler |
| POST | `/scheduler/start` | Sim | Iniciar scheduler |
| POST | `/scheduler/stop` | Sim | Parar scheduler |

## Schemas (Pydantic)

Os schemas estão em `api/schemas/`:

| Arquivo | Schemas |
|---------|---------|
| `_base.py` | StatusResponse, list_response factory |
| `auth.py` | LoginRequest, TokenResponse |
| `dashboard.py` | DashboardSummary, BSCResponse, KPIResponse, EvolutionResponse, AgentRanking, ChannelResponse |
| `conversations.py` | Conversation list/detail |
| `reports.py` | GenerateReport, AvailableReports, DownloadReport |
| `admin.py` | Health, Sync, Scheduler, Agent, Department |

## Dependências (FastAPI DI)

- `get_repository()` → Injeta `PostgresReportRepository`
- `get_pool()` → Injeta pool asyncpg
- `get_current_user()` → Validates JWT e retorna user dict
- `get_reports_dir()` → Diretório de relatórios configurado

## Middleware

- **CORS:** Configurável via `CORS_ORIGINS` (ex: `http://localhost:3000`)
- **Logging:** Request logging com tempo de resposta
