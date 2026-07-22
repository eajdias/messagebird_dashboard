# Frontend — MessageBird Dashboard

> Next.js 16, Tailwind v4, Recharts, framer-motion

## Stack
- Next.js 16.2.10, React 19.2.7, TypeScript strict
- Tailwind CSS v4, PostCSS
- Radix UI, TanStack Table, Recharts
- framer-motion, lucide-react
- axios, react-hook-form, zod, sonner

## Comandos
- Dev: `npm run dev` (usa Turbopack)
- Build: `npm run build`
- Lint: `npm run lint`
- Typecheck: `npm run type-check`
- Analyze: `npm run analyze`

## Estrutura
```
app/              # App Router (login, dashboard, agents, conversations, reports, settings)
components/       # ui/, layout/, dashboard/, settings/
hooks/            # useAuth, useDashboard, useConversations, useKeyboardShortcuts
lib/              # api.ts (axios), utils.ts, logger.ts
types/            # TypeScript interfaces
```

## Convenções
- Usar Server Components por padrão, Client Components só quando necessário (interatividade, hooks, context)
- Componentes de UI em `components/ui/` seguem pattern de shadcn/ui (class-variance-authority)
- Nomes de arquivo em kebab-case
- Fetch de dados via hooks customizados em `hooks/`
- API calls via `lib/api.ts` (axios com interceptors de auth)
- Usar `cn()` (tailwind-merge + clsx) para classes condicionais
- Formulários com react-hook-form + zod validation
- Animações com framer-motion (evitar CSS transitions complexas)
- Tabelas com @tanstack/react-table

## Regras de Estilo
- Usar variantes `glass` nos cards onde disponível (backdrop-blur)
- KPIs com `accentColor` e glow no hover
- Animações stagger com delay progressivo
- Suporte obrigatório dark + light mode
- Tooltips customizados com glass effect
- Loading states com Skeleton component + shimmer

## Documentação Relacionada
- docs/FRONTEND.md — Detalhes completos do frontend
- GLASSMORPHISM-REDESIGN.md — Plano de redesign visual