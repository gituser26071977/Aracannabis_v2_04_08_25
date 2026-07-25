# AS-004 — AraOS Standard 004: Clinical Knowledge Engine

```
STATUS: Draft 0.1
NÃO-NORMATIVO
URN: urn:araos:standard:004:0.1
Próxima revisão: após Sprint 4.5 (persistência SQL)
Data: 2026-07-20
```

> **Aviso editorial.** Este documento é um **Draft 0.1** e **NÃO
> é normativo**. Ele foi redigido a partir da implementação Sprint 4.4
> (Clinical Knowledge Engine v1.0) e endurecido pela Sprint 4.4.5
> (Architecture Hardening). Sua única função é servir como **espelho
> fiel** do que está implementado e testado, para orientar revisões
> futuras. Quaisquer decisões aqui registradas **NÃO** vinculam
> implementações futuras até que o status seja elevado a `Verified`
> ou superior conforme ASM-001 §7.

---

## 1. Header

| Atributo | Valor |
|---|---|
| **URN** | `urn:araos:standard:004:0.1` |
| **Maturity** | Draft 0.1 (não-normativo) |
| **Parent Meta** | ASM-001 v1.0 |
| **Foundations** | AS-000 v1.0, AS-001 v1.0, AS-002 v1.0 |
| **ADRs referenciados** | ADR-0001, ADR-0005, ADR-0006 |
| **Origem** | Sprint 4.4 + Sprint 4.4.5 |
| **Próxima revisão obrigatória** | Após Sprint 4.5 (SQL persistence) |

---

## 2. Normative Sources

Este Standard referencia e reutiliza, sem modificar:

- **AS-000 v1.0** — AraOS Language Specification (termos canônicos).
- **AS-001 v1.0** — Clinical Gene (Aggregate Root imutável).
- **AS-002 v1.0** — Clinical Expression (Value Object imutável).
- **ADR-0001** — Clinical Event Engine (event-sourcing).
- **ADR-0005** — Clinical Genome como projection.
- **ADR-0006** — Normative Conflict Resolution (Foundation Freeze).
- **ASM-001 v1.0** — Specification Meta Model (estrutura canônica).

Nenhuma destas Foundations é modificada por AS-004 Draft 0.1.

---

## 3. Design Goals (8 objetivos derivados)

G1. **Determinismo replay** — Toda inferência deve ser reproduzível
    byte-a-byte a partir do estado inicial. Implementado via
    `state_hash = SHA-256(canonical_dict)` em 4 tipos (ClinicalGenome,
    Cohort, KnowledgeGraph, ResearchSession).

G2. **Proveniência obrigatória** — Toda inferência deve carregar
    explicação rastreável (5 elementos canônicos). Implementado via
    `InferenceExplanation.participating_*`.

G3. **Multi-tenancy absoluta** — Zero vazamento entre tenants.
    Implementado em `__post_init__` (ClinicalGenome), `CohortBuilder`,
    `correlation_id` (SHA-256 inclui `tenant_id`).

G4. **Pure domain** — Zero dependência de SQL/REST/Flask no domínio.
    Knowledge é puro Python + stdlib.

G5. **Content-derived IDs** — IDs reproduzíveis sem UUID.
    Implementado para Correlation, Hypothesis, Cohort, Graph node+edge+graph.

G6. **Thread-safety** — Repositório InMemory protegido por RLock em
    15 operações. Engines são puros (frozen dataclasses).

G7. **Invariantes enforced** — Validação em `__post_init__` quando
    possível sem quebrar construção transitória.

G8. **Testabilidade máxima** — Property-based (Hypothesis v6.156.6),
    concurrency, multi-tenancy stress.

---

## 4. Non-Goals (explicitamente fora do escopo)

N1. **Persistência SQL** — Sprint 4.5 territory.
N2. **REST API / Flask** — Sprint 4.5.
N3. **Dashboard** — Sprint 4.5.
N4. **ML / Embeddings** — Sprint 4.5+ ou posterior.
N5. **Diagnóstico clínico** — Knowledge Engine **NUNCA** diagnostica;
    apenas correlaciona e levanta hipóteses (observational, não causal).
N6. **Causalidade** — Correlation nunca declara causa. Implementado
    e validado em test_decision_verification.py.

---

## 5. Scope

AS-004 Draft 0.1 governa:

- **Projection Model** — `ClinicalGenome` (read-model derivado).
- **Correlation Model** — 6 métodos canônicos.
- **Hypothesis Model** — Regras declarativas + status enum.
- **Knowledge Graph Model** — 5 NodeTypes × 7 EdgeTypes.
- **Cohort Model** — 7 CriterionOperators + tenant isolation.
- **Research Workspace Model** — 4 AnalysisTypes + execute ≡ replay.
- **Explainability** — Cross-cutting, 5 InferenceTypes.
- **Replay Model** — `ReplayEngine` + content-derived IDs.

---

## 6. Normative References

Nenhuma referência externa. Todos os conceitos são internos ao AraOS.

---

## 7. Terms and Definitions (18 termos canônicos)

| # | Termo | Definição |
|---|---|---|
| 1 | **ClinicalGenome** | Projection read-model derivado de ClinicalGenes do mesmo paciente em uma TimeWindow. |
| 2 | **CorrelationMethod** | Enum de 6 valores: POSITIVE, NEGATIVE, CO_OCCURRENCE, MUTUAL_EXCLUSION, TEMPORAL_PRECEDENCE, STATISTICAL_DEPENDENCY. |
| 3 | **HypothesisStatus** | Enum de 6 valores: PROPOSED, SUPPORTED, CONTRADICTED, INCONCLUSIVE, RETRACTED. |
| 4 | **NodeType** | Enum de 5 valores (ClinicalGene, Correlation, Hypothesis, Cohort, ResearchSession). |
| 5 | **EdgeType** | Enum de 7 valores (CORRELATES_WITH, SUPPORTS, CONTRADICTS, INCLUDED_IN, GENERATED_BY, DERIVED_FROM, REFERENCES). |
| 6 | **CriterionOperator** | Enum de 7 valores: EQ, NE, GT, LT, IN, NOT_IN, EXISTS. |
| 7 | **AnalysisType** | Enum de 4 valores: CORRELATIONS, HYPOTHESES, GRAPH, STATS. |
| 8 | **InferenceType** | Enum de 5 valores: CORRELATION, HYPOTHESIS, COHORT, GRAPH_EDGE, RESEARCH. |
| 9 | **InferenceExplanation** | Value Object cross-cutting com 5 elementos proveniência (participating_genes, expressions, events, correlations, hypotheses). |
| 10 | **TimeWindow** | Intervalo temporal fechado `[start, end]` UTC-aware. |
| 11 | **StateHash** | SHA-256 hex 64 chars do canonical dict (exclui `built_at`, IDs efêmeros). |
| 12 | **ReplayDeterminism** | Propriedade: replay N vezes = mesmo `state_hash` byte-idêntico. |
| 13 | **ContentDerivedID** | ID derivado de SHA-256 dos atributos canônicos (sem UUID). |
| 14 | **Cohort** | Conjunto filtrado de pacientes sob critérios declarativos. |
| 15 | **ResearchSession** | Execução reproduzível de ResearchQuery sobre cohort + genes. |
| 16 | **ResearchQuery** | Declaração de análise (cohort_id + analysis_type + params). |
| 17 | **Provenance** | Cadeia completa de evidências (5 elementos InferenceExplanation). |
| 18 | **TenantIsolation** | Garantia absoluta de zero vazamento entre tenants (testado). |

---

## 8. Projection Model — ClinicalGenome

**Definição:** `ClinicalGenome` é um read-model imutável (frozen
dataclass) que agrega `ClinicalGenes` de um paciente em uma
`TimeWindow`.

**Invariantes:**

- É frozen (não mutável).
- `tenant_id` deve ser único e presente em todos os genes.
- `state_hash` é SHA-256 hex 64 chars.
- Não é Aggregate Root (ADR-0005) — é projection.
- Não emite eventos.

**Campos canônicos:** `genome_id`, `tenant_id`, `patient_id`,
`window`, `genes`, `built_at`, `state_hash`.

**Garantia:** Toda reconstrução via `build_clinical_genome` produz
o mesmo `state_hash` se inputs forem idênticos.

---

## 9. Correlation Model

**Definição:** Motor de correlação observacional entre pares de
ClinicalGenes do mesmo ClinicalGenome.

**6 Métodos canônicos:**

| Método | Coefficient Range | Significado |
|---|---|---|
| POSITIVE | `(-1.0, 1.0]` | Pearson simplificado > 0 |
| NEGATIVE | `[-1.0, 0.0)` | Pearson simplificado < 0 |
| CO_OCCURRENCE | `[0.0, 1.0]` | Fração de co-ocorrência temporal |
| MUTUAL_EXCLUSION | `[0.0, 1.0]` | Inverso de co-ocorrência |
| TEMPORAL_PRECEDENCE | `[0.0, 1.0]` | Lag fraction |
| STATISTICAL_DEPENDENCY | `[0.0, 1.0]` | Chi-quadrado simplificado |

**Invariantes:**

- `correlation_id` é content-derived SHA-256 incluindo `tenant_id`.
- `coefficient ∈ [-1.0, 1.0]`.
- `confidence ∈ [0.0, 1.0]`.
- Nunca declara causalidade (não há string `causa`/`because` no código).

---

## 10. Hypothesis Model

**Definição:** Regras declarativas que geram hipóteses a partir de
correlações e genes.

**Regras canônicas (6):**

1. `H_CORR_POSITIVE` — Correlação POSITIVE forte → hipótese SUPPORTED.
2. `H_CORR_NEGATIVE` — Correlação NEGATIVE forte → hipótese SUPPORTED.
3. `H_CORR_WEAK` — Correlação fraca → PROPOSED.
4. `H_COOCCURRENCE` — Co-ocorrência ≥ threshold → SUPPORTED.
5. `H_MUTUAL_EXCLUSION` — Exclusão mútua → PROPOSED.
6. `H_TEMPORAL` — Precedência temporal → SUPPORTED.

**Invariantes:**

- `hypothesis_id` é content-derived SHA-256.
- `confidence ∈ [0.0, 1.0]`.
- `status ∈ {PROPOSED, SUPPORTED, CONTRADICTED, INCONCLUSIVE, RETRACTED}`.
- Não muta `ClinicalGene` (pure function).

---

## 11. Knowledge Graph Model

**Definição:** Grafo dirigido de nós (5 tipos) conectados por arestas
(7 tipos) com pesos.

**5 NodeTypes:** `ClinicalGene`, `Correlation`, `Hypothesis`,
`Cohort`, `ResearchSession`.

**7 EdgeTypes:** `CORRELATES_WITH`, `SUPPORTS`, `CONTRADICTS`,
`INCLUDED_IN`, `GENERATED_BY`, `DERIVED_FROM`, `REFERENCES`.

**Invariantes:**

- `graph_id` é content-derived.
- `state_hash` é SHA-256 hex.
- Single-tenant (KnowledgeGraph sempre single-tenant enforced via ClinicalGenome upstream).
- BFS path preservado (integridade referencial).

---

## 12. Cohort Model

**Definição:** Conjunto filtrado de `PatientData` sob critérios
declarativos.

**7 CriterionOperators:** `EQ`, `NE`, `GT`, `LT`, `IN`, `NOT_IN`, `EXISTS`.

**Campos placeholder:** `gene.*`, `expression.*`, `context.*`,
`patient.*` (4 namespaces).

**Invariantes:**

- `cohort_id` é content-derived SHA-256.
- Cross-tenant gene injection rejeitado em `__post_init__`.
- `state_hash` é SHA-256 hex.
- `matched_patient_ids` filtra pacientes cross-tenant.

---

## 13. Research Workspace Model

**Definição:** Camada de execução reproduzível de queries de pesquisa
sobre cohorts + genes.

**4 AnalysisTypes:** `CORRELATIONS`, `HYPOTHESES`, `GRAPH`, `STATS`.

**Invariantes:**

- `state_hash` é SHA-256 hex do `result_json` canônico.
- `explanation` (InferenceExplanation) sempre presente.
- `execute(query, patients, genes_by_patient) ≡ replay` byte-idêntico.
- Single-tenant enforced via cohort.

---

## 14. Explainability Model

**Definição:** Camada cross-cutting de proveniência obrigatória.

**5 InferenceTypes:** `CORRELATION`, `HYPOTHESIS`, `COHORT`,
`GRAPH_EDGE`, `RESEARCH`.

**5 Elementos proveniência (`participating_*`):**

1. `participating_genes` (gene_ids)
2. `participating_expressions` (expression refs)
3. `participating_events` (event_ids)
4. `participating_correlations` (correlation_ids)
5. `participating_hypotheses` (hypothesis_ids)

**Invariantes:**

- Para `CORRELATION`, `HYPOTHESIS`, `GRAPH_EDGE`: `participating_genes`
  MUST ser não-vazio (enforced em `__post_init__`).
- Para `COHORT`, `RESEARCH`: exempto (meta-análise, sem gene correlato direto).
- `confidence ∈ [0.0, 1.0]` enforced.
- `created_at` MUST ser UTC-aware enforced.

---

## 15. Replay Model

**Definição:** `ReplayEngine` reconstrói `ClinicalGenome` a partir de
events, garantindo determinismo byte-idêntico.

**Garantias:**

- `replay(events) = original.state_hash` (bit-identical).
- `replay(replay(events)) == replay(events)` (idempotente).
- Ordem de eventos não importa (state_hash canônico).
- Content-derived IDs (`correlation_id`, `hypothesis_id`, `cohort_id`,
  `graph_id`, `graph_node_id`, `graph_edge_id`).

---

## 16. Determinism Rules

D1. Mesmos inputs → mesmos outputs (engines são pure functions).
D2. `state_hash` é estável sob N replays (`N ∈ {100, 500, 1000}` testado).
D3. Ordem de genes não altera `state_hash` (canonical dict).
D4. TimeWindow idêntico em diferentes runs → mesmo hash.
D5. `tenant_id` sempre no `correlation_id` (cross-tenant leak prevention).

---

## 17. Traceability Rules

T1. Toda decisão de design → ADR correspondente ou § AS-XXX.
T2. Toda classe de domínio → ao menos 1 teste em `tests/sprint_4_4*`.
T3. Todo ADR ou AS → referência em código (import) ou teste (assert).
T4. `participating_*` em inferências → cross-referenced com
    source (correlation/hypothesis/graph/cohort/research).

---

## 18. Domain Invariants (25 catalogadas)

**I-01** ClinicalGenome é frozen.
**I-02** ClinicalGenome.state_hash != "" (validated em build).
**I-03** ClinicalGenome rejeita mistura de tenants.
**I-04** ClinicalGenome rejeita mistura de pacientes.
**I-05** CorrelationResult.coefficient ∈ [-1.0, 1.0].
**I-06** CorrelationResult.confidence ∈ [0.0, 1.0].
**I-07** CorrelationResult.n_observations >= 0.
**I-08** CorrelationResult nunca declara causalidade.
**I-09** ClinicalHypothesis não muta Gene (pure).
**I-10** KnowledgeGraph é frozen.
**I-11** KnowledgeGraph.state_hash != "".
**I-12** KnowledgeGraph.single-tenant enforced (via upstream).
**I-13** Cohort é frozen.
**I-14** Cohort.state_hash != "".
**I-15** Cohort.cohort_id é content-derived.
**I-16** Cohort rejeita cross-tenant patient.
**I-17** ResearchSession.state_hash é SHA-256 hex 64 chars.
**I-18** ResearchSession.execute ≡ replay byte-identical.
**I-19** InferenceExplanation é frozen.
**I-20** InferenceExplanation.confidence ∈ [0.0, 1.0].
**I-21** InferenceExplanation.created_at MUST ser UTC-aware.
**I-22** InferenceExplanation MUST ter participating_genes para
        CORRELATION/HYPOTHESIS/GRAPH_EDGE (enforced).
**I-23** Datetimes sempre UTC timezone-aware.
**I-24** IDs são content-derived (replay byte-equivalente).
**I-25** `correlation_id` MUST incluir `tenant_id` no hash.

---

## 19. Integration

- **AS-001 v1.0** — `ClinicalGenome.genes` contém `ClinicalGene`s.
- **AS-002 v1.0** — `ClinicalGene.current_expression` é `ClinicalExpression`.
- **ADR-0001** — Knowledge consome event store para replay.
- **ADR-0005** — `ClinicalGenome` é projection (read-model).
- **ADR-0006** — Foundation Freeze respeitada.

---

## 20. Acceptance Criteria (Draft 0.1)

Estes critérios validam que AS-004 Draft 0.1 é coerente com a
implementação. **Não são critérios de aceitação do Draft** — apenas
metadados de verificação editorial.

AC-01. 8 Design Goals (G1–G8) refletem o que está implementado.
AC-02. 6 Non-Goals (N1–N6) explicitamente fora do escopo Sprint 4.5.
AC-03. 18 Termos canônicos estão presentes no código.
AC-04. 25 Domain Invariants enforced em `__post_init__` ou métodos.
AC-05. Coverage ≥ 87% (target 90-95% — Sprint 4.4.5 entrega 87%).
AC-06. 313 testes passing (Sprint 4.4 + 4.4.5).
AC-07. Nenhuma modificação em Foundation Freeze (AS-000/001/002,
       ASM-001, ADR-0001/0005/0006).
AC-08. Architecture Decision Verification suite (31 testes) passing.

---

## Apêndice A — Mapeamento Requirement → Code → Test

| Requirement | Code | Test |
|---|---|---|
| G1 Determinism replay | `correlation.py`, `clinical_genome.py` | `test_replay_hardening.py` |
| G2 Provenance | `explainability.py` | `test_explainability_audit.py` |
| G3 Multi-tenancy | `clinical_genome.py`, `cohort.py`, `correlation.py` | `test_multitenancy_stress.py` |
| G4 Pure domain | (zero SQL/REST imports) | `test_decision_verification.py` |
| G5 Content-derived IDs | `correlation.py`, `cohort.py`, `knowledge_graph.py` | `test_property_based.py` |
| G6 Thread-safety | `infrastructure/in_memory.py` | `test_concurrency.py` |
| G7 Invariantes | todos os `__post_init__` | `test_domain_invariants.py` |
| G8 Testabilidade | Hypothesis v6.156.6 | `test_property_based.py` |

---

## Apêndice B — Status Editorial

```
Status: Draft 0.1
Próxima elevação: Verified (após Sprint 4.5)
Bloqueios para Verified:
  - Sprint 4.5 SQL persistence deve preservar todas invariantes.
  - Replay determinístico deve manter-se byte-idêntico após migração SQL.
  - Multi-tenancy deve ser validada em SQL real (não apenas in-memory).
Nenhuma decisão registrada aqui é vinculante até elevação para Verified.
```

---

## Apêndice C — Histórico de Revisões

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-07-20 | Redação inicial a partir de Sprint 4.4 + 4.4.5. |

---

> **Foundation Freeze respeitada.**
> **Arquitetura endurecida.**
> **READY FOR SPRINT 4.5.**