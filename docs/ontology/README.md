# Clinical Gene Ontology (CGO)

> **Status:** Estrutura inicial. **Nenhuma implementação nesta Sprint (4.3).**
> Esta pasta é reservada para documentação da futura Clinical Gene
> Ontology — base semântica formal que descreverá cada Clinical Gene,
> suas Clinical Functions, relações hierárquicas, axiomas e mappings
> para ontologias externas (HPO, SNOMED CT, DOID etc.).

---

## Propósito

A Clinical Gene Ontology (CGO) é a camada semântica que conecta o
**Clinical Genome** (modelo computacional) a **ontologias biomédicas
externas** e ao vocabulário clínico compartilhado.

Quando estiver implementada (pós-Sprint 4.3), a CGO permitirá:

- Definir formalmente o que cada `ClinicalGene` representa.
- Mapear `ClinicalFunction` ↔ termos HPO / SNOMED / DOID.
- Inferir relações hierárquicas (e.g., `LANGUAGE` é subclasse de
  `COMMUNICATION`).
- Versionar a ontologia de forma independente do Registry v1.x.
- Dar suporte a Reasoning Engines (Sprint 5+).

---

## Estrutura de Diretórios (reservada)

```
docs/ontology/
├── README.md                   # este arquivo
├── CGO_SPECIFICATION.md        # spec formal (a criar)
├── CGO_REGISTRY_MAPPING.md     # mapping Registry v1.0 ↔ ontologias externas (a criar)
├── CGO_VERSIONING.md           # estratégia de versionamento (a criar)
└── CHANGELOG.md                # mudanças por versão da CGO (a criar)
```

---

## Relação com ADR-0005

- ADR-0005 (Clinical Genome Engine — 1ª Iteração) **fixa** o Registry v1.0
  como vocabulário fechado inicial de Genes.
- A CGO **estende** semanticamente o Registry, sem substituí-lo. O
  Registry permanece a fonte de verdade para `clinical_gene_id`.
- Mudanças no Registry (1.1, 1.2, 2.0) **não** exigem mudança na CGO;
  mudanças na CGO podem coexistir com versões anteriores do Registry
  via `registry_version` carregada em cada Gene.

---

## Fora de Escopo (Sprint 4.3)

Esta estrutura **NÃO será populada nesta Sprint**. Decisão explícita:
estabilizar primeiro o modelo computacional do Gene; introduzir a
camada semântica formal em Sprint posterior, quando a base clínica já
estiver validada.

Nada aqui deve ser interpretado como plano de implementação.