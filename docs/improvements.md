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

## Referências

- [React Dashboard: The Complete 2026 Guide](https://www.usedatabrain.com/how-to/create-react-dashboard)
- [Dashboard Design Principles (UXPin, 2026)](https://www.uxpin.com/studio/blog/dashboard-design-principles/)
- [UX Strategies for Real-Time Dashboards (Smashing Magazine)](https://www.smashingmagazine.com/2025/09/ux-strategies-real-time-dashboards/)
- [Shadcn UI Best Practices for 2026](https://medium.com/write-a-catalyst/shadcn-ui-best-practices-for-2026-444efd204f44)
- [Effective Dashboard Design (DataCamp)](https://www.datacamp.com/tutorial/dashboard-design-tutorial)
