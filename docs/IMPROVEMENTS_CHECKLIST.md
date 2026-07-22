# Checklist de Melhorias — Frontend Dashboard

> Acompanhamento da implementação das melhorias propostas em [improvements.md](improvements.md)
> Legenda: ✅ Concluído | 🔄 Em andamento | ⏳ Pendente | ❌ Cancelado

---

## Alta Prioridade

### 13. Micro-Interactions e Animações
**Esforço:** Médio | **Impacto:** Alto

- [x] Animar contadores de KPI (framer-motion useSpring + useMotionValue)
- [x] Animação de entrada nos cards do dashboard (fade + slide up, staggered)
- [x] Hover states com shadow-md nos cards KPI
- [x] Loading skeletons com animação pulse (nativo Tailwind)
- [x] Transições de página (framer-motion AnimatePresence)

### 14. Data Table Aprimorada (TanStack Table)
**Esforço:** Médio | **Impacto:** Alto

- [x] Ordenação por coluna (click no header com indicadores ArrowUpDown/ArrowUp/ArrowDown)
- [x] Controle de visibilidade de colunas (dropdown "Colunas" com checkboxes)
- [x] Filtros faceted (departamento, canal, status com selects)
- [x] Coluna de ações (ícone Eye → link para detalhes)
- [x] Paginação com registros por página configurável (10/20/50/100)
- [x] Row selection + ações em lote (checkbox + botão "Arquivar (N)")
- [x] Select all no header da tabela

### 19. Acessibilidade (A11y)
**Esforço:** Médio | **Impacto:** Alto

- [ ] Auditoria de contraste de cor (WCAG AA 4.5:1)
- [ ] Navegação por teclado (Tab order, skip links)
- [ ] ARIA labels em componentes interativos
- [ ] Testes automatizados com jest-axe / vitest-axe
- [ ] Zoom 200% não quebra layout
- [ ] Screen reader testing (VoiceOver / NVDA)

### 24. Performance e Code Splitting
**Esforço:** Baixo | **Impacto:** Alto

- [x] Dynamic imports para componentes pesados (EvolutionChart, AgentRanking, ChannelBreakdown, BSCTable)
- [ ] Bundle analysis com @next/bundle-analyzer (instalado, configurar em PR separado)
- [x] Code splitting via next/dynamic com ssr:false para Recharts
- [x] Loading skeletons com shadcn/ui Skeleton
- [x] modularizeImports para lucide-react (tree-shaking de ícones)
- [x] Route-level loading.tsx para todas as páginas do dashboard
- [x] Route-level error.tsx para dashboard
- [x] TypeScript target ES2017 → ES2022 (menor output)

### 21. Error/Empty States
**Esforço:** Baixo | **Impacto:** Médio

- [x] Instalar sonner para toasts
- [x] Toaster no root layout com richColors e closeButton
- [x] EmptyState component reutilizável (ícone, título, descrição, action)
- [x] Empty table de conversas com ilustração Inbox
- [x] Toast de sucesso ao exportar CSV
- [x] Error state do dashboard com ícone AlertCircle + botão retry

### 23. Responsive Improvements
**Esforço:** Médio | **Impacto:** Alto

- [x] Mobile sidebar drawer com animação slide-in (framer-motion spring)
- [x] Backdrop overlay ao abrir menu mobile
- [x] Hamburger button no topbar (visível apenas em lg:hidden)
- [x] Fechar menu ao navegar
- [x] Tabela de conversas com overflow-x-auto (scroll horizontal)
- [x] Search bar responsiva (texto menor em md, full em lg)
- [x] Padding responsivo no header (px-4 md:px-6)
- [x] Touch targets 44px+ nos itens de navegação mobile

---

## Média Prioridade

### 15. Command Palette (Cmd+K)
**Esforço:** Baixo | **Impacto:** Médio

- [x] Instalar e configurar cmdk + shadcn Command
- [x] Navegação entre páginas via Cmd+K (useRouter push)
- [x] Atalhos para ações comuns (export, refresh, report)
- [x] Botão de busca no header com indicador ⌘K
- [x] Busca fuzzy nos comandos (nativo do cmdk)
- [x] Grupos: Navegação + Ações
- [x] Responsivo: botão search no desktop, ícone no mobile

### 16. Bento Grid Layout
**Esforço:** Médio | **Impacto:** Alto

- [x] Redesenhar layout da dashboard como bento grid (CSS Grid template-areas)
- [x] NPS como hero card (2 colunas × 2 linhas, gradiente bg-primary/10)
- [x] Cards médios 1x1 para métricas secundárias (Conversas, ART, Mensagens)
- [x] Card full-width para gráfico de evolução (4 colunas)
- [x] Channel Breakdown + Agent Ranking lado a lado (2 colunas cada)
- [x] BSC Table full width
- [x] Responsivo: mobile usa grid simples (sm:grid-cols-2), lg aplica bento grid

### 17. Sparklines nos KPIs
**Esforço:** Médio | **Impacto:** Alto

- [x] Mini AreaChart (64px) em cada KPI Card
- [x] Gradiente de cor por tendência (chart-1 a chart-4)
- [x] Tooltip no hover com valores
- [x] Dados dos últimos 12 meses (evolution data)
- [x] Dynamic import do Sparkline (Recharts lazy)
- [x] NPS sparkline (azul), Conversas (verde), ART (âmbar), Mensagens (roxo)

### 20. Design Tokens e Temas Customizados
**Esforço:** Baixo | **Impacto:** Médio

- [x] Definir paleta de cores da marca (primary azul profissional #2563eb/#3b82f6)
- [x] Customizar CSS variables no globals.css
- [x] Adicionar Inter via @next/font/google com variable CSS
- [x] Configurar chart colors (5 cores para gráficos Recharts)
- [x] Ajustar sidebar colors para light/dark
- [x] Melhorar contraste e legibilidade (dark mode refinado)
- [x] Font smoothing e antialiasing

### 21. Visualizações Salvas (Saved Views)
**Esforço:** Médio | **Impacto:** Médio

- [ ] Botão "Salvar visualização" com nome
- [ ] Persistência em localStorage (Zustand persist)
- [ ] Combinação: período + departamento + canais + colunas
- [ ] View default ao abrir o dashboard
- [ ] Compartilhável via URL (query params)

---

## Baixa Prioridade

### 18. Central de Notificações
**Esforço:** Alto | **Impacto:** Médio

- [ ] Ícone de sino no header com badge
- [ ] Dropdown com últimas notificações
- [ ] Tipos: SLA, NPS, sync, relatório
- [ ] Toast (sonner) para notificações efêmeras
- [ ] Lidas vs não-lidas com persistência

### 22. Product Tour (Onboarding)
**Esforço:** Baixo | **Impacto:** Baixo

- [ ] Configurar React Joyride
- [ ] Tour de boas-vindas no primeiro acesso
- [ ] Passos destacando: KPIs, gráficos, filtros, export
- [ ] Botão "Iniciar Tour" no header

### 23. Page Transitions
**Esforço:** Baixo | **Impacto:** Baixo

- [x] Instalar framer-motion 12.x
- [x] PageTransition com AnimatePresence (fade + slide 12px, 0.2s)
- [x] mode="wait" para evitar conflito entre animações
- [x] Integrado no dashboard layout

### 25. Keyboard Shortcuts
**Esforço:** Baixo | **Impacto:** Médio

- [x] `G D` → Dashboard
- [x] `G C` → Conversas
- [x] `G A` → Agentes
- [x] `G R` → Relatórios
- [x] `G S` → Settings
- [x] `R` → Refresh (reload)
- [x] Hook global `useKeyboardShortcuts` com suporte a sequências (G + letra)
- [x] Buffer de 500ms para digitação de sequências
- [x] Ignora inputs e textareas

---

## Resumo

| Prioridade | Total | ✅ Concluído | 🔄 Em andamento | ⏳ Pendente |
|------------|-------|--------------|------------------|-------------|
| Alta | 6 itens | 4 | 0 | 2 |
| Média | 5 itens | 5 | 0 | 0 |
| Baixa | 4 itens | 2 | 0 | 2 |
| **Total** | **15 itens** | **11** | **0** | **4** |
