# application/ — Orquestração e Use Cases

> **Mandato:** Conectar domain/ com infrastructure/. Orquestrar fluxos, NUNCA implementar lógica de negócio.

---

## 🏗️ Estrutura

```
application/
├── __init__.py
├── interfaces/
│   ├── __init__.py
│   ├── repository.py     # ABC ReportRepository
│   └── exporter.py       # ABC ReportExporter, DashboardDTO
├── use_cases/
│   ├── __init__.py
│   ├── generate_report.py    # GenerateReportUseCase
│   ├── sync_database.py      # SyncDatabaseUseCase
│   └── data_quality_report.py # DataQualityReportUseCase
└── services/
    ├── __init__.py
    ├── report_aggregator.py  # Agrega dados brutos em métricas
    └── sub_aggregators.py    # TemporalAggregator, TopicAggregator
```

---

## 📐 Regras

### Interfaces (ABC)
- Definir contratos em `interfaces/`
- `ReportRepository`: busca dados do banco
- `ReportExporter`: exporta dados (Excel, PDF, Markdown)
- Implementações concretas ficam em `infrastructure/`

### Use Cases
- Cada use case = 1 fluxo de negócio
- Orquestrar: buscar dados → processar → exportar
- NUNCA implementar lógica de cálculo (isso é de `domain/`)
- Usar dependency injection (interfaces, não implementações concretas)

### Services
- `ReportAggregator`: orquestra estratégias de cálculo
- `SubAggregators`: agrupam dados por dimensão (tempo, tópico, rating)
- Delegar cálculos para `domain/services/metrics_calculator.py`

### DashboardDTO
- Objeto de transferência entre application/ e infrastructure/
- Contém todos os dados pré-processados para o dashboard
- Serializável para JSON (respostas da API)

---

## 📝 Exemplo

```python
# application/use_cases/generate_report.py
class GenerateReportUseCase:
    def __init__(self, repository: ReportRepository, exporter: ReportExporter):
        self._repo = repository
        self._exporter = exporter

    async def execute(self, year: int, month: int, group: str):
        # 1. Buscar dados brutos
        raw_data = await self._repo.fetch_raw_data_range(start, end, group)

        # 2. Processar (delegar para domain)
        processed = [self._process(c) for c in raw_data]

        # 3. Exportar
        dto = self._build_dashboard_dto(processed)
        self._exporter.export_executive_dashboard(filename, dto)
```

---

## 🚨 Erros Comuns

1. **Lógica de negócio**: Cálculos ficam em `domain/`, não aqui
2. **Import de infrastructure/**: Apenas via interfaces/ABC
3. **I/O direto**: Use cases não devem acessar banco diretamente (usar repository)
