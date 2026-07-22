# Sistema de Relatórios

> Geração de relatórios gerenciais em Excel, PDF e Markdown.

## Visão Geral

Relatórios são gerados sob demanda via API e salvos em disco. O sistema suporta múltiplos formatos e tipos de relatório.

## Tipos de Relatório

| Tipo | Formato | Descrição |
|------|---------|-----------|
| **Dashboard Executivo** | Excel (.xlsx) | Relatório principal com métricas por agente, departamento e grupo |
| **Ordem de Serviço** | PDF (.pdf) | OS individual por atendimento |
| **Resumo** | Markdown (.md) | Resumo textual das métricas |

## Estrutura de Geração

```
ReportRequest (API)
    │
    ▼
GenerateReportUseCase
    │
    ├──▶ ReportAggregator (processa dados)
    │       │
    │       ├── aggregate_statistics()
    │       ├── aggregate_dashboard() → DashboardDTO
    │       └── build_excel_rows()
    │
    ├──▶ PostgresReportRepository (busca dados)
    │
    └──▶ ExcelExporter (gera arquivo)
            │
            └──▶ reports/{report_id}/
                    ├── Dashboard_Executivo_GLOBAL_*.xlsx
                    ├── {Departamento}/
                    │   └── Dashboard_Executivo_{Dept}_*.xlsx
                    └── auditoria/
                        ├── auditoria_*.xlsx
                        └── ordens_servico_*.pdf
```

## Arquivos Gerados

Para cada relatório, são gerados:

1. **Dashboard Global** — Métricas consolidadas de todos os departamentos
2. **Dashboard por Departamento** — Um arquivo por departamento (Suporte Técnico, Comercial, Financeiro, Ouvidoria)
3. **Planilhas de Auditoria** — Auditoria de chats, contatos, demanda e ordens de serviço
4. **PDFs de OS** — Uma ordem de serviço em PDF por conversa

## DashboardDTO

O `DashboardDTO` contém todos os dados necessários para a planilha:

- `general_metrics` — Métricas gerais (total chats, NPS, SLA, ART, etc.)
- `nps_distribution` / `rating_distribution` — Distribuições
- `heatmap_data` — Heatmap temporal
- `topic_data` / `occurrence_data` — Motivos e ocorrências
- `bsc_header` / `bsc_data_t1/t2` — Dados BSC por agente
- `tabular_header` / `tabular_data` — Tabela de agentes
- `department_header` / `department_data` — Tabela de departamentos
- `dow_data` — Análise por dia da semana
- `agent_rating_detail` / `agent_nps_detail` — Detalhamento por agente

## Relatório Anual

O relatório anual (`AnnualReportUseCase`) agrega dados mês a mês com:

- Total de chats e mensagens
- ART médio, SLA compliance, duração média
- NPS Real e Nota Técnica Média
- Elogios e feedbacks negativos
- Clientes únicos e retornantes

## Cache de Métricas

- Métricas computadas são cacheadas em `reports/_metrics_cache.json`
- Cache evita recálculo para mesmos períodos
- `MetricsCache` em `infrastructure/exporters/metrics_cache.py`

## Manifesto

Relatórios gerados são registrados em `reports/manifest.json`:

```json
[
  {
    "report_id": "a34b17ab",
    "type": "monthly",
    "year": 2026,
    "month": 6,
    "group": "global",
    "path": "reports/a34b17ab",
    "created_at": "2026-07-22T10:00:00"
  }
]
```

## Exporters

| Exporter | Arquivo | Tecnologia |
|----------|---------|-----------|
| Excel | `excel_exporter.py` | xlsxwriter |
| PDF | `pdf_exporter.py` | fpdf2 |
| Markdown | `markdown_exporter.py` | — |
| BSC Writer | `mappers/_bsc_writer.py` | Fórmulas Excel para BSC |

## Convenções

- Nomes de arquivo: `Dashboard_Executivo_{TIPO}_{DATA}.xlsx`
- Relatórios mensais: pasta com formato `{report_id}/{YYYYMMDD}_{YYYYMMDD}/`
- Relatórios anuais: pasta `{report_id}/{YYYY}/`
