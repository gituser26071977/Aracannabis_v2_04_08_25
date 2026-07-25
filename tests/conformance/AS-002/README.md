# AraOS Conformance Suite — AS-002

> **Documento de planejamento da Conformance Suite do AS-002**
> **Data:** 2026-07-17
> **Status:** Estrutura inaugural (sem testes ainda)

## Propósito

Esta suíte de testes verificará que toda implementação da
Clinical Expression **observa o contrato normativo** fixado pelo
AS-002, utilizando exclusivamente a gramática do AS-000.

Ela **não** substitui as suítes de testes dos módulos do
sistema. Ela **complementa-as** ao verificar conformidade
*terminológica*, *axiomática* e *estrutural* com o Standard.

## Organização Proposta

```
tests/conformance/AS-002/
├── README.md                          # este arquivo
├── test_vocabulary_conformance.py     # §3: uso dos 17 termos canônicos
├── test_value_object_invariants.py    # §4.1, §5: Expression é VO
├── test_required_fields.py            # §4.2: Confidence, Observed Value etc.
├── test_explainability.py             # §4.3, Axiom 6: Explanation Reference
├── test_temporality.py                # §4.4, Axiom 3: bitemporalidade
├── test_contextual.py                 # §4.5, Axiom 4: Context References
├── test_immutability.py               # §4.6: substituição integral
├── test_equality.py                   # §4.7: igualdade estrutural
├── test_trajectory_append_only.py     # §4.8: Trajectory append-only
├── test_hypothesis_coexistence.py     # §4.9, Axiom 12
├── test_grammar_consistency.py        # gramática AS-000
└── test_ddd_mapping.py                # §7: Value Object
```

## Mapeamento Requisito → Teste

Esta seção antecipa como cada requisito SHALL do AS-002 será
rastreado por testes automatizados.

### §3 — Termos e Definições (17 conceitos)

| Termo | Teste planejado | Como verificar |
|---|---|---|
| Clinical Expression | `test_value_object_invariants.py` | Verifica que Expression é VO. |
| Expression State | `test_required_fields.py` | Todos os campos obrigatórios presentes. |
| Observed Value | `test_required_fields.py` | Campo presente, mesmo que `null`. |
| Confidence | `test_required_fields.py` | Intervalo `[0.0, 1.0]` fechado. |
| Trend | `test_vocabulary_conformance.py` | Valores ∈ {improving, stable, declining, oscillating, unknown}. |
| Volatility | `test_vocabulary_conformance.py` | Valores ∈ {low, medium, high, unknown}. |
| Clinical Interpretation Reference | `test_required_fields.py` | Cardinalidade 0..1. |
| Explanation Reference | `test_explainability.py` | Nunca vazio. |
| Evidence References | `test_value_object_invariants.py` | Cardinalidade 1..*. |
| Context References | `test_contextual.py` | Apenas Contexts válidos. |
| Last Update | `test_temporality.py` | Timezone-aware UTC. |
| Valid Time | `test_temporality.py` | Timezone-aware UTC. |
| Transaction Time | `test_temporality.py` | Timezone-aware UTC; ≥ Valid Time. |
| Unknown State | `test_vocabulary_conformance.py` | Representation canônica. |
| Unavailable State | `test_vocabulary_conformance.py` | Gene em `not_observed`. |
| Derived State | `test_ddd_mapping.py` | is-a Expression; nunca canonical. |
| Canonical Expression | `test_value_object_invariants.py` | Uma por Gene. |

### §4 — Invariantes (Requisitos Normativos)

#### §4.1 Identidade e Pertinência

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.1.1 — exatamente um Gene | `test_value_object_invariants.py` | Toda Expression carrega Gene. |
| 4.1.2 — sem semantic identity | `test_value_object_invariants.py` | Expression não expõe `id` próprio. |
| 4.1.3 — nunca detached | `test_value_object_invariants.py` | Expression órfã é rejeitada. |
| 4.1.4 — sem campo `id` | `test_value_object_invariants.py` | Reflexão: `hasattr(expr, 'id') == False`. |

#### §4.2 Conteúdo Mínimo

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.2.1 — Confidence explícita `[0,1]` | `test_required_fields.py` | Property-based: 1000 valores válidos. |
| 4.2.2 — Observed Value sempre presente | `test_required_fields.py` | Pode ser `null` mas nunca ausente. |
| 4.2.3 — Trend/Volatility enumerados | `test_required_fields.py` | Membership em conjuntos enumerados. |
| 4.2.4 — Timestamps UTC | `test_required_fields.py` | `tzinfo == timezone.utc`. |

#### §4.3 Explicabilidade e Evidência

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.3.1 — Explanation nunca vazio | `test_explainability.py` | Falha quando ausente. |
| 4.3.2 — Evidence 1..* | `test_value_object_invariants.py` | Lista não-vazia. |
| 4.3.3 — reconstructable | `test_immutability.py` | Property-based: replay 1x/2x/50x/100x. |

#### §4.4 Temporalidade

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.4.1 — bitemporalidade | `test_temporality.py` | Valid + Transaction presentes. |
| 4.4.2 — Transaction ≥ Valid | `test_temporality.py` | Assertion. |
| 4.4.3 — Expression anterior preservada | `test_trajectory_append_only.py` | Substituição adiciona snapshot, não remove. |

#### §4.5 Contextualidade

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.5.1 — Contexts válidos | `test_contextual.py` | Membership no escopo. |
| 4.5.2 — remoção dispara reavaliação | `test_contextual.py` | Evento de remoção publicado. |

#### §4.6 Imutabilidade

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.6.1 — Expression immutable | `test_immutability.py` | Atributos `frozen=True`. |
| 4.6.2 — Events replace | `test_immutability.py` | Substituição integral, não merge. |
| 4.6.3 — New snapshot | `test_immutability.py` | Snapshot em Trajectory. |

#### §4.7 Comparação e Igualdade

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.7.1 — equality estrutural | `test_equality.py` | `==` quando campos iguais. |
| 4.7.2 — comparação determinística | `test_equality.py` | Resultado estável. |

#### §4.8 Trajetória e Histórico

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.8.1 — snapshot em Trajectory | `test_trajectory_append_only.py` | Após publicação, snapshot presente. |
| 4.8.2 — append-only | `test_trajectory_append_only.py` | Tentativa de remoção falha. |

#### §4.9 Interação com Hipóteses

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 4.9.1 — múltiplas Hypothesis | `test_hypothesis_coexistence.py` | Coexistem. |
| 4.9.2 — sem sobrescrita | `test_hypothesis_coexistence.py` | Hypothesis não substitui Expression. |

### §5 — Axiomas

| Axioma | Teste planejado |
|---|---|
| 1 — VO | `test_value_object_invariants.py` |
| 2 — no identity | `test_value_object_invariants.py` |
| 3 — temporal | `test_temporality.py` |
| 4 — contextual | `test_contextual.py` |
| 5 — derived from Evidence | `test_value_object_invariants.py` |
| 6 — explainable | `test_explainability.py` |
| 7 — reconstructable | `test_immutability.py` |
| 8 — projection | `test_ddd_mapping.py` |
| 9 — never owns knowledge | `test_grammar_consistency.py` |
| 10 — represents knowledge | `test_grammar_consistency.py` |

### §6 — Modelo Computacional

| Item | Teste planejado |
|---|---|
| Current Expression | `test_value_object_invariants.py` |
| Historical Expression | `test_trajectory_append_only.py` |
| Expression Snapshot | `test_immutability.py` |
| Expression Timeline | `test_trajectory_append_only.py` |
| Expression Replacement | `test_immutability.py` |
| Expression Reconstruction | `test_immutability.py` |
| Expression Serialization | `test_equality.py` |
| Expression Comparison | `test_equality.py` |
| Expression Equality | `test_equality.py` |
| Expression Lifecycle | `test_immutability.py` |

### §7 — DDD Mapping

| Requisito | Teste planejado |
|---|---|
| Expression é Value Object | `test_ddd_mapping.py` |
| Gene é Aggregate Root | `test_grammar_consistency.py` (delegado a AS-001) |

### Gramática AS-000

| Requisito | Teste planejado |
|---|---|
| Sem redefinição de termos | `test_grammar_consistency.py` |
| Conformidade cumulativa | `test_grammar_consistency.py` |

## Estratégia de Implementação

### Fase 1 — Conformidade Estrutural (PRIORIDADE 1)

Foco: verificar que o módulo `Expression` respeita estrutura e
invariantes.

- `test_value_object_invariants.py`
- `test_required_fields.py`
- `test_vocabulary_conformance.py`
- `test_ddd_mapping.py`

### Fase 2 — Conformidade Axiomática (PRIORIDADE 2)

Foco: verificar respeito aos axiomas.

- `test_explainability.py`
- `test_temporality.py`
- `test_contextual.py`
- `test_immutability.py`
- `test_equality.py`

### Fase 3 — Conformidade Comportamental (PRIORIDADE 3)

Foco: comportamento operacional da Expression ao longo do
tempo.

- `test_trajectory_append_only.py`
- `test_hypothesis_coexistence.py`
- Property-based: replay 1x / 2x / 50x / 100x / ordem
  aleatória.

### Fase 4 — Conformidade Cross-AS (PRIORIDADE 4)

Foco: garantir coerência com AS-000 e AS-001.

- `test_grammar_consistency.py`

## Critério de Done da Conformance Suite

A suíte é considerada **completa** quando:

1. Cobre **100% dos requisitos SHALL** do AS-002.
2. Cobre **100% dos axiomas** do AS-002.
3. Roda em CI (≤ 5 minutos).
4. Falha determinística em qualquer violação.
5. Documenta **o que falhou e por quê** em mensagens claras.
6. Atinge **Verified** quando passa integralmente (gatilho para
   promover AS-002 para estado Verified no AraOS Library).

## Estado Atual

| Componente | Status |
|---|---|
| `tests/conformance/AS-002/` | Criado |
| `tests/conformance/AS-002/README.md` | ✅ |
| 12 arquivos de teste planejados | Pendentes |

## Próximos Passos

1. Aguardar promoção de **AS-002 para Technical Review**.
2. Implementar Fase 1 (conformidade estrutural) em paralelo à
   implementação do módulo `Expression` na Sprint 4.3 Phase 2.
3. Atingir **Verified** após a Conformance Suite passar
   integralmente, no mesmo gate que promove AS-002 a
   Reference Implementation.

---

**Esta suíte é a guardiã do Value Object Clinical Expression.**