# ASM-001 — AraOS Specification Meta Model v1.0

> **URN:** `urn:araos:meta:001:1.0`
> **Categoria:** Meta-normative Specification
> **Status editorial:** Draft (2026-07-17)
> **Maturidade:** Draft
> **Versão:** 1.0
> **Posição hierárquica:** acima de AS-001..006; abaixo de AS-000 Language Specification
> **Idiomas:** PT-BR (canônico) / EN (derivado, quando aplicável)

---

## §1 — Header

### 1.1 Objetivo da seção
Identificar univocamente o documento e expor seus metadados canônicos para indexação e consumo automatizado.

### 1.2 Obrigatoriedade
**MANDATÓRIO.** Todo AraOS Standard **SHALL** possuir um Header com todos os campos especificados em §10 (Requisitos Normativos).

### 1.3 Regras de escrita
- O Header é a **primeira** seção do documento.
- Cada campo aparece em sua própria linha.
- O **URN** SHALL seguir o esquema `urn:araos:<categoria>:<número>:<versão>`.
- A **Maturidade** SHALL ser um dos 9 estados definidos em §11.

### 1.4 Dependências
Nenhuma (auto-contida).

### 1.5 Restrições
- Nenhum campo SHALL ser inferido por leitores.
- A versão SHALL seguir SemVer (`MAJOR.MINOR.PATCH`).

---

## §2 — Normative Sources

### 2.1 Objetivo
Declarar formalmente a origem teórica e decisória do Standard.

### 2.2 Obrigatoriedade
**MANDATÓRIO.**

### 2.3 Regras de escrita
- Listar em ordem hierárquica: Constituição → Papers → ADRs.
- Cada fonte SHALL ser referenciada por nome e versão quando aplicável.
- A ausência de um Paper SHALL ser justificada explicitamente.

### 2.4 Dependências
Nenhuma.

### 2.5 Restrições
Esta seção **SHALL NOT** introduzir conceitos novos; apenas referenciar fontes externas ao Standard.

---

## §3 — Design Goals

### 3.1 Objetivo
Declarar os **objetivos** que motivaram a redação do Standard.

### 3.2 Obrigatoriedade
**MANDATÓRIO.**

### 3.3 Regras de escrita
- Goals SHALL ser enunciados com verbos no infinitivo.
- Cada Goal SHALL ser testável por presença/ausência.
- Goals SHALL ser ordenados por prioridade quando hierárquicos.

### 3.4 Dependências
Nenhuma.

### 3.5 Restrições
- Goals SHALL NOT descrever **como** atingir o objetivo (isso é responsabilidade da seção §10).
- Goals SHALL NOT contradizer Non Goals (§4).

---

## §4 — Non Goals

### 4.1 Objetivo
Declarar explicitamente o que está **fora do escopo** do Standard, prevenindo interpretações extensivas indevidas.

### 4.2 Obrigatoriedade
**MANDATÓRIO.**

### 4.3 Regras de escrita
- Cada Non Goal SHALL ser redigido como uma negação explícita do que **não** é objetivo.
- Non Goals SHOULD ser redigidos em par com um Design Goal correspondente.

### 4.4 Dependências
Nenhuma.

### 4.5 Restrições
Non Goals SHALL NOT ser usados como mecanismo de exclusão para逃避 análise crítica.

---

## §5 — Scope

### 5.1 Objetivo
Definir a fronteira exata do que o Standard governa.

### 5.2 Obrigatoriedade
**MANDATÓRIO.**

### 5.3 Regras de escrita
- Scope SHALL ser redigido em prosa contínua, sem listas.
- Scope SHALL responder: "o que está dentro" e "o que está fora".

### 5.4 Dependências
Referencia §3 e §4.

### 5.5 Restrições
Scope SHALL NOT duplicar Design Goals ou Non Goals.

---

## §6 — Normative References

### 6.1 Objetivo
Listar documentos externos (normas técnicas, RFCs, papers) referenciados como autoridade.

### 6.2 Obrigatoriedade
**MANDATÓRIO** quando o Standard referenciar normas externas; caso contrário, **OPCIONAL** com menção "Nenhuma".

### 6.3 Regras de escrita
- Cada referência SHALL incluir identificador, título e data de publicação.
- Referências SHALL ser listadas em ordem alfabética por identificador.

### 6.4 Dependências
Nenhuma.

### 6.5 Restrições
Esta seção SHALL NOT incluir Standards AraOS internos (esses aparecem em §7 — Terms and Definitions como cross-references).

---

## §7 — Terms and Definitions

### 7.1 Objetivo
Definir cada termo canônico usado pelo Standard, em alinhamento com AS-000 §3.

### 7.2 Obrigatoriedade
**MANDATÓRIO.**

### 7.3 Regras de escrita
- Cada termo SHALL ser definido usando exatamente **9 propriedades**: Definição, Motivação, Responsabilidades, Invariantes, Exemplos, Contraexemplos, Relação, Consequência para implementação, Referências cruzadas.
- Termos SHALL ser ordenados alfabeticamente.
- Termos já definidos em AS-000 SHALL ser referenciados por seção (`AS-000 §3.X`) e **não redefinidos**.

### 7.4 Dependências
Depende de AS-000 §3 (vocabulário canônico).

### 7.5 Restrições
Esta seção SHALL NOT redefinir termos canônicos do AS-000.

---

## §8 — Invariants

### 8.1 Objetivo
Declarar propriedades que **devem sempre ser verdadeiras** durante toda a vida do objeto definido.

### 8.2 Obrigatoriedade
**MANDATÓRIO.**

### 8.3 Regras de escrita
- Cada invariante SHALL ser identificável univocamente (`§8.N.M`).
- Invariantes SHALL ser redigidas em forma declarativa, sem verbo normativo (são fatos, não requisitos).
- Invariantes SHALL ser verificáveis em tempo constante (O(1)) sempre que possível.

### 8.4 Dependências
Construídas sobre §7.

### 8.5 Restrições
Invariantes SHALL NOT depender de estado externo mutável.

---

## §9 — Formal Axioms

### 9.1 Objetivo
Capturar princípios formais do Standard em axiomas verificáveis.

### 9.2 Obrigatoriedade
**MANDATÓRIO.**

### 9.3 Regras de escrita
- Cada axioma SHALL ser identificável (`Axiom N`).
- Cada axioma SHALL ser redigido como uma implicação ou equivalência lógica.
- Axiomas SHOULD ser demonstráveis a partir de propriedades mais fundamentais.
- Axiomas SHALL ser enumerados em ordem lógica (axiomas básicos primeiro).

### 9.4 Dependências
Construídas sobre §7 e §8.

### 9.5 Restrições
- Axiomas SHALL NOT contradizer axiomas do AS-000.
- Axiomas SHALL ser em número mínimo necessário (não proliferar axiomas triviais).

---

## §10 — Normative Requirements (SHALL)

### 10.1 Objetivo
Listar **todos** os requisitos normativos do Standard, cada um identificável, testável e rastreável.

### 10.2 Obrigatoriedade
**MANDATÓRIO.** Esta é a seção central do Standard.

### 10.3 Regras de escrita
- Cada requisito SHALL possuir exatamente os campos definidos em §10.3.1–10.3.10 abaixo.
- Requisitos SHALL ser identificados pelo formato `AS-XXX-REQ-NNNN` (Requirement ID canônico).
- Requisitos SHOULD ser agrupados em subseções por invariante ou axioma relacionado.
- O verbo SHALL ser um dos definidos em §12.

#### 10.3.1 Requirement ID
- Formato: `AS-XXX-REQ-NNNN` onde `XXX` é o número do Standard e `NNNN` é sequência zero-padded.
- SHALL ser único dentro do Standard.
- SHALL ser estável (não reutilizado após deprecation).

#### 10.3.2 Section
- Referência à seção do Standard que contém o requisito (ex: `§4.2.1`).

#### 10.3.3 Text
- Texto do requisito em prosa declarativa, começando com o verbo normativo.
- SHALL ser auto-contido (não depender de contexto fora do Standard).

#### 10.3.4 Normative Verb
- SHALL ser um de: `SHALL`, `SHALL NOT`, `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, `MAY`.

#### 10.3.5 Rationale
- Justificativa da existência do requisito.
- SHOULD referenciar o axioma ou invariante que origina o requisito.

#### 10.3.6 References
- Lista de IDs de outros requisitos, axiomas, ADRs ou Papers relacionados.

#### 10.3.7 Conformance Test
- Referência ao teste de conformidade (path relativo ou nome simbólico).
- SHALL ser verificável em CI.

#### 10.3.8 Status
- Valores possíveis: `active`, `deprecated`, `superseded`.
- Default: `active`.

#### 10.3.9 Version Introduced
- Versão SemVer na qual o requisito foi introduzido.

#### 10.3.10 Version Deprecated (opcional)
- Versão SemVer na qual o requisito foi marcado como deprecated.
- Quando preenchido, SHALL também referenciar o requisito que o substituiu.

### 10.4 Dependências
Nenhuma (auto-contida).

### 10.5 Restrições
- Nenhum requisito SHALL ser adicionado sem Requirement ID.
- Requisitos `deprecated` SHALL NOT ser removidos antes da versão `superseded`.

---

## §11 — Computational Model

### 11.1 Objetivo
Descrever a estrutura de dados computável que materializa o Standard.

### 11.2 Obrigatoriedade
**MANDATÓRIO.**

### 11.3 Regras de escrita
- O modelo SHALL ser descrito em termos de entidades, value objects, eventos e operações.
- O modelo SHALL usar exclusivamente tipos DDD definidos em AS-000 §5.
- Diagramas (Mermaid, UML) SHOULD acompanhar a descrição textual.
- O modelo SHALL ser **independente de implementação** (sem código de produção).

### 11.4 Dependências
Construída sobre §7.

### 11.5 Restrições
- Nenhuma linguagem de programação SHALL ser imposta.
- O modelo SHALL ser serializável (ver §17 — Machine Readability).

---

## §12 — Normative Verbs

### 12.1 Definição canônica (RFC 2119 + ISO/IEC Directives Part 2)

| Verbo | Significado | Quando usar |
|---|---|---|
| **SHALL** | Requisito absoluto. Conformidade impossível sem cumprimento. | Obrigação não-negociável da qual dependem outras propriedades. |
| **SHALL NOT** | Proibição absoluta. | Vedação cuja violação quebra o invariante. |
| **MUST** | Sinônimo de SHALL. | Quando citação literal de norma externa usa MUST. |
| **MUST NOT** | Sinônimo de SHALL NOT. | Quando citação literal de norma externa usa MUST NOT. |
| **SHOULD** | Recomendação forte; pode haver razão válida para não cumprir, mas implicações devem ser compreendidas. | Práticas recomendadas cuja omissão degrada qualidade mas não quebra invariantes. |
| **SHOULD NOT** | Vedação recomendada. | Práticas desencorajadas mas toleráveis em contextos específicos. |
| **MAY** | Permissão explícita; opcional. | Comportamentos opcionais que melhoram o sistema mas não são exigidos. |

### 12.2 Regras de uso
- Todo uso de verbo SHALL estar em **maiúsculas**.
- Em texto corrido, verbos SHOULD ser capitalizados para destaque.
- Mistura de `SHALL` e `MUST` no mesmo Standard SHOULD ser evitada (preferir um único conjunto).
- Verbos em minúsculas (`shall`, `must`) SHALL ser interpretados como texto descritivo, não como requisito.

---

## §13 — DDD Mapping

### 13.1 Objetivo
Mapear cada conceito do Standard a uma categoria DDD canônica do AS-000 §5.

### 13.2 Obrigatoriedade
**MANDATÓRIO.**

### 13.3 Regras de escrita
- Tabela canônica: `Conceito | Tipo DDD`.
- Conceitos SHALL ser mapeados para exatamente uma categoria.
- A categoria SHALL estar entre as definidas em AS-000 §5.

### 13.4 Dependências
Depende de AS-000 §5.

### 13.5 Restrições
Conceitos SHALL NOT ser mapeados para múltiplas categorias simultaneamente.

---

## §14 — Canonical Examples

### 14.1 Objetivo
Ilustrar, por meio de exemplos canônicos, a aplicação dos requisitos.

### 14.2 Obrigatoriedade
**OBRIGATÓRIO** para conceitos centrais; **OPCIONAL** para periféricos.

### 14.3 Regras de escrita
- Cada exemplo SHALL demonstrar **conformidade positiva** com pelo menos um requisito.
- Exemplos SHOULD incluir dados realistas (não `foo`/`bar`).
- Exemplos SHALL ser identificados (`Exemplo N: título`).
- Contraexemplos (demonstrações de violação) SHOULD ser incluídos quando o requisito for sutil.

### 14.4 Dependências
Construída sobre §10.

### 14.5 Restrições
Exemplos SHALL NOT substituir a especificação formal (não são fonte primária).

---

## §15 — Compliance Levels

### 15.1 Objetivo
Definir níveis graduais de conformidade para que diferentes implementações possam declarar perfis de aderência.

### 15.2 Obrigatoriedade
**MANDATÓRIO.**

### 15.3 Regras de escrita
- Níveis SHALL ser cumulativos (N+1 inclui todos os requisitos de N).
- Cada nível SHALL ter nome, requisitos cobertos e critérios de promoção.
- SHOULD existir entre 2 e 4 níveis.

### 15.4 Dependências
Construída sobre §10.

### 15.5 Restrições
Níveis SHALL NOT ser incompatíveis entre si (uma implementação nível N+1 SHALL também passar no nível N).

---

## §16 — Conformance Requirements

### 16.1 Objetivo
Especificar métricas e critérios de cobertura que a Conformance Suite SHALL atingir.

### 16.2 Obrigatoriedade
**MANDATÓRIO.**

### 16.3 Regras de escrita
- Métricas SHALL ser quantificáveis (threshold numérico).
- Métricas SHOULD incluir:

| Métrica | Definição | Threshold mínimo |
|---|---|---|
| **Requirement Coverage** | % de requisitos SHALL com teste de conformidade. | 100% |
| **Axiom Coverage** | % de axiomas com teste. | 100% |
| **Vocabulary Coverage** | % de termos canônicos usados e testados. | 100% |
| **DDD Coverage** | % de conceitos com teste de tipo DDD. | 100% |
| **Behavior Coverage** | % de comportamentos especificados testados. | ≥ 95% |
| **Temporal Coverage** | % de invariantes temporais testados. | 100% |
| **Replay Coverage** | % de projections testadas para replay bit-identical. | 100% (quando aplicável) |
| **Explainability Coverage** | % de análises com Explanation testadas. | 100% (quando aplicável) |
| **Traceability Coverage** | % de requisitos com cadeia de rastreabilidade completa. | 100% |

### 16.4 Dependências
Construída sobre §10.

### 16.5 Restrições
Nenhuma métrica SHALL ser declarada sem threshold mensurável.

---

## §17 — Machine Readability

### 17.1 Objetivo
Definir o **modelo conceitual** para exportação automática do Standard em formatos estruturados (JSON, YAML).

### 17.2 Obrigatoriedade
**MANDATÓRIO para o modelo conceitual.** Implementação de parser é OPCIONAL e fora do escopo do ASM-001 v1.0.

### 17.3 Modelo conceitual (Requirement serializado)

```json
{
  "id": "AS-002-REQ-0046",
  "section": "§4.3.1",
  "verb": "SHALL",
  "text": "Explanation Reference shall never be empty.",
  "rationale": "Axiom 6 (explainability) requires that every Expression carries a justified Explanation; absence of the reference would break the audit chain.",
  "references": [
    "AS-000-AXIOM-006",
    "AS-000-§3.16"
  ],
  "tests": [
    "tests/conformance/AS-002/test_explainability.py::REDACTED"
  ],
  "status": "active",
  "version_introduced": "1.0",
  "version_deprecated": null,
  "supersedes": null,
  "superseded_by": null
}
```

### 17.4 Modelo conceitual (Standard serializado)

```json
{
  "id": "AS-002",
  "urn": "urn:araos:standard:002:1.0",
  "title": "Clinical Expression v1.0",
  "category": "clinical",
  "maturity": "draft",
  "version": "1.0",
  "parent": "AS-001",
  "sections": ["§1", "§2", "§3", "§4", "§5", "§6", "§7", "§8", "§9", "§10", "§11", "§12", "§13", "§14", "§15", "§16", "§17"],
  "requirements": ["AS-002-REQ-0001", "AS-002-REQ-0046", "..."],
  "axioms": ["AS-002-AXIOM-001", "..."],
  "vocabulary": ["clinical_expression", "expression_state", "..."],
  "ddd_mapping": {
    "clinical_expression": "value_object",
    "clinical_gene": "aggregate_root"
  },
  "conformance_metrics": {
    "requirement_coverage_target": 1.0,
    "axiom_coverage_target": 1.0,
    "vocabulary_coverage_target": 1.0
  },
  "normative_sources": {
    "papers": ["Paper IV"],
    "adrs": ["ADR-0005"]
  }
}
```

### 17.5 Restrições
- O modelo SHALL ser serializável em JSON (obrigatório) e SHOULD em YAML (opcional).
- Nenhum campo SHALL ser obrigatório além dos especificados em §10.3.
- Implementação de parser SHALL ser responsabilidade de outro Standard (ASM-002 ou sucessor).

---

## §18 — Appendices

### 18.1 Objetivo
Anexar material de referência que **não pertence** ao corpo normativo.

### 18.2 Obrigatoriedade
**OPCIONAL.**

### 18.3 Regras de escrita
- Apêndices SHALL ser identificados por letra (`Apêndice A`, `Apêndice B`...).
- Apêndices SHALL ser marcados como `informative` ou `normative` (default: informative).
- Apêndices normativos SHALL ter seus próprios requisitos rastreáveis.

### 18.4 Dependências
Variável por apêndice.

### 18.5 Restrições
Apêndices SHALL NOT contradizer requisitos do corpo normativo.

---

## §19 — Version History

### 19.1 Objetivo
Registrar todas as mudanças publicadas do Standard.

### 19.2 Obrigatoriedade
**MANDATÓRIO.**

### 19.3 Regras de escrita
Tabela canônica: `Versão | Data | Status | Mudanças | Autor`.

### 19.4 Dependências
Nenhuma.

### 19.5 Restrições
Versões SHALL seguir SemVer (ver §20 — Change Control).

---

## §20 — Change Control

### 20.1 SemVer

| Componente | Incremento quando | Compatibilidade |
|---|---|---|
| **MAJOR** | Mudança incompatível. | Quebra. |
| **MINOR** | Adição retrocompatível. | Preservada. |
| **PATCH** | Correção ou clarificação. | Preservada. |

### 20.2 Deprecation
- Um requisito MAY ser marcado como `deprecated`.
- Deprecation SHALL indicar versão de remoção prevista.
- Requisitos deprecated SHALL continuar sendo testados até a remoção.

### 20.3 Replacement
- Um Standard MAY ser substituído por outro via `Replacement`.
- O Standard substituinte SHALL indicar `supersedes: <ID>`.
- O Standard substituído SHALL indicar `superseded_by: <ID>`.

### 20.4 Superseded
- Estado terminal do Maturity Model (§21).
- Indica que o Standard foi **oficialmente substituído** por outro.
- O Standard superseded SHALL permanecer na Library para referência histórica.

### 20.5 Backward Compatibility
- Adições retrocompatíveis (novos requisitos opcionais, novos exemplos) MAY ser feitas em MINOR.
- Mudanças em requisitos existentes SHALL exigir MAJOR.

### 20.6 Forward Compatibility
- Implementações MAY antecipar features de versões futuras.
- O Standard SHOULD declarar features experimentais claramente.

---

## §21 — Maturity Model

### 21.1 Definição dos 9 estados

```
Draft → Technical Review → Scientific Review → Accepted →
Published → Verified → Reference Implementation →
Superseded (terminal) / Archived (terminal)
```

### 21.2 Critérios de promoção

| Estado | Critério de saída |
|---|---|
| **Draft** | Documento editado; aberto para mudanças editoriais. |
| **Technical Review** | Revisão por pares de engenharia (DDD, arquitetura, consistência computacional) aprovada. |
| **Scientific Review** | Revisão por pares de pesquisa (correção, completude, alinhamento com Papers) aprovada. |
| **Accepted** | Comitê aprova como normativa; congelamento editorial. |
| **Published** | Disponível na AraOS Library com URN persistente e versão SemVer. |
| **Verified** | Conformance Suite passa em CI com cobertura mínima. |
| **Reference Implementation** | Uma implementação **oficialmente reconhecida como exemplar** existe, documentada e mantida. |
| **Superseded** | Substituído por outro Standard via Replacement. |
| **Archived** | Retirado sem substituição (descontinuação explícita). |

### 21.3 Distinção crítica

| | Verified | Reference Implementation |
|---|---|---|
| **O que comprova** | A especificação é executável e testável. | Uma implementação é canônica para o domínio. |
| **Requisito** | Conformance Suite passa. | Implementação reconhecida pelo comitê como exemplar. |
| **Quando ocorre** | Após Published. | Após Verified. |
| **Quem decide** | CI (automatizado). | Comitê editorial. |

### 21.4 Ordem obrigatória

A ordem correta de promoção após Published é:

```
Published → Verified → Reference Implementation
```

Um Standard SHALL NOT saltar `Verified` (a conformidade deve ser comprovada antes de reconhecer uma implementação exemplar).

---

## §22 — Dependency Graph

### 22.1 Regra fundamental

> Um Standard `S_X` MAY depender de um Standard `S_Y` se, e somente se, `S_Y` precede `S_X` na ordem canônica AS-000 < AS-001 < AS-002 < ...

### 22.2 Dependências permitidas (exemplos)

| Origem | → | Destino | Permitido? |
|---|---|---|---|
| AS-002 | → | AS-001 | ✅ |
| AS-002 | → | AS-000 | ✅ |
| AS-001 | → | AS-000 | ✅ |
| AS-000 | → | Constituição | ✅ |
| **AS-000** | → | **AS-001** | **❌ (proibido)** |
| **AS-001** | → | **AS-002** | **❌ (proibido)** |
| AS-X | → | AS-X | ❌ (auto-referência proibida exceto para versionamento) |

### 22.3 Proibições

- **Dependência ascendente**: Standard inferior SHALL NOT depender de Standard superior.
- **Dependência circular**: ciclos `S_A → S_B → S_A` SHALL NOT existir.
- **Dependência lateral**: AS-001 SHALL NOT depender de AS-002 (mesmo que "independentes").
- **Auto-referência**: SHALL NOT existir exceto para referências versionais explícitas.

### 22.4 Verificação

O grafo de dependências SHALL ser verificável por inspeção dos Requirements → References em cada Standard publicado.

---

## §23 — Traceability Chain

### 23.1 Cadeia canônica

```
Constituição
   ↓
Paper
   ↓
ADR
   ↓
AS (Standard)
   ↓
Requirement (REQ-NNNN)
   ↓
Conformance Test
   ↓
Implementation
   ↓
Evidence (test execution, deployment, audit log)
```

### 23.2 Regras

- Cada elemento SHALL ser identificável univocamente.
- Cada elemento SHALL referenciar seu predecessor imediato.
- A cadeia SHALL ser navegável em ambas as direções (forward e backward).
- Nenhum elemento SHALL quebrar a cadeia (todo Requirement SHALL ter pelo menos um Conformance Test).

### 23.3 Métrica de cobertura

A métrica `Traceability Coverage` (§16.3) SHALL medir a fração de Requirements com cadeia completa até Evidence. Target: 100%.

---

## §24 — Meta-Model Formal

### 24.1 Elementos do meta-modelo

| Elemento | Definição | Tipo DDD |
|---|---|---|
| **Standard** | Documento normativo completo. Identificável por URN. | Aggregate Root |
| **Section** | Subdivisão estruturada do Standard. Numerada (e.g., `§4.2.1`). | Entity |
| **Requirement** | Cláusula normativa individual com Requirement ID. | Entity |
| **Constraint** | Restrição técnica ou formal que limita o Requirement. | Value Object |
| **Example** | Ilustração canônica de conformidade ou violação. | Value Object |
| **Reference** | Apontamento para fonte externa ou interna (Paper, ADR, Standard). | Value Object |
| **Artifact** | Materialização física do Standard (MD, HTML, PDF, JSON serializado). | Entity |

### 24.2 Relacionamentos

```
Standard (AR)
  ├─ contains → Section (1..*)
  ├─ contains → Requirement (1..*)
  ├─ contains → Example (0..*)
  ├─ references → Reference (1..*)
  └─ produces → Artifact (1..*)

Section
  └─ contains → Requirement (0..*)

Requirement
  ├─ uses → Normative Verb (1..1)
  ├─ references → Reference (0..*)
  ├─ constrained by → Constraint (0..*)
  └─ tested by → Conformance Test (1..*)

Reference
  └─ points to → External/Internal target (1..1)

Artifact
  └─ serializes → Standard/Requirement (1..*)
```

### 24.3 Invariantes do meta-modelo

- **MM-INV-01**: Todo Standard SHALL conter pelo menos um Requirement.
- **MM-INV-02**: Todo Requirement SHALL conter exatamente um Normative Verb.
- **MM-INV-03**: Todo Requirement SHALL ser testável por pelo menos um Conformance Test.
- **MM-INV-04**: Todo Standard SHALL produzir pelo menos um Artifact (MD mínimo).
- **MM-INV-05**: Todo Standard SHALL referenciar pelo menos uma Normative Source.
- **MM-INV-06**: Nenhum Requirement SHALL ter `Version Deprecated` sem `Superseded By` quando marcado como `deprecated`.
- **MM-INV-07**: A soma de Requirements ativos + deprecated SHALL ser igual ao número de Requirements já introduzidos.

---

## §25 — Axiomas Formais

### Axiom 1 — Structure Precedes Content
A estrutura de um Standard precede e governa seu conteúdo. Um Standard sem estrutura canônica não é interpretável.

### Axiom 2 — Requirements are Testable
Todo requisito normativo SHALL ser testável. Requisitos não-testáveis são recomendações, não normas.

### Axiom 3 — Vocabulary is Canonical
Termos usados em Standards SHALL ser do vocabulário do AS-000. Novos termos SHALL ser adicionados via bump do AS-000, não redefinidos localmente.

### Axiom 4 — Dependency is Strictly Downward
Standards SHALL depender apenas de Standards anteriores na ordem canônica. Dependências ascendentes invalidam o Standard.

### Axiom 5 — Maturity is Monotonic
A promoção de maturidade SHALL ser monotônica (não regride). Superseded/Archived são estados terminais.

### Axiom 6 — Conformance Precedes Reference
Verified SHALL anteceder Reference Implementation. Implementação exemplar só pode ser reconhecida após conformidade comprovada.

### Axiom 7 — Traceability is Total
Toda Requirement SHALL ter cadeia de rastreabilidade completa até Evidence. Requirements órfãs são inválidas.

### Axiom 8 — Machine Readability is Mandatory
Todo Requirement SHALL poder ser serializado sem perda semântica em JSON. Texto não-serializável é texto interpretativo, não requisito.

### Axiom 9 — Section Structure is Mandatory
Todo Standard SHALL conter as 16 seções definidas em §1–§17 (ou seção única agregadora se o Standard for minimal).

### Axiom 10 — Backward Compatibility is Default
Mudanças SHALL preservar compatibilidade descendente. Quebras SHALL ser explicitamente marcadas como MAJOR.

---

## §26 — Compliance Levels (do próprio ASM-001)

| Nível | Nome | Requisitos |
|---|---|---|
| **M0** | Document-Structural | §1, §2, §3, §4, §5 — Header, Normative Sources, Design Goals, Non Goals, Scope |
| **M1** | Reference-Complete | M0 + §6, §7 — Normative References, Terms and Definitions |
| **M2** | Semantically-Sound | M1 + §8, §9 — Invariants, Formal Axioms |
| **M3** | Normative | M2 + §10 — Normative Requirements (SHALL) |
| **M4** | Computational | M3 + §11, §13 — Computational Model, DDD Mapping |
| **M5** | Documented | M4 + §14, §15 — Canonical Examples, Compliance Levels |
| **M6** | Verified | M5 + §16 — Conformance Requirements |
| **M7** | Machine-Readable | M6 + §17 — Machine Readability |
| **M8** | Full ASM-001 Compliance | M7 + §18–§26 — Appendices, Version History, Change Control, Maturity, Dependency Graph, Traceability, Meta-Model, Axiomas |

---

## §27 — Computational Model (do ASM-001)

### 27.1 Estrutura de um Standard (esquema)

```
Standard {
  id: URN                        # urn:araos:<categoria>:<num>:1.0
  title: string
  category: enum                 # standard | meta | constitution
  maturity: Maturity             # 9 estados
  version: SemVer
  parent: optional URN           # Standard predecessor
  children: list of URN          # Standards dependentes
  sections: list of Section      # 1..16 mínimo
  requirements: list of REQ      # 1..*
  axioms: list of AXIOM          # 0..*
  vocabulary: list of Term       # todos os termos usados
  ddd_mapping: Dict<Term, DDDType>
  normative_sources: list of Source
  references: list of Reference
  artifacts: list of Artifact    # MD, HTML, PDF, JSON
}

Section {
  number: string                 # §4.2.1
  title: string
  objective: string
  mandatory: bool
  writing_rules: list of Rule
  dependencies: list of SectionRef
  restrictions: list of Rule
}

Requirement {
  id: AS-XXX-REQ-NNNN
  section: SectionRef
  text: string
  verb: NormativeVerb            # SHALL, MUST, SHOULD, MAY
  rationale: string
  references: list of Reference
  conformance_tests: list of TestRef
  status: enum                   # active | deprecated | superseded
  version_introduced: SemVer
  version_deprecated: optional SemVer
  superseded_by: optional REQ_ID
}
```

### 27.2 Operações canônicas

| Operação | Descrição |
|---|---|
| `parse_standard(path)` | Carrega Standard de MD estruturado. |
| `extract_requirements()` | Lista todos os REQ-IDs do Standard. |
| `verify_dependency_graph()` | Confirma que não há ciclos nem upward deps. |
| `check_machine_readability()` | Confirma que cada REQ é serializável em JSON. |
| `compute_traceability_coverage()` | Mede % de REQs com cadeia até Evidence. |
| `validate_maturity_transition(from, to)` | Confirma que transição é permitida. |

---

## §28 — DDD Mapping (do ASM-001)

| Conceito ASM-001 | Tipo DDD |
|---|---|
| Standard | Aggregate Root |
| Section | Entity |
| Requirement | Entity |
| Constraint | Value Object |
| Example | Value Object |
| Reference | Value Object |
| Artifact | Entity |
| Conformance Test | Domain Service |
| Normative Verb | Value Object (enum) |
| Maturity State | Value Object (enum) |
| URN | Value Object |
| SemVer | Value Object |

---

## §29 — Canonical Examples

### 29.1 Exemplo 1: Requirement completo (AS-002-REQ-0046)

```yaml
id: AS-002-REQ-0046
section: §4.3.1
text: "Explanation Reference shall never be empty."
verb: SHALL
rationale: |
  Axiom 6 (Explainability is mandatory) requires that every
  Clinical Expression carries a justified Explanation. Absence
  of the reference would break the audit chain and violate the
  explainability contract.
references:
  - AS-002-AXIOM-006
  - AS-000-§3.16
tests:
  - tests/conformance/AS-002/test_explainability.py::REDACTED
status: active
version_introduced: 1.0
version_deprecated: null
superseded_by: null
```

### 29.2 Exemplo 2: Header canônico (AS-002)

```yaml
urn: urn:araos:standard:002:1.0
categoria: Clinical Specification
status_editorial: Draft
maturidade: Draft
versao: 1.0
data: 2026-07-17
idiomas: [pt-BR]
```

### 29.3 Contraexemplo: Requirement inválido

```yaml
# INVÁLIDO — sem Requirement ID
text: "Expression should be explainable."
# Faltam: id, section, rationale, references, tests
```

Por que viola ASM-001:
- Sem Requirement ID (MM-INV-02 falharia).
- Sem Conformance Test referenciado (§10.3.7 obrigatório).
- Rationale ausente (§10.3.5 obrigatório).

---

## §30 — Conformance Requirements (do ASM-001)

| Métrica | Threshold | Como medir |
|---|---|---|
| **Header Coverage** | 100% | Todos os 6 campos canônicos presentes. |
| **Section Coverage** | 100% | Todas as 16 seções mínimas presentes (§1–§17, exceto §18 §19 que são opcionais/informativos). |
| **Requirement Coverage** | 100% | Toda REQ com teste em `tests/conformance/AS-XXX/`. |
| **Dependency Coverage** | 100% | Grafo de dependências verifica §22. |
| **Maturity Consistency** | 100% | Transições seguem §21.2. |
| **Vocabulary Coverage** | 100% | Todos os termos mapeados em §7. |
| **Axiom Coverage** | 100% | Todo axioma testado em conformidade. |

---

## Apêndice A — Norma externa de referência

- **RFC 2119** — "Key words for use in RFCs to Indicate Requirement Levels" (1997).
- **ISO/IEC Directives Part 2** — Principles and rules for the structure and drafting of ISO and IEC documents.
- **IETF RFC 8126** — Guidelines for Writing an IETF Standards Track RFC.

---

## Apêndice B — Glossário de Meta-Termos

| Termo | Significado |
|---|---|
| **Standard** | Documento normativo da AraOS Library. |
| **Requirement** | Cláusula normativa individual com ID canônico. |
| **Constraint** | Restrição técnica ou formal. |
| **Reference** | Apontamento para fonte interna ou externa. |
| **Artifact** | Materialização física do Standard. |
| **Conformance Test** | Teste automatizado que verifica cumprimento de Requirement. |
| **Maturity** | Estado do ciclo de vida editorial. |
| **URN** | Uniform Resource Name — identificador persistente. |

---

## Apêndice C — Conformidade Cross-AS

| AS verificado | Como ASM-001 se aplica |
|---|---|
| AS-000 | ASM-001 SHALL NOT redefinir termos de AS-000. |
| AS-001 | ASM-001 SHALL usar AS-001 §10 como exemplo concreto de Requirement. |
| AS-002 | ASM-001 SHALL usar AS-002 §10 como exemplo concreto de Requirement. |

---

## Apêndice D — Roadmap

| Versão | Mudança prevista |
|---|---|
| 1.1 | Adicionar suporte a schemas versionais (Requirement → Schema). |
| 1.2 | Adicionar modelo de Profile (subconjunto nomeado de Requirements). |
| 2.0 | Parser canônico de MD → JSON. |

---

## Version History

| Versão | Data | Status | Mudanças | Autor |
|---|---|---|---|---|
| 1.0 | 2026-07-17 | Draft | Redação inaugural. Definição completa do meta-modelo, maturidade 9 estados, verbos RFC 2119, dependency graph, traceability chain, machine readability. | AraOS Editorial Committee |

---

**Fim do ASM-001 v1.0 (Draft).**
