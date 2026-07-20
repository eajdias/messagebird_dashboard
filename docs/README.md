# MBird Dashboard — Omnichannel Reporting

Dashboard web para relatórios omnichannel da plataforma Bird API.

## Stack

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| Backend | FastAPI + Uvicorn | 0.139.0 / 0.51.0 |
| DB | PostgreSQL (asyncpg) | 18.4 / 0.31.0 |
| Frontend | Next.js + React | 16.2.10 / 19.2.7 |
| TypeScript | TypeScript | 5.8.x |
| Styling | Tailwind CSS + shadcn/ui | 4.3.3 |
| Charts | Recharts | 3.9.2 |
| Auth | python-jose + passlib | 3.5.0 / 1.7.4 |

## Pré-requisitos

- Python 3.14+
- Node.js 20+
- PostgreSQL 18+

## Setup Rápido

### 1. Clone e instale dependências

```bash
git clone <repo-url>
cd messagebird_dashboard

# Backend
pip install -e ".[dev]"

# Frontend
cd frontend
npm install
cd ..
```

### 2. Configure variáveis de ambiente

```bash
cp .env.example .env
# Edite .env com suas credenciais
```

Variáveis principais:
- `DATABASE_URL` — URL de conexão PostgreSQL
- `BIRD_API_KEY` — Chave da API Bird
- `JWT_SECRET` — Chave para assinatura JWT
- `NEXT_PUBLIC_API_URL` — URL da API para o frontend

### 3. Inicie os serviços

**Docker (recomendado):**
```bash
docker compose up -d
```

**Manual:**
```bash
# PostgreSQL (via Docker ou local)
docker compose up -d postgres

# Backend
uvicorn api.main:app --reload --port 8000

# Frontend (em outro terminal)
cd frontend
npm run dev
```

### 4. Acesse

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/api/v1/admin/health |

## Credenciais Padrão

| Email | Senha | Role |
|-------|-------|------|
| admin@empresa.com | admin123 | admin |

> **TODO:** Implementar lookup no banco de dados.

## Comandos Úteis

### Backend
```bash
# Lint
ruff check . && ruff format .

# Testes
pytest -v

# Criar migração
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend
```bash
cd frontend

# Dev server (Turbopack)
npm run dev

# Build produção
npm run build

# Lint
npm run lint

# Type check
npm run type-check
```

## Estrutura do Projeto

```
messagebird_dashboard/
├── api/                    # FastAPI endpoints, auth, schemas
├── frontend/               # Next.js 16 dashboard
├── domain/                 # Lógica de negócio pura
├── application/            # Use cases e interfaces
├── infrastructure/         # PostgreSQL, exporters, API client
├── tests/                  # Pytest
├── docs/                   # Documentação
├── business_config.yaml    # Mapas de negócio
├── business_bsc.yaml       # KPIs e thresholds
├── docker-compose.yml      # PostgreSQL + API + Frontend
└── .env.example            # Template de variáveis
```

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| [API.md](API.md) | Todos os 20 endpoints documentados |
| [FRONTEND.md](FRONTEND.md) | Arquitetura, componentes, páginas |
| [DATABASE.md](DATABASE.md) | Schema PostgreSQL, migrations, queries |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Clean Architecture, fluxo de dependências |
