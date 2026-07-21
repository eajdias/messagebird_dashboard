# Plano de Correções — Sync Pipeline

> Comparação com o projeto legado funcional (`MessageBird_API_Reports`) e
> identificação de bugs/design issues no pipeline PostgreSQL.

---

## Diagnóstico

### Bug 1: Contacts sync re-baixa TODOS os contatos a cada incremental ⚠️ CRÍTICO

O projeto legado tem `should_skip("contacts")` — pula contacts se feito nos
últimos 60 min. Nosso `trigger_sync_pg` **NÃO** tem isso. Cada incremental
re-baixa 7968 contatos (398 páginas), travando o sync por 5-20 minutos.

**Causa raiz**: `pg_sync_engine.py:895` chama `sync_contacts()` sem verificação.

### Bug 2: Sem progress logging no contacts sync

Contacts sync só loga "Starting contacts sync..." e "Contacts sync completed".
Nenhum progresso intermediário — impossível saber se está funcionando ou travado.

### Bug 3: ConnectTimeout intermitente na primeira tentativa

O primeiro request do Docker para `conversations.messagebird.com` às vezes
estoura timeout. O retry resolve, mas o projeto legado raramente tem isso
porque usa `timeout=HTTP_TIMEOUT` (float simples) vs nosso
`httpx.Timeout(HTTP_TIMEOUT, connect=10.0)`.

### Bug 4: Response key mismatch (data vs items)

`pg_sync_engine.py:261` usa `response.get("data", response.get("items", []))`.
A API retorna `items`, não `data`. Funciona por acidente (fallback).

### Design Issue: Complexidade desnecessária

Legado: ~400 linhas para sync. Ours: ~900 (pg_sync_engine) + ~1250 (sync.py)
+ use case + connection class separada. Muita abstração para fetches paginados.

---

## Fase 1: Fix crítico — Contacts skip + Logging

- [x] **1.1** Adicionar `should_skip("contacts")` no `trigger_sync_pg` (skip se <60 min)
- [x] **1.2** Adicionar progress logging no `sync_contacts` (page counter, items)
- [x] **1.3** Adicionar progress logging no `sync_conversations` (page counter)
- [x] **1.4** Simplificar timeout do client: `timeout=HTTP_TIMEOUT` (float, como legado)
- [x] **1.5** Testar sync incremental — deve completar em <30s

## Fase 2: Quick sync "hoje"

- [x] **2.1** Adicionar parâmetro `sync_today` em `SyncTriggerRequest`
- [x] **2.2** Implementar lógica no `trigger_sync_pg`: sync conversations de hoje + messages
- [x] **2.3** Passar `sync_today` pelo use case
- [x] **2.4** Testar via API: `{"sync_today": true}`

## Fase 3: Limpeza e alinhamento com legado

- [x] **3.1** Corrigir `response.get("data", ...)` → `response.get("items", [])`
- [x] **3.2** Alinhar paginação conversations com legado (pageToken + offset)
- [x] **3.3** Verificar e documentar estado do `sync.py` (SQLite legado)
- [x] **3.4** Rodar lint e todos os testes unitários

---

## Status

| Fase | Estado | Notas |
|------|--------|-------|
| Fase 1 | ✅ Concluída | Contacts skip funcional, 1.1s incremental |
| Fase 2 | ✅ Concluída | sync_today funcional, 32s com messages |
| Fase 3 | ✅ Concluída | 111/111 testes passando, lint limpo |
