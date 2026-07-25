# AraOS Conformance Suite — ASM-001

> **Documento de planejamento da Conformance Suite do ASM-001**
> **Data:** 2026-07-17
> **Status:** Estrutura inaugural (sem testes ainda)

## Propósito

Esta suíte verificará que **todo AraOS Standard** observa a
estrutura, os requisitos e as restrições fixadas pelo **ASM-001
— Specification Meta Model**. É a guardiã da consistência
editorial da Library.

Ela **não** substitui as Conformance Suites dos AS específicos
(AS-001, AS-002, …). Ela **complementa-as** ao verificar
conformidade **estrutural** de qualquer Standard publicado.

## Organização Proposta

```
tests/conformance/ASM-001/
├── README.md                              # este arquivo
├── test_header_structure.py               # §1: campos canônicos
├── test_normative_sources.py              # §2
├── test_design_goals.py                   # §3
├── test_non_goals.py                      # §4
├── test_scope.py                          # §5
├── test_normative_references.py           # §6
├── test_terms_and_definitions.py          # §7 (referencia AS-000)
├── test_invariants.py                     # §8
├── test_formal_axioms.py                  # §9
├── test_normative_requirements.py         # §10: Requirement ID, verbos, campos
├── test_normative_verbs.py                # §12: SHALL/MAY/etc.
├── test_ddd_mapping.py                    # §13
├── test_canonical_examples.py             # §14
├── test_compliance_levels.py              # §15
├── test_conformance_requirements.py       # §16: métricas
├── test_machine_readability.py            # §17: serialização JSON
├── test_change_control.py                 # §20: SemVer
├── test_maturity_model.py                 # §21: transições permitidas
├── test_dependency_graph.py               # §22: grafo sem ciclos
├── test_traceability_chain.py             # §23: REQ → Evidence
├── test_meta_model_invariants.py          # §24: MM-INV-01..07
└── test_formal_axioms_consistency.py      # §25: coerência
```

## Mapeamento Requisito → Teste

Esta seção antecipa como cada requisito SHALL do ASM-001 será
rastreado por testes automatizados.

### §1 — Header

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 1.2 — campos canônicos | `test_header_structure.py` | Todos os 6 campos obrigatórios presentes. |
| 1.3.1 — Header é primeira seção | `test_header_structure.py` | Posição 1. |
| 1.3.2 — URN scheme | `test_header_structure.py` | Regex `urn:araos:<categoria>:<num>:<ver>`. |
| 1.3.3 — Maturidade ∈ 9 estados | `test_maturity_model.py` | Membership no enum. |

### §7 — Terms and Definitions

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 7.3 — 9 propriedades por termo | `test_terms_and_definitions.py` | Cada termo tem 9 chaves. |
| 7.3 — termos AS-000 referenciados | `test_terms_and_definitions.py` | Nenhum termo redefinido. |

### §10 — Normative Requirements

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 10.3.1 — Requirement ID canônico | `test_normative_requirements.py` | Regex `AS-XXX-REQ-NNNN`. |
| 10.3.2 — Section reference | `test_normative_requirements.py` | §X.Y.Z válida. |
| 10.3.3 — Text auto-contido | `test_normative_requirements.py` | Análise sintática. |
| 10.3.4 — Verb ∈ {SHALL, MUST, …} | `test_normative_verbs.py` | Membership. |
| 10.3.5 — Rationale presente | `test_normative_requirements.py` | Não-vazio. |
| 10.3.6 — References listadas | `test_normative_requirements.py` | Não-vazia. |
| 10.3.7 — Conformance Test referenciado | `test_traceability_chain.py` | Path resolúvel. |
| 10.3.8 — Status ∈ {active, deprecated, superseded} | `test_normative_requirements.py` | Membership. |
| 10.3.9 — Version Introduced (SemVer) | `test_normative_requirements.py` | Regex SemVer. |
| 10.3.10 — Version Deprecated optional | `test_normative_requirements.py` | Quando presente, SemVer. |
| 10.5 — Nenhum requisito sem ID | `test_normative_requirements.py` | Auditoria completa. |
| 10.5 — Deprecated só removido pós-superseded | `test_normative_requirements.py` | Coerência. |

### §12 — Normative Verbs

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 12.1 — verbos em maiúsculas | `test_normative_verbs.py` | Regex uppercase. |
| 12.2 — SHALL/MUST não misturados | `test_normative_verbs.py` | Consistência. |
| 12.2 — minúsculas = descritivo | `test_normative_verbs.py` | Apenas em prosa. |

### §16 — Conformance Metrics

| Métrica | Teste planejado | Threshold |
|---|---|---|
| Header Coverage | `test_conformance_requirements.py` | 100% |
| Section Coverage | `test_conformance_requirements.py` | 100% |
| Requirement Coverage | `test_conformance_requirements.py` | 100% |
| Dependency Coverage | `test_dependency_graph.py` | 100% |
| Maturity Consistency | `test_maturity_model.py` | 100% |
| Vocabulary Coverage | `test_terms_and_definitions.py` | 100% |
| Axiom Coverage | `test_formal_axioms.py` | 100% |

### §17 — Machine Readability

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| Requirement serializável em JSON | `test_machine_readability.py` | `json.dumps()` sem erro. |
| Standard serializável em JSON | `test_machine_readability.py` | Estrutura conforme §17.4. |
| Nenhum campo obrigatório fora de §10.3 | `test_machine_readability.py` | Schema check. |

### §20 — Change Control

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| SemVer compliance | `test_change_control.py` | Regex SemVer. |
| Replacement → supersedes_by simétrico | `test_change_control.py` | Coerência. |

### §21 — Maturity Model

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 9 estados enforçados | `test_maturity_model.py` | Enum membership. |
| Transições monotônicas | `test_maturity_model.py` | State machine. |
| Published → Verified → Reference Implementation | `test_maturity_model.py` | Ordem obrigatória. |

### §22 — Dependency Graph

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| Sem dependência ascendente | `test_dependency_graph.py` | DFS check. |
| Sem ciclos | `test_dependency_graph.py` | Tarjan. |
| Sem auto-referência (exceto versioning) | `test_dependency_graph.py` | Exceção controlada. |

### §23 — Traceability Chain

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| Toda REQ com cadeia até Evidence | `test_traceability_chain.py` | Path completo. |
| Coverage ≥ 100% | `test_traceability_chain.py` | Métrica. |

### §24 — Meta-Model Invariants

| Invariante | Teste planejado |
|---|---|
| MM-INV-01 — Standard com ≥1 REQ | `test_meta_model_invariants.py` |
| MM-INV-02 — REQ com exatamente 1 verb | `test_meta_model_invariants.py` |
| MM-INV-03 — REQ com ≥1 test | `test_meta_model_invariants.py` |
| MM-INV-04 — Standard com ≥1 artifact | `test_meta_model_invariants.py` |
| MM-INV-05 — Standard com ≥1 source | `test_meta_model_invariants.py` |
| MM-INV-06 — Deprecated com Superseded By | `test_meta_model_invariants.py` |
| MM-INV-07 — Contagem de REQs consistente | `test_meta_model_invariants.py` |

### §25 — Formal Axioms

| Axioma | Teste planejado |
|---|---|
| 1 — Structure Precedes Content | `test_formal_axioms_consistency.py` |
| 2 — Requirements are Testable | `test_formal_axioms_consistency.py` |
| 3 — Vocabulary is Canonical | `test_terms_and_definitions.py` |
| 4 — Dependency is Strictly Downward | `test_dependency_graph.py` |
| 5 — Maturity is Monotonic | `test_maturity_model.py` |
| 6 — Conformance Precedes Reference | `test_maturity_model.py` |
| 7 — Traceability is Total | `test_traceability_chain.py` |
| 8 — Machine Readability is Mandatory | `test_machine_readability.py` |
| 9 — Section Structure is Mandatory | `test_conformance_requirements.py` |
| 10 — Backward Compatibility is Default | `test_change_control.py` |

## Estratégia de Implementação

### Fase 1 — Conformidade Documental (PRIORIDADE 1)

Foco: verificar que documentos Markdown observam estrutura e
requisitos textuais.

- `test_header_structure.py`
- `test_normative_sources.py`
- `test_design_goals.py`
- `test_non_goals.py`
- `test_scope.py`
- `test_normative_references.py`
- `test_terms_and_definitions.py`
- `test_normative_requirements.py`
- `test_ddd_mapping.py`
- `test_canonical_examples.py`

### Fase 2 — Conformidade Axiomática (PRIORIDADE 2)

Foco: verificar respeito aos axiomas e invariantes.

- `test_invariants.py`
- `test_formal_axioms.py`
- `test_formal_axioms_consistency.py`
- `test_meta_model_invariants.py`

### Fase 3 — Conformidade Comportamental (PRIORIDADE 3)

Foco: verificar comportamento operacional.

- `test_conformance_requirements.py`
- `test_machine_readability.py`
- `test_change_control.py`

### Fase 4 — Conformidade Cross-AS (PRIORIDADE 4)

Foco: garantir coerência entre Standards e Maturity Model.

- `test_maturity_model.py`
- `test_dependency_graph.py`
- `test_traceability_chain.py`

## Critério de Done da Conformance Suite

A suíte é considerada **completa** quando:

1. Cobre **100% dos requisitos SHALL** do ASM-001.
2. Cobre **100% dos axiomas** do ASM-001.
3. Roda em CI (≤ 5 minutos).
4. Falha determinística em qualquer violação.
5. Documenta **o que falhou e por quê** em mensagens claras.
6. Atinge **Verified** quando passa integralmente (gatilho para
   promover ASM-001 a estado Verified no AraOS Library).

## Estado Atual

| Componente | Status |
|---|---|
| `tests/conformance/ASM-001/` | Criado |
| `tests/conformance/ASM-001/README.md` | ✅ |
| 23 arquivos de teste planejados | Pendentes |

## Próximos Passos

1. Aguardar promoção de **ASM-001 para Technical Review**.
2. Implementar Fase 1 em paralelo à reestruturação editorial
   dos AS existentes conforme as 16 seções canônicas.
3. Atingir **Verified** após a Conformance Suite passar
   integralmente.

---

**Esta suíte é a guardiã da Specification Meta Model.**
