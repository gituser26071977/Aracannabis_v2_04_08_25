# Post-RC1 Refactor — Backlog estrutural

> Backlog de melhorias **estruturais** identificadas durante a fase RC1, mas **não implementáveis** na branch `rc1-demo` por restrição do brief:
>
> *"Caso alguma necessidade estrutural seja encontrada: registrar em `POST_RC1_REFACTOR.md`. Não implementar."*
>
> Toda entrada aqui será revisada durante o planejamento do **RC2**.

---

## Convenção de ID

Cada item recebe um `POST-RC1-NNN` para rastreamento. Os IDs são estáveis — manter ao mover entre seções.

---

## Itens identificados

### POST-RC1-001 — Adicionar helper de "último pipeline" no backend

- **Origem:** Validation 4 (Developer) — devs não sabem se há um endpoint para "listar últimos pipelines executados pelo tenant".
- **Impacto atual:** workaround manual (listar sessions + filtrar).
- **Solução proposta:** `GET /api/v1/knowledge/pipelines/recent?tenant_id=&limit=` (somente leitura, com permissão `knowledge.read`).
- **Escopo:** REST API (Gate 3.x).
- **Estimativa:** 1 sprint pequeno.
- **Status:** 📝 Backlog.

---

### POST-RC1-002 — DTO `Correlation.coefficient` deve expor `p_value` opcional

- **Origem:** Validation 2 (Research) — pesquisador pediu intervalo de confiança explícito.
- **Impacto atual:** só o coeficiente é retornado; o `confidence` no DTO atual **não é p-valor**, é score do motor de regras (confunde pesquisador).
- **Solução proposta:** adicionar campo opcional `p_value` no DTO `Correlation` e **renomear** o `confidence` para `rule_confidence` para desfazer a ambiguidade.
- **Escopo:** DTO + documentação (Gate 3.x).
- **Impacto na UI:** mudar label em `CorrelationsCard.js` (de "Confiança" para "Confiança da regra").
- **Status:** 📝 Backlog. Requer migração de consumidores.

---

### POST-RC1-003 — Endpoint para listar `rule_id` versionados

- **Origem:** Validation 2 (Research) — pesquisador quer ver a lista de regras que estão em produção.
- **Impacto atual:** `rule_id` aparece como string opaca nos cards; pesquisador não sabe auditar.
- **Solução proposta:** `GET /api/v1/knowledge/rules?version=&status=` retornando `[{ rule_id, version, status, description, citation }]`.
- **Escopo:** REST API + persistência (Gate 3.x).
- **Estimativa:** 1 sprint.
- **Status:** 📝 Backlog.

---

### POST-RC1-004 — Página de detalhe do Knowledge Graph

- **Origem:** Validation 1 (Clinical) — médico pediu para "clicar num nó e ver a evidência".
- **Impacto atual:** grafo é read-only mas não-clicável (apenas zoom/pan).
- **Solução proposta:** ao clicar num nó, abrir painel lateral com: descrição do gene, hipóteses relacionadas, correlações em que aparece, citações bibliográficas.
- **Escopo:** UI + 1 endpoint novo (`GET /api/v1/knowledge/genes/{id}/evidence`).
- **Status:** 📝 Backlog. Wave 5+.

---

### POST-RC1-005 — Suporte a múltiplos `methods` simultâneos no `pipelines/run`

- **Origem:** Validation 2 (Research) — pesquisador pediu para rodar Pearson + Spearman juntos.
- **Impacto atual:** o array `methods` é aceito mas o backend filtra para um único método.
- **Solução proposta:** backend retorna lista de `correlations` agrupada por método, com flag `method` em cada item (já existe, mas só 1 método).
- **Escopo:** Domain + Application + DTO + UI.
- **Status:** 📝 Backlog. Mudança estrutural.

---

### POST-RC1-006 — Cohorts visíveis na UI

- **Origem:** Validation 1 (Clinical) — médico quer comparar este paciente com outros similares.
- **Impacto atual:** `cohort` foi desescopado do Gate 2; apenas consumido internamente.
- **Solução proposta:** novo card **"Comparar com coorte"** com 1 endpoint + 1 card.
- **Escopo:** REST + UI + persistência.
- **Status:** 📝 Backlog. Wave 5+.

---

### POST-RC1-007 — Filtros na linha do tempo

- **Origem:** Validation 2 (Research) — pesquisador quer filtrar timeline por tipo de evento.
- **Impacto atual:** timeline mostra todos os eventos.
- **Solução proposta:** chips de filtro por categoria (genome / correlation / hypothesis / graph / replay).
- **Escopo:** UI only.
- **Status:** 📝 Backlog. Mudança estrutural na VM (timeline deve ter `category`).

---

### POST-RC1-008 — Onboarding first-run

- **Origem:** Validation 1 e Validation 3 — primeiro acesso é confuso sem guia.
- **Impacto atual:** Demo Mode é a única "guia". Sem demo, primeiro run é assustador.
- **Solução proposta:** tooltip walkthrough de 3 passos no primeiro acesso (não-Demo).
- **Escopo:** UI only (intro.js ou shepherd.js).
- **Status:** 📝 Backlog. Wave 5+.

---

### POST-RC1-009 — Internacionalização (i18n)

- **Origem:** Brief — *"i18n deferred para V2"*.
- **Impacto atual:** strings hardcoded em PT-BR.
- **Solução proposta:** mover todos os textos para `i18n/pt-BR.json` + `i18n/en.json` + hook `useT()`.
- **Escopo:** UI only (componentes + página).
- **Status:** 📝 Backlog. Wave 5+.

---

### POST-RC1-010 — Mobile layout

- **Origem:** Brief — *"Mobile deferred"*.
- **Impacto atual:** layout desktop-first; em mobile fica empilhado mas a Timeline rail fica espremida.
- **Solução proposta:** revisar grid em `< md`; mover Timeline rail para accordion abaixo do último card em mobile.
- **Escopo:** UI only.
- **Status:** 📝 Backlog. Wave 5+.

---

### POST-RC1-011 — Dark mode

- **Origem:** Feedback informal — "ficaria bem em dark".
- **Impacto atual:** tokens MUI são light-only.
- **Solução proposta:** criar `tokens.dark.js` e Theme toggle (sem mudar arquitetura).
- **Escopo:** tokens + theme + (opcional) toggle na UI.
- **Status:** 📝 Backlog. Wave 5+.

---

### POST-RC1-012 — Storybook binary install

- **Origem:** Gate 3 — stories escritas mas binary não instalado (CRA 5 + React 18 + Storybook 7 tem friction conhecida).
- **Impacto atual:** stories são arquivos `.stories.js` válidos mas não rodáveis.
- **Solução proposta:** `npx storybook@latest init --type=react` em branch dedicada, isolada desta.
- **Escopo:** devDependencies + scripts + `.storybook/`.
- **Status:** 📝 Backlog. Não é urgente para RC1.

---

### POST-RC1-013 — Paginação e filtros em `pipelines/run` history

- **Origem:** Consumer Review 🟡 — deferred.
- **Impacto atual:** histórico cresce indefinidamente.
- **Solução proposta:** `?limit=&offset=&patient_id=&date_from=&date_to=` no endpoint de listagem.
- **Escopo:** REST + persistência.
- **Status:** 📝 Backlog.

---

### POST-RC1-014 — Layout dagre para grafos grandes

- **Origem:** Wave 4 brief — deferred.
- **Impacto atual:** layout é círculo determinístico (bom até ~20 nós; ruim acima).
- **Solução proposta:** adicionar `@dagrejs/dagre` ou similar; layout adaptativo.
- **Escopo:** UI only.
- **Status:** 📝 Backlog. Wave 5+.

---

### POST-RC1-015 — Integração com prontuário eletrônico (PEP)

- **Origem:** Validation 1 (Clinical) — médico perguntou "como populo isso com dados reais?".
- **Impacto atual:** nenhuma integração; dados vêm de CSV/JSON manual.
- **Solução proposta:** conector HL7/FHIR + endpoint de intake `POST /api/v1/clinical/intake`.
- **Escopo:** Domain + Application + REST + Integração externa.
- **Status:** 📝 Backlog. Mudança grande; requer ADR novo.

---

## Como adicionar novos itens

Quando uma sessão de validação revelar uma necessidade estrutural:

1. Não implementar na branch `rc1-demo`.
2. Adicionar item aqui com o próximo `POST-RC1-NNN`.
3. Marcar como `📝 Backlog`.
4. Incluir: origem (qual validação), impacto, solução proposta, escopo, estimativa.

Quando for revisar para o RC2:

1. Classificar cada item como: `❌ Descartado`, `🟡 Aceito, mover para ADR`, `🟢 Aceito, entrar no RC2 backlog`.
2. Items `🟢` viram tarefas no `RC2_BACKLOG.md`.
3. Items `🟡` exigem ADR antes de implementação.

---

*Esse arquivo vive na branch `rc1-demo` e **deve** ser mergeado junto com o RC1 — é insumo para o planejamento do RC2, não resíduo.*