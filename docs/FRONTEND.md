# Frontend

> Aplicação Next.js 16 com dashboard, relatórios e configurações.

## Estrutura de Diretórios

```
frontend/
├── app/
│   ├── globals.css              # Estilos globais + Tailwind v4
│   ├── layout.tsx               # Root layout (Inter font, ThemeProvider, Toaster)
│   ├── (auth)/login/page.tsx    # Página de login
│   └── (dashboard)/
│       ├── layout.tsx           # Dashboard shell: Sidebar + TopBar + PageTransition
│       ├── page.tsx             # Dashboard principal (KPIs, charts, BSC)
│       ├── agents/page.tsx      # Agentes e departamentos
│       ├── conversations/       # Lista e detalhe de conversas
│       ├── reports/page.tsx     # Geração e download de relatórios
│       └── settings/page.tsx    # Controle do scheduler
├── components/
│   ├── ui/                      # Componentes base (button, card, table, badge, etc.)
│   ├── layout/                  # Sidebar, TopBar, MobileNav, PageTransition, CommandPalette
│   ├── dashboard/               # KPICard, EvolutionChart, AgentRanking, ChannelBreakdown, BSC
│   └── settings/               # SchedulerControl
├── hooks/                       # useAuth, useDashboard, useConversations, useKeyboardShortcuts
├── lib/                         # api.ts (axios), utils.ts (cn helper), logger.ts
└── types/                       # TypeScript interfaces (index.ts)
```

## Stack Frontend

- **Next.js 16** com App Router e Turbopack
- **React 19** com Server Components
- **TypeScript** strict mode
- **Tailwind CSS v4** com PostCSS
- **Radix UI** para componentes acessíveis (Dialog, Popover)
- **Recharts** para gráficos (AreaChart, BarChart, PieChart, RadialBarChart, RadarChart)
- **framer-motion** para animações
- **lucide-react** para ícones
- **TanStack Table** para tabelas de dados
- **react-hook-form + zod** para formulários
- **axios** para HTTP client
- **next-themes** para suporte dark/light mode
- **sonner** para notificações toast

## Rotas do Frontend

| Rota | Página | Descrição |
|------|--------|-----------|
| `/login` | Login | Autenticação |
| `/` | Dashboard | KPIs, evolução, canais, agentes, BSC |
| `/agents` | Agentes | Lista de agentes e departamentos |
| `/conversations` | Conversas | Lista de conversas |
| `/conversations/[id]` | Detalhe | Conversa com mensagens |
| `/reports` | Relatórios | Geração e download |
| `/settings` | Configurações | Controle do scheduler |

## Hooks

| Hook | Descrição |
|------|-----------|
| `useAuth` | Login, token storage, auth state |
| `useDashboard` | Fetch summary, evolution, agents, channels |
| `useConversations` | Lista e detalhe de conversas |
| `useKeyboardShortcuts` | Atalhos de teclado globais |

## Componentes de UI Base

- `button.tsx` — Variants: primary, secondary, ghost, outline, danger
- `card.tsx` — Variants: solid, glass (backdrop-blur para redesign)
- `badge.tsx` — Status badges com cores
- `table.tsx` — TanStack Table wrapper
- `dialog.tsx` — Radix Dialog modal
- `skeleton.tsx` — Loading skeletons com shimmer
- `animated-number.tsx` — Números com animação spring (framer-motion)
- `empty-state.tsx` — Estado vazio com ícone e mensagem
- `command-palette.tsx` — cmdk command palette

## Layout

- **Sidebar:** Navegação principal, responsiva (hidden em mobile, drawer)
- **TopBar:** Busca, theme toggle, informações do usuário
- **PageTransition:** Animações de transição entre páginas (framer-motion)
- **ThemeProvider:** next-themes com suporte dark/light

## API Client

O cliente HTTP (`lib/api.ts`) usa axios com:
- Base URL dinâmica (auto-detect via hostname ou env var)
- Interceptor de auth (adiciona Bearer token)
- Interceptor de erro (redirect para login em 401)
- Token armazenado em localStorage

## Redesign (Glassmorphism)

O arquivo `GLASSMORPHISM-REDESIGN.md` contém o plano de transformação visual:
- Background animado com gradiente
- Cards com efeito glass (backdrop-blur)
- Glow e hover effects
- Novos gráficos (NPS Gauge, Channel PieChart, Agent Radar)
- Sidebar e TopBar vitrificadas
- Animações stagger em cascata
