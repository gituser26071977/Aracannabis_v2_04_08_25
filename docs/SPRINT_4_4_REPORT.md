# Sprint 4.4 — Clinical Knowledge Engine v1.0 — Report

**Status:** ✅ ENTREGUE
**Data:** 2026-07-20
**Branch:** `fix/p0-stabilization-2026-06`
**Foundation Freeze:** RESPEITADO — nenhuma modificação em AS-000/AS-001/AS-002/ASM-001/ADR-0001..0006.

---

## Escopo entregue

Sprint 4.4 implementou o **Clinical Knowledge Engine v1.0** — a primeira camada
de inteligência clínica sobre o Clinical Gene Engine validado no Sprint 4.3.

### 7 módulos de domínio (pure domain)

| Módulo | Responsabilidade | Linhas |
|---|---|---|
| `ClinicalGenome` | Projection read-model do estado de 1+ Genes para 1 paciente em uma janela temporal | 116 stmts |
| `CorrelationEngine` | 6 métodos canônicos (POSITIVE / NEGATIVE / CO_OCCURRENCE / MUTUAL_EXCLUSION / TEMPORAL_PRECEDENCE / STATISTICAL_DEPENDENCY) | 228 stmts |
| `HypothesisEngine` | 6 regras de geração de hipóteses (H_CORR_POSITIVE / H_CORR_NEGATIVE / H_VOLATILITY_COOCCUR / H_NO_EXPRESSION / H_MUTUAL_EXCLUSION / H_TEMPORAL_PRECEDENCE) | 146 stmts |
| `KnowledgeGraph` | 5 NodeTypes × 7 EdgeTypes; BFS path finding; nodes/edges ordenados para replay determinístico | 198 stmts |
| `CohortBuilder` | 7 CriterionOperators (EQ, NE, GT, LT, IN, NOT_IN, EXISTS); tenant isolation | 170 stmts |
| `ResearchWorkspace` | 4 AnalysisTypes (CORRELATIONS / HYPOTHESES / GRAPH / STATS); ResearchSession reproduzível byte-a-byte | 182 stmts |
| `ExplainabilityPipeline` | InferenceExplanation + 5 InferenceTypes + builder fluente | 177 stmts |

### Application Layer (Knowledge Service)

- `KnowledgeService` — facade principal (`run_pipeline`).
- `CorrelationService` / `HypothesisService` / `CohortService` /
  `ResearchService` / `GraphService` — serviços finos.
- DTOs frozen (`KnowledgePipelineResult`, requests por engine).

### Infrastructure Layer

- `InMemoryKnowledgeRepository` — genes, genomes, sessions, cohorts, graphs.
- RLock para thread-safety.
- 0 dependências externas (apenas stdlib + dataclasses).

---

## Critérios de Aceite (10 critérios)

Todos os 10 critérios validados pela demo `test_clinical_knowledge_scenario.py`:

| # | Critério | Status |
|---|---|---|
| 1 | Domínio completamente implementado | ✓ |
| 2 | Replay determinístico (state_hash byte-equivalente) | ✓ |
| 3 | ClinicalGenome reconstruível via ReplayEngine | ✓ |
| 4 | Explainability completa (toda inferência emite InferenceExplanation) | ✓ |
| 5 | Traceability completa (Requirement → Code → Test) | ✓ |
| 6 | Knowledge Graph reconstruível | ✓ |
| 7 | Testes passando (≥120 testes) | ✓ (128) |
| 8 | Demo funcional (12 pacientes sintéticos) | ✓ |
| 9 | Zero dependências de infraestrutura | ✓ |
| 10 | Arquitetura aderente a AS-000/AS-001/AS-002/ASM-001/ADR-0006 | ✓ |

---

## Métricas

- **Testes:** 128 (todos passando).
- **Domínio:** 1.476 statements, 75% cobertura.
- **Pipeline end-to-end:** ~35ms para 12 pacientes.
- **Patient profiles demo:** 3 perfis (TEA+Sono, TDAH+Ansiedade, Controle).
- **Determinismo verificado:** 3 runs consecutivos do mesmo input produzem
  state_hash bit-idêntico (Genome + Graph).

---

## Decisões de design fundamentais

### 1. ClinicalGenome NÃO é Aggregate Root
Conforme ADR-0005 + AS-001: é **projection/read-model derivado**, não fonte
de verdade. Sempre reconstruível via ReplayEngine.

### 2. Determinismo bit-identical
- IDs internos (graph nodes/edges, hypothesis, correlation) **derivados do
  conteúdo** (SHA-256 do conteúdo) ao invés de UUIDs aleatórios.
- Canonical dicts **excluem** `built_at` e timestamps efêmeros — só incluem
  estado clínico.
- Genes sempre ordenados por `gene_id` antes de entrar no canonical dict.

### 3. Explainability cross-cutting
TODA inferência (correlação, hipótese, edge de graph, cohort) carrega
`InferenceExplanation` com 5 elementos de proveniência:
participating_genes / expressions / events / correlations / hypotheses.

### 4. Hypothesis ≠ verdade clínica
`ClinicalHypothesis` é explicitamente **conhecimento derivado**:
- confidence ∈ [0, 1]
- status: PROPOSED / SUPPORTED / CONTRADICTED / INCONCLUSIVE / RETRACTED
- regras declarativas (não ML)

### 5. Correlation ≠ causalidade
Nenhum método declara causalidade — apenas associação observacional
(estatística) ou sequencial (lag).

---

## Foundation Freeze Compliance

- ✅ Nenhuma alteração em AS-000, AS-001, AS-002, ASM-001.
- ✅ Nenhuma alteração em ADR-0001..ADR-0006.
- ✅ Sem criação de novos standards (AS-004 reservada para Sprint 4.5
  quando amadurecer).
- ✅ Pure Domain — zero import de flask, sqlalchemy, redis, numpy, pydantic,
  requests, pydantic ou qualquer framework.
- ✅ Apenas stdlib + tipos já validados do genome/.

---

## Pendências para Sprint 4.5

Ver `docs/SPRINT_4_4_PENDING_FOR_4_5.md`.

---

## Próxima sprint

**Sprint 4.5 — Knowledge Graph Materializado + Dashboard + ML Prep.**

Foco:
1. Persistência definitiva (PostgreSQL via SQLAlchemy).
2. REST API (Flask blueprints).
3. Integração com ClinicalIdentity Registry (diagnoses).
4. Integração com Timeline Query (correlation windows).
5. Domain Events persistidos (CORRELATION_COMPUTED, HYPOTHESIS_GENERATED, etc).
6. AS-004 (Clinical Knowledge Standard).

Ver `docs/SPRINT_4_4_PENDING_FOR_4_5.md` para lista completa.
