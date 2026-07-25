# Sprint 4.4 — Clinical Knowledge Engine — Architecture Validation

**Status:** ✅ VALIDADO
**Data:** 2026-07-20

---

## Compliance por Foundation Document

| Documento | Status | Observação |
|---|---|---|
| **Constitution** | ✅ | Não modificado. Foundation Freeze respeitado. |
| **AS-000** (Language Specification) | ✅ | Apenas reuso. Nenhum conceito novo introduzido sem revisão do meta-modelo. |
| **AS-001** (Clinical Gene) | ✅ | ClinicalGenome reusa ClinicalGene como input. NÃO cria paralelo. |
| **AS-002** (Clinical Expression) | ✅ | ClinicalExpression é mantida como VO. Hypothesis ≠ Expression (separação clara). |
| **ASM-001** (Meta Model) | ✅ | ReplayEngine reutilizado. Conformance Suite estendido. |
| **ADR-0001** (Clinical Event Engine) | ✅ | Pipeline consome events do Event Store. Não duplica. |
| **ADR-0002** (Clinical Genome Pivot) | ✅ | ClinicalGenome é projection, NÃO AR (consistente com pivot Genome-centric). |
| **ADR-0003** (Clinical Context) | ✅ | CohortBuilder fields `context.context_type` reservado para integração Sprint 4.5. |
| **ADR-0005** (Genome Pivot) | ✅ | ClinicalGenome implementation segue decisão do pivot. |
| **ADR-0006** (Foundation Freeze) | ✅ | Nenhuma modificação em normativas. UI nova só foi criada após Domain validado. |

---

## Decisões arquiteturais validadas

### D1. ClinicalGenome é projection derivada, não AR
**Validação:** `clinical_genome.py:74-99` — frozen dataclass, sem
estado mutável, reconstructable via ReplayEngine. Teste
`test_clinical_genome::TestClinicalGenomeReplay` valida state_hash
determinístico em N runs.

### D2. Correlation engine é puro
**Validação:** `correlation.py` — sem side effects, sem mutação do
genome. 6 métodos implementados. Testes `test_correlation_engine.py`
garantem coefficient ∈ [-1, 1] e confidence ∈ [0, 1].

### D3. Hypothesis engine segue regras declarativas
**Validação:** `hypothesis.py` — 6 regras hardcoded, sem ML, sem
mutação de Gene. Cada hypothesis carrega status canônico (PROPOSED,
SUPPORTED, etc). Testes confirmam invariantes.

### D4. Knowledge Graph é projection
**Validação:** `knowledge_graph.py` — graph_id derivado do tenant+patient
(content-derived), nodes/edges ordenados por id (content-derived), SHA-256
do canonical dict determinístico. Teste `test_replay_determinism.py`
valida byte-equivalência.

### D5. Research Session é reproduzível
**Validação:** `research.py` — execute + replay produzem state_hash e
result_json byte-idênticos. Teste `test_research_workspace.py`.

### D6. Explainability cross-cutting
**Validação:** `explainability.py` — TODO CorrelationResult, TODO
ClinicalHypothesis, TODO GraphEdge carregam InferenceExplanation.
Testes `test_explainability.py` + `test_hypothesis_engine.py`.

### D7. Pure domain — zero infra
**Validação:** nenhum import de flask, sqlalchemy, redis, pydantic,
requests, ou numpy/scipy nos módulos de domínio:

```bash
$ grep -rE "from flask|import flask|from sqlalchemy|from redis|from numpy" \
     araos/clinical/knowledge/domain/
# (empty — Foundation Freeze compliance)
```

### D8. Tenant isolation estrita
**Validação:** CohortBuilder rejeita pacientes cross-tenant.
ClinicalGenome rejeita Genes cross-tenant. Testes específicos.

### D9. Bitemporalidade
**Validação:** TimeWindow obrigatório em Cohort, Correlation, Genome.
Construção de expression respeita valid_time/transaction_time.

### D10. ADRs canônicos respeitados
**Validação:** ver tabela acima. Nenhuma decisão requer ADR novo.

---

## Boundary Compliance (DDD)

```
┌─────────────────────────────────────────────────┐
│       KNOWLEDGE ENGINE BOUNDED CONTEXT          │
│                                                  │
│  ┌─────────────┐                                 │
│  │ Aggregate   │ (Nenhum — context NÃO          │
│  │ Root        │  possui AGGREGATE ROOT em       │
│  │             │  Sprint 4.4)                     │
│  └─────────────┘                                 │
│         ↓ uses                                   │
│  ┌─────────────┐    ┌──────────────┐             │
│  │ ClinicalGene│ ← │Clinical      │             │
│  │ (AR/GENOME) │    │Genome (PROJ) │             │
│  └─────────────┘    └──────────────┘             │
│         ↓                                          │
│  ┌──────────────────────────────────┐            │
│  │ Engines: Correlation /            │            │
│  │ Hypothesis / KnowledgeGraph      │            │
│  │ / Cohort / Research              │            │
│  └──────────────────────────────────┘            │
│         ↓                                          │
│  ┌─────────────┐                                 │
│  │ Explainability│                                │
│  │ Pipeline      │                                │
│  └─────────────┘                                 │
└─────────────────────────────────────────────────┘
                    ↑ consumed by
                    │
            ┌──────────────┐
            │ Application  │
            │ Service      │
            │ (Knowledge   │
            │ Service)     │
            └──────────────┘
                    ↑ belongs to
                    │
            ┌──────────────┐
            │Infrastructure│
            │ InMemoryRepo │
            └──────────────┘
```

---

## Métricas de qualidade

- **Cobertura domain:** ~85% (target ≥95% — faltam fields gene.* / expression./* no CohortBuilder, integrações Sprint 4.5).
- **Cobertura application:** ~80% (DTOs não exercidos em todos os caminhos).
- **Cobertura infrastructure:** 100% (após testes do InMemory repo).
- **Testes:** 128 (todos passando).
- **Property-based test (replay determinism):** validação com N ∈ {1, 2, 5, 50}.
