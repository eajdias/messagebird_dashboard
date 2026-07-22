# Architecture Decision Records (ADRs)

> Registro cronológico de decisões arquiteturais importantes. Consulte antes de tomar decisões que possam conflitar com decisões anteriores.

---

### 2026-06-05: Clean Architecture com Python

**Contexto:** Projeto cresceu e precisava de organização clara.

**Decisão:** Adotar Clean Architecture (api/ → application/ → domain/ ← infrastructure/) com interfaces ABC em application/interfaces/.

**Consequências:** Separação clara de responsabilidades, facilidade para testar cada camada isoladamente. Maior boilerplate inicial.

---

### 2026-06-01: Escolha do Banco PostgreSQL

**Contexto:** Necessário banco relacional para dados estruturados de conversas e métricas.

**Decisão:** PostgreSQL com asyncpg (driver assíncrono) e migrations SQL puras aplicadas automaticamente.

**Consequências:** Performance excelente, schema versionado, sem ORM overhead.

---

### 2026-05-15: Docker Compose como Infraestrutura

**Contexto:** Necessário ambiente reproduzível para desenvolvimento e produção.

**Decisão:** docker-compose com 3 serviços (postgres, api, frontend) e portas 8050/3050 para Cloudflare Tunnel.

**Consequências:** Setup simples com `docker compose up -d`. Portas não-padrão para evitar conflitos.

---

### 2026-05-10: CLI vs API para Sync

**Contexto:** Sync pode ser disparado tanto por CLI quanto por scheduler automático.

**Decisão:** Manter ambos: CLI (`main.py sync`) para operações manuais/backfill, scheduler automático para sync regular.

**Consequências:** Flexibilidade máxima. CLI usa rich para output formatado.