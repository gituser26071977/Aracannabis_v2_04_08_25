# ADR-0002: Clinical Identity & Neurodevelopmental Registry

| | |
|---|---|
| **Status** | ✅ Accepted |
| **Data** | 2026-07-16 |
| **Autor** | Claude (M3) · revisado e aprovado por arquitetura sênior AraOS |
| **Decisor** | Arquiteto-chefe AraOS |
| **Impacto** | Cross-specialty · plataforma inteira · visão 10+ anos |
| **Complementa** | [ADR-0001 — Clinical Event Engine](0001-clinical-event-engine.md) |
| **Substitui** | Premissa de "CRUD de diagnósticos" como modelo de domínio |

---

## 1. Contexto

O AraOS evoluiu ao longo de 6 sprints (Foundation → Specialties → Clinical Event Engine). A Sprint 3.1 entregou o Event Store — infraestrutura de audit, replay e cadeia canônica. **Mas o Event Store é meio, não fim.**

O modelo mental ainda era, em muitos lugares, o de "tabelas com CRUD":

- Diagnóstico era "uma linha em `neuro_patient_profiles` que pode ser atualizada ou apagada".
- Mudança de estado (ex.: hipótese → confirmado) era "UPDATE direto na linha".
- A história clínica do paciente era o que sobrava na tabela após cada UPDATE — sem garantia de integridade temporal.
- Multi-classificação (CID-10 + DSM-5) era "colunas opcionais" que podiam ficar fora de sincronia.

Esse modelo **não escala** para a visão do AraOS: representar a evolução clínica longitudinal de uma pessoa durante toda a vida.

> "Não estamos criando um sistema para registrar diagnósticos.
> Estamos criando uma infraestrutura capaz de representar a evolução clínica
> longitudinal de uma pessoa durante toda a vida."
> — Diretriz arquitetural, Sprint 3.2

Análise comparada com **OpenEHR (modelo dual)**, **FHIR `Condition` resource lifecycle**, **HL7 CIMI** e o pensamento de **Domain-Driven Design (Eric Evans, Vaughn Vernon)** confirmou a direção:

> **A identidade clínica do paciente é um agregado permanente, distinto da pessoa administrativa.
> Cada mudança clínica é um evento. Diagnósticos têm ciclo de vida.
> O Registry é uma projeção, não uma fonte primária.**

---

## 2. Decisão

A partir de 2026-07-16, o AraOS adota **Domain-Driven Design** no bounded context "Neurodevelopmental Registry":

### 2.1. Bounded Context

```
Neurodevelopmental Registry (Bounded Context)
├── Aggregate Roots: ClinicalIdentity, Intervention
├── Entities:        Diagnosis, Phenotype, Assessment, Outcome
├── Value Objects:   CID-10, CID-11, DSM-5-TR, ConditionCode, DiagnosisState, ...
├── Domain Events:   DiagnosisHypothesized, DiagnosisConfirmed, PhenotypeObserved, ...
├── Domain Services: DiagnosisTransitionService, PhenotypeDerivationService
└── Projections:     NeurodevelopmentalRegistry (read model, rebuildable)
```

**Anti-corruption layer** com outros bounded contexts:
- `Patient` (bounded context administrativo) — referência por ID, sem mutação
- `Clinical Event Store` (Sprint 3.1) — única porta de saída de eventos
- `Conditions Catalog` (Sprint 3.3) — conceitos clínicos versionados

### 2.2. Princípios arquiteturais (não-negociáveis)

1. **Event-First** — nenhuma entidade altera outra diretamente. Toda mudança clínica flui por Clinical Events.

2. **Registry = Projection** — `neurodevelopmental_registry` é read model, **descartável e reconstruível integralmente** a partir do Event Store. Se apagarmos a tabela inteira, replay dos eventos deve reconstruí-la bit a bit.

3. **Clinical Identity é permanente** — não depende de diagnóstico específico. Sobrevive a todas as mudanças clínicas. É a âncora longitudinal.

4. **Diagnóstico ≠ Pessoa** — pessoa é administrativa (Patient). Diagnóstico é estado evolutivo com ciclo de vida explícito. Nunca atualizar silenciosamente.

5. **Multi-classificação simultânea** — diagnóstico pode ter CID-10, CID-11, DSM-5-TR, SNOMED, classificações internas **em paralelo**. Não assumir exclusividade.

6. **Imutabilidade do histórico** — nenhum evento é sobrescrito ou apagado. Correções = novos eventos.

7. **API expressa linguagem clínica** — endpoints refletem o domínio, não tabela do banco.

8. **Reconstructibilidade** — toda informação clínica é derivável de eventos. Não há "campo mágico" no Registry que não tenha evento correspondente.

### 2.3. Modelo de domínio

#### 2.3.1. Patient (referência administrativa)

```python
# NÃO mutável pelo Registry. Apenas referência por ID.
class Patient:
    id: PatientId           # UUID do bounded context Patient (SIAP)
    tenant_id: TenantId
    name: str               # display apenas
    birth_date: date
    # ... apenas dados administrativos
```

#### 2.3.2. ClinicalIdentity (Aggregate Root — permanente)

```python
class ClinicalIdentity:
    """Identidade clínica longitudinal. Sobrevive a todas as mudanças."""
    id: ClinicalIdentityId
    tenant_id: TenantId
    patient_id: PatientId           # FK para Patient (admin)
    created_at: datetime            # primeira vez que o paciente teve evento clínico
    status: ClinicalIdentityStatus  # ACTIVE | ARCHIVED (nunca DELETED)

    # Não é editável. Composição de eventos.
    diagnoses: List[Diagnosis]            # reconstruído via projection
    phenotypes: List[Phenotype]
    assessments: List[Assessment]
    interventions: List[Intervention]
    outcomes: List[Outcome]
```

**Invariantes:**
- 1 Patient ↔ 0..1 ClinicalIdentity (idempotente)
- ClinicalIdentity nunca é deletada fisicamente. Status = ARCHIVED significa "paciente não está mais em acompanhamento", mas o histórico permanece.
- Toda referência a ClinicalIdentity é por `ClinicalIdentityId`, nunca por composição direta com Patient.

#### 2.3.3. Diagnosis (Entity — ciclo de vida explícito)

```python
class DiagnosisState(Enum):
    HYPOTHESIS = "hypothesis"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    REVISED = "revised"
    IN_REMISSION = "in_remission"
    DISCARDED = "discarded"


class Diagnosis:
    """Estado evolutivo de uma condição clínica no paciente."""
    id: DiagnosisId
    clinical_identity_id: ClinicalIdentityId
    condition_code: ConditionCode       # ref ao Conditions Catalog (Sprint 3.3)
    state: DiagnosisState
    onset_date: Optional[date]          # quando clinicamente iniciou
    resolved_date: Optional[date]       # quando entrou em remissão

    # Multi-classificação simultânea
    classification: DiagnosisClassification
    #   cid10: Optional[CID10Code]
    #   cid11: Optional<CID11Code>
    #   dsm5_tr: Optional<DSM5Code>
    #   snomed: Optional<SNOMEDCode>      # futuro
    #   internal: List<InternalCode>

    # Rastreabilidade completa
    source_event_ids: List[ClinicalEventId]   # eventos que compuseram este estado

    # Atores e evidência
    hypothesised_by: Optional[ProfessionalId]
    hypothesised_at: Optional[datetime]
    hypothesised_reason: Optional[str]
    confirmed_by: Optional[ProfessionalId]
    confirmed_at: Optional[datetime]
    confirmation_evidence: Optional[Dict[str, Any]]    # refs a assessments, exames
```

**Transições válidas** (state machine):

```
HYPOTHESIS  → INVESTIGATING
HYPOTHESIS  → CONFIRMED         (com evidência)
HYPOTHESIS  → DISCARDED         (sem evidência)
INVESTIGATING → CONFIRMED       (com evidência)
INVESTIGATING → DISCARDED       (sem evidência)
CONFIRMED  → REVISED            (mudança de condição/severidade)
CONFIRMED  → IN_REMISSION       (resolução parcial/total)
CONFIRMED  → DISCARDED          (erro diagnóstico)
IN_REMISSION → CONFIRMED        (recidiva)
REVISED    → CONFIRMED          (nova hipótese confirmada)
REVISED    → DISCARDED
```

**Invariantes:**
- Cada transição gera evento. Não há UPDATE silencioso.
- Transições fora da state machine são rejeitadas (não há `from_state` inválido).
- `confirmed_at` requer `confirmation_evidence` não-vazio.
- `source_event_ids` lista — não há campo que não tenha evento correspondente.

#### 2.3.4. Condition (Catalog — versionado, compartilhado)

```python
class Condition:
    """Conceito clínico do catálogo (não pertence a paciente)."""
    code: ConditionCode
    name_pt: str
    name_en: str
    description: str
    version: str                   # "1.0", "2.0", ...
    category: ConditionCategory    # NEURODEVELOPMENTAL | PSYCHIATRIC | ...
    status: ConditionStatus        # ACTIVE | DEPRECATED

    # Mapeamentos multi-classificação
    typical_cid10: Optional[List[CID10Code]]
    typical_cid11: Optional[List[CID11Code]]
    typical_dsm5_tr: Optional[List[DSM5Code>]

    # Metadados científicos
    scientific_references: List[ScientificReference]
    diagnostic_criteria: Optional[str]    # texto ou ref a guideline
    onset_age_range: Optional[AgeRange]
```

Sprint 3.3 entrega o Conditions Catalog completo.

#### 2.3.5. Phenotype (Entity — manifestações funcionais observáveis)

```python
class Phenotype:
    """Manifestações funcionais observáveis — independentes de diagnóstico."""
    id: PhenotypeId
    clinical_identity_id: ClinicalIdentityId
    code: PhenotypeCode          # ex: 'social_deficit', 'sensory_hypersensitivity'
    label_pt: str
    label_en: str
    severity: PhenotypeSeverity  # MILD | MODERATE | SEVERE | PROFOUND
    onset_date: Optional[date]
    resolution_date: Optional[date]
    source_event_ids: List[ClinicalEventId]
    # Pode existir ANTES do diagnóstico (ex.: atraso de linguagem aos 18m,
    # diagnóstico de TEA aos 36m).
    # Pode PERSISTIR após mudança diagnóstica.
```

**Invariantes:**
- Phenotype pode existir sem Diagnosis (manifestação precede diagnóstico).
- Phenotype persiste após Diagnosis ser descartado (pode ser manifestação de outra condição).
- `source_event_ids` lista — toda criação/resolução tem evento correspondente.

#### 2.3.6. Assessment (Entity — aplicação de escala)

```python
class Assessment:
    """Aplicação de escala — produz evidência, não mutua paciente diretamente."""
    id: AssessmentId
    clinical_identity_id: ClinicalIdentityId
    scale_code: str              # ref ao ScaleRegistry (Neurodevelopmental)
    scale_version: str
    applied_at: datetime
    applied_by: ProfessionalId
    raw_responses: Dict[str, Any]      # entrada bruta (validação por JSON Schema)
    computed_scores: Dict[str, float]  # cache do cálculo
    interpretation: str
    source_event_ids: List[ClinicalEventId]
```

**Invariantes:**
- Assessment nunca altera diretamente `Diagnosis.state` ou `Phenotype`.
- Mudanças em Assessment geram `SCALE_UPDATED` events (nova versão).
- Projeções (Dashboard, IA, Correlação) decidem impacto — não há trigger automático.

#### 2.3.7. Intervention (Aggregate Root — toda intervenção clínica)

```python
class InterventionType(Enum):
    MEDICATION = "medication"
    CANNABIS = "cannabis"
    PSYCHOTHERAPY = "psychotherapy"
    OCCUPATIONAL_THERAPY = "occupational_therapy"
    SPEECH_THERAPY = "speech_therapy"
    ABA = "aba"                          # Applied Behavior Analysis
    NEUROMODULATION = "neuromodulation"  # TMS, tDCS
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    SCHOOL_SUPPORT = "school_support"
    PARENT_TRAINING = "parent_training"
    OTHER = "other"


class Intervention:
    """Qualquer intervenção clínica — modelo conceitual único."""
    id: InterventionId
    clinical_identity_id: ClinicalIdentityId
    type: InterventionType
    subtype: str                 # ex.: MEDICATION → 'methylphenidate', ABA → 'DTT'
    start_date: date
    end_date: Optional[date]
    status: InterventionStatus   # PLANNED | ACTIVE | ADJUSTED | PAUSED | STOPPED
    dose: Optional[Dose]          # para Medication/Cannabis
    frequency: Optional[str]
    prescriber_id: Optional[ProfessionalId]
    indication: Optional[ConditionCode]   # por que foi indicado
    adverse_events: List[AdverseEvent]
    source_event_ids: List[ClinicalEventId]
```

**Invariantes:**
- Medication, Cannabis, TO, Fono, ABA, etc. **compartilham o mesmo modelo** — diferem apenas em `type` e `subtype`.
- Toda mudança de status é evento. Não há UPDATE silencioso.
- `indication` referencia ConditionCode do catálogo — não é texto livre.

#### 2.3.8. Outcome (Entity — resultados clínicos)

```python
class OutcomeType(Enum):
    IMPROVEMENT = "improvement"
    WORSENING = "worsening"
    PARTIAL_RESPONSE = "partial_response"
    REMISSION = "remission"
    ADVERSE_EVENT = "adverse_event"
    NO_CHANGE = "no_change"


class Outcome:
    """Resultado clínico — derivado de eventos, observável."""
    id: OutcomeId
    clinical_identity_id: ClinicalIdentityId
    type: OutcomeType
    observed_at: datetime
    evidence: List[AssessmentId | PhenotypeId]   # o que fundamenta
    intervention_id: Optional[InterventionId]     # se for resposta a tratamento
    severity: Optional[OutcomeSeverity]
    notes: Optional[str]
    source_event_ids: List[ClinicalEventId]
```

**Invariantes:**
- Outcome é sempre derivado de eventos anteriores (não é input primário).
- Outcome com `intervention_id` = resposta terapêutica; sem = evolução natural.

### 2.4. Fluxo Event-First

Toda ação clínica segue o fluxo:

```
[Clinical Action / API Request]
        │
        ▼
[Application Service]  ← orquestra, NÃO acessa Registry diretamente
        │
        ▼
[ClinicalEventPublisher.publish()]  ← ADR-0001
        │
        ├──→ 1. Validate event_type contra CLINICAL_EVENT_CATALOG
        ├──→ 2. Validate payload contra JSON Schema
        ├──→ 3. Build EventEnvelopeV2 (canonical form)
        ├──→ 4. Compute event_hash + assign sequence
        └──→ 5. INSERT INTO clinical_events + fan-out to bus
                │
                ▼
        [Clinical Event Store]  ← ADR-0001 — única fonte de verdade
                │
                ▼
        [Event Bus (Redis Streams)]  ← fan-out assíncrono
                │
                ▼
        [Projection: NeurodevelopmentalRegistry]  ← rebuildable
                │
                ▼
        [Read Model: Registry / Dashboards / IA / Observatory]
```

**Garantias:**
- Application Service **nunca** escreve no Registry diretamente.
- Projection **sempre** idempotente (replay do mesmo evento = mesmo estado).
- Bus é canal de notificação — falha do bus não impede escrita no store.

### 2.5. Registry como Projection

O `NeurodevelopmentalRegistry` é uma **view materializada** do Event Store:

```python
class REDACTED:
    """
    Reconstrói ClinicalIdentity, Diagnosis, Phenotype, etc. a partir de eventos.

    Propriedade fundamental: SE apagarmos toda a tabela do Registry e
    rodarmos replay desde o genesis, o estado final é IDÊNTICO.
    """
    def replay_all_events(self, tenant_id: TenantId) -> None:
        """Reconstrói o Registry inteiro a partir do Event Store."""

    def replay_from(self, tenant_id: TenantId, since_sequence: int) -> None:
        """Replay incremental a partir de uma sequência."""
```

**Garantias testáveis:**

| Propriedade | Como verificar |
|---|---|
| **Replay = reconstrução exata** | Wipe Registry → replay → comparar bit a bit |
| **Idempotência** | Aplicar mesmo evento N vezes → mesmo resultado |
| **Eventos fora de ordem** | Aplicar eventos embaralhados → mesmo estado final |
| **Diagnósticos simultâneos** | Múltiplas hipóteses paralelas → todas mantidas |
| **Rollback de projeções** | Voltar sequence → estado volta ao ponto |

### 2.6. API — Linguagem clínica

Endpoints refletem o domínio:

```
# Identidade clínica (permanente)
POST   /clinical-identities                    → cria ClinicalIdentity
GET    /clinical-identities/{id}               → recupera (do Registry)
GET    /clinical-identities/{id}/timeline      → eventos ordenados por event_datetime

# Diagnósticos
POST   /clinical-identities/{id}/diagnoses                → cria hipótese
POST   /diagnoses/{id}/transitions                       → mudança de estado (state machine)
POST   /diagnoses/{id}/classifications                    → adiciona CID/DSM/SNOMED
GET    /diagnoses/{id}                                   → estado atual

# Fenótipos
POST   /clinical-identities/{id}/phenotypes               → observa manifestação
POST   /phenotypes/{id}/resolve                          → marca resolução

# Assessments (escala)
POST   /clinical-identities/{id}/assessments              → aplica escala

# Interventions
POST   /clinical-identities/{id}/interventions            → inicia intervenção
POST   /interventions/{id}/transitions                   → ajuste/pausa/stop

# Outcomes
POST   /clinical-identities/{id}/outcomes                 → registra outcome

# Admin
POST   /admin/registry/replay                            → replay completo (DESTRUTIVO)
POST   /admin/registry/replay/{tenant_id}                → replay por tenant
```

**Princípios:**
- Nenhum endpoint aceita UPDATE genérico.
- Cada mudança = endpoint específico ou `POST /transitions`.
- Todos retornam 202 (Accepted) com `event_id` — não há leitura síncrona do Registry na escrita.
- GETs leem da projection (read model).

### 2.7. Catálogo de Eventos (extensão do Sprint 3.1)

Novos event types adicionados ao `CLINICAL_EVENT_CATALOG`:

| event_type | aggregate | descrição |
|---|---|---|
| `CLINICAL_IDENTITY_CREATED` | `clinical_identity` | Primeira identidade para o paciente |
| `CLINICAL_IDENTITY_ARCHIVED` | `clinical_identity` | Arquivamento (não deleta) |
| `DIAGNOSIS_HYPOTHESIZED` | `diagnosis` | Criação com estado HYPOTHESIS |
| `DIAGNOSIS_INVESTIGATING` | `diagnosis` | Em investigação |
| `DIAGNOSIS_CONFIRMED` | `diagnosis` | Confirmado com evidência |
| `DIAGNOSIS_REVISED` | `diagnosis` | Revisão de condição/severidade |
| `DIAGNOSIS_IN_REMISSION` | `diagnosis` | Em remissão |
| `DIAGNOSIS_DISCARDED` | `diagnosis` | Descartado |
| `DIAGNOSIS_CLASSIFICATION_ADDED` | `diagnosis` | Adiciona CID/DSM/SNOMED |
| `DIAGNOSIS_CLASSIFICATION_REMOVED` | `diagnosis` | Remove classificação |
| `PHENOTYPE_OBSERVED` | `phenotype` | Manifestação registrada |
| `PHENOTYPE_RESOLVED` | `phenotype` | Manifestação resolvida |
| `ASSESSMENT_APPLIED` | `assessment` | Escala aplicada |
| `ASSESSMENT_UPDATED` | `assessment` | Atualização de scores |
| `INTERVENTION_STARTED` | `intervention` | Início de qualquer intervenção |
| `INTERVENTION_ADJUSTED` | `intervention` | Ajuste de dose/frequência |
| `INTERVENTION_PAUSED` | `intervention` | Pausa temporária |
| `INTERVENTION_RESUMED` | `intervention` | Retomada |
| `INTERVENTION_STOPPED` | `intervention` | Fim (com motivo) |
| `OUTCOME_IMPROVEMENT` | `outcome` | Melhora clínica |
| `OUTCOME_WORSENING` | `outcome` | Piora clínica |
| `OUTCOME_PARTIAL_RESPONSE` | `outcome` | Resposta parcial |
| `OUTCOME_REMISSION` | `outcome` | Remissão observada |
| `OUTCOME_ADVERSE_EVENT` | `outcome` | Evento adverso |
| `OUTCOME_NO_CHANGE` | `outcome` | Sem mudança |

Zero migração Alembic adicional — extensão do catálogo (Sprint 3.1).

---

## 3. Estrutura de arquivos

```
araos/specialties/neurodevelopmental/
├── domain/                       # DDD — pure Python, zero SQLAlchemy
│   ├── __init__.py
│   ├── clinical_identity.py      # Aggregate root + value objects
│   ├── diagnosis.py              # Entity + state machine
│   ├── condition.py              # Value objects (CID-10, CID-11, DSM-5, ...)
│   ├── phenotype.py
│   ├── assessment.py
│   ├── intervention.py
│   ├── outcome.py
│   ├── events.py                 # Domain Events (dataclass frozen)
│   └── services.py               # Domain Services
│
├── application/                  # Application Services
│   ├── __init__.py
│   ├── diagnosis_service.py
│   ├── phenotype_service.py
│   ├── assessment_service.py
│   ├── intervention_service.py
│   └── outcome_service.py
│
├── projections/                  # Read models — rebuildable from events
│   ├── __init__.py
│   ├── registry.py               # REDACTED
│   └── handlers.py               # Event → Projection reducers
│
├── api/                          # Flask routes (DDD-aligned)
│   ├── __init__.py
│   ├── clinical_identities.py
│   ├── diagnoses.py
│   ├── phenotypes.py
│   ├── assessments.py
│   ├── interventions.py
│   └── outcomes.py
│
└── tests/                        # Behavioral + unit
    ├── domain/
    ├── application/
    ├── projections/
    └── api/
```

---

## 4. Consequências

### Positivas

1. **Replay garante audit** — qualquer estado pode ser reconstruído e verificado.
2. **Diagnósticos não somem** — histórico completo preservado para LGPD, perícia, pesquisa.
3. **Multi-classificação sem perda** — CID-10, CID-11, DSM-5 coexistindo sem campos nullable conflitantes.
4. **Phenotype independente** — manifestation precede diagnóstico, suporta casos clínicos reais.
5. **Intervention unificada** — Medication, Cannabis, ABA, TO compartilham modelo conceitual.
6. **Testes de replay** — propriedade testável mecanicamente, não apenas "boa prática".

### Negativas

1. **Mais complexidade inicial** — domain layer + projection + application service vs CRUD simples.
2. **Latência de leitura** — Registry pode ter lag de milissegundos vs store (aceitável para domínio clínico).
3. **Custo de replay** — replay completo pode ser pesado para tenants grandes (mitigação: replay incremental, projections assíncronas).
4. **Onboarding** — desenvolvedores precisam entender DDD + Event Sourcing (vale o investimento).

### Mitigações

- **Replay assíncrono** — projections rebuild em background, sem bloquear escrita
- **Materialized view** — Registry é tabela física com índices otimizados
- **Documentação** — ADR + testes comportamentais como onboarding
- **Migração gradual** — Sprint 3.2 entrega o esqueleto; sprints 3.3+ preenchem comportamento

---

## 5. Decisões adiadas (open questions)

Estas serão resolvidas em sprints subsequentes ou via discussão:

1. **Patient é bounded context separado?** — Sim, mas como referenciar (eventos vs FK)?
2. **SNOMED** — integrado agora ou Sprint futura?
3. **Versionamento de Diagnosis** — quando muda condition_code, é REVISED ou novo Diagnosis?
4. **Intervention.comorbidity_indication** — múltiplas indicações por intervention?
5. **Outcome.evidence** — aceita tipos heterogêneos via tag union?

---

## 6. Validação

Esta decisão se valida quando:

- [ ] Domain models (pure Python) implementados com testes unitários >95%
- [ ] Application services publicam eventos via `ClinicalEventPublisher`
- [ ] Projection `NeurodevelopmentalRegistry` reconstruída a partir de replay
- [ ] Testes comportamentais: hypothesis → confirmed → revised → remission
- [ ] Testes de replay: wipe + replay = estado idêntico
- [ ] Testes de idempotência: mesmo evento N vezes = mesmo estado
- [ ] Testes de ordem: eventos embaralhados = mesmo estado final
- [ ] Cobertura geral do módulo ≥95%
- [ ] API implementada com URLs DDD-aligned
- [ ] OpenAPI documentado

---

## 7. Visão de longo prazo

> "Não estamos criando um sistema para registrar diagnósticos.
> Estamos criando uma infraestrutura capaz de representar a evolução clínica
> longitudinal de uma pessoa durante toda a vida."

Esta decisão orientará toda a evolução futura do AraOS:

- **Sprint 3.3** — Conditions Catalog completo (CID-10/11/DSM-5/SNOMED, versionado)
- **Sprint 3.4** — Timeline read model (projection que ordena por `event_datetime`)
- **Sprint 3.5** — Longitudinal Phenotypes (snapshot materializado por paciente)
- **Sprint 3.6** — Escalas finais (ABC, PSQI, AQ, Conners) com Assessment events
- **Futuro** — Clinical Graph, Correlation Engine, Research Layer, Digital Twin

Cada um destes será construído **sobre** esta fundação DDD, não apesar dela.

---

## 8. Referências

- **Eric Evans** — *Domain-Driven Design* (2003)
- **Vaughn Vernon** — *Implementing Domain-Driven Design* (2013)
- **Greg Young** — *Event Sourcing* (2010)
- **OpenEHR** — Reference Model, EHR Information Model
- **FHIR R5** — `Condition` resource lifecycle
- **HL7 CIMI** — Clinical Information Modeling Initiative
- **ADR-0001** — Clinical Event Engine (foundation técnica)
