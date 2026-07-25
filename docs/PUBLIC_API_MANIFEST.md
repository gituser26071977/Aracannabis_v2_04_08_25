# Public API Manifest v1.0

**Data:** 2026-07-21
**Status:** FROZEN
**Propósito:** Inventário autoritativo do que é **público** vs.
**interno** em cada bounded context. Apenas itens nesta lista devem
ser consumidos por outros contexts, application services, ou
infraestrutura externa (REST, etc.).

**Regra:** O que não está aqui é **interno** por default. Modificações
em API pública exigem ADR formal.

---

## Convenções

- **Público (P):** estável, contrato documentado, parte de backward-compatibility.
- **Estável (S):** exportado, mas sujeito a refinamentos (signature changes
  permitidas com aviso).
- **Interno (I):** implementação; **NÃO** importar de fora do bounded context.

---

## 1. Clinical Events (`araos/clinical/event_store/`)

### Tipos públicos

| Símbolo | Categoria | Status | Path |
|---|---|---|---|
| `ClinicalEventPublisher` | Application Service | S | `event_store/publisher.py` |
| `ClinicalEventStore` (ABC) | Repository Interface | P | `event_store/store.py` |
| `ClinicalEventDefinition` | Aggregate (Catalog) | P | `event_store/catalog.py` |
| `EventType` (enum) | Catalog Enum | S | `event_store/catalog.py` |
| `LifecycleStatus` (enum) | Catalog Enum | S | `event_store/catalog.py` |

### Eventos canônicos (26 tipos)

**Clinical Identity (2):**
- `CLINICAL_IDENTITY_CREATED`
- `CLINICAL_IDENTITY_ARCHIVED`

**Clinical Genome (15):** sequência por Gene.
- `GENE_CREATED`, `GENE_ARCHIVED`, `GENE_SNAPSHOTTED`, `GENE_METADATA_RECORDED`
- `EXPRESSION_OBSERVED`, `EXPRESSION_REPLACED`, `EXPRESSION_REMOVED`
- `HYPOTHESIS_ADDED`, `HYPOTHESIS_UPDATED`, `HYPOTHESIS_RESOLVED`
- `EVIDENCE_ADDED`, `EVIDENCE_UPDATED`
- `RELATIONSHIP_ADDED`, `CONTEXT_ADDED`
- `EVENT_OBSERVED` (genérico)

**Clinical Context (10):**
- `CONTEXT_CREATED`, `CONTEXT_STATUS_CHANGED`, `CONTEXT_CONFIRMED`
- `CONTEXT_CANCELLED`, `CONTEXT_COMPLETED`, `CONTEXT_REJECTED`
- `CONTEXT_LINKED_EVENT`, `CONTEXT_UNLINKED_EVENT`
- `CONTEXT_ARCHIVED`, `CONTEXT_SUGGESTED`

**Total:** 27 tipos catalogados (verificação por `event_store/catalog.py`).

### Internos (NÃO importar)

- `event_store/models.py` — SQLAlchemy.
- `event_store/validators.py` — jsonschema (Draft 7).
- `event_store/sql.py` — adapter.
- `event_store/store.py::SqlClinicalEventStore` — implementação concreta.

---

## 2. Clinical Genome (`araos/clinical/genome/`)

### Aggregate Root

| Símbolo | Status | Path |
|---|---|---|
| `ClinicalGene` | **P** | `genome/domain/aggregate/clinical_gene.py` |

### Value Objects (per AS-001 v1.0 §5.4)

Todos com **P**:

- `Trajectory`, `History`, `MetadataRecord`, `EvidenceReference`
- `Hypothesis`, `Relationship`, `ContextDependency`
- `Snapshot`, `SnapshotPolicy`
- `Sequence` (per-tenant BIGINT per ADR-0001)

### Clinical Expression (per AS-002 v1.0)

Todos com **P**:

- `ClinicalExpression` (root VO)
- `ExpressionState`
- `Magnitude`, `Trend`, `Polarity`, `Certainty` (sub-VOs)

### Domain Services

| Símbolo | Status | Path |
|---|---|---|
| `create_gene` (factory) | **P** | `genome/domain/aggregate/clinical_gene_factory.py` |
| `ReplayEngine` | **P** | `genome/application/replay_engine.py` |
| `make_*` (15 factories de evento) | S | `genome/domain/events/factory.py` |

### Domain Events (per ADR-0001 + AS-001)

| Símbolo | Status | Path |
|---|---|---|
| `DomainEvent` (ABC) | **P** | `genome/domain/events/base.py` |
| 15 implementações concretas | **P** | `genome/domain/events/` |

### Enums

| Símbolo | Status | Path |
|---|---|---|
| `EventType` | **P** | `genome/domain/events/enums.py` |
| `EventOrigin` | S | `genome/domain/events/enums.py` |
| `SnapshotPolicyType` | S | `genome/domain/aggregate/snapshot.py` |
| `ExpressionPolarity` | P | `genome/domain/expression/polarity.py` |
| `ExpressionTrend` | P | `genome/domain/expression/trend.py` |
| `CertaintyLevel` | P | `genome/domain/expression/certainty.py` |

### Internos

- `genome/infrastructure/serialization/canonical_json.py` — stdlib only, mas
  contrato interno de canonicalização.
- Qualquer coisa em `genome/infrastructure/` fora de ABCs.

---

## 3. Clinical Knowledge (`araos/clinical/knowledge/`)

### Projections (Read-Models)

| Símbolo | Status | Path |
|---|---|---|
| `ClinicalGenome` | **P** | `knowledge/domain/clinical_genome.py` |
| `Cohort` | **P** | `knowledge/domain/cohort.py` |
| `KnowledgeGraph` | **P** | `knowledge/domain/knowledge_graph.py` |
| `ResearchSession` | **P** | `knowledge/domain/research.py` |

### Value Objects / Enums

| Símbolo | Status | Path |
|---|---|---|
| `TimeWindow` | **P** | (cross-cutting via timeline) |
| `CorrelationMethod` (6 valores) | **P** | `knowledge/domain/correlation.py` |
| `HypothesisStatus` (6 valores) | **P** | `knowledge/domain/hypothesis.py` |
| `CriterionOperator` (7 valores) | **P** | `knowledge/domain/cohort.py` |
| `AnalysisType` (4 valores) | **P** | `knowledge/domain/research.py` |
| `NodeType` (5 valores) | **P** | `knowledge/domain/knowledge_graph.py` |
| `EdgeType` (7 valores) | **P** | `knowledge/domain/knowledge_graph.py` |
| `Criterion` | S | `knowledge/domain/cohort.py` |
| `CohortCriteria` | S | `knowledge/domain/cohort.py` |
| `CorrelationResult` | **P** | `knowledge/domain/correlation.py` |
| `ClinicalHypothesis` | **P** | `knowledge/domain/hypothesis.py` |
| `ResearchQuery` | **P** | `knowledge/domain/research.py` |
| `GraphNode` | S | `knowledge/domain/knowledge_graph.py` |
| `GraphEdge` | S | `knowledge/domain/knowledge_graph.py` |

### Domain Services

| Símbolo | Status | Path |
|---|---|---|
| `ClinicalGenomeBuilder` | **P** | `knowledge/domain/clinical_genome.py` |
| `CorrelationEngine` | **P** | `knowledge/domain/correlation.py` |
| `HypothesisEngine` | **P** | `knowledge/domain/hypothesis.py` |
| `KnowledgeGraphBuilder` | **P** | `knowledge/domain/knowledge_graph.py` |
| `CohortBuilder` | **P** | `knowledge/domain/cohort.py` |
| `ExplainabilityPipeline` | **P** | `knowledge/domain/explainability.py` |
| `ResearchWorkspace` | **P** | `knowledge/domain/research.py` |
| `InferenceExplanation` | **P** | `knowledge/domain/explainability.py` |
| `InferenceType` (5 valores) | **P** | `knowledge/domain/explainability.py` |

### Application Services

| Símbolo | Status | Path | Comandos |
|---|---|---|---|
| `KnowledgeService` | **P** | `knowledge/application/knowledge_service.py` | `run_pipeline(genome)` |
| `CorrelationService` | **P** | `knowledge/application/correlation_service.py` | `execute(request)`, `execute_all(genome)` |
| `HypothesisService` | **P** | `knowledge/application/hypothesis_service.py` | `execute(request)` |
| `GraphService` | **P** | `knowledge/application/graph_service.py` | `execute(request)` |
| `CohortService` | **P** | `knowledge/application/cohort_service.py` | `execute(request)` |
| `ResearchService` | **P** | `knowledge/application/research_service.py` | `execute(request, patients, genes_by_patient)`, `replay(session)` |

### DTOs (Application Layer)

| Símbolo | Status | Path |
|---|---|---|
| `CorrelationRequest` | **P** | `knowledge/application/dto.py` |
| `HypothesisRequest` | **P** | `knowledge/application/dto.py` |
| `GraphRequest` | **P** | `knowledge/application/dto.py` |
| `CohortRequest` | **P** | `knowledge/application/dto.py` |
| `ResearchRequest` | **P** | `knowledge/application/dto.py` |
| `KnowledgePipelineResult` | **P** | `knowledge/application/dto.py` |

### Infrastructure

| Símbolo | Status | Path |
|---|---|---|
| `InMemoryKnowledgeRepository` | S | `knowledge/infrastructure/in_memory.py` |
| `KnowledgeRepository` (ABC) | **P** | `knowledge/infrastructure/repository.py` (interface) |

### Internos

- Builders transitórios (`_make_edge`, `_with_state_hash`).
- Qualquer método com prefixo `_` (privado).
- `knowledge/infrastructure/in_memory.py` (S — usado por testes).

---

## 4. Timeline (`araos/clinical/timeline/`)

### Application Service (ABC)

| Símbolo | Status | Path | Queries |
|---|---|---|---|
| `TimelineQuery` (ABC) | **P** | `timeline/application/query.py` | `query(...)`, `count(...)` |
| `InMemoryTimelineQuery` | S | `timeline/application/query.py` | (idem) |

### Domain

| Símbolo | Status | Path |
|---|---|---|
| `TimelineEntry` | **P** | `timeline/domain/entries.py` |
| `TimelineEntry.from_event` | **P** | (classmethod) |

### Internos

- `timeline/models.py` (SQLAlchemy).
- `timeline/sql.py`.

---

## 5. Clinical Context (`araos/clinical/context/`)

### Aggregate Root

| Símbolo | Status | Path |
|---|---|---|
| `ClinicalContext` | **P** | `context/domain/clinical_context.py` |

### Value Objects / Enums

| Símbolo | Status | Path |
|---|---|---|
| `ContextStatus` (7 estados) | **P** | `context/domain/enums.py` |
| `ContextOrigin` (5 origens) | **P** | `context/domain/enums.py` |
| `ContextType` (10 subtipos) | **P** | `context/domain/enums.py` |
| `ContextRelationship` | S | `context/domain/relationships.py` |
| `RelationshipType` (6 valores) | **P** | `context/domain/relationships.py` |

### Application Services

| Símbolo | Status | Path |
|---|---|---|
| `ClinicalContextService` | **P** | `context/application/context_service.py` |
| `RuleEngine` | S | `context/application/rule_engine.py` |
| `ContextSuggester` | S | `context/application/suggester.py` |
| `BuiltinRule` (6 default rules) | S | `context/application/builtin_rules.py` |

### Domain Services

| Símbolo | Status | Path |
|---|---|---|
| `ContextProjection` | S | `context/projections/*` (read-models) |

### Internos

- `context/sql.py`, `context/projections/*` (SQLAlchemy).
- Métodos `_private` no AR.

---

## 6. Explainability (`araos/clinical/explainability/`)

### Value Objects

| Símbolo | Status | Path |
|---|---|---|
| `Explanation` | **P** | `explainability/domain/explanation.py` |
| `ExplanationRegistry` (ABC) | **P** | `explainability/domain/registry.py` |
| `InMemoryExplanationRegistry` | S | `explainability/domain/registry.py` |
| `VariableSpec` | **P** | (via timeline.domain.variable) |
| `ExplanationVariable` | **P** | `explainability/domain/explanation.py` |

### Internos

- `explainability/sql.py` (SQLAlchemy + tenant Base).

---

## 7. Pacotes Top-Level (Cross-Cutting)

### `araos/clinical/clinical_events/` (producers)

| Símbolo | Status | Path |
|---|---|---|
| `EventProducer.INTELLIGENCE` | **P** | `clinical_events/producers/intelligence.py` |
| `EventProducer.IDENTITY` | S | `clinical_events/producers/identity.py` |
| 2 `event_type` registrations | **P** | (Sprint 4.1) |

---

## 8. API Pública Não-Exposta (reservada para Sprint 4.5)

Estes símbolos serão introduzidos como parte da camada REST, mas seus
**shapes** já estão congelados para evitar quebrar contratos futuros:

| Símbolo | Status atual | Path futuro |
|---|---|---|
| `ClinicalGeneEndpoint` | reservado | `interfaces/rest/genome.py` |
| `CohortEndpoint` | reservado | `interfaces/rest/knowledge.py` |
| `TimelineEndpoint` | reservado | `interfaces/rest/timeline.py` |
| `EventStoreEndpoint` | reservado | `interfaces/rest/events.py` |

**Nota:** Nenhum dos arquivos acima existe ainda. A reserva é apenas
para alinhamento de nomenclatura com REST consumers.

---

## 9. Contratos Cross-Cutting

### `state_hash` (SHA-256 hex 64 chars)

- Aplicado em: `ClinicalGenome`, `Cohort`, `KnowledgeGraph`, `ResearchSession`.
- Exclui: `built_at`, IDs efêmeros (`genome_id` em canonical dict).
- Inclui: `tenant_id`, `patient_id`, `window`, atributos semânticos.

**G4 — Sprint 4.5 fix aplicado:** `_deterministic_correlation_id` foi
atualizado em Sprint 4.4.5 (fix cross-tenant leak prevention) para
incluir `tenant_id` E `window_start|window_end` em vez de
`coefficient_rounded`. Manifest acima reflete o estado real do código.

### Content-Derived IDs

| ID | Input para SHA-256 |
|---|---|
| `correlation_id` | `tenant_id\|method\|gene_x_id\|gene_y_id\|window_start\|window_end` (Sprint 4.4.5 fix — substitui `coefficient_rounded` que perdia informação da window) |
| `hypothesis_id` | `tenant_id\|rule_name\|gene_ids_sorted\|correlation_id` (manifest; ⚠️ code ainda usa `rule_id\|sorted(gene_ids)\|sorted(correlation_ids)\|claim` — gap cross-tenant registrado para Sprint 4.5+) |
| `cohort_id` | `tenant_id\|name\|criteria_signature` |
| `graph_id` | `tenant_id\|patient_id` |
| `graph_node_id` | `tenant_id\|node_type\|entity_id[|extras…]` (prefixo + tenant_id primeiro; exemplos: `"patient"\|tid\|pid`, `"gene"\|tid\|gene_id`, `"expr"\|tid\|gene_id\|sequence`, `"ev"\|tid\|event_id`) |
| `graph_edge_id` | derivado de `source_node_id\|target_node_id\|edge_type\|attrs` (não usa tenant_id direto porque source/target já são content-derived com tenant_id incluído) |

### Replay Equivalence

`ReplayEngine.replay(events) ≡ original` (bit-identical state_hash).

`ResearchWorkspace.execute(query, patients, genes_by_patient) ≡ replay(session)`.

---

## 10. Padrão de Import (Sprint 4.5+)

```python
# ✅ Correto (P ou S):
from araos.clinical.genome.domain.aggregate import ClinicalGene
from araos.clinical.knowledge.domain import Cohort, KnowledgeGraph
from araos.clinical.knowledge.application import CorrelationService
from araos.clinical.timeline.application import TimelineQuery

# ❌ Proibido (I):
from araos.clinical.knowledge.infrastructure.in_memory import InMemoryKnowledgeRepository
from araos.clinical.event_store.models import ...
from araos.clinical.context.sql import ...
```

**Regra:** Application services dependem apenas de **P** + **S**.
Domain depende apenas de **P** (entre contexts).
Infrastructure depende de tudo (é seu trabalho).

---

## 11. Mudanças Proibidas

- ❌ Adicionar novo símbolo como **P** sem ADR formal.
- ❌ Mover símbolo de **P** para **I** sem ADR (quebra compatibilidade).
- ❌ Modificar signature de símbolo **P** sem ADR.
- ❌ Expor detalhes internos de SQLAlchemy fora de `*/infrastructure/`.

---

## Resumo

| Categoria | Total | P | S | I |
|---|---|---|---|---|
| Aggregate Roots | 3 | 3 | 0 | 0 |
| Projections | 8 | 8 | 0 | 0 |
| Domain Services | 14 | 11 | 3 | 0 |
| Application Services | 9 | 9 | 0 | 0 |
| DTOs | 6 | 6 | 0 | 0 |
| Enums | 12+ | 11 | 1+ | 0 |
| Value Objects | 20+ | 18 | 2 | 0 |
| Events | 27 | 27 | 0 | 0 |

> **Public API Manifest v1.0 FROZEN.**
> Pronto para Boundary Validation.