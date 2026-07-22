# Melhorias para o Dashboard Gerencial

> Dashboard omnichannel MessageBird — Frontend React + shadcn/ui + Tailwind CSS v4
> Uso principal: gerência da empresa (monitoramento de KPIs, tomada de decisão)

---

## 1. Skeleton Loading States

**Problema:** Spinners genéricos durante carregamento dão sensação de lentidão.

**Solução:** Substituir spinners por skeletons do shadcn/ui (`<Skeleton />`). O layout aparece antes dos dados, reduzindo a percepção de espera.

**Onde aplicar:**
- Cards de KPI na dashboard
- Tabela de conversas
- Gráficos (Recharts)
- Página de relatórios

**Ref:** https://ui.shadcn.com/docs/components/skeleton

---

## 2. KPI Cards com Indicadores de Tendência

**Problema:** KPIs atuais mostram apenas o valor numérico, sem contexto de evolução.

**Solução:** Enriquecer os cards com:
- Setas ▲▼ coloridas (verde/vermelho) para variação percentual
- Mini sparklines (Recharts) dentro do card
- Barra de progresso meta vs. realizado
- Tooltip com detalhes ao hover

**Onde aplicar:** Página inicial (dashboard), todas as métricas do BSC.

**Ref:** https://shadcnblocks.com/block/stats-card1

---

## 3. Date Range Picker com Presets

**Problema:** Relatórios usam selects separados para mês/ano — experiência pouco intuitiva.

**Solução:** Substituir por Date Range Picker com presets rápidos:
- Hoje, Esta Semana, Este Mês, Últimos 30 Dias, Últimos 90 Dias
- Comparação entre dois períodos (ex: esse mês vs mês passado)
- Campos start/end visíveis para customização

**Onde aplicar:** Página de relatórios, filtro de conversas, dashboard.

**Ref:** https://ui.shadcn.com/examples/date-picker-with-range

---

## 4. Export Aprimorado (Excel + PDF)

**Problema:** Export atual apenas CSV — gerência frequentemente precisa de Excel ou PDF.

**Solução:** Adicionar export para:
- **Excel (.xlsx):** usando SheetJS (`xlsx`) no frontend ou openpyxl (já existe no backend)
- **PDF:** usando `jspdf` + `jspdf-autotable` no frontend
- Menu dropdown com as opções (CSV, Excel, PDF)

**Onde aplicar:** página de conversas e relatórios.

**Ref:** https://ui.shadcn.com/blocks/tables-export

---

## 5. Drill-Down nas Métricas

**Problema:** KPIs na dashboard não são clicáveis — gerência precisa navegar para outra página para ver detalhes.

**Solução:** KPIs clicáveis que abrem modal/drawer com detalhes:
- NPS → histórico mensal + comentários associados
- Conversas → distribuição por canal / departamento
- SLA → detalhamento por agente
- BSC → indicadores-filho de cada perspectiva

**Benefício:** Reduz fricção — gestor vê o overview e mergulha nos detalhes sem mudar de tela.

---

## 6. Filtros Globais Persistentes

**Problema:** Cada página tem seu próprio filtro — ao navegar, o contexto se perde.

**Solução:** Barra de filtros global no topo que persiste entre páginas:
- Período (date range)
- Departamento
- Canal
- Agente (quando aplicável)

**Implementação:** Estado global com Zustand (já presente no projeto) ou Context API. Filtros são passados como query params nas chamadas da API.

---

## 7. Cache e Refetch com TanStack Query

**Problema:** Dados são refetchados do zero a cada navegação, sem cache.

**Solução:** Adotar TanStack Query (React Query) para:
- Cache automático de respostas da API
- Refetch em background (dados sempre frescos sem bloquear a UI)
- Deduplication: 2 componentes usando o mesmo endpoint = 1 request
- Stale-while-revalidate: mostra cache imediatamente, atualiza em segundo plano

**Stack ideal 2026:** React 19 + shadcn/ui + TanStack Query + Zustand + Recharts.

**Ref:** https://tanstack.com/query/latest

---

## 8. Empty States Inteligentes

**Problema:** Quando não há dados (ex: sync ainda rodando, período sem conversas), a tela fica vazia ou confusa.

**Solução:** Substituir "nenhum resultado" por estados informativos:
- Ilustração + texto explicativo
- "Sincronização em andamento — últimos dados disponíveis: 14:30"
- CTA para trigger manual de sync (já existe no Settings)
- Sugestão de ação: "Tente selecionar outro período"

---

## 9. Layout Responsivo para Reuniões

**Problema:** Dashboard não adaptado para tablets/projetores — comuns em reuniões de gerência.

**Solução:**
- Sidebar collapsível (shadcn/ui já tem suporte)
- Grid de KPIs adaptativo: 4 colunas desktop → 2 tablet → 1 mobile
- Tabelas com horizontal scroll em telas menores
- Modo "apresentação" sem sidebar (via query param `?presentation=true`)

---

## 10. Página de Comparativo / Tendências

**Problema:** Não é possível comparar períodos lado a lado ou ver tendências de longo prazo.

**Solução:** Nova página ou seção na dashboard com:
- Comparação mês atual vs mês anterior (receita, NPS, conversas)
- Gráfico de tendência dos últimos 12 meses
- Variação percentual em cada KPI
- Projeção baseada em média histórica (simple moving average)

---

## 11. Melhorias na Experiência de Relatórios

**Problema:** Relatório gerado é apenas um status "processing" sem feedback visual.

**Solução:**
- Progress bar durante geração
- Notificação quando o relatório ficar pronto
- Lista de relatórios gerados com download direto
- Preview do relatório antes de exportar

---

## 12. Alertas e Notificações

**Problema:** Gerência precisa monitorar ativamente — não há alertas proativos.

**Solução:**
- Badge no header com contagem de alertas
- Alertas para: SLA estourado, NPS abaixo do threshold, pico de conversas sem resposta
- Toast notifications para eventos importantes
- Indicador visual quando sync falha

**Ref:** shadcn/ui já tem componentes Toast e Badge.

---

## 13. Micro-Interactions e Animações

**Problema:** Dashboard estático — transições bruscas entre páginas, KPIs aparecem instantaneamente sem feedback visual.

**Solução:** Adicionar camada sutil de animação com Framer Motion (Motion):
- **Contadores animados:** valores de KPI incrementam do zero ao valor real (NumberFlow ou `useSpring`)
- **Entrada de gráficos:** Recharts com animação nativa ou `motion.div` wrap
- **Transições de página:** fade + slide entre rotas (Next.js App Router com `layoutRouter` ou `AnimatePresence`)
- **Hover states:** escala sutil em cards, tooltips com delay
- **Loading skeletons:** animação pulse do shadcn/ui

**Onde aplicar:** Dashboard (todos os cards), transições de página, botões.

**Refs:**
- [SmoothUI — Componentes animados para shadcn/ui](https://smoothui.dev/)
- [Animate UI — Biblioteca open-source de componentes animados](https://www.shadcn.io/template/animate-ui-animate-ui)
- [Motion Primitives — UI kit animado](https://allshadcn.com/tools/motion-primitives/)

---

## 14. Data Table Aprimorada (TanStack Table)

**Problema:** Tabela de conversas básica — sem ordenação por coluna, sem controle de visibilidade, sem filtros avançados.

**Solução:** Evoluir para Data Table completa com TanStack Table:
- Ordenação por qualquer coluna (sortable headers)
- Controle de visibilidade (mostrar/esconder colunas via dropdown)
- Filtros faceted (categoria, status, departamento como checkboxes)
- Coluna de ações (visualizar, exportar linha)
- Resize de colunas
- Row selection + ações em lote
- Paginação com número de registros por página configurável

**Onde aplicar:** Página de conversas, relatórios, agentes.

**Ref:** https://ui.shadcn.com/docs/components/data-table

---

## 15. Command Palette (Cmd+K)

**Problema:** Gerência precisa navegar entre páginas via menu — fluxo lento para usuários avançados.

**Solução:** Adicionar paleta de comandos global com `Cmd+K`:
- Navegação rápida entre páginas (dashboard, conversas, relatórios, settings)
- Atalhos para ações comuns (exportar relatório, sync, nova conversa)
- Busca fuzzy (já incluso no cmdk)
- Atalhos de teclado visíveis (`KBD` components)

**Onde aplicar:** Global — acionado por `Cmd+K` de qualquer página.

**Refs:**
- https://ui.shadcn.com/docs/components/command
- https://www.shadcn.io/blocks/sidebar-with-command-menu

---

## 16. Bento Grid Layout

**Problema:** Layout da dashboard é uma grade homogênea — todos os cards têm o mesmo tamanho, sem hierarquia visual.

**Solução:** Adotar Bento Grid — layout assimétrico com tiles de tamanhos variados:
- Card principal (2x1) para KPI mais importante (ex: NPS ou Receita)
- Cards médios (1x1) para métricas secundárias
- Card largo (2x1) para gráfico de evolução
- Cards compactos para indicadores de tendência
- Hierarquia visual guia o olhar do gestor para o que importa primeiro

**Onde aplicar:** Página inicial da dashboard.

**Refs:**
- [Guia completo Bento Grid Dashboard (2026)](https://www.orbix.studio/blogs/bento-grid-dashboard-design-aesthetics)
- [shadcn Bento Grid blocks](https://shadcnstudio.com/blocks/bento-grid/bento-grid)

---

## 17. Sparklines e Mini Gráficos nos KPIs

**Problema:** KPIs mostram apenas o valor atual — não é possível ver a tendência sem olhar o gráfico separado.

**Solução:** Adicionar sparklines (mini gráficos de linha/área) dentro de cada KPI Card:
- Mini AreaChart (64px altura) com gradiente
- Últimos 30 dias de evolução
- Indicador de direção com cor (verde ↗ / vermelho ↘)
- Tooltip no hover com valores

**Onde aplicar:** Todos os KPI Cards na dashboard.

**Refs:**
- [shadcn Sparkline Card](https://www.shadcn.io/blocks/stats-sparkline)
- [shadcn Sparkline Table](https://www.shadcn.io/blocks/tables-sparkline)
- [MetricUI — KPI Cards completos](https://www.metricui.com/)

---

## 18. Central de Notificações

**Problema:** Não há um local centralizado para o gestor ver alertas e eventos importantes.

**Solução:** Implementar notificação in-app com:
- **Ícone de sino** no header com badge de não-lidas
- **Dropdown** com as últimas notificações
- **Tipos:** SLA estourado, NPS abaixo do threshold, sync concluída, relatório pronto
- **Toast** (sonner/react-hot-toast) para notificações efêmeras
- Notificações lidas vs não-lidas com persistência local

**Onde aplicar:** Header global + integração com backend de eventos.

**Refs:**
- [Sonner — Toast library para React](https://knock.app/blog/the-top-notification-libraries-for-react)
- shadcn/ui tem Badge, DropdownMenu, Sheet

---

## 19. Acessibilidade (A11y)

**Problema:** Dashboard pode não atender WCAG 2.1 AA — contraste, navegação por teclado, leitores de tela.

**Solução:** Garantir conformidade com:
- **Contraste de cor:** mínimo 4.5:1 para texto normal (usar ferramentas como axe DevTools, Lighthouse)
- **Navegação por teclado:** Tab order lógico, skip links, foco visível
- **ARIA labels:** em todos os componentes interativos
- **Textos alternativos:** em gráficos e ícones
- **Testes automatizados:** `jest-axe` ou `vitest-axe` nos componentes críticos
- **Zoom 200%:** layout não quebra com zoom

**Impacto:** Empresas exigem conformidade WCAG para onboarding de fornecedores (60% até 2027).

**Refs:**
- [Complete Accessibility Checklist 2026](https://www.gitnexa.com/blogs/web-accessibility-checklist)
- [React Accessibility Best Practices](https://rtcamp.com/handbook/react-best-practices/accessibility/)
- [WCAG Color Contrast Guide 2026](https://www.webability.io/blog/color-contrast-for-accessibility)

---

## 20. Design Tokens e Temas Customizados

**Problema:** Tema atual usa cores padrão do shadcn/ui — sem identidade visual da empresa.

**Solução:** Implementar sistema de design tokens:
- Paleta de cores baseada na marca (primary, secondary, accent customizados)
- Tipografia definida (font family para headings e body)
- Escala de raio (border-radius) consistente
- Sombras e elevation tokens
- **TweakCN** ou **Shadcn Studio** para gerar tema visualmente
- Suporte a white-label (múltiplos tenants com cores diferentes)

**Onde aplicar:** Global — CSS variables em `globals.css`.

**Refs:**
- [TweakCN — Theme Generator](https://tweakcn.com/)
- [shadcn/ui Theming docs](https://ui.shadcn.com/docs/theming)
- [8 Best shadcn/ui Themes 2026](https://adminlte.io/blog/shadcn-ui-themes/)

---

## 21. Visualizações Salvas (Saved Views)

**Problema:** Gestor aplica filtros toda vez que acessa o dashboard — não há como salvar uma configuração de visualização.

**Solução:** Permitir salvar visualizações com:
- Botão "Salvar visualização" com nome customizado
- Persistência em localStorage (Zustand + persist middleware)
- Combinação de: período, departamento, canais, colunas visíveis
- Visualização "default" que carrega ao abrir o dashboard
- Compartilhável via URL (filtros como query params)

**Onde aplicar:** Dashboard, página de conversas, relatórios.

**Refs:**
- [Zustand persist middleware](https://dev.to/finalgirl321/getting-started-with-zustand-state-management-for-react-5786)
- URL state com `useSearchParams`

---

## 22. Onboarding / Product Tour

**Problema:** Novos usuários da gerência não conhecem todas as funcionalidades do dashboard.

**Solução:** Adicionar tour guiado com React Joyride:
- Tour de boas-vindas na primeira vez que o gestor acessa
- Passos destacando: KPIs, gráficos, filtros, export, relatórios, settings
- Botão "Iniciar Tour" no header (acessível a qualquer momento)
- Tooltips com explicação do que cada seção faz
- Progresso do tour visível

**Onde aplicar:** Dashboard — acionado no primeiro login ou manualmente.

**Ref:** https://react-joyride.com/

---

## 23. Transições de Página

**Problema:** Navegação entre páginas é instantânea e seca — sem continuidade visual.

**Solução:** Adicionar transições suaves entre rotas:
- Fade in/out entre páginas
- Slide lateral para navegação entre seções irmãs
- Layout compartilhado preserva sidebar e header durante transição
- Usar Next.js App Router + CSS transitions ou Motion `AnimatePresence`

**Onde aplicar:** Global — transições entre todas as páginas do dashboard.

**Refs:**
- [Motion (Framer Motion) para Next.js](https://www.shadcn.io/prompts/react-animation)
- [shadcn + Framer Motion guide](https://shadcnstudio.com/blog/shadcn-framer-motion/)

---

## 24. Performance e Code Splitting

**Problema:** Todo o bundle do dashboard é carregado de uma vez — páginas não visitadas também são baixadas.

**Solução:** Otimizar performance com:
- **Code splitting:** Next.js App Router já faz lazy loading por rota — garantir que está ativo
- **Dynamic imports:** componentes pesados (chart, tabelas) carregados sob demanda
- **Bundle analysis:** usar `@next/bundle-analyzer` para identificar oportunidades
- **Image optimization:** Next.js `<Image>` com lazy loading nativo
- **Recharts selective imports:** evitar `import * as Recharts` (135 KB gzipped) — importar só o necessário
- **Prefetch inteligente:** links visíveis na viewport têm prefetch; links fora não

**Impacto:** Reduz bundle inicial e melhora Lighthouse Performance score.

**Refs:**
- [React Dashboard Performance Guide](https://www.usedatabrain.com/blog/react-chart-libraries)
- Next.js App Router lazy loading (documentação oficial)

---

## 25. Keyboard Shortcuts para Power Users

**Problema:** Gestores que usam o dashboard diariamente precisam de atalhos de teclado para ações frequentes.

**Solução:** Implementar atalhos de teclado com indicação visual:
- `G D` → Go to Dashboard
- `G C` → Go to Conversas
- `G R` → Go to Relatórios
- `G S` → Go to Settings
- `E` → Export current view
- `R` → Refresh data
- `/` → Focus search
- `Cmd+K` → Command palette

**Onde aplicar:** Global — hints visuais com componente `<Kbd>` do shadcn/ui.

**Refs:**
- [shadcn KBD examples](https://shadcnspace.com/components/kbd)
- [shadcn Command palette](https://ui.shadcn.com/docs/components/command)

---

## Priorização Sugerida

| Prioridade | Item | Esforço | Impacto |
|------------|------|---------|---------|
| Alta | 13. Micro-interactions e Animações | Médio | Alto |
| Alta | 14. Data Table Aprimorada | Médio | Alto |
| Alta | 19. Acessibilidade (A11y) | Médio | Alto |
| Alta | 24. Performance | Baixo | Alto |
| Média | 15. Command Palette | Baixo | Médio |
| Média | 16. Bento Grid | Médio | Alto |
| Média | 17. Sparklines | Médio | Alto |
| Média | 20. Design Tokens | Baixo | Médio |
| Média | 21. Saved Views | Médio | Médio |
| Baixa | 18. Notificações | Alto | Médio |
| Baixa | 22. Product Tour | Baixo | Baixo |
| Baixa | 23. Page Transitions | Baixo | Baixo |
| Baixa | 25. Keyboard Shortcuts | Baixo | Médio |

---

## Referências

- [React Dashboard: The Complete 2026 Guide](https://www.usedatabrain.com/how-to/create-react-dashboard)
- [Dashboard Design Principles (UXPin, 2026)](https://www.uxpin.com/studio/blog/dashboard-design-principles/)
- [UX Strategies for Real-Time Dashboards (Smashing Magazine)](https://www.smashingmagazine.com/2025/09/ux-strategies-real-time-dashboards/)
- [Shadcn UI Best Practices for 2026](https://medium.com/write-a-catalyst/shadcn-ui-best-practices-for-2026-444efd204f44)
- [Effective Dashboard Design (DataCamp)](https://www.datacamp.com/tutorial/dashboard-design-tutorial)
- [The Ultimate shadcn/ui Handbook (2026 Edition)](https://shadcnspace.com/blog/shadcn-ui-handbook)
- [18 Best Next.js 16 Admin Dashboards With shadcn/ui (2026)](https://adminlte.io/blog/build-admin-dashboard-shadcn-nextjs/)
- [20 Best shadcn/ui Projects and Examples (2026)](https://www.shadcndeck.com/blog/shadcn-ui-projects-examples-2026)
- [Best React Chart Libraries 2026](https://blog.logrocket.com/best-react-chart-libraries-2026/)
- [Bento Grid Dashboard Design Guide 2026](https://www.orbix.studio/blogs/bento-grid-dashboard-design-aesthetics)
- [Complete Accessibility Checklist 2026](https://www.gitnexa.com/blogs/web-accessibility-checklist)
- [React Joyride — Product Tour Library](https://react-joyride.com/)
