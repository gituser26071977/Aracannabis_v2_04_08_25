# Description

<!-- Descreva brevemente o que esta PR faz -->

## Type of change

- [ ] feat (nova funcionalidade)
- [ ] fix (correção de bug)
- [ ] refactor (refatoração sem mudança de comportamento)
- [ ] perf (otimização de performance)
- [ ] test (adição/ajuste de testes)
- [ ] docs (documentação)
- [ ] build (CI/CD, build system)
- [ ] arch (decisão arquitetural)
- [ ] adr (novo Architecture Decision Record)
- [ ] chore (manutenção)

## Constitution compliance

Verifiquei que esta PR **NÃO** contradiz:

- [ ] `docs/AraFlow/32_FINAL_PRODUCT_DECISIONS.md` (Produto)
- [ ] `docs/AraFlow/33_ENGINEERING_BLUEPRINT.md` (Engenharia)
- [ ] ADRs já publicados em `docs/adr/araflow/`

## Quality gates

- [ ] Lint passa (`npm run lint`)
- [ ] Type check passa (`npm run typecheck`)
- [ ] Testes passam (`npm test`)
- [ ] Coverage não regrediu (verificar `npm run coverage`)
- [ ] Sem `TODO` / `FIXME` / `any` no código
- [ ] Sem `console.log` (apenas `logger`)
- [ ] Commits seguem Conventional Commits
- [ ] Branch atualizada com `main` / `develop`

## Testing

<!-- Descreva como você testou esta PR -->

## Related

<!-- Link para issues, ADRs, ou outras PRs relacionadas -->

## Checklist para Reviewer

- [ ] Arquitetura respeita separação de camadas
- [ ] Domain não importa de Infrastructure
- [ ] Testes cobrem casos felizes E casos de erro
- [ ] Mensagens de erro são localizáveis (i18n)
- [ ] Performance não regrediu (especialmente em mobile)
- [ ] LGPD respeitado (opt-in explícito, PII scrubbing)
