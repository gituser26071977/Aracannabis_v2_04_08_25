# AraOS Meta Specifications (ASM)

> **Status:** Adotado — ASM-001 redigido em Draft em 2026-07-17.
> **Data:** 2026-07-17

## Definição

**AraOS Meta Specification (ASM)** é um documento **metanormativo**
que governa a **estrutura** de outros documentos do AraOS. Ele NÃO
define conceitos clínicos nem regras de negócio — define **como
outros Standards devem ser escritos**.

A numeração segue o esquema `ASM-XXX — Título`. Versões SemVer.

## Distinção entre tipos de documentos canônicos

| Tipo | Sigla | Propósito | Status |
|---|---|---|---|
| **Papers** | Paper I, II, … | Desenvolvimento teórico. | Paper II, IV, V, VI publicados. |
| **ADRs** | ADR-XXXX | Decisões arquiteturais. | ADR-0001 … ADR-0005. |
| **AraOS Standards** | AS-XXX | Especificações normativas clínicas. | AS-000 (Draft), AS-001 (Verified), AS-002 (Draft). |
| **AraOS Meta Specifications** | **ASM-XXX** | **Estrutura normativa dos próprios Standards.** | **ASM-001 (Draft, 2026-07-17).** |

## Hierarquia Canônica

```
Constituição (Lex AraOS)              ← filosofia
   ↓
AS-000 Language Specification         ← vocabulário canônico
   ↓
ASM-001 Specification Meta Model      ← estrutura dos Standards
   ↓
AS-001..006                            ← vocabulário clínico específico
   ↓
Implementação (código + testes)
```

A ordem reflete **dependência**: AS-000 fixa o vocabulário;
ASM-001 fixa como escrever Standards que usam esse vocabulário;
AS-001..006 são Standards concretos.

## Catálogo

| ID | Título | Posição | Status |
|---|---|---|---|
| **ASM-001** | Specification Meta Model v1.0 | acima de AS-001..006 | **Draft** (2026-07-17) |

## Diretrizes para Escrita de uma Meta Specification

1. **Não redefine vocabulário** — referencie AS-000 §3 sempre que
   precisar de termo canônico.
2. **Não introduz conceitos clínicos** — domínio é responsabilidade
   dos AS específicos.
3. **É auto-aplicável** — toda ASM SHALL ser escrita conforme a
   estrutura que ela mesma prescreve.
4. **É autoridade estrutural** — após aceitação, nenhum AS pode
   descumprir a estrutura fixada pela ASM-001.

## Localização

- Canônica: `docs/meta/ASM-XXX-titulo.md`
- Library: `docs/library/meta/ASM-XXX-titulo-vY.Z.md` + `.html`
