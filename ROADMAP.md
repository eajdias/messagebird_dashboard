# Roadmap — Contribuições de Documentação

Este arquivo lista as melhorias de documentação pendentes para deixar o repositório pronto para colaboradores externos. As tarefas priorizadas são independentes e podem ser feitas em qualquer ordem.

---

## 🔴 Prioridade Alta

### `docs/API.md` — Completar referência de endpoints
Atualmente documenta ~23 endpoints. O código tem ~60. Faltam principalmente:
- `GET /dashboard/executive/*` (quality, heatmap, motives, occurrences, dow, departments, agents, bsc, meta, art-distribution, returners)
- `GET /dashboard/bsc/scorecard`
- `GET /dashboard/evolution/granular`
- `POST /reports/export`, `POST /reports/export-dashboard`
- `POST /auth/change-password`, `POST /auth/register`
- `GET/POST/PUT/DELETE /admin/users`
- `GET/POST/PUT/DELETE /admin/agents/{name}/manual-entries`
- `PUT /admin/scheduler/profile`

### `docs/DATABASE.md` — Tabelas `users`, `bsc_manual_values`, `agent_manual_entries`
As migrations 005, 006 e 007 foram adicionadas mas as tabelas não estão descritas no schema do documento.

### `docs/CONFIG.md` — Adicionar vars ausentes
Faltam documentar: `REPORTS_DIR`, `MESSAGEBIRD_DEFAULT_SOFTWARE`, `DB_PASSWORD`, `MESSAGEBIRD_PHRASE_TICKET_HEADER`, `MESSAGEBIRD_SOFTWARE_NAMES`, `MESSAGEBIRD_BASE_URL_BIRD`.

---

## 🟡 Prioridade Média

### `docs/SETUP.md` — Guia de primeira execução
Cobrindo: pré-requisitos, clonar, configurar `.env`, obter API keys, executar migrações, iniciar scheduler, acessar dashboard.

### `docs/USERS.md` — Sistema de usuários e autenticação
Explicar: tabela `users`, roles (admin/agent), endpoints de CRUD, `require_admin`, change-password, diferenças de acesso no frontend.

### `docs/DEPLOY.md` — Deploy com Docker
Como fazer deploy em produção, configurar nginx reverso, variáveis de ambiente de produção, volumes, healthchecks.

---

## 🟢 Prioridade Baixa

### `README.md` — Página inicial do repositório
Badges, descrição do projeto, quickstart (clone → docker-compose up), links para docs/.

### `Dockerfile` — Migrar para `uv`
O Dockerfile atual usa `pip` enquanto o gerenciador declarado do projeto é `uv`. Também há dependências não utilizadas (`sqlalchemy`, `alembic`).

### `.gitignore` — Limpar regra conflitante
Linha `reports/*` conflita com regras específicas das linhas anteriores. Manter apenas um estilo.

### `CHANGELOG.md` + `CONTRIBUTING.md`
Arquivos padrão para repositórios públicos: histórico de versões e guia para contribuidores.

---

## 📝 Convenções

- Commits de documentação devem usar prefixo `docs:` (Conventional Commits)
- Nunca incluir credenciais reais (senhas, tokens) na documentação
- Manter referências de arquivos e caminhos sempre atualizadas
