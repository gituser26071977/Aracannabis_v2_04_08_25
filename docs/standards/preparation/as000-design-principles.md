# AS-000 — AraOS Language Specification

> **Status:** Documento de preparação (não normativo)
> **Data:** 2026-07-17
> **Posição no catálogo:** Reservado (pós-AS-002)
> **Propósito:** Estabelecer, **antes** da redação do AS-002, a
> **gramática comum** que todos os AraOS Standards passarão a
> referenciar.
> **Audiência:** arquitetos e engenheiros que escreverão o AS-002
> e AraOS Standards subsequentes.

## Visão

> **AS-000 não descreve conceitos clínicos. Descreve as
> categorias fundamentais sobre as quais todos os AraOS
> Standards serão escritos.**

Toda vez que um AS precisa utilizar um termo como *Entity*,
*Value Object*, *Aggregate*, *Domain Event*, *Projection*,
*Evidence*, *Context*, *Canonical State*, *Derived State*,
*Interpretation*, *Hypothesis*, atualmente ele **redefine** o
termo. Isso provoca três problemas:

1. **Duplicação**: a mesma definição aparece em vários AS com
   pequenas variações.
2. **Inconsistência sutil**: AS-002 pode definir *Value Object*
   ligeiramente diferente de AS-003.
3. **Dificuldade de composição**: quando um sistema precisa
   cumprir dois AS simultaneamente, surgem ambiguidades.

**AS-000 elimina esses três problemas** ao centralizar a
definição canônica dos termos arquiteturais.

## Posição Hierárquica

```
Constituição do AraOS  (lei suprema do domínio)
   ↓
AS-000 Language Spec   (gramática comum — este documento)
   ↓
AS-001 .. AS-006       (normas específicas de domínio)
   ↓
Implementação
```

**AS-000 ocupa um lugar hierárquico acima dos AS específicos**:
ele é o **padrão de padrões**, equivalente em importância à
Constituição, mas com **escopo técnico-linguístico** (não
clínico-filosófico).

## Termos a Definir (Catálogo Inicial)

AS-000 deverá fixar as definições canônicas dos seguintes
termos:

| # | Termo | Categoria | Uso típico |
|---|---|---|---|
| 1 | **Entity** | DDD core | Identidade referencial, ciclo de vida próprio. |
| 2 | **Value Object** | DDD core | Igualdade estrutural, sem identidade, imutável. |
| 3 | **Aggregate** | DDD core | Cluster de Entities + VOs sob uma raiz. |
| 4 | **Aggregate Root** | DDD core | Ponto de entrada do Aggregate. |
| 5 | **Domain Event** | DDD core | Fato passado relevante ao domínio. |
| 6 | **Projection** | Read model | Estado derivado, rebuildable. |
| 7 | **Evidence** | Knowledge | Item atômico de sustentação. |
| 8 | **Context** | Knowledge | Modulador semântico do estado. |
| 9 | **Canonical State** | State | Fonte primária de verdade. |
| 10 | **Derived State** | State | Estado calculado a partir de Canonical. |
| 11 | **Interpretation** | Knowledge | Leitura atual do estado pelo sistema. |
| 12 | **Hypothesis** | Knowledge | Interpretação alternativa concorrente. |

Este catálogo é **aberto** — novos termos podem ser adicionados
em versões futuras do AS-000.

## Princípios Norteadores

> **P1** — Cada termo **shall** ter **uma única definição**
> canônica no AraOS Library.
>
> **P2** — Nenhum AraOS Standard **may** redefinir um termo já
> fixado pelo AS-000; **shall** apenas referenciar.
>
> **P3** — Termos definidos pelo AS-000 **shall** ser usados
> com o mesmo significado em todos os AS subsequentes.
>
> **P4** — Termos herdados do DDD **shall** ser referenciados
> ao AS-000, não a fontes externas (Eric Evans, Vaughn Vernon),
> exceto quando o AS-000 ainda não cobrir o termo.
>
> **P5** — Conflito entre AS-000 e Constituição **shall** ser
> resolvido a favor da Constituição.
>
> **P6** — Conflito entre AS-000 e um AS específico **shall** ser
> resolvido a favor do AS-000 (gramática prevalece).

## Aplicação Imediata (Pré-AS-002)

Antes da redação do AS-002, AS-000 deverá fixar pelo menos os
seguintes termos — **pré-requisitos do AS-002**:

| Termo | Necessário para |
|---|---|
| Value Object | AS-002 (Clinical Expression é VO) |
| Aggregate Root | AS-001 já pressupõe, AS-002 confirma |
| Evidence | AS-002 (Expression deriva de evidências) |
| Hypothesis | AS-002 (Expression admite hipóteses concorrentes) |
| Interpretation | AS-002 / AS-005 |
| Canonical State / Derived State | AS-002 / AS-003 (Genome vs. Expression) |
| Context | AS-002 / AS-006 |

## Estrutura Proposta do AS-000 (quando redigido)

```
AS-000 — AraOS Language Specification

§1   Escopo
§2   Referências normativas (Constituição + DDD clássicos)
§3   Termos e Definições (12 termos do catálogo inicial)
     §3.1  Entity
     §3.2  Value Object
     §3.3  Aggregate
     §3.4  Aggregate Root
     §3.5  Domain Event
     §3.6  Projection
     §3.7  Evidence
     §3.8  Context
     §3.9  Canonical State
     §3.10 Derived State
     §3.11 Interpretation
     §3.12 Hypothesis
§4   Convenções de Uso
§5   Conformidade
§6   Mapeamento para Fontes Normativas
Apêndice A — Glossário de Referência Rápida
Apêndice B — Histórico de Versões
```

## Pré-requisitos do AS-000

| Pré-requisito | Status |
|---|---|
| Catálogo inicial de termos proposto | ✅ (este documento) |
| Catálogo aceito pelo AraOS Architecture | Pendente |
| AS-001 Aceito (referência obrigatória) | ✅ |
| AS-002 publicado (referência obrigatória) | Pendente |
| Constituição do AraOS publicada | ✅ |

## Posicionamento Editorial

| Família | Função |
|---|---|
| Constituição | Filosofia do domínio |
| **AS-000** | **Gramática (termos arquiteturais)** |
| AS-001..006 | Vocabulário clínico específico |

AS-000 é **publicado primeiro** logicamente, mas **redigido em
paralelo** ao AS-002. Quando ambos atingirem Published, o
catálogo AraOS Library passa a ter três camadas coerentes:
Filosofia → Gramática → Vocabulário.

## Sequência Editorial Revisada (2026-07-17)

> **Decisão arquitetural registrada após discussão editorial.**

A sequência de redação/publicação do catálogo clínico é:

1. **AS-000** (gramática) → Draft ✅
2. **AS-001** (Aggregate Root) → Published ✅
3. **AS-002** (Value Object) → próximo
4. **Implementação concreta** de AS-001 + AS-002 com testes
   ≥ 95% coverage (Sprint 4.3 Phase 2)
5. **AS-003** (Aggregate Genome) → **somente após** o item 4
6. AS-004 / AS-005 / AS-006 → após AS-003

**Justificativa:** a teoria do Genome como Aggregate que agrega
múltiplos Genes **deve** ser informada pela experiência
operacional de ter escrito e exercitado um Gene real + uma
Expression real. Publicar o AS-003 antes da implementação
convidaria a especular arquitetura sem evidência.

**Implicação prática:** após Sprint 4.3 Phase 2 (Gene +
Expression implementados e testados), o AraOS Architecture
Board **shall** revisar a experiência operacional antes de
redigir o AS-003. Lições aprendidas **may** ser publicadas como
AraOS Notes (AN-XXX) informativas antes do Standard formal.

---

**Próximo passo:** redação do AS-002 — AraOS Standard 002:
Clinical Expression v1.0 — em paralelo à finalização do AS-000
— AraOS Language Specification v1.0. AS-002 será publicado
primeiro; AS-000 em seguida, com catálogo de termos
consolidado. AS-003 aguardará a implementação concreta.