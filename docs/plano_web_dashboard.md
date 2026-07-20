# Plano de Transformação: CLI → API + Dashboard Web

> **Status:** Aprovado
>
> **Objetivo:** Transformar o MessageBird Reporting Tool (atualmente CLI batch) em uma aplicação web completa com API REST e dashboard interativo estilo Power BI.

---

## Sumário Executivo

| Aspecto | Atual | Proposto |
|---------|-------|----------|
| **Interface** | Terminal CLI (`rich`) | Dashboard web (Next.js) |
| **Acesso** | Manual via SSH | HTTP/HTTPS autenticado |
| **Sync** | Manual (`python main.py sync`) | Automático a cada 15 min (APScheduler) |
| **Banco** | SQLite (WAL) | PostgreSQL (via Docker) |
| **Relatórios** | Excel/PDF no filesystem | Visualização web + download |
| **Multi-usuário** | Não | Sim (10-30 usuários) |
| **Deploy** | Local/VPS manual | Docker Compose + Cloudflare Tunnels |

---

## Arquitetura Final

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                       │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │  Frontend   │  │  Backend API │  │  PostgreSQL   │   │
│  │  Next.js    │  │  FastAPI     │  │  15           │   │
│  │  :3050      │  │  :8050       │  │  :5432        │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬──────┘   │
│         │                │                   │          │
│         │           ┌────┴───────┐           │          │
│         │           │Scheduler   │           │          │
│         │           │APScheduler │           │          │
│         │           │(sync 15min)│           │          │
│         │           └────┬───────┘           │          │
│         │                │                   │          │
│         └────────────────┼───────────────────┘          │
│                          │                              │
│                    ┌─────▼──────┐                       │
│                    │ MessageBird│                       │
│                    │    API     │                       │
│                    └────────────┘                       │
└─────────────────────────────────────────────────────────┘
                          │
                   Cloudflare Tunnel
                          │
            ┌─────────────┴─────────────┐
            │                           │
     app.empresa.com             api.empresa.com
      (Frontend)                    (API)
```

### Componentes

| Componente | Tecnologia | Versão | Função |
|------------|------------|--------|--------|
| **Backend API** | FastAPI (Python) | 0.139.0 | Endpoints REST, auth JWT, sync automático |
| **Frontend** | Next.js (TypeScript) | 16.2.10 | Dashboard interativo estilo Power BI |
| **React** | React | 19.2.7 | Biblioteca de UI |
| **Banco** | PostgreSQL (via Docker) | 18.4 | Migração do SQLite existente |
| **Infra** | Docker Compose | - | Orquestrar todos os serviços |
| **Exposição** | Cloudflare Tunnels | - | SSL/TLS e exposição dos serviços |

### Rotas Cloudflare Tunnel

| Subdomínio | Serviço | Porta |
|------------|---------|-------|
| `zsc-sac.eajdias.com` | Frontend Next.js | 3050 |
| `zsc-sac-api.eajdias.com` | Backend FastAPI | 8050 |

O frontend consome a API via `zsc-sac-api.eajdias.com/api/v1/...`. CORS configura o domínio permitido (`zsc-sac.eajdias.com`).

---

## Fases de Implementação

### Fase 1: Preparação (2-3 dias)

**Objetivo:** Adaptar o código existente para suportar PostgreSQL e preparar para API.

#### 1.1 Migrar de SQLite para PostgreSQL

- Criar `infrastructure/database/postgres_repository.py` implementando `ReportRepository`
- Criar `infrastructure/database/migrations/` com SQL do schema PostgreSQL
- Adaptar queries (sintaxe SQLite → PostgreSQL):
  - `?` → `$1`, `$2`, ...
  - `datetime()` → `NOW()`
  - `PRAGMA` → `SET`
- Usar `asyncpg` como driver async (substitui `aiosqlite`)
- Manter compatibilidade SQLite para testes locais

#### 1.2 Dockerizar o backend

- Criar `Dockerfile` para o Python backend
- Criar `docker-compose.yml` com:
  - Serviço `postgres` (imagem oficial + volume de dados)
  - Serviço `api` (FastAPI + APScheduler)
  - Serviço `frontend` (Next.js)

#### 1.3 Setup do FastAPI

Criar `api/` directory com:

```
api/
├── __init__.py
├── main.py              # App factory
├── dependencies.py      # DI container
├── auth.py              # JWT auth
├── middleware.py         # CORS, logging
├── schemas/             # Pydantic models
└── routes/              # Endpoint routers
```

#### 1.4 Endpoints de Autenticação

- `POST /auth/login` → retorna JWT token
- `POST /auth/register` → cria usuário (apenas admin)
- `GET /auth/me` → retorna usuário logado
- Middleware JWT nas rotas protegidas

---

### Fase 2: Backend API (5-7 dias)

**Objetivo:** Criar todos os endpoints REST necessários.

#### 2.1 Modelos Pydantic (request/response)

```python
# api/schemas/
├── auth.py          # LoginRequest, TokenResponse, UserResponse
├── dashboard.py     # DashboardResponse, KPIResponse, MetricsSummary
├── conversations.py # ConversationList, ConversationDetail, MessageList
├── reports.py       # ReportRequest, ExportResponse
└── sync.py          # SyncStatus, TriggerSyncRequest
```

#### 2.2 Endpoints do Dashboard (`/api/v1/dashboard`)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/dashboard/summary` | GET | Métricas gerais do período (volume, NPS, FRT, ART) |
| `/dashboard/bsc` | GET | Dados BSC completos (T1 + T2) |
| `/dashboard/kpis` | GET | KPIs por departamento com scores |
| `/dashboard/evolution` | GET | Evolução mensal (12 meses) |
| `/dashboard/agents` | GET | Ranking de agentes |
| `/dashboard/channels` | GET | Métricas por canal (WhatsApp, Webchat, etc.) |

#### 2.3 Endpoints de Conversas (`/api/v1/conversations`)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/conversations` | GET | Lista paginada com filtros |
| `/conversations/{id}` | GET | Detalhe completo da conversa |
| `/conversations/{id}/messages` | GET | Mensagens da conversa |

**Parâmetros de filtro para `/conversations`:**

- `start_date`, `end_date` — Período
- `department` — Departamento
- `agent` — Agente
- `channel` — Canal (WhatsApp, Webchat, etc.)
- `status` — Status (active, archived)
- `search` — Busca por nome/telefone
- `page`, `per_page` — Paginação
- `sort_by`, `sort_order` — Ordenação

#### 2.4 Endpoints de Exportação (`/api/v1/reports`)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/reports/generate` | POST | Gera relatório sob demanda |
| `/reports/{id}/download` | GET | Download do arquivo gerado |
| `/reports/available` | GET | Lista relatórios disponíveis |

**Body para `/reports/generate`:**

```json
{
  "type": "monthly" | "annual",
  "year": 2026,
  "month": 6,
  "group": "Suporte"
}
```

#### 2.5 Endpoints de Administração (`/api/v1/admin`)

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/admin/sync/status` | GET | Status da última sincronização |
| `/admin/sync/trigger` | POST | Dispara sync manual |
| `/admin/agents` | GET | Lista de agentes |
| `/admin/departments` | GET | Departamentos |
| `/admin/health` | GET | Health check |

#### 2.6 Scheduler de Sync

- APScheduler com trigger `interval` (15 minutos)
- Modo incremental por padrão
- Full sync diário às 3:00 AM
- Logs de sync para tabela `sync_logs`
- Roda junto com o FastAPI no mesmo container

---

### Fase 3: Frontend Dashboard (7-10 dias)

**Objetivo:** Dashboard interativo estilo Power BI.

#### 3.1 Setup do Next.js

```bash
npx create-next-app@latest frontend --typescript --tailwind --app
```

#### 3.2 Estrutura de Páginas

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── layout.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx          # Sidebar + topbar
│   │   ├── page.tsx            # Dashboard principal (KPIs)
│   │   ├── conversations/
│   │   │   ├── page.tsx        # Lista de conversas
│   │   │   └── [id]/page.tsx   # Detalhe da conversa
│   │   ├── agents/
│   │   │   └── page.tsx        # Ranking de agentes
│   │   ├── reports/
│   │   │   └── page.tsx        # Gerar/baixar relatórios
│   │   └── settings/
│   │       └── page.tsx        # Configurações
│   └── layout.tsx              # Root layout
├── components/
│   ├── ui/                     # Button, Card, Table, etc.
│   ├── dashboard/
│   │   ├── KPICard.tsx
│   │   ├── BSCChart.tsx
│   │   ├── EvolutionChart.tsx
│   │   ├── AgentRanking.tsx
│   │   └── ChannelBreakdown.tsx
│   ├── conversations/
│   │   ├── ConversationTable.tsx
│   │   ├── ConversationFilters.tsx
│   │   └── MessageThread.tsx
│   └── layout/
│       ├── Sidebar.tsx
│       └── TopBar.tsx
├── lib/
│   ├── api.ts                  # API client (fetch wrapper)
│   ├── auth.ts                 # Auth context + JWT
│   └── utils.ts                # Formatação, helpers
├── hooks/
│   ├── useDashboard.ts
│   ├── useConversations.ts
│   └── useAuth.ts
└── types/
    └── index.ts                # TypeScript interfaces
```

#### 3.3 Páginas Principais

**Dashboard Home:**

- 4 KPI Cards (NPS, FRT, ART, Volume) com ícone e trend
- Gráfico de evolução mensal (line chart - Recharts)
- Tabela BSC com cores (verde/amarelo/vermelho)
- Breakdown por canal (pie chart)

**Conversas:**

- Tabela paginada com busca
- Filtros laterais: período, departamento, agente, canal
- Click para detalhe → mensagens da conversa
- Exportação para CSV

**Relatórios:**

- Formulário: período, tipo (mensal/anual), grupo
- Botão gerar → status de progresso
- Lista de relatórios gerados para download

#### 3.4 Bibliotecas de UI

| Biblioteca | Função |
|------------|--------|
| **Tailwind CSS** | Styling utilitário |
| **shadcn/ui** | Componentes acessíveis |
| **Recharts** | Gráficos React |
| **TanStack Table** | Tabelas (sort, filter, paginate) |
| **React Hook Form + Zod** | Forms e validação |
| **Axios** | HTTP client |

#### 3.5 Dark/Light Mode

- Next.js ThemeProvider
- Toggle no TopBar
- Tema escuro: cores base `#0f172a` (slate-900)
- Tema claro: cores base `#ffffff`
- Persistência via localStorage

---

### Fase 4: Integração e Deploy (3-5 dias)

**Objetivo:** Tudo funcionando em Docker na VPS com Cloudflare Tunnels.

#### 4.1 Docker Compose Completo

```yaml
services:
  postgres:
    image: postgres:15-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: mbird_reports
      POSTGRES_USER: mbird
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    # Não expõe porta externamente — apenas comunicação entre containers

  api:
    build: .
    command: uvicorn api.main:app --host 0.0.0.0 --port 8050
    env_file: .env
    depends_on:
      - postgres
    volumes:
      - ./reports:/app/reports
    ports:
      - "127.0.0.1:8050:8000"  # Apenas localhost para Cloudflare Tunnel

  frontend:
    build: ./frontend
    ports:
      - "127.0.0.1:3050:3000"  # Apenas localhost para Cloudflare Tunnel
    depends_on:
      - api

volumes:
  pgdata:
```

> **Nota:** Portas expostas apenas em `127.0.0.1` (localhost) para que apenas o Cloudflare Tunnel tenha acesso externo.

#### 4.2 Migrar Dados Existentes

- Script para exportar do SQLite → importar no PostgreSQL
- Preserva: contacts, agents, conversations, messages, sync, sync_errors

#### 4.4 Variáveis de Ambiente

```env
# Database
DATABASE_URL=postgresql+asyncpg://mbird:${DB_PASSWORD}@postgres:5432/mbird_reports

# Auth
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=480
CORS_ORIGINS=https://app.empresa.com

# MessageBird API
MESSAGEBIRD_API_KEY_LIVE=...
MESSAGEBIRD_WORKSPACE_ID_LIVE=...
MESSAGEBIRD_BASE_URL_CONVERSATIONS=https://conversations.messagebird.com/v1
MESSAGEBIRD_BASE_URL_CONTACTS=https://contacts.messagebird.com/v2
MESSAGEBIRD_DB_FILENAME=m_bird.db
MESSAGEBIRD_HTTP_TIMEOUT=30.0
MESSAGEBIRD_TIMEZONE_OFFSET=-3
```

---

## Estrutura de Diretórios Final

```
MessageBird_API_Reports/
├── api/                          # NOVO: FastAPI backend
│   ├── __init__.py
│   ├── main.py                   # App factory
│   ├── dependencies.py           # DI container
│   ├── auth.py                   # JWT auth
│   ├── middleware.py             # CORS, logging
│   ├── schemas/                  # Pydantic models
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── conversations.py
│   │   └── reports.py
│   └── routes/                   # Endpoint routers
│       ├── auth.py
│       ├── dashboard.py
│       ├── conversations.py
│       ├── reports.py
│       └── admin.py
│
├── frontend/                     # NOVO: Next.js dashboard
│   ├── app/                      # App Router
│   ├── components/               # React components
│   ├── lib/                      # API client, utils
│   ├── hooks/                    # Custom React hooks
│   ├── types/                    # TypeScript types
│   ├── tailwind.config.ts
│   └── package.json
│
├── domain/                       # EXISTENTE (inalterado)
├── application/                  # EXISTENTE (inalterado)
├── infrastructure/               # EXISTENTE + novo postgres_repository
│   ├── database/
│   │   ├── postgres_repository.py    # NOVO
│   │   ├── migrations/               # NOVO
│   │   │   └── 001_initial.sql
│   │   └── sqlite_repository.py      # EXISTENTE
│   └── ...
│
├── docker-compose.yml            # NOVO
├── Dockerfile                    # NOVO
├── pyproject.toml                # ATUALIZADO
├── .env.example                  # NOVO (template)
├── main.py                       # EXISTENTE (CLI continua)
├── business_config.yaml          # EXISTENTE
├── business_bsc.yaml             # EXISTENTE
└── docs/                         # EXISTENTE + novos docs
    ├── plano_web_dashboard.md    # ESTE ARQUIVO
    └── deploy.md                 # NOVO: guia de deploy
```

---

## Estimativa de Esforço

| Fase | Dias | Dependências |
|------|------|--------------|
| **Fase 1:** Preparação (PG + Docker + FastAPI) | 2-3 | Nenhuma |
| **Fase 2:** Backend API completo | 5-7 | Fase 1 |
| **Fase 3:** Frontend dashboard | 7-10 | Fase 2 |
| **Fase 4:** Integração e deploy | 3-5 | Fase 3 |
| **Total** | **17-25 dias** | |

---

### Stack Tecnológica (Julho 2026)

#### Backend (Python)

| Dependência | Versão | Função |
|-------------|--------|--------|
| Python | 3.14.6 | Runtime |
| FastAPI | 0.139.0 | Framework web async |
| Uvicorn | 0.51.0 | ASGI server |
| Pydantic | 2.13.4 | Validação de dados |
| SQLAlchemy | 2.0.51 | ORM + queries |
| Alembic | 1.18.5 | Migrations |
| asyncpg | 0.31.0 | Driver PostgreSQL async |
| python-jose | 3.5.0 | JWT tokens |
| passlib | 1.7.4 | Password hashing |
| httpx | 0.27.0 | HTTP client async |
| APScheduler | 3.10.0 | Scheduler de sync |

#### Frontend (TypeScript)

| Dependência | Versão | Função |
|-------------|--------|--------|
| Next.js | 16.2.10 | Framework React |
| React | 19.2.7 | UI library |
| Tailwind CSS | 4.3.3 | Estilização |
| shadcn/ui | 4.13.0 | Componentes UI |
| Recharts | 3.9.2 | Gráficos |
| TanStack Table | 8.21.3 | Tabelas |
| React Hook Form | 7.x | Forms |
| Zod | 3.x | Validação |

#### Banco de Dados

| Componente | Versão | Função |
|------------|--------|--------|
| PostgreSQL | 18.4 | Banco relacional |
| Docker Image | postgres:18-alpine | Container otimizado |

---

## Decisões Técnicas

### Por que FastAPI (Python) e não NestJS (TypeScript)?

| Aspecto | FastAPI (Python) | NestJS (TypeScript) |
|---------|------------------|---------------------|
| **Reuso de código** | ✅ 100% do backend existente | ❌ Reescrever TUDO em TS |
| **Sinergia com frontend** | ⚠️ Duas linguagens | ✅ TypeScript puro |
| **Escopo do projeto** | 17-25 dias | 40-60 dias (reescrever lógica) |
| **Risco** | Baixo | Alto |

**Justificativa:** 50-70% do backend Python já existe e está testado:
- `sync.py` (1253 linhas) — sincronização MessageBird
- `metrics_calculator.py` — NPS, FRT, ART, duração
- `report_aggregator.py` — agregação e scoring BSC
- `sqlite_repository.py` — queries SQL otimizadas
- `_bsc_writer.py` — fórmulas Excel

Migrar para NestJS significaria reescrever cada uma dessas peças em TypeScript.

### Por que PostgreSQL e não SQLite?

| Aspecto | SQLite | PostgreSQL |
|---------|--------|------------|
| **Concorrência** | 1 writer por vez | Multi-writer |
| **30 usuários** | Degrada | Confortável |
| **Queries complexas** | Limitado | Full SQL |
| **Migração** | N/A | Alembic/SQL |

### Por que Next.js e não React puro?

| Aspecto | React + Vite | Next.js |
|---------|--------------|---------|
| **SSR** | Não | Sim (dashboard rápido) |
| **API Routes** | Não | Sim (pode substituir FastAPI parcialmente) |
| **Deploy** | Mais simples | Docker |
| **SEO** | Limitado | Excelente |

### Por que Cloudflare Tunnels e não Nginx?

| Aspecto | Nginx | Cloudflare Tunnels |
|---------|-------|-------------------|
| **Setup** | Configuração manual | Já configurado na VPS |
| **SSL** | Certbot/Let's Encrypt | Automático |
| **DDoS** | Não protege | Proteção Cloudflare |
| **Manutenção** | Renovar certs manual | Zero manutenção |

### Por que shadcn/ui?

- Gratuito e open-source
- Componentes estilizados com Tailwind
- Acessível por padrão
- Fácil customização
- Não é uma dependência pesada (código copiado, não importado)

---

## Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Migração SQLite → PostgreSQL quebra queries | Alto | Manter SQLite para testes unitários |
| Sync durante alto tráfego bloqueia escritas | Médio | PostgreSQL resolve isso |
| Frontend complexo demais | Médio | Focar MVP: Dashboard + Conversas |
| VPS sem recursos suficientes | Baixo | Docker resource limits |
| API keys expostas no frontend | Alto | Nunca expor .env no browser |
| Cloudflare Tunnel indisponível | Baixo | Tunnel tem alta disponibilidade |

---

## Funcionalidades Prioritárias (MVP)

Para 10-30 usuários em departamento, priorizar:

1. **KPIs BSC em tempo real** — Ver métricas atualizadas sem gerar Excel manualmente
2. **Consulta de conversas** — Buscar, filtrar e ver detalhes de conversas individuais
3. **Exportação automática** — Gerar e baixar relatórios Excel/PDF sob demanda
