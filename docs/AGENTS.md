# docs/ — Documentação

> **Mandato:** Documentar arquitetura, decisões de design e guias de uso.

---

## Estrutura

```
docs/
├── README.md              # Visão geral, setup, quick start
├── API.md                 # Todos os 20 endpoints documentados
├── FRONTEND.md            # Arquitetura, componentes, páginas
├── DATABASE.md            # Schema PostgreSQL, migrations, queries
├── ARCHITECTURE.md        # Clean Architecture, fluxo de dependências
├── CHECKLIST.md           # Checklist de desenvolvimento por fase
├── plano_web_dashboard.md # Plano de transformação CLI → Web
└── AGENTS.md              # Este arquivo
```

---

## Regras

### Formato
- Markdown para toda documentação
- Incluir exemplos de código quando relevante
- Manter diagrams em Mermaid ou ASCII art

### Atualização
- Atualizar docs ao mudar arquitetura
- Incluir novos endpoints na API reference
- Registrar mudanças significativas no changelog

### Diagramas
- Usar Mermaid para diagramas de arquitetura
- Manter simples e legível

---

## Template para Novas Páginas

```markdown
# Título

> Descrição breve do que este documento cobre.

## Seção 1
...

## Seção 2
...
```
