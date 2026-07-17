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
│   ├── connection.py         # DatabaseConnection (SQLite, legado)
│   ├── sync_connection.py    # SyncConnection (SQLite bulk, legado)
│   ├── init_db.py            # Schema creation (SQLite)
│   ├── queries.py            # SQL queries (SQLite)
│   ├── sqlite_repository.py  # Implementação SQLite (legado)
│   └── migrations/
│       ├── __init__.py
│       ├── 001_initial.sql   # Schema SQL puro
│       └── models.py         # SQLAlchemy models (para Alembic)
├── repositories/
│   ├── __init__.py
│   └── postgres_report_repository.py  # Implementação PostgreSQL (asyncpg)
├── api/
│   ├── __init__.py
│   ├── client.py             # MessageBird API client (httpx)
│   ├── config.py             # API config (keys, timeouts)
│   └── sync.py               # Sync pipeline (1253 loc)
├── exporters/
│   ├── __init__.py
│   ├── excel_exporter.py     # Exportação Excel (xlsxwriter)
│   ├── pdf_exporter.py       # Exportação PDF (fpdf2)
│   ├── markdown_exporter.py  # Exportação Markdown
│   ├── metrics_cache.py      # Cache de métricas
│   └── mappers/
│       ├── __init__.py
│       └── _bsc_writer.py    # Fórmulas Excel BSC
└── sync/                     # (reservado para sync engine async)
    └── __init__.py
```

---

## 📐 Regras

### Database
- `PostgresRepository` implementa `ReportRepository` ABC
- Queries ficam em `queries.py` (não inline no repository)
- Usar `asyncpg` para PostgreSQL (async)
- WAL mode para SQLite (sync)
- Migrations com Alembic

### API Client
- `MessageBirdClient` usa `httpx.AsyncClient`
- Autenticação via header `Authorization: AccessKey`
- Retry automático com backoff exponencial
- Rate limiting: máximo 10 requests/segundo
- Timeout: 30 segundos (configurável)

### Sync Pipeline
- `SyncManager` orquestra contacts → conversations → messages
- Modos: incremental, full, backfill-surveys
- Progress bars com `rich`
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

## 📝 Exemplo

```python
# infrastructure/database/postgres_repository.py
class PostgresReportRepository(ReportRepository):
    def __init__(self, db: PostgresConnection):
        self.db = db

    async def fetch_raw_data_range(self, start_date: str, end_date: str) -> List[RawConversationData]:
        rows = await self.db.fetch_all(queries.SURVEY_DATA, (start_date, end_date))
        return [self._to_raw(r) for r in rows]

# infrastructure/api/client.py
class MessageBirdClient:
    def __init__(self, api_key: str):
        self._client = httpx.AsyncClient(
            base_url="https://conversations.messagebird.com/v1",
            headers={"Authorization": f"AccessKey {api_key}"},
            timeout=30.0
        )

    async def list_conversations(self, **params):
        response = await self._client.get("/conversations", params=params)
        response.raise_for_status()
        return response.json()
```

---

## 🚨 Erros Comuns

1. **Lógica de negócio**: Implementações são técnicas, não inteligentes
2. **SQL inline**: Todas as queries ficam em `queries.py`
3. **Sem tratamento de erro**: API client deve tratar HTTPStatusError
4. **Hardcoded config**: Usar variáveis de ambiente ou config_loader
