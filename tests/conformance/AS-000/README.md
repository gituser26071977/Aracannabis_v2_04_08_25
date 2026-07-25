# AraOS Conformance Suite — AS-000

> **Documento de planejamento da Conformance Suite do AS-000**
> **Data:** 2026-07-17
> **Status:** Estrutura inaugural (sem testes ainda)

## Propósito

Esta suíte de testes verificará que toda implementação do
AraOS **observa a gramática oficial** fixada pelo AS-000.

Ela **não** substitui as suítes de testes dos módulos do
sistema. Ela **complementa-as** ao verificar conformidade
*terminológica*, *axiomática* e *arquitetural* com o Standard.

## Organização Proposta

```
tests/conformance/AS-000/
├── README.md                          # este arquivo
├── test_vocabulary_conformance.py     # nível 0: termos canônicos
├── test_axiom_conformance.py          # nível 1: axiomas
├── test_ddd_mapping.py                # nível 2: DDD classification
├── test_no_redefinition.py            # §6.1: nenhum Standard redefine termos
└── test_registry_terms.py             # §3.15: Registry usa linguagem oficial
```

## Mapeamento Requisito → Teste

Esta seção antecipa como cada requisito SHALL do AS-000 será
rastreado por testes automatizados.

### §6.1 — Proibição de Redefinição

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 6.1.1 — nenhum Standard redefine termos | `test_no_redefinition.py` | Static analysis: scaneia docs/standards/ procurando definições divergentes de §3. |
| 6.1.2 — referenciar AS-000 §3.X | `test_no_redefinition.py` | Verifica que toda seção que usa termos canônicos inclui link para AS-000 §3.X. |

### §6.2 — Uso Obrigatório de Termos Canônicos

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 6.2.1 — uso exclusivo de termos §3 | `test_vocabulary_conformance.py` | Lint de vocabulário contra a lista canônica de §3. |
| 6.2.2 — termos legados proibidos | `test_vocabulary_conformance.py` | Falha quando encontrar *capability* (e outros legados) em código novo. |

### §6.3 — Mapeamento DDD

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 6.3.1 — declaração DDD em Standards | `test_ddd_mapping.py` | Verifica que toda seção "Natureza DDD" existe em cada AS. |
| 6.3.2 — divergências justificadas | `test_ddd_mapping.py` | Verifica presença de ADR referenciado quando divergência existir. |

### §6.4 — Axiomas Não-Negociáveis

| Axioma | Teste planejado | Como verificar |
|---|---|---|
| 1 — Knowledge precedes Data | `test_axiom_conformance.py` | Documentação não pode apresentar dados antes de contexto de conhecimento. |
| 2 — Language governs Architecture | `test_axiom_conformance.py` | Toda decisão arquitetural referencia a linguagem que a justifica. |
| 3 — Aggregate Roots own VOs | `test_axiom_conformance.py` | Nenhum VO existe fora de Aggregate. |
| 4 — VOs have no semantic identity | `test_axiom_conformance.py` | Value Objects não expõem campo `id`. |
| 5 — Events modify state, not identity | `test_axiom_conformance.py` | Domain Events não alteram Semantic Identity em testes de replay. |
| 6 — Interpretations are projections | `test_axiom_conformance.py` | Nenhuma Interpretation escrita como canonical state. |
| 7 — Canonical state reconstructable | `test_axiom_conformance.py` | Property-based: replay 1x/2x/50x/100x produz mesmo estado. |
| 8 — Single official definition | `test_no_redefinition.py` | Cada termo canônico tem uma única definição em AS-000. |
| 9 — Knowledge is temporal | `test_axiom_conformance.py` | Estados evolutivos carregam `valid_time` + `transaction_time`. |
| 10 — Knowledge is explainable | `test_axiom_conformance.py` | Toda Interpretation carrega `explanation_reference`. |
| 11 — Knowledge is probabilistic | `test_axiom_conformance.py` | Confidence explícita em Expressões e Interpretações. |
| 12 — Hypotheses coexist | `test_axiom_conformance.py` | Múltiplas Hypothesis podem coexistir; nenhuma sobrescreve outra. |

### §6.5 — Conformidade Cross-Standard

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 6.5.1 — coerência semântica | `test_no_redefinition.py` | Combinações de Standards preservam definições de §3. |
| 6.5.2 — AS-000 prevalece | `test_no_redefinition.py` | Em conflito, AS-000 prevalece sobre outros AS. |

### §6.6 — Versionamento

| Requisito | Teste planejado | Como verificar |
|---|---|---|
| 6.6.1 — major em mudanças incompatíveis | `test_no_redefinition.py` | Verifica bump de major quando termo canônico muda. |
| 6.6.2 — minor em adições | (manual) | Verificação editorial. |
| 6.6.3 — patch em correções | (manual) | Verificação editorial. |

## Estratégia de Implementação

### Fase 1 — Conformidade Documental (PRIORIDADE 1)

Foco: verificar que o **catálogo** de Standards respeita AS-000.

- `test_vocabulary_conformance.py`
- `test_no_redefinition.py`
- `test_ddd_mapping.py`

### Fase 2 — Conformidade Axiomática (PRIORIDADE 2)

Foco: verificar que **implementações** existentes respeitam
axiomas. Usa property-based testing (Hypothesis) para Axiom 7
(replay).

- `test_axiom_conformance.py`

### Fase 3 — Conformidade Runtime (PRIORIDADE 3)

Foco: testes integrados que verificam comportamento de
Aggregate Roots, Value Objects, Projections em cenários
reais.

## Critério de Done da Conformance Suite

A suíte é considerada **completa** quando:

1. Cobre **100% dos requisitos SHALL** do AS-000.
2. Cobre **100% dos axiomas** do AS-000.
3. Roda em CI (≤ 5 minutos).
4. Falha determinística em qualquer violação detectada.
5. Documenta **o que falhou e por quê** em mensagens claras.

## Estado Atual

| Componente | Status |
|---|---|
| `tests/conformance/AS-000/` | Criado |
| `tests/conformance/AS-000/README.md` | ✅ |
| `test_vocabulary_conformance.py` | Pendente |
| `test_axiom_conformance.py` | Pendente |
| `test_ddd_mapping.py` | Pendente |
| `test_no_redefinition.py` | Pendente |
| `test_registry_terms.py` | Pendente |

## Próximos Passos

1. Aguardar o AS-000 ser promovido de **Draft** para
   **Review**.
2. Após promoção, implementar Fase 1 (conformidade
   documental).
3. Após AS-001 + AS-002 estarem Published + implementados,
   implementar Fase 2 (conformidade axiomática) com base em
   exemplos reais.

---

**Esta suíte é a guardiã da gramática do AraOS.**