# ADR-0016 — npm workspaces para monorepo

> **Status:** Accepted
> **Data:** 2026-06-25

## Contexto

AraFlow tem três artefatos compartilhados:

1. **mobile/** — App React Native (iOS + Android).
2. **backend/** — Backend próprio (Fastify), apenas para componentes não cobertos pelo AraOS.
3. **shared-contracts/** — Tipos e schemas Zod compartilhados entre mobile e backend.

A pergunta: monorepo ou polyrepo? E se monorepo, qual ferramenta?

## Decisão

**Monorepo com npm workspaces.**

## Alternativas consideradas

| Alternativa | Prós | Contras |
|-------------|------|---------|
| **Polyrepo** | Independência total de releases | Overhead de gestão, contratos precisam ser publicados como npm package, mais CI |
| **Yarn workspaces** | Mesma ideia do npm workspaces | yarn é mais pesado, berry tem breaking changes |
| **pnpm** | Disk-efficient, content-addressable store | Time não tem experiência |
| **Nx / Turborepo** | Build cache, generators | Custo de adoção, dependência de ferramenta externa |
| **Lerna** | Time testou em outros projetos | Lerna virou legacy; pouco ativa |
| **npm workspaces (escolhido)** | Built-in, zero config, team já usa npm | Limitações de hoisting em alguns pacotes nativos RN |

## Consequências

### Positivas
- Zero dependência externa.
- Time já familiarizado com npm.
- Setup mínimo (`workspaces` no `package.json` raiz).
- Path aliases via `paths` no `tsconfig.json` + `babel-plugin-module-resolver`.

### Negativas
- Hoisting de pacotes nativos RN pode exigir `nohoist` em `package.json`.
- Sem build cache sofisticado (precisamos implementar manualmente se necessário).

### Neutras
- Build e CI devem ser orquestrados manualmente (scripts npm + workflows GH Actions).

## Conformidade com a Constituição

- ✅ Não contradiz 32 (Decisões de Produto).
- ✅ Não contradiz 33 (Engenharia).
- ✅ Alinha com §3 (Estrutura do Projeto) e §19 (CI/CD).
