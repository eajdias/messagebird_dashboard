# Stack Tecnológico

> Stack completo do MessageBird Dashboard. Consulte este arquivo quando precisar saber versões, frameworks ou configurações específicas.

## Backend (Python)

| Categoria | Tecnologia | Versão |
|-----------|-----------|--------|
| Linguagem | Python | >=3.14 |
| Gerenciador de pacotes | `uv` (recomendado) / pip | — |
| Build system | Hatchling | — |
| Web framework | FastAPI | >=0.139.0 |
| ASGI server | Uvicorn | >=0.51.0 |
| Validação | Pydantic v2 | >=2.13.4 |
| Autenticação | python-jose (JWT HS256) + passlib (bcrypt) | — |
| Database driver | asyncpg | >=0.31.0 |
| HTTP client | httpx (AsyncClient) | >=0.27.0 |
| Scheduler | APScheduler | >=3.10.0 |
| CLI | rich | >=13.7.0 |
| Linter | Ruff | >=0.8.0 |
| Type checker | mypy (strict mode) | >=1.13.0 |
| Test runner | Pytest | >=8.0.0 |
| HTTP mocking | respx | >=0.23.1 |

## Frontend (TypeScript/React)

| Categoria | Tecnologia | Versão |
|-----------|-----------|--------|
| Framework | Next.js | 16.2.10 |
| Linguagem | TypeScript (strict) | ~5.8 |
| Estilização | Tailwind CSS | 4.3.3 |
| UI Components | Radix UI (Dialog, Popover) | — |
| Forms | react-hook-form + zod | 7.81 / 3.25 |
| Tabelas | @tanstack/react-table | 8.21.3 |
| Gráficos | Recharts | 3.9.2 |
| Animações | framer-motion | 12.42.2 |
| Ícones | lucide-react | 0.460 |
| HTTP client | axios | ^1.7 |
| Tema | next-themes | ^0.4 |
| Notificações | sonner | ^2.0.7 |
| Linter | ESLint (eslint-config-next) | ^9.0 |

## DevOps

| Categoria | Tecnologia |
|-----------|-----------|
| Containerização | Docker (multi-stage) |
| Orquestração | docker-compose (3 serviços) |
| Banco de dados | PostgreSQL 18 Alpine |
| Portas | API: 8050, Frontend: 3050, PG: 5432 |

## Dependências do Projeto (pyproject.toml)

O backend é definido como pacote `mbird-web` v2.0.0. As dependências principais estão em `[project] dependencies`, as de desenvolvimento em `[project.optional-dependencies] dev`.

Estrutura de pacotes para build:
```
packages = ["api/", "domain/", "application/", "infrastructure/"]
```

## Configurações de Ferramentas

### Ruff (lint)
- line-length: 120
- target-version: py314
- Regras: E, F, I, N, W, UP, B, SIM
- Ignorado: B008

### MyPy
- strict mode ativado
- python-version: 3.14

### Pytest
- asyncio_mode = auto
- testpaths = ["tests"]
- Marker customizado: `integration` (pular com `-m 'not integration'`)
