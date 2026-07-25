# RC1 Release Inventory — Estado Atual do Repositório

> **Inspeção não-destrutiva.** Nenhum comando destrutivo foi executado (sem `git checkout`, `git restore`, `git reset`, `git clean`, `git stash`, `git commit`, `git tag`, `git push`, `git rebase`, `git merge`, `git rm`, `git mv`).
>
> **Data do inventário:** 2026-07-25
> **Branch atual:** `rc1-demo` (branched from `main` @ `4398ceb`)
> **Working tree:** modificado (12 tracked + 104 untracked = 116 entradas em `git status --short`)

---

## 1. Executive Summary

O repositório contém:

- **Worktree limpo do `rc1-demo`:** a branch foi criada mas **nenhum commit foi feito** nela. Todas as edições de Demo Mode / UX Polish / 7 docs novos continuam como modificações de working tree (não-comitadas).
- **Mudanças legítimas pendentes de commit:** deps do Wave 4 (`tanstack/react-query`, `reactflow`, testing-library, msw), rota `/clinical-pipeline`, e o módulo `clinicalPipeline` inteiro (21 arquivos) — **são RC1 Core**.
- **Material de sprints anteriores não-comitado:** ~80 arquivos de Sprints 3.2, 4.1, 4.2, 4.3, 4.4, 4.5 que existem no disco mas nunca foram commitados. Estão como untracked.
- **Material experimental/legacy:** alguns arquivos (`docs/AraFlow/codex-vps-handoff-prompt.md`, `.coverage`) claramente não pertencem ao RC1.

**Risco de perda de trabalho:** ALTO. Há centenas de arquivos Python e MD no disco que **não estão sob versionamento**. Remover o working tree agora destruiria sprints inteiros. Qualquer operação de Release DEVE preservar tudo.

---

## 2. Estatísticas

| Categoria | Quantidade | % |
|-----------|-----------|---|
| **A** — RC1 Core | ~38 | 33% |
| **B** — RC1 Demo | ~30 | 26% |
| **C** — Legacy / Experimental | ~14 | 12% |
| **D** — Generated | ~20 | 17% |
| **E** — Ambiguous | ~14 | 12% |
| **TOTAL** | **116** | 100% |

> Obs.: 116 entradas em `git status --short`. Algumas entradas são diretórios inteiros (ex.: `docs/` representa 52 arquivos).

### Resumo por tipo Git

```
?? untracked:   104
 M modified:     12
```

### Modificações tracked (12)

```
.coverage                                     M  (Bin 77824 → 53248 bytes)
.env.staging                                  M  (-1 linha)
.gitignore                                    M  (+1 linha: mobile/web/dist/)
app_cors_livre.py                             M  (+27 linhas — registra 4 blueprints)
araos/clinical/timeline/__init__.py           M  (Sprint 4.1 — re-exports)
araos/platform/events/catalog.py              M  (+143 linhas — eventos NEURODEVELOPMENTAL)
araos/platform/identity/permissions.py        M  (+183 linhas — permissions Sprint 1-3)
araos/platform/tenant/models.py               M  (+23 linhas — AuditFieldsMixin)
docs/AraFlow/49_GO_NO_GO.md                   M  (AraFlow)
frontend/package-lock.json                    M  (+1121 linhas — deps do Wave 4)
frontend/package.json                         M  (+8 linhas — deps do Wave 4)
frontend/src/App.js                           M  (+2 linhas — rota /clinical-pipeline)
```

---

## 3. Categoria A — RC1 Core (~38 arquivos)

Arquivos essenciais do RC1 que **devem** ir na Release. Critério: foram entregues via Gates 1, 2, 3 ou são fundação da Plataforma de Inteligência Clínica.

### A.1 — Domain Layer (AraOS Clinical)

| Caminho | Origem | Confiança |
|---------|--------|-----------|
| `araos/clinical/context/` (untracked, 14 arquivos) | Sprint 4.2 — Clinical Context Engine | Alta |
| `araos/clinical/event_store/` (untracked, 6 arquivos) | Sprint 3.1 — Clinical Event Engine | Alta |
| `araos/clinical/explainability/` (untracked, 2 arquivos) | Sprint 4.1 — Explainability Registry | Alta |
| `araos/clinical/genome/` (untracked, 8+ arquivos) | Sprint 4.3 — Clinical Genome Engine | Alta |
| `araos/clinical/knowledge/` (untracked, 4 subdirs) | Sprint 4.4/4.5 — Knowledge Engine | Alta |
| `araos/clinical/observability/` (untracked, 2 arquivos) | Sprint 4.1 — Observability | Alta |
| `araos/clinical/timeline/application/` (untracked) | Sprint 4.1 — Timeline Application | Alta |
| `araos/clinical/timeline/domain/` (untracked) | Sprint 4.1 — Timeline Domain | Alta |
| `araos/clinical/timeline/__init__.py` (modified) | Compat shim Sprint 4.1 | Alta |

### A.2 — REST API Layer (Gate 2 — frozen)

| Caminho | Origem | Confiança |
|---------|--------|-----------|
| `interfaces/__init__.py` | untracked — novo pacote | Alta |
| `interfaces/rest/__init__.py` | untracked — wrapper Flask | Alta |
| `interfaces/rest/v1/__init__.py` | untracked — blueprint export | Alta |
| `interfaces/rest/v1/auth.py` | untracked — auth header contract | Alta |
| `interfaces/rest/v1/dto.py` | untracked — 11 DTOs frozen | Alta |
| `interfaces/rest/v1/errors.py` | untracked — error envelope | Alta |
| `interfaces/rest/v1/knowledge.py` | untracked — 9 endpoints frozen | Alta |
| `interfaces/rest/v1/mappers.py` | untracked — DTO mappers | Alta |
| `interfaces/rest/v1/observability.py` | untracked — request hooks | Alta |

### A.3 — Routes (blueprints Flask)

| Caminho | Origem | Confiança |
|---------|--------|-----------|
| `routes/_helpers.py` | Sprint 4.1 helper compartilhado | Alta |
| `routes/clinical_context.py` | Sprint 4.2 blueprint | Alta |
| `routes/explainability.py` | Sprint 4.1 blueprint | Alta |
| `routes/intelligence_timeline.py` | Sprint 4.1 blueprint | Alta |
| `routes/neuro_registry.py` | Sprint 3.2 blueprint | Alta |
| `routes/neuro_scales.py` | Sprint 1/2 blueprint | Alta |

### A.4 — Migrations (Alembic)

| Caminho | Origem | Confiança |
|---------|--------|-----------|
| `migrations/versions/2026_07_15_clinical_event_engine.py` | Sprint 3.1 | Alta |
| `migrations/versions/REDACTED.py` | Sprint 1 | Alta |
| `migrations/versions/REDACTED.py` | Sprint 3.2 | Alta |
| `migrations/versions/REDACTED.py` | Sprint 4.1 | Alta |
| `migrations/versions/2026_07_18_clinical_context_s42.py` | Sprint 4.2 | Alta |
| `migrations/versions/REDACTED.py` | Sprint 4.5 | Alta |
| `migrations/versions/REDACTED.py` | Sprint 4.5 | Alta |
| `migrations/versions/2026_07_22_merge_araos_heads.py` | Sprint 4.5 W1.2 | Alta |

### A.5 — Clinical Pipeline Explorer (frontend)

| Caminho | Origem | Confiança |
|---------|--------|-----------|
| `frontend/src/features/clinicalPipeline/api/knowledgeApi.js` | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/hooks/` (5 arquivos) | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/mappers/` (2 arquivos) | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/types/knowledge.d.ts` | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/CardShell.js` + test + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/PipelineCard.js` + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/PatientCard.js` | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/GenomeCard.js` | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/CorrelationsCard.js` + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/HypothesesCard.js` + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/KnowledgeGraphViewer.js` + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/ReplayPanel.js` + test + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/TimelineRail.js` + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/features/clinicalPipeline/components/PipelineInputBar.js` + test + story | Wave 4 / Gate 3 | Alta |
| `frontend/src/pages/ClinicalPipelineExplorer/index.js` | Wave 4 / Gate 3 | Alta |
| `frontend/src/pages/ClinicalPipelineExplorer/ClinicalPipelineExplorer.js` | Wave 4 / Gate 3 | Alta |
| `frontend/src/lib/queryClient.js` (presume — não listado mas Wave 4) | Wave 4 / Gate 3 | Média |
| `frontend/src/mocks/handlers.js` | Wave 4 / Gate 3 | Média |
| `frontend/src/mocks/server.js` | Wave 4 / Gate 3 | Média |
| `frontend/src/setupTests.js` | Wave 4 / Gate 3 | Média |

### A.6 — Modified tracked que são RC1 Core

| Caminho | Razão | Confiança |
|---------|-------|-----------|
| `frontend/package.json` (+`@tanstack/react-query`, `reactflow`, testing-library, msw) | Wave 4 deps | Alta |
| `frontend/package-lock.json` | Lock do `package.json` | Alta |
| `frontend/src/App.js` (+import + rota `/clinical-pipeline`) | Wave 4 route wiring | Alta |
| `app_cors_livre.py` (+4 blueprints register) | Sprints 3.2/4.1/4.2/4.5 wiring | Alta |

### A.7 — Specialties (Neurodevelopmental)

| Caminho | Origem | Confiança |
|---------|--------|-----------|
| `araos/specialties/neurodevelopmental/` (8+ arquivos) | Mission 9 / Sprint 1-3 | Alta |

---

## 4. Categoria B — RC1 Demo (~30 arquivos)

Arquivos exclusivos da branch `rc1-demo` — UX, narrative, Demo Mode, validation scripts. **Não** pertencem ao núcleo, mas foram criados **explicitamente** pela missão RC1 Demo.

### B.1 — Demo Mode (frontend)

| Caminho | Confiança |
|---------|-----------|
| `frontend/src/features/clinicalPipeline/demo/fixture.js` | Alta |
| `frontend/src/features/clinicalPipeline/demo/DemoBanner.js` | Alta |
| `frontend/src/features/clinicalPipeline/demo/useDemoMode.js` | Alta |

### B.2 — Documentação de Demo

| Caminho | Confiança |
|---------|-----------|
| `docs/RC1_DEMO_SCRIPT.md` | Alta |
| `docs/CLINICAL_VALIDATION.md` | Alta |
| `docs/RESEARCH_VALIDATION.md` | Alta |
| `docs/INVESTOR_VALIDATION.md` | Alta |
| `docs/DEVELOPER_VALIDATION.md` | Alta |
| `docs/RC1_DEMO_CHECKLIST.md` | Alta |
| `docs/POST_RC1_REFACTOR.md` | Alta |

### B.3 — Componentes editados (UX Polish + Storytelling)

Estes **são** RC1 Core **e** Demo: as edições de copy são do escopo Demo. Listados aqui para rastreamento do diff:

| Caminho | Edição | Confiança |
|---------|--------|-----------|
| `frontend/src/features/clinicalPipeline/components/PipelineInputBar.js` | labels PT-BR + placeholder condicional | Alta |
| `frontend/src/features/clinicalPipeline/components/PipelineInputBar.test.js` | test atualizado para novos labels | Alta |
| `frontend/src/features/clinicalPipeline/components/PipelineCard.js` | títulos viraram perguntas | Alta |
| `frontend/src/features/clinicalPipeline/components/GenomeCard.js` | parágrafo explicativo | Alta |
| `frontend/src/features/clinicalPipeline/components/CorrelationsCard.js` | "ρ mais forte" + parágrafo | Alta |
| `frontend/src/features/clinicalPipeline/components/HypothesesCard.js` | disclaimer "não sugere diagnóstico" | Alta |
| `frontend/src/features/clinicalPipeline/components/PatientCard.js` | "Janela analisada" | Alta |
| `frontend/src/features/clinicalPipeline/components/ReplayPanel.js` | título pergunta | Alta |
| `frontend/src/features/clinicalPipeline/components/KnowledgeGraphViewer.js` | título + "relações" | Alta |
| `frontend/src/features/clinicalPipeline/components/TimelineRail.js` | "Linha do tempo" | Alta |
| `frontend/src/pages/ClinicalPipelineExplorer/ClinicalPipelineExplorer.js` | DemoMode import + auto-seed + banner | Alta |

---

## 5. Categoria C — Legacy / Experimental (~14 arquivos)

Material de sprints/projetos anteriores. **Não decidir removê-los.** Apenas identificar.

### C.1 — AraFlow (produto irmão standalone)

| Caminho | Conteúdo | Confiança |
|---------|----------|-----------|
| `docs/AraFlow/codex-vps-handoff-prompt.md` | Prompt operacional para deploy AraFlow em VPS separado (Fastify + nginx + RN-web em `flow.arapath.com.br`) | Alta |
| `docs/AraFlow/49_GO_NO_GO.md` (modified) | Documento de go/no-go AraFlow | Alta |

> AraFlow é um **produto separado** que roda em subdomínio próprio e não toca os containers AraOS. Não pertence ao RC1 do Knowledge Engine.

### C.2 — Memory araos (Claude auto-memory)

| Caminho | Conteúdo | Confiança |
|---------|----------|-----------|
| `memory/REDACTED.md` | Memória auto-persistente do Claude sobre Sprint 3.1 do Neurodevelopmental | Alta |

> O subdiretório `memory/` **não está versionado** por convenção do Claude Code. É arquivo de sistema, não código de release. Mas o usuário pode querer preservá-lo manualmente.

---

## 6. Categoria D — Generated (~20 arquivos)

Artefatos gerados automaticamente. Não devem ser commitados; devem estar em `.gitignore`.

### D.1 — Python bytecode (`__pycache__`)

| Origem | Confiança |
|--------|-----------|
| `interfaces/__pycache__/` | Alta |
| `interfaces/rest/__pycache__/` | Alta |
| `interfaces/rest/v1/__pycache__/` (6 arquivos .pyc) | Alta |
| `araos/clinical/context/__pycache__/` | Alta |
| `araos/clinical/event_store/__pycache__/` | Alta |
| `araos/clinical/explainability/__pycache__/` | Alta |
| `araos/clinical/genome/__pycache__/` | Alta |
| `araos/clinical/knowledge/__pycache__/` | Alta |
| `araos/clinical/observability/__pycache__/` | Alta |
| `araos/clinical/timeline/__pycache__/` | Alta |
| `tests/*/__pycache__/` (em cada sprint test dir) | Alta |
| `araos/specialties/neurodevelopmental/__pycache__/` | Alta |

### D.2 — Cobertura

| Origem | Confiança |
|--------|-----------|
| `.coverage` (modified, 53248 bytes) | Arquivo binário de coverage data do pytest | Alta |

---

## 7. Categoria E — Ambiguous (~14 arquivos)

Itens cuja origem **não pode ser determinada com segurança** apenas por inspeção. Requerem revisão humana.

### E.1 — ADRs / Standards (duplicação aparente)

Existem **dois conjuntos** de ADRs e Standards:

- `docs/adr/0001-clinical-event-engine.md`, `0002-...`, `0006-...` (untracked, 3 arquivos) — versão "source"
- `docs/library/adrs/ADR-0008-...md`, `REDACTED.0.md` + `.html` (untracked, 6+ arquivos) — versão "published"

**Origem ambígua:** o conjunto em `docs/library/` é a **versão publicada** do AraOS Library (Markdown + HTML + PDF + templates LaTeX/CSS). O conjunto em `docs/adr/` é a versão **canônica**. Os 2 coexistem por design (ADR-0001/0002 + ASM-001 + ADR-0006 só existem em `library/`; ADR-0001/0002/0006 só em `adr/`).

**Recomendação:** revisar se a duplicação é intencional ou se `docs/library/` deveria ser link/referência, não cópia.

### E.2 — Reports massivos em `docs/` (52 arquivos untracked)

Lista parcial:
- `docs/REDACTED.md`
- `docs/REDACTED.md`
- `docs/REDACTED.md`
- `docs/API_CONSUMER_REVIEW.md`
- `docs/ARCHITECTURE_BASELINE_v1.md`
- `docs/ARCHITECTURE_FREEZE_REPORT.md`
- `docs/DEPENDENCY_MAP.md`
- `docs/FOUNDATION_FREEZE_REPORT.md`
- `docs/PUBLIC_API_MANIFEST.md`
- `docs/SPRINT_3_3_DESIGN.md`
- `docs/SPRINT_4_1_REPORT.md` ... `docs/SPRINT_4_5_REST_INVENTORY.md`
- `docs/RC1_GATE_1_REPORT.md` ... `docs/RC1_GATE_3_REPORT.md`
- `docs/RC1_DEPLOY_REPORT.md`, `RC3_RELEASE_REPORT.md`, `RC1_GATE1_PERFORMANCE_REVIEW.md`
- `docs/NEURODEVELOPMENTAL_SPRINT*.md` (4 arquivos)
- `docs/OPERATIONS_AUDIT.md`, `OPERATOR_RUNBOOK.md`, etc.
- `docs/AraFlow/codex-vps-handoff-prompt.md` (classificado em C)
- `docs/AraFlow/49_GO_NO_GO.md` (modified, classificado em C)
- `docs/library/...` (ver E.1)
- `docs/meta/ASM-001-specification-meta-model.md`
- `docs/ontology/README.md`
- `docs/standards/AS-000-language-specification.md` ... `AS-004-clinical-knowledge.md`

**Origem ambígua:** muitos desses reports são **RC1 Core** (Gate 1/2/3 reports, Architecture Freeze, Foundation Freeze, Public API Manifest) e devem ir para a Release. Outros (NEURODEVELOPMENTAL_SPRINT*, OPERATOR_*) são de produtos/módulos adjacentes. **Requer triagem humana.**

### E.3 — Tests (`tests/*` untracked)

| Diretório | Origem provável | Confiança |
|-----------|------------------|-----------|
| `tests/clinical_event_store/` | Sprint 3.1 | Alta |
| `tests/conformance/` | **VAZIO** — diretório criado mas sem testes | Alta |
| `tests/genome_sprint_4_3_phase_2/` | Sprint 4.3 | Alta |
| `tests/intel_sprint_4_1/` | Sprint 4.1 | Alta |
| `tests/intel_sprint_4_2/` | Sprint 4.2 | Alta |
| `tests/intel_sprint_4_3/` | Sprint 4.3 | Alta |
| `tests/neuro_sprint1/`, `neuro_sprint2/` | Sprints 1/2 Neurodevelopmental | Alta |
| `tests/neurodev_sprint_3_2/` | Sprint 3.2 Neurodevelopmental | Alta |
| `tests/sprint_4_4/`, `sprint_4_4_5/`, `sprint_4_5/` | Sprints 4.4 / 4.4.5 / 4.5 | Alta |

> Todos parecem ser testes oficiais de sprints finalizados. **Requer confirmação** se devem ser mergeados como parte do RC1 ou mantidos em branch separada.

### E.4 — frontend/src/pages/neuro/ + neuroService.js

| Caminho | Conteúdo | Confiança |
|---------|----------|-----------|
| `frontend/src/pages/neuro/NeuroScaleApplyPage.js` | Página de aplicação de escalas neuro | Média |
| `frontend/src/pages/neuro/NeuroScalesListPage.js` | Listagem de escalas neuro | Média |
| `frontend/src/services/neuroService.js` | Service client para neuro API | Média |

> **Origem:** Sprint 1-2 do Neurodevelopmental. Não fazem parte do RC1 Knowledge Engine — são do módulo Neuro. Requer decisão: merge junto com o RC1 ou branch separada.

---

## 8. Arquivos que merecem decisão humana

### Decisões críticas (bloqueiam a Release)

| ID | Decisão | Risco se não resolvido |
|----|---------|------------------------|
| **DEC-001** | Commitar tudo do `rc1-demo` em uma única commit na branch `rc1-demo`? Ou quebrar em commits por responsabilidade (Demo Mode / UX Polish / 7 docs)? | Histórico ilegível vs esforço de separar |
| **DEC-002** | O que fazer com as 80+ arquivos untracked de Sprints 3.2/4.1/4.2/4.3/4.4/4.5 que nunca foram commitados? Merge tudo em uma commit histórica + branch taggeada? Ou commitar por sprint? | Trabalho de meses pode ser perdido se a working tree for limpa |
| **DEC-003** | A branch `main` deve ser taggeada com `rc1.0.0` no commit atual (`4398ceb`) **antes** ou **depois** de qualquer merge? | Tag prematura captura estado incompleto |
| **DEC-004** | Os ADRs duplicados em `docs/library/` vs `docs/adr/` são por design ou acúmulo? | Inconsistência documental |
| **DEC-005** | `tests/conformance/` é um diretório vazio — manter como placeholder intencional ou remover? | Ruído no repo |

### Decisões menores

| ID | Decisão |
|----|---------|
| DEC-006 | `frontend/src/pages/neuro/*` + `neuroService.js`: merge no RC1 ou branch `neuro/*`? |
| DEC-007 | `memory/REDACTED.md`: versionar? ignorar? mover para fora do repo? |
| DEC-008 | `docs/AraFlow/codex-vps-handoff-prompt.md`: é produto irmão ou deveria estar em outro repo? |
| DEC-009 | `.env.staging` modificado (perdeu 1 linha): restaurar? o que estava antes? |
| DEC-010 | `__pycache__/` em diretórios untracked: adicionar a `.gitignore` antes de qualquer commit. |

---

## 9. Avaliação de Risco

### Existe algum arquivo cuja remoção possa causar perda de trabalho?

**SIM — risco ALTO.**

- `araos/clinical/{context,event_store,explainability,genome,knowledge,observability}/` (~40 arquivos Python) — contém Domain + Application + Infrastructure de **5 sprints finalizadas**. Remover destrói meses de trabalho.
- `interfaces/rest/v1/*` (8 arquivos Python) — REST API completa do Gate 2 (Foundation-Freeze compliant).
- `routes/{clinical_context,explainability,intelligence_timeline,neuro_registry,neuro_scales,_helpers}.py` — blueprints Flask registrados em `app_cors_livre.py`.
- `migrations/versions/2026_07_*.py` (8 arquivos) — migrations Alembic que **devem** ser aplicadas antes do código.
- `tests/*` (12 diretórios, ~70+ testes) — suite de testes oficial.
- `araos/specialties/neurodevelopmental/*` — módulo Neuro inteiro.

### Existe algum arquivo claramente temporário?

**SIM:**

- `.coverage` (Bin 77824 → 53248 bytes) — dado binário de coverage. **Já está no `.gitignore`** mas foi modificado (talvez por execução local de pytest).
- `**/__pycache__/` (15+ diretórios) — bytecode Python. **Já está no `.gitignore` mas não impede criação dos untracked**.
- `docs/AraFlow/codex-vps-handoff-prompt.md` — prompt operacional. Temporário para o deploy, não é código.

### Existe algum arquivo duplicado?

**SIM:**

- `docs/adr/0001-clinical-event-engine.md` vs `docs/library/...` — versão source vs versão published
- `docs/adr/REDACTED.md` vs `docs/library/adrs/REDACTED.0.md`
- `docs/standards/AS-000-language-specification.md` vs `docs/library/standards/AS-000-language-specification-v1.0.md`
- `docs/meta/ASM-001-specification-meta-model.md` vs `docs/library/meta/REDACTED.0.md`

### Existe algum arquivo que deveria estar no `.gitignore`?

**SIM:**

- `__pycache__/` (Python bytecode) — geralmente já está; precisa garantir que vale para todos os novos diretórios (`araos/clinical/*/`, `interfaces/rest/v1/`, `tests/*/`)
- `*.pyc` (redundante)
- `.coverage` (já está)
- `frontend/node_modules/` (já está, presumido)
- `frontend/build/` (já está, presumido)

### Existe algum arquivo inesperadamente versionado?

**SIM:**

- `.env.staging` (modificado) — secrets/envs não deveriam estar versionados. Modificação pode indicar mudança acidental de credencial.

---

## 10. Recomendações

### Antes de qualquer operação destrutiva

1. **Tirar snapshot completo do working tree** em uma branch de backup antes de qualquer operação:
   ```bash
   git switch -c backup/pre-rc1-inventory-20260725
   git add -A
   git commit -m "snapshot: working tree antes da decisão de Release"
   ```
   (Não executar agora — apenas documentar a recomendação.)

2. **Revisar este inventário com o time** antes de qualquer commit/tag/push.

3. **Resolver DEC-001..DEC-010** antes de criar a tag.

### Ordem de operações sugerida (quando autorizada)

1. Resolver DEC-002 (commitar material não-versionado de sprints anteriores) **antes** de qualquer outra coisa.
2. Adicionar `__pycache__/` global ao `.gitignore` (DEC-010).
3. Resolver DEC-001 (estratégia de commits no `rc1-demo`).
4. Resolver DEC-003 (timing da tag `rc1.0.0`).
5. Resolver DEC-004/005 (ADRs duplicados, tests/conformance vazio).
6. Push da branch `rc1-demo` para `origin`.
7. Push da tag `rc1.0.0` para `origin`.

---

## 11. Próximos passos

> Esta seção é informativa. **Nenhuma ação será tomada** sem autorização explícita.

| Passo | Responsável | Bloqueado por |
|-------|--------------|---------------|
| Triagem dos ~14 itens da Categoria E | humano | nada |
| Decisão sobre duplicação ADRs (DEC-004) | humano | nada |
| Decisão sobre AraFlow / Neuro modules (DEC-006/008) | humano | nada |
| Autorização para commit do material não-versionado | humano | DEC-002 |
| Autorização para tag `rc1.0.0` | humano | DEC-003 |
| Push para `origin` | humano | DEC-003 + commit |

---

## Decisão Final

> 🟡 **Existem arquivos que precisam de classificação manual antes da Release.**
>
> A Release **NÃO é segura** enquanto DEC-001..DEC-010 não forem resolvidos. Há risco real de perder ~80 arquivos não-comitados de sprints finalizadas, e há duplicações e ambiguidades que requerem decisão humana.
>
> Nenhuma operação destrutiva foi executada. O estado do repositório foi apenas **inspecionado** e **descrito**.

---

*Inventário gerado em modo somente-leitura. Nenhum `git checkout`, `git restore`, `git reset`, `git clean`, `git stash`, `git commit`, `git tag`, `git push`, `git rebase`, `git merge`, `git rm`, `git mv` foi executado.*