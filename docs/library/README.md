# AraOS Library

> **Política Editorial — Publicações Oficiais do AraOS**
> **Data:** 2026-07-17
> **Status:** Adotado (atualizado pós-ASM-001)

## Propósito

A **AraOS Library** é o repositório oficial de **publicações** do
AraOS — documentos com identidade editorial, numeração canônica e
múltiplos formatos de distribuição (Markdown, HTML, PDF).

Ela coexiste com a árvore de trabalho técnico:

| Localização | Conteúdo | Função |
|---|---|---|
| `docs/standards/AS-*.md` | Markdown-fonte (working tree) | Edição, versionamento Git, revisão por pares. |
| `docs/library/standards/AS-*.*` | Publicação oficial | Distribuição multi-formato com identidade visual. |
| `docs/meta/ASM-*.md` | Markdown-fonte de Meta Specifications | Estrutura normativa dos Standards. |
| `docs/library/meta/ASM-*.*` | Publicação oficial das Meta Specifications | ASM-001 governa a estrutura da Library. |

A fonte é canônica. A Library é a **publicação derivada**.

## Hierarquia de Documentos

A AraOS Library reconhece **cinco famílias** de documentos, cada
qual com numeração própria:

| Família | Prefixo | Conteúdo | Diretório |
|---|---|---|---|
| **Constituição** | (sem numeração) | Lei suprema do domínio. | `docs/library/constitution/` |
| **Papers** | `Paper I`, `Paper II`, … | Desenvolvimento teórico. | `docs/library/papers/` |
| **ADRs** | `ADR-0001`, `ADR-0002`, … | Decisões arquiteturais. | `docs/library/adrs/` |
| **AraOS Standards** | `AS-001`, `AS-002`, … | Especificações normativas clínicas. | `docs/library/standards/` |
| **AraOS Meta Specifications** | `ASM-001`, … | Estrutura normativa dos Standards. | `docs/library/meta/` |

A ordem reflete a **hierarquia normativa** (Constituição → Papers →
ADRs → ASM → AS).

> **Foundation Freeze declarado por ADR-0006 (2026-07-18).**
> Componentes da infraestrutura normativa (Constituição, AS-000,
> ASM-001, Maturity Model, Library pipeline, Dependency Graph,
> Traceability Chain) estão congelados. Mudanças exigem novo ADR
> + Foundation Thaw. Ver ADR-0006 §9 para detalhes.

## Pipeline de Publicação

Toda publicação oficial segue o pipeline:

```
Fonte Markdown (docs/standards/ ou docs/meta/)
        │
        ├── render_html.py ── HTML temático ─→ docs/library/<family>/ASM|AS-XXX-vY.Z.html
        │                     (com stylesheet AraOS)
        │
        └── publish.py ── PDF tipográfico ─→ docs/library/<family>/ASM|AS-XXX-vY.Z.pdf
                          (com capa, índice, header/footer)
```

O Markdown é o **source-of-truth**. HTML e PDF são **renderizações
oficiais** derivadas.

## Convenção de Nomenclatura

```
AS-{NNN}-{slug}-v{MAJOR}.{MINOR}.{PATCH}.{ext}
ASM-{NNN}-{slug}-v{MAJOR}.{MINOR}.{PATCH}.{ext}
```

Exemplos:

- `AS-001-clinical-gene-v1.0.md`
- `REDACTED.0.html`

A versão SemVer está **no nome do arquivo** para garantir
identificação estável independente do formato.

## Política de Versionamento

A Library publica **uma versão por Status**. Status válidos (declarados
no Header de cada documento conforme ASM-001 §1):

| Status | Visibilidade |
|---|---|
| **Draft** | Working tree; visível mas não publicado na Library. |
| **Accepted** | Norma aprovada; antes da publicação formal. |
| **Published** | Biblioteca pública. Distribuído como arte final. |
| **Superseded** | Substituído por outro documento; ver cabeçalho para link. |
| **Archived** | Retirado sem substituição. |

## Maturity Model

> **Esta seção é o espelho da ASM-001 §21. Qualquer alteração no
> modelo aqui descrito SHALL ser precedida de atualização da
> ASM-001.**

Toda publicação oficial da AraOS Library atravessa um **ciclo de
vida** com **nove estados de maturidade** mutuamente exclusivos,
inspirados no modelo W3C/IETF para padrões técnicos maduros.

### §6.1 Estados de Maturidade e Critérios de Transição

| # | Estado | Critérios de entrada | Significado |
|---|---|---|---|
| 1 | **Draft** | Documento criado em working tree. Estrutura ASM-001 presente. | Redação inicial; nenhuma revisão formal. |
| 2 | **Technical Review** | (a) Estrutura ASM-001 completa. (b) Revisão por par(s) de engenharia solicitada. (c) Requisitos SHALL/MUST identificáveis. | Engenharia revisa: DDD, arquitetura, consistência computacional, viabilidade de teste. |
| 3 | **Scientific Review** | (a) Technical Review aprovada. (b) Coerência epistemológica auditada. (c) Consistência com Constituição validada. | Comitê científico revisa: aderência ao Paper, correção semântica, ausência de regressão conceitual. |
| 4 | **Accepted** | (a) Scientific Review aprovada. (b) Todas as cláusulas SHALL/MUST validadas por argumentos formais ou testes prospectivos. (c) ADR governante referenciado e vigente. | Norma aprovada como contrato. |
| 5 | **Published** | (a) Status Accepted. (b) Renderização em MD + HTML depositada em `docs/library/<family>/`. (c) Identificador persistente (URN) atribuído. | Disponível publicamente como AraOS Standard / Meta Specification. |
| 6 | **Verified** | (a) Status Published. (b) **Conformance Suite** (`tests/conformance/AS-XXX/` ou `ASM-XXX/`) passa em CI. (c) Cobertura mínima ≥ 95% em métricas ASM-001 §16. (d) Traceability Coverage 100%. | A especificação foi **comprovadamente exercitada** por testes de conformidade. Máxima evidência de que o contrato é executável. |
| 7 | **Reference Implementation** | (a) Status Verified. (b) Existe **uma implementação oficialmente reconhecida como exemplar** pelo comitê editorial. (c) Implementação documentada, mantida e citada como canônica. | Existe um **caso exemplar público** que serve de referência para outras implementações. |
| T1 | **Superseded** | (a) Versão substituta atinge Verified. (b) Cabeçalho da substituta referencia a anterior. (c) URN da anterior torna-se *redirect* explícito. | Substituída por nova versão; mantida para histórico. |
| T2 | **Archived** | (a) Versão substituída e fora do ciclo de citações. (b) **24 meses** desde Superseded **OU** decisão do AraOS Architecture Board. | Retirada sem substituto. |

### §6.2 Diagrama de Maturidade (9 estados)

```
       ┌─────────┐
       │  Draft  │
       └────┬────┘
            │ §6.1.2 (engenharia)
            ▼
   ┌──────────────────┐
   │ Technical Review │
   └────────┬─────────┘
            │ §6.1.3 (epistemologia + clínica)
            ▼
   ┌─────────────────────┐
   │ Scientific Review   │
   └────────┬────────────┘
            │ §6.1.4 (norma aprovada)
            ▼
       ┌──────────┐
       │ Accepted │
       └────┬─────┘
            │ §6.1.5 (publicação na Library)
            ▼
       ┌───────────┐
       │ Published │
       └─────┬─────┘
             │ §6.1.6 (Conformance Suite passing)
             ▼
        ┌──────────┐
        │ Verified │  ← comprovado por testes
        └─────┬────┘
              │ §6.1.7 (implementação exemplar reconhecida)
              ▼
   ┌──────────────────────┐
   │ Reference            │
   │ Implementation       │  ← caso exemplar público
   └──────────────────────┘

   Estados terminais (não-lineares):
   Superseded ─── Archived
```

### §6.3 Distinção crítica

| | Verified | Reference Implementation |
|---|---|---|
| **O que comprova** | A especificação é executável e testável. | Uma implementação é canônica para o domínio. |
| **Requisito** | Conformance Suite passa. | Comitê editorial reconhece implementação exemplar. |
| **Quando ocorre** | Após Published. | Após Verified. |
| **Quem decide** | CI (automatizado). | Comitê editorial. |

**Ordem obrigatória:** `Published → Verified → Reference Implementation`. Verified SHALL sempre anteceder Reference Implementation.

### §6.4 Obrigações por Estado

- **6.4.1** — Toda publicação **shall** declarar seu estado atual
  de forma explícita e verificável no cabeçalho.
- **6.4.2** — Uma publicação só **may** avançar para Scientific
  Review se a Technical Review estiver aprovada.
- **6.4.3** — Uma publicação só **may** avançar para Accepted se
  nenhuma cláusula SHALL/MUST estiver sem validação.
- **6.4.4** — Uma publicação só **may** ser declarada Verified se
  a Conformance Suite estiver 100% verde em CI.
- **6.4.5** — Uma publicação só **may** ser declarada Reference
  Implementation se já estiver Verified.
- **6.4.6** — Toda transição **shall** ser registrada em changelog
  (Apêndice de Histórico de Versões do documento).
- **6.4.7** — Transições para Superseded ou Archived **shall**
  manter a URL/URN da versão anterior como *redirect* permanente.

### §6.5 Estados Atuais (2026-07-17)

#### AS-001 — Clinical Gene Standard v1.0

| Campo | Valor |
|---|---|
| Estado | **Published** (correção aplicada após ASM-001 §21) |
| Razão da reclassificação | O 9-estado modelo exige que Verified venha antes de Reference Implementation, e Verified requer Conformance Suite passando — não apenas existência de testes de unidade. |
| Status mantido | Implementação concreta existe (`araos/clinical/genome/`, 88 testes, 98% coverage) mas **Conformance Suite formal** ainda não publicada em `tests/conformance/AS-001/`. |
| Data de Draft | 2026-07-17 |
| Data de Published | 2026-07-17 |
| Identificador persistente | `urn:araos:standard:001:1.0` |
| Próxima transição | Draft → Verified após publicação da Conformance Suite AS-001. |

#### AS-000 — AraOS Language Specification v1.0

| Campo | Valor |
|---|---|
| Estado | **Draft** |
| Data de Draft | 2026-07-17 |
| Identificador persistente | `urn:araos:standard:000:1.0` |

> **Próxima transição prevista para AS-000:** Draft → Technical
> Review assim que o AS-002 for Aceito, garantindo que a
> gramática tenha sido exercitada por pelo menos um Standard
> derivado além do próprio AS-001.

#### AS-002 — Clinical Expression Standard v1.0

| Campo | Valor |
|---|---|
| Estado | **Draft** |
| Data de Draft | 2026-07-17 |
| Identificador persistente | `urn:araos:standard:002:1.0` |

> **Próxima transição prevista para AS-002:** Draft → Technical
> Review após revisão por pares de engenharia. → Scientific
> Review após validação epistemológica. → Accepted → Published →
> Verified após Conformance Suite passando → Reference
> Implementation após Sprint 4.3 Phase 2.

#### ASM-001 — AraOS Specification Meta Model v1.0

| Campo | Valor |
|---|---|
| Estado | **Draft** |
| Data de Draft | 2026-07-17 |
| Identificador persistente | `urn:araos:meta:001:1.0` |
| Posição | Acima de AS-001..006; abaixo de AS-000. Governa estrutura. |

> **Próxima transição prevista para ASM-001:** Draft → Technical
> Review após a estrutura ser aplicada a AS-001/AS-002 (formatação
> conforme as 16 seções canônicas). → Published → Verified após
> Conformance Suite ASM-001 passar.

## Identidade Visual

A AraOS Library possui:

- **Logo AraOS** (a definir; reserva de espaço)
- **Paleta cromática institucional** (a definir)
- **Stylesheet comum** em `docs/library/stylesheets/araos.css`
  aplicado em todas as versões HTML.

## Comandos de Publicação

```bash
# Renderizar HTML (sem dependência pandoc)
python3 docs/library/render_html.py \
  docs/standards/AS-001-clinical-gene.md \
  docs/library/standards/AS-001-clinical-gene-v1.0.html

# Para Meta Specifications
python3 docs/library/render_html.py \
  docs/meta/ASM-001-specification-meta-model.md \
  docs/library/meta/REDACTED.0.html
```

## Catálogo Atual

| ID | Título | Versão | Estado | Formatos |
|---|---|---|---|---|
| ADR-0006 | Normative Conflict Resolution and Governance | v1.0 | Proposto | MD · HTML |
| ASM-001 | Specification Meta Model | v1.0 | Draft | MD · HTML |
| AS-000 | AraOS Language Specification | v1.0 | Draft | MD · HTML |
| AS-001 | Clinical Gene Standard | v1.0 | Published | MD · HTML |
| AS-002 | Clinical Expression Standard | v1.0 | Draft | MD · HTML |

## Catálogo Planejado

| ID | Título | Previsão |
|---|---|---|
| AS-003 | Clinical Genome Standard | pós-implementação de AS-001 + AS-002 |
| AS-004 | Clinical Inference Standard | Sprint 4.4 |
| AS-005 | Clinical Interpretation Standard | pós-Sprint 4.4 |
| AS-006 | Clinical Context Standard | paralelo ao AS-002 |
| ASM-002 | Specification Parser Model | Após ASM-001 atingir Verified |

---

**Documento fundacional da AraOS Library.**
**Próxima revisão:** quando AS-002 for Accepted.
