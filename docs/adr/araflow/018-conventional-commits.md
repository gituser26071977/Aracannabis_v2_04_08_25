# ADR-0018 — Conventional Commits + Commitlint

> **Status:** Accepted
> **Data:** 2026-06-25

## Contexto

Time distribuído, releases baseadas em tags, e necessidade de gerar changelogs automaticamente. Mensagens de commit inconsistentes dificultam tudo isso.

## Decisão

**Conventional Commits com Commitlint enforcing via Husky `commit-msg` hook.**

Tipos permitidos: `feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert, arch, adr`.

## Alternativas consideradas

| Alternativa | Prós | Contras |
|-------------|------|---------|
| **Sem padrão** | Zero friction | Inconsistência, changelog manual |
| **Conventional Commits com Hook** | Automação, ferramenta padrão | Requer disciplina |
| **Gitmoji** | Visual | Difícil de pesquisar, requer `gitmoji-cli` |

## Consequências

### Positivas
- `standard-version` ou `release-please` consegue gerar changelog automático.
- Reviewers entendem escopo do commit pelo prefixo.
- Permite filtrar por tipo (`git log --grep="^feat"`).

### Negativas
- Requer hook `commit-msg` ativo em todos os clones.
- Força desenvolvedor a pensar no tipo do commit (intencional).

## Conformidade com a Constituição

- ✅ Não contradiz 33 (Engenharia).
- ✅ Alinha com §19 (CI/CD).
