# AraOS Standards (AS)

> **Status:** Adotado — primeira emissão AS-001 publicada em 2026-07-17.
> **Data:** 2026-07-17 (atualizado pós-ASM-001)

## Definição

**AraOS Standard (AS)** é um documento normativo que define
**exatamente como um conceito ou teoria do AraOS deve ser implementado**.

Padrão de numeração: `AS-XXX — Título`. Versões SemVer.

A estrutura de todo AS SHALL seguir as 16 seções canônicas fixadas
pela **ASM-001 — Specification Meta Model**.

## Distinção entre os Documentos Canônicos do AraOS

| Tipo | Sigla | Propósito | Status atual |
|---|---|---|---|
| **Papers** | Paper I, II, … | Desenvolvimento teórico. Estabelecem os conceitos, princípios e relações. | Paper II, IV, V, VI publicados. |
| **ADRs** | ADR-XXXX | Decisões arquiteturais. Documentam o **porquê** de uma escolha técnica. | ADR-0001 … ADR-0005. |
| **AraOS Meta Specifications** | **ASM-XXX** | Estrutura normativa dos Standards (metanormativo). | **ASM-001 Draft (2026-07-17)**. |
| **AraOS Standards** | **AS-XXX** | Especificações normativas. Definem **exatamente como** a teoria deve ser implementada. | **AS-001 Published (2026-07-17)**. |

Os quatro tipos são complementares:

- O **Paper** explica a teoria.
- O **ADR** documenta a decisão arquitetural.
- A **ASM** fixa a estrutura pela qual os AS são escritos.
- O **AraOS Standard** torna a teoria e a decisão **executáveis**.

## Hierarquia Canônica

```
Constituição (Lex AraOS)
   ↓
AS-000 Language Specification (vocabulário)
   ↓
ASM-001 Specification Meta Model (estrutura)
   ↓
AraOS Standards (AS-XXX — especificações normativas)
   ↓
Implementação (código + testes)
```

Uma implementação está em conformidade com o AraOS quando:

1. Respeita os princípios do(s) Paper(s) correspondente(s).
2. Está alinhada com o ADR que rege a área.
3. Implementa fielmente o AraOS Standard que rege o conceito.
4. Passa na suite de testes de conformidade (ver ASM-001 §16).
5. Foi escrita conforme a estrutura fixada pela ASM-001.

## Catálogo Atual

| ID | Título | Posição | Status |
|---|---|---|---|
| ASM-001 | Specification Meta Model v1.0 | acima de AS-001..006 | **Draft** (2026-07-17) |

## Catálogo Proposto

| ID | Título | Paper de Referência | ADR de Referência | Status |
|---|---|---|---|---|
| **AS-001** | Clinical Gene v1.0 | Paper III (Clinical Genome) | ADR-0005 | **Published** (2026-07-17) |
| AS-000 | AraOS Language Specification v1.0 | Paper II | (TBD) | **Draft** (2026-07-17) |
| **AS-002** | Clinical Expression v1.0 | Paper IV | ADR-0005 | **Draft** (2026-07-17) |
| AS-003 | Clinical Genome v1.0 | Paper III | ADR-0005 | **Após implementação** de AS-001 + AS-002 |
| AS-004 | Clinical Inference v1.0 | Paper V | ADR-0005 | Planejado |
| AS-005 | Clinical Interpretation v1.0 | Paper VI | ADR-0005 | Planejado |
| AS-006 | Clinical Context v1.0 | — | ADR-0003 | Planejado (pós Sprint 4.2) |

> **NOTA — Sequência editorial revisada em 2026-07-17:** AS-003
> será redigido **somente após** a primeira implementação
> concreta e testada do Aggregate Root (AS-001) e da Expression
> (AS-002). A teoria do Genome reflete a prática operacional.
> Ver Apêndice F do AS-000.

> **NOTA — Maturity Model atualizado em 2026-07-17 (pós-ASM-001):**
> AS-001 foi reclassificado de "Verified" para "Published" porque
> o modelo de 9 estados exige que Verified venha antes de
> Reference Implementation e Verified requer Conformance Suite
> passando (não apenas testes de unidade). Ver ASM-001 §21.

## Natureza DDD dos AraOS Standards

Cada AraOS Standard é mapeado a uma categoria DDD canônica.
Itens não publicados permanecem como **Draft** até a redação
definitiva de cada AS.

| AS | Título | Natureza | Tipo DDD | Estado Editorial |
|---|---|---|---|---|
| **ASM-001** | Specification Meta Model | Meta-normative Specification | (Aggregate Root sobre Standards) | Draft |
| **AS-000** | AraOS Language Specification | Foundational Standard | (meta-normativo) | Draft |
| **AS-001** | Clinical Gene | Aggregate Root | Aggregate Root | **Published** |
| **AS-002** | Clinical Expression | Value Object | Value Object | Draft |
| AS-003 | Clinical Genome | Aggregate (read-model) | Aggregate | Draft (pós-implementação) |
| AS-004 | Clinical Inference | Domain Service | Domain Service | Draft |
| AS-005 | Clinical Interpretation | Projection | Projection | Draft |
| AS-006 | Clinical Context | Bounded Context | Aggregate Root | Draft |

> **NOTA** — Esta tabela é **orientativa** e será refinada em
> cada AS publicado. A categoria DDD definitiva de cada
> conceito é fixada no AraOS Standard correspondente.

## Diretrizes para Escrita de um AraOS Standard

1. **Estrutura canônica** — todo AS SHALL seguir as 16 seções
   definidas na **ASM-001 §1–§17**. Verbos SHALL ser RFC 2119
   (`SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`,
   `SHOULD NOT`, `MAY`).
2. **Requirement ID canônico** — todo requisito SHALL ter ID
   no formato `AS-XXX-REQ-NNNN` (ASM-001 §10.3.1).
3. **Independência de implementação** — o AS descreve o
   **contrato**, não o código. Implementações concretas estão
   fora do escopo.
4. **Conformidade verificável** — cada requisito deve poder ser
   testado. A Conformance Suite referencia cada cláusula.
5. **Versionamento SemVer** — `MAJOR.MINOR.PATCH`. Mudanças
   incompatíveis incrementam `MAJOR`. Adições retrocompatíveis
   incrementam `MINOR`. Correções, `PATCH`.
6. **Maturidade explícita** — todo AS SHALL declarar seu
   estado no Maturity Model de 9 estados (ASM-001 §21).
7. **Mapeamento completo** — cada AS referencia o(s) Paper(s)
   e ADR(s) que materializa.
8. **Vocabulário do AS-000** — termos canônicos SHALL ser
   referenciados por seção AS-000 §3.X; nunca redefinidos.
9. **Dependency graph** — todo AS SHALL depender apenas de
   Standards anteriores na ordem canônica (ASM-001 §22).
10. **Traceability chain** — todo requisito SHALL ter cadeia
    completa até Evidence (ASM-001 §23).

## Localização

- Canônica: `docs/standards/AS-XXX-titulo.md`
- Library: `docs/library/standards/AS-XXX-titulo-vY.Z.{md,html,pdf.txt}`
- Meta-norma: `docs/meta/ASM-XXX-titulo.md` + `docs/library/meta/`