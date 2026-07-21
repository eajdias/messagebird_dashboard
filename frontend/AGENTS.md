# frontend/ — Next.js Dashboard
> **Mandato:** Camada de apresentação web. Consome a API via HTTP — NUNCA acessa o banco diretamente.

---

## 🏗️ Estrutura Atualizada

```
frontend/
├── app/                          # App Router (Next.js 14+)
│   ├── (auth)/                   # Layout de autenticação
│   │   ├── login/page.tsx        # Tela de login
│   │   └── layout.tsx
│   ├── (dashboard)/              # Layout do dashboard
│   │   ├── layout.tsx            # Sidebar + TopBar
│   │   ├── page.tsx              # Dashboard principal (KPIs)
│   │   ├── conversations/
│   │   │   ├── page.tsx          # Lista de conversas
│   │   │   └── [id]/page.tsx     # Detalhe da conversa
│   │   ├── agents/page.tsx       # Ranking de agentes
│   │   ├── reports/page.tsx      # Gerar/baixar relatórios
│   │   └── settings/page.tsx     # Configurações
│   └── layout.tsx                # Root layout
├── components/
│   ├── ui/                       # Componentes base (Button, Card, etc.)
│   ├── dashboard/                # KPIs, gráficos, tabelas BSC
│   ├── conversations/            # Tabela, filtros, mensagens
│   └── layout/                   # Sidebar, TopBar
├── lib/
│   ├── api.ts                    # API client (wrapper do fetch)
│   ├── auth.ts                   # Auth context + JWT
│   └── utils.ts                  # Formatação, helpers
├── hooks/
│   ├── useDashboard.ts           # Hook para dados do dashboard
│   ├── useConversations.ts       # Hook para conversas
│   └── useAuth.ts                # Hook de autenticação
├── types/
│   └── index.ts                  # TypeScript interfaces
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

---

## 📐 Regras

### Componentes
- Componentes de página em `app/` (Server Components por padrão)
- Componentes interativos com `"use client"`
- Componentes reutilizáveis em `components/`
- UI base de `shadcn/ui` em `components/ui/`

### State Management
- `useDashboard` hook para buscar dados do dashboard
- `useConversations` hook para tratar conversas
- `useAuth` hook para autenticação

### API Client
- **Uso obrigatório:** Sempre usar `lib/api.ts` para chamar endpoints
- **Pattern:**
  ```typescript
// Exemplo de uso no componente
const dashboardData = await fetchDashboard({ group: "Suporte", period: "monthly" });
```
- **Tratamento de erros:** Mensagens de erro são redirecionadas para `/login` em caso de 401

### Autenticação
- JWT armazenado em `localStorage` via `lib/auth.ts`
- Fluxo de login:
  1. `POST /auth/login` com payload `{ email, password, client_secret }`
  2. Token armazenado em `localStorage.token`
  3. Todas as chamadas à API injetam o token automaticamente

## 🔧 Exemplos de Comandos para Introspecão

```bash
# Testar autenticação
curl -X POST http://localhost:3050/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresa.com", "password":"senha", "client_secret":"..."}' \
  -o token.json && cat token.json

# Validar dados do dashboard
curl -s http://localhost:3050/api/v1/dashboard/summary | jq .'

# Verificar estado da auth
curl -s http://localhost:3050/auth/me | jq .'
```

## 🚨 Erros Comuns

1. **CORS** → Verificar configuração no backend (API em `:8050`)
2. **401 Unauthorized** → Token expirado ou inválido
3. **Hydration Mismatch** → Use `useEffect` para acesso ao client-side apenas
4. **Loading States** → Mostrar skeleton durante fetch via `useQuery` do React Query

---

## 💡 Dicas para Agentes LLM

1. **Nunca** chamar endpoints diretamente no cliente
2. **Usar sempre** o wrapper `lib/api.ts` para solicitações HTTP
3. **Validar tokens** via `useAuth` antes de ações sensíveis
4. **Testar fluxos completos:** login → dashboard → gera relatório
5. **Evitar** usar `fetch` ou `axios` diretamente em componentes