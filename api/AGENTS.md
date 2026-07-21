# api/ — FastAPI Backend
> **Mandato:** Este diretório contém a camada de apresentação HTTP. Apenas orquestração e roteamento — NUNCA lógica de negócio.

---

## 🏗️ Estrutura Atual (Atualizado Julho 2026)

Intermediário entre Application Layer e MessageBird API. Contém:

- **3 Complexos Domínios**: Admin, Dashboard, Conversations
- **15 Rotas Implementadas**: Todas com Pydantic Schemas validadas
- **Integração com Infrastructure**: Apenas via interfaces definidas
- **Dependência Injetável**: Todos os repositórios são passados como dependências

## 📂 Estrutura

```
api/
├── __init__.py
├── main.py              # App factory, startup/shutdown events
├── dependencies.py      # Dependency injection container
├── auth.py              # JWT authentication logic
├── middleware.py         # CORS, logging, error handling
├── schemas/             # Pydantic models (request/response)
│   ├── __init__.py
│   ├── auth.py          # LoginRequest, TokenResponse, UserResponse
│   ├── dashboard.py     # DashboardResponse, KPIResponse, etc.
│   ├── conversations.py # ConversationList, ConversationDetail
│   └── reports.py       # ReportRequest, ExportResponse
└── routes/              # Endpoint routers (implementados)
    ├── __init__.py
    ├── auth.py          # POST /auth/login, POST /auth/register, GET /auth/me
    ├── dashboard.py     # GET /dashboard/summary, /bsc, /kpis, /evolution
    ├── conversations.py # GET /conversations, POST /conversations/{id}
    ├── reports.py       # POST /reports/generate, GET /reports/{id}/download
    └── admin.py         # GET /admin/sync/status, POST /admin/sync/trigger, GET /admin/agents
```

## 🔌 Patrones Técnicos

### 1. Injeção de Dependência (Dependency Injection)
- Padrão rigoroso: repositórios passados via `async def get_xxx()`
- Todas as dependências cabelas evitam imports diretos de infrastructure
- Usa AsyncPG pool recompartilhado via context managers

### 2. Schema Validation Universa
- Cada rota tem template de resposta documentado
- Schemas incluem exemplos de request/response
- Uso extensivo de `@router.get(..., response_model=XXXResponse)`

### 3. Autenticação Baseada em JWT
- Middleware centralizado verifica tokens nas rotas protegidas
- Roles definidos em `domain/constants.py` para controle de permissão
- Expiração configurável via `.env` (`JWT_EXPIRATION_MINUTES`)

## 📡 Endpoints Ativos (15+ Implementados)

### Auth
- `POST /auth/login` → `TokenResponse` | Autenticação
- `POST /auth/register` → `UserResponse` | Criação de usuário admin
- `GET /auth/me` → `UserResponse` | Dados do usuário logado

### Dashboard
- `GET /dashboard/summary` → `DashboardSummaryResponse` | KPIs gerais
- `GET /dashboard/bsc` → `BSCResponse` | Requisitos BSC detalhados
- `GET /dashboard/kpis` → `KPIResponse` | Requisitos KPIs detalhados
- `GET /dashboard/evolution` → `EvolutionResponse` | Evolução mensal detalhada
- `GET /dashboard/agents` → `AgentRankingResponse` | Ranking de agentes
- `GET /dashboard/channels` → `ChannelResponse` | Métricas por canal

### Conversations
- `GET /conversations` → `ConversationListResponse` | Lista filtrada (11 parâmetros)
- `GET /conversations/{id}` → `ConversationDetailResponse` | Detalhes completos
- `GET /conversations/{id}/messages` → `ConversationMessagesResponse` | Mensagens da conversa

### Reports
- `POST /reports/generate` → `GenerateReportResponse` | Gera relatório sob demanda
- `GET /reports/{id}/download` → `DownloadReportResponse` | Download do relatório
- `GET /reports/available` → `AvailableReportsResponse` | Lista relatórios disponíveis

### Admin
- `GET /admin/sync/status` → `SyncStatusResponse` | Status da última sync
- `POST /admin/sync/trigger` → `SyncTriggerResponse` | Disparar sync manual
- `GET /admin/sync/profile` → `SyncProfileResponse` | Procurar perfis MessageBird
- `GET /admin/agents` → `AgentListResponse` | Dados completos de agentes
- `GET /admin/departments` → `DepartmentListResponse` | Departamentos suportados
- `GET /admin/health` → `HealthResponse` | Verificação de saúde da API

---

## 📐 Regras Novas

### Rotas Dinâmicas
- Tudo em `(prefixo)/{id}/...` para dados estruturados
- Usar `@router.get(..., response_model=XXXResponse)` para validação de resposta

### Segurança
- **Todas exceto `/auth/login` exigem JWT**
- Middleware verifica `/auth/me` para permissão admin obrigatório
- Roles definidos em `application/interfaces/decision_engine.py`

### Documentação Automatizada
- Swagger UI em `/docs` gerado automaticamente
- Genera OpenAPI 3.0 spec completa com exemplos de request/response
- Todas as respostas incluem `detail` opcional e código definido implícitos

---

## 🚨 Erros Comuns Atualizados

1. **CORS Configuration** → Verificar `CORS_ORIGINS` no `.env` e em `middleware.py`
2. **Schema Validation Failure** → Request body não confere com o schema Pydantic
3. **JWT Expired** → Excluir token com `master_token` ausente ou expirado
4. **Query Parameter Issues** → Filtros SQL não usam padrão olhar para `createdAfter`
5. **Database Connection Error** → Verificar pool connections no `dependencies.py`

---

## 💡 Diretrizes para Agents LLM

1. **Nunca** assumir lógica de negócio em templates
2. **Sempre** verificar respostas `response_model=` antes de responder
3. **Priorizar** endpoints com maior uso: `/dashboard/summary`, `/reports/generate`
4. **Verificar** se novo endpoint já existe em `/routes/ antes de propor**
5. **Consultar** `api/schem*` antes de gerar modelos de resposta
6. **Documentar** novos endpoints no OpenAPI schema automaticamente

---

## 🔧 Comandos Relevantes para Agents

```bash
# Listar endpoints implementados
curl -s http://localhost:8050/api/v1/dashboard/summary | jq '.'

# Testar autenticação válida
curl -X POST http://localhost:8050/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresa.com", "password":"senha", "client_secret":"..."}' \
  -o token.json && cat token.json

# Verificar status da sync
curl -s http://localhost:8050/admin/sync/status | jq '.'
```