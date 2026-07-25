# AS-000 — AraOS Language Specification

> **Status:** Draft
> **Versão:** 1.0
> **Data:** 2026-07-17
> **Tipo:** AraOS Standard (Normativo — Foundational)
> **Autoria:** AraOS Architecture
> **Substitui:** nenhum documento (primeira emissão da família AS-000)

| Campo | Valor |
|---|---|
| **Identificador** | AS-000 |
| **Título** | AraOS Language Specification |
| **Categoria** | Foundational Standard (Language Specification) |
| **Status** | Normative |
| **Maturity** | Stable |
| **Versão** | 1.0 |
| **Data de emissão** | 2026-07-17 |
| **Próxima revisão prevista** | quando 3+ AraOS Standards adicionais forem Published |
| **Norma superior** | Constituição do AraOS v1.0 (Lex AraOS) |
| **ADR governante** | ADR-0005 (ACCEPTED) |
| **Paper governante** | Paper II — The Nature of Clinical Knowledge |
| **Persistent Identifier** | `urn:araos:standard:000:1.0` |
| **Estado editorial** | Draft (ver §6 da AraOS Library README) |
| **Posição hierárquica** | Acima de AS-001..AS-006; abaixo da Constituição |

## Fontes Normativas Obrigatórias

Este AraOS Standard é derivado e materializa as seguintes fontes:

| Fonte | Status | Papel |
|---|---|---|
| **Manifesto do AraOS** | Manifesto v0.1 | Princípio fundacional |
| **Constituição do AraOS (Lex AraOS)** | Constituição v1.0, 17/07/2026 | Lei suprema do domínio |
| **Paper II — The Nature of Clinical Knowledge** | Paper II | Distinção informação × conhecimento |
| **Paper III — Clinical Genome** | Paper III | Origem dos conceitos clínicos |
| **ADR-0001 — Clinical Event Engine** | ADR-0001 (ACCEPTED) | Origem de Domain Event |
| **ADR-0005 — Sprint 4.3 Clinical Genome Engine** | ADR-0005 (ACCEPTED) | Origem de Clinical Gene/Expression |
| **AS-001 — Clinical Gene Standard** | AS-001 v1.0 (Published) | Primeiro consumidor desta gramática |

Em caso de conflito, prevalece a **Constituição do AraOS** (Lex AraOS).
Em caso de ambiguidade, prevalece a redação do ADR correspondente.

---

## Prefácio

O AraOS (Knowledge Infrastructure for Clinical Reasoning) é uma
infraestrutura computacional para **representação, evolução,
inferência e interpretação do conhecimento clínico**. A qualidade
dessa representação depende, antes de qualquer tecnologia, da
**linguagem** utilizada para descrevê-la.

> **Este Standard — AS-000 — define a gramática oficial do AraOS.**

Ele **não** descreve conceitos clínicos. Descreve os termos
arquiteturais e epistemológicos sobre os quais todos os AraOS
Standards serão escritos.

Após sua aprovação, **nenhum Standard poderá redefinir** um
termo fixado por este documento; apenas **referenciá-lo**.

> **AS-000 ocupa o topo da pirâmide normativa técnica do AraOS** —
> logo abaixo da Constituição (Lex AraOS) e acima de todos os
> AraOS Standards clínicos (AS-001..AS-006).

---

## Design Goals (Objetivos de Design)

Este Standard foi concebido para satisfazer os seguintes
objetivos:

| # | Goal | Materializa |
|---|---|---|
| 1 | **Language Stability** — cada termo mantém significado estável entre versões. | Constituição Art. 4 |
| 2 | **Single Definition** — cada termo canônico possui exatamente uma definição oficial. | Constituição Art. 4 |
| 3 | **Composability** — Standards podem ser combinados sem ambiguidade. | Constituição Art. 19 |
| 4 | **Traceability** — todo termo é rastreável a Paper, ADR ou Constituição. | Constituição Art. 9 |
| 5 | **Cross-Domain Reuse** — termos aplicam-se a múltiplos domínios clínicos. | Constituição Art. 1 |
| 6 | **DDD Compatibility** — termos mapeiam-se a categorias DDD canônicas. | Origem DDD (Evans, Vernon) |
| 7 | **Temporal Awareness** — termos admitem evolução sem quebrar contratos. | Constituição Art. 16 |
| 8 | **Knowledge Centricity** — termos priorizam conhecimento sobre dados. | Manifesto + Constituição Art. 2 |
| 9 | **Explainability Native** — termos carregam responsabilidade de explicação. | Constituição Art. 9 |
| 10 | **Multi-Tenancy by Default** — termos admitem isolamento por tenant. | Constituição Art. 1 |

---

## Non-Goals (Fora do Escopo)

Este Standard **deliberadamente não define**:

| # | Item | Razão |
|---|---|---|
| 1 | **Conceitos clínicos específicos** (Gene, Expression, Genome, Episode, Outcome). | definidos em AS-001..AS-006. |
| 2 | **Algoritmos de inferência ou interpretação.** | definidos no AS-004 (Clinical Inference). |
| 3 | **Regras de diagnóstico.** | proibidas constitucionalmente (Art. 17). |
| 4 | **Storage engines.** | decisão técnica (ADR-0001, livre escolha de implementação). |
| 5 | **Protocolos de serialização.** | responsabilidade do transport layer. |
| 6 | **Schemas SQL.** | responsabilidade das migrations. |
| 7 | **Modelos de machine learning.** | proibidos como entrada diagnóstica. |
| 8 | **Camada de apresentação (UI).** | decisão arquitetural fora do escopo. |
| 9 | **Contratos de API.** | definidos em blueprints Flask. |
| 10 | **Definições DDD originais.** | este AS herda e referencia; não substitui Evans/Vernon. |

---

## 1. Escopo

Este AraOS Standard define a **gramática oficial** utilizada por
todos os AraOS Standards clínicos e técnicos. Em particular:

1. Os termos arquiteturais e epistemológicos canônicos do AraOS.
2. As invariantes lógicas (axiomas) que governam o uso desses
   termos.
3. O mapeamento dos conceitos AraOS para categorias DDD.
4. As regras que **proíbem redefinição** desses termos em outros
   Standards.
5. Os requisitos de conformidade que todo Standard deve atender
   para ser considerado compatível com a linguagem oficial.

**Fora do escopo** (tratados em outros AraOS Standards):

- Estrutura interna da Clinical Expression → **AS-002**.
- Clinical Gene → **AS-001**.
- Clinical Genome → **AS-003**.
- Clinical Inference → **AS-004**.
- Clinical Interpretation → **AS-005**.
- Clinical Context → **AS-006**.

---

## 2. Referências Normativas

Os documentos a seguir são indispensáveis para a aplicação
deste Standard. Para referências datadas, aplica-se somente a
edição citada.

- **Constituição do AraOS**, versão 1.0, 17 de julho de 2026.
- **Manifesto do AraOS**, versão 0.1 — A Fundação.
- **Paper II — The Nature of Clinical Knowledge**.
- **Paper III — Clinical Genome**.
- **ADR-0001 — Clinical Event Engine (canonical reference)**.
- **ADR-0005 — Clinical Genome Engine (Sprint 4.3)**, ACCEPTED.
- **AS-001 — Clinical Gene Standard v1.0**, Published.

---

## 3. Termos e Definições

Cada termo abaixo é **oficial** e **imutável entre versões**
deste Standard, salvo emissão de nova versão major (SemVer).

### 3.1 Entity

> Uma Entity é qualquer objeto de domínio distinguível por
> **identidade referencial** estável ao longo do tempo.

- **Motivação:** representar conceitos cujo ciclo de vida é
  independente de seus atributos.
- **Responsabilidades:** carregar identificador único; permitir
  mutação ao longo do tempo.
- **Invariantes:** igualdade referencial; ciclo de vida próprio.
- **Exemplos:** Clinical Gene, Clinical Identity, Cohort.
- **Contraexemplos:** Clinical Expression (não possui identidade
  própria — é Value Object).
- **Relação:** difere de Value Object (3.2) por possuir
  identidade; difere de Aggregate Root (3.4) por não ser ponto de
  entrada obrigatório.
- **Consequência para implementação:** toda Entity **shall**
  possuir campo `id` estável e operação de equality referencial.
- **Referências cruzadas:** §3.2 Value Object; §3.4 Aggregate
  Root; §3.13 Semantic Identity.

### 3.2 Value Object

> Um Value Object é um objeto de domínio sem identidade
> referencial, cuja igualdade é **estrutural**.

- **Motivação:** representar conceitos descritos inteiramente por
  seus atributos, sem história própria.
- **Responsabilidades:** carregar valores; produzir igualdade
  estrutural; permanecer imutável.
- **Invariantes:** sem `id`; imutável após construção;
  substituível integralmente.
- **Exemplos:** Clinical Expression, Clinical Context, Evidence,
  Trajectory point.
- **Contraexemplos:** Clinical Gene (é Aggregate Root, com
  identidade estável).
- **Relação:** pertence a um Aggregate (3.3); pode ser criado,
  substituído ou removido sem afetar a identidade do Aggregate
  hospedeiro.
- **Consequência para implementação:** todo Value Object **shall**
  ser imutável; equality **shall** ser estrutural (todos os
  campos).
- **Referências cruzadas:** §3.3 Aggregate; §3.4 Aggregate Root;
  Axiom 4.

### 3.3 Aggregate

> Um Aggregate é um cluster de Entities e Value Objects tratados
> como uma **unidade de consistência**.

- **Motivação:** delimitar fronteiras transacionais e de
  invariantes.
- **Responsabilidades:** agrupar; garantir consistência interna;
  emitir Domain Events.
- **Invariantes:** possui exatamente um Aggregate Root (3.4);
  modificações externas **shall** passar pelo Root.
- **Exemplos:** Clinical Genome (cluster de Genes de um paciente),
  Clinical Context (com dependencies).
- **Contraexemplos:** Clinical Event (não é Aggregate — é evento).
- **Relação:** sempre contém um Aggregate Root; pode conter
  Value Objects e Entities internas.
- **Consequência para implementação:** transações **shall** afetar
  apenas um Aggregate por vez.
- **Referências cruzadas:** §3.4 Aggregate Root; §3.5 Domain Event.

### 3.4 Aggregate Root

> Um Aggregate Root é a Entity que serve como **ponto de entrada
> único** de um Aggregate.

- **Motivação:** concentrar responsabilidade de invariantes do
  cluster.
- **Responsabilidades:** expor operações; proteger invariantes;
  emitir Domain Events.
- **Invariantes:** único caminho externo ao Aggregate; possui
  identidade estável (3.13).
- **Exemplos:** Clinical Gene (AR do Genome de um paciente).
- **Contraexemplos:** Clinical Expression (não é AR — é VO).
- **Relação:** governa Value Objects (3.2) e Entities internas do
  Aggregate.
- **Consequência para implementação:** somente o AR **shall**
  publicar Domain Events do Aggregate.
- **Referências cruzadas:** §3.3 Aggregate; Axiom 3.

### 3.5 Domain Event

> Um Domain Event é um **fato passado** relevante ao domínio,
> carregando identificação, momento e payload suficiente para
> reconstruir mudanças.

- **Motivação:** representar a evolução do conhecimento como
  sequência de fatos verificáveis.
- **Responsabilidades:** carregar timestamp; identificar o
  Aggregate afetado; preservar payload.
- **Invariantes:** append-only; imutável; ordenado por sequence
  per-tenant.
- **Exemplos:** ClinicalEvent (Tabela `clinical_events`),
  ClinicalGeneTrajectoryPoint.
- **Contraexemplos:** Clinical Expression (não é evento — é
  estado).
- **Relação:** modifica o estado de Aggregates (3.3); consumido
  por Projections (3.6); registrado em History (3.18).
- **Consequência para implementação:** todo Domain Event **shall**
  ser registrado no Event Store antes de ser refletido em
  qualquer projeção (ADR-0001).
- **Referências cruzadas:** §3.6 Projection; §3.18 Traceability;
  Axiom 5.

### 3.6 Projection

> Uma Projection é um **estado derivado** construído a partir da
> sequência de Domain Events.

- **Motivação:** oferecer visões otimizadas para leitura,
  pesquisa e dashboard.
- **Responsabilidades:** consumir eventos; materializar estado;
  ser rebuildable.
- **Invariantes:** rebuildable bit-identical; idempotente;
  descartável.
- **Exemplos:** Timeline Projection, Outcome Trajectory, Cohort
  materialization.
- **Contraexemplos:** Event Store (não é Projection — é source of
  truth).
- **Relação:** **nunca é** canonical state (3.9); sempre
  derivado (3.10); consumido por Interpretation (3.11).
- **Consequência para implementação:** toda Projection **shall**
  ser reconstruível a partir do Event Store; **shall not** ser
  tratada como source of truth.
- **Referências cruzadas:** §3.5 Domain Event; §3.9 Canonical
  State; §3.10 Derived State; Axiom 6, 7.

### 3.7 Evidence

> Evidence é um **item atômico** de informação clínica que
> sustenta uma afirmação sobre o estado de um objeto de domínio.

- **Motivação:** tornar afirmações rastreáveis, auditáveis e
  refutáveis.
- **Responsabilidades:** referenciar Domain Events (3.5); carregar
  peso/confiança; preservar proveniência.
- **Invariantes:** append-only; preservada para sempre; não
  reduzível após escrita.
- **Exemplos:** ClinicalEvent como Evidence de uma Expression,
  Assessment score como Evidence de Trajectory.
- **Contraexemplos:** Interpretation (não é Evidence — é leitura
  agregada).
- **Relação:** produzida por Domain Events; consumida por
  Aggregate Roots para atualizar Expression.
- **Consequência para implementação:** toda Evidence **shall**
  preservar referência ao Domain Event que a produziu.
- **Referências cruzadas:** §3.5 Domain Event; §3.18 Traceability;
  Axiom 8.

### 3.8 Context

> Context é um **modulador semântico** do estado de um objeto de
> domínio, sem o qual a interpretação é incompleta.

- **Motivação:** modelar a dependência do conhecimento em
  circunstâncias (medicação, ambiente, fase escolar, etc.).
- **Responsabilidades:** carregar descrição canônica; modular
  Expression; ser versionado.
- **Invariantes:** referenciado por ContextDependencies;
  removível; reavaliação obrigatória após mudança.
- **Exemplos:** Clinical Context (ADR-0003), ClinicalEpisode,
  MedicationContext.
- **Contraexemplos:** Clinical Gene (não é Context — é unidade
  fundamental).
- **Relação:** modula Expression; não altera identidade do
  Aggregate hospedeiro.
- **Consequência para implementação:** remoção de Context **shall**
  disparar reavaliação de Expression dependente (AS-004).
- **Referências cruzadas:** §3.13 Semantic Identity; §3.17
  Temporality.

### 3.9 Canonical State

> Canonical State é o estado **primário de verdade** de um
> Aggregate, do qual todas as demais visões derivam.

- **Motivação:** estabelecer uma única fonte de verdade.
- **Responsabilidades:** ser reconstruível; ser durável; admitir
  evolução temporal.
- **Invariantes:** reconstruível bit-identical; imutável em sua
  forma final; append-only para evolução.
- **Exemplos:** Event Store como canonical state de todo o
  sistema; Clinical Gene como canonical state do conhecimento
  clínico de um paciente.
- **Contraexemplos:** qualquer Projection (3.6).
- **Relação:** oposto complementar de Derived State (3.10);
  preservado por History (3.18).
- **Consequência para implementação:** canonical state **shall
  not** depender de Projeções; **shall** ser reconstruível.
- **Referências cruzadas:** §3.6 Projection; §3.10 Derived State;
  Axiom 7.

### 3.10 Derived State

> Derived State é qualquer estado **calculado** a partir do
> Canonical State.

- **Motivação:** oferecer leituras especializadas sem duplicar a
  verdade.
- **Responsabilidades:** refletir o canonical state; ser
  descartável; ser reconstruível.
- **Invariantes:** rebuildable; consistente com canonical;
  dispensável.
- **Exemplos:** Timeline, Outcome Trajectory, Cohort list.
- **Contraexemplos:** Event Store (canonical); Clinical Gene
  (canonical para o paciente).
- **Relação:** produzido por Processadores de Eventos; consumido
  por APIs de leitura.
- **Consequência para implementação:** derived state **shall** ser
  regenerável sem perda; **shall not** alimentar decisões
  clínicas sem passar por canonical state.
- **Referências cruzadas:** §3.6 Projection; §3.9 Canonical
  State.

### 3.11 Interpretation

> Interpretation é a **leitura atual** do estado de um objeto de
  domínio, produzida pela integração de evidências e hipóteses.

- **Motivação:** tornar o estado acessível ao julgamento clínico
  humano, sem substituir o julgamento.
- **Responsabilidades:** integrar Evidence; consolidar
  Hypotheses; carregar confidence; referenciar Explanation.
- **Invariantes:** referenciar Explanation (3.16); confidence
  explícita; nunca canônica.
- **Exemplos:** Clinical Interpretation de um Gene, Narrative
  Interpretation, Risk Interpretation.
- **Contraexemplos:** Clinical Expression (é estado; não é
  leitura).
- **Relação:** lê Expression e Hypotheses; **nunca** é fonte
  primária de verdade.
- **Consequência para implementação:** toda Interpretation
  **shall** carregar `explanation_reference` não-vazio.
- **Referências cruzadas:** §3.6 Projection; §3.12 Hypothesis;
  §3.16 Explainability; Axiom 6.

### 3.12 Hypothesis

> Hypothesis é uma **interpretação alternativa concorrente**
  sobre o estado de um objeto de domínio.

- **Motivação:** representar dúvida clínica legítima; permitir
  múltiplas leituras coexistentes.
- **Responsabilidades:** competir com outras Hypothesis; carregar
  peso (`weight`); admitir Evidence própria.
- **Invariantes:** coexistência obrigatória; exclusividade
  proibida; peso no intervalo `[0.0, 1.0]`.
- **Exemplos:** hipóteses diagnósticas concorrentes; hipóteses
  etiológicas.
- **Contraexemplos:** Interpretation única (que **deveria** ser
  múltipla, conforme este padrão).
- **Relação:** compõe Interpretation; sustentada por Evidence.
- **Consequência para implementação:** nenhuma Hypothesis **shall**
  sobrescrever outra diretamente; resolução **shall** ocorrer
  por Evidence nova.
- **Referências cruzadas:** §3.11 Interpretation; Axiom 6.

### 3.13 Semantic Identity

> Semantic Identity é a propriedade de um objeto de domínio de
> **manter seu significado estável** ao longo do tempo,
> independentemente da variação de seus atributos.

- **Motivação:** preservar interpretabilidade longitudinal.
- **Responsabilidades:** identificar o objeto sem ambiguidade;
  sobreviver a mudanças de estado.
- **Invariantes:** imutável durante o ciclo de vida do objeto;
  única no escopo declarado.
- **Exemplos:** `clinical_gene_id` identifica um Gene; `patient_id`
  identifica um paciente.
- **Contraexemplos:** timestamp (não é identidade semântica).
- **Relação:** núcleo da estabilidade do Aggregate Root (3.4).
- **Consequência para implementação:** nenhuma operação **shall**
  alterar semantic identity de um objeto.
- **Referências cruzadas:** §3.4 Aggregate Root; §3.5 Domain
  Event; Axiom 5.

### 3.14 Clinical Function

> Clinical Function é uma **função semântica** à qual um objeto
> clínico pode estar associado, usada para classificação, busca
  e correlação.

- **Motivação:** permitir categorização cross-cutting sem
  reificar como identidade.
- **Responsabilidades:** rotular; classificar; correlacionar.
- **Invariantes:** não é identidade; pode ser compartilhada
  entre múltiplos Genes.
- **Exemplos:** `sleep`, `communication`, `anxiety`,
  `self-regulation`.
- **Contraexemplos:** `clinical_gene_id` (é identidade; não
  função).
- **Relação:** substitui terminologia legada *capability*;
  nunca é chave primária.
- **Consequência para implementação:** Clinical Function **shall
  not** ser usada como identificador único.
- **Referências cruzadas:** §3.13 Semantic Identity; §3.15
  Registry.

### 3.15 Registry

> Registry é um **catálogo versionado** que define o conjunto
> fechado de identificadores válidos para uma classe de objetos.

- **Motivação:** garantir vocabulário fechado e reprodutível.
- **Responsabilidades:** validar; versionar; publicar.
- **Invariantes:** versionamento SemVer; vocabulário fechado;
  referências estáveis ao longo do tempo.
- **Exemplos:** Clinical Gene Registry v1.0 (AS-001 Apêndice B).
- **Contraexemplos:** lista de Clinical Events (não é Registry
  — é catálogo extensível).
- **Relação:** governa Semantic Identity (3.13) dos objetos que
  registra.
- **Consequência para implementação:** toda referência a um
  identificador registrado **shall** carregar a versão do
  Registry sob a qual foi criada.
- **Referências cruzadas:** §3.13 Semantic Identity; §3.20
  Knowledge Evolution.

### 3.16 Explainability

> Explainability é a propriedade de um sistema de **produzir e
  referenciar justificativas** para cada afirmação significativa.

- **Motivação:** tornar o sistema auditável e responsável.
- **Responsabilidades:** acompanhar cada afirmação com
  justificação; referenciar Evidence e Hypothesis.
- **Invariantes:** obrigatória em toda Interpretation (3.11);
  não pode ser omitida.
- **Exemplos:** Explanation (Sprint 4.1), explanation_reference
  em Expression.
- **Contraexemplos:** afirmação clínica sem proveniência.
- **Relação:** required por Interpretation (3.11); produzida por
  Domain Services.
- **Consequência para implementação:** análises sem Explanation
  **shall** ser rejeitadas pelo projection handler (DLQ +
  métrica `unexplained_total`).
- **Referências cruzadas:** §3.11 Interpretation; Constituição
  Art. 9.

### 3.17 Temporality

> Temporality é a propriedade de um objeto de domínio de
> **carregar informação temporal bitemporal** (valid_time +
> transaction_time).

- **Motivação:** representar corretamente a evolução do
  conhecimento clínico, onde passado pode ser reinterpretado.
- **Responsabilidades:** carregar `valid_time`; carregar
  `transaction_time`; preservar ordenação causal.
- **Invariantes:** bitemporalidade; preservada na reconstrução.
- **Exemplos:** Trajectory points (valid_time + transaction_time).
- **Contraexemplos:** campo único `created_at` (não é
  bitemporalidade).
- **Relação:** complementa Traceability (3.18); sustenta
  Knowledge Evolution (3.20).
- **Consequência para implementação:** todo estado evolutivo
  **shall** carregar ambos os timestamps.
- **Referências cruzadas:** §3.18 Traceability; §3.20 Knowledge
  Evolution; Constituição Art. 8.

### 3.18 Traceability

> Traceability é a propriedade de um objeto de domínio de
> **carregar referência rastreável** ao Domain Event que o
> produziu.

- **Motivação:** tornar toda afirmação reconstruível a partir do
  Event Store.
- **Responsabilidades:** carregar `source_event_ids`; permitir
  auditoria completa.
- **Invariantes:** preservada em todas as camadas; obrigatória
  em Projections e Interpretations.
- **Exemplos:** `source_event_ids` em Outcome, Interpretation,
  Cohort.
- **Contraexemplos:** resultado clínico sem proveniência.
- **Relação:** implementa Explainability (3.16); complementada
  por Temporality (3.17).
- **Consequência para implementação:** todo objeto derivado
  **shall** carregar proveniência.
- **Referências cruzadas:** §3.5 Domain Event; §3.16
  Explainability; Constituição Art. 9.

### 3.19 Knowledge Representation

> Knowledge Representation é a **codificação formal** do
> conhecimento clínico, contemplando estrutura, relações,
  contexto, temporalidade, evidências e explicações.

- **Motivação:** ir além do armazenamento de dados, representando
  o **significado** dos eventos clínicos.
- **Responsabilidades:** preservar relações; preservar contexto;
  preservar temporalidade.
- **Invariantes:** representa conhecimento, não apenas dados;
  sempre reconstruível.
- **Exemplos:** Clinical Gene, Clinical Genome, Trajectory.
- **Contraexemplos:** tabela relacional sem semântica associada.
- **Relação:** domínio de aplicação do AraOS; abrange todos os
  outros conceitos.
- **Consequência para implementação:** Knowledge Representation
  **shall not** ser confundida com persistência física; é
  contrato lógico.
- **Referências cruzadas:** todos os demais conceitos;
  Constituição Art. 2.

### 3.20 Knowledge Evolution

> Knowledge Evolution é o processo contínuo de **refinamento e
  expansão** do conhecimento clínico ao longo do tempo.

- **Motivação:** capturar a natureza dinâmica, adaptativa e
  probabilística do conhecimento médico.
- **Responsabilidades:** admitir revisões; preservar histórico;
  atribuir nova confiança.
- **Invariantes:** append-only; versionada; explicável.
- **Exemplos:** Trajectory, Hypothesis refinamento, Registry
  versioning.
- **Contraexemplos:** mutação destrutiva do conhecimento
  registrado.
- **Relação:** sustentada por Temporality (3.17) e Traceability
  (3.18).
- **Consequência para implementação:** evolução **shall** ocorrer
  por Domain Events novos, não por mutação direta.
- **Referências cruzadas:** §3.5 Domain Event; §3.17
  Temporality; Constituição Art. 8.

---

## 4. Axiomas Formais (Formal Axioms)

Os axiomas a seguir fundamentam a linguagem do AraOS. Toda
implementação **shall** preservar sua validade.

### Axiom 1 — Knowledge Precedes Data

> **Knowledge precedes Data.**
>
> Toda estrutura computacional no AraOS existe para representar
> conhecimento clínico, não para acumular dados. Dados são
> consequência do conhecimento, jamais o inverso.

### Axiom 2 — Language Governs Architecture

> **Language governs Architecture.**
>
> Decisões arquiteturais decorrem da clareza semântica da
> linguagem. Onde a linguagem falha, a arquitetura falha. Onde
> a linguagem é precisa, a arquitetura torna-se natural.

### Axiom 3 — Aggregate Roots Own Their Value Objects

> **Every Aggregate Root owns its Value Objects.**
>
> Um Value Object nunca existe comoAggregate independente; sempre
> pertence ao Aggregate cujo Root o expõe. A identidade do
> Value Object **shall** ser derivada da identidade do Aggregate.

### Axiom 4 — Value Objects Have No Semantic Identity

> **Value Objects have no semantic identity.**
>
> A igualdade de um Value Object é puramente estrutural. Duas
> instâncias com os mesmos campos são indistinguíveis, ainda
> que tenham sido construídas em momentos diferentes.

### Axiom 5 — Events Modify State, Not Identity

> **Events never modify identity. They modify state.**
>
> Domain Events alteram o estado de um Aggregate (Expression,
  Trajectory, Hypothesis), jamais sua Semantic Identity.
> Identidade é permanente durante o ciclo de vida do objeto.

### Axiom 6 — Interpretations Are Projections

> **Interpretations are projections. Never canonical state.**
>
> Toda Interpretation é leitura derivada, jamais fonte de
> verdade. Nenhuma decisão clínica pode basear-se
> exclusivamente em uma Interpretation; **shall** sempre
> consultar o Canonical State.

### Axiom 7 — Canonical State Must Be Reconstructable

> **Canonical state must always be reconstructable.**
>
> O estado canônico de qualquer Aggregate **shall** ser
> reconstruível bit-identical a partir do Event Store. Esta
> propriedade **shall** ser testada por suite de conformidade
> (replay 1x / 2x / 50x / 100x, ordem aleatória).

### Axiom 8 — Single Official Definition

> **Every normative concept must have exactly one official
> definition.**
>
> Cada termo fixado por este Standard possui **uma única**
> definição canônica. Nenhum outro Standard pode redefinir,
> ampliar ou restringir o termo; apenas referenciá-lo.
> Conflitos **shall** ser resolvidos em favor do AS-000.

### Axiom 9 — Knowledge is Temporal

> **Knowledge is temporal.**
>
> Toda representação de conhecimento **shall** carregar
> informação temporal bitemporal (valid_time + transaction_time).
> Conhecimento sem temporalidade é informação incompleta.

### Axiom 10 — Knowledge is Explainable

> **Knowledge is explainable.**
>
> Toda afirmação significativa **shall** poder ser explicada
> por referência às Evidence que a sustentam. Sistema sem
> Explainability **shall not** ser publicado em produção.

### Axiom 11 — Knowledge is Probabilistic

> **Knowledge is probabilistic.**
>
> O conhecimento clínico admite graus de confiança. Confidence
> explícita (`[0.0, 1.0]`) **shall** acompanhar toda Expression
> e toda Interpretation.

### Axiom 12 — Hypotheses Coexist

> **Hypotheses coexist.**
>
> Múltiplas Hypothesis podem coexistir sobre o mesmo objeto.
> Nenhuma Hypothesis **shall** suprimir outra por sobrescrita.
> Resolução **shall** ocorrer por Evidence nova.

> **NOTA** — Axiomas são **invariantes lógicas**. Uma
> implementação que viole qualquer axioma **shall** ser declarada
> não-conforme, independentemente do atendimento a requisitos
> sintáticos.

---

## 5. Mapeamento DDD (DDD Classification)

Tabela oficial de classificação DDD dos conceitos do AraOS.
Esta tabela é **referência canônica** para qualquer
implementação.

| Conceito AraOS | Classificação DDD | Justificativa |
|---|---|---|
| **Clinical Gene** | **Aggregate Root** | Identidade estável; hospeda Expression; emite eventos do Aggregate. |
| **Clinical Expression** | **Value Object** | Igualdade estrutural; substituível integralmente; sem identidade. |
| **Clinical Genome** | **Aggregate** | Cluster de Genes de um paciente sob uma raiz. |
| **Clinical Event** | **Domain Event** | Fato passado; imutável; append-only. |
| **Clinical Interpretation** | **Projection** | Leitura derivada do estado. |
| **Clinical Context** | **Value Object** | Modulador semântico; substituível. |
| **Evidence** | **Value Object** | Item atômico; imutável; estrutural. |
| **Trajectory** | **Value Object** | Série temporal; estruturalmente igual se mesmo conteúdo. |
| **History** | **Event Log** | Audit chain; append-only; não é objeto de domínio. |
| **Clinical Identity** | **Entity** | Identidade referencial do paciente dentro do contexto clínico. |
| **Phenotype / Assessment / Intervention** | **Entity** | Objetos com ciclo de vida próprio. |
| **Cohort** | **Entity / Aggregate** | Cluster de pacientes definidos por critérios. |
| **Explanation** | **Value Object** | Justificativa estrutural; imutável após escrita. |
| **Hypothesis** | **Value Object** | Interpretação alternativa; coexistência; estrutural. |
| **Registry Version** | **Value Object** | Marcador SemVer; imutável. |

> **NOTA** — Esta tabela é **orientativa** e pode ser ampliada
> em futuras versões deste Standard mediante justificativa
> arquitetural.

---

## 6. Requisitos Normativos

Esta seção fixa as regras que regem o uso da linguagem do
AraOS. Todo AraOS Standard **shall** observar estes requisitos.

### 6.1 Proibição de Redefinição

> **Requisito 6.1.1** — Nenhum AraOS Standard,Paper, ADR ou
> implementação **shall** redefinir, ampliar ou restringir
> qualquer termo fixado em §3 deste Standard.
>
> **Requisito 6.1.2** — Quando um Standard necessitar de um
> termo cujo significado esteja fixado por este AS, **shall**
> referenciar este AS pelo identificador (AS-000) e seção (§3.X).

### 6.2 Uso Obrigatório dos Termos Canônicos

> **Requisito 6.2.1** — Todo AraOS Standard **shall** utilizar
> exclusivamente os termos canônicos definidos em §3 para
> descrever seus conceitos.
>
> **Requisito 6.2.2** — Termos legados (ex.: *capability*) **shall
> not** ser introduzidos em novos Standards; **may** apenas
> ser referenciados como sinônimos históricos em notas
> explicativas.

### 6.3 Mapeamento DDD Obrigatório

> **Requisito 6.3.1** — Todo AraOS Standard **shall** declarar
> a classificação DDD de seus conceitos, observando a tabela
> canônica de §5 sempre que aplicável.
>
> **Requisito 6.3.2** — Divergências da tabela canônica **shall**
> ser justificadas no próprio Standard e referenciadas em ADR
> específico.

### 6.4 Axiomas Não-Negociáveis

> **Requisito 6.4.1** — Todo AraOS Standard **shall not** violar
> nenhum dos axiomas definidos em §4.
>
> **Requisito 6.4.2** — Toda aparente violação de axioma **shall**
> ser registrada como erro arquitetural e resultar em ADR de
> revisão.

### 6.5 Conformidade Cross-Standard

> **Requisito 6.5.1** — A combinação de dois ou mais AraOS
> Standards **shall** preservar a coerência semântica dos
> termos compartilhados.
>
> **Requisito 6.5.2** — Em caso de divergência entre Standards,
> prevalecerá a definição deste AS (AS-000).

### 6.6 Versionamento da Linguagem

> **Requisito 6.6.1** — Mudanças incompatíveis nos termos
> canônicos **shall** produzir nova versão major (SemVer) deste
> AS.
>
> **Requisito 6.6.2** — Adições retrocompatíveis (novos termos)
> **may** produzir versão minor.
>
> **Requisito 6.6.3** — Correções editoriais ou clarificações
> **may** produzir versão patch.

---

## 7. Compliance Levels (Níveis de Conformidade)

Uma implementação ou AraOS Standard pode declarar conformidade
em **três níveis cumulativos**:

| Nível | Nome | Requisitos | Caso de Uso |
|---|---|---|---|
| **0** | **Vocabulary-Conformant** | Utiliza os termos canônicos de §3 com o significado oficial. | Documentação e nomenclatura. |
| **1** | **Axiom-Conformant** | **0** + respeita todos os axiomas de §4. | Modelagem e design. |
| **2** | **Full AraOS Language Compliance** | **1** + mapeia conceitos ao DDD conforme §5 + respeita os requisitos de §6. | Implementação e revisão por pares. |

> **Requisito 7.1** — Todo AraOS Standard **shall** declarar
> o nível de conformidade reivindicado na seção "Compliance".
>
> **Requisito 7.2** — Conformidade em nível **N** **shall**
> implicar conformidade em todos os níveis inferiores.

---

## 8. Hierarquia Canônica

```
Constituição do AraOS (Lex AraOS)        ← Lei suprema do domínio
        ↓
AS-000 — AraOS Language Specification    ← Gramática oficial (este Standard)
        ↓
AS-001 — Clinical Gene Standard          ← First Domain Standard
        ↓
AS-002 — Clinical Expression Standard    ← Value Object do Gene
        ↓
AS-003 — Clinical Genome Standard        ← Aggregate (cluster de Genes)
        ↓
AS-004 — Clinical Inference Standard
        ↓
AS-005 — Clinical Interpretation Standard
        ↓
AS-006 — Clinical Context Standard
        ↓
Implementação (código + testes)
```

> **Requisito 8.1** — Standards publicados em posição inferior
> **shall** referenciar e respeitar os termos deste Standard.
>
> **Requisito 8.2** — Standards publicados em posição superior
> **shall not** existir; este Standard é o topo da pilha técnica.

---

## 9. Conformidade com a Constituição

Este Standard observa integralmente a Constituição do AraOS. Em
particular:

- Artigo 1 — O Domínio governa a Tecnologia.
- Artigo 2 — O Conhecimento precede os Dados.
- Artigo 4 — A Linguagem é o Principal Ativo.
- Artigo 8 — Todo Conhecimento é Temporal.
- Artigo 9 — Explicabilidade é Obrigatória.
- Artigo 16 — O Conhecimento é Versionado.
- Artigo 18 — Princípio da Coerência.
- Artigo 19 — Princípio da Simplicidade Conceitual.

Em caso de conflito, a Constituição prevalece.

---

## Apêndice A — Glossário de Referência Rápida

| Termo | Definição Resumida | § |
|---|---|---|
| **Entity** | Objeto distinguível por identidade referencial. | 3.1 |
| **Value Object** | Objeto sem identidade, com igualdade estrutural. | 3.2 |
| **Aggregate** | Cluster de Entities + VOs sob um Root. | 3.3 |
| **Aggregate Root** | Entity ponto de entrada do Aggregate. | 3.4 |
| **Domain Event** | Fato passado relevante ao domínio. | 3.5 |
| **Projection** | Estado derivado, rebuildable. | 3.6 |
| **Evidence** | Item atômico de sustentação. | 3.7 |
| **Context** | Modulador semântico do estado. | 3.8 |
| **Canonical State** | Estado primário de verdade. | 3.9 |
| **Derived State** | Estado calculado a partir do canonical. | 3.10 |
| **Interpretation** | Leitura atual do estado. | 3.11 |
| **Hypothesis** | Interpretação alternativa concorrente. | 3.12 |
| **Semantic Identity** | Identidade semântica estável no tempo. | 3.13 |
| **Clinical Function** | Função semântica associada, não-identidade. | 3.14 |
| **Registry** | Catálogo versionado de identificadores válidos. | 3.15 |
| **Explainability** | Capacidade de justificar afirmações. | 3.16 |
| **Temporality** | Bitemporalidade (valid + transaction time). | 3.17 |
| **Traceability** | Proveniência rastreável ao Domain Event. | 3.18 |
| **Knowledge Representation** | Codificação formal do conhecimento. | 3.19 |
| **Knowledge Evolution** | Refinamento contínuo do conhecimento. | 3.20 |

---

## Apêndice B — Dependency Graph

```
                  ┌─────────────────────────┐
                  │   Lex AraOS             │
                  │   (Constituição v1.0)   │
                  └────────────┬────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   AS-000                │
                  │   AraOS Language Spec   │
                  └────────────┬────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────────┐
        │ AS-001   │    │ AS-002   │    │ Implementação│
        │  Gene    │───▶│Expression│───▶│ AS-001+AS-002│
        └──────────┘    └──────────┘    └──────┬───────┘
              │                │               │
              │       ┌────────┼────────┐     │
              ▼       ▼        ▼        ▼     │
        ┌──────────┐ ┌────────┐ ┌────────┐    │
        │ AS-004   │ │AS-005  │ │AS-006  │    │
        │Inference │ │Interpr.│ │Context │    │
        └──────────┘ └────────┘ └────────┘    │
                               │              │
                               │   (aprendizado operacional)
                               ▼              ▼
                          ┌────────────────────┐
                          │   AS-003           │
                          │   Clinical Genome  │
                          │   (escrito após    │
                          │    implementação)  │
                          └────────────────────┘
                               │
                               ▼
                  ┌─────────────────────────┐
                  │   Implementação        │
                  │   (código + testes)     │
                  └─────────────────────────┘
```

> **NOTA** — AS-003 é deliberadamente posicionado **após** a
> primeira implementação concreta de AS-001 (Aggregate Root) e
> AS-002 (Value Object). A teoria do Genome reflete a prática
> operacional, evitando especular arquitetura sem evidência.

---

## Apêndice C — Mapeamento para Fontes Normativas

| Conceito | Paper | Constituição | ADR | AS Relacionado |
|---|---|---|---|---|
| Entity (§3.1) | — | — | — | AS-001 (uso) |
| Value Object (§3.2) | Paper IV §3 | Art. 4 | ADR-0005 | AS-002 (Expression) |
| Aggregate (§3.3) | Paper III §5 | — | ADR-0005 | AS-003 (Genome) |
| Aggregate Root (§3.4) | Paper III §3 | Art. 5 | ADR-0005 | AS-001 (Gene) |
| Domain Event (§3.5) | Paper II Cap. 7 | Art. 7 | ADR-0001 | — |
| Projection (§3.6) | Paper II Cap. 5 | Art. 8 | ADR-0001 | — |
| Evidence (§3.7) | Paper V §6 | Art. 11 | — | — |
| Context (§3.8) | Paper IV §8 | Art. 10 | ADR-0003 | AS-006 |
| Canonical State (§3.9) | Paper II Cap. 3 | Art. 2 | ADR-0001 | — |
| Derived State (§3.10) | Paper II Cap. 5 | Art. 2 | — | — |
| Interpretation (§3.11) | Paper VI §3 | Art. 9 | — | AS-005 |
| Hypothesis (§3.12) | Paper VI §4 | Art. 15 | — | — |
| Semantic Identity (§3.13) | Paper III §4 | Art. 5 | ADR-0005 | AS-001 |
| Clinical Function (§3.14) | Paper III §3 | Art. 4 | ADR-0005 | AS-001 |
| Registry (§3.15) | Paper III §4 | Art. 13 | ADR-0005 | AS-001 |
| Explainability (§3.16) | Paper IV §9 | Art. 9 | ADR-0001 | — |
| Temporality (§3.17) | Paper II Cap. 3 | Art. 8 | ADR-0001 | — |
| Traceability (§3.18) | Paper V §8 | Art. 9 | ADR-0001 | — |
| Knowledge Representation (§3.19) | Paper II | Art. 2 | — | — |
| Knowledge Evolution (§3.20) | Paper II Cap. 5 | Art. 8 | ADR-0001 | — |

---

## Apêndice D — Requisitos de Conformidade

Um novo AraOS Standard é considerado **compatível com a
linguagem oficial do AraOS** quando:

1. **D1** — Utiliza exclusivamente os termos canônicos
   definidos em §3, sem redefinição.
2. **D2** — Respeita todos os axiomas de §4.
3. **D3** — Declara classificação DDD de seus conceitos
   conforme tabela de §5.
4. **D4** — Referencia este Standard pelo identificador
   `AS-000` na seção "Fontes Normativas".
5. **D5** — Mapeia seus conceitos para Constitution/Papers/ADRs
   (Apêndice C como modelo).
6. **D6** — Declara o nível de conformidade Language Compliance
   (Vocabulary / Axiom / Full) conforme §7.
7. **D7** — Inclui matriz de testes rastreáveis por requisito
   (mesmo que os testes ainda não existam).
8. **D8** — Não contradiz este Standard em nenhuma cláusula.

> **Requisito D.1** — Standards não conformes **shall not** ser
> marcados como Published no AraOS Library.

---

## Apêndice E — Histórico de Versões

| Versão | Data | Mudança | Status |
|---|---|---|---|
| 1.0 | 2026-07-17 | Emissão inicial | Draft |

---

## Apêndice F — Nota Editorial sobre Sequência de Publicação

> **Sequência revisada em 2026-07-17 após decisão arquitetural.**

O AS-003 (Clinical Genome) **shall not** ser publicado antes da
primeira implementação concreta e testada do Aggregate Root
(AS-001) e da Expression (AS-002).

**Justificativa:** a teoria do Genome como Aggregate que agrega
múltiplos Genes **deve** ser informada pela experiência
operacional de ter escrito e exercitado um Gene real + uma
Expression real. Publicar o AS-003 antes da implementação
convidaria a especular arquitetura sem evidência.

**Sequência revisada:**

1. AS-001 (Gene) → Aceito ✅
2. AS-002 (Expression) → próximo
3. **Implementação concreta** de Gene + Expression com testes
   ≥ 95% coverage
4. AS-003 (Genome) → **somente após** o item 3
5. AS-004 / AS-005 / AS-006 → após AS-003

Esta decisão **não** altera nenhuma cláusula normativa deste
Standard; ela governa apenas o **roteiro editorial** da AraOS
Library.

---

## Aviso Final

> Este AraOS Standard define a **gramática oficial** do AraOS.
>
> Após sua aprovação, nenhum AraOS Standard **shall** redefinir,
> ampliar ou restringir qualquer termo aqui fixado; apenas
> **referenciá-lo**.
>
> Em caso de dúvida durante a redação de qualquer AS:
>
> *"Este termo canônico está definido em AS-000 §3.X?"*
>
> Se **sim** → **shall** referenciar AS-000, não redefinir.
> Se **não** → **may** definir localmente, mas **shall**
> propor a inclusão em AS-000 na próxima versão minor.

> Este é o **padrão de padrões** do AraOS. Cuide dele com o
> mesmo rigor da Constituição.