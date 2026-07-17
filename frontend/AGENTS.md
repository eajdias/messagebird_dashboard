# frontend/ — Next.js Dashboard

> **Mandato:** Camada de apresentação web. Consome a API via HTTP — NUNCA acessa o banco diretamente.

---

## 🏗️ Estrutura

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
│   ├── api.ts                    # API client (fetch wrapper)
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
- Componentes interativos com `"use client"` explícito
- Componentes reutilizáveis em `components/`
- UI base de `shadcn/ui` em `components/ui/`

### State Management
- Server State: React Query (TanStack Query) para cache de dados da API
- Client State: React Context para auth e tema
- Formulários: React Hook Form + Zod

### API Client
- Usar `lib/api.ts` como wrapper do fetch
- Nunca chamar a API diretamente nos componentes
- Pattern:
```typescript
// lib/api.ts
export async function fetchDashboard(params: DashboardParams) {
  const response = await fetch(`${API_URL}/api/v1/dashboard/summary`, {
    headers: { Authorization: `Bearer ${getToken()}` }
  });
  return response.json();
}
```

### Estilização
- Tailwind CSS para todos os estilos
- Tema escuro/claro via Next.js ThemeProvider
- Cores do tema em `tailwind.config.ts`
- NUNCA usar estilos inline (exceto dynamic values)

### Rotas
- Layouts agrupam páginas com estrutura comum
- `(auth)/` — layout sem sidebar/topbar
- `(dashboard)/` — layout com sidebar/topbar
- `[id]` — dynamic routes para detalhes

### Autenticação
- JWT armazenado em `localStorage` (via `lib/auth.ts`)
- Redirect automático para `/login` se não autenticado
- Token injetado em todas as chamadas à API

---

## 🔧 Comandos

```bash
# Desenvolvimento
npm run dev

# Build
npm run build

# Lint
npm run lint

# Adicionar shadcn/ui component
npx shadcn-ui@latest add button
```

---

## 🚨 Erros Comuns

1. **CORS**: Frontend roda em `:3000`, API em `:8000`. Configurar CORS no backend.
2. **Hydration mismatch**: Usar `useEffect` para valores que só existem no client
3. **Loading states**: Sempre mostrar skeleton/spinner durante fetch
4. **Type errors**: Rodar `npm run build` antes de commitar
