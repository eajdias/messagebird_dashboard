# Roadmap

> Visão geral do projeto, funcionalidades implementadas e próximos passos.

## Propósito

O MessageBird Dashboard é uma ferramenta de relatórios omnichannel que conecta-se à API MessageBird (Bird) para sincronizar conversas, mensagens, contatos e pesquisas NPS em um banco PostgreSQL, fornecendo um dashboard rico e sistema de relatórios para métricas de atendimento ao cliente.

**Público-alvo:** Equipes de suporte (Suporte Técnico, Comercial, Financeiro, Ouvidoria) que usam Bird para atendimento via WhatsApp e Webchat.

## Funcionalidades Implementadas

### Backend ✅
- [x] Sincronização completa de contacts, conversations, messages e surveys via API Bird
- [x] Pipeline de sync com modos incremental, full, mensal e backfill
- [x] Scheduler APScheduler com perfis configuráveis (debug a monthly)
- [x] Cálculo de métricas: NPS, ART, FRT, SLA, duração, ratings
- [x] BSC (Balanced Scorecard) com sistema de pontuação por agente
- [x] Geração de relatórios Excel, PDF e Markdown
- [x] Relatórios mensais, anuais e por departamento
- [x] Auditoria de chats, contatos, demanda e ordens de serviço
- [x] Autenticação JWT
- [x] Materialized view para performance de queries
- [x] Cache de métricas em disco
- [x] Testes automatizados (pytest) em todas as camadas

### Frontend ✅
- [x] Dashboard com KPIs, evolução mensal, ranking de agentes, canais
- [x] Tabela BSC interativa
- [x] Lista e detalhe de conversas com mensagens
- [x] Geração e download de relatórios
- [x] Tema dark/light mode
- [x] Animações e micro-interações (framer-motion)
- [x] Sparklines nos cards de KPI
- [x] Command palette com atalhos de teclado
- [x] Responsivo com sidebar drawer em mobile
- [x] Empty states, loading skeletons, notificações toast
- [x] Paginação, filtros e ordenação em tabelas
- [x] Login com JWT

## Próximos Passos

### Curto Prazo


### Médio Prazo


### Longo Prazo


## Decisões Técnicas

- **Clean Architecture** para separação clara de responsabilidades e testabilidade
- **Async/await** em toda a stack (asyncpg, httpx, FastAPI)
- **Materialized View** para performance em dashboards com grandes volumes
- **APScheduler in-process** por simplicidade operacional (sem dependência externa)
- **Excel como formato principal** de relatório por ser o mais usado pelo cliente final
