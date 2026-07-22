# Configuração

> Variáveis de ambiente, arquivos de configuração YAML, Docker.

## Variáveis de Ambiente (`.env`)

| Variável | Descrição | Default |
|----------|-----------|---------|
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql+asyncpg://...` |
| `DATABASE_ECHO` | Log de queries SQL | `false` |
| `JWT_SECRET` | Chave secreta para JWT | — |
| `JWT_ALGORITHM` | Algoritmo JWT | `HS256` |
| `JWT_EXPIRATION_MINUTES` | Expiração do token | `480` |
| `CORS_ORIGINS` | Origens permitidas CORS | `http://localhost:3000` |
| `MESSAGEBIRD_API_KEY_LIVE` | API Key MessageBird (produção) | — |
| `MESSAGEBIRD_WORKSPACE_ID_LIVE` | Workspace ID (produção) | — |
| `MESSAGEBIRD_BASE_URL_CONVERSATIONS` | URL base conversations API | `https://conversations.messagebird.com/v1` |
| `MESSAGEBIRD_BASE_URL_CONTACTS` | URL base contacts API | `https://contacts.messagebird.com/v2` |
| `MESSAGEBIRD_HTTP_TIMEOUT` | Timeout HTTP client | `30.0` |
| `MESSAGEBIRD_TIMEZONE_OFFSET` | Offset de fuso horário | `-3` (Brasília) |
| `SYNC_PROFILE` | Perfil de sincronização | `daily` |
| `SYNC_ENABLED` | Habilitar sync automático | `true` |
| `APP_ENV` | Ambiente (development/production) | `development` |
| `APP_DEBUG` | Modo debug | `true` |
| `APP_PORT` | Porta da API | `8000` |
| `LOG_LEVEL` | Nível de log | `INFO` |

## Arquivos de Configuração YAML

### `business_config.yaml`

Configuração de negócio: agentes, departamentos, canais, roteamento. Exemplo em `business_config.yaml.example`.

```yaml
agents:
  "agent_bird_id_1":
    name: "Nome do Agente"
    group: "Suporte Tecnico"
departments:
  1: "Suporte Tecnico"
  2: "Comercial"
  3: "Financeiro"
  4: "Ouvidoria"
  5: "Nova Instalacao | Migracao"
```

**Importante:** `business_config.yaml` está no `.gitignore` por conter dados reais da empresa. Use `business_config.yaml.example` como template.

### `business_bsc.yaml`

Configuração de pontuação BSC/KPI. Exemplo em `business_bsc.yaml.example`.

```yaml
kpi_config:
  "Suporte Tecnico":
    t1: [...]  # Métricas principais (elogios, NPS, penalidades, etc.)
    t2: [...]  # Métricas secundárias (updates, treinamentos, tarefas)
```

## Docker

### Serviços (`docker-compose.yml`)

| Serviço | Porta | Dockerfile | Descrição |
|---------|-------|-----------|-----------|
| `postgres` | 5432 | — (imagem oficial) | PostgreSQL 18 Alpine |
| `api` | 8050:8000 | `./Dockerfile` | FastAPI com reload |
| `frontend` | 3050:3000 | `./frontend/Dockerfile` | Next.js |

### Variáveis Docker

- `DB_PASSWORD` — Senha do PostgreSQL (default: `mbird_dev_2024`)
- Volumes montados para hot-reload do backend: `api/`, `domain/`, `application/`, `infrastructure/`, `reports/`

### Comandos Docker

```bash
# Iniciar todos os serviços
docker compose up -d

# Ver logs
docker compose logs -f api

# Rebuildar um serviço
docker compose build api

# Parar tudo
docker compose down
```

## Senhas e Segurança

- `Default: password padrão` (usuário admin) — alterar em produção
- `JWT_SECRET` — gerar secret forte mínimo 32 caracteres
- `MESSAGEBIRD_API_KEY_LIVE` — key de produção do MessageBird
- `business_config.yaml` e `business_bsc.yaml` estão no `.gitignore`
- `.env` está no `.gitignore`
