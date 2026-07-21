# infrastructure/ — Detalhes Técnicos

> **Mandato:** Implementar as interfaces definidas em `application/interfaces/`. Concretizar persistência, APIs externas e exportação.

---

## 🏗️ Estrutura

```
infrastructure/
├── __init__.py
├── config/
│   ├── __init__.py
│   └── config_loader.py      # Carrega business_config.yaml / business_bsc.yaml
├── database/
│   ├── __init__.py
│   ├── postgres_connection.py # PostgresPool (asyncpg)
│   ├── sync_connection_pg.py  # PostgresSyncConnection (bulk)
│   ├── queries_pg.py          # SQL queries (PostgreSQL)
│   └── migrations/
│       ├── __init__.py
│       └── 001_initial.sql   # Schema SQL puro (aplicado automaticamente via _init_schema)
├── repositories/
│   ├── __init__.py
│   └── postgres_report_repository.py  # Implementação PostgreSQL (asyncpg)
├── api/
│   ├── __init__.py
│   ├── client.py             # MessageBird API client (httpx)
│   └── config.py             # API config (keys, timeouts)
├── sync/
│   ├── __init__.py
│   └── pg_sync_engine.py     # Sync engine PostgreSQL (asyncpg)
└── exporters/
    ├── __init__.py
    ├── excel_exporter.py     # Exportação Excel (xlsxwriter)
    ├── pdf_exporter.py       # Exportação PDF (fpdf2)
    ├── markdown_exporter.py  # Exportação Markdown
    ├── metrics_cache.py      # Cache de métricas
    └── mappers/
        ├── __init__.py
        └── _bsc_writer.py    # Fórmulas Excel BSC
```

---

## 📐 Regras

### Database
- `PostgresReportRepository` implementa `ReportRepository` ABC
- Queries ficam em `queries_pg.py` (não inline no repository)
- Usar `asyncpg` para PostgreSQL (async)

### API Client
- `MessageBirdClient` usa `httpx.AsyncClient`
- Autenticação via header `Authorization: AccessKey`
- Retry automático com backoff exponencial
- Rate limiting: máximo 10 requests/segundo
- Timeout: 30 segundos (configurável)

### Sync Pipeline
- `PgSyncManager` orquestra contacts → conversations → messages
- Modos: incremental, full, backfill-surveys
- Erros salvos em `sync_errors` table

### Exporters
- `ExcelExporter` implementa `ReportExporter` ABC
- `PDFOsExporter` para Ordens de Serviço
- `MarkdownExporter` para resumos
- Formatação profissional com cores condicionais

### Config Loader
- Carrega `business_config.yaml` e `business_bsc.yaml`
- Cache em memória (recarregar apenas em dev)
- Tipagem com dataclasses

---

## 🚨 Erros Comuns

1. **Lógica de negócio**: Implementações são técnicas, não inteligentes
2. **SQL inline**: Todas as queries ficam em `queries_pg.py`
3. **Sem tratamento de erro**: API client deve tratar HTTPStatusError
4. **Hardcoded config**: Usar variáveis de ambiente ou config_loader

