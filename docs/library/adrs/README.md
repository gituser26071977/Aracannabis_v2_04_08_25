# AraOS Library — Architectural Decision Records (ADRs)

Catálogo de **ADRs** publicadas oficialmente.

Cada ADR é publicada em três formatos:

- **Markdown** (`.md`) — fonte canônica editável.
- **HTML** (`.html`) — renderizado com stylesheet AraOS.
- **PDF** (`.pdf.txt`) — versão texto-plano extraída.

## Hierarquia

```
Constituição → Manifesto → Papers → ADRs → ASM → AS → Implementação
```

ADRs ocupam o **Nível 4** da hierarquia normativa (ver ADR-0006 §3).

## Catálogo Atual

| ID | Título | Status | MD | HTML |
|---|---|---|---|---|
| [ADR-0001](../adrs/../../adr/0001-clinical-event-engine.md) | Clinical Event Engine — Event Sourcing + CQRS | Accepted | — | — |
| ADR-0002 | Clinical Identity — Neurodevelopmental Registry | Accepted | — | — |
| ADR-0003 | Clinical Context Engine | Accepted | — | — |
| ADR-0004 | Outcome Evolution Engine | Accepted | — | — |
| ADR-0005 | Clinical Genome Engine | Accepted | — | — |
| **[ADR-0006](REDACTED.0.md)** | **Normative Conflict Resolution and Governance** | **Proposto (2026-07-18)** | ✅ | ✅ |

> ADR-0001..0005 ainda não foram republicadas na Library no formato
> canônico; apenas ADR-0006 segue o pipeline oficial atual.

## ADR-0006 — Normative Conflict Resolution and Governance

Encerramento definitivo da infraestrutura normativa:

- Define **9 níveis de hierarquia normativa** (Constituição → Application Code).
- Estabelece **matriz de precedência** com **30 entradas** (M1–M30) cobrindo todos os pares de conflito.
- Normatiza **resolução de 7 tipos de ambiguidade** (A1–A7).
- Declara **Foundation Freeze** da infraestrutura normativa (AS-000, ASM-001, Maturity Model, etc.).
- Define **6 papéis formais** (Architecture Board, Editorial Committee, etc.).
- Estabelece processo de **Foundation Thaw** para emergências.

Após aceitação, conflitos futuros serão resolvidos **objetivamente**.

## Próximas Publicações

| ADR | Título | Quando |
|---|---|---|
| ADR-0007+ | Domain-specific (clínico) | Conforme demanda de Sprints |

## Estrutura

```
docs/library/adrs/
├── README.md                                       # este arquivo
└── ADR-XXXX-titulo-vY.Z.{md,html,pdf.txt}
```
