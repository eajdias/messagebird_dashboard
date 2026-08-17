---
name: sync-pipeline
description: Executar sincronização de dados da MessageBird API para o PostgreSQL. Use quando o usuário pedir para sincronizar dados, atualizar o banco, ou executar o pipeline de sync.
---

# Skill: Sync Pipeline

Executa a sincronização de dados entre MessageBird API e PostgreSQL.

## Comandos

### Sync estrutural (contacts + conversations)
```bash
python main.py sync
```

### Sync com mensagens dos últimos N dias
```bash
python main.py sync --messages-days 7
```

### Full sync completo
```bash
python main.py sync --full --full-messages
```

### Sync de um mês específico
```bash
python main.py sync --year 2026 --month 6
```

### Backfill de surveys (NPS)
```bash
python main.py sync --backfill-surveys
```

## Via API (se servidor estiver rodando)

### Trigger manual
```bash
curl -X POST http://localhost:8000/api/v1/admin/sync/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_sync": false, "sync_messages": true, "messages_days": 7}'
```

### Ver status do scheduler
```bash
curl http://localhost:8000/api/v1/admin/scheduler/status \
  -H "Authorization: Bearer $TOKEN"
```

## Verificação Pós-Sync

1. Refresh da materialized view é automático
2. Verificar logs: `docker compose logs -f api` (se rodando em Docker)
3. Verificar dashboard: os dados devem refletir as novas informações

## Erros Comuns

- **Rate limit:** API Bird tem limite de 10 req/s — respeitado pelo client
- **Timeout:** Configurável via `MESSAGEBIRD_HTTP_TIMEOUT` (default 30s)
- **Chave inválida:** Verificar `MESSAGEBIRD_API_KEY_LIVE` no `.env`
