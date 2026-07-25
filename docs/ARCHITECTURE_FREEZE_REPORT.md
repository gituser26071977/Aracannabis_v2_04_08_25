# Architecture Freeze Report v1.0

**Data:** 2026-07-21
**Status:** 🟢 **FROZEN**
**Próxima ação autorizada:** Sprint 4.5 — Infrastructure Layer
**Documentos produzidos:** 5 (este + 4 deliverables)

---

## Sumário Executivo

Após Sprint 4.4 (Clinical Knowledge Engine v1.0) e Sprint 4.4.5
(Architecture Hardening), uma etapa intermediária **exclusivamente
documental** foi executada para estabilizar definitivamente a
arquitetura antes da entrada da infraestrutura (Sprint 4.5).

**Esta etapa não adicionou nenhuma funcionalidade. Apenas
documentou e estabilizou o que já existe.**

Resultado:

- ✅ **5 documentos** produzidos
- ✅ **2 violações de layering** registradas (V1, V2) — não-bloqueantes
- ✅ **0 ciclos** detectados no grafo de dependências
- ✅ **100% domain purity** verificada por grep
- ✅ **Foundation Freeze 100% preservada**
- ✅ **244 testes** boundary-aware passing

---

## Deliverables Produzidos

| # | Documento | Conteúdo |
|---|---|---|
| 1 | `docs/ARCHITECTURE_BASELINE_v1.md` | 7 bounded contexts (5+2 aux), 3 ARs, 8 projections, 14 domain services, 9 application services, 10 decisões estabilizadas (A1-A10), 10 mudanças proibidas (P1-P10) |
| 2 | `docs/DEPENDENCY_MAP.md` | DAG cross-context, 24 edges, 2 violações V1/V2 registradas, domain purity verification |
| 3 | `docs/PUBLIC_API_MANIFEST.md` | Inventário P/S/I para 5 bounded contexts principais + 2 auxiliares |
| 4 | `docs/BOUNDARY_VALIDATION.md` | 10 verificações de layering + decision PASS |
| 5 | `docs/ARCHITECTURE_FREEZE_REPORT.md` | (este documento) |

---

## Conformidade com Diretrizes do Usuário

### Diretriz 1 — "Não adicionar nenhuma funcionalidade"

✅ **Aplicada.** Esta sprint produziu apenas documentação markdown.
Nenhum arquivo `.py` foi criado ou modificado durante o freeze.

### Diretriz 2 — "Não alterar: Domain Model, Aggregate boundaries, Projection Model, Replay Model, Explainability, Correlation Model, Hypothesis Model, Event Flow"

✅ **Aplicada.** Nenhuma alteração em qualquer `*/domain/*.py`. Todos
os símbolos catalogados são os mesmos existentes em
`Sprint_4_4_5_REPORT.md`.

### Diretriz 3 — "Caso alguma inconsistência estrutural seja encontrada: não corrigi-la silenciosamente; registrar explicitamente; propor ADR somente se realmente necessário"

✅ **Aplicada.** 2 violações de layering (V1, V2) **registradas
explicitamente** em `DEPENDENCY_MAP.md` §"Violações Registradas" e
em `BOUNDARY_VALIDATION.md` §"Verificação 1". Nenhuma correção
silenciosa foi aplicada.

### Diretriz 4 — "Não modificar: AS-000, AS-001, AS-002, AS-004 Draft, ASM-001, ADR-0001, ADR-0002, ADR-0003, ADR-0004, ADR-0005, ADR-0006"

✅ **Aplicada.** Foundation Freeze 100% preservada (ver
`BOUNDARY_VALIDATION.md` §"Verificação 9").

### Diretriz 5 — "Não criar novos standards. Não criar novas funcionalidades. Não iniciar SQL. Não iniciar REST. Não iniciar Dashboard. Não iniciar Materialized Graph. Não iniciar ML."

✅ **Aplicada.** Nenhum novo standard, nenhuma nova funcionalidade,
zero SQL/REST/Dashboard/ML adicionado durante o freeze.

---

## O Que Está Congelado

### Aggregate Roots (3)

- `ClinicalGene` (AS-001 v1.0)
- `ClinicalContext` (ADR-0003)
- `ClinicalEventDefinition` (event_store/catalog.py)

### Projections (8)

`ClinicalGenome`, `Cohort`, `KnowledgeGraph`, `ResearchSession`,
`Snapshot`, `TimelineEntry`, `Explanation`, `InferenceExplanation`.

### Domain Services (14)

| # | Service | Context |
|---|---|---|
| 1 | `create_gene` | genome |
| 2 | `ReplayEngine` | genome |
| 3 | `make_*` (15 factories) | genome |
| 4 | `ClinicalGenomeBuilder` | knowledge |
| 5 | `CorrelationEngine` | knowledge |
| 6 | `HypothesisEngine` | knowledge |
| 7 | `KnowledgeGraphBuilder` | knowledge |
| 8 | `CohortBuilder` | knowledge |
| 9 | `ExplainabilityPipeline` | knowledge |
| 10 | `ResearchWorkspace` | knowledge |
| 11 | `TimelineQuery` (ABC) | timeline |
| 12 | `ClinicalProjectionEngine` | projections |
| 13 | `RuleEngine` (Context) | context |
| 14 | `ContextSuggester` | context |

### Application Services (9)

`KnowledgeService`, `CorrelationService`, `HypothesisService`,
`GraphService`, `CohortService`, `ResearchService`,
`ClinicalContextService`, `TimelineQuery` (façade),
`ClinicalEventPublisher`.

### Decisões Arquiteturais Estabilizadas (A1-A10)

A1. Knowledge Engine é composto de **projections read-only** (não AR).
A2. `state_hash` = SHA-256 do canonical dict (exclui `built_at`/IDs efêmeros).
A3. IDs são **content-derived** via SHA-256 — sem UUIDs persistentes.
A4. Replay **byte-idêntico** é invariante.
A5. Cross-tenant leak prevention: `tenant_id` em todos content-derived IDs.
A6. Multi-tenancy enforced em `__post_init__` e em service-level.
A7. Explainability é **cross-cutting** via `InferenceExplanation`.
A8. Application services são **façades** sobre domain services.
A9. `InMemoryKnowledgeRepository` é a única infraestrutura atual.
A10. Domain purity: zero import de SQL/Flask/Redis/Requests/Pydantic/Numpy.

### Mudanças Proibidas Antes do Sprint 4.5 (P1-P10)

P1. ❌ Modificar Foundation Freeze (AS-000/001/002, ASM-001, ADR-0001..0006).
P2. ❌ Modificar AS-004 Draft 0.1 (exceto para elevar a Verified).
P3. ❌ Adicionar novos Aggregate Roots.
P4. ❌ Adicionar novos Domain Services além dos catalogados.
P5. ❌ Adicionar novos projections read-model além dos catalogados.
P6. ❌ Adicionar imports de infraestrutura em qualquer `*/domain/`.
P7. ❌ Adicionar UUIDs persistentes.
P8. ❌ Adicionar causalidade em Correlation/Hypothesis engines.
P9. ❌ Adicionar Application Service que dependa diretamente de SQL/Flask.
P10. ❌ Criar novos standards (AS, ADR, ASM) sem processo formal.

---

## 2 Violações Aceitas (V1, V2)

### V1 — `timeline.application.query` → `event_store.store`

**Severidade:** Baixa (não-bloqueante).
**Mitigação proposta:** Criar `event_store/domain/store.py` com
interface abstrata pura; mover SQLAlchemy para
`event_store/infrastructure/sql_store.py`.
**ADR necessário:** ADR-0007 (se for corrigida antes do Sprint 4.5).

### V2 — `knowledge.domain.clinical_genome` → `genome.application.ReplayEngine`

**Severidade:** Média (não-bloqueante).
**Mitigação proposta:** Mover `ReplayEngine` para
`genome/domain/services/replay_engine.py` (Opção A) ou criar Shared
Kernel (Opção B).
**ADR necessário:** ADR-0007 (idem).

---

## Estado de Verificação (resumo de `BOUNDARY_VALIDATION.md`)

| # | Verificação | Resultado |
|---|---|---|
| 1 | Layering canônico | ⚠️ com V1 |
| 2 | Domain purity | ✅ 100% |
| 3 | Application purity | ✅ 100% |
| 4 | DAG cross-context | ✅ 100% |
| 5 | Application dependency surface | ⚠️ com V1 |
| 6 | Repository ↔ Infrastructure | ✅ 100% |
| 7 | Invariantes | ✅ 25/25 |
| 8 | Cross-tenant leak prevention | ✅ 6/6 IDs |
| 9 | Foundation Freeze | ✅ 100% |
| 10 | Test suite boundary | ✅ 244 testes |

**Veredicto global:** 🟢 **PASS** com 2 violações aceitas.

---

## Riscos Conhecidos (registrados, não-bloqueantes)

| Risco | Mitigação |
|---|---|
| V1/V2 não corrigidas antes do Sprint 4.5 | Documentadas; ADR-0007 recomendado |
| Coverage 87% (vs target 90-95%) | Preservado por política (gap em helpers defensivos) |
| AS-004 Draft 0.1 não-normativo | Próxima elevação após Sprint 4.5 (Verified) |
| UUIDs transientes em 4 locais | Não persistentes, OK |

---

## Próximas Etapas Autorizadas

### 🟢 Sprint 4.5 — Infrastructure Layer

**Escopo permitido:**

- ✅ PostgreSQL + SQLAlchemy (implementar `SqlClinicalEventStore`, `SqlKnowledgeRepository`, `SqlExplanationRegistry`)
- ✅ REST API + Flask (implementar endpoints em `interfaces/rest/`)
- ✅ Dashboard (camada de leitura read-only)
- ✅ AuthN/AuthZ (integração com `araos/auth` se aplicável)

**Escopo proibido (registrar antes de implementar):**

- ❌ Qualquer mudança estrutural no **domínio** (A1-A10, P1-P10).
- ❌ Modificação de V1/V2 sem ADR-0007 formal.
- ❌ Adição de novos Aggregate Roots, Projections ou Domain Services sem ADR.
- ❌ Adição de imports de infraestrutura em `*/domain/*.py`.

### 📋 ADR-0007 (opcional, recomendado)

Resolver V1 e V2 **antes** do Sprint 4.5 iniciar. Não-bloqueante,
mas reduz risco arquitetural.

---

## Próximas Etapas NÃO Autorizadas (registro defensivo)

- ❌ Sprint 4.6+ não pode assumir que arquitetura atual é modificável.
- ❌ Qualquer mudança estrutural futura deve ser precedida por ADR
  formal (per ADR-0006), e não por implementação direta.
- ❌ Materialized Graph permanece fora do escopo até ADR formal.
- ❌ ML/Embeddings permanece fora do escopo até ADR formal.

---

## Declaração Final

> # 🟢 ARCHITECTURE FROZEN — READY FOR SPRINT 4.5
>
> Após Sprint 4.4 (Clinical Knowledge Engine v1.0),
> Sprint 4.4.5 (Architecture Hardening) e Architecture Freeze v1.0
> (etapa documental), a arquitetura do AraOS Clinical Knowledge
> Engine está **oficialmente congelada**.
>
> **O que foi entregue:**
>
> - 7 bounded contexts (5 principais + 2 auxiliares)
> - 3 Aggregate Roots catalogados
> - 8 Projections read-only
> - 14 Domain Services
> - 9 Application Services
> - 25 Domain Invariants enforced
> - 244 testes boundary-aware passing
> - 5 documentos de freeze
> - 10 decisões arquiteturais estabilizadas (A1-A10)
> - 10 mudanças proibidas (P1-P10)
> - 2 violações de layering conhecidas (V1, V2)
> - 100% Foundation Freeze preservada
> - 0 ciclos de dependência
> - 0 imports de infraestrutura em `*/domain/`
>
> **A partir desta declaração, toda evolução deverá ocorrer apenas
> por meio das camadas de infraestrutura e integração, preservando
> o núcleo do domínio.**
>
> **Qualquer mudança estrutural futura deverá ser precedida por ADR
> formal, e não por implementação direta.**

---

## Histórico de Revisões

| Data | Sprint | Mudança |
|---|---|---|
| 2026-07-15 | 4.4 | Clinical Knowledge Engine v1.0 entregue |
| 2026-07-20 | 4.4.5 | Architecture Hardening (313 testes, AS-004 Draft 0.1, cross-tenant fix) |
| 2026-07-21 | **Freeze v1.0** | **5 documentos de estabilização, declaration final** |

---

> **Foundation Freeze respeitada.**
> **Arquitetura endurecida.**
> **Documentada e congelada.**
> **🟢 ARCHITECTURE FROZEN — READY FOR SPRINT 4.5**