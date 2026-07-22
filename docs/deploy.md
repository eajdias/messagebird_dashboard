# Guia de Deploy — new_bird

> Guia completo para deploy do dashboard omnichannel usando Docker Compose + Cloudflare Tunnels.

---

## Stack

| Serviço | Imagem | Porta Host |
|---------|--------|------------|
| **PostgreSQL** | `postgres:18-alpine` | `5432` |
| **API** (FastAPI) | `python:3.14-slim` | `8050` |
| **Frontend** (Next.js) | `node:22-alpine` | `3050` |

---

## Pré-requisitos

- Docker + Docker Compose instalados
- Cloudflare Tunnel configurado na VPS (cloudflared)
- Domínios: `zsc-sac.eajdias.com` (frontend) e `zsc-sac-api.eajdias.com` (API)

---

## 1. Setup Inicial

```bash
# Clone o repositório
git clone <repo-url> new_bird
cd new_bird

# Crie o arquivo .env
cp .env.example .env

# Edite as variáveis sensíveis
#   DB_PASSWORD=senha_forte_aqui
#   JWT_SECRET=outra_senha_forte_minimo_32_chars
#   MESSAGEBIRD_API_KEY_LIVE=sua_chave_real
#   MESSAGEBIRD_WORKSPACE_ID_LIVE=seu_workspace_id
#   SYNC_ENABLED=true
```

### Variáveis de Ambiente Obrigatórias

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `DB_PASSWORD` | Senha do PostgreSQL | `m87#xF2pK9!` |
| `JWT_SECRET` | Chave para assinar tokens JWT (mín. 32 chars) | `uma-chave-muito-longa-e-segura-com-32-chars` |
| `MESSAGEBIRD_API_KEY_LIVE` | API Key do MessageBird | `live_xxx...` |
| `MESSAGEBIRD_WORKSPACE_ID_LIVE` | Workspace ID | `uuid-do-workspace` |

### Variáveis com Valores Padrão (opcional)

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `SYNC_PROFILE` | `daily` | Perfil de sync: `debug` (15min), `short` (30min), `hourly`, `daily`, `weekly`, `monthly` |
| `SYNC_ENABLED` | `true` | Habilitar sync automático |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `CORS_ORIGINS` | `https://zsc-sac.eajdias.com,http://localhost:3050` | Origens permitidas |

---

## 2. Build e Start

```bash
# Build das imagens
docker compose build

# Subir serviços
docker compose up -d

# Verificar status
docker compose ps
# NAME             STATUS
# mbird_postgres   Up (healthy)
# mbird_api        Up (healthy)
# mbird_frontend   Up (healthy)
```

### Health Checks

Os 3 serviços têm health checks automáticos:

- **PostgreSQL:** `pg_isready -U mbird -d mbird_reports` (intervalo 5s)
- **API:** `GET /api/v1/admin/health` via HTTP (intervalo 30s, start-period 15s)
- **Frontend:** `wget -qO- http://localhost:3000/` (intervalo 30s, start-period 15s)

---

## 3. Verificação Pós-Deploy

```bash
# 1. Health check da API
curl http://localhost:8050/api/v1/admin/health
# {"status":"healthy","version":"2.0.0","database":"connected"}

# 2. Login — obter token JWT
curl -X POST http://localhost:8050/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresa.com","password":"admin123"}'
# {"access_token":"eyJ...","token_type":"bearer"}

# 3. Refresh token
TOKEN="eyJ..."  # token obtido acima
curl -X POST http://localhost:8050/api/v1/auth/refresh \
  -H "Authorization: Bearer $TOKEN"
# {"access_token":"eyJ...novo...","token_type":"bearer"}

# 4. Dashboard summary
curl http://localhost:8050/api/v1/dashboard/summary \
  -H "Authorization: Bearer $TOKEN"
# {"total_conversations":..., "nps_score":..., ...}

# 5. Frontend — abrir no navegador
# http://localhost:3050

# 6. Gerar relatório de teste
curl -X POST http://localhost:8050/api/v1/reports/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"monthly","year":2026,"month":6}'
# {"status":"ok","report_id":"..."}
```

---

## 4. Sincronização com MessageBird

### Sincronização Automática

O APScheduler roda dentro do container da API com dois jobs:

| Job | Trigger | Descrição |
|-----|---------|-----------|
| `sync_incremental` | A cada `SYNC_PROFILE` (ex.: 1h) | Sync estrutural + mensagens recentes |
| `sync_daily_full` | Diariamente às 3:00 AM | Full structural sync |

### Sincronização Manual

```bash
TOKEN="seu_token_jwt"

# Sync completo (estrutura + mensagens)
curl -X POST http://localhost:8050/api/v1/admin/sync/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": true, "sync_messages": true}'

# Sync de hoje
curl -X POST http://localhost:8050/api/v1/admin/sync/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "sync_today"}'

# Sync de mês específico
curl -X POST http://localhost:8050/api/v1/admin/sync/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "month": 6}'

# Verificar status
curl http://localhost:8050/api/v1/admin/sync/status \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5. Cloudflare Tunnel

### Configuração

```bash
# Instalar cloudflared (se não estiver instalado)
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

# Autenticar
cloudflared tunnel login

# Criar tunnel
cloudflared tunnel create messagebird-tunnel

# Configurar rotas no arquivo ~/.cloudflared/config.yml
# Tunnel: <tunnel-uuid>
# credentials-file: /root/.cloudflared/<tunnel-uuid>.json
# ingress:
#   - hostname: zsc-sac.eajdias.com
#     service: http://localhost:3050
#   - hostname: zsc-sac-api.eajdias.com
#     service: http://localhost:8050
#   - service: http_status:404

# Configurar DNS
cloudflared tunnel route dns messagebird-tunnel zsc-sac.eajdias.com
cloudflared tunnel route dns messagebird-tunnel zsc-sac-api.eajdias.com

# Iniciar tunnel como serviço
cloudflared tunnel install messagebird-tunnel
```

### Verificação

```bash
# Tunnel ativo?
cloudflared tunnel list

# Testar através do Cloudflare
curl https://zsc-sac-api.eajdias.com/api/v1/admin/health
# {"status":"healthy","version":"2.0.0","database":"connected"}
```

---

## 6. Logs e Manutenção

```bash
# Ver logs de todos os serviços
docker compose logs -f

# Logs de um serviço específico
docker compose logs -f api
docker compose logs -f frontend

# Reiniciar um serviço
docker compose restart api

# Atualizar para nova versão
docker compose pull
docker compose up -d --force-recreate

# Parar tudo
docker compose down

# Parar tudo + remover volumes (dados!)
docker compose down -v

# Acessar o banco
docker compose exec postgres psql -U mbird -d mbird_reports
```

---

## 7. Troubleshooting

### API não fica healthy

```bash
# Verificar logs
docker compose logs api

# Problemas comuns:
# 1. passlib + bcrypt incompatíveis → docker compose build api
# 2. DB não acessível → verificar DATABASE_URL e health do postgres
# 3. MESSAGEBIRD_API_KEY inválida → verificar .env
```

### Frontend não carrega

```bash
# Verificar se a build foi bem-sucedida
docker compose logs frontend

# Verificar se NEXT_PUBLIC_API_URL está apontando para API correta
# No docker compose, o valor é http://api:8000
```

### Sincronização não funciona

```bash
# Verificar API keys no .env
# Testar conexão manual com MessageBird API
curl -H "Authorization: AccessKey live_xxx" \
  https://conversations.messagebird.com/v1/conversations?limit=1
```

---

## 8. Testes de Validação (Checklist)

| Teste | Como Executar | Critério |
|-------|---------------|----------|
| **Health check** | `curl localhost:8050/api/v1/admin/health` | Status 200, `"status":"healthy"` |
| **Login** | `POST /api/v1/auth/login` | Retorna `access_token` |
| **Refresh token** | `POST /api/v1/auth/refresh` | Novo token emitido |
| **Dashboard** | `GET /api/v1/dashboard/summary` | Dados do período |
| **Conversas** | `GET /api/v1/conversations/?page=1&per_page=5` | Lista paginada |
| **Relatório** | `POST /api/v1/reports/generate` | `report_id` gerado |
| **Dark/Light mode** | Clicar toggle no TopBar | Tema persiste ao recarregar |
| **Sync manual** | `POST /api/v1/admin/sync/trigger` | Status atualizado |
| **Exportação CSV** | Clicar "CSV" na página de Conversas | Arquivo `.csv` baixado |
| **Docker Compose** | `docker compose ps` | 3/3 serviços healthy |
