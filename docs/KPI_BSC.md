# KPIs e BSC (Balanced Scorecard)

> Sistema de métricas, metas e pontuação para avaliação de desempenho dos agentes.

## Visão Geral

O sistema BSC calcula pontuações mensais para cada agente baseado em múltiplas métricas com pesos configuráveis. O objetivo é avaliar desempenho de forma objetiva e calcular bônus.

## Métricas Principais (Tier 1)

| Métrica | Descrição | Meta | Peso |
|---------|-----------|------|------|
| Elogios / Feedback | % de notas 4-5 sobre total avaliado | >40% | 30 pts |
| NPS | NPS individual ((Promotores - Detratores) / Total × 100) | >=90 | 50 pts |
| Feedback Negativo (Penalidade) | % de notas 1-2 sobre total avaliado | <=5.5% | Penalidade |
| Atendimentos Finalizados | Volume bruto de chats encerrados | 150 | 10 pts |
| Instalações e Migrações | Tickets de instalação/migração finalizados | 10 | 30 pts |
| Assiduidade | 0 faltas/atrasos no mês | 0 | 35 pts |
| Indicação Comercial | Indicações comerciais realizadas | 10 | 50 pts |
| Indicação Comercial Vendida | Vendas por indicação | 10 | 100 pts |
| Updates/Treinamentos/Tarefas | Tarefas gerais do suporte | 50 | 50 pts |

## Métricas Secundárias (Tier 2)

| Métrica | Meta | Peso por unidade |
|---------|------|-----------------|
| Updates | 50 | 1 pt |
| Treinamentos | 50 | 1 pt |
| Tarefa N1 | 50 | 2 pts |
| Tarefa N2 | 50 | 3 pts |
| Tarefa N3 | 50 | 5 pts |

## Penalidades Setoriais

| Penalidade | Descrição | Valor |
|-----------|-----------|-------|
| Ligações Perdidas | Penalidade setorial (não individual) | -2 pts por ligação perdida |

## SLA

- **FRT (First Response Time):** ≤ 60 minutos
- **ART (Average Response Time):** Máximo 480 minutos (8 horas)
- **Duração Máxima de Chat:** 630 minutos (10h30)
- **Reabertura:** Gap de 24h de inatividade para detectar reabertura

## Métricas Calculadas

### NPS (Net Promoter Score)
```
NPS = ((Promotores - Detratores) / Total) × 100
```
- Promotores: nota >= 9
- Neutros: nota 7-8
- Detratores: nota < 7

### SLA Compliance
```
SLA = (Conversas com ART ≤ 60min / Total de conversas) × 100
```

### Tipos de Pontuação BSC

| Tipo | Comportamento | Exemplo |
|------|--------------|---------|
| `escalonado_percentual` | Pontos por faixa + extra por unidade acima da meta | Elogios: 40% = 30pts, cada 1% extra = +0.75pt (cap 50 pts) |
| `escalonado_nps` | Pontos fixos por faixa de NPS | >=90 = 50pts, >=70 = 30pts, >=63 = 15pts, >=50 = 5pts |
| `penalidade_percentual` | Penalidade base + extra por unidade | Feedback negativo: 5.5% = -5pts, cada 1% extra = -5pts |
| `proporcional` | Pontos por unidade até a meta | Instalações: 3 pts por ticket, max 30 pts |
| `binaria` | Tudo ou nada se meta atingida | Assiduidade: 35pts se 0 faltas |

## Configuração

As métricas e metas são configuradas em `business_bsc.yaml` (template em `business_bsc.yaml.example`):

```yaml
kpi_config:
  "Suporte Tecnico":
    t1:
      - name: "Elogios de atendimento / Feedback"
        metric: "% em cima do total de avaliados com nota"
        meta: ">40%"
        peso: 30
        tipo: "escalonado_percentual"
        niveis:
          - { min: 40, pts: 30, extra_per_unit: 0.75 }
          - { min: 35, pts: 15 }
          - { min: 30, pts: 10 }
        cap: 50
```

## Departamentos

| ID | Departamento |
|----|-------------|
| 1 | Suporte Tecnico |
| 2 | Comercial |
| 3 | Financeiro |
| 4 | Ouvidoria |
| 5 | Nova Instalacao / Migracao |

## Canais

| Canal ID | Nome |
|----------|------|
| `3fa4639084614f7e9fbe121dea5a28e5` | WhatsApp |
| `79a46c93-19a2-4eed-8050-beea59b23528` | Templates/Sites |
