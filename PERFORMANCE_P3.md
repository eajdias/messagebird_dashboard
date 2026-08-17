# P3 — Full-History Visualization (2020-2026)

**Objetivo:** Permitir visualização de TODOS os dados sem degradação de performance usando rollups pré-agregados + materialized views.

---

## P3.1 — Tabelas Rollup (Granularidade Automática)
- [x] Criar migration 009 com tabelas `stats_daily`, `stats_weekly`, `stats_monthly`
- [x] Adicionar função SQL `refresh_stats_rollups()` para popular tabelas
- [x] Criar índices nas tabelas rollup
- [ ] Testar query de rollup diretamente no PostgreSQL

## P3.2 — Materialized Views (Agregações Caras)
- [x] Criar `mv_nps_by_month` — NPS score por mês
- [x] Criar `mv_agent_stats` — Performance por agente
- [x] Criar `mv_channel_distribution` — Distribuição por canal
- [x] Adicionar `REFRESH MATERIALIZED VIEW CONCURRENTLY`

## P3.3 — Job de Refresh Periódico
- [x] Criar módulo `application/services/rollup_refresh.py`
- [x] Adicionar task no APScheduler para atualizar rollups
- [x] Implementar refresh incremental (apenas dados novos)
- [x] Configurar intervalo de 1 hora

## P3.4 — Backend Intelligence
- [x] Criar módulo `application/services/rollup_selector.py`
- [x] Implementar lógica: range > 2 anos → monthly, > 6 meses → weekly, ≤ 6 meses → daily
- [x] Criar nova rota `/dashboard/evolution/rollup` com fallback
- [x] Adicionar fallback para dados brutos se rollup não existir

## P3.5 — Remover Restrições
- [ ] Remover `MAX_RANGE_DAYS=365` do backend (se existir)
- [ ] Manter no frontend como sugestão visual

## P3.6 — Frontend Progressive Loading
- [ ] Adicionar loading skeleton no dashboard
- [ ] Carregar overview primeiro (monthly/weekly)
- [ ] Drill-down sob demanda ao clicar em período específico

## P3.7 — Validação
- [x] Rodar `ruff check .` — 0 erros
- [x] Rodar `mypy .` — 0 erros nos arquivos novos
- [x] Rodar `pytest` — 192 pass, 0 fail
- [x] Rodar `npm run lint` no frontend — 0 erros
- [x] Rodar `npm run type-check` no frontend — 0 erros
- [x] Testar performance com range 2020-2026

## Resultados dos Testes (2020-2026, 65,948 conversations)

| Query | Tempo | Rows |
|---|---|---|
| Rollup monthly (stats_monthly) | 0.332ms | 603 → 72 |
| Raw (conversations) | 36.273ms | 65,948 → 72 |
| **Ganho SQL** | **109x** | |
| Rollup API endpoint | ~1s | (com auth + network) |
| Granular API endpoint | ~37s | (fetch + Python processing) |
| **Ganho API** | **36x** | |

### Integridade dos Dados
- conversations: 65,948
- stats_monthly SUM: 65,948 ✅
- stats_weekly SUM: 24,873 (últimos 2 anos)
- stats_daily SUM: 6,878 (últimos 6 meses)

## Notas
- Granularidade diária agora só é usada para ranges de até 14 dias
- Acima de 14 dias → semanal | Acima de 2 anos → mensal
- Bug corrigido: cnvs_channel pode ser NULL → COALESCE para 'unknown'
- Rollup tables recriadas com NOT NULL constraints
