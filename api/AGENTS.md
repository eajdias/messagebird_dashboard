# api/ — FastAPI Backend

> **Mandato:** Este diretório contém a camada de apresentação HTTP. Apenas orquestração e roteamento — NUNCA lógica de negócio.

---

## 🏗️ Estrutura

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
│   ├── dashboard.py     # DashboardResponse, KPIResponse
│   ├── conversations.py # ConversationList, ConversationDetail
│   └── reports.py       # ReportRequest, ExportResponse
└── routes/              # Endpoint routers
    ├── __init__.py
    ├── auth.py          # POST /auth/login, /auth/register
    ├── dashboard.py     # GET /dashboard/summary, /bsc, /kpis
    ├── conversations.py # GET /conversations, /conversations/{id}
    ├── reports.py       # POST /reports/generate, GET /download
    └── admin.py         # GET /admin/sync/status, POST /trigger
```

---

## 📐 Regras

### Roteamento
- Usar `APIRouter` com prefixo: `router = APIRouter(prefix="/api/v1/dashboard")`
- Agrupar endpoints por domínio (dashboard, conversations, reports, admin)
- Todas as rotas exceto `/auth/login` requerem JWT

### Schemas (Pydantic)
- Todo request body deve ter um schema Pydantic correspondente
- Todo response deve ter um schema Pydantic correspondente
- Usar `response_model=` no decorator da rota
- Nunca retornar objetos do banco diretamente

### Dependency Injection
- Usar `dependencies.py` para injetar repositórios e services
- Pattern:
```python
async def get_repository() -> ReportRepository:
    db = get_database()
    return PostgresReportRepository(db)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    return verify_token(token)
```

### Autenticação
- JWT com `python-jose`
- Token no header: `Authorization: Bearer <token>`
- Rotas admin requerem role `admin`
- Expiração: 8 horas (configurável via `JWT_EXPIRATION_MINUTES`)

### Sync Scheduler
- APScheduler roda dentro do FastAPI (startup event)
- Configuração em `main.py` via `lifespan`
- Jobs: incremental (15 min), full (diário 3:00 AM)

---

## 🔧 Comandos

```bash
# Desenvolvimento
uvicorn api.main:app --reload --port 8000

# Produção
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4

# Testar endpoints
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@empresa.com", "password": "senha"}'
```

---

## 🚨 Erros Comuns

1. **CORS error**: Verificar `CORS_ORIGINS` no `.env` e em `middleware.py`
2. **401 Unauthorized**: Token expirado ou inválido
3. **422 Unprocessable Entity**: Request body não confere com o schema Pydantic
4. **500 Internal Server Error**: Verificar logs do FastAPI
