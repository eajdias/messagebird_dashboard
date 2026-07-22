# Checklist de Melhorias — Frontend Dashboard

> Acompanhamento da implementação das melhorias propostas em [improvements.md](improvements.md)
> Legenda: ✅ Concluído | 🔄 Em andamento | ⏳ Pendente | ❌ Cancelado

---

## Alta Prioridade

### 13. Micro-Interactions e Animações
**Esforço:** Médio | **Impacto:** Alto

- [ ] Animar contadores de KPI (NumberFlow / useSpring)
- [ ] Animação de entrada nos gráficos Recharts
- [ ] Hover states com escala sutil nos cards
- [ ] Loading skeletons com animação pulse
- [ ] Transições de página (fade/slide)

### 14. Data Table Aprimorada (TanStack Table)
**Esforço:** Médio | **Impacto:** Alto

- [ ] Ordenação por coluna (sortable headers)
- [ ] Controle de visibilidade de colunas (dropdown)
- [ ] Filtros faceted (categoria, status, departamento)
- [ ] Coluna de ações por linha
- [ ] Paginação com registros por página configurável
- [ ] Row selection + ações em lote
- [ ] Resize de colunas

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

- [ ] Redesenhar layout da dashboard como bento grid
- [ ] Card principal 2x1 para KPI mais importante
- [ ] Cards médios 1x1 para métricas secundárias
- [ ] Card largo 2x1 para gráfico de evolução
- [ ] Responsivo: adaptar grid para tablet/mobile

### 17. Sparklines nos KPIs
**Esforço:** Médio | **Impacto:** Alto

- [ ] Mini AreaChart (64px) em cada KPI Card
- [ ] Gradiente de cor por tendência (verde/vermelho)
- [ ] Tooltip no hover com valores
- [ ] Dados dos últimos 30 dias

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

- [ ] Fade in/out entre páginas
- [ ] Slide lateral para navegação entre seções
- [ ] AnimatePresence com Motion

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
| Alta | 4 itens | 1 | 0 | 3 |
| Média | 5 itens | 2 | 0 | 3 |
| Baixa | 4 itens | 1 | 0 | 3 |
| **Total** | **13 itens** | **4** | **0** | **9** |
