# MessageBird Dashboard

Dashboard omnichannel para monitoramento de campanhas SMS/voice e atendimento via MessageBird (Bird) API. Suporta WhatsApp, Webchat, Facebook Messenger e Instagram Direct.

## Stack
- **Backend:** Python 3.14, FastAPI, asyncpg, APScheduler
- **Frontend:** Next.js 16, Tailwind v4, Recharts, framer-motion
- **Database:** PostgreSQL 18
- **Package manager (backend):** `uv` | **(frontend):** `npm`

## Comandos Essenciais
- Dev API: `uvicorn api.main:app --reload --port 8000`
- Dev frontend: `npm run dev` (na pasta `frontend/`)
- Test: `pytest`
- Lint: `ruff check .`
- Format: `ruff format .`
- Typecheck backend: `mypy .`
- Typecheck frontend: `npm run type-check` (na pasta `frontend/`)
- Sync CLI: `python main.py sync [--full] [--messages-days N]`

## Documentação de Referência
- **Stack completo:** docs/STACK.md
- **Arquitetura:** docs/ARCHITECTURE.md
- **Banco de Dados:** docs/DATABASE.md
- **API REST:** docs/API.md
- **Pipeline de Sync:** docs/SYNC_PIPELINE.md
- **Relatórios:** docs/REPORTS.md
- **Frontend:** docs/FRONTEND.md
- **Testes:** docs/TESTING.md
- **Configuração:** docs/CONFIG.md
- **KPIs/BSC:** docs/KPI_BSC.md

## Skills
- sync-pipeline — Executar sincronização MessageBird → PostgreSQL
- generate-report — Gerar relatório mensal/anual com BSC

## Regras Importantes
- CRITICAL: Nunca edite `.env` ou arquivos `business_config.yaml`/`business_bsc.yaml` reais
- CRITICAL: Use Conventional Commits (feat:, fix:, docs:, refactor:, etc.)
- Sempre rode lint + typecheck + tests antes de finalizar uma tarefa
- Código novo precisa de testes correspondentes