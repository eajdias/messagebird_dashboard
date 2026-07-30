# Performance Fixes — Dashboard Visão Geral

> Diagnóstico completo de performance do dashboard quando visualizado com histórico de 2020-2026.
> Cada item inclui arquivo afetado, linha, explicação do problema e implementação.

---

## P0 — Críticos (Impedem o funcionamento)

### 1. Cache de `process_all()` — eliminar 4/5 redundâncias

**Problema:** `process_all()` é chamado 5 vezes para o mesmo date range (`/summary`, `/bsc`, `/agents`, `/channels`, `/executive/meta`). Cada chamada recria `ProcessedReportData` com FRT/ART/Duration.

**Arquivo:** `api/routes/dashboard.py:109-117`

```python
# ATUAL — sem cache, processa toda vez
async def _fetch_and_process(repo, start_date, end_date):
    raw = await repo.fetch_raw_data_range(start_date, end_date)
    agg = _make_aggregator()
    return raw, agg.process_all(raw)
```

**Implementação:**

- [ ] Criar cache `processed_cache` em `infrastructure/cache.py` (já existe, reutilizar)
- [ ] Adicionar cache em `_fetch_and_process()`:
  ```python
  async def _fetch_and_process(repo, start_date, end_date):
      cache_key = f"proc:{start_date}:{end_date}"
      cached = await _pc.get(cache_key)
      if cached is not None:
          return cached
      raw = await repo.fetch_raw_data_range(start_date, end_date)
      agg = _make_aggregator()
      processed = agg.process_all(raw)
      await _pc.set(cache_key, (raw, processed))
      return raw, processed
  ```
- [ ] Invalidar cache no refresh da materialized view (`infrastructure/cache.py`)
- [ ] Testar que cache hit evita reprocessamento

---

### 2. Validar período máximo no frontend (12 meses)

**Problema:** `DateRangePicker` aceita qualquer período. 6 anos = milhões de rows.

**Arquivo:** `frontend/components/ui/date-range-picker.tsx`

**Implementação:**

- [ ] Adicionar constante `MAX_RANGE_DAYS = 365` no topo do componente
- [ ] Validar no `handleConfirm`:
  ```typescript
  const handleConfirm = () => {
      const diff = (new Date(localEnd).getTime() - new Date(localStart).getTime()) / (1000 * 60 * 60 * 24);
      if (diff > MAX_RANGE_DAYS) {
          toast.error("Período máximo permitido é de 12 meses");
          return;
      }
      (onConfirm ?? onChange)(localStart, localEnd);
  };
  ```
- [ ] Validar no `handlePreset` também
- [ ] Adicionar mensagem visual de aviso quando período > 6 meses
- [ ] Testar com período de 13 meses

---

### 3. Adicionar `command_timeout` no asyncpg

**Problema:** Sem timeout, queries pesadas rodam indefinidamente.

**Arquivo:** `infrastructure/database/postgres_connection.py`

**Implementação:**

- [ ] Adicionar `command_timeout=30` no construtor do `PostgresPool`:
  ```python
  self._pool = await asyncpg.create_pool(
      dsn=dsn,
      min_size=min_size,
      max_size=max_size,
      command_timeout=30,
  )
  ```
- [ ] Adicionar `acquire(timeout=10)` em todas as chamadas de `pool.acquire()`:
  ```python
  async with self._pool.acquire(timeout=10) as conn:
      ...
  ```
- [ ] Testar que queries >30s são canceladas com erro adequado
- [ ] Verificar logs do PostgreSQL para `statement timeout`

---

## P1 — Altos (Impacto significativo)

### 4. `asyncio.to_thread` para operações CPU-bound

**Problema:** `_rows_to_conversations()` e `process_all()` bloqueiam o event loop.

**Arquivos:**
- `infrastructure/repositories/postgres_report_repository.py:131-137`
- `api/routes/dashboard.py:109-117`

**Implementação:**

- [ ] Envolver `_rows_to_conversations` em `asyncio.to_thread`:
  ```python
  async def _fetch():
      rows = await self._pool.fetch_all(queries_pg.SURVEY_MV_RANGE, s, e)
      return await asyncio.to_thread(_rows_to_conversations, rows, agent_group)
  ```
- [ ] Envolver `process_all` em `asyncio.to_thread`:
  ```python
  async def _fetch_and_process(repo, start_date, end_date):
      raw = await repo.fetch_raw_data_range(start_date, end_date)
      agg = _make_aggregator()
      processed = await asyncio.to_thread(agg.process_all, raw)
      return raw, processed
  ```
- [ ] Testar que event loop não bloqueia durante processamento
- [ ] Monitorar uso de threads no ThreadPoolExecutor

---

### 5. Single-pass `aggregate_statistics`

**Problema:** 11 iterações separadas sobre o mesmo array.

**Arquivo:** `application/services/report_aggregator.py:64-142`

**Implementação:**

- [ ] Reescrever com uma única iteração:
  ```python
  def aggregate_statistics(self, processed_data):
      ratings, nps_scores, arts, durations = [], [], [], []
      compliments = negatives = neutrals = both_rated = 0
      art_buckets = {k: 0 for k in ["0_5", "5_10", "10_30", "30_60", "60_120", "120_plus"]}
      contacts = Counter()

      for p in processed_data:
          if p.rating is not None:
              ratings.append(p.rating)
              if p.nps is not None:
                  both_rated += 1
                  if p.rating >= 4: compliments += 1
                  elif p.rating <= 2: negatives += 1
                  else: neutrals += 1
          if p.nps is not None:
              nps_scores.append(p.nps)
          if p.art_min is not None:
              arts.append(p.art_min)
              if p.art_min <= 5: art_buckets["0_5"] += 1
              elif p.art_min <= 10: art_buckets["5_10"] += 1
              elif p.art_min <= 30: art_buckets["10_30"] += 1
              elif p.art_min <= 60: art_buckets["30_60"] += 1
              elif p.art_min <= 120: art_buckets["60_120"] += 1
              else: art_buckets["120_plus"] += 1
          if p.duration_min is not None:
              durations.append(p.duration_min)
          if p.contact_id:
              contacts[p.contact_id] += 1

      returners = sum(1 for c in contacts.values() if c > 1)
      # ... restante das métricas
  ```
- [ ] Manter interface pública inalterada
- [ ] Testar que resultados são idênticos ao anterior
- [ ] Benchmark: medir tempo antes/depois com 10k conversas

---

### 6. Unificar FRT e ART em um único calculator

**Problema:** FRTCalculator e ARTCalculator são 100% idênticos.

**Arquivos:**
- `domain/metrics/frt.py:8-27`
- `domain/metrics/art.py:8-27`

**Implementação:**

- [ ] Criar `domain/metrics/response_time.py`:
  ```python
  class ResponseTimeCalculator:
      def calculate(self, data: RawConversationData) -> tuple[float | None, float | None]:
          first_resp_dt = None
          for m in data.msgs:
              if m.direction == "sent" and m.agent_id is not None:
                  first_resp_dt = logic.parse_datetime(m.created, apply_offset=True)
                  break
          start_dt = logic.parse_datetime(data.raw_created, apply_offset=True)
          if first_resp_dt and start_dt:
              diff = (first_resp_dt - start_dt).total_seconds() / 60
              return round(diff, 2), round(diff, 2)
          return None, None
  ```
- [ ] Atualizar `report_aggregator.py` para usar o calculator unificado
- [ ] Remover `frt.py` e `art.py`
- [ ] Testar que FRT e ART continuam calculados corretamente

---

### 7. Otimizar `parse_datetime` — evitar try/except em loop

**Problema:** ~5M chamadas com exception handling (lento em Python).

**Arquivo:** `domain/logic.py:10-36`

**Implementação:**

- [ ] Reescrever com detecção por formato sem try/except:
  ```python
  _CACHE: dict[str, datetime] = {}

  def parse_datetime(dt_string: str | None, apply_offset: bool = False) -> datetime | None:
      if not dt_string:
          return None
      if dt_string in _CACHE:
          return _CACHE[dt_string]

      dt = None
      if "T" in dt_string:
          clean = dt_string.replace("Z", "").split(".")[0]
          dt = datetime.strptime(clean, "%Y-%m-%dT%H:%M:%S")
      elif len(dt_string) == 19 and dt_string[4] == "-" and dt_string[10] == " ":
          dt = datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S")
      elif len(dt_string) == 10 and dt_string[4] == "-":
          dt = datetime.strptime(dt_string, "%Y-%m-%d")

      if dt and apply_offset:
          dt += timedelta(hours=TIMEZONE_OFFSET)

      if dt:
          _CACHE[dt_string] = dt
      return dt
  ```
- [ ] Adicionar LRU cache com tamanho máximo (ex: 100k entradas)
- [ ] Testar todos os formatos existentes no banco
- [ ] Benchmark: medir chamadas/segundo antes/depois

---

### 8. Batch `setState` no frontend

**Problema:** 9 micro-state updates causam 4-9 re-renders intermediários.

**Arquivos:**
- `frontend/hooks/useDashboard.ts:83-99`
- `frontend/hooks/useExecutive.ts:115-132`

**Implementação em `useDashboard.ts`:**

- [ ] Acumular resultados e aplicar em um único `setState`:
  ```typescript
  const fetchBaseData = useCallback(async (signal: AbortSignal) => {
      if (!enabled) return;
      setState((prev) => ({ ...prev, loading: true, error: null }));

      const baseEndpoints = [/* ... */];
      const results: Record<string, unknown> = {};

      await Promise.allSettled(
          baseEndpoints.map(async (ep) => {
              try {
                  const res = await api.get(ep.url, { signal });
                  results[ep.key] = res.data;
              } catch (err) {
                  if (err instanceof DOMException && err.name === "AbortError") return;
                  // coletar erros
              }
          })
      );

      // ÚNICO setState
      setState((prev) => ({
          ...prev,
          ...results,
          loading: false,
          error: failures.length > 0 ? `Falha ao carregar: ${failures.join(", ")}` : null,
      }));
  }, [/* deps */]);
  ```
- [ ] Aplicar mesmo padrão em `useExecutive.ts`
- [ ] Testar que todos os dados aparecem corretamente
- [ ] Verificar que não há flicker durante carregamento

---

### 9. `useMemo` em chartData (3 charts)

**Problema:** Novo array criado a cada re-render.

**Arquivos:**
- `frontend/components/dashboard/rating-evolution-chart.tsx:55`
- `frontend/components/dashboard/nps-evolution-chart.tsx:55`
- `frontend/components/dashboard/art-evolution-chart.tsx:50`

**Implementação:**

- [ ] Adicionar `useMemo` em cada chart:
  ```typescript
  const chartData = useMemo(() =>
      data.map((b) => ({
          label: b.label,
          value: /* cálculo */,
      })),
      [data]
  );
  ```
- [ ] Aplicar em todos os 3 arquivos
- [ ] Verificar que gráficos renderizam corretamente

---

## P2 — Médios (Qualidade e manutenção)

### 10. Remover `--reload` do compose em production

**Problema:** `--reload` ativa file watching com 6 bind mounts.

**Arquivo:** `docker-compose.yml:38`

**Implementação:**

- [ ] Criar profile `dev` com `--reload`:
  ```yaml
  api:
    profiles: ["dev"]
    command: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
  ```
- [ ] Criar profile `prod` sem `--reload`:
  ```yaml
  api:
    profiles: ["prod"]
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
  ```
- [ ] Atualizar `docker-compose.yml` com profiles adequados
- [ ] Documentar uso: `docker compose --profile dev up` vs `docker compose --profile prod up`

---

### 11. Adicionar `--workers` ao uvicorn

**Problema:** Single process não paraleliza requests.

**Arquivo:** `docker-compose.yml:38`

**Implementação:**

- [ ] Adicionar `--workers 2` (ou `2 * CPU + 1`):
  ```yaml
  command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 2
  ```
- [ ] Ajustar `max_size` do pool para `workers * 10` (ex: 20)
- [ ] Testar concorrência de requests
- [ ] Monitorar uso de memória (cada worker é um processo)

---

### 12. Limitar tamanho do cache

**Problema:** `_store` cresce indefinidamente.

**Arquivo:** `infrastructure/cache.py`

**Implementação:**

- [ ] Usar `cachetools.TTLCache` com `maxsize`:
  ```python
  from cachetools import TTLCache
  repo_cache = TTLCache(maxsize=1000, ttl=300)
  processed_cache = TTLCache(maxsize=500, ttl=300)
  ```
- [ ] Ou implementar LRU manual com `maxsize`
- [ ] Testar que cache evicta corretamente quando cheio

---

### 13. Consolidar `agent_map` — construir uma vez

**Problema:** `agent_map` é construído 3 vezes em `aggregate_dashboard`.

**Arquivo:** `application/services/report_aggregator.py`

**Implementação:**

- [ ] Construir `agent_map` uma vez no início de `aggregate_dashboard`:
  ```python
  def aggregate_dashboard(self, data, ...):
      agent_map = defaultdict(list)
      for p in data:
          agent_map[p.agent].append(p)
      # Passar agent_map para funções auxiliares
  ```
- [ ] Atualizar `_build_agents_rows`, `aggregate_agent_ratings` para receber `agent_map`
- [ ] Remover construções duplicadas

---

### 14. Desabilitar animação do Recharts em re-renders

**Problema:** Todos os 4 charts reanimam ao trocar período.

**Arquivos:**
- `frontend/components/dashboard/rating-evolution-chart.tsx`
- `frontend/components/dashboard/nps-evolution-chart.tsx`
- `frontend/components/dashboard/art-evolution-chart.tsx`
- `frontend/components/dashboard/rated-breakdown-chart.tsx`

**Implementação:**

- [ ] Adicionar state `animDone` e desabilitar após primeira animação:
  ```typescript
  const [animDone, setAnimDone] = useState(false);
  useEffect(() => { setAnimDone(true); }, []);

  // No chart:
  <Line isAnimationActive={!animDone} animationDuration={1200} />
  ```
- [ ] Aplicar em todos os 4 charts
- [ ] Verificar que animação inicial funciona

---

### 15. Remover prop `mounted` morta

**Problema:** `mounted` é passada mas nunca lida, causa re-render extra.

**Arquivo:** `frontend/app/(dashboard)/page.tsx:499-508`

**Implementação:**

- [ ] Remover state `mounted`:
  ```typescript
  // REMOVER:
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);
  ```
- [ ] Remover prop `mounted` de `<DashboardContent>`:
  ```typescript
  // ATUAL:
  <DashboardContent mounted={mounted} />
  // NOVO:
  <DashboardContent />
  ```
- [ ] Atualizar interface de `DashboardContent` para não receber `mounted`
- [ ] Verificar que dashboard renderiza corretamente

---

## P3 — Baixos (Melhorias de qualidade)

### 16. Healthcheck menos agressivo para PostgreSQL

**Arquivo:** `docker-compose.yml:26-30`

- [ ] Alterar `interval: 5s` para `interval: 15s`
- [ ] Manter `retries: 5`

---

### 17. Adicionar `max_connections` ao PostgreSQL

**Arquivo:** `docker-compose.yml`

- [ ] Adicionar `command` explícito:
  ```yaml
  postgres:
    command: postgres -c max_connections=200 -c shared_buffers=256MB
  ```

---

### 18. Pool `max_size` ajustado para workers

**Arquivo:** `infrastructure/database/postgres_connection.py`

- [ ] Tornar configurável via env var:
  ```python
  max_size = int(os.getenv("DB_POOL_MAX", "10"))
  ```

---

### 19. Logging driver mais eficiente

**Arquivo:** `docker-compose.yml`

- [ ] Alterar `driver: json-file` para `driver: local`:
  ```yaml
  logging:
    driver: local
    options:
      max-size: "10m"
      max-file: "3"
  ```

---

## Ordem de Implementação Recomendada

1. **P0.3** — `command_timeout` (5 min, melhoria imediata)
2. **P0.2** — Validar período no frontend (15 min, previne o problema)
3. **P0.1** — Cache `process_all()` (30 min, maior impacto)
4. **P1.8** — Batch `setState` no frontend (20 min, melhoria visual)
5. **P1.4** — `asyncio.to_thread` (20 min, libera event loop)
6. **P1.5** — Single-pass `aggregate_statistics` (40 min, reduz iterações)
7. **P1.6** — Unificar FRT/ART (15 min, elimina duplicação)
8. **P1.7** — Otimizar `parse_datetime` (30 min, reduz overhead)
9. **P1.9** — `useMemo` em charts (10 min, melhoria simples)
10. **P2.10** — Profiles Docker (15 min)
11. **P2.11** — Workers uvicorn (10 min)
12. **P2.12** — Limitar cache (10 min)
13. **P2.13** — Consolidar agent_map (20 min)
14. **P2.14** — Desabilitar animação Recharts (15 min)
15. **P2.15** — Remover mounted (5 min)

**Tempo estimado total: ~4-5 horas**

---

## Como Validar

1. **Antes de começar:** Medir tempo de carregamento com período 2020-2026 (deve ser >30min ou timeout)
2. **Após P0:** Medir novamente — deve cair para <2min
3. **Após P1:** Medir novamente — deve cair para <30s
4. **Testes:** Rodar `pytest` e `npm run type-check` após cada fix
5. **Lint:** Rodar `ruff check .` e `npm run lint` antes de commit
