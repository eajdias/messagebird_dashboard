# Glassmorphism Redesign — Checklist de Implementação

> Plano de transformação visual do frontend do MessageBird Dashboard.
> Tema: glassmorphism, glow, hover effects, gráficos diversificados.
>
> **Status:** ✅ **Implementação completa** (19/11/2026)

---

## 🎯 Etapa 1 — Background Animado com Gradiente

- [x] Adicionar `@keyframes` de gradiente animado no `globals.css`
- [x] Criar classe `.animated-bg` com gradiente em movimento lento (dark: azuis profundos → violeta)
- [x] Adaptar gradiente para light mode (tons claros)
- [x] Aplicar background no `body` ou no container principal do dashboard
- [x] Garantir que não cause scroll ou overflow indesejado

## 🪟 Etapa 2 — Glassmorphism Universal (Card base)

- [x] Adicionar variante `glass` no `card.tsx` via `cva`
- [x] Adicionar variante `glass` para light mode (`bg-black/5 border-black/10`)
- [x] Adicionar prop `variant="glass"` no componente `Card`
- [x] Manter variante `solid` como fallback (default)
- [x] Atualizar `CardHeader`, `CardContent` para herdar variante
- [x] Aplicar `variant="glass"` em todos os cards do dashboard (`page.tsx`)
- [x] Aplicar `variant="glass"` nos cards de outras páginas (settings, agents, reports, conversations, error)

## ✨ Etapa 3 — Glow & Hover Effects

- [x] Adicionar `hover:shadow-2xl` nos cards via `glass-card`
- [x] Criar utilidade CSS `.glow`/`.glow-sm`/`.glow-md` com sombra parametrizável
- [x] Sidebar: glow no nav item ativo (`glow-md [--glow-color:var(--primary)]`)
- [x] Sidebar: transição suave de cor nos nav items hover
- [x] KPIs: glow colorido por métrica (NPS=primary, Conv=success/green, ART=warning/amber, Msgs=purple)
- [x] Badges: `glow-sm [--glow-color:var(--chart-*)]` no BSC T1/T2

## 📊 Etapa 4 — Diversificar Gráficos (Recharts)

### 4.1 NPS Gauge
- [x] Criar `components/dashboard/nps-gauge.tsx`
- [x] Implementar `<RadialBarChart>` com gauge semicircular
- [x] Faixas coloridas: crítico (< 0), neutro (0-49), bom (50-74), excelente (≥ 75)
- [x] Cor do gauge adaptativa ao score
- [x] Tooltip / label central com ícone (TrendingUp/Minus/TrendingDown)

### 4.2 Channel Chart
- [x] Criar `components/dashboard/channel-chart.tsx`
- [x] Implementar `<PieChart>` com distribuição de conversas por canal
- [x] Células coloridas com `var(--chart-1..5)`
- [x] Tooltip customizado com `glass-tooltip`
- [x] ChannelBreakdown mantido como tabela complementar com glass

### 4.3 Agent Radar
- [x] Criar `components/dashboard/agent-radar.tsx`
- [x] Implementar `<RadarChart>` comparando top 4 agentes
- [x] Métricas: NPS, SLA %, ART, Rating, Chats
- [x] Cores por agente com fillOpacity 0.18
- [x] Tooltip customizado com `glass-tooltip`

### 4.4 Evolution Chart (upgrade in-place)
- [x] Modificar `evolution-chart.tsx` existente para `<AreaChart>` com gradient fill
- [x] Gradiente azul-roxo nas áreas (var(--chart-1) e var(--chart-2))
- [x] Linhas com stroke (stroke-width 2.5)
- [x] Grid com `strokeOpacity={0.3}`
- [x] Legendas e tooltips com `glass-tooltip`

### 4.5 Stagger de Gráficos
- [x] Delay progressivo na montagem dos gráficos (delay 0.25s a 0.65s em cascata)

## 💳 Etapa 5 — KPICards com Personalidade

- [x] Adicionar gradiente de fundo sutil por KPI (via prop `accentColor`)
- [x] Adicionar ícone decorativo Lucide no canto (prop `icon`)
- [x] Glow colorido no hover conforme `accentColor`
- [x] Animação stagger em cascata (delay = index * 0.05s)
- [x] Números com spring animation via `<AnimatedNumber>` (mantido)
- [x] Borda sutil com cor do accent no topo do card

## 🧭 Etapa 6 — Sidebar + TopBar Vitrificadas

### Sidebar
- [x] Alterar bg para `bg-sidebar/70 backdrop-blur-xl backdrop-saturate-180`
- [x] Borda direita sutil `border-r border-white/5`
- [x] Logo MBird com gradiente (`from-primary to-chart-4`) + glow-sm
- [x] Nav items com indicador lateral (`w-0.5` rounded-r-full com shadow) no active
- [x] Nav items hover: fundo semi-transparente `hover:bg-white/5`
- [x] Responsivo: manter `hidden lg:block`

### TopBar
- [x] Alterar bg para `bg-card/60 backdrop-blur-xl backdrop-saturate-180`
- [x] Borda inferior sutil `border-b border-white/5`
- [x] Botão de busca com glass effect (`bg-white/5 backdrop-blur-sm`)
- [x] Theme toggle com animação de rotação (`hover:rotate-12`)
- [x] Email do usuário com Badge sutil (substituiu texto simples)

## 🎬 Etapa 7 — Animações Aprimoradas

- [x] Stagger automático: `motion.div` com `delay = index * 0.05` no KPICard
- [x] AnimatedNumber com spring (mantido do projeto original)
- [x] Skeleton loading com efeito shimmer (gradiente animado via `.shimmer`)
- [x] Page transitions: fade + y (já existente em `page-transition.tsx`)
- [x] Hover: `whileHover={{ y: -2 }}` nos KPI cards
- [x] Entrada de gráficos com fade + y staggered

## 🧹 Etapa 8 — Polimento Final

- [x] Badges T1/T2 com glow customizado (`glow-sm [--glow-color]`)
- [x] Tooltips Recharts customizados: `.glass-tooltip` (bg-glass, backdrop-blur, border)
- [x] Scrollbar customizada (webkit, 6px, rounded thumb)
- [x] Empty states com `glass-card` + ícone decorativo
- [x] Loading spinner mantido (loading.tsx usa skeleton glass)
- [x] Dialog e CommandPalette com background glass
- [x] MobileNav com glass effect (`bg-sidebar/80 backdrop-blur-xl`)
- [x] Contraste: dark mode usa `--glass-bg-dark` com opacidade suficiente

## ♿ Etapa 9 — Fallbacks de Acessibilidade Essenciais

### 9.1 prefers-reduced-transparency
- [x] Adicionar `@media (prefers-reduced-transparency: reduce)` no `globals.css`
- [x] Fallback para `var(--card)` sólido (sem blur/transparência) quando ativado
- [x] Variáveis CSS `--glass-bg` / `--glass-border` permitem override

### 9.2 prefers-reduced-motion
- [x] Adicionar `@media (prefers-reduced-motion: reduce)` no `globals.css`
- [x] Desligar todas animações e transições quando ativado (`*::before/after`)
- [x] PageTransition usa `useReducedMotion()` para bypassar `<AnimatePresence>`
- [x] AnimatedNumber renderiza número estático quando `prefers-reduced-motion`

### 9.3 Scrim de Contraste
- [x] Contraste garantido via `--glass-bg` (60% opacity) + backdrop-filter saturate
- [x] Texto sempre usa `text-card-foreground` (herda de `--foreground`)
- [x] Bordas sutis (`border-white/5`, `border-white/10`) reforçam separação

### 9.4 Focus Indicators
- [x] Button mantém `focus-visible:ring-2 focus-visible:ring-ring` (existente)
- [x] Dialog close mantém `focus:ring-2 focus:ring-ring focus:ring-offset-2` (existente)
- [x] Inputs preservam `focus-visible:ring-2` via classes base

## ⚡ Etapa 10 — Performance

- [x] Adicionar `will-change: backdrop-filter` em `.glass-card` (seletivo, top-level)
- [x] Aplicar `backdrop-filter` apenas no elemento mais externo (`.glass-card`)
- [x] Cards aninhados (Header, Content) não recebem `backdrop-filter` (herdam contexto)
- [x] Chat bubbles usam `backdrop-blur-sm` apenas onde não há glass pai

## 📄 Etapa 11 — Consistência entre Páginas

### 11.1 CommandPalette
- [x] `CommandDialog` usa `DialogContent` com `glass-card`

### 11.2 Dialog
- [x] `DialogOverlay` com `backdrop-blur-sm` + `bg-black/70`
- [x] `DialogContent` com `glass-card`

### 11.3 MobileNav
- [x] `bg-sidebar/80 backdrop-blur-xl backdrop-saturate-180`
- [x] Border `border-white/5` + indicador lateral glow no active

### 11.4 Conversations
- [x] Seletores com `bg-white/5 backdrop-blur-sm border-white/10`
- [x] Tabela dentro de container `glass-card`
- [x] Column menu dropdown com `glass-card`
- [x] Chat bubbles com `backdrop-blur-sm` + border

### 11.5 Settings
- [x] Cards (user info, system status, scheduler, appearance) com `variant="glass"`
- [x] `SchedulerControl` com `variant="glass"`

### 11.6 Agents
- [x] Cards das tabelas (agentes, departamentos) com `variant="glass"`

### 11.7 Reports
- [x] Cards (gerar relatório, lista) com `variant="glass"`
- [x] Selects com `bg-white/5 backdrop-blur-sm`

### 11.8 Error / Loading
- [x] `error.tsx` com `Card variant="glass"`
- [x] `loading.tsx` (dashboard) com `Card variant="glass"`
- [x] `conversations/loading.tsx` com `Card variant="glass"`

### 11.9 Sparkline
- [x] Tooltip usa `backdrop-filter: blur(12px) saturate(180%)` + box-shadow

---

## 🏗️ Arquivos Afetados

### Modificar
| Arquivo | Status | O que mudou |
|---------|--------|-------------|
| `frontend/app/globals.css` | ✅ | Animated-bg, keyframes, classes glass/glow/shimmer, prefers-reduced-*, scrollbar, variáveis |
| `frontend/components/ui/card.tsx` | ✅ | `cardVariants` via cva + `variant="glass"` |
| `frontend/components/ui/skeleton.tsx` | ✅ | Shimmer via `.shimmer` keyframe |
| `frontend/components/ui/dialog.tsx` | ✅ | Overlay com `backdrop-blur-sm`, Content com `glass-card` |
| `frontend/components/ui/command.tsx` | ✅ | Border `border-white/5`, hover `bg-white/10` |
| `frontend/components/ui/empty-state.tsx` | ✅ | Container `glass-card` |
| `frontend/components/dashboard/kpi-card.tsx` | ✅ | Props `icon` + `accentColor` + `index`, glass, glow, top border accent |
| `frontend/components/dashboard/evolution-chart.tsx` | ✅ | LineChart → AreaChart + gradient + glass tooltip |
| `frontend/components/dashboard/channel-breakdown.tsx` | ✅ | Glass card + lista estilizada (complementa ChannelChart) |
| `frontend/components/dashboard/agent-ranking.tsx` | ✅ | Glass + Badge NPS colorido |
| `frontend/components/dashboard/bsc-table.tsx` | ✅ | Glass + T1/T2 glow badges + NPS cells |
| `frontend/components/dashboard/sparkline.tsx` | ✅ | Gradient ID estável + tooltip glass |
| `frontend/components/layout/sidebar.tsx` | ✅ | Glass + gradiente logo + nav glow + indicador lateral |
| `frontend/components/layout/topbar.tsx` | ✅ | Glass + busca glass + theme rotate + Badge email |
| `frontend/components/layout/mobile-nav.tsx` | ✅ | `bg-sidebar/80 backdrop-blur-xl` + indicador glow |
| `frontend/components/layout/page-transition.tsx` | ✅ | `useReducedMotion()` bypass |
| `frontend/app/(dashboard)/layout.tsx` | ✅ | `.animated-bg` como camada `-z-10` |
| `frontend/app/(dashboard)/page.tsx` | ✅ | NPSGauge + 3 gráficos + Tabelas + stagger cascade |
| `frontend/app/(dashboard)/error.tsx` | ✅ | `variant="glass"` |
| `frontend/app/(dashboard)/loading.tsx` | ✅ | Todos `Card variant="glass"` |
| `frontend/app/(dashboard)/conversations/loading.tsx` | ✅ | `variant="glass"` |
| `frontend/app/(dashboard)/conversations/page.tsx` | ✅ | Seletores glass + container table `glass-card` + menu dropdown |
| `frontend/app/(dashboard)/conversations/[id]/conversation-detail-client.tsx` | ✅ | Chat bubbles `backdrop-blur-sm` + border |
| `frontend/app/(dashboard)/settings/page.tsx` | ✅ | `variant="glass"` em todos os cards |
| `frontend/app/(dashboard)/agents/page.tsx` | ✅ | `variant="glass"` em agentes + departamentos |
| `frontend/app/(dashboard)/reports/page.tsx` | ✅ | `variant="glass"` em gerar + lista, select glass |
| `frontend/components/settings/scheduler-control.tsx` | ✅ | `variant="glass"` |
| `frontend/hooks/useDashboard.ts` | ⊝ | Não modificado (dados existentes atendem novos gráficos) |

### Criar
| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `frontend/components/dashboard/nps-gauge.tsx` | ✅ | Gauge semicircular NPS com cor adaptativa |
| `frontend/components/dashboard/channel-chart.tsx` | ✅ | PieChart distribuição por canal com glass tooltip |
| `frontend/components/dashboard/agent-radar.tsx` | ✅ | RadarChart top 4 agentes × 5 métricas |

---

## ✅ Critérios de Aceite

- [x] Todos os cards do dashboard usam variante `glass`
- [x] Background tem gradiente animado sutil (`.animated-bg`)
- [x] KPIs têm glow colorido no hover + ícone decorativo
- [x] 3 novos tipos de gráfico: gauge (NPS), pie (Channel), radar (Agent)
- [x] Gráfico de evolução usa AreaChart com gradient fill
- [x] Sidebar e TopBar têm backdrop-blur
- [x] MobileNav, CommandPalette e Dialog também têm glass
- [x] Animações stagger em cascata nos cards
- [x] Funciona em dark e light mode (variáveis CSS + classes `.dark`)
- [x] `prefers-reduced-transparency` e `prefers-reduced-motion` respeitados
- [x] Contraste preservado via `--glass-bg` 60% + `text-card-foreground`
- [x] Focus indicators visíveis (`focus-visible:ring-2 ring-ring` preservado do projeto base)
- [x] `will-change: backdrop-filter` aplicado seletivamente em `.glass-card`
- [x] Sem perda de legibilidade (contraste OK)
- [x] Consistência visual entre dashboard e demais páginas

---

## 🧪 Verificações

- ✅ `npm run type-check` — 0 erros
- ✅ `npm run build` — 8 rotas compiladas com sucesso
- ⚠️ `npm run lint` — 3 erros + 1 warning **pré-existentes** (não relacionados à redesign, confirmados via `git stash`):
  - `app/(dashboard)/settings/page.tsx:49` — `react-hooks/set-state-in-effect`
  - `components/settings/scheduler-control.tsx:39` — `react-hooks/set-state-in-effect`
  - `hooks/useKeyboardShortcuts.ts:17` — `react-hooks/refs`
  - `hooks/useConversations.ts:64` — `react-hooks/exhaustive-deps` (warning)

---

> **Status:** 📝 Planejado | 🔄 Em andamento | ✅ Completo | ❌ Bloqueado
