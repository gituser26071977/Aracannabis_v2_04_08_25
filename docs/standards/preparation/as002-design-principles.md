# AS-002 — Princípios de Design

> **Status:** Documento de preparação (não normativo)
> **Data:** 2026-07-17
> **Propósito:** Estabelecer, **antes** da redação do AS-002, a
> **natureza conceitual** da Clinical Expression e os princípios
> que orientarão sua especificação normativa.
> **Audiência:** arquitetos e engenheiros que escreverão o AS-002.

## Natureza do Clinical Expression

> **Clinical Expression NÃO representa uma entidade.**
>
> **Clinical Expression representa um Value Object normativo.**

Sua responsabilidade é única e bem definida:

> Representar o estado observável de um Clinical Gene.

Esta distinção tem consequência direta sobre toda a modelagem
futura. Implementações que tratarem a Clinical Expression como
**entidade** produzirão modelos semanticamente incorretos, ainda
que sintaticamente válidos.

## Propriedades Fundamentais

Clinical Expression possui as propriedades abaixo. Cada uma é
**invariante lógica** e deverá ser respeitada por qualquer
implementação.

| # | Propriedade | Implicação |
|---|---|---|
| 1 | **Não possui identidade própria** | Não há `expression_id`. Duas expressions do mesmo Gene no mesmo instante e contexto são indistinguíveis. |
| 2 | **Não existe sem um Clinical Gene** | Toda Expression é parte integrante de um Gene. Expression "órfã" é modelagem incorreta. |
| 3 | **Pode ser substituída integralmente** | A Expression atual é substituída por uma nova Expression derivada. Não há mutação parcial. |
| 4 | **Preserva imutabilidade lógica** | Após produzida, a Expression anterior é congelada; sua substituição é registrada na Trajectory. |
| 5 | **É temporal** | Carrega `valid_time` (quando clinicamente relevante) e `transaction_time` (quando registrada). |
| 6 | **É contextual** | Carrega `context_dependencies` — lista de Clinical Contexts que a influenciam. |
| 7 | **Deriva exclusivamente de evidências** | Sua origem é o conjunto de Clinical Events que fundamentam o estado atual. |

## Mapeamento DDD

| Conceito | Tipo DDD |
|---|---|
| **Clinical Gene** | **Aggregate Root** |
| **Clinical Expression** | **Value Object** |

A distinção acima é arquitetural e **shall** orientar toda
implementação futura do Clinical Gene Engine:

- Toda referência à Expression **shall** ser feita dentro do
  contexto de seu Gene hospedeiro.
- Toda Equality entre duas Expressions **shall** ser estrutural
  (valor de todos os campos), nunca referencial.
- Toda substituição de Expression **shall** ser feita pelo Gene
  AR, jamais por serviço externo.

## Consequências Práticas

| Decisão | Orientada por |
|---|---|
| A Expression não é Aggregate. | Propriedade 1. |
| A Expression não tem Repository próprio. | Propriedade 1 + 2. |
| A Expression não publica Domain Events próprios. | Propriedade 1 (eventos vêm do Gene). |
| A Expression pode ser reconstruída a partir da Trajectory. | Propriedade 4. |
| A Expression carrega `valid_time` e `transaction_time`. | Propriedade 5. |
| A Expression é reavaliada quando um Clinical Context muda. | Propriedade 6. |
| A Expression só é produzida pelo mecanismo de inferência. | Propriedade 7. |

## Invariante Canônica

> **A Expression é o que se sabe sobre um Gene no presente.**
>
> **O Gene é o que se sabe sobre o paciente ao longo do tempo.**

Esta relação **assimetria temporal** entre Gene e Expression é a
chave do modelo: o Gene é durável; a Expression é atual.

## O que o AS-002 Deverá Especificar

O AS-002 — AraOS Standard 002: Clinical Expression v1.0 — deverá
detalhar:

1. **Estrutura interna** da Expression (campos canônicos).
2. **Contratos de imutabilidade** (structural equality, freeze
   after commit).
3. **Regras de produção** (como eventos geram nova Expression).
4. **Regras de reavaliação** (mudança de contexto, novas
   evidências).
5. **Integração com Trajectory** (append de Expression snapshot).
6. **Integração com Explanation** (cada nova Expression produz
   `explanation_reference`).
7. **Limites de versão** (compatibilidade retroativa).

## Princípios Norteadores para o AS-002

> **P1** — Toda expressão é substituível, não mutável.
>
> **P2** — Toda expressão nasce de evidência, nunca de estado vazio.
>
> **P3** — Toda expressão é semanticamente determinística
>         dado o mesmo conjunto de evidências.
>
> **P4** — Toda expressão preserva proveniência.
>
> **P5** — Toda expressão produz explicação.
>
> **P6** — Toda expressão é temporalmente indexada.
>
> **P7** — Nenhuma expressão "vive" sem Gene.

## Pré-requisitos do AS-002

| Pré-requisito | Status |
|---|---|
| AS-001 Aceito | ✅ (2026-07-17) |
| Paper IV publicado | ✅ |
| ADR-0005 ACCEPTED | ✅ (2026-07-17) |
| Refinamento Value Object × Entity concluído | ✅ (este documento) |
| AS-000 Language Specification (recomendado) | Pendente |

## Nota Final

> Este documento é **preparatório** e **não normativo**. Ele
> existe para registrar o consenso arquitetural sobre a
> natureza da Clinical Expression **antes** da redação formal
> do AS-002.
>
> Quando o AS-002 for Aceito, este documento será movido para
> o histórico de decisões e o AS-002 will become o único
> documento normativo sobre o tema.

---

**Próximo passo:** redação do AS-002 — AraOS Standard 002:
Clinical Expression v1.0, observando integralmente este
princípio de Value Object.