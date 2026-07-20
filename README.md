# new_bird — Omnichannel Reporting Dashboard

Dashboard web para relatórios omnichannel Bird API.

**Backend:** FastAPI (Python 3.14) | **Frontend:** Next.js 16 (TypeScript 7.0) | **DB:** PostgreSQL 18

## Quick Start

```bash
# 1. Clone e entre no diretório
git clone <repo-url> && cd new_bird

# 2. Configure o ambiente
cp .env.example .env
# Edite .env com suas credenciais

# 3. Suba com Docker Compose
docker compose up -d

# 4. Acesse
# Frontend: http://localhost:3050
# API:      http://localhost:8050/docs
```

## Desenvolvimento

### Backend
```bash
pip install -e ".[dev]"
uvicorn api.main:app --reload --port 8000
pytest -v
ruff check . && ruff format .
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Estrutura

```
new_bird/
├── api/            # FastAPI — endpoints REST, auth JWT
├── frontend/       # Next.js 16 — dashboard interativo
├── domain/         # Lógica pura de negócio
├── application/    # Orquestração e use cases
├── infrastructure/ # PostgreSQL, exporters, API client
├── tests/          # Pytest
├── alembic/        # Migrations PostgreSQL
└── docs/           # Documentação
```

## Tech Stack

| Componente | Tecnologia |
|------------|------------|
| Backend | FastAPI 0.139.0 + Uvicorn |
| DB | PostgreSQL 18 + asyncpg |
| Auth | JWT (python-jose + passlib) |
| Frontend | Next.js 16 + React 19 + TypeScript 7.0 |
| Styling | Tailwind CSS 4 + shadcn/ui |
| Charts | Recharts |
| Infra | Docker Compose + Cloudflare Tunnels |

## Deploy

- **Docker Compose**: PostgreSQL + API + Frontend
- **Cloudflare Tunnels**: HTTPS sem nginx
  - `zsc-sac.eajdias.com` → Frontend (:3050)
  - `zsc-sac-api.eajdias.com` → API (:8050)

## License

MIT
