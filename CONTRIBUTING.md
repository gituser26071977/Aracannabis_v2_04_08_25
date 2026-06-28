# Contributing — AraFlow

Obrigado por contribuir. Este documento cobre o ciclo completo de contribuição: setup, fluxo de trabalho, revisão, e processo de ADR.

## Princípios

1. **A Constituição é lei.** Não contradiga `docs/AraFlow/32_FINAL_PRODUCT_DECISIONS.md` ou `33_ENGINEERING_BLUEPRINT.md`.
2. **Strict TypeScript sempre.** Sem `any`. Sem `@ts-ignore` sem justificativa.
3. **Testes primeiro.** Toda nova lógica tem teste. Toda correção de bug tem teste de regressão.
4. **Sem TODO em produção.** Use `NotImplementedError` quando precisar stubar.
5. **Mensagens localizáveis.** Toda string visível ao usuário via i18n, nunca hard-coded.

## Setup local

```bash
# 1. Clone
git clone <repo>
cd Aracannabis_SIAP

# 2. Use Node correto
nvm use  # usa .nvmrc

# 3. Instale dependências (monorepo)
npm install

# 4. Setup Husky
npm run prepare

# 5. Rode os testes
npm test

# 6. Verifique lint e types
npm run lint
npm run typecheck
```

## Workflow

```bash
# 1. Crie branch a partir de develop
git checkout develop
git pull
git checkout -b feat/nome-da-feature

# 2. Faça commits em Conventional Commits
git commit -m "feat(session): add pause/resume to breath engine"

# 3. Antes de push: rode quality gates
npm run lint
npm run typecheck
npm test

# 4. Push
git push origin feat/nome-da-feature

# 5. Abra PR via GitHub contra develop
# - Use o template .github/PULL_REQUEST_TEMPLATE.md
# - Marque reviewers
# - Aguarde CI verde
```

## Estrutura do monorepo

```
/                     # workspace root
├── mobile/           # React Native app
├── backend/          # Fastify (apenas para o que AraOS não cobre)
├── shared-contracts/ # Tipos e schemas compartilhados
├── docs/
│   ├── AraFlow/      # Constituição (32, 33, ...)
│   └── adr/araflow/  # ADRs publicadas
├── scripts/          # scripts utilitários
└── .github/          # workflows + templates
```

## Path aliases (mobile)

| Alias | Aponta para |
|-------|-------------|
| `@core/*` | `mobile/src/core/*` |
| `@features/*` | `mobile/src/features/*` |
| `@shared/*` | `mobile/src/shared/*` |
| `@infrastructure/*` | `mobile/src/infrastructure/*` |
| `@contracts/*` | `shared-contracts/src/*` |

Aliases são resolvidos por Babel (build) e Jest (testes) e TypeScript (typecheck). Mantenha os três sincronizados.

## Camadas e direção de imports

```
core       ←   features
   ↑           ↑
   └─── shared ───┘
         ↑
   infrastructure
```

Regras:
- `core` NUNCA importa de `features`, `shared`, ou `infrastructure`.
- `shared` NUNCA importa de `features`, `core`, ou `infrastructure`.
- `features` PODE importar de `core`, `shared`, `infrastructure`.
- `infrastructure` PODE importar de `core` (apenas tipos) e `shared`.

## Como criar um ADR

1. Copie `docs/adr/araflow/template.md` para `docs/adr/araflow/NNNN-titulo-kebab-case.md`.
2. Preencha todas as seções.
3. Adicione entrada no índice em `docs/adr/araflow/README.md`.
4. Abra PR com label `adr`.
5. ADR entra em vigor após merge.

ADRs publicados são IMUTÁVEIS. Para mudar uma decisão, crie novo ADR referenciando o anterior.

## Como abrir PR

1. Use o template `.github/PULL_REQUEST_TEMPLATE.md`.
2. Marque todos os checkboxes aplicáveis.
3. Vincule a issue ou ADR relacionada.
4. Aguarde revisão de pelo menos 1 maintainer.
5. CI deve estar verde.

## Code review — o que esperamos

**Reviewer:**
- Arquitetura respeita separação de camadas.
- Testes cobrem happy path E error path.
- Mensagens de erro localizáveis.
- Performance não regrediu (especialmente em mobile).
- LGPD respeitado.
- Sem secrets, sem PII em logs.
- Branch atualizada com a base.

**Author:**
- Responda a todos os comentários.
- Se discordar, justifique tecnicamente.
- Não force-merge; se há bloqueio, converse.

## Estilo de código

- ESLint + Prettier (não discuta estilo, formate).
- 2 espaços, single quotes, semicolons.
- Imports agrupados: external → @aliased → relative.

## Onde pedir ajuda

- `#araflow-dev` no Slack.
- Dúvidas arquiteturais: review do CTO em PR.
- Dúvidas de produto: review do CPO em issue.
