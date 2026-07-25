# Sprint 4.4 → 4.5 — Pendências Identificadas

**Data de identificação:** 2026-07-20
**Origem:** Implementação Sprint 4.4 (Clinical Knowledge Engine v1.0)

Este documento cataloga TODAS as decisões/integrações necessárias para
que o Sprint 4.5 (Knowledge Graph Materializado + Dashboard + ML Prep)
possa ser iniciado com clareza.

---

## 1. Persistência SQL definitiva

Sprint 4.4 usou apenas InMemory. Sprint 4.5 deve implementar:

- Migration Alembic criando as tabelas:
  - `clinical_genomes` (state_hash, tenant_id, patient_id, window_start, window_end)
  - `clinical_correlations` (correlation_id, method, gene_x, gene_y, coefficient, confidence, n_observations)
  - `clinical_hypotheses` (hypothesis_id, rule_id, status, confidence, claim)
  - `clinical_cohorts` (cohort_id, tenant_id, name, criteria_json, matched_patient_ids_json)
  - `clinical_research_sessions` (session_id, urn, query_id, cohort_id, version, result_json, state_hash)
  - `clinical_knowledge_graph_snapshots` (graph_id, tenant_id, patient_id, nodes_json, edges_json, state_hash)
  - `clinical_inference_explanations` (explanation_id, inference_type, claim, participating_*)

- Adapters SQLAlchemy + Repository Persistence (separação do InMemoryRepository).

---

## 2. REST API (Flask blueprints)

Endpoints a criar:

| Endpoint | Descrição |
|---|---|
| `POST /api/intelligence/knowledge/build_genome` | Replay→Genome |
| `POST /api/intelligence/knowledge/correlations` | Compute correlations |
| `POST /api/intelligence/knowledge/hypotheses` | Generate hypotheses |
| `POST /api/intelligence/knowledge/graph` | Build knowledge graph |
| `POST /api/intelligence/knowledge/cohort` | Build cohort |
| `POST /api/intelligence/research/sessions` | Execute research session |
| `POST /api/intelligence/research/{id}/replay` | Replay research session |
| `GET  /api/intelligence/explanations/{id}` | Fetch InferenceExplanation |

Blueprint registration em `app_factory` (padrão Sprint 4.2).

---

## 3. Integração com ClinicalIdentity Registry (Sprint 3.2)

CohortBuilder fields placeholder atualmente:
- `diagnosis.code` — wire com `clinical_identity.diagnoses`
- `context.context_type` — wire com `clinical_contexts` (Sprint 4.2)

Atualizar `_matches()` em CohortBuilder para resolver esses paths.

---

## 4. Integração com Timeline Query (Sprint 4.1)

- CorrelationEngine.compute() aceita TimeWindow agora, mas poderia
  também aceitar TimelineQuery como entrada — usar TimelineEntry ranges
  para correlação avançada.

---

## 5. Domain Events persistidos

Adicionar 5 event types novos ao `clinical_events` catalog:

| event_type | quando dispara |
|---|---|
| `CORRELATION_COMPUTED` | ao rodar CorrelationEngine.compute() |
| `HYPOTHESIS_GENERATED` | ao rodar HypothesisEngine.generate() |
| `COHORT_DEFINED` | ao rodar CohortBuilder.evaluate() |
| `RESEARCH_SESSION_CREATED` | ao rodar ResearchWorkspace.execute() |
| `KNOWLEDGE_GRAPH_BUILT` | ao rodar KnowledgeGraphBuilder.build() |

Cada evento carrega `explanation_id` (referência ao
InferenceExplanation produzido).

---

## 6. Autenticação/Autorização

As permissions já estão declaradas (Sprint 4.1) mas não wireadas.
Sprint 4.5 deve registrar handlers:

- `INTELLIGENCE_CORRELATION_COMPUTE`
- `INTELLIGENCE_CORRELATION_READ`
- `INTELLIGENCE_HYPOTHESIS_READ`
- `INTELLIGENCE_COHORT_CREATE`
- `INTELLIGENCE_COHORT_READ`
- `INTELLIGENCE_RESEARCH_CREATE`
- `INTELLIGENCE_RESEARCH_READ`
- `INTELLIGENCE_RESEARCH_REPLAY`
- `RESEARCH_EXPORT` (exportar cohort/results)
- `KNOWLEDGE_GRAPH_READ`

RBAC + tenant scoping + audit log por endpoint.

---

## 7. Multi-tenancy enforcement na persistência

Hoje a tenant isolation é respeitada no domínio
(`CohortBuilder` filtra por `patient.tenant_id`).
Sprint 4.5 deve garantir:

- Todos os services aceitam `tenant_id` e filtram antes da query SQL.
- Nenhum cross-tenant leakage via `load_*` ou `list_*`.

---

## 8. AS-004 — Clinical Knowledge Standard

A Foundation Freeze reservou AS-004 para o domínio de Knowledge Engine
após maturação prática. Sprint 4.5+ pode escrever o Standard próprio
quando a arquitetura estiver estabilizada (após REST + SQL + auth).

Target: Sprint 4.6 ou posterior.

---

## 9. Machine Learning Prep

Pendente para além de 4.5:
- Embedding learning para ClinicalGenome (geração de vetor representacional).
- Testes A/B de regras vs. ML-derived hypotheses.
- Drift detection (Sprint 4.6).

---

## 10. Documentação adicional

- ADRs referenciando o Sprint 4.4 (se necessário para decisões
  estruturais que não estão capturadas nos ADRs existentes).
- Diagramas (PlantUML ou equivalente) do Knowledge Engine pipeline.
- Manual de uso extensivo para KBEs (Knowledge-Based Engines).
