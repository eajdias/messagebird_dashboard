# Glassmorphism Redesign — Checklist de Implementação

> Plano de transformação visual do frontend do MessageBird Dashboard.
> Tema: glassmorphism, glow, hover effects, gráficos diversificados.

---

## 🎯 Etapa 1 — Background Animado com Gradiente

- [ ] Adicionar `@keyframes` de gradiente animado no `globals.css`
- [ ] Criar classe `.animated-bg` com gradiente em movimento lento (dark: azuis profundos → violeta)
- [ ] Adaptar gradiente para light mode (tons claros)
- [ ] Aplicar background no `body` ou no container principal do dashboard
- [ ] Garantir que não cause scroll ou overflow indesejado

## 🪟 Etapa 2 — Glassmorphism Universal (Card base)

- [ ] Adicionar variante `glass` no `card.tsx`:
  - `backdrop-blur-xl bg-white/5 border border-white/10 shadow-xl hover:shadow-2xl hover:border-white/20`
- [ ] Adicionar variante `glass` para light mode (`bg-black/5 border-black/10`)
- [ ] Adicionar prop `variant="glass"` no componente `Card`
- [ ] Manter variante `solid` como fallback
- [ ] Atualizar `CardHeader`, `CardContent` para herdar variante
- [ ] Aplicar `variant="glass"` em todos os cards do dashboard (`page.tsx`)
- [ ] Aplicar `variant="glass"` nos cards de outras páginas (settings, agents, reports, conversations, error)

## ✨ Etapa 3 — Glow & Hover Effects

- [ ] Adicionar `hover:shadow-[0_0_20px_-5px_var(--primary)]` nos cards
- [ ] Criar utilidade CSS `.glow-{color}` com sombra glow parametrizável
- [ ] Sidebar: glow no nav item ativo (`shadow-[0_0_12px_-3px_var(--primary)]`)
- [ ] Sidebar: transição suave de cor nos nav items hover
- [ ] KPIs: glow colorido por métrica (NPS=blue, Conv=green, ART=amber, Msgs=purple)
- [ ] Badges: `shadow-[0_0_8px]` na cor correspondente

## 📊 Etapa 4 — Diversificar Gráficos (Recharts)

### 4.1 NPS Gauge
- [ ] Criar `components/dashboard/nps-gauge.tsx`
- [ ] Implementar `<RadialBarChart>` com gauge semicircular 0-100
- [ ] Faixas coloridas: vermelho (< 50), amarelo (50-74), verde (≥ 75)
- [ ] Animação de preenchimento na montagem
- [ ] Tooltip customizado com glass effect

### 4.2 Channel Chart
- [ ] Criar `components/dashboard/channel-chart.tsx`
- [ ] Implementar `<PieChart>` com distribuição de conversas por canal
- [ ] Alternativa: `<BarChart>` horizontal para ranking de canais
- [ ] Células coloridas com gradiente
- [ ] Tooltip customizado com glass effect
- [ ] Substituir/Complementar a tabela `ChannelBreakdown`

### 4.3 Agent Radar
- [ ] Criar `components/dashboard/agent-radar.tsx`
- [ ] Implementar `<RadarChart>` comparando top 3-5 agentes
- [ ] Métricas: NPS, ART, SLA, rating, chats
- [ ] Cores por agente com fill semi-transparente
- [ ] Tooltip customizado

### 4.4 Evolution Chart (upgrade in-place)
- [ ] Modificar `evolution-chart.tsx` existente para `<AreaChart>` com gradient fill
- [ ] Gradiente azul-roxo nas áreas
- [ ] Linhas com stroke com glow sutil (stroke-width 2-3)
- [ ] Grid com opacidade reduzida (`stroke-opacity`)
- [ ] Legendas e tooltips com glass effect

### 4.5 Stagger de Gráficos
- [ ] Delay progressivo na montagem dos gráficos (stagger)

## 💳 Etapa 5 — KPICards com Personalidade

- [ ] Adicionar gradiente de fundo sutil por KPI (via prop `accentColor`)
- [ ] Adicionar ícone decorativo Lucide no canto (prop `icon`)
- [ ] Glow colorido no hover conforme `accentColor`
- [ ] Animação stagger em cascata (delay = index * 0.05s)
- [ ] Números com spring animation mais pronunciada
- [ ] Borda sutil com cor do accent no topo do card

## 🧭 Etapa 6 — Sidebar + TopBar Vitrificadas

### Sidebar
- [ ] Alterar bg para `bg-sidebar/70 backdrop-blur-xl`
- [ ] Borda direita sutil `border-r border-white/5`
- [ ] Logo MBird com gradiente + glow
- [ ] Nav items com indicador lateral (barra `border-l-2`) no active
- [ ] Nav items hover: glow + fundo semi-transparente (bg-white/5)
- [ ] Responsivo: manter `hidden lg:block`

### TopBar
- [ ] Alterar bg para `bg-card/60 backdrop-blur-xl`
- [ ] Borda inferior sutil `border-b border-white/5`
- [ ] Botão de busca com glass effect
- [ ] Theme toggle com animação de rotação suave
- [ ] Avatar/email do usuário com Badge sutil

## 🎬 Etapa 7 — Animações Aprimoradas

- [ ] Stagger automático: `motion.div` com `delay = index * 0.05`
- [ ] Spring mais elástico no `AnimatedNumber` (aumentar stiffness/damping)
- [ ] Skeleton loading com efeito shimmer (gradiente animado + glass)
- [ ] Page transitions: fade + scale leve (não só slide)
- [ ] Hover: scale(1.02) sutil nos cards
- [ ] Entrada de gráficos com fade + scaleY do eixo

## 🧹 Etapa 8 — Polimento Final

- [ ] Badges com glow customizado (`shadow-[0_0_8px_var(--badge-color)]`)
- [ ] Tooltips Recharts customizados: bg-glass, backdrop-blur, borda sutil
- [ ] Scrollbar customizada no `main`:
  ```css
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-thumb { bg: white/10; rounded }
  ```
- [ ] Empty states com glass effect + ícone decorativo animado
- [ ] Loading spinner com glass effect
- [ ] Dialog e CommandPalette com background glass
- [ ] MobileNav com glass effect (substituir bg sólido por backdrop-blur)
- [ ] Verificar contraste acessibilidade (WCAG) nos textos sobre glass

## ♿ Etapa 9 — Fallbacks de Acessibilidade Essenciais

### 9.1 prefers-reduced-transparency
- [ ] Adicionar `@media (prefers-reduced-transparency: reduce)` no `globals.css`
- [ ] Fallback para `bg-card` sólido (sem blur/transparência) quando ativado
- [ ] Usar variável CSS para opacidade que se adapta à preferência

### 9.2 prefers-reduced-motion
- [ ] Adicionar `@media (prefers-reduced-motion: reduce)` no `globals.css`
- [ ] Desligar stagger, spring, scale(1.02), gradiente animado quando ativado
- [ ] Garantir que números ainda apareçam (AnimatedNumber sem spring)

### 9.3 Scrim de Contraste
- [ ] Adicionar camada semi-opaca (`bg-black/40` dark / `bg-white/40` light) atrás do texto em cards glass
- [ ] Garantir contraste WCAG AA (4.5:1 texto normal, 3:1 texto grande)
- [ ] Testar todas as combinações de cor de texto sobre glass

### 9.4 Focus Indicators
- [ ] Garantir `:focus-visible` ring visível em todos elementos interativos com glass
- [ ] Usar `ring-2 ring-primary offset-2` nos botões, links, inputs em superfícies glass

## ⚡ Etapa 10 — Performance

- [ ] Adicionar `will-change: backdrop-filter` nos cards com glass animado (hover/entrada)
- [ ] Aplicar `backdrop-filter` apenas no elemento mais externo (evitar aninhamento de blur)
- [ ] Evitar `backdrop-filter` em elementos dentro de outros com `backdrop-filter`

## 📄 Etapa 11 — Consistência entre Páginas

### 11.1 CommandPalette
- [ ] Adicionar `backdrop-blur-xl bg-background/80` no `CommandDialog`

### 11.2 Dialog
- [ ] Adicionar glass no overlay e content do Dialog

### 11.3 MobileNav
- [ ] Alterar bg do `motion.aside` para `bg-sidebar/80 backdrop-blur-xl`

### 11.4 Conversations
- [ ] Aplicar `variant="glass"` nos cards de filtro e na tabela
- [ ] Adicionar glass effect nos chat bubbles (`conversation-detail-client.tsx`)

### 11.5 Settings
- [ ] Aplicar `variant="glass"` em todos os cards (user info, system status, scheduler, appearance)

### 11.6 Agents
- [ ] Aplicar `variant="glass"` nos cards das tabelas de agentes e departamentos

### 11.7 Reports
- [ ] Aplicar `variant="glass"` nos cards do formulário e lista de relatórios

### 11.8 Error / Loading
- [ ] Aplicar `variant="glass"` no card de erro (`error.tsx`)
- [ ] Aplicar `variant="glass"` nos skeletons (`loading.tsx`)

### 11.9 Sparkline
- [ ] Atualizar tooltip do sparkline para usar glass effect (bg-glass, backdrop-blur)

---

## 🏗️ Arquivos Afetados

### Modificar
| Arquivo | O que muda |
|---------|------------|
| `frontend/app/globals.css` | Background animado, glow utils, scrollbar, prefers-reduced-*, scrim, variáveis |
| `frontend/components/ui/card.tsx` | Variante `glass` + TypeScript interface |
| `frontend/components/ui/skeleton.tsx` | Shimmer glass |
| `frontend/components/ui/dialog.tsx` | Glass no overlay/content |
| `frontend/components/ui/empty-state.tsx` | Glass + ícone animado |
| `frontend/components/dashboard/kpi-card.tsx` | Glass + glow + ícone + accentColor + stagger |
| `frontend/components/dashboard/evolution-chart.tsx` | AreaChart gradient + glow |
| `frontend/components/dashboard/channel-breakdown.tsx` | Substituir por gráfico + glass |
| `frontend/components/dashboard/agent-ranking.tsx` | Substituir por radar + glass |
| `frontend/components/dashboard/bsc-table.tsx` | Glass + glow badges |
| `frontend/components/dashboard/sparkline.tsx` | Tooltip glass effect |
| `frontend/components/layout/sidebar.tsx` | Glass + glow nav |
| `frontend/components/layout/topbar.tsx` | Glass + blur |
| `frontend/components/layout/mobile-nav.tsx` | Glass backdrop-blur |
| `frontend/components/layout/command-palette.tsx` | Glass no CommandDialog |
| `frontend/app/(dashboard)/page.tsx` | Stagger, novos gráficos, layout |
| `frontend/app/(dashboard)/error.tsx` | Card com variant="glass" |
| `frontend/app/(dashboard)/loading.tsx` | Skeleton + card com variant="glass" |
| `frontend/app/(dashboard)/conversations/page.tsx` | Glass nos filtros e tabela |
| `frontend/app/(dashboard)/conversations/[id]/conversation-detail-client.tsx` | Glass chat bubbles |
| `frontend/app/(dashboard)/settings/page.tsx` | Cards com variant="glass" |
| `frontend/app/(dashboard)/agents/page.tsx` | Cards com variant="glass" |
| `frontend/app/(dashboard)/reports/page.tsx` | Cards com variant="glass" |
| `frontend/hooks/useDashboard.ts` | (se precisar) adaptar dados p/ novos gráficos |

### Criar
| Arquivo | Descrição |
|---------|-----------|
| `frontend/components/dashboard/nps-gauge.tsx` | Gauge semicircular NPS |
| `frontend/components/dashboard/channel-chart.tsx` | Pie/Bar chart por canal |
| `frontend/components/dashboard/agent-radar.tsx` | Radar chart comparativo |

---

## ✅ Critérios de Aceite

- [ ] Todos os cards do dashboard usam variante `glass`
- [ ] Background tem gradiente animado sutil
- [ ] KPIs têm glow colorido no hover + ícone decorativo
- [ ] Pelo menos 3 novos tipos de gráfico (gauge, pie/bar, radar)
- [ ] Gráfico de evolução usa AreaChart com gradient fill
- [ ] Sidebar e TopBar têm backdrop-blur
- [ ] MobileNav, CommandPalette e Dialog também têm glass
- [ ] Animações stagger em cascata nos cards
- [ ] Funciona em dark e light mode
- [ ] `prefers-reduced-transparency` e `prefers-reduced-motion` respeitados
- [ ] Scrim de contraste aplicado onde necessário
- [ ] Focus indicators visíveis em elementos glass
- [ ] `will-change` aplicado em elementos animados
- [ ] Sem perda de legibilidade (contraste OK)
- [ ] Consistência visual entre dashboard e demais páginas

---

> **Status:** 📝 Planejado | 🔄 Em andamento | ✅ Completo | ❌ Bloqueado
