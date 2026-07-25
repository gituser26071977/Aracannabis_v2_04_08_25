# AraOS Notes (AN-XXX)

> **Coleção de Notas Técnicas do AraOS**
> **Data:** 2026-07-17
> **Status:** Estrutura inaugural. Sem conteúdo publicado ainda.

## Propósito Editorial

**AraOS Notes (AN)** registram **racional técnico e decisões de
engenharia** que:

- **Não pertencem aos Papers** — Papers tratam de teoria
  original; Notas tratam de observações técnicas.
- **Não pertencem aos Standards (AS)** — Standards são
  documentos normativos; Notas são reflexões justificativas.
- **Não pertencem aos ADRs** — ADRs registram decisões
  arquiteturais; Notas exploram alternativas consideradas ou
  lições aprendidas pós-decisão.

Em suma: **AN é a coleção "entre bastidores"** do AraOS — onde o
processo de pensamento é registrado para futura referência.

## Tipos de Conteúdo Aceitos

| Tipo | Descrição |
|---|---|
| **Notas de Design** | Por que determinada escolha foi feita, alternativas avaliadas. |
| **Pós-Mortem** | Análise de incidentes, falhas de premissas, ajustes de rota. |
| **Benchmarks** | Medições de performance, comparativos de implementação. |
| **Trade-offs** | Análise comparativa entre abordagens. |
| **Padrões Emergentes** | Convenções identificadas no uso prático que ainda não são norma. |
| **Notas de Revisão** | Comentários sobre uma versão publicada de Paper, ADR ou AS. |

## Numeração

Notas usam prefixo `AN-{NNN}` — AraOS Note — seguida de slug
descritivo. Exemplos:

- `REDACTED.md`
- `REDACTED.md`
- `REDACTED.md`

## Política de Versionamento

Cada Nota **deve** declarar:

| Campo | Obrigatório |
|---|---|
| Identificador (AN-NNN) | Sim |
| Título | Sim |
| Status (Draft / Review / Published) | Sim |
| Data | Sim |
| Autor | Sim |
| Versão SemVer | Sim |
| Referências (Papers/ADRs/AS relacionadas) | Sim |

## Estado Editorial

Notas **não são normas**. Seu conteúdo é informativo e pode
ser citado, mas **não pode substituir** um Paper, ADR ou AS.

Quando uma observação de uma AN ascender a **decisão
arquitetural**, **deve** ser promovida a ADR.
Quando ascender a **norma de implementação**, **deve** ser
promovida a AraOS Standard (AS).
Quando ascender a **contribuição teórica**, **deve** ser
incorporada ao Paper correspondente.

## Distinção Editorial

| Família | Prefixo | Função | Norma? |
|---|---|---|---|
| Papers | Paper I, II, … | Teoria original | Não (descritivo) |
| ADRs | ADR-NNNN | Decisão arquitetural | Não (registro) |
| AraOS Standards | AS-NNN | Norma de implementação | **Sim** |
| **AraOS Notes** | **AN-NNN** | **Racional técnico** | **Não (reflexão)** |
| Constituição | — | Lei suprema | **Sim** |

## Catálogo Atual

Nenhuma nota publicada. Coleção em estado inaugural.

## Próximos Passos

A critério da AraOS Architecture, podem ser publicadas:

- AN-001 — Análise de Replay Idempotency (1x / 2x / 50x / 100x) — *planejado*
- AN-002 — Pattern Matching entre Clinical Events e Clinical Genes — *planejado*
- AN-003 — Estratégias de Versionamento de Registries clínicos — *planejado*

---

**AraOS Notes — a memória operacional do AraOS.**