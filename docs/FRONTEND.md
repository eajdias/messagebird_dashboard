# Frontend — MBird Dashboard

Next.js 16 com App Router, React 19, Tailwind CSS 4.

## Rotas

| Rota | Arquivo | Descrição |
|------|---------|-----------|
| `/` | `app/page.tsx` | Redirect → `/login` |
| `/login` | `app/(auth)/login/page.tsx` | Formulário de login |
| `/` (dashboard) | `app/(dashboard)/page.tsx` | KPIs, gráficos, BSC |
| `/conversations` | `app/(dashboard)/conversations/page.tsx` | Lista paginada |
| `/conversations/[id]` | `app/(dashboard)/conversations/[id]/page.tsx` | Thread de mensagens |
| `/agents` | `app/(dashboard)/agents/page.tsx` | Agentes e departamentos |
| `/reports` | `app/(dashboard)/reports/page.tsx` | Gerar e listar relatórios |
| `/settings` | `app/(dashboard)/settings/page.tsx` | Placeholder |

## Layout Hierarchy

```
layout.tsx (Root: ThemeProvider)
├── (auth)/layout.tsx (centrado, sem sidebar)
│   └── login/page.tsx
│
└── (dashboard)/layout.tsx (auth guard + Sidebar + TopBar)
    ├── page.tsx (dashboard principal)
    ├── conversations/page.tsx
    ├── conversations/[id]/page.tsx
    ├── agents/page.tsx
    ├── reports/page.tsx
    └── settings/page.tsx
```

## Componentes UI (`components/ui/`)

Todos usam `class-variance-authority` + `cn()`.

| Componente | Variants | Tamanhos |
|------------|----------|----------|
| `Button` | default, destructive, outline, secondary, ghost, link | default, sm, lg, icon |
| `Card` | Compound: CardHeader, CardTitle, CardDescription, CardContent, CardFooter | — |
| `Table` | Compound: TableHeader, TableBody, TableRow, TableHead, TableCell | — |
| `Badge` | default, secondary, destructive, outline, success, warning | — |
| `Input` | — | — |

## Componentes Dashboard (`components/dashboard/`)

| Componente | Props | Descrição |
|------------|-------|-----------|
| `KPICard` | title, value, subtitle?, trend?, className? | Card de métrica com valor e trend |
| `EvolutionChart` | data: EvolutionMonth[] | LineChart Recharts (conversas + NPS) |
| `AgentRanking` | agents: AgentRankingItem[] | Tabela top 10 agentes |
| `ChannelBreakdown` | channels: ChannelItem[] | Tabela métricas por canal |
| `BSCTable` | header, data_t1, data_t2 | Tabelas BSC (T1 verde, T2 amarelo) |

## Componentes Layout (`components/layout/`)

| Componente | Descrição |
|------------|-----------|
| `Sidebar` | Menu lateral fixo (w-64), 5 itens: Dashboard, Conversas, Relatórios, Agentes, Configurações. lucide-react icons. |
| `TopBar` | Barra superior: toggle dark/light, email do usuário, botão logout. |

## Hooks (`hooks/`)

| Hook | Retorna | Uso |
|------|---------|-----|
| `useAuth` | { user, token, loading, isAuthenticated, login, logout } | Login/logout, JWT no localStorage |
| `useDashboard` | { summary, bsc, kpis, evolution, agents, channels, loading, error, refetch } | Busca 5 endpoints em paralelo |
| `useConversations` | { data, loading, error, refetch } | Lista paginada com filtros |
| `useConversation` | { detail, loading, error } | Detalhe de conversa |
| `useConversationMessages` | { messages, total, loading, error } | Mensagens de uma conversa |

## API Client (`lib/api.ts`)

Axios instance com:
- Base URL: `NEXT_PUBLIC_API_URL` (default: `http://localhost:8050`)
- Request interceptor: injeta `Authorization: Bearer {token}`
- Response interceptor: redireciona `/login` em 401

## Utilitários

- `lib/utils.ts` — `cn()`: merge de classes (clsx + tailwind-merge)

## Scripts NPM

```bash
npm run dev        # Dev server com Turbopack
npm run build      # Build produção
npm run start      # Iniciar server produção
npm run lint       # ESLint
npm run type-check # TypeScript --noEmit
```

## Configuração

- `next.config.ts` — output standalone, env NEXT_PUBLIC_API_URL
- `app/globals.css` — Tailwind v4 @theme com variáveis light/dark
- `.npmrc` — legacy-peer-deps=true
- `tsconfig.json` — strict mode, path alias `@/*`

## Dependências Não Usadas (instaladas)

| Pacote | Status |
|--------|--------|
| `@tanstack/react-table` | Instalado, não importado |
| `react-hook-form` | Instalado, não usado nas páginas |
| `zod` | Instalado, não usado nas páginas |
| `@hookform/resolvers` | Instalado, não usado |
