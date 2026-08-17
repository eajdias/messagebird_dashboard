# Testes

> Padrões, estrutura e comandos para testes.

## Stack de Testes

- **Framework:** Pytest >=8.0.0
- **Async:** pytest-asyncio (asyncio_mode = auto)
- **Coverage:** pytest-cov
- **HTTP Mocking:** respx (para mockar httpx)

## Estrutura

```
tests/
├── conftest.py                  # Fixtures globais (event_loop, mock_db, samples)
├── test_health.py               # Health check test
├── api/                         # Testes de rota
│   ├── conftest.py              # Fixtures da API (test client)
│   ├── test_auth.py
│   ├── test_admin.py
│   ├── test_dashboard.py
│   ├── test_reports.py
│   └── test_conversations.py
├── domain/                      # Testes de domínio
│   ├── test_logic.py
│   ├── test_dept_routing.py
│   └── services/
│       ├── test_metrics_calculator.py
│       └── test_annual_aggregation.py
├── application/                 # Testes de aplicação
│   └── __init__.py              # (vazio — testes a serem escritos)
├── infrastructure/              # Testes de infraestrutura
│   ├── test_client.py
│   ├── test_pg_sync_engine.py
│   ├── test_sync_contacts.py
│   ├── test_sync_messages.py
│   ├── test_sync_surveys.py
│   └── test_sync_integration.py
├── exporters/                   # Testes de exportadores
│   ├── test_metrics_cache.py
│   ├── test_metrics_cache_annual.py
│   └── test_exporter_style.py
└── integration/                 # Testes de integração
    ├── test_report_flow.py
    └── test_dept_routing_flow.py
```

## Comandos

```bash
# Rodar todos os testes
pytest

# Rodar com coverage
pytest --cov

# Pular testes de integração
pytest -m 'not integration'

# Rodar apenas testes de integração
pytest -m integration

# Rodar testes de um diretório específico
pytest tests/api/
pytest tests/domain/
pytest tests/infrastructure/
pytest tests/exporters/
pytest tests/integration/
```

## Fixtures Compartilhadas

Em `tests/conftest.py`:
- `event_loop` — Loop assíncrono para testes
- `mock_db` — Pool de conexão mockado
- `sample_conversation` — RawConversationData de exemplo
- `sample_metrics` — Métricas processadas de exemplo

## Padrões de Teste

- **Testes de API:** Usam TestClient do FastAPI com autenticação mockada
- **Testes de Domínio:** Testam cálculos puros (NPS, ART, SLA, FRT, duração)
- **Testes de Infraestrutura:** Usam respx para mockar chamadas HTTP à MessageBird
- **Testes de Integração:** Validam fluxos completos (sync → report → export)

## Markers Customizados

- `integration` — Testes que dependem de múltiplos componentes. Pular com `-m 'not integration'` para testes rápidos.

## Cobertura

Recomendado:
- Manter cobertura acima de 80% nas camadas domain e application
- Testes de integração para fluxos críticos (sync + report)
- Testes de API para todas as rotas
