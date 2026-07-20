# API Reference — MBird Dashboard

Base URL: `http://localhost:8050/api/v1`

Autenticação: Bearer JWT no header `Authorization`.

---

## Auth

### POST `/auth/login`

Login — retorna token JWT.

**Body:**
```json
{ "email": "admin@empresa.com", "password": "admin123" }
```

**Response:**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### POST `/auth/register`

Registrar novo usuário (admin). **Stub/TODO** — não implementado.

### GET `/auth/me`

Retorna info do usuário autenticado.

**Response:**
```json
{ "email": "admin@empresa.com", "role": "admin" }
```

---

## Dashboard

Todos os endpoints requerem JWT.

### GET `/dashboard/summary`

KPIs consolidados do período.

**Query params:** `start_date`, `end_date` (YYYY-MM-DD, opcional — default: mês atual)

**Response:**
```json
{
  "total_conversations": 1500,
  "nps_score": 72.5,
  "frt_avg_minutes": 3.2,
  "art_avg_minutes": 15.8,
  "rating_avg": 4.3,
  "sla_compliance_pct": 89.2,
  "total_messages": 12000,
  "unique_contacts": 800,
  "returning_contacts": 200
}
```

### GET `/dashboard/evolution`

Evolução mês a mês das métricas.

**Query params:** `months` (1-24, default: 12)

**Response:**
```json
{
  "evolution": [
    {
      "year": 2026, "month": 1, "label": "Jan/2026",
      "total_conversations": 1200, "nps_score": 70.0,
      "art_avg_minutes": 16.2, "frt_avg_minutes": 3.5,
      "sla_compliance_pct": 88.0, "rating_avg": 4.2
    }
  ]
}
```

### GET `/dashboard/agents`

Ranking de agentes por métricas.

**Query params:** `start_date`, `end_date`

**Response:**
```json
{
  "agents": [
    {
      "rank": 1, "agent_name": "João", "department": "Suporte",
      "group": "N1", "total_chats": 150, "nps_score": 85.0,
      "rating_avg": 4.8, "art_avg_minutes": 12.0,
      "frt_avg_minutes": 2.1, "sla_compliance_pct": 95.0,
      "total_messages": 2000
    }
  ]
}
```

### GET `/dashboard/channels`

Métricas por canal de atendimento.

**Query params:** `start_date`, `end_date`

**Response:**
```json
{
  "channels": [
    {
      "channel_id": "whatsapp", "channel_name": "WhatsApp",
      "total_conversations": 800, "total_messages": 6000,
      "nps_score": 75.0, "rating_avg": 4.5
    }
  ]
}
```

### GET `/dashboard/bsc`

Balanced Scorecard (BSC) com dados T1/T2.

**Query params:** `start_date`, `end_date`

**Response:**
```json
{
  "header": ["Indicador", "Meta", "Resultado"],
  "data_t1": [["NPS", "≥70", "72.5"]],
  "data_t2": [["ART", "≤15min", "15.8min"]],
  "kpi_config": { ... }
}
```

### GET `/dashboard/kpis`

Configuração de KPIs por departamento.

**Query params:** `department` (opcional)

**Response:**
```json
{
  "department": "Suporte",
  "kpis": [
    { "name": "NPS", "value": 72.5, "meta": "≥70", "peso": 30, "score": 9.5, "tipo": "maior_melhor" }
  ]
}
```

---

## Conversations

Todos os endpoints requerem JWT.

### GET `/conversations/`

Lista paginada de conversas com filtros.

**Query params:**

| Param | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `start_date` | str | — | Data início |
| `end_date` | str | — | Data fim |
| `department` | str | — | Departamento |
| `agent` | str | — | Agente |
| `channel` | str | — | Canal |
| `status` | str | — | Status |
| `search` | str | — | Busca livre |
| `page` | int | 1 | Página (≥1) |
| `per_page` | int | 20 | Itens/página (1-100) |
| `sort_by` | str | created_at | Campo ordenação |
| `sort_order` | str | desc | asc/desc |

**Response:**
```json
{
  "conversations": [
    {
      "id": "12345", "contact": "Maria", "phone": "+5511...",
      "agent": "João", "department": "Suporte", "channel": "WhatsApp",
      "status": "closed", "start_time": "2026-01-15T10:00:00",
      "end_time": "2026-01-15T10:30:00", "duration_minutes": 30.0,
      "frt_minutes": 2.5, "art_minutes": 15.0, "rating": 5,
      "nps": 9, "msg_count": 25, "reopened_count": 0
    }
  ],
  "total": 1500, "page": 1, "per_page": 20
}
```

### GET `/conversations/{id}`

Detalhe de uma conversa com mensagens.

**Response:**
```json
{
  "id": "12345", "contact": "Maria", "phone": "+5511...",
  "agent": "João", "department": "Suporte", "channel": "WhatsApp",
  "status": "closed", "start_time": "...", "end_time": "...",
  "duration_minutes": 30.0, "frt_minutes": 2.5, "art_minutes": 15.0,
  "rating": 5, "nps": 9, "msg_count": 25, "reopened_count": 0,
  "messages": [
    {
      "message_id": "msg_001", "direction": "inbound",
      "content": "Olá, preciso de ajuda", "created_at": "...",
      "agent_id": null, "agent_name": null
    }
  ]
}
```

### GET `/conversations/{id}/messages`

Mensagens de uma conversa.

**Response:**
```json
{
  "conversation_id": "12345",
  "messages": [ ... ],
  "total": 25
}
```

---

## Reports

Todos os endpoints requerem JWT. **Stubs/TODO** — não implementados.

### POST `/reports/generate`

Gerar relatório on-demand.

**Body:**
```json
{ "type": "monthly", "year": 2026, "month": 1, "group": null }
```

**Response:**
```json
{ "status": "processing", "report_id": "pending" }
```

### GET `/reports/{report_id}/download`

Download do relatório gerado.

### GET `/reports/available`

Listar relatórios disponíveis.

---

## Admin

### GET `/admin/health`

Health check (sem auth).

**Response:**
```json
{ "status": "healthy", "version": "2.0.0", "database": "unknown" }
```

### GET `/admin/sync/status`

Status da última sincronização. **Stub/TODO.**

### POST `/admin/sync/trigger`

Trigger sincronização manual.

**Body:**
```json
{
  "full_sync": false,
  "sync_messages": false,
  "messages_days": null,
  "year": null, "month": null,
  "backfill_surveys": false
}
```

### GET `/admin/agents`

Lista todos os agentes (de `business_config.yaml`).

### GET `/admin/departments`

Lista todos os departamentos (de `business_config.yaml`).

---

## Background Jobs (APScheduler)

| Job | Frequência | Descrição |
|-----|-----------|-----------|
| Incremental sync | A cada 15 min | Contatos + conversas das últimas 60min |
| Full sync | Diário às 03:00 | Dados completos + mensagens + surveys |

Ambos executam `REFRESH MATERIALIZED VIEW CONCURRENTLY vw_survey_data` ao final.
