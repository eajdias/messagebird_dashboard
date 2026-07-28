# MessageBird Dashboard

Dashboard omnichannel para monitoramento de atendimento via [Bird](https://bird.com) (MessageBird) API. Suporte a **WhatsApp**, **Webchat**, **Facebook Messenger** e **Instagram Direct**.

---

## ✨ Funcionalidades

- **Dashboard interativo** — KPIs, evolução temporal (diário/semanal/mensal), cobertura de avaliações, distribuição ART
- **Visão executiva** — Heatmap de atendimentos, NPS, notas, motivos de contato, ocorrências, retornantes
- **BSC (Balanced Scorecard)** — Métricas configuráveis por departamento com pesos, níveis e penalidades
- **Sincronização automática** — Pipeline incremental/full com agendador (APScheduler) e 6 perfis configuráveis
- **Exportação de dados** — CSV, Excel, ZIP (OS em PDF), dashboard multi-sheet
- **Gerenciamento de usuários** — Roles admin/agente, alteração de senha
- **Responsivo** — Interface glassmorphism adaptada para desktop e mobile
- **Dark/Light mode**

---

## 🚀 Quick Start

Pré-requisitos: **Docker** + **Docker Compose**

```bash
git clone https://github.com/seu-usuario/messagebird_dashboard.git
cd messagebird_dashboard

# Copiar e configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas API keys do MessageBird

# Subir tudo
docker compose up -d
```

Acesse: **http://localhost:3050**

> O banco de dados é criado e migrado automaticamente na primeira execução.

---

## 📚 Documentação

| Documento | Conteúdo |
|-----------|----------|
| [STACK.md](docs/STACK.md) | Stack completa (versões, dependências) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura do projeto (camadas, decisões) |
| [DATABASE.md](docs/DATABASE.md) | Schema, migrations, índices |
| [API.md](docs/API.md) | Referência dos endpoints REST |
| [SYNC_PIPELINE.md](docs/SYNC_PIPELINE.md) | Pipeline de sincronização MessageBird → PostgreSQL |
| [REPORTS.md](docs/REPORTS.md) | Sistema de relatórios e exportação |
| [FRONTEND.md](docs/FRONTEND.md) | Arquitetura do frontend Next.js |
| [CONFIG.md](docs/CONFIG.md) | Variáveis de ambiente e configuração |
| [KPI_BSC.md](docs/KPI_BSC.md) | Métricas, BSC e sistema de pontuação |
| [TESTING.md](docs/TESTING.md) | Estratégia de testes |
| [ROADMAP.md](ROADMAP.md) | Tarefas pendentes para contribuidores |

---

## 🛠️ Stack

| Camada | Tecnologia |
|--------|-----------|
| **Backend** | Python 3.14, FastAPI, asyncpg, APScheduler |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind v4 |
| **Banco** | PostgreSQL 18 |
| **Gráficos** | Recharts, framer-motion |
| **Infra** | Docker, Docker Compose |

---

## 🏗️ Desenvolvimento Local

### Backend

```bash
# Criar virtualenv com uv
uv sync

# Rodar API
uvicorn api.main:app --reload --port 8000

# Testes
pytest

# Lint + format
ruff check .
ruff format .
```

### Frontend

```bash
cd frontend

# Instalar dependências
npm ci

# Dev server (Turbopack)
npm run dev

# Typecheck
npm run type-check

# Lint
npm run lint
```

---

## 📁 Estrutura

```
├── api/                    # FastAPI — rotas, auth, schemas, middleware
│   └── routes/             # admin, auth, conversations, dashboard, reports
├── application/            # Casos de uso e serviços
│   ├── use_cases/          # SyncDatabase, GenerateReport
│   └── services/           # ReportAggregator, BSC, ExportService
├── domain/                 # Entidades, constantes, métricas
│   └── services/           # MetricsCalculator
├── infrastructure/         # PostgreSQL, HTTP client, sync, exporters
│   ├── database/           # Pool, queries, migrations
│   ├── exporters/          # CSV, XLSX, PDF, Excel multi-sheet
│   ├── sync/               # Pipeline contact→conversation→message
│   └── config/             # Sync profiles, YAML loaders
├── frontend/               # Next.js 16 App Router
│   ├── app/(dashboard)/    # Páginas: dashboard, conversas, relatórios, etc.
│   ├── components/         # ui/, layout/, dashboard/, settings/
│   ├── hooks/              # useAuth, useDashboard, useExecutive, etc.
│   └── lib/                # api.ts (axios), utils.ts
├── docs/                   # Documentação
├── business_bsc.yaml.example   # Template de métricas BSC
├── business_config.yaml.example # Template de configuração
├── docker-compose.yml
└── ROADMAP.md              # Tarefas para contribuidores
```

---

## 🤝 Contribuindo

- Use **Conventional Commits** (`feat:`, `fix:`, `docs:`, `refactor:`)
- Rode `lint` + `typecheck` + `tests` antes de commitar
- Código novo precisa de testes
- Veja [ROADMAP.md](ROADMAP.md) para tarefas de documentação pendentes

---

## 📄 Licença

MIT
