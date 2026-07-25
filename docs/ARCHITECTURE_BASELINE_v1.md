# Architecture Baseline v1.0

**Data:** 2026-07-21
**Status:** FROZEN
**Escopo:** AraOS Clinical — Sprint 4.4 + 4.4.5 + Architecture Freeze
**Próxima revisão:** Apenas via ADR formal (Foundation Freeze)

---

## Sumário

Este documento congela a arquitetura do AraOS Clinical Knowledge Engine
após sua validação prática (Sprint 4.4 + 4.4.5). Nenhuma alteração
estrutural é permitida antes do Sprint 4.5 sem ADR formal.

**Auditoria de pureza:** 100% dos módulos `*/domain/` estão livres de
imports de infraestrutura (zero `sqlalchemy`, `flask`, `redis`,
`requests`, `pydantic`, `numpy`). Verificação por grep em todos os
arquivos `*/domain/*.py`.

---

## Bounded Contexts (7 canônicos + 2 auxiliares)

| # | Bounded Context | Path | Status |
|---|---|---|---|
| 1 | Clinical Identity | `event_store/catalog.py` (CLINICAL_IDENTITY_CREATED/ARCHIVED) | Canônico — event-sourced |
| 2 | Clinical Events | `araos/clinical/event_store/` | Canônico — event store |
| 3 | Clinical Expression | `araos/clinical/genome/domain/expression/` | Canônico — VO per AS-002 |
| 4 | Clinical Genome | `araos/clinical/genome/` | Canônico — AR per AS-001 |
| 5 | Clinical Knowledge | `araos/clinical/knowledge/` | Canônico — projections |
| 6 | Timeline | `araos/clinical/timeline/` | Canônico — query interface |
| 7 | Research | `araos/clinical/knowledge/domain/research.py` | Canônico — embutido |
| Aux | Clinical Context | `araos/clinical/context/` | Auxiliar — Sprint 4.2 |
| Aux | Explainability | `araos/clinical/explainability/` | Auxiliar — cross-cutting (Sprint 4.1) |

**Mapeamento de responsabilidades:**

- **Clinical Identity** — entidade-raiz do paciente; reconstruída a partir
  de eventos (`CLINICAL_IDENTITY_CREATED`, `CLINICAL_IDENTITY_ARCHIVED`).
  Não há classe AR dedicada; é read-model derivado do event store.
- **Clinical Events** — append-only log de eventos clínicos com hash chain
  per-tenant monotonic sequence (ADR-0001).
- **Clinical Expression** — Value Object observável de um Gene
  (AS-002 v1.0).
- **Clinical Genome** — Aggregate Root do Gene do paciente (AS-001 v1.0);
  dono de todas as expressões e metadata.
- **Clinical Knowledge** — Projeções read-only (ClinicalGenome,
  Cohort, KnowledgeGraph, ResearchSession); engines de correlação e
  hipótese; explainability cross-cutting.
- **Timeline** — read-model de eventos clínicos com bitemporalidade.
- **Research** — execução reproduzível de queries sobre cohorts + genes.
- **Clinical Context** — episode/milestone aggregator (Sprint 4.2).
- **Explainability** — Value Object cross-cutting usado por todos os engines.

---

## Aggregate Roots

### 1. ClinicalGene (AS-001 v1.0)

- **Path:** `araos/clinical/genome/domain/aggregate/clinical_gene.py`
- **Responsabilidades:**
  - Identidade do Gene por `(tenant_id, patient_id, gene_id)`.
  - Mutações append-only (replace_expression, add_hypothesis,
    add_relationship, add_context, add_evidence, add_metadata,
    take_snapshot, archive).
  - Expor `current_expression`, `why()`, `state_at()`, `known_at()`.
- **Invariantes (AS-001 §6 + §7.7.1):**
  - Replay bit-identical.
  - ARCHIVED é estado terminal.
  - `tenant_id` enforced em toda mutação.
  - Structural equality across 9 componentes internos.
  - Identity via URN `urn:araos:gene:{tenant}:{patient}:{gene}`.
- **Ownership:** Trajectory, History, MetadataRecord, EvidenceReference,
  Hypothesis, Relationship, ContextDependency, Snapshot, SnapshotPolicy,
  `last_event_id`/`sequence`.

### 2. ClinicalContext (Sprint 4.2, ADR-0003)

- **Path:** `araos/clinical/context/domain/clinical_context.py`
- **Responsabilidades:** Unificar episodes, medication periods, school
  changes, family events, milestones. State machine completa
  (Suggested→Planned→Active→Completed/Cancelled/Archived/Rejected).
- **Invariantes:**
  - `context_id`, `patient_id`, `tenant_id`, `title`, `created_by` required.
  - UTC-aware timestamps; `end_date ≥ start_date`.
  - `confidence_score ∈ [0,1]`; MANUAL origin → confidence == 1.0.
  - REJECTED não pode ter `confirmed_by`.
  - Status terminais (Completed/Cancelled/Archived) requerem `end_date`.
  - ACTIVE + automated origin requer `confirmed_by`.
  - SUGGESTED requer origin ∈ {rule_engine, ai}.
- **Ownership:** linked_event_ids, linked_diagnosis_ids, linked_phenotype_ids,
  linked_intervention_ids, linked_outcome_ids, linked_assessment_ids,
  professionals, source_event_ids, suggestion_id, explanation_id.

### 3. ClinicalEventDefinition

- **Path:** `araos/clinical/event_store/catalog.py`
- **Responsabilidades:** Schema de evento registrado (event_type,
  schema version, JSON schema, consumers, sensitivity flag, lifecycle status).
- **Invariantes:**
  - `event_type` required.
  - Status enum ACTIVE/DEPRECATED.
  - `json_schema` Draft 7 opcional.
  - `sensitive` default True.
- **Ownership:** Nenhuma (entrada isolada no `CLINICAL_EVENT_CATALOG`).

### Contextos sem Aggregate Root

- **Clinical Knowledge Engine** — explicitamente **sem AR**.
  É composto de projections read-only (ClinicalGenome, Cohort,
  KnowledgeGraph, ResearchSession) com `state_hash` SHA-256 e
  content-derived IDs. Conforme ADR-0005, projections não são AR.
- **Timeline** — sem AR. É read-model derivado do event store.
- **Research** — sem AR. ResearchSession é projection reproduzível.
- **Clinical Identity** — sem AR dedicada. É reconstruído via
  event-sourcing a partir de `CLINICAL_IDENTITY_*` events.

---

## Projections (Read-Models)

### 1. ClinicalGenome

- **Path:** `araos/clinical/knowledge/domain/clinical_genome.py`
- **Origem:** `ClinicalGenomeBuilder.build_from_genes()` ou
  `build_from_events()` (usa ReplayEngine).
- **Replay:** Sim — replay byte-idêntico via SHA-256 state_hash.
- **Determinismo:** `state_hash` SHA-256 hex (64 chars); multi-tenancy
  enforced (single tenant + single patient); canonical dict exclui
  `built_at`/`genome_id`; URN `urn:araos:genome:{tenant}:{patient}:{window}`.

### 2. Cohort

- **Path:** `araos/clinical/knowledge/domain/cohort.py`
- **Origem:** `CohortBuilder.evaluate(patients, tenant_id, name, criteria)`.
- **Replay:** Sim — `cohort_id = sha256(tenant|name|criteria_signature)[:12]`.
- **Determinismo:** `state_hash` SHA-256 do canonical dict;
  `matched_patient_ids` sorted; canonical dict exclui `built_at`.

### 3. KnowledgeGraph

- **Path:** `araos/clinical/knowledge/domain/knowledge_graph.py`
- **Origem:** `KnowledgeGraphBuilder.build(genome, correlations, hypotheses)`.
- **Replay:** Sim — node/edge/graph IDs são SHA-256-derived.
- **Determinismo:** `state_hash` SHA-256 do canonical dict; edges ordenados
  por `edge_id`; `graph_id = sha256(tenant|patient)[:12]`;
  referential integrity enforced.

### 4. ResearchSession

- **Path:** `araos/clinical/knowledge/domain/research.py`
- **Origem:** `ResearchWorkspace.execute(query, patients, genes_by_patient)`.
- **Replay:** Sim — `result_json` é canonical JSON (`sort_keys=True`);
  `state_hash` SHA-256 do `result_json`; replay() byte-equivalente.
- **Determinismo:** URN `urn:araos:research:{cohort_id}:{session_id}`;
  `reproducible=True` sempre.

### 5. Snapshot (Clinical Genome)

- **Path:** `araos/clinical/genome/domain/aggregate/snapshot.py`
- **Origem:** `SnapshotPolicy` + `take_snapshot()`.
- **Replay:** Sim — `Snapshot.state_hash` enables incremental replay via
  `ReplayEngine.replay_from_snapshot()`.
- **Determinismo:** `state_hash` SHA-256 hex; `transaction_time ≥ valid_time`.

### 6. TimelineEntry (domain)

- **Path:** `araos/clinical/timeline/domain/entries.py`
- **Origem:** `TimelineEntry.from_event()` from ClinicalEventStore dict.
- **Replay:** Sim — re-derivable from any sequence-ordered event stream.
- **Determinismo:** Bitemporal UTC; `sequence ≥ 0`; `aggregate_version ≥ 1`.

### 7. Explanation (cross-cutting)

- **Path:** `araos/clinical/explainability/domain/explanation.py`
- **Origem:** Produzido por toda análise de inteligência clínica.
- **Replay:** Sim — derivável; deterministic given same input.
- **Determinismo:** `confidence ∈ [0,1]`; variáveis ≥ 1; limitações ≥ 1;
  UTC `created_at`.

### 8. InferenceExplanation (Knowledge)

- **Path:** `araos/clinical/knowledge/domain/explainability.py`
- **Origem:** Cross-cutting via `ExplainabilityPipeline`.
- **Replay:** Sim.
- **Determinismo:** `confidence ∈ [0,1]`; `participating_genes` required
  para CORRELATION/HYPOTHESIS/GRAPH_EDGE.

---

## Domain Services

### Pure functions / Engines

| # | Service | Path | Input | Output | Dependencies |
|---|---|---|---|---|---|
| 1 | `create_gene` | `genome/domain/aggregate/clinical_gene_factory.py` | tenant/patient/gene/version/origin/snapshot_policy/created_at | Empty ClinicalGene | ClinicalGene, Trajectory, History, MetadataRecord, SnapshotPolicy |
| 2 | `ReplayEngine` | `genome/application/replay_engine.py` | Iterable[DomainEvent] (+ opcional Snapshot) | ClinicalGene bit-identical | ClinicalGene, all aggregate VOs, ClinicalExpression + sub-VOs, Explanation |
| 3 | `make_*` event factories | `genome/domain/events/factory.py` | tenant/patient/gene/sequence/valid_time/origin/payload | Frozen DomainEvent (15 tipos canônicos) | DomainEvent |
| 4 | `ClinicalGenomeBuilder` | `knowledge/domain/clinical_genome.py` | tenant/patient/window/genes (+ opcional events/corr/hyp) | ClinicalGenome | ClinicalGene, DomainEvent, ReplayEngine, TimeWindow |
| 5 | `CorrelationEngine` | `knowledge/domain/correlation.py` | ClinicalGenome + CorrelationMethod | tuple[CorrelationResult] | ClinicalGene, TimeWindow, ExplainabilityPipeline |
| 6 | `HypothesisEngine` | `knowledge/domain/hypothesis.py` | ClinicalGenome + Sequence[CorrelationResult] | tuple[ClinicalHypothesis] (6 regras) | ClinicalGene, ExpressionState, TimeWindow, ExplainabilityPipeline |
| 7 | `KnowledgeGraphBuilder` | `knowledge/domain/knowledge_graph.py` | ClinicalGenome + correlations + hypotheses | KnowledgeGraph (5 NodeTypes × 7 EdgeTypes) | ClinicalGene, TimeWindow, InferenceExplanation |
| 8 | `CohortBuilder` | `knowledge/domain/cohort.py` | patients + tenant_id + name + criteria | Cohort (content-derived cohort_id) | ClinicalGene, TimeWindow |
| 9 | `ExplainabilityPipeline` | `knowledge/domain/explainability.py` | inference_type + claim + method + confidence + participating_* | InferenceExplanation | stdlib only |
| 10 | `ResearchWorkspace` | `knowledge/domain/research.py` | ResearchQuery + patients + genes_by_patient | ResearchSession (reproduzível) | ClinicalGene, ClinicalGenome, Cohort, CorrelationEngine, HypothesisEngine, KnowledgeGraph |
| 11 | `TimelineQuery (ABC)` | `timeline/application/query.py` | tenant/patient/window/event_types | List[TimelineEntry] + count() | ClinicalEventStore, TimeWindow, TimelineEntry.from_event |
| 12 | `ClinicalProjectionEngine` | `projections/engine.py` | EventEnvelopeV2 | Dict (processed bool + entity metadata) | ClinicalRepository, IdempotencyTracker, Diagnosis, Medication, etc. |
| 13 | `RuleEngine` (Context) | `context/application/rule_engine.py` | events + context | Suggested contexts | Built-in rules |
| 14 | `ContextSuggester` | `context/application/suggester.py` | events + patient context | Suggestions | Explanation, AnalysisType, TimelineQuery |

---

## Application Services

### Clinical Knowledge Engine

| Service | Path | Commands | Queries | DTOs |
|---|---|---|---|---|
| `KnowledgeService` | `knowledge/application/knowledge_service.py` | `run_pipeline(genome)` | — | `KnowledgePipelineResult` |
| `CorrelationService` | `knowledge/application/correlation_service.py` | `execute(request)`, `execute_all(genome)` | — | `CorrelationRequest` |
| `HypothesisService` | `knowledge/application/hypothesis_service.py` | `execute(request)` | — | `HypothesisRequest` |
| `GraphService` | `knowledge/application/graph_service.py` | `execute(request)` | — | `GraphRequest` |
| `CohortService` | `knowledge/application/cohort_service.py` | `execute(request)` | — | `CohortRequest` |
| `ResearchService` | `knowledge/application/research_service.py` | `execute(request, patients, genes_by_patient)`, `replay(session)` | — | `ResearchRequest` |

### Clinical Context

| Service | Path | Commands | Queries | DTOs |
|---|---|---|---|---|
| `ClinicalContextService` | `context/application/context_service.py` | state transitions + persistence | `query(patient)` | (interno) |

### Timeline

| Service | Path | Commands | Queries | DTOs |
|---|---|---|---|---|
| `TimelineQuery` (ABC) + `InMemoryTimelineQuery` | `timeline/application/query.py` | — | `query(...)`, `count(...)` | `TimelineEntry` |

### Event Store

| Service | Path | Commands | Queries | DTOs |
|---|---|---|---|---|
| `ClinicalEventPublisher` | `event_store/publisher.py` | `publish(...)` | — | (interno) |

---

## Infrastructure Boundary

**O domínio NÃO conhece:**

- ❌ SQL
- ❌ Flask
- ❌ Redis
- ❌ HTTP
- ❌ JSON parser libraries (somente stdlib `json`)
- ❌ ORM (SQLAlchemy, Peewee, etc.)
- ❌ Dashboard libraries
- ❌ ML / Embeddings / numpy
- ❌ Pydantic
- ❌ Requests
- ❌ jsonschema (exceto em `event_store/validators.py`, fora do domain)

**Toda infraestrutura depende do domínio. Nunca o contrário.**

**Verificação automática:**

```bash
grep -rEn "import sqlalchemy|from sqlalchemy|import flask|from flask|import redis|from redis|import requests|from requests|import pydantic|from pydantic|import numpy|from numpy" \
  araos/clinical/genome/domain araos/clinical/knowledge/domain araos/clinical/timeline/domain araos/clinical/context/domain araos/clinical/explainability/domain
# Resultado: 0 hits
```

**Infraestrutura corretamente localizada:**

- `event_store/models.py`, `event_store/store.py` (lazy SQLAlchemy)
- `event_store/validators.py` (jsonschema)
- `explainability/sql.py` (SQLAlchemy + tenant Base)
- `context/sql.py` + `context/projections/*` (SQLAlchemy)
- `profile/models.py`, `entities/models.py` (SQLAlchemy)
- `timeline/models.py` (SQLAlchemy — top-level, fora do `domain/`)

**Regra arquitetural obrigatória para Sprint 4.5:**

```
REST → DTO → Application Service → Domain → Repository Interface ← Infrastructure
```

**Proibido:**

```
REST → Domain (camada pulada)
REST → Infrastructure (camada pulada)
Application Service → SQL/Flask/Redis (acoplamento direto)
Domain → ORM/SQL/Flask (vazamento)
```

---

## Decisões Arquiteturais Estabilizadas

A1. Knowledge Engine é composto de **projections read-only** (não AR).
A2. `state_hash` = SHA-256 do canonical dict (exclui `built_at`/IDs efêmeros).
A3. IDs são **content-derived** via SHA-256 — sem UUIDs persistentes.
A4. Replay **byte-idêntico** é invariante.
A5. Cross-tenant leak prevention: `tenant_id` incluído em todos os
    content-derived IDs (Sprint 4.4.5 fix).
A6. Multi-tenancy enforced em `__post_init__` e em service-level.
A7. Explainability é **cross-cutting** via `InferenceExplanation`
    em 4 dos 5 engines (Cohort exempted).
A8. Application services são **façades** sobre domain services.
A9. `InMemoryKnowledgeRepository` é a única infraestrutura atual
    (com RLock para thread-safety).
A10. Domain purity: zero import de SQL/Flask/Redis/Requests/Pydantic/Numpy
     em `*/domain/`.

---

## Mudanças Proibidas Antes do Sprint 4.5

P1. ❌ Modificar Foundation Freeze (AS-000/001/002, ASM-001, ADR-0001..0006).
P2. ❌ Modificar AS-004 Draft 0.1 (exceto para elevar a Verified).
P3. ❌ Adicionar novos Aggregate Roots.
P4. ❌ Adicionar novos Domain Services além dos catalogados.
P5. ❌ Adicionar novos projections read-model além dos catalogados.
P6. ❌ Adicionar imports de infraestrutura em qualquer `*/domain/`.
P7. ❌ Adicionar UUIDs persistentes (4 transitórios documentados são OK).
P8. ❌ Adicionar causalidade em Correlation/Hypothesis engines.
P9. ❌ Adicionar Application Service que dependa diretamente de SQL/Flask.
P10. ❌ Criar novos standards (AS, ADR, ASM) sem processo formal.

---

## Estado Final

> **Architecture Baseline v1.0 FROZEN.**
> 7 bounded contexts (5 principais + 2 auxiliares).
> 3 Aggregate Roots catalogados.
> 8 Projections catalogadas.
> 14 Domain Services catalogados.
> 9 Application Services catalogados.
> Domain purity verificada por grep em 100% dos arquivos `*/domain/`.
> Foundation Freeze + AS-004 Draft 0.1 respeitados.