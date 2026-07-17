# tests/ — Testes

> **Mandato:** Garantir que domain/, application/ e infrastructure/ funcionam corretamente.

---

## 🏗️ Estrutura

```
tests/
├── __init__.py
├── conftest.py                  # Fixtures compartilhadas
├── domain/
│   ├── __init__.py
│   ├── test_logic.py            # Testes de domain/logic.py
│   ├── test_dept_routing.py     # Testes de department routing
│   └── services/
│       ├── __init__.py
│       ├── test_metrics_calculator.py
│       └── test_annual_aggregation.py
├── application/
│   ├── __init__.py
│   └── use_cases/
│       ├── __init__.py
│       └── test_generate_report.py
├── infrastructure/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── test_postgres_repository.py
│   └── exporters/
│       ├── __init__.py
│       ├── test_exporter_style.py
│       └── test_metrics_cache.py
└── integration/
    ├── __init__.py
    ├── test_report_flow.py      # Teste ponta a ponta
    └── test_sync_flow.py        # Teste de sincronização
```

---

## 📐 Regras

### Tipos de Teste
- **Unitários** (`domain/`, `application/`): Rápidos, sem I/O
- **Integração** (`integration/`): Usam banco real (PostgreSQL de teste)
- **Snapshot** (`exporters/`): Verificam formatação Excel/PDF

### Fixtures
- Usar `conftest.py` para fixtures compartilhadas
- Banco de teste: PostgreSQL em container ou SQLite temporário
- Dados de teste: fixtures com conversas simuladas

### Mocking
- Mockar apenas `infrastructure/` (APIs externas, banco)
- NUNCA mockar `domain/` (testar lógica real)
- Usar `unittest.mock` ou `pytest-mock`

### Cobertura
- Mínimo 80% para `domain/`
- Mínimo 70% para `application/`
- Testes de integração: cobrir fluxos críticos

---

## 🔧 Comandos

```bash
# Todos os testes
pytest -v

# Apenas domain
pytest tests/domain/ -v

# Com cobertura
pytest --cov=domain --cov=application --cov-report=html

# Integração (requer PostgreSQL rodando)
pytest tests/integration/ -v --integration
```

---

## 📝 Exemplo

```python
# tests/domain/test_logic.py
def test_calculate_frt_minutes():
    first_user = "2026-06-01T10:00:00"
    first_agent = "2026-06-01T10:15:00"
    result = calculate_frt_minutes(first_agent, first_user)
    assert result == 15.0

# tests/integration/test_report_flow.py
@pytest.mark.integration
async def test_generate_monthly_report(postgres_db):
    repo = PostgresReportRepository(postgres_db)
    exporter = ExcelExporter()
    use_case = GenerateReportUseCase(repo, exporter)
    await use_case.execute(year=2026, month=6, group="Suporte")
    assert os.path.exists("reports/2026-06_Suporte.xlsx")
```

---

## 🚨 Erros Comuns

1. **Testes lentos**: Isolar testes de integração com `@pytest.mark.integration`
2. **Dados persistentes**: Usar transactions com rollback nos testes
3. **Flaky tests**: Evitar dependência de horário ou dados externos
