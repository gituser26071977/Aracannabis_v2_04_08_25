# AraOS Week 10 — Specialty Framework Foundation

**Status:** ✅ CONCLUÍDO  
**Release:** AraOS Alpha 0.5  
**Data:** 2026-06-08  
**Branch:** `main`

---

## Objetivo

Construir a **fundação comum para especialidades médicas e multiprofissionais** do AraOS. Antes de criar qualquer módulo especializado (Cannabis, Nutrologia, Psiquiatria, etc.), precisamos de uma infraestrutura que permita que qualquer especialidade seja implementada como um **plugin da plataforma**.

> *"Construir a fábrica de especialidades do AraOS."*

**Princípio:** Nenhuma especialidade deve depender de código específico fora do framework.

---

## Arquitetura do Specialty Framework

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     SPECIALTY FRAMEWORK                                  │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Profile   │  │   Timeline  │  │   Protocol  │  │   Workflow  │    │
│  │  (dados)    │  │  (eventos)  │  │  (fluxos)   │  │  (jornadas) │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│  ┌──────┴────────────────┴────────────────┴────────────────┴──────┐    │
│  │                      SpecialtyRegistry                           │    │
│  │         (registro dinâmico, resolução de dependências)           │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     │
│  │  Dashboard  │  │   Agent     │  │  Knowledge  │                     │
│  │  (KPIs)     │  │  (runtime)  │  │  (layer)    │                     │
│  └─────────────┘  └─────────────┘  └─────────────┘                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
   ┌──────────┐              ┌──────────┐              ┌──────────┐
   │ Cannabis │              │Cardiology│              │Psychiatry│
   │  (stub)  │              │  (stub)  │              │  (stub)  │
   └──────────┘              └──────────┘              └──────────┘
   ┌──────────┐              ┌──────────┐              ┌──────────┐
   │Nutrology │              │Nephrology│              │Psychology│
   │  (stub)  │              │  (stub)  │              │  (stub)  │
   └──────────┘              └──────────┘              └──────────┘
   ┌──────────┐              ┌──────────┐
   │Pulmonology│             │Infectology│
   │  (stub)   │             │  (stub)   │
   └──────────┘              └──────────┘
```

---

## Componentes Implementados

### Parte 1: Specialty Core

**Arquivos:**
- `araos/specialties/core/definitions.py` — `SpecialtyDefinition`, `SpecialtyCategory`, `SpecialtyStatus`, `SpecialtyCapability`
- `araos/specialties/core/profile.py` — `SpecialtyProfile`, `SpecialtyField`, `SpecialtyScore`
- `araos/specialties/core/timeline.py` — `SpecialtyTimeline`, `SpecialtyTimelineEvent`
- `araos/specialties/core/protocol.py` — `SpecialtyProtocol`, `ProtocolStep`, `ProtocolStepType`, `ProtocolTrigger`
- `araos/specialties/core/workflow.py` — `SpecialtyWorkflow`, `WorkflowCheckpoint`, `WorkflowInstance`, `WorkflowStatus`, `WorkflowPhase`
- `araos/specialties/core/dashboard.py` — `SpecialtyDashboard`, `SpecialtyMetric`, `SpecialtyKPI`, `SpecialtyChart`, `SpecialtyMetricsCollector`

---

### Parte 2: Specialty Registry

**Arquivo:** `araos/specialties/core/registry.py` — `SpecialtyRegistry`

**Funcionalidades:**
- Registro dinâmico de especialidades
- Resolução por código
- Listagem por categoria, status, capacidade
- Verificação de dependências
- **Topological sort** para ordem de carregamento

**Uso:**
```python
registry = SpecialtyRegistry()

# Registrar todas as especialidades
for definition in ALL_SPECIALTY_DEFINITIONS:
    registry.register(definition)

# Resolver
cannabis = registry.get("cannabis")
medical = registry.list_by_category(SpecialtyCategory.MEDICAL)
with_protocols = registry.list_by_capability(SpecialtyCapability.PROTOCOLS)

# Verificar dependências
missing = registry.check_dependencies("derived_specialty")
order = registry.resolve_dependency_order()
```

---

### Parte 3: Specialty Profile

**Arquivo:** `araos/specialties/core/profile.py`

**Contrato:** `SpecialtyProfile(ABC)`

Todo módulo de especialidade deve implementar um profile que herda desta classe:

```python
class CannabisProfile(SpecialtyProfile):
    def __init__(self, patient_id: str, tenant_id: str):
        super().__init__(patient_id, tenant_id, specialty_code="cannabis")

    def validate(self) -> List[str]:
        # Validações específicas
        return []

    def get_definition(self) -> SpecialtyDefinition:
        return CANNABIS_DEFINITION
```

**Features:**
- Campos especializados (`SpecialtyField`)
- Escalas/pontuações (`SpecialtyScore`)
- Metadados extensíveis
- Validação customizável

---

### Parte 4: Specialty Timeline

**Arquivo:** `araos/specialties/core/timeline.py`

Integração com `ClinicalTimeline` via conversão para `TimelineEntry`:

```python
timeline = SpecialtyTimeline("cannabis", "p_001")
timeline.add_event(SpecialtyTimelineEvent(
    event_id="e1",
    specialty_code="cannabis",
    event_type="dose_change",
    title="Aumento de dose THC",
    value_before=20.0,
    value_after=25.0,
    unit="mg",
))

# Converter para TimelineEntry do Clinical Timeline
entries = timeline.to_timeline_entries(tenant_id="t_001")
```

---

### Parte 5: Specialty Knowledge

**Arquivo:** `araos/specialties/core/knowledge.py` — `SpecialtyKnowledgeSource`

Integração com Knowledge Layer:

```python
source = SpecialtyKnowledgeSource(repository, tenant_id)

# Indexar protocolo
source.index_protocol(cannabis_protocol)

# Indexar template
source.index_template("cannabis", "Evolução Cannabis", "...")

# Indexar escala
source.index_scale_document("psychiatry", "PHQ-9", "...", items=[...])

# Buscar
docs = source.search("cannabis", "protocolo")
```

---

### Parte 6: Specialty Workflows

**Arquivo:** `araos/specialties/core/workflow.py`

Workflows especializados com checkpoints e fases:

```python
workflow = SpecialtyWorkflow("wf_001", "cannabis", "Acompanhamento")
workflow.add_checkpoint(WorkflowCheckpoint(
    checkpoint_id="cp_intake",
    phase=WorkflowPhase.INTAKE,
    title="Avaliação inicial",
    required_fields=["main_complaint"],
    due_days_from_start=0,
))
workflow.add_checkpoint(WorkflowCheckpoint(
    checkpoint_id="cp_7d",
    phase=WorkflowPhase.MONITORING,
    title="Avaliação 7 dias",
    due_days_from_start=7,
))

# Criar instância
instance = workflow.create_instance("inst_001", "p_001", "t_001")
instance.complete_checkpoint("cp_intake")
```

---

### Parte 7: Specialty Dashboards

**Arquivo:** `araos/specialties/core/dashboard.py`

Contratos para KPIs, métricas e gráficos (sem frontend):

```python
dashboard = SpecialtyDashboard("cannabis")

# KPIs com thresholds
dashboard.add_kpi(SpecialtyKPI(
    kpi_id="avg_thc_dose",
    name="Dose Média THC",
    value=22.5,
    unit="mg",
    threshold_warning=40.0,
    threshold_critical=80.0,
))

# Métricas
dashboard.add_metric(SpecialtyMetric(
    metric_id="total_consultations",
    name="Total de Consultas",
    metric_type=MetricType.COUNT,
    value=128,
))

# Gráficos
dashboard.add_chart(SpecialtyChart(
    chart_id="dose_evolution",
    name="Evolução de Dose",
    chart_type=ChartType.LINE,
    data={"months": ["Jan", "Fev"], "doses": [10, 15]},
))
```

---

### Parte 8: Specialty Agents

**Arquivo:** `araos/specialties/core/agent.py` — `SpecialtyAgent`

Integração com Agent Runtime:

```python
class CannabisAgent(SpecialtyAgent):
    def __init__(self):
        super().__init__(
            agent_id="cannabis_agent",
            name="Cannabis Agent",
            version="1.0.0",
            capabilities=[AgentCapability.CLINICAL_SUMMARY],
            required_permissions=["patient.read"],
        )

    @property
    def specialty_code(self) -> str:
        return "cannabis"

    async def execute(self, context: AgentContext) -> AgentResult:
        # Lógica específica
        ...
```

---

### Parte 9: First Implementation Stubs

**Arquivos:** `araos/specialties/stubs/*.py`

8 especialidades stub registradas:

| Especialidade | Código | Categoria | Capacidades |
|--------------|--------|-----------|-------------|
| Cannabis Medicinal | `cannabis` | Integrative | 9 |
| Nutrologia | `nutrology` | Medical | 8 |
| Psiquiatria | `psychiatry` | Medical | 9 |
| Psicologia | `psychology` | Multiprofessional | 8 |
| Cardiologia | `cardiology` | Medical | 8 |
| Nefrologia | `nephrology` | Medical | 8 |
| Pneumologia | `pulmonology` | Medical | 8 |
| Infectologia | `infectology` | Medical | 8 |

Todas herdam `SpecialtyProfile` e possuem `SpecialtyDefinition`.

---

## Testes

```bash
python -m pytest tests/test_week10_specialties.py -v
```

**Resultado:** 68 passed, 0 failed

### Testes por categoria

| Categoria | Testes | Status |
|-----------|--------|--------|
| Specialty Definitions | 5 | ✅ |
| Specialty Profile | 5 | ✅ |
| Specialty Timeline | 4 | ✅ |
| Specialty Protocol | 3 | ✅ |
| Specialty Workflow | 3 | ✅ |
| Specialty Dashboard | 6 | ✅ |
| Specialty Registry | 7 | ✅ |
| Profile Contract | 1 | ✅ |
| Timeline Integration | 2 | ✅ |
| Knowledge Integration | 5 | ✅ |
| Workflows | 2 | ✅ |
| Dashboards | 2 | ✅ |
| Specialty Agents | 3 | ✅ |
| Specialty Stubs | 8 | ✅ |
| Platform Integration | 5 | ✅ |
| Full Lifecycle | 1 | ✅ |

---

## Testes completos (Weeks 6 + 7A + 7B + 8 + 10)

```bash
python -m pytest tests/test_week*.py -v
```

**Resultado:** 174 passed, 0 failed

| Semana | Testes | Status |
|--------|--------|--------|
| Week 6 (Fluxos MVP) | 11 | ✅ |
| Week 7A (Hardening) | 17 | ✅ |
| Week 7B (Intelligence) | 32 | ✅ |
| Week 8 (Knowledge) | 46 | ✅ |
| Week 10 (Specialty Framework) | 68 | ✅ |
| **Total** | **174** | **✅** |

---

## Arquivos Criados/Modificados

### Novos (Week 10)
| Arquivo | Descrição |
|---------|-----------|
| `araos/specialties/__init__.py` | Exportações do pacote |
| `araos/specialties/core/__init__.py` | Exportações do core |
| `araos/specialties/core/definitions.py` | SpecialtyDefinition, Category, Status, Capability |
| `araos/specialties/core/profile.py` | SpecialtyProfile, SpecialtyField, SpecialtyScore |
| `araos/specialties/core/timeline.py` | SpecialtyTimeline, SpecialtyTimelineEvent |
| `araos/specialties/core/protocol.py` | SpecialtyProtocol, ProtocolStep |
| `araos/specialties/core/workflow.py` | SpecialtyWorkflow, WorkflowCheckpoint, WorkflowInstance |
| `araos/specialties/core/dashboard.py` | SpecialtyDashboard, Metric, KPI, Chart, Collector |
| `araos/specialties/core/registry.py` | SpecialtyRegistry com topological sort |
| `araos/specialties/core/agent.py` | SpecialtyAgent integrado ao Agent Runtime |
| `araos/specialties/core/knowledge.py` | SpecialtyKnowledgeSource integrado à Knowledge Layer |
| `araos/specialties/stubs/__init__.py` | Exportações dos stubs |
| `araos/specialties/stubs/cannabis.py` | CannabisSpecialty stub |
| `araos/specialties/stubs/nutrology.py` | NutrologySpecialty stub |
| `araos/specialties/stubs/psychiatry.py` | PsychiatrySpecialty stub |
| `araos/specialties/stubs/psychology.py` | PsychologySpecialty stub |
| `araos/specialties/stubs/cardiology.py` | CardiologySpecialty stub |
| `araos/specialties/stubs/nephrology.py` | NephrologySpecialty stub |
| `araos/specialties/stubs/pulmonology.py` | PulmonologySpecialty stub |
| `araos/specialties/stubs/infectology.py` | InfectologySpecialty stub |
| `tests/test_week10_specialties.py` | 68 testes |
| `docs/WEEK10_SPECIALTY_FRAMEWORK.md` | Esta documentação |

### Modificados
| Arquivo | Mudança |
|---------|---------|
| `araos/platform/sdk/__init__.py` | Exporta Specialty Framework |

---

## Checklist do CTO

| # | Requisito | Status |
|---|-----------|--------|
| 1 | Specialty Core (definitions, profile, timeline, protocol, workflow, dashboard) | ✅ |
| 2 | Specialty Registry (dynamic loading, topological sort) | ✅ |
| 3 | Specialty Profile contract (ABC + base implementation) | ✅ |
| 4 | Specialty Timeline (Clinical Timeline integration) | ✅ |
| 5 | Specialty Knowledge (Knowledge Layer integration) | ✅ |
| 6 | Specialty Workflows (checkpoints, phases, instances) | ✅ |
| 7 | Specialty Dashboards (KPIs, metrics, charts — no frontend) | ✅ |
| 8 | Specialty Agents (Agent Runtime integration) | ✅ |
| 9 | 8 Specialty Stubs (Cannabis, Nutrology, Psychiatry, Psychology, Cardiology, Nephrology, Pulmonology, Infectology) | ✅ |
| 10 | Digital Twin integration | ✅ |
| 11 | Knowledge Layer integration | ✅ |
| 12 | Agent Runtime integration | ✅ |
| 13 | Platform desacoplada | ✅ |
| 14 | Sem regras clínicas específicas | ✅ |
| 15 | SDK exporta todos os componentes | ✅ |
| 16 | Todos os testes passando | ✅ (174/174) |

---

## Próximos Passos

**AraOS Week 11+ — Módulos Especializados**

Agora que o Specialty Framework está operacional:
- ✅ Infraestrutura comum para todas as especialidades
- ✅ Registro dinâmico com resolução de dependências
- ✅ Profile, Timeline, Protocol, Workflow, Dashboard como contratos
- ✅ Integração com Clinical Layer, Knowledge Layer, Agent Runtime
- ✅ 8 stubs validando a arquitetura
- ✅ 174 testes da plataforma passando

Próximas capacidades:
1. **Cannabis Module** — primeiras regras clínicas específicas
2. **Escalas e Questionários** — PHQ-9, GAD-7, EVA, etc.
3. **Protocolos específicos** — primeiros fluxos de tratamento
4. **Agentes especializados** — CannabisAgent, CardiologyAgent

**A plataforma possui a fábrica de especialidades. Está pronta para produzir módulos médicos.** 🏥🌿
