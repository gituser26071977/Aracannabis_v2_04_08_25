# 🧬 PLANO ARAOS — Evolução do SIAP para a Infraestrutura de Conhecimento Clínico

> **Data:** 04/08/2026 · **Autor:** parceria Anderson Holzwarth + agente
> **Referências:** `STATUS_DO_PROJETO.md` (estado atual) · `Documentos/AraOS`
> (constituição + 5 papers) · `ara-intake/` (produção)

---

## 1. O que temos hoje (SIAP) — em 1 página

**Um prontuário eletrônico de produção** (Flask, ~83 tabelas, ~400+ endpoints):

- Pacientes, consultas, anamneses, sintomas, dosagens, evoluções
- Exames com OCR (Tesseract), prescrições em PDF, escalas (PHQ-9, GAD-7, Beck,
  SNAP-IV)
- Agenda + Google Calendar, billing multi-provedor (Mercado Pago/Asaas/Stripe),
  planos/assinaturas
- Agentes: Dr. Anderson/LIA (WhatsApp/Telegram), CrewAI multi-agente, gateway de
  11 providers LLM
- Pacote **`araos/`** embutido (v0.8.0-alpha): Clinical Genome Engine, event
  store (hash chain), knowledge/context/explainability/timeline — **parcial, em
  grande parte não usado em produção**
- **Ara Intake** (irmão, FastAPI, **em produção**): pré-consulta
  conversacional + exames

**Dívidas conhecidas:** 3 camadas de LLM · RBAC (106 permissões sem aplicação) ·
multi-tenant com 3 mecanismos · ~100 scripts one-off · código morto auditado (20
componentes frontend + stubs araos) · repositório de conhecimento só In-Memory.

---

## 2. Aonde o AraOS quer chegar — a teoria em 1 página

A essência dos 5 papers (Constituição, Natureza, Expressão, Inferência,
Interpretação):

> **Evento clínico → modifica a Expressão de um Gene Clínico → o conjunto de
> Expressões forma o Genoma Clínico (estado canônico) → o Genoma produz
> Interpretações (hipóteses probabilísticas) → e Projeções
> (diagnóstico/prognóstico/tratamento).**

Princípios inegociáveis (da Constituição):

1. **Genes são estáveis; Expressões são dinâmicas.**
2. **Eventos não modificam diagnósticos — modificam Genes.**
3. Tudo é **temporal**, com **contexto** e **evidências** preservadas.
4. **Explicabilidade obrigatória** — toda inferência é rastreável e
   reproduzível.
5. **A CKO (Ontologia de Conhecimento Clínico) é a fonte da verdade da
   linguagem.**
6. **IA produz hipóteses, nunca verdades** — integra-se ao Genoma só após
   interpretação.
7. O código preserva a teoria; tecnologias podem mudar.

**O salto:** hoje o sistema **armazena informação** (eventos/registros). O AraOS
quer **representar conhecimento** (estado funcional canônico + hipóteses
derivadas).

---

## 3. Diagnóstico honesto

1. **O SIAP é a "informação"; o AraOS é o "conhecimento".** O gap é o coração da
   tarefa.
2. **Risco nº 1 — "laboratório paralelo":** a teoria AraOS pode virar mais um
   módulo que ninguém usa (como parte do `araos/` atual: engine existe,
   repositório de conhecimento é In-Memory, stubs auditados como mortos). **A
   teoria só vale se tocar o fluxo clínico real.**
3. **Não reconstruir o SIAP.** Ele é um negócio funcionando. Ele precisa
   **emitir eventos** para o AraOS, não ser substituído.
4. **Os documentos são a visão; o código é a prova.** Hoje há muito mais
   documento do que código vivo no AraOS.

---

## 4. Fases — o caminho concreto

### Fase 0 — Evento clínico canônico + primeiro fluxo genome-backed (~1 semana)

**Objetivo:** transformar a teoria em algo **visível no dashboard de um
médico**.

- [ ] Definir o contrato de **Clinical Event** (schema canônico: tipo, gene(s)
      afetado(s), evidências, contexto, temporalidade, força, autor)
- [ ] **Ara Intake** (em produção) passa a **emitir eventos reais** ao event
      store/genome
- [ ] Motor de genome consome os eventos e mantém **Expressões** de Clinical
      Genes
- [ ] Dashboard do médico mostra **estado funcional derivado do genome** (ex.:
      status de sono/dor/energia em evolução, não só a lista de respostas)
- [ ] `make quality` + deploy

**Validação:** um médico vê uma pré-consulta e o genome mostra a evolução do
estado, com a cadeia de evidências clicável.

### Fase 1 — Ontologia mínima (CKO v0.1) (~2 semanas)

**Objetivo:** a linguagem canônica sem a qual eventos viram strings soltas.

- [ ] Vocabulário inicial de **Clinical Genes**, **tipos de evento** e
      **evidências** (focado no intake + conceitos comuns: sono, dor, energia,
      humor, atividade, resposta a tratamento)
- [ ] Registrar a ontologia como **versionada** (Constituição art. 16)
- [ ] Eventos validados contra a ontologia (não aceitar termos soltos)

### Fase 2 — SIAP emite eventos (~3-4 semanas)

**Objetivo:** o prontuário inteiro alimenta o genome.

- [ ] Anamnese, evolução, exame, dosagem e prescrição passam a **emitir
      eventos** (wrap, não rewrite)
- [ ] **Replay** das anamneses/evoluções históricas para bootstrap do genome
      (retrofit)
- [ ] Pontos de integração: `routes/anamneses.py`, `routes/evolucoes.py`,
      `routes/exames.py`, `routes/dosagens.py`, `routes/prescricoes.py`

### Fase 3 — Interpretação e projeção (~4-6 semanas)

**Objetivo:** o genome gera valor (hipóteses), não só registros.

- [ ] Motor de **Interpretação** probabilística (confiança, evidências a
      favor/contra, hipóteses alternativas)
- [ ] **Projeções** no dashboard ("a função do paciente está piorando",
      "resposta ao tratamento X")
- [ ] Explicabilidade: cada projeção mostra a cadeia de eventos que a sustenta

### Fase 4 — Consolidação (contínuo)

**Objetivo:** sustentar o genome com o resto em ordem.

- [ ] Unificar as 3 camadas de LLM num gateway
- [ ] Aplicar RBAC de verdade (hoje 106 permissões sem uso)
- [ ] Unificar o multi-tenant (3 mecanismos hoje)
- [ ] Limpeza de código morto e scripts one-off

---

## 5. Anti-padrões a evitar

1. **Não** construir a "teoria completa" como laboratório paralelo (já aconteceu
   com os stubs).
2. **Não** substituir o SIAP de uma vez — envolver/evoluir.
3. **Não** popular o genome com dados ad-hoc sem ontologia (Fase 1 antes de
   escalar).
4. **Não** deixar a explicabilidade de fora — é o que diferencia o AraOS de
   "mais um prontuário".
5. **Não** tratar IA como fonte de verdade clínica — sempre hipótese rastreável.

---

## 6. Decisões que precisam de você

1. **Onde o genome vive?** Hoje `araos/` está embutido no Flask (monolito).
   Manter embutido ou evoluir para serviço? _(Recomendo: manter embutido por ora
   — o event store já está lá.)_
2. **Qual o primeiro Clinical Gene a "ir ao ar"?** _(Recomendo: começar pelos do
   intake — sono, dor, energia, humor.)_
3. **Retrofit dos dados históricos?** Replay das anamneses antigas para o genome
   nascer com histórico. _(Recomendo: sim, é o que dá vida imediata.)_
4. **Prioridade entre Fase 0 e a "limpeza" (Fase 4)?** _(Recomendo: Fase 0
   agora; limpeza em paralelo, não antes.)_

---

## 7. Primeiro passo concreto (Fase 0, detalhe)

1. Criar `ara-intake` → contrato de evento (schema Pydantic + port de
   publicação)
2. Criar no SIAP um **event store** consumidor (endpoint HTTP ou barramento) que
   grava no `araos/clinical/event_store` existente
3. Mapear as respostas do intake para **2-3 Clinical Genes** iniciais (ex.:
   `sono`, `energia`, `dor`) com **Expressão** calculada (0-10 + tendência)
4. Exibir no dashboard do Intake (ou do SIAP) o **estado do genome** com a
   cadeia de evidências
5. Testar com um paciente real, ajustar, deploy

---

_Este é um plano vivo — revise, corte, reordene. O sucesso do AraOS não será
medido por papers, mas por um médico vendo o estado do paciente evoluir na tela,
explicado evento por evento._
