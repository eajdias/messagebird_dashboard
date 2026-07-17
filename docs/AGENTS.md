# docs/ — Documentação

> **Mandato:** Documentar arquitetura, decisões de design e guias de uso.

---

## 🏗️ Estrutura

```
docs/
├── plano_web_dashboard.md       # Plano de transformação CLI → Web
├── deploy.md                    # Guia de deploy (Docker + Cloudflare)
├── banco_de_dados.md            # Schema completo do banco
├── arquitetura.md               # Arquitetura Clean Architecture
├── api_reference.md             # Documentação dos endpoints
└── changelog.md                 # Histórico de versões
```

---

## 📐 Regras

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

## 📝 Template para Novas Páginas

```markdown
# Título

> **Descrição breve do que este documento cobre.

## Seção 1
...

## Seção 2
...
```
