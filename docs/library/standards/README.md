# AraOS Library — Standards

> **Repositório oficial de publicação dos AraOS Standards (AS-XXX)**
> **Data:** 2026-07-17
> **Status:** Inaugurado com AS-001 (Clinical Gene v1.0)

## Propósito

Este diretório é o **ponto oficial de distribuição** dos AraOS
Standards. Documentos aqui são considerados **publicações finais**
com identidade editorial AraOS e múltiplos formatos (Markdown,
HTML, PDF).

A fonte canônica permanece em `docs/standards/` (working tree de
edição e revisão).

## Catálogo

| ID | Título | Versão | Status | Formatos disponíveis |
|---|---|---|---|---|
| **AS-000** | AraOS Language Specification | v1.0 | Draft | MD · HTML · PDF* |
| **AS-001** | Clinical Gene Standard | v1.0 | **Verified** | MD · HTML · PDF* |
| **AS-002** | Clinical Expression Standard | v1.0 | Draft | MD · HTML · PDF* |

\* PDF placeholder até que pandoc+xelatex estejam disponíveis.

## Convenção de Nomenclatura

```
AS-{NNN}-{slug}-v{MAJOR}.{MINOR}.{PATCH}.{ext}
```

A versão SemVer está **no nome do arquivo** para garantir
identificação estável e independente do formato.

Exemplos:

- `AS-001-clinical-gene-v1.0.md`
- `AS-001-clinical-gene-v1.0.html`
- `AS-001-clinical-gene-v1.0.pdf`

## Política Editorial

A AraOS Library segue a política descrita em `docs/library/README.md`:

- Markdown-fonte em `docs/standards/` (editável, versionado em Git).
- Publicação oficial em `docs/library/standards/` (multi-formato).
- Renderização HTML/PDF via pandoc (quando disponível).
- Stylesheet institucional: `docs/library/stylesheets/araos.css`.
- Template LaTeX institucional: `docs/library/templates/araos.tex`.

## Como Republicar

```bash
# Markdown → HTML (depende apenas de Python + markdown)
python3 docs/library/render_html.py \
  docs/standards/AS-001-clinical-gene.md \
  docs/library/standards/AS-001-clinical-gene-v1.0.html

# Markdown → PDF (requer pandoc + xelatex)
pandoc -s --template=docs/library/templates/araos.tex \
       --pdf-engine=xelatex --toc --toc-depth=3 \
       -M title="AS-001 — AraOS Standard 001: Clinical Gene v1.0" \
       -M version="1.0" \
       -M status="Aceito" \
       -M maturity="Stable" \
       -M category="Clinical Knowledge Representation" \
       -M date="2026-07-17" \
       docs/standards/AS-001-clinical-gene.md \
       -o docs/library/standards/AS-001-clinical-gene-v1.0.pdf
```

## Status Semântico

| Status | Visibilidade |
|---|---|
| **Aceito** | Biblioteca pública. |
| **Proposto** | Disponível para revisão por pares. |
| **Obsoleto** | Mantido para histórico. |
| **Superseded** | Substituído por outro AS. |

---

**Próxima publicação prevista:** AS-002 — Clinical Expression
Standard v1.0 (Sprint 4.3 Phase 2).

**Sequência editorial revisada em 2026-07-17:** AS-003 (Clinical
Genome) será redigido **somente após** a implementação concreta
de AS-001 + AS-002 com testes ≥ 95% coverage.