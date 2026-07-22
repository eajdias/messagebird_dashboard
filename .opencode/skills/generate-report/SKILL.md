---
name: generate-report
description: Gerar relatórios mensais, anuais ou por departamento com métricas BSC. Use quando o usuário pedir para gerar relatório, exportar dados, ou criar dashboard executivo.
---

# Skill: Generate Report

Gera relatórios gerenciáveis em Excel, PDF ou Markdown.

## Pela API

### Gerar relatório mensal
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 6, "type": "monthly", "group": "global"}'
```

### Gerar relatório anual
```bash
curl -X POST http://localhost:8000/api/v1/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "type": "annual", "group": "global"}'
```

### Listar relatórios disponíveis
```bash
curl http://localhost:8000/api/v1/reports/available \
  -H "Authorization: Bearer $TOKEN"
```

## Estrutura de Saída

Os relatórios são salvos em `reports/{report_id}/` com:
- `Dashboard_Executivo_GLOBAL_{data}.xlsx`
- Pastas por departamento com dashboards específicos
- `auditoria/` com planilhas de auditoria e PDFs de OS

## Parâmetros do Relatório

| Parâmetro | Valores | Descrição |
|-----------|---------|-----------|
| type | monthly, annual | Tipo do relatório |
| year | 2026 | Ano |
| month | 1-12 | Mês (opcional para anual) |
| group | global, ou nome do departamento | Grupo |
