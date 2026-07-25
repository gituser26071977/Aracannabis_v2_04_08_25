# AS-002 — AraOS Standard 002: Clinical Expression Standard

> **Status:** Draft
> **Versão:** 1.0
> **Data:** 2026-07-17
> **Tipo:** AraOS Standard (Normativo)
> **Autoria:** AraOS Architecture
> **Substitui:** nenhum documento (primeira emissão)

| Campo | Valor |
|---|---|
| **Identificador** | AS-002 |
| **Título** | Clinical Expression Standard |
| **Categoria** | Clinical Knowledge Representation |
| **Status** | Normative |
| **Maturity** | Draft |
| **Versão** | 1.0 |
| **Data de emissão** | 2026-07-17 |
| **Próxima revisão prevista** | após primeira implementação concreta do ClinicalGene AR |
| **Norma superior** | Constituição do AraOS v1.0 (Lex AraOS) |
| **Gramática oficial** | AS-000 §3 (termos canônicos) |
| **ADR governante** | ADR-0005 (ACCEPTED) |
| **Paper governante** | Paper IV — A Teoria da Expressão Clínica |
| **Persistent Identifier** | `urn:araos:standard:002:1.0` |
| **Estado editorial** | Draft (ver §6 da AraOS Library README) |
| **Posição hierárquica** | Logo abaixo de AS-000; acima de implementações de Expression |

## Fontes Normativas Obrigatórias

Este AraOS Standard é derivado e materializa as seguintes fontes,
**utilizando exclusivamente a gramática oficial fixada por AS-000**:

| Fonte | Status | Papel |
|---|---|---|
| **Manifesto do AraOS** | Manifesto v0.1 | Princípio fundacional |
| **Constituição do AraOS (Lex AraOS)** | Constituição v1.0, 17/07/2026 | Lei suprema do domínio |
| **Paper II — The Nature of Clinical Knowledge** | Paper II | Distinção informação × conhecimento |
| **Paper III — Clinical Genome** | Paper III | Origem do Clinical Gene hospedeiro |
| **Paper IV — A Teoria da Expressão Clínica** | Paper IV | Teoria da Expression |
| **ADR-0005 — Sprint 4.3 Clinical Genome Engine** | ADR-0005 (ACCEPTED) | Decisão arquitetural canônica |
| **AS-000 — AraOS Language Specification** | AS-000 v1.0 (Draft) | Gramática oficial |
| **AS-001 — Clinical Gene Standard** | AS-001 v1.0 (Published) | Hospedeiro da Expression |

Em caso de conflito, prevalece a **Constituição do AraOS** (Lex AraOS).
Em caso de ambiguidade terminológica, prevalece a redação do **AS-000**.

---

## Prefácio

O AraOS (Knowledge Infrastructure for Clinical Reasoning) é uma
infraestrutura computacional para **representação, evolução,
inferência e interpretação do conhecimento clínico**.

O **Clinical Gene** (AS-001) representa uma Função Clínica
Fundamental cuja identidade permanece semanticamente estável ao
longo do tempo. A **Clinical Expression** — definida por este
Standard — representa o **estado observável** desse Gene em um
determinado instante.

> **Este Standard (AS-002) responde a uma única pergunta:**
>
> ***"Como um Clinical Gene se torna observável?"***

Toda a modelagem subsequente decorre dessa pergunta. A Expression
é a **interface observável** entre o conhecimento durável
(Gene) e o julgamento clínico humano.

Este documento **não** redefine o Clinical Gene, o Clinical
Genome, o Inference Engine, o Knowledge Graph, o Rule Engine
ou o Projection Engine. Esses pertencem a outros Standards.
Toda a terminologia aqui empregada é **herdada da gramática
oficial do AS-000** (§3) e referenciada explicitamente.

---

## Design Goals (Objetivos de Design)

Este Standard foi concebido para satisfazer os seguintes
objetivos de design:

| # | Goal | Materializa |
|---|---|---|
| 1 | **Observable State** — tornar o Gene observável sem expor sua estrutura interna. | AS-001 §6.1, AS-000 §3.9 |
| 2 | **Replaceability** — toda Expression pode ser substituída integralmente. | AS-000 §3.2, Axiom 4 |
| 3 | **Temporal Awareness** — toda Expression carrega bitemporalidade. | AS-000 §3.17, Axiom 9 |
| 4 | **Contextual Sensitivity** — toda Expression registra dependências de contexto. | AS-000 §3.8 |
| 5 | **Confidence Always Explicit** — Confidence nunca é omitida. | AS-000 Axiom 11 |
| 6 | **Reconstructability** — toda Expression pode ser reconstruída do Event Store. | AS-000 §3.9, Axiom 7 |
| 7 | **Explainability Native** — toda Expression referencia Explanation. | AS-000 §3.16, Axiom 10 |
| 8 | **Hypothesis Coexistence** — múltiplas Hypothesis sobre o mesmo Gene convivem. | AS-000 §3.12, Axiom 12 |
| 9 | **Knowledge Probabilistic** — Confidence no intervalo `[0.0, 1.0]`. | AS-000 Axiom 11 |
| 10 | **Grammar Consistency** — terminologia 100% consistente com AS-000. | AS-000 §6.1 |

> **NOTA** — Toda referência a um conceito canônico do AraOS
> neste documento **shall** referenciar AS-000 §3.X
> explicitamente. Ver Apêndice C.

---

## Non-Goals (Fora do Escopo)

Este Standard **deliberadamente não define**:

| # | Item | Razão |
|---|---|---|
| 1 | **Clinical Gene** | definido no AS-001. |
| 2 | **Clinical Genome** | definido no AS-003 (futuro, pós-implementação). |
| 3 | **Algoritmos de inferência** | definidos no AS-004 (Clinical Inference). |
| 4 | **Knowledge Graph** | decisão arquitetural; fora do escopo deste Standard. |
| 5 | **Rule Engine** | decisão arquitetural; fora do escopo. |
| 6 | **Projection Engine** | responsabilidade do read-model layer. |
| 7 | **Storage engine** | decisão técnica (ADR-0001, livre escolha). |
| 8 | **UI** | decisão arquitetural. |
| 9 | **Diagnóstico clínico** | proibido constitucionalmente (Art. 17). |
| 10 | **Padrões de Machine Learning** | proibidos como entrada diagnóstica. |

> **NOTA** — Toda interpretação futura deste Standard **shall
> not** estender seu escopo a itens desta lista sem revisão
> explícita em ADR, seguida de nova versão SemVer major.

---

## 1. Escopo

Este AraOS Standard define exclusivamente o **Value Object
normativo Clinical Expression** e seus componentes canônicos.

Em particular:

1. A natureza de Value Object da Expression.
2. Os 17 conceitos que compõem a Expression.
3. As invariantes SHALL que toda Expression deve respeitar.
4. O modelo computacional de produção, substituição,
   reconstrução e comparação de Expressions.
5. O mapeamento DDD definitivo (Value Object × Aggregate Root).
6. Os critérios de conformidade para qualquer implementação.

**Fora do escopo** (definidos em outros Standards):

- Hospedeiro (Clinical Gene) → **AS-001**.
- Coleção (Clinical Genome) → **AS-003** (futuro).
- Inferência que produz Expression → **AS-004** (futuro).
- Interpretação da Expression → **AS-005** (futuro).
- Clinical Context modulador → **AS-006** (ADR-0003).
- Gramática oficial → **AS-000**.

---

## 2. Referências Normativas

Os documentos a seguir são indispensáveis para a aplicação
deste Standard. Para referências datadas, aplica-se somente a
edição citada.

- **Constituição do AraOS**, versão 1.0, 17 de julho de 2026.
- **Manifesto do AraOS**, versão 0.1 — A Fundação.
- **Paper II — The Nature of Clinical Knowledge**.
- **Paper III — Clinical Genome**.
- **Paper IV — A Teoria da Expressão Clínica**.
- **ADR-0001 — Clinical Event Engine**.
- **ADR-0005 — Clinical Genome Engine**, ACCEPTED.
- **AS-000 — AraOS Language Specification v1.0**.
- **AS-001 — Clinical Gene Standard v1.0**, Published.

---

## 3. Termos e Definições

> **NOTA** — Todo termo arquitetural utilizado neste Standard
> (Entity, Value Object, Aggregate Root, Domain Event,
> Projection, Evidence, Context, Canonical State, Derived
> State, Interpretation, Hypothesis, Semantic Identity,
> Clinical Function, Registry, Explainability, Temporality,
> Traceability, Knowledge Representation, Knowledge Evolution)
> **shall** ter seu significado oficial consultado em **AS-000
> §3**. Este Standard **shall not** redefinir nenhum desses
> termos.

Os termos **específicos da Clinical Expression** são definidos
a seguir. Cada definição referencia explicitamente os conceitos
canônicos de AS-000 quando aplicável.

### 3.1 Clinical Expression

> **Clinical Expression é o Value Object (AS-000 §3.2) que
> representa o estado observável de um Clinical Gene (AS-001) em
> um determinado instante, carregando Observed Value, Confidence,
> Trend, Volatility e referências a Evidence, Context,
> Interpretation e Explanation.**

- **Natureza DDD:** Value Object (AS-000 §3.2).
- **Hospedeiro:** Aggregate Root Clinical Gene (AS-000 §3.4,
  AS-001 §3.1).
- **Motivação:** tornar o Gene observável sem expor sua
  estrutura interna; produzir leitura atual do estado.
- **Responsabilidades:** carregar estado observável; referenciar
  Evidence; referenciar Explanation.
- **Invariantes:** §4 deste Standard.
- **Contraexemplos:** Clinical Gene (não é Expression — é
  Aggregate Root).

### 3.2 Expression State

> **Expression State é o conjunto de campos observáveis que
> constituem o conteúdo da Clinical Expression em um instante.**

Inclui: Observed Value, Confidence, Trend, Volatility, Last
Update, Valid Time, Transaction Time e Unknown State.

### 3.3 Observed Value

> **Observed Value é o valor quantitativo ou qualitativo que
> representa o estado observado do Gene em um instante.**

- **Tipo:** numérico (`float`), ordinal, categórico ou textual.
- **Invariante:** **shall** sempre estar presente, mesmo quando
  igual a `null` ou marcador de Unknown State (§3.14).

### 3.4 Confidence

> **Confidence é o grau de certeza `[0.0, 1.0]` associado ao
> Observed Value, indicando a confiança do sistema na
> observação.**

- **Intervalo:** `[0.0, 1.0]` (fechado).
- **Invariante:** **shall** ser sempre explícita. Ausência
  equivale a `0.0` e **shall** ser registrada como tal.
- **Natureza:** derivada (AS-000 Axiom 11), não primária.

### 3.5 Trend

> **Trend é a direção observada da variação do Observed Value
> ao longo de uma janela temporal.**

- **Valores permitidos:**
  `improving` · `stable` · `declining` · `oscillating` ·
  `unknown`.
- **Invariante:** **shall** pertencer ao conjunto enumerado.

### 3.6 Volatility

> **Volatility é a magnitude da variação do Observed Value em
> uma janela temporal, normalizada para fins de comparação.**

- **Valores permitidos:** `low` · `medium` · `high` ·
  `unknown`.
- **Invariante:** **shall** pertencer ao conjunto enumerado.

### 3.7 Clinical Interpretation Reference

> **Clinical Interpretation Reference é a referência à Clinical
> Interpretation (AS-000 §3.11) que produziu leitura sobre o
> estado atual da Expression.**

- **Cardinalidade:** `0..1` (pode ser ausente antes da primeira
  interpretação).
- **Invariante:** quando presente, **shall** referenciar
  Interpretation Published no AraOS.

### 3.8 Explanation Reference

> **Explanation Reference é a referência à Explanation que
> justifica o estado atual da Expression.**

- **Cardinalidade:** `1` (obrigatória, AS-000 §3.16, Axiom 10).
- **Invariante:** **shall** sempre existir; nunca nula.
- **Sem Explanation, não há Expression publicável.**

### 3.9 Evidence References

> **Evidence References é a lista de identificadores de
> Domain Events (AS-000 §3.5) que fundamentam o Observed Value.**

- **Cardinalidade:** `1..*` (ao menos uma evidência).
- **Invariante:** **shall** ser append-only; **shall not** ser
  reduzida após escrita (AS-000 Axiom 8).

### 3.10 Context References

> **Context References é a lista de identificadores de Clinical
> Contexts (AS-000 §3.8, AS-006) que modularam o estado atual.**

- **Cardinalidade:** `0..*`.
- **Invariante:** **shall** referenciar Contexts válidos no
  escopo `(tenant_id, patient_id)`.

### 3.11 Last Update

> **Last Update é o timestamp (UTC) que registra o momento
> lógico da última substituição da Expression.**

- **Invariante:** **shall** ser timezone-aware (UTC).

### 3.12 Valid Time

> **Valid Time é o instante em que a mudança do Gene foi
> clinicamente relevante.**

- **Relação:** complementa Transaction Time (§3.13) para
  formar bitemporalidade (AS-000 §3.17).
- **Invariante:** **shall** ser timezone-aware (UTC).

### 3.13 Transaction Time

> **Transaction Time é o instante em que o sistema registrou a
> Expression no Event Store.**

- **Invariante:** **shall** ser timezone-aware (UTC); **shall
  not** ser anterior a Valid Time no fluxo normal.

### 3.14 Unknown State

> **Unknown State é o estado explícito da Expression quando o
> Gene é observado mas as evidências são insuficientes para
> inferir valor.**

- **Representação canônica:** `observed_value = null`,
  `confidence = 0.0`, `trend = "unknown"`,
  `volatility = "unknown"`.
- **Invariante:** **shall** ser distinguível de Unavailable State
  (§3.15).

### 3.15 Unavailable State

> **Unavailable State é o estado explícito da Expression quando
> o Gene deixou de ser observado por mudança de contexto ou
> retirada de acompanhamento.**

- **Representação canônica:** Expression ausente do Aggregate
  Root (Gene passa a estado `not_observed`).
- **Diferença semântica:** Unknown = observado sem evidência;
  Unavailable = não-observado.

### 3.16 Derived State

> **Derived State é o estado da Expression calculado a partir de
> Canonical State (AS-000 §3.9) por meio de leitura especializada.**

- **Mapeamento:** Derived State **is-a** Expression; nunca é
  source of truth (AS-000 §3.10).

### 3.17 Canonical Expression

> **Canonical Expression é a Expression que reside no Aggregate
> Root (Clinical Gene) e representa o estado canônico
> observável do Gene no presente.**

- **Cardinalidade:** exatamente **1** por Gene.
- **Mapeamento:** Canonical Expression **is-a** Expression
  current; reside no Aggregate Root (AS-000 §3.4).

---

## 4. Invariantes (Requisitos Normativos)

> **Os requisitos abaixo são obrigatórios** (`SHALL`). Uma
> Expression que viole qualquer invariante **shall** ser
> rejeitada pelo projection handler e **shall** ser registrada
> como falha na métrica `expression_violations_total`.

### 4.1 Identidade e Pertinência

> **Requisito 4.1.1** — Expression **shall** sempre referenciar
> exatamente um Clinical Gene (AS-000 §3.4, Axiom 3).
>
> **Requisito 4.1.2** — Expression **shall** never possess
> semantic identity (AS-000 §3.13, Axiom 4). Igualdade é
> puramente estrutural.
>
> **Requisito 4.1.3** — Expression **shall** never exist detached
> from a Clinical Gene (AS-000 Axiom 3).
>
> **Requisito 4.1.4** — Expression **shall not** possuir campo
> `id` próprio. Identificação ocorre exclusivamente via
> `(tenant_id, patient_id, clinical_gene_id, valid_time)`.

### 4.2 Conteúdo Mínimo

> **Requisito 4.2.1** — Expression **shall** always possess
> explicit Confidence (AS-000 Axiom 11) no intervalo
> `[0.0, 1.0]`.
>
> **Requisito 4.2.2** — Expression **shall** always carry
> Observed Value (mesmo que `null` em Unknown State).
>
> **Requisito 4.2.3** — Expression **shall** always carry Trend e
> Volatility pertencentes aos conjuntos enumerados em §3.5 e
> §3.6.
>
> **Requisito 4.2.4** — Expression **shall** always carry Last
> Update, Valid Time e Transaction Time timezone-aware (UTC).

### 4.3 Explicabilidade e Evidência

> **Requisito 4.3.1** — Expression **shall** always preserve
> Explainability (AS-000 §3.16, Axiom 10). Explanation Reference
> **shall** nunca ser vazio.
>
> **Requisito 4.3.2** — Expression **shall** always carry Evidence
> References não-vazio, com `1..*` Domain Events (AS-000 §3.5).
>
> **Requisito 4.3.3** — Expression **shall** always be
> reconstructable (AS-000 Axiom 7) a partir do Event Store.

### 4.4 Temporalidade

> **Requisito 4.4.1** — Expression **shall** be temporal
> (AS-000 §3.17, Axiom 9). Bitemporalidade é obrigatória
> (Valid Time + Transaction Time).
>
> **Requisito 4.4.2** — Transaction Time **shall not** ser
> anterior a Valid Time no fluxo normal (sem retroação
> artificial).
>
> **Requisito 4.4.3** — Substituição de Expression **shall**
> preservar a Expression anterior na Trajectory (AS-001 §6.2)
> como Expression Snapshot imutável.

### 4.5 Contextualidade

> **Requisito 4.5.1** — Expression **shall** be contextual
> (AS-000 §3.8). Context References **shall** referenciar
> apenas Clinical Contexts válidos no escopo do Gene.
>
> **Requisito 4.5.2** — Mudança em qualquer Context Reference
> **shall** disparar reavaliação da Expression (AS-004).

### 4.6 Imutabilidade

> **Requisito 4.6.1** — Expression **shall** be immutable after
> publication (AS-000 §3.2). Mutações produzem **nova**
> Expression que substitui a anterior.
>
> **Requisito 4.6.2** — Events **shall** replace Expressions
> (AS-000 Axiom 5). Events **shall** never mutate previous
> Expressions.
>
> **Requisito 4.6.3** — New state **shall** create a new
> Expression snapshot na Trajectory.

### 4.7 Comparação e Igualdade

> **Requisito 4.7.1** — Expression equality **shall** be
> structural (AS-000 Axiom 4): dois Value Objects com os mesmos
> campos são indistinguíveis.
>
> **Requisito 4.7.2** — Comparison **shall** ser canônica e
> determinística para qualquer par de Expressions no mesmo Gene.

### 4.8 Trajetória e Histórico

> **Requisito 4.8.1** — Toda Expression publicada **shall** ser
> acrescentada à Trajectory do Gene (AS-001 §6.2) como snapshot
> imutável.
>
> **Requisito 4.8.2** — Trajectory **shall** be append-only
> (AS-001 Requisito 6.2.1). Nenhuma operação **may** remover,
> sobrescrever ou reordenar snapshots históricos.

### 4.9 Interação com Hipóteses

> **Requisito 4.9.1** — Expression **shall** admitir múltiplas
> Hypothesis concorrentes (AS-000 §3.12, Axiom 12) sem
> exclusividade.
>
> **Requisito 4.9.2** — Hypothesis **shall** never substituir
> Expression diretamente. Resolução **shall** ocorrer por nova
> Evidence (novo Domain Event).

---

## 5. Formal Axioms (Axiomas Formais)

Os axiomas a seguir fundamentam a Clinical Expression como
**Value Object normativo** do AraOS.

### Axiom 1 — Expression is a Value Object

> **Clinical Expressions are Value Objects.**
>
> Pertencem ao Aggregate Root Clinical Gene (AS-000 §3.2,
> §3.4). Possuem igualdade estrutural (Axiom 4) e não carregam
> identidade semântica.

### Axiom 2 — Expression has no Identity

> **Clinical Expressions have no identity.**
>
> Dois Value Objects com os mesmos campos são indistinguíveis.
> Identificação de uma Expression **shall** ocorrer via
> `(tenant_id, patient_id, clinical_gene_id, valid_time)`.

### Axiom 3 — Expression is Temporal

> **Clinical Expressions are temporal.**
>
> Toda Expression **shall** carregar bitemporalidade
> (Valid Time + Transaction Time) conforme AS-000 §3.17.

### Axiom 4 — Expression is Contextual

> **Clinical Expressions are contextual.**
>
> Toda Expression referencia os Clinical Contexts que a
> modularam. Remoção de um Context **shall** disparar
> reavaliação (AS-004).

### Axiom 5 — Expression is Derived from Evidence

> **Clinical Expressions are derived from Evidence.**
>
> Origem exclusiva de uma Expression é o conjunto de Domain
> Events que a sustentam (AS-000 §3.5, §3.7).

### Axiom 6 — Expression is Explainable

> **Clinical Expressions are explainable.**
>
> Toda Expression **shall** carregar Explanation Reference não
> vazio. Sem Explanation, não há Expression publicável.

### Axiom 7 — Expression is Reconstructable

> **Clinical Expressions are reconstructable.**
>
> O estado de qualquer Expression pode ser reconstruído
> bit-identical a partir do Event Store (AS-000 Axiom 7).

### Axiom 8 — Expression is a Projection of Observable State

> **Clinical Expressions are projections of observable state.**
>
> Expression **is-a** Projection (AS-000 §3.6). Nunca é
> canonical state; é leitura derivada do Gene.

### Axiom 9 — Expression never Owns Knowledge

> **Clinical Expressions never own knowledge.**
>
> Conhecimento é de propriedade do Aggregate Root Clinical Gene.
> Expression é apenas sua leitura observável.

### Axiom 10 — Expression Represents Knowledge

> **Clinical Expressions represent knowledge.**
>
> Embora não possuam identidade, Expressions são a forma
> canônica pela qual o conhecimento clínico se torna
> acessível ao julgamento humano.

> **NOTA** — Axiomas 9 e 10 formam par dialético: Expression
> não possui conhecimento (Ax. 9), mas **representa** o
> conhecimento do Gene hospedeiro (Ax. 10). Esta tensão é
> resolvida pela substituição: cada nova Expression é nova
> **representação** do mesmo conhecimento subjacente.

---

## 6. Modelo Computacional

Esta seção define os 10 elementos formais do modelo
computacional da Expression.

### 6.1 Current Expression

> **Current Expression** é a Canonical Expression (§3.17)
> atualmente residente no Aggregate Root Clinical Gene.

Propriedades:

- **Cardinalidade:** exatamente 1 por Gene.
- **Substituível:** integralmente a cada Domain Event relevante.
- **Persistência:** reside no Aggregate Root.

### 6.2 Historical Expression

> **Historical Expression** é qualquer Expression que já foi
> Current Expression em momento anterior.

- **Persistência:** reside na Trajectory (AS-001 §6.2).
- **Acesso:** read-only.

### 6.3 Expression Snapshot

> **Expression Snapshot** é a forma serializada e imutável de
> uma Expression em um instante específico.

- **Invariante:** **shall** ser byte-equivalente em qualquer
  serialização subsequente.
- **Uso:** persistência, audit, replay.

### 6.4 Expression Timeline

> **Expression Timeline** é a sequência ordenada por Valid Time
> ascendente de Expression Snapshots para um Gene.

- **Operação:** append-only.
- **Cardinalidade:** `0..*` por Gene (zero antes da primeira
  observação).

### 6.5 Expression Replacement

> **Expression Replacement** é a operação canônica de troca da
> Current Expression por uma nova Expression.

- **Trigger:** Domain Event (AS-000 §3.5).
- **Atomicidade:** substituição integral (não há merge parcial).
- **Efeito colateral:** Expression anterior **shall** ser
  preservada na Timeline como Historical Expression.

### 6.6 Expression Reconstruction

> **Expression Reconstruction** é a operação de rebuild da
> Current Expression a partir do Event Store.

- **Idempotência:** `f(f(state)) == f(state)`.
- **Ordem:** Determinística por Valid Time ascendente.

### 6.7 Expression Serialization

> **Expression Serialization** é a conversão de Expression
> Snapshot em formato transmível/estocável.

- **Determinismo:** mesma Expression → mesma serialização.
- **Estabilidade:** forward-compatible com versões anteriores do
  AS-002.

### 6.8 Expression Comparison

> **Expression Comparison** é a operação de verificar se duas
> Expressions são equivalentes.

- **Regra:** igualdade estrutural (todos os campos).

### 6.9 Expression Equality

> **Expression Equality** é a propriedade de duas Expressions
> serem indistinguíveis estruturalmente.

- **Garantia:** AS-000 Axiom 4.

### 6.10 Expression Lifecycle

> **Expression Lifecycle** é o conjunto de estados pelos quais
> uma Expression transita: **produced** → **published** →
> **replaced** → **historical**.

```
[produced] → [published (Current)]
                  │
                  ▼ (Domain Event)
              [replaced] → [historical]
```

---

## 7. Mapeamento DDD (Definitivo)

A tabela abaixo fixa **definitivamente** o mapeamento DDD dos
conceitos centrais do Clinical Genome Engine. Implementações
**shall** observar esta tabela.

| Conceito AraOS | Tipo DDD | Justificativa |
|---|---|---|
| **Clinical Gene** | **Aggregate Root** | Identidade estável; hospeda Expression; emite eventos do Aggregate (AS-001 §3.1, AS-000 §3.4). |
| **Clinical Expression** | **Value Object** | Igualdade estrutural; substituível integralmente; sem identidade (AS-000 §3.2, Axiom 1 deste Standard). |
| **Clinical Genome** | Aggregate | Cluster de Genes (a ser detalhado no AS-003, pós-implementação). |
| **Clinical Event** | Domain Event | Fato passado; imutável; append-only (AS-000 §3.5). |
| **Clinical Interpretation** | Projection | Leitura derivada do estado (AS-000 §3.11). |
| **Clinical Context** | Value Object | Modulador semântico (AS-000 §3.8). |
| **Evidence** | Value Object | Item atômico; imutável (AS-000 §3.7). |
| **Trajectory** | Value Object | Série temporal; estruturalmente igual se mesmo conteúdo (AS-000 §3.17). |
| **History** | Event Log | Audit chain append-only (AS-000 §3.18). |
| **Expression Snapshot** | Value Object | Forma serializada imutável (§6.3). |
| **Expression Timeline** | Aggregate-internal Collection | Coleção ordenada interna ao Aggregate Root. |
| **Hypothesis** | Value Object | Interpretação alternativa (AS-000 §3.12). |
| **Confidence** | Value | Decimal `[0.0, 1.0]`. |
| **Explanation Reference** | Reference (string/ULID) | Ponteiro imutável. |

> **NOTA** — Este mapeamento **shall** prevalecer até que nova
> revisão seja publicada em ADR e bump de versão deste AS.

---

## 8. Exemplos Canônicos

> **NOTA** — Os exemplos a seguir são **ilustrativos** e não
> vinculantes quanto à sintaxe de implementação. Eles ilustram
> o **comportamento normativo** exigido por este Standard.

### 8.1 Novo paciente

Gene observado pela primeira vez:

```
Expression {
  observed_value: null      # Unknown State (§3.14)
  confidence: 0.0           # Confidence explícita (Req. 4.2.1)
  trend: "unknown"
  volatility: "unknown"
  evidence_references: [E1] # primeira evidência (Req. 4.3.2)
  context_references: []    # sem contexto modulador ainda
  explanation_reference: X1  # explicação da observação inicial
  valid_time: T0            # momento clínico
  transaction_time: T0+ε    # momento do registro
  last_update: T0+ε
}
```

### 8.2 Nova evidência

Nova Evidence modifica Expression:

```
Antes:  Expression { observed_value: 0.4, confidence: 0.6, ... }
Depois: Expression { observed_value: 0.55, confidence: 0.75, ... }

Eventos: E2 adicionado a evidence_references.
Confiança recalculada. Expressão anterior preservada em Timeline.
```

### 8.3 Atualização de Expression

Substituição integral disparada por Domain Event E3:

```
Current Expression (v2) substitui Current Expression (v1).
v1 → preservada em Trajectory como Historical Expression.
v2 → nova Current Expression do Gene.
Evidence: [...E1, E2, E3].
Explanation: X2 (justifica a substituição).
```

### 8.4 Mudança de Confidence

Confiança recalculada após Evidence conflitante:

```
Expression {
  observed_value: 0.55,
  confidence: 0.50,         # diminuiu (Evidence E4 contradiz E3)
  trend: "stable",
  volatility: "medium",
  evidence_references: [...E1, E2, E3, E4],
  ...
}
```

> **NOTA** — Evidence E4 foi **adicionada**; Evidence E3 foi
> **preservada** (AS-000 Axiom 8). Confidence diminuiu porque
> o sistema integra múltiplas evidências, não porque
> "descartou" E3.

### 8.5 Mudança de Trend

Declínio observado em janela de 90 dias:

```
Expression {
  trend: "declining",
  velocity: -0.02,         # magnitude normalizada
  volatility: "high",
  ...
}
```

### 8.6 Mudança de contexto

Clinical Context C5 adicionado; reavaliação disparada:

```
Expression {
  context_references: [..., C5],   # novo contexto
  confidence: recalculada,         # novo cálculo
  ...
}
```

> Remoção de C5 no futuro **shall** disparar nova reavaliação
> (AS-004).

### 8.7 Replay

Aplicação de eventos do Event Store produz Expression idêntica
à atual:

```
Replay 1x: Expression_state_after_replay == Current Expression
Replay 2x: igual
Replay 50x: igual
Replay 100x: igual
```

> Invariante: AS-000 Axiom 7, Requisito 4.3.3.

### 8.8 Reconstrução histórica

Para uma data D no passado:

```
historical_expression_at(D):
  Expression válida em Valid Time = D
  Calculada por projection sobre Timeline truncada em D
```

---

## 9. Conformidade

### 9.1 Compliance Levels

Uma implementação declara conformidade com este Standard em
**quatro níveis cumulativos**:

| Nível | Nome | Requisitos | Caso de Uso |
|---|---|---|---|
| **E0** | **Expression-Vocabulary** | Utiliza os 17 termos canônicos (§3) com o significado oficial. | Documentação e nomenclatura. |
| **E1** | **Expression-Axiom** | **E0** + respeita todos os axiomas (§5). | Modelagem e design. |
| **E2** | **Expression-Invariants** | **E1** + observa todas as invariantes SHALL (§4). | Implementação. |
| **E3** | **Full AS-002 Compliance** | **E2** + respeita o modelo computacional (§6) + mapeamento DDD (§7). | Produção canônica. |

> **Requisito 9.1.1** — Toda implementação **shall** declarar
> o nível de conformidade reivindicado na seção "Compliance".
>
> **Requisito 9.1.2** — Conformidade em nível **N** **shall**
> implicar conformidade em todos os níveis inferiores.
>
> **Requisito 9.1.3** — Conformidade com este Standard **shall**
> pressupor conformidade com **AS-000** (gramática oficial).

### 9.2 Processo de Mudança

Mudanças neste Standard **shall** ser propostas via ADR,
seguindo a hierarquia:

```
Papers → ADR → AS-000 → AS-002 → Implementação
```

Versões deste AS seguem SemVer:

- Mudança incompatível com versão anterior → `MAJOR+1`.
- Adição retrocompatível → `MINOR+1`.
- Correção editorial → `PATCH+1`.

---

## 10. Hierarquia Canônica

```
Constituição do AraOS (Lex AraOS)        ← Lei suprema
        ↓
AS-000 — AraOS Language Specification   ← Gramática oficial
        ↓
AS-001 — Clinical Gene Standard         ← Aggregate Root
        ↓
AS-002 — Clinical Expression Standard   ← Value Object (este)
        ↓
AS-003+ demais Standards                 ← Genome, Inference, etc.
        ↓
Implementação (código + testes)
```

---

## 11. Conformidade com a Constituição

Este Standard observa integralmente a Constituição do AraOS:

- Artigo 1 — O Domínio governa a Tecnologia.
- Artigo 2 — O Conhecimento precede os Dados.
- Artigo 4 — A Linguagem é o Principal Ativo.
- Artigo 5 — O Clinical Gene é a Unidade Fundamental.
- Artigo 7 — Eventos Transformam Conhecimento.
- Artigo 8 — Todo Conhecimento é Temporal.
- Artigo 9 — Explicabilidade é Obrigatória.
- Artigo 10 — O Contexto faz Parte do Conhecimento.
- Artigo 17 — IA nunca substitui o médico.

---

## Apêndice A — Glossário de Referência Rápida

| Termo | Definição Resumida | § |
|---|---|---|
| **Clinical Expression** | Value Object que representa o estado observável do Gene. | 3.1 |
| **Expression State** | Conjunto de campos observáveis. | 3.2 |
| **Observed Value** | Valor quantitativo ou qualitativo observado. | 3.3 |
| **Confidence** | Certeza `[0.0, 1.0]` da observação. | 3.4 |
| **Trend** | improving / stable / declining / oscillating / unknown. | 3.5 |
| **Volatility** | low / medium / high / unknown. | 3.6 |
| **Clinical Interpretation Reference** | Ref. à Interpretation atual. | 3.7 |
| **Explanation Reference** | Ref. à Explanation (obrigatória). | 3.8 |
| **Evidence References** | Lista de Domain Events que fundamentam. | 3.9 |
| **Context References** | Lista de Contexts moduladores. | 3.10 |
| **Last Update** | Timestamp lógico da substituição. | 3.11 |
| **Valid Time** | Momento clínico da mudança. | 3.12 |
| **Transaction Time** | Momento do registro no Event Store. | 3.13 |
| **Unknown State** | Observado sem evidência suficiente. | 3.14 |
| **Unavailable State** | Gene não-observado. | 3.15 |
| **Derived State** | Expression calculada a partir do canonical. | 3.16 |
| **Canonical Expression** | Current Expression residente no AR. | 3.17 |

---

## Apêndice B — Dependency Graph

```
        ┌────────────────────────────┐
        │  Lex AraOS                │
        └─────────────┬─────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  AS-000 Language Spec      │
        └─────────────┬─────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  AS-001 Clinical Gene      │
        └─────────────┬─────────────┘
                      │ (Expression é VO do Gene)
                      ▼
        ┌────────────────────────────┐
        │  AS-002 Clinical           │
        │  Expression (este)         │
        └─────────────┬─────────────┘
                      │
                      ▼
        ┌────────────────────────────┐
        │  Implementação             │
        │  Gene AR + Expression VO   │
        └────────────────────────────┘
```

---

## Apêndice C — Mapeamento para AS-000 (Gramática)

Cada termo canônico utilizado neste Standard é referenciado
explicitamente a AS-000 §3:

| Termo usado neste AS | Origem canônica (AS-000) |
|---|---|
| Value Object | §3.2 |
| Aggregate Root | §3.4 |
| Domain Event | §3.5 |
| Evidence | §3.7 |
| Context | §3.8 |
| Canonical State | §3.9 |
| Derived State | §3.10 |
| Interpretation | §3.11 |
| Hypothesis | §3.12 |
| Semantic Identity | §3.13 |
| Explainability | §3.16 |
| Temporality | §3.17 |
| Traceability | §3.18 |

**Este Standard não redefine nenhum desses termos.**

---

## Apêndice D — Mapeamento para Fontes Normativas

| Cláusula deste AS | Paper | Constituição | ADR | AS |
|---|---|---|---|---|
| §3 Value Object | Paper IV §3 | Art. 4 | ADR-0005 | AS-000 §3.2 |
| §4.1 Identidade | Paper IV §2 | Art. 5 | ADR-0005 | AS-000 §3.13 |
| §4.2 Conteúdo | Paper IV §3 | — | ADR-0005 | AS-001 §6.1 |
| §4.3 Explainability | Paper IV §9 | Art. 9 | ADR-0001 | AS-000 §3.16 |
| §4.4 Temporalidade | Paper IV §6 | Art. 8 | ADR-0001 | AS-000 §3.17 |
| §4.5 Contextualidade | Paper IV §8 | Art. 10 | ADR-0003 | AS-000 §3.8 |
| §4.6 Imutabilidade | Paper IV §4 | Art. 7 | ADR-0005 | AS-000 Axiom 4 |
| §5 Axiom 5 | Paper V §6 | Art. 11 | — | AS-000 §3.5 |
| §5 Axiom 8 | Paper IV §1 | Art. 2 | — | AS-000 §3.6 |
| §6 Modelo | Paper IV §5 | Art. 7 | ADR-0001 | AS-001 §6.2 |

---

## Apêndice E — Requisitos de Conformidade

Um sistema é considerado **compatível com o AS-002** quando:

1. **C1** — Utiliza exclusivamente os termos de §3 com o
   significado oficial do AS-000.
2. **C2** — Respeita todos os axiomas de §5.
3. **C3** — Observa todos os requisitos SHALL de §4.
4. **C4** — Implementa o modelo computacional de §6.
5. **C5** — Mapeia Expression como Value Object conforme §7.
6. **C6** — Mantém cobertura de testes ≥ 95% para o módulo
   Expression.
7. **C7** — Inclui suite de replay bit-identical (1x / 2x /
   50x / 100x).
8. **C8** — Documenta divergências eventuais em ADR.

> **Requisito E.1** — Sistemas não conformes **shall not** ser
> marcados como compatíveis com o AraOS.

---

## Apêndice F — Histórico de Versões

| Versão | Data | Mudança | Status |
|---|---|---|---|
| 1.0 | 2026-07-17 | Emissão inicial | Draft |

---

## Aviso Final

> Este AraOS Standard define a Clinical Expression como
> **Value Object normativo** do AraOS — a forma canônica pela
> qual o conhecimento clínico se torna observável.
>
> Após sua aprovação, nenhuma implementação **shall** tratar
> Expression como Entity ou Aggregate. Expression é o que se
> sabe sobre um Gene no presente.
> Gene é o que se sabe sobre o paciente ao longo do tempo.
>
> Toda a terminologia deste documento é **herdada da gramática
> oficial do AS-000**. Em caso de dúvida sobre um termo,
> consultar AS-000 §3 antes de presumir significado local.

---

**Próxima transição prevista:** Draft → Review após a
implementação concreta da Expression como Value Object do
Clinical Gene (Sprint 4.3 Phase 2).