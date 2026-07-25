# AraOS Library — Meta Specifications

Catálogo de **AraOS Meta Specifications (ASM)** publicadas oficialmente.

Cada ASM é publicada em três formatos:

- **Markdown** (`.md`) — fonte canônica editável.
- **HTML** (`.html`) — renderizado com stylesheet AraOS.
- **PDF** (`.pdf.txt`) — versão texto-plano extraída (geração PDF
  completa requer `pdflatex`; não disponível no ambiente atual).

## Hierarquia

```
Constituição → AS-000 → ASM-001 → AS-001..006 → Implementação
```

ASM-001 governa a estrutura; AS-000 governa o vocabulário.

## Catálogo Atual

| ID | Título | URN | Versão | Maturidade | MD | HTML |
|---|---|---|---|---|---|---|
| [ASM-001](REDACTED.0.md) | Specification Meta Model v1.0 | `urn:araos:meta:001:1.0` | 1.0 | Draft | ✅ | ✅ |

## Conformidade da Library com ASM-001

A AraOS Library SHALL ser reformatada progressivamente para seguir
as 16 seções canônicas do ASM-001. O catálogo atual cumpre as
seções mandatórias; ajustes editoriais finais serão aplicados após
ASM-001 atingir estado **Published**.

## Próximas Publicações

| ASM | Título | Planejado para |
|---|---|---|
| ASM-002 | Specification Parser Model | Após ASM-001 atingir Verified |

## Estrutura de uma ASM publicada

```
docs/library/meta/
├── README.md                                       # este arquivo
└── ASM-XXX-titulo-vY.Z.{md,html,pdf.txt}
```
