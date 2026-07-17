# domain/ — Lógica de Negócio

> **Mandato:** Este é o coração do sistema. ZERO dependências externas. Apenas lógica pura.

---

## 🏗️ Estrutura

```
domain/
├── __init__.py
├── constants.py          # Mapas de configuração (DEPT_MAP, REASON_MAP, etc.)
├── logic.py              # Funções puras de cálculo (FRT, ART, duração)
├── entities/
│   ├── __init__.py
│   └── report_data.py    # Dataclasses: RawConversationData, ProcessedReportData
└── services/
    ├── __init__.py
    └── metrics_calculator.py  # NPS, SLA, scoring BSC
```

---

## 📐 Regras

### Dependências
- **ZERO imports** de `infrastructure/`, `application/`, `api/`, ou qualquer lib externa
- Apenas `dataclasses`, `typing`, `enum`, `datetime` (stdlib Python)
- Exceção: `pyyaml` pode ser usada para carregar config YAML

### Entidades
- Usar `@dataclass` para todas as entidades
- NUNCA usar classes com estado mutável
- Entidades são imutáveis após criação

### Funções
- Funções puras: mesma entrada → mesmo resultado
- NUNCA acessar banco de dados, APIs, ou filesystem
- NUNCA fazer I/O (print, logging, network)
- Cálculos matemáticos puros

### Services
- `MetricsCalculator` encapsula regras de negócio complexas
- NUNCA depender de repositórios ou external services
- Retornar valores primitivos ou dataclasses

---

## 📝 Exemplo

```python
# domain/logic.py
def calculate_frt_minutes(first_agent_msg: str, first_user_msg: str) -> float:
    """Calcula First Response Time em minutos."""
    t1 = parse_datetime(first_user_msg)
    t2 = parse_datetime(first_agent_msg)
    return (t2 - t1).total_seconds() / 60

# domain/entities/report_data.py
@dataclass
class RawConversationData:
    id: str
    contact: str
    phone: str
    msgs: List[RawMessageData] = field(default_factory=list)
    rating: Optional[float] = None
    nps: Optional[float] = None
```

---

## 🚨 Erros Comuns

1. **Import de infrastructure**: REMOVER IMEDIATAMENTE. Domain é puro.
2. **Lógica em entities**: Entities devem ser apenas dados. Lógica vai em services/ ou logic.py.
3. **Estado mutável**: Usar `frozen=True` em dataclasses quando possível.
