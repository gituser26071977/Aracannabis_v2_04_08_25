# AS-001 — AraOS Standard 001: Clinical Gene Standard

> **Status:** Aceito
> **Versão:** 1.0
> **Data:** 2026-07-17
> **Tipo:** AraOS Standard (Normativo)
> **Autoria:** AraOS Architecture
> **Substitui:** nenhum documento (primeira emissão)

| Campo | Valor |
|---|---|
| **Identificador** | AS-001 |
| **Título** | Clinical Gene Standard |
| **Categoria** | Clinical Knowledge Representation |
| **Status** | Normative |
| **Maturity** | Stable |
| **Versão** | 1.0 |
| **Data de emissão** | 2026-07-17 |
| **Próxima revisão prevista** | quando AS-002 atingir Reference Implementation |
| **Norma superior** | Constituição do AraOS v1.0 (Lex AraOS) |
| **ADR governante** | ADR-0005 (ACCEPTED) |
| **Paper governante** | Paper III (Clinical Genome) |
| **Persistent Identifier** | `urn:araos:standard:001:1.0` |
| **Estado editorial** | **Verified** (Draft → Technical Review → Scientific Review → Accepted → Published → Reference Implementation → Verified) |

## Fontes Normativas Obrigatórias

Este AraOS Standard é derivado e materializa as seguintes fontes:

| Fonte | Status | Papel |
|---|---|---|
| **Manifesto do AraOS** | Manifesto v0.1 | Princípio fundacional |
| **Constituição do AraOS (Lex AraOS)** | Constituição v1.0, 17/07/2026 | Lei suprema do domínio |
| **Paper II — The Nature of Clinical Knowledge** | Paper II | Distinção informação × conhecimento |
| **Paper III — Clinical Genome** (referenciado em Papers IV–VI) | Paper III | Teoria do Genoma Clínico |
| **Paper IV — A Teoria da Expressão Clínica** | Paper IV | Dinâmica do Gene |
| **Paper V — A Teoria da Inferência Clínica** | Paper V | Atualização por evidências |
| **Paper VI — A Teoria da Interpretação Clínica** | Paper VI | Interpretação do Gene |
| **ADR-0005 — Sprint 4.3 Clinical Genome Engine** | ADR-0005 (ACCEPTED) | Decisão arquitetural canônica |

Em caso de conflito, prevalece a **Constituição do AraOS** (Lex AraOS).
Em caso de ambiguidade, prevalece a redação do ADR-0005.

---

## Prefácio

O AraOS (Knowledge Infrastructure for Clinical Reasoning) é uma
infraestrutura computacional para **representação, evolução,
inferência e interpretação do conhecimento clínico**.

A unidade fundamental dessa representação é o **Clinical Gene** —
conceito central introduzido pelo Paper III e ratificado pelo Artigo 5
da Constituição do AraOS.

Este documento (**AS-001**) é a primeira especificação normativa do
AraOS. Ele define, com rigor comparável a uma RFC ou norma ISO, o
**contrato conceitual, semântico e computacional** que toda
implementação do Clinical Gene deve observar.

Nenhuma linha de código relacionada ao Clinical Gene é canônica se
desrespeitar este Standard.

---

## Design Goals (Objetivos de Design)

Este Standard foi concebido para satisfazer os seguintes objetivos
de design, alinhados ao Manifesto do AraOS e à Constituição:

| # | Goal | Materializa |
|---|---|---|
| 1 | **Semantic Stability** — Genes mantêm identidade ao longo do tempo. | Paper III §3, Constituição Art. 5 |
| 2 | **Longitudinal Representation** — toda observação clínica é integrada em trajetória temporal. | Paper II Cap. 3, Constituição Art. 8 |
| 3 | **Explainability** — toda alteração significativa produz explicação rastreável. | Constituição Art. 9 |
| 4 | **Scientific Reproducibility** — estado reconstruível bit-identical a partir de eventos. | ADR-0001, Constituição Art. 7 |
| 5 | **Computational Traceability** — toda mutação é registrada com proveniência. | ADR-0001, Constituição Art. 7 |
| 6 | **Multi-tenancy** — isolamento estrito por tenant sem vazamento. | Constituição Art. 1 |
| 7 | **Version Compatibility** — múltiplas versões do Registry coexistem. | Constituição Art. 16 |
| 8 | **Incremental Evolution** — adições futuras preservam compatibilidade. | Constituição Art. 16, Art. 19 |
| 9 | **AI Compatibility** — Gene state é interpretável por sistemas de IA sem substituir o julgamento clínico. | Constituição Art. 17 |
| 10 | **Knowledge Graph Compatibility** — Relationships nasce KG-ready. | Paper III §5, ADR-0005 |

> **NOTA** — Implementações **should** explicitar, em sua declaração
> de conformidade, quais Design Goals foram atendidos por quais
> requisitos (§11.3) e por quais decisões arquiteturais (ADRs
> derivados).

---

## Non-Goals (Fora do Escopo)

Este Standard **deliberadamente não define**:

| # | Item | Razão |
|---|---|---|
| 1 | **Algoritmos de inferência clínica** | definidos no AS-004 (Clinical Inference). |
| 2 | **Regras de diagnóstico** | proibidas constitucionalmente (Art. 17). IA nunca diagnostica. |
| 3 | **Camada de apresentação (UI)** | decisão arquitetural fora do escopo. |
| 4 | **Storage engine específico** | definido pelo ADR-0001 (Event Store) e livre escolha de projeção. |
| 5 | **Protocolo de serialização** | responsabilidade do transport layer (não canônica). |
| 6 | **Schema SQL** | responsabilidade das migrations; AS-001 exige apenas persistência append-only e rebuildable. |
| 7 | **Modelos de machine learning** | proibidos constitucionalmente como entrada diagnóstica (Art. 17); ML só como contrato (Sprint 4.5). |
| 8 | **Contratos de API** | definidos em blueprints Flask; AS-001 fixa apenas o **domínio**. |
| 9 | **Critérios de interpretação clínica** | definidos no AS-005 (Clinical Interpretation). |
| 10 | **Regras de decisão clínica automatizada** | proibidas — toda decisão exige confirmação humana. |

> **NOTA** — Toda interpretação futura deste Standard **shall not**
> estender seu escopo a itens desta lista sem revisão explícita em
> ADR, seguida de nova versão SemVer major deste AS.

---

## Formal Axioms (Axiomas Formais)

Os axiomas a seguir fundamentam o Clinical Gene como conceito
canônico. Toda implementação **shall** preservar sua validade.

### Axiom 1 — Uniqueness of Function

> **Every Clinical Gene represents exactly one Fundamental Clinical
> Function.**
>
> A granularidade de um Gene é determinada pelo Gene Registry v1.0
> (Apêndice B). Nenhum Gene pode representar duas funções
> fundamentais simultaneamente.

### Axiom 2 — Semantic Stability

> **A Clinical Gene preserves semantic identity throughout its
> lifecycle.**
>
> `clinical_gene_id` **shall not** mudar em resposta a eventos
> clínicos. A evolução do conhecimento que o Gene representa é
> expressa exclusivamente por sua Clinical Expression (AS-002) e
> documentada em sua Trajectory.

### Axiom 3 — Event-Expression Decoupling

> **Clinical Events never modify Clinical Genes.**
> **Clinical Events modify Clinical Expressions.**
>
> Toda mutação observável do Gene ocorre via Expression.
> Identidade, composição estrutural e relações de identidade do Gene
> **shall not** ser afetadas por eventos.

### Axiom 4 — Canonical Representation

> **The Clinical Genome is the canonical representation of clinical
> knowledge for a patient.**
>
> O Genome é reconstruído a partir do Event Store e do conjunto de
> Genes observados. Não existe estado canônico fora do Genome.

### Axiom 5 — Interpretation as Projection

> **Interpretations are projections. Never canonical state.**
>
> Clinical Interpretation, Outcome View e demais leituras são
> derivados do estado do Gene. Nenhuma implementação **shall**
> tratar interpretação como fonte primária de verdade.

### Axiom 6 — Identity is Stable, Context Modulates

> **A Clinical Gene is semantically identical across patients and
> contexts; only its Clinical Expression is modulated.**
>
> Contexto clínico modula Expression, Hypotheses e Confidence, mas
> **shall not** alterar a identidade do Gene.

### Axiom 7 — Replay Idempotency

> **The state of any Clinical Gene is bit-identical regardless of
> replay order or count.**
>
> Reconstrução a partir do Event Store é determinística e
> idempotente. Esta propriedade **shall** ser testada por suite de
> conformidade (replay bit-identical, 1x / 2x / 50x / 100x, ordem
> aleatória).

### Axiom 8 — Evidence Preservation

> **Evidence that contributed to a Clinical Expression is preserved
> for the lifetime of the Expression.**
>
> A lista de evidências que sustentam uma Expression **shall not**
> ser reduzida após sua escrita. Novas evidências agregam; antigas
> permanecem como histórico causal.

### Axiom 9 — Hypothesis Coexistence

> **Multiple Hypotheses may coexist for the same Clinical Gene.**
>
> Nenhuma implementação **shall** impor exclusividade automática
> entre hipóteses. Resolução **shall** ocorrer por novas evidências,
> nunca por sobrescrita direta.

### Axiom 10 — Versioned Ontology

> **Every Clinical Gene is bound to a Registry Version at creation
> time and remains so bound.**
>
> O Registry é versionado (SemVer). Genes carregam a versão sob a
> qual foram criados. Mudanças incompatíveis no Registry
> **shall** produzir versão major; Genes antigos permanecem
> interpretáveis.

> **NOTA** — Axiomas são **invariantes lógicas**. Uma implementação
> que viole qualquer axioma **shall** ser declarada não-conforme,
> independentemente do atendimento a requisitos sintáticos.

---

## 1. Escopo

Este AraOS Standard define:

1. O conceito normativo de **Clinical Gene** e seus atributos canônicos.
2. A composição interna do Gene (Expression, Trajectory, History,
   ContextDependencies, Evidence, Confidence, Hypotheses, Relationships,
   Metadata).
3. Os requisitos de identidade, versionamento e persistência.
4. As invariantes que toda representação computacional do Gene deve
   respeitar.
5. Os critérios de conformidade para implementações que declarem
   aderência a este Standard.

**Fora do escopo** (tratados em outros AraOS Standards):

- Estrutura interna da Clinical Expression → **AS-002**.
- Composição do Clinical Genome → **AS-003**.
- Processo de Inferência Clínica → **AS-004**.
- Clinical Interpretation → **AS-005**.
- Clinical Context (alimentador) → ADR-0003 / Clinical Context Engine.

---

## 2. Referências Normativas

Os documentos a seguir são indispensáveis para a aplicação deste
Standard. Para referências datadas, aplica-se somente a edição citada.

- **Constituição do AraOS**, versão 1.0, 17 de julho de 2026.
- **Manifesto do AraOS**, versão 0.1 — A Fundação.
- **Paper II — The Nature of Clinical Knowledge**.
- **Paper III — Clinical Genome** (referência conceitual).
- **Paper IV — A Teoria da Expressão Clínica**.
- **Paper V — A Teoria da Inferência Clínica**.
- **Paper VI — A Teoria da Interpretação Clínica**.
- **ADR-0005 — Clinical Genome Engine (Sprint 4.3)**, status ACCEPTED.

---

## 3. Termos e Definições

Para os fins deste Standard, aplicam-se os termos e definições a
seguir. Termos em **negrito** estão definidos neste Standard; termos
em *itálico* remetem a definições da Constituição do AraOS.

### 3.1 Clinical Gene

Unidade fundamental do conhecimento clínico no AraOS, representando
uma **Função Clínica Fundamental** cuja expressão pode variar ao longo
do tempo em resposta a eventos clínicos, preservando contexto,
evidências, temporalidade, rastreabilidade e explicabilidade.

> **NOTA 1** — Um Clinical Gene **não** representa qualidade,
> gravidade, intensidade ou desfecho. Esses pertencem à Clinical
> Expression (AS-002).
>
> **NOTA 2** — O Clinical Gene é semanticamente estável; identidade
> não muda. O que evolui é sua Expression.
>
> **NOTA 3** — Um Clinical Gene nunca é canonicamente criado ou
> destruído por um evento; ele passa a ser **observado** ou
> **deixar de ser observado**.

### 3.2 Clinical Genome

Estado coletivo e canônico do conhecimento clínico de um paciente,
representado pelo conjunto organizado de seus Clinical Genes e suas
respectivas Expressions.

> **NOTA** — Genome é conceito arquitetural derivado. Sua
> especificação detalhada pertence ao AS-003.

### 3.3 Clinical Expression

Estado computacional observável de um Clinical Gene em um determinado
instante temporal e contextual, inferido a partir da integração de
múltiplas evidências clínicas.

> **NOTA** — A composição interna da Clinical Expression é definida
> pelo AS-002.

### 3.4 Clinical Function

Função semântica à qual um Clinical Gene pode estar associado,
utilizada para classificação, busca e correlação clínica.

> **NOTA 1** — Substitui o termo legado *capability* (singular).
>
> **NOTA 2** — Clinical Function **não** é identidade do Gene;
> múltiplos Genes podem partilhar funções.

### 3.5 Clinical Context

Contexto clínico que modula a interpretação de um ou mais Genes
(medicação, sono, fase escolar, transição familiar, etc.).
Definido em detalhe no ADR-0003 (Clinical Context Engine).

### 3.6 Clinical Event

Ocorrência clínica observada (consulta, exame, intervenção, relato,
medição, etc.) que produz **evidências** capazes de modificar
Expressões de Genes.

### 3.7 Evidence

Item atômico de informação clínica que sustenta uma afirmação sobre
o estado de um Gene.

### 3.8 Clinical Hypothesis

Interpretação alternativa do estado de um Gene, com peso
probabilístico explícito.

### 3.9 Clinical Interpretation

Leitura do estado funcional atual de um Gene, resultante da
integração de suas Expressões, Hipóteses e contexto. Especificada
pelo AS-005.

### 3.10 Registry Version

Identificador SemVer que carateriza um snapshot do Clinical Gene
Registry em um determinado momento. Permite reprodutibilidade
científica e compatibilidade entre estudos.

### 3.11 Ubiquitous Language

Linguagem canônica do AraOS, ratificada pela Constituição (Artigo 4)
e consolidada no ADR-0005.

---

## 4. Modelo Conceitual do Clinical Gene

### 4.1 Princípio Fundamental

> **O Clinical Gene é a unidade fundamental do conhecimento clínico
> no AraOS.**
>
> Toda representação computacional do conhecimento clínico deve
> **partir** do Clinical Gene. (Constituição, Artigo 5.)

### 4.2 Estabilidade Semântica

Um Clinical Gene é **semanticamente estável**: sua identidade
(`clinical_gene_id`) não se altera em resposta a eventos clínicos.
A variação temporal do conhecimento que ele representa é expressa
por meio de sua **Clinical Expression** (AS-002) e documentada em
sua **Trajectory**.

> **Requisito 4.2.1** — Uma implementação **shall not** permitir que
> um Clinical Gene mude de identidade (`clinical_gene_id`) em
> resposta a eventos.

### 4.3 Granularidade

Um Clinical Gene representa uma **única** Função Clínica Fundamental.
A granularidade é determinada pelo **Clinical Gene Registry v1.0**
(Apêndice B).

> **Requisito 4.3.1** — Cada Clinical Gene **shall** estar associado
> a exatamente uma entrada do Clinical Gene Registry.

### 4.4 Representação Canônica

A representação canônica do conhecimento clínico de um paciente é o
seu **Clinical Genome** — conjunto de Genes observados, com suas
Expressões, Trajectories e Interpretações.

> **Requisito 4.4.1** — O Clinical Genome **shall** ser reconstruível
> de forma bit-identical a partir do Event Store (Constituição,
> Artigo 7).

---

## 5. Identidade do Clinical Gene

### 5.1 Composição da Identidade

A identidade de uma instância de Clinical Gene é a tupla ordenada:

```
(tenant_id, patient_id, clinical_gene_id)
```

> **Requisito 5.1.1** — A identidade **shall** ser única no escopo
> do tenant.
>
> **Requisito 5.1.2** — `clinical_gene_id` **shall** ser um valor
> pertencente ao **Clinical Gene Registry** vigente no momento da
> criação da instância.
>
> **Requisito 5.1.3** — `tenant_id` e `patient_id` **shall** ser
> não-vazios.

### 5.2 Catálogo Fechado: Clinical Gene Registry

O conjunto de `clinical_gene_id` válidos é definido pelo
**Clinical Gene Registry** — vocabulário **fechado** e
**versionado**.

> **Requisito 5.2.1** — O Registry **shall** ser o único produtor
> legítimo de `clinical_gene_id`.
>
> **Requisito 5.2.2** — Toda instância de Gene **shall** referenciar
> a versão do Registry sob a qual foi criada.

### 5.3 Capability é Terminologia Legada

> **Requisito 5.3.1** — Implementações **shall not** tratar
> *capability* como identidade do Gene. *Capability* pode
> aparecer apenas como sinônimo histórico de **Clinical Function**
> (Artigo 13 da Constituição).

---

## 6. Composição Interna do Clinical Gene

Um Clinical Gene é composto por **nove elementos canônicos**, todos
obrigatórios:

### 6.1 Clinical Expression

Representa o estado observável atual do Gene.

> **Nota editorial (2026-07-17)** — This Standard intentionally does
> not define the internal structure of Clinical Expression.
> Clinical Expression is specified by AS-002 and shall be treated as
> a normative Value Object. Ver
> `docs/standards/preparation/as002-design-principles.md` para os
> princípios arquiteturais que orientam o AS-002.
>
> No escopo do AS-001, a Clinical Expression é tratada **apenas
> como um componente do Gene** — sua estrutura interna é delegada
> integralmente ao AS-002.

> **Requisito 6.1.1** — A Composition interna da Expression é
> especificada pelo **AS-002** e **shall** ser respeitada integralmente.
>
> **Requisito 6.1.2** — O Gene **shall** sempre portar uma Expression
> atual, mesmo que inicializada com valores nulos explícitos.

### 6.2 Clinical Trajectory

Série histórica bitemporal da Expression, preservando:

- `valid_time` — quando a mudança ocorreu clinicamente.
- `transaction_time` — quando o sistema registrou a mudança.
- `expression_snapshot` — estado da Expression naquele ponto.
- `contributing_event_ids` — proveniência.

> **Requisito 6.2.1** — A Trajectory **shall** ser **append-only**.
> Nenhuma operação **may** remover, sobrescrever ou reordenar pontos
> históricos.
>
> **Requisito 6.2.2** — A ordenação natural da Trajectory é por
> `valid_time` ascendente.
>
> **Requisito 6.2.3** — Em caso de recebimento de evento
> desordenado, a inserção **shall** preservar a ordem por
> `valid_time`.

### 6.3 History

Audit chain canônico do Gene, contendo todas as mutações
significativas (criação, atualização, transição de Expression, novo
Relationship, nova Hypothesis).

> **Requisito 6.3.1** — History **shall** ser append-only.
>
> **Requisito 6.3.2** — Cada entrada **shall** referenciar um
> `event_id` único e preservar o `sequence` (cadeia canônica por
> tenant — ADR-0001).
>
> **Requisito 6.3.3** — Toda mutação no Gene **shall** produzir
> ao menos uma entrada em History.

### 6.4 ContextDependencies

Lista de identificadores de **Clinical Context** que afetam ou
modulam a interpretação deste Gene.

> **Requisito 6.4.1** — ContextDependencies **shall** referenciar
> apenas Contextos válidos no escopo `(tenant_id, patient_id)`.
>
> **Requisito 6.4.2** — A remoção de um Clinical Context **shall**
> disparar a reavaliação da Expression (regra geral de inferência,
> AS-004).

### 6.5 Evidence

Lista de `event_id` que fundamentam o estado atual da Expression.

> **Requisito 6.5.1** — Toda alteração de Expression **shall**
> preservar a referência às evidências que a produziram.
>
> **Requisito 6.5.2** — Evidence **shall not** ser reduzida após a
> alteração (mesmo que novos eventos enfraqueçam a evidência
> original).

### 6.6 Confidence

Grau de confiança agregado da Expression atual.

> **Requisito 6.6.1** — Confidence **shall** ser um valor decimal
> no intervalo `[0.0, 1.0]`.
>
> **Requisito 6.6.2** — Confidence **shall** ser sempre explícita.
> Ausência de confiança equivale a **0.0** e **shall** ser
> registrada como tal.
>
> **Requisito 6.6.3** — Confidence **shall** ser **derivada**, não
> primária. Ela é calculada a partir das evidências (Paper V, §6).

### 6.7 Hypotheses

Interpretações alternativas concorrentes sobre o estado do Gene.

> **Requisito 6.7.1** — Cada Hypothesis **shall** possuir
> identificador único, descrição, peso (`weight ∈ [0.0, 1.0]`),
> lista de supporting events, confiança própria e timestamp de
> criação.
>
> **Requisito 6.7.2** — A soma dos pesos das Hypotheses ativas
> **may** exceder `1.0` (representando hipóteses concorrentes
> com pesos normalizados pelo motor de inferência).
>
> **Requisito 6.7.3** — Hypotheses **shall** poder coexistir e
> competir. Nenhuma implementação **may** impor exclusividade.

### 6.8 Relationships

Arestas Knowledge-Graph-ready que conectam este Gene a outros Genes.

> **Requisito 6.8.1** — Cada Relationship **shall** especificar:
> `target_gene_id`, `relationship_type`, `confidence`,
> `evidence_event_ids`.
>
> **Requisito 6.8.2** — Os tipos de Relationship canônicos
> **shall** ser versionados pelo Registry e **shall** incluir,
> no mínimo: `influences`, `co_occurs_with`, `precedes`,
> `antagonizes`, `amplifies`.
>
> **Requisito 6.8.3** — Relationships **shall** respeitar a
> simetria ou direcionalidade declarada por `relationship_type`.
> Auto-relacionamentos (Gene → Gene) **are permitted** desde que
> justificados pela evidência.

### 6.9 Metadata

Extensões não-canônicas, labels livres, hints de UI, anotações
operacionais.

> **Requisito 6.9.1** — Metadata **shall** ser tratada como **não
> canônica**. Operações de inferência **shall not** depender do
> conteúdo de Metadata.
>
> **Requisito 6.9.2** — Metadata **shall** ser imutável a partir
> do momento em que é registrada (atualizações produzem nova
> entrada em History).

### 6.10 Resumo da Composição

| # | Componente | Mutabilidade | Obrigatório | Regido por |
|---|---|---|---|---|
| 1 | Clinical Expression | Substituível | Sim | AS-002 |
| 2 | Trajectory | Append-only | Sim | §6.2 |
| 3 | History | Append-only | Sim | §6.3 |
| 4 | ContextDependencies | Mutável | Sim | §6.4 |
| 5 | Evidence | Append-only | Sim | §6.5 |
| 6 | Confidence | Derivada | Sim | §6.6 |
| 7 | Hypotheses | Mutável | Sim | §6.7 |
| 8 | Relationships | Mutável | Sim | §6.8 |
| 9 | Metadata | Append-only | Sim | §6.9 |

---

## 7. Princípios de Comportamento

### 7.1 Eventos Modificam Expressões, não Genes

> **Requisito 7.1.1** — Eventos clínicos **shall** modificar
> primariamente a Clinical Expression, e por consequência a
> Confidence, Hypotheses e History do Gene. A identidade do Gene
> **shall not** ser afetada.
>
> (Paper IV, §4; Constituição Artigo 7)

### 7.2 Estabilidade do Conhecimento

> **Requisito 7.2.1** — A unidade semântica do Gene **shall** ser
> preservada em toda a evolução temporal do sistema.

### 7.3 Integração de Evidências

> **Requisito 7.3.1** — A Expression **shall** integrar múltiplas
> evidências. Nenhuma evidência isolada **may** definir a
> Expression final.

### 7.4 Continuidade Longitudinal

> **Requisito 7.4.1** — A Trajectory **shall** preservar
> continuidade da expressão ao longo do tempo. Descontinuidades
> (gaps) **shall** ser representadas como pontos válidos com
> estado explícito `unknown`.

### 7.5 Explainability Obrigatória

> **Requisito 7.5.1** — Toda alteração significativa de uma
> Expression **shall** produzir uma **Explanation** (Sprint 4.1,
> ADR-0001) referenciada por `Expression.explanation_reference`.
>
> (Constituição Artigo 9; Paper IV §9)

### 7.6 Independência de Hipóteses

> **Requisito 7.6.1** — Hipóteses **shall** poder coexistir.
> Implementações **shall not** impor exclusividade automática.
> Resolução de hipóteses **shall** ocorrer por novas evidências,
> não por sobrescrita direta.

### 7.7 Idempotência de Replay

> **Requisito 7.7.1** — A reconstrução do Gene a partir do Event
> Store **shall** ser **bit-identical** ao estado atual, qualquer
> que seja a ordem de aplicação dos eventos (processamento
> sequencial) e qualquer que seja o número de aplicações
> (idempotência).

---

## 8. Versionamento do Clinical Gene Registry

### 8.1 Princípio do Versionamento Explícito

O Clinical Gene Registry é **versionado** para garantir
rastreabilidade científica, reprodutibilidade e compatibilidade
entre estudos e versões da plataforma.

> **Requisito 8.1.1** — Toda referência a um `clinical_gene_id`
> **shall** carregar implicitamente a versão do Registry sob a
> qual foi criada.

### 8.2 Formato Semântico

O Registry usa **SemVer** simplificado: `MAJOR.MINOR` (com PATCH
opcional: `MAJOR.MINOR.PATCH`).

- **MAJOR** incompatível (reorganização conceitual).
- **MINOR** aditivo/renomeação retrocompatível.
- **PATCH** correções documentacionais.

### 8.3 Versão Vigente

A versão vigente por este Standard é **Registry v1.0** (Apêndice B).

> **Requisito 8.3.1** — Versões futuras **shall** coexistir com
> a v1.0. Implementações **shall** preservar a capacidade de
> interpretar Genes criados sob qualquer versão anterior do
> Registry.

### 8.4 Persistência da Versão

> **Requisito 8.4.1** — A versão do Registry **shall** ser
> persistida junto a cada Gene e **shall** ser consultável
> separadamente em tabela de controle
> (`clinical_gene_registry_versions`).
>
> **Requisito 8.4.2** — A tabela de controle **shall** registrar,
> no mínimo: `version`, `effective_from`, `gene_ids_json`,
> `created_by`.

---

## 9. Multi-Tenancy

> **Requisito 9.1** — Toda instância de Clinical Gene **shall**
> carregar `tenant_id` explícito.

> **Requisito 9.2** — Operações **shall** verificar isolamento por
> tenant antes de qualquer acesso. Fuga de tenant **shall** ser
> registrada como falha de segurança.

> **Requisito 9.3** — Identidade `(tenant_id, patient_id,
> clinical_gene_id)` **shall** ser única no escopo global da
> plataforma.

---

## 10. Requisitos de Persistência

> **Requisito 10.1** — Toda mutação de Gene **shall** ser
> registrada no Event Store antes de ser refletida em qualquer
> projeção (Constituição Artigo 7; ADR-0001).

> **Requisito 10.2** — A projeção materializada do Gene **shall**
> ser rebuildable a partir do Event Store.

> **Requisito 10.3** — Reconstrução **shall** ser bit-identical
> ao estado atual.

> **Requisito 10.4** — Processamento concorrente do mesmo Gene
> **shall** ser resolvido por `sequence` per-tenant (ADR-0001) e
> `processed_events`.

> **Requisito 10.5** — Indexação mínima obrigatória:
> `(tenant_id, patient_id, gene_id)` único;
> `(tenant_id, patient_id, valid_time)` para Trajectory;
> `(tenant_id, source_gene_id)` para Relationships.

---

## 11. Conformidade

### 11.0 Compliance Levels (Níveis de Conformidade)

Uma implementação pode declarar conformidade em **quatro níveis
cumulativos**, alinhados ao roadmap (Apêndice E):

| Nível | Nome | Requisitos | Caso de Uso |
|---|---|---|---|
| **A** | Gene-Conformant | Implementa integralmente o **AS-001** (Clinical Gene v1.0). | Implementações standalone que armazenam apenas Genes. |
| **B** | Expression-Conformant | **A** + **AS-002** (Clinical Expression v1.0). | Sistemas que precisam dinâmicas de Expression ao longo do tempo. |
| **C** | Genome-Conformant | **B** + **AS-003** (Clinical Genome v1.0). | Sistemas clínicos integrados com representação completa do Genome. |
| **D** | Full AraOS Standard Compliance | **C** + **AS-004** (Clinical Inference) + **AS-005** (Clinical Interpretation) + **AS-006** (Clinical Context). | Plataforma AraOS canônica. |

> **Requisito 11.0.1** — Toda implementação **shall** declarar
> explicitamente o nível de conformidade reivindicado.
>
> **Requisito 11.0.2** — Conformidade em nível **N** **shall**
> implicar conformidade em todos os níveis inferiores.
>
> **Requisito 11.0.3** — Integrações externas **shall** recusar
> declarar conformidade acima do nível que efetivamente
> implementam.

### 11.1 Declaração de Conformidade

Uma implementação declara conformidade com este Standard quando:

1. Implementa **todas** as invariantes enumeradas neste documento
   sem exceção.
2. Aplica o Registry v1.0 (Apêndice B) integralmente.
3. Respeita o Princípio da Coerência (Constituição Artigo 18):
   toda decisão de modelagem é precedida pela pergunta
   *"Esta decisão fortalece o Clinical Gene como unidade
   fundamental da representação computacional do conhecimento
   clínico?"*.
4. Mantém cobertura de testes ≥ 95% para os componentes
>   diretamente relacionados ao Gene.
5. Documenta cada divergência eventual em ADR específico,
>   aprovado conforme o processo definido em §11.2.
6. Declara o Compliance Level (§11.0) alcançado.

### 11.2 Processo de Mudança

Mudanças neste Standard **shall** ser propostas via ADR, seguindo
a hierarquia:

```
Papers → ADR → AS → Implementação
```

Versões deste AS seguem SemVer:

- Mudança incompatível com a versão anterior → `MAJOR+1`.
- Adição retrocompatível → `MINOR+1`.
- Correção editorial ou clarificação → `PATCH+1`.

### 11.3 Matriz de Conformidade (Resumo)

| Requisito | Verificável por |
|---|---|
| 4.2.1 (estabilidade identidade) | Teste de invariante de domínio |
| 4.3.1 (Registry) | Teste de loader / enum coverage |
| 5.1.1–5.1.3 (identidade) | Teste de chave primária |
| 5.2.1–5.2.2 (Registry) | Teste de versionamento |
| 5.3.1 (sem capability) | Teste estático de código |
| 6.2.1 (Trajectory append-only) | Property-based test |
| 6.3.1–6.3.3 (History) | Teste de audit chain |
| 6.6.1–6.6.3 (Confidence) | Teste de invariante |
| 6.7.1–6.7.3 (Hypotheses) | Property-based test |
| 7.1.1 (eventos não mudam Gene) | Teste de invariante |
| 7.7.1 (idempotência replay) | Teste de replay bit-identical |
| 8.4.1–8.4.2 (versão persistida) | Teste de schema SQL |
| 9.1–9.3 (multi-tenancy) | Teste de tenant isolation |
| 10.1–10.5 (persistência) | Teste de projection rebuild |

---

## 12. Conformidade com a Constituição

Este Standard não derroga nem substitui a Constituição do AraOS.
Em particular, observam-se integralmente:

- Artigo 1 — O Domínio governa a Tecnologia.
- Artigo 2 — O Conhecimento precede os Dados.
- Artigo 4 — A Linguagem é o Principal Ativo.
- Artigo 5 — O Clinical Gene é a Unidade Fundamental.
- Artigo 7 — Eventos Transformam Conhecimento.
- Artigo 8 — Todo Conhecimento é Temporal.
- Artigo 9 — Explicabilidade é Obrigatória.
- Artigo 10 — O Contexto faz Parte do Conhecimento.
- Artigo 13 — A Ontologia é a Fonte da Verdade.
- Artigo 16 — O Conhecimento é Versionado.
- Artigo 18 — Princípio da Coerência.
- Artigo 19 — Princípio da Simplicidade Conceitual.

---

## Apêndice A — Mapeamento para Fontes Normativas

| Cláusula deste AS | Paper | Constituição | ADR |
|---|---|---|---|
| §3.1 Clinical Gene | Paper III §3 | Artigo 5 | ADR-0005 §1 |
| §3.2 Clinical Genome | Paper III §5 | Artigo 6 | ADR-0005 §5 |
| §3.3 Clinical Expression | Paper IV §3 | Artigo 7 | ADR-0005 §5 |
| §4 Estabilidade | Paper IV §2 | — | ADR-0005 §1 |
| §5 Identidade | Paper III §4 | Artigo 5 | ADR-0005 §1 |
| §6.1 Expression | Paper IV §3 | — | ADR-0005 §5 |
| §6.2 Trajectory | Paper IV §6 | Artigo 8 | ADR-0005 §5 |
| §6.3 History | — | Artigo 7 | ADR-0001 |
| §6.4 ContextDependencies | Paper IV §8 | Artigo 10 | ADR-0003 |
| §6.5 Evidence | Paper V §6 | Artigo 11 | — |
| §6.6 Confidence | Paper IV §7 | Artigo 11 | — |
| §6.7 Hypotheses | Paper VI §4 | Artigo 15 | — |
| §6.8 Relationships | Paper III §5 | Artigo 6 | — |
| §6.9 Metadata | — | Artigo 3 | — |
| §7.1 Eventos → Expression | Paper IV §4 | Artigo 7 | ADR-0005 |
| §7.5 Explainability | Paper IV §9 | Artigo 9 | ADR-0001 |
| §7.7 Idempotência | Paper V §8 | — | ADR-0001 |
| §8 Versionamento | Paper III §4 | Artigo 16 | ADR-0005 §4 |

---

## Apêndice B — Clinical Gene Registry v1.0 (Canônico)

A versão **v1.0** do Clinical Gene Registry é fixada por este
Standard. Mudanças incrementais exigem nova versão do Registry.

| Gene ID | Display Name | Clinical Functions |
|---|---|---|
| `SOCIAL_COMMUNICATION` | Social Communication | communication, language, social |
| `EXECUTIVE_FUNCTION` | Executive Function | attention, planning, flexibility |
| `SLEEP` | Sleep | sleep, circadian, rest |
| `LANGUAGE` | Language | language, communication |
| `EMOTIONAL_REGULATION` | Emotional Regulation | emotion, affect, self-regulation |
| `ANXIETY_REGULATION` | Anxiety Regulation | anxiety, worry, fear |
| `MOBILITY` | Mobility | motor, coordination, gait |

> **Renomeações ratificadas neste Standard:**
>
> - `SLEEP_QUALITY` (proposta inicial) → **`SLEEP`** (canônico).
>   Genes representam funções, não qualidades.
> - `ANXIETY` (proposta inicial) → **`ANXIETY_REGULATION`**
>   (canônico). Genes representam funções regulatórias, não
>   estados absolutos.

---

## Apêndice C — Glossário de Referência Rápida

| Termo | Definição |
|---|---|
| **Clinical Gene** | Unidade fundamental do conhecimento clínico (AS-001). |
| **Clinical Genome** | Estado canônico coletivo (AS-003). |
| **Clinical Expression** | Estado observável atual do Gene (AS-002). |
| **Clinical Trajectory** | Evolução bitemporal da Expression (§6.2). |
| **Clinical Context** | Contexto clínico modulador (ADR-0003). |
| **Clinical Event** | Ocorrência que produz Evidence. |
| **Evidence** | Item atômico de sustentação. |
| **Clinical Hypothesis** | Interpretação alternativa concorrente. |
| **Clinical Interpretation** | Leitura atual do estado do Gene (AS-005). |
| **Clinical Function** | Função semântica associada ao Gene. |
| **Registry Version** | Identificador SemVer do Registry. |
| **Confidence** | Grau de certeza `[0.0, 1.0]`. |
| **History** | Audit chain canônico do Gene. |
| **Metadata** | Extensões não-canônicas. |
| **Ubiquitous Language** | Linguagem canônica do AraOS. |

---

## Apêndice D — Histórico de Versões

| Versão | Data | Mudança | Status |
|---|---|---|---|
| 1.0 | 2026-07-17 | Emissão inicial | Aceito |

---

## Apêndice E — Evolution Roadmap

Este Standard é o **primeiro** de uma família. Implementações
devem prever sua evolução dentro do roadmap abaixo. Cada AraOS
Standard da sequência adiciona contratos sem invalidar os
anteriores; conformidade é cumulativa (§11.0).

### E.1 Sequência Canônica

```
AS-001  Clinical Gene v1.0         ← (este documento)
   ↓
AS-002  Clinical Expression v1.0   ← Paper IV, ADR-0005
   ↓
AS-003  Clinical Genome v1.0       ← Paper III, ADR-0005
   ↓
AS-004  Clinical Inference v1.0    ← Paper V, ADR-0005
   ↓
AS-005  Clinical Interpretation v1.0 ← Paper VI, ADR-0005
   ↓
AS-006  Clinical Context v1.0      ← ADR-0003
```

### E.2 Compatibilidade Direcional

> **Requisito E.2.1** — Cada AS subsequente **shall** referenciar
> e estender os AS anteriores, sem contradizê-los.
>
> **Requisito E.2.2** — Caso um AS futuro precise romper
> compatibilidade com um AS anterior, o rompimento **shall**
> produzir nova versão major do AS anterior **e** o AS
> sucessor.
>
> **Requisito E.2.3** — Implementações **shall** preservar a
> capacidade de ler Genes criados sob qualquer versão do
> Registry, indefinidamente.

### E.3 Mapa de Acoplamento

| De → Para | Acoplamento |
|---|---|
| AS-001 → AS-002 | Gene hospeda Expression (§6.1) |
| AS-001 → AS-003 | Gene compõe Genome |
| AS-001 → AS-006 | Gene referencia ContextDependencies (§6.4) |
| AS-002 → AS-003 | Expressions compõem Genome state |
| AS-002 → AS-004 | Expression é atualizada por Inference |
| AS-002 → AS-005 | Interpretation lê Expression |
| AS-004 → AS-005 | Inference alimenta Interpretation |

> **NOTA** — A direção `→` indica **dependência funcional**, não
> dependência temporal de publicação. Uma implementação
> Gene-Conformant (Level A) **may** existir antes do AS-002.

### E.4 Marcos Históricos do Roadmap

| Marco | Data | Status |
|---|---|---|
| AS-001 emitido | 2026-07-17 | **Alcançado** |
| AS-002 a emitir | Sprint 4.3 Phase 2 | Planejado |
| AS-003 a emitir | pós-Sprint 4.3 | Planejado |
| AS-004 a emitir | Sprint 4.4 (Correlation + Cohort + Research) | Planejado |
| AS-005 a emitir | pós-Sprint 4.4 | Planejado |
| AS-006 a emitir | paralelo ao AS-002 (Clinical Context já implementado) | Planejado |

---

## Aviso Final

> Este AraOS Standard define o **contrato normativo** do Clinical
> Gene. Toda implementação que deseje ostentar conformidade com o
> AraOS **shall** observar as invariantes aqui declaradas.
>
> Em caso de dúvida durante a modelagem, responder primeiro:
>
> *"Esta implementação fortalece o Clinical Gene como a unidade
> fundamental da representação computacional do conhecimento
> clínico?"*
>
> Se a resposta for negativa, **shall** revisar a modelagem
> **antes** de escrever código. (Constituição, Artigo 18.)