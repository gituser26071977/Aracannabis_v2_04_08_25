"""
AraOS Week 10 — Specialty Framework Foundation Tests

Valida:
    1. Specialty Core (definitions, profile, timeline, protocol, workflow, dashboard)
    2. Specialty Registry (dynamic loading)
    3. Specialty Profile contract
    4. Specialty Timeline (Clinical Timeline integration)
    5. Specialty Knowledge (Knowledge Layer integration)
    6. Specialty Workflows (Workflow Engine integration)
    7. Specialty Dashboards (KPIs/metrics contracts)
    8. Specialty Agents (Agent Runtime integration)
    9. First implementation stubs (8 specialties)
    10. Validation: Digital Twin, Knowledge Layer, Agent Runtime integration
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from araos.specialties.core.definitions import (
    SpecialtyDefinition, SpecialtyCategory, SpecialtyStatus, SpecialtyCapability,
)
from araos.specialties.core.profile import (
    SpecialtyProfile, SpecialtyField, SpecialtyScore,
)
from araos.specialties.core.timeline import SpecialtyTimeline, SpecialtyTimelineEvent
from araos.specialties.core.protocol import (
    SpecialtyProtocol, ProtocolStep, ProtocolStepType, ProtocolTrigger,
)
from araos.specialties.core.workflow import (
    SpecialtyWorkflow, WorkflowCheckpoint, WorkflowInstance,
    WorkflowStatus, WorkflowPhase,
)
from araos.specialties.core.dashboard import (
    SpecialtyDashboard, SpecialtyMetric, SpecialtyKPI, SpecialtyChart,
    SpecialtyMetricsCollector, MetricType, ChartType, KpiSeverity,
)
from araos.specialties.core.registry import SpecialtyRegistry
from araos.specialties.core.agent import SpecialtyAgent
from araos.specialties.core.knowledge import SpecialtyKnowledgeSource

from araos.specialties.stubs import (
    CANNABIS_DEFINITION, CannabisProfile,
    NUTROLOGY_DEFINITION, NutrologyProfile,
    PSYCHIATRY_DEFINITION, PsychiatryProfile,
    PSYCHOLOGY_DEFINITION, PsychologyProfile,
    CARDIOLOGY_DEFINITION, CardiologyProfile,
    NEPHROLOGY_DEFINITION, NephrologyProfile,
    PULMONOLOGY_DEFINITION, PulmonologyProfile,
    INFECTOLOGY_DEFINITION, InfectologyProfile,
    ALL_SPECIALTY_DEFINITIONS,
)

from araos.knowledge.repository import InMemoryKnowledgeRepository
from araos.demo.demo_base import DemoEnvironment
from araos.agents.runtime.agent import AgentCapability
from araos.agents.runtime.context import AgentContext
from araos.platform.shared.context import TenantContext
from araos.platform.identity.context import IdentityContext, ActorType


@pytest.fixture
def env():
    e = DemoEnvironment().setup()
    yield e
    e.teardown()


# ═══════════════════════════════════════════════════════════════════════
# PART 1: Specialty Core
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyDefinitions:
    """Valida definições de especialidades."""

    def test_specialty_definition_creation(self):
        definition = SpecialtyDefinition(
            code="test",
            name="Test Specialty",
            description="A test specialty",
            category=SpecialtyCategory.MEDICAL,
            status=SpecialtyStatus.ACTIVE,
            capabilities={SpecialtyCapability.PROTOCOLS, SpecialtyCapability.DASHBOARD},
        )
        assert definition.code == "test"
        assert definition.name == "Test Specialty"
        assert definition.category == SpecialtyCategory.MEDICAL
        assert definition.has_capability(SpecialtyCapability.PROTOCOLS)
        assert not definition.has_capability(SpecialtyCapability.AGENT_SUPPORT)

    def test_specialty_definition_to_dict(self):
        definition = SpecialtyDefinition(
            code="test",
            name="Test",
            capabilities={SpecialtyCapability.PROTOCOLS},
        )
        d = definition.to_dict()
        assert d["code"] == "test"
        assert "protocols" in d["capabilities"]

    def test_all_categories_exist(self):
        assert SpecialtyCategory.MEDICAL.value == "medical"
        assert SpecialtyCategory.MULTIPROFESSIONAL.value == "multiprofessional"
        assert SpecialtyCategory.PARAMEDICAL.value == "paramedical"
        assert SpecialtyCategory.DIAGNOSTIC.value == "diagnostic"
        assert SpecialtyCategory.SURGICAL.value == "surgical"
        assert SpecialtyCategory.INTEGRATIVE.value == "integrative"

    def test_all_statuses_exist(self):
        assert SpecialtyStatus.ACTIVE.value == "active"
        assert SpecialtyStatus.BETA.value == "beta"
        assert SpecialtyStatus.EXPERIMENTAL.value == "experimental"
        assert SpecialtyStatus.DEPRECATED.value == "deprecated"
        assert SpecialtyStatus.PLANNED.value == "planned"

    def test_all_capabilities_exist(self):
        assert SpecialtyCapability.CLINICAL_PROFILE.value == "clinical_profile"
        assert SpecialtyCapability.SPECIALTY_TIMELINE.value == "specialty_timeline"
        assert SpecialtyCapability.PROTOCOLS.value == "protocols"
        assert SpecialtyCapability.SCALES.value == "scales"
        assert SpecialtyCapability.WORKFLOWS.value == "workflows"
        assert SpecialtyCapability.DASHBOARD.value == "dashboard"
        assert SpecialtyCapability.AGENT_SUPPORT.value == "agent_support"


class TestSpecialtyProfile:
    """Valida perfis especializados."""

    def test_profile_field_management(self):
        profile = CannabisProfile("p_001", "t_001")

        profile.add_field(SpecialtyField(
            name="thc_dose", value=25.0, unit="mg", field_type="number"
        ))
        profile.add_field(SpecialtyField(
            name="cbd_dose", value=10.0, unit="mg", field_type="number"
        ))

        assert len(profile.list_fields()) == 2
        assert profile.get_field_value("thc_dose") == 25.0
        assert profile.get_field_value("missing", "default") == "default"

    def test_profile_score_management(self):
        profile = CannabisProfile("p_001", "t_001")

        profile.add_score(SpecialtyScore(
            scale_name="pain_scale", score=7.0, max_score=10.0
        ))
        profile.add_score(SpecialtyScore(
            scale_name="pain_scale", score=5.0, max_score=10.0
        ))

        scores = profile.get_scores("pain_scale")
        assert len(scores) == 2

        latest = profile.get_latest_score("pain_scale")
        assert latest.score == 5.0

    def test_profile_validation_stub(self):
        profile = CannabisProfile("p_001", "t_001")
        errors = profile.validate()
        assert isinstance(errors, list)
        assert profile.is_valid()

    def test_profile_to_dict(self):
        profile = CannabisProfile("p_001", "t_001")
        profile.add_field(SpecialtyField(name="test", value="value"))
        profile.add_score(SpecialtyScore(scale_name="s1", score=5.0))

        d = profile.to_dict()
        assert d["patient_id"] == "p_001"
        assert d["tenant_id"] == "t_001"
        assert d["specialty_code"] == "cannabis"
        assert d["field_count"] == 1
        assert d["score_count"] == 1

    def test_profile_get_definition(self):
        profile = CannabisProfile("p_001", "t_001")
        definition = profile.get_definition()
        assert definition.code == "cannabis"
        assert definition.name == "Cannabis Medicinal"


class TestSpecialtyTimeline:
    """Valida timeline especializada."""

    def test_timeline_event_creation(self):
        event = SpecialtyTimelineEvent(
            event_id="evt_001",
            specialty_code="cannabis",
            event_type="dose_change",
            title="Aumento de dose THC",
            value_before=20.0,
            value_after=25.0,
            unit="mg",
        )
        assert event.specialty_code == "cannabis"
        assert event.event_type == "dose_change"
        assert event.value_before == 20.0
        assert event.value_after == 25.0

    def test_timeline_event_to_timeline_entry(self):
        from datetime import datetime, timezone

        event = SpecialtyTimelineEvent(
            event_id="evt_001",
            specialty_code="cannabis",
            event_type="dose_change",
            title="Dose alterada",
            event_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )

        entry = event.to_timeline_entry("p_001", "t_001")
        assert entry.tenant_id == "t_001"
        assert entry.patient_id == "p_001"
        assert entry.event_category == "specialty"
        assert "SPECIALTY_DOSE_CHANGE" in entry.event_type

    def test_specialty_timeline(self):
        timeline = SpecialtyTimeline("cannabis", "p_001")

        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e1", specialty_code="cannabis", event_type="dose_change",
            title="Dose 1", value_after=10.0,
        ))
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e2", specialty_code="cannabis", event_type="dose_change",
            title="Dose 2", value_after=15.0,
        ))

        assert len(timeline.get_events()) == 2
        assert timeline.get_latest_event("dose_change").value_after == 15.0

    def test_timeline_to_dict(self):
        timeline = SpecialtyTimeline("cannabis", "p_001")
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e1", specialty_code="cannabis", event_type="test",
            title="Test",
        ))

        d = timeline.to_dict()
        assert d["specialty_code"] == "cannabis"
        assert d["patient_id"] == "p_001"
        assert d["event_count"] == 1


class TestSpecialtyProtocol:
    """Valida protocolos especializados."""

    def test_protocol_creation(self):
        protocol = SpecialtyProtocol(
            protocol_id="proto_001",
            specialty_code="cannabis",
            name="Protocolo de Acompanhamento Cannabis",
        )
        assert protocol.specialty_code == "cannabis"
        assert protocol.name == "Protocolo de Acompanhamento Cannabis"

    def test_protocol_steps(self):
        protocol = SpecialtyProtocol(
            protocol_id="proto_001",
            specialty_code="cannabis",
            name="Protocolo Cannabis",
        )

        protocol.add_step(ProtocolStep(
            step_id="s1", order=1, step_type=ProtocolStepType.ASSESSMENT,
            title="Avaliação inicial",
        ))
        protocol.add_step(ProtocolStep(
            step_id="s2", order=2, step_type=ProtocolStepType.PRESCRIPTION,
            title="Prescrição inicial",
        ))

        steps = protocol.get_steps_ordered()
        assert len(steps) == 2
        assert steps[0].order == 1
        assert steps[1].order == 2

    def test_protocol_trigger(self):
        protocol = SpecialtyProtocol(
            protocol_id="proto_001",
            specialty_code="cannabis",
            name="Protocolo Cannabis",
            triggers=[ProtocolTrigger.DIAGNOSIS, ProtocolTrigger.SCHEDULED],
        )

        assert protocol.can_trigger(ProtocolTrigger.DIAGNOSIS)
        assert not protocol.can_trigger(ProtocolTrigger.ALERT)


class TestSpecialtyWorkflow:
    """Valida workflows especializados."""

    def test_workflow_creation(self):
        workflow = SpecialtyWorkflow(
            workflow_id="wf_001",
            specialty_code="cannabis",
            name="Acompanhamento Cannabis",
        )
        assert workflow.specialty_code == "cannabis"
        assert workflow.name == "Acompanhamento Cannabis"

    def test_workflow_checkpoints(self):
        workflow = SpecialtyWorkflow("wf_001", "cannabis", "Acompanhamento")
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp1", phase=WorkflowPhase.INTAKE,
            title="Cadastro inicial",
        ))
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp2", phase=WorkflowPhase.TREATMENT,
            title="Início do tratamento",
        ))

        assert len(workflow.get_checkpoints()) == 2
        assert len(workflow.get_checkpoints(WorkflowPhase.INTAKE)) == 1

    def test_workflow_instance(self):
        workflow = SpecialtyWorkflow("wf_001", "cannabis", "Acompanhamento")
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp1", phase=WorkflowPhase.INTAKE, title="Cadastro",
        ))

        instance = workflow.create_instance("inst_001", "p_001", "t_001")
        assert instance.patient_id == "p_001"
        assert instance.status == WorkflowStatus.PENDING
        assert instance.current_phase == WorkflowPhase.INTAKE

        instance.complete_checkpoint("cp1")
        assert instance.is_checkpoint_completed("cp1")
        assert not instance.is_checkpoint_completed("cp2")


class TestSpecialtyDashboard:
    """Valida dashboards especializados."""

    def test_dashboard_creation(self):
        dashboard = SpecialtyDashboard("cannabis", "Dashboard Cannabis")
        assert dashboard.specialty_code == "cannabis"
        assert dashboard.name == "Dashboard Cannabis"

    def test_kpi_management(self):
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_kpi(SpecialtyKPI(
            kpi_id="k1", name="Dose Média THC", value=25.0, unit="mg",
            threshold_warning=50.0, threshold_critical=100.0,
        ))
        dashboard.add_kpi(SpecialtyKPI(
            kpi_id="k2", name="Pacientes Ativos", value=42,
        ))

        assert len(dashboard.get_kpis()) == 2

    def test_kpi_evaluation(self):
        kpi = SpecialtyKPI(
            kpi_id="k1", name="Dose", value=75.0,
            threshold_warning=50.0, threshold_critical=100.0,
        )
        assert kpi.evaluate() == KpiSeverity.WARNING

        kpi2 = SpecialtyKPI(
            kpi_id="k2", name="Dose", value=120.0,
            threshold_warning=50.0, threshold_critical=100.0,
        )
        assert kpi2.evaluate() == KpiSeverity.CRITICAL

    def test_metric_management(self):
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_metric(SpecialtyMetric(
            metric_id="m1", name="Média de Doses", metric_type=MetricType.AVERAGE,
            value=25.0, unit="mg",
        ))

        metrics = dashboard.get_metrics(MetricType.AVERAGE)
        assert len(metrics) == 1
        assert metrics[0].value == 25.0

    def test_chart_management(self):
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_chart(SpecialtyChart(
            chart_id="c1", name="Evolução de Dose", chart_type=ChartType.LINE,
            data={"x": [1, 2, 3], "y": [10, 15, 20]},
        ))

        charts = dashboard.get_charts(ChartType.LINE)
        assert len(charts) == 1

    def test_dashboard_to_dict(self):
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_kpi(SpecialtyKPI(kpi_id="k1", name="KPI", value=1))
        dashboard.add_metric(SpecialtyMetric(metric_id="m1", name="M", metric_type=MetricType.COUNT, value=1))
        dashboard.add_chart(SpecialtyChart(chart_id="c1", name="C", chart_type=ChartType.TABLE))

        d = dashboard.to_dict()
        assert d["specialty_code"] == "cannabis"
        assert d["kpi_count"] == 1
        assert d["metric_count"] == 1
        assert d["chart_count"] == 1

    def test_metrics_collector(self):
        collector = SpecialtyMetricsCollector("cannabis")
        collector.record(SpecialtyMetric(metric_id="m1", name="M1", metric_type=MetricType.COUNT, value=1))
        collector.record(SpecialtyMetric(metric_id="m2", name="M2", metric_type=MetricType.AVERAGE, value=2.0))

        summary = collector.get_summary()
        assert summary["specialty_code"] == "cannabis"
        assert summary["total_metrics"] == 2


# ═══════════════════════════════════════════════════════════════════════
# PART 2: Specialty Registry
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyRegistry:
    """Valida registro dinâmico de especialidades."""

    def test_register_and_get(self):
        registry = SpecialtyRegistry()
        definition = SpecialtyDefinition(code="test", name="Test")

        registry.register(definition)
        assert registry.is_registered("test")
        assert registry.get("test").name == "Test"

    def test_unregister(self):
        registry = SpecialtyRegistry()
        registry.register(SpecialtyDefinition(code="test", name="Test"))
        assert registry.unregister("test") is True
        assert not registry.is_registered("test")

    def test_list_by_category(self):
        registry = SpecialtyRegistry()
        registry.register(SpecialtyDefinition(code="med1", name="Med1", category=SpecialtyCategory.MEDICAL))
        registry.register(SpecialtyDefinition(code="int1", name="Int1", category=SpecialtyCategory.INTEGRATIVE))

        medical = registry.list_by_category(SpecialtyCategory.MEDICAL)
        assert len(medical) == 1
        assert medical[0].code == "med1"

    def test_list_by_capability(self):
        registry = SpecialtyRegistry()
        registry.register(SpecialtyDefinition(
            code="c1", name="C1",
            capabilities={SpecialtyCapability.PROTOCOLS},
        ))
        registry.register(SpecialtyDefinition(
            code="c2", name="C2",
            capabilities={SpecialtyCapability.DASHBOARD},
        ))

        with_protocols = registry.list_by_capability(SpecialtyCapability.PROTOCOLS)
        assert len(with_protocols) == 1
        assert with_protocols[0].code == "c1"

    def test_dependency_resolution(self):
        registry = SpecialtyRegistry()
        registry.register(SpecialtyDefinition(code="base", name="Base"))
        registry.register(SpecialtyDefinition(code="derived", name="Derived", dependencies=["base"]))

        missing = registry.check_dependencies("derived")
        assert len(missing) == 0

        missing = registry.check_dependencies("unknown")
        assert len(missing) == 1

    def test_topological_sort(self):
        registry = SpecialtyRegistry()
        registry.register(SpecialtyDefinition(code="a", name="A"))
        registry.register(SpecialtyDefinition(code="b", name="B", dependencies=["a"]))
        registry.register(SpecialtyDefinition(code="c", name="C", dependencies=["b"]))

        order = registry.resolve_dependency_order()
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    def test_register_all_stubs(self):
        registry = SpecialtyRegistry()
        for definition in ALL_SPECIALTY_DEFINITIONS:
            registry.register(definition)

        assert len(registry.list_all()) == 8
        assert registry.is_registered("cannabis")
        assert registry.is_registered("cardiology")
        assert registry.is_registered("psychiatry")

    def test_registry_summary(self):
        registry = SpecialtyRegistry()
        for definition in ALL_SPECIALTY_DEFINITIONS:
            registry.register(definition)

        summary = registry.summary()
        assert summary["total_specialties"] == 8
        assert "cannabis" in summary["codes"]


# ═══════════════════════════════════════════════════════════════════════
# PART 3: Specialty Profile Contract
# ═══════════════════════════════════════════════════════════════════════

class TestProfileContract:
    """Valida contrato de profile."""

    def test_all_stub_profiles_inherit_base(self):
        profiles = [
            CannabisProfile("p1", "t1"),
            NutrologyProfile("p1", "t1"),
            PsychiatryProfile("p1", "t1"),
            PsychologyProfile("p1", "t1"),
            CardiologyProfile("p1", "t1"),
            NephrologyProfile("p1", "t1"),
            PulmonologyProfile("p1", "t1"),
            InfectologyProfile("p1", "t1"),
        ]

        for profile in profiles:
            assert isinstance(profile, SpecialtyProfile)
            assert profile.is_valid()
            definition = profile.get_definition()
            assert definition.code is not None
            assert definition.name is not None


# ═══════════════════════════════════════════════════════════════════════
# PART 4: Specialty Timeline (Clinical Timeline Integration)
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyTimelineIntegration:
    """Valida integração com Clinical Timeline."""

    def test_timeline_entry_conversion(self):
        event = SpecialtyTimelineEvent(
            event_id="evt_001",
            specialty_code="cannabis",
            event_type="dose_change",
            title="Aumento de dose",
            description="THC de 20mg para 25mg",
            value_before=20.0,
            value_after=25.0,
            unit="mg",
        )

        entry = event.to_timeline_entry("p_001", "t_001")
        assert entry.event_category == "specialty"
        assert entry.entity_data["specialty_code"] == "cannabis"
        assert entry.entity_data["value_before"] == 20.0
        assert entry.entity_data["value_after"] == 25.0
        assert entry.metadata["specialty_event"] is True

    def test_timeline_to_entries(self):
        timeline = SpecialtyTimeline("cannabis", "p_001")
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e1", specialty_code="cannabis", event_type="dose_change",
            title="Dose 1", value_after=10.0,
        ))
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e2", specialty_code="cannabis", event_type="dose_change",
            title="Dose 2", value_after=15.0,
        ))

        entries = timeline.to_timeline_entries("t_001")
        assert len(entries) == 2
        assert all(e.tenant_id == "t_001" for e in entries)
        assert all(e.patient_id == "p_001" for e in entries)


# ═══════════════════════════════════════════════════════════════════════
# PART 5: Specialty Knowledge (Knowledge Layer Integration)
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyKnowledge:
    """Valida integração com Knowledge Layer."""

    def test_index_protocol(self):
        repo = InMemoryKnowledgeRepository()
        source = SpecialtyKnowledgeSource(repo, "t_001")

        protocol = SpecialtyProtocol(
            protocol_id="proto_001",
            specialty_code="cannabis",
            name="Protocolo Cannabis",
        )
        protocol.add_step(ProtocolStep(
            step_id="s1", order=1, step_type=ProtocolStepType.ASSESSMENT,
            title="Avaliação",
        ))

        doc = source.index_protocol(protocol)
        assert doc.knowledge_type.value == "clinical"
        assert "cannabis" in doc.metadata.tags
        assert len(doc.chunks) == 1

    def test_index_template(self):
        repo = InMemoryKnowledgeRepository()
        source = SpecialtyKnowledgeSource(repo, "t_001")

        doc = source.index_template(
            specialty_code="cannabis",
            title="Evolução Cannabis",
            content="Template de evolução...",
        )
        assert doc.source_type.value == "template"
        assert "cannabis" in doc.metadata.tags

    def test_index_scale(self):
        repo = InMemoryKnowledgeRepository()
        source = SpecialtyKnowledgeSource(repo, "t_001")

        doc = source.index_scale_document(
            specialty_code="psychiatry",
            scale_name="PHQ-9",
            scale_description="Escala de depressão",
            items=["Item 1", "Item 2", "Item 3"],
        )
        assert "PHQ-9" in doc.title
        assert "psychiatry" in doc.metadata.tags

    def test_search_specialty_knowledge(self):
        repo = InMemoryKnowledgeRepository()
        source = SpecialtyKnowledgeSource(repo, "t_001")

        source.index_template("cannabis", "Protocolo Dose", "Conteúdo do protocolo")
        source.index_template("cardiology", "Protocolo HAS", "Conteúdo de hipertensão")

        results = source.search("cannabis", "protocolo")
        assert len(results) == 1
        assert results[0].metadata.tags[1] == "cannabis"

    def test_get_specialty_knowledge(self):
        repo = InMemoryKnowledgeRepository()
        source = SpecialtyKnowledgeSource(repo, "t_001")

        source.index_template("cannabis", "Doc 1", "Content 1")
        source.index_template("cannabis", "Doc 2", "Content 2")
        source.index_template("cardiology", "Doc 3", "Content 3")

        docs = source.get_specialty_knowledge("cannabis")
        assert len(docs) == 2


# ═══════════════════════════════════════════════════════════════════════
# PART 6: Specialty Workflows
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyWorkflows:
    """Valida workflows especializados."""

    def test_workflow_phases(self):
        workflow = SpecialtyWorkflow("wf_001", "cannabis", "Follow-up")
        workflow.add_checkpoint(WorkflowCheckpoint("cp1", WorkflowPhase.INTAKE, "Cadastro"))
        workflow.add_checkpoint(WorkflowCheckpoint("cp2", WorkflowPhase.TREATMENT, "Início"))
        workflow.add_checkpoint(WorkflowCheckpoint("cp3", WorkflowPhase.MONITORING, "Monitoramento"))
        workflow.add_checkpoint(WorkflowCheckpoint("cp4", WorkflowPhase.FOLLOW_UP, "Retorno"))

        phases = workflow.get_phases()
        assert len(phases) == 4
        assert WorkflowPhase.INTAKE in phases
        assert WorkflowPhase.COMPLETION not in phases

    def test_workflow_to_dict(self):
        workflow = SpecialtyWorkflow("wf_001", "cannabis", "Follow-up")
        workflow.add_checkpoint(WorkflowCheckpoint("cp1", WorkflowPhase.INTAKE, "Cadastro"))

        d = workflow.to_dict()
        assert d["workflow_id"] == "wf_001"
        assert d["checkpoint_count"] == 1
        assert "intake" in d["phases"]


# ═══════════════════════════════════════════════════════════════════════
# PART 7: Specialty Dashboards
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyDashboards:
    """Valida dashboards e KPIs."""

    def test_dashboard_kpi_filter_by_severity(self):
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_kpi(SpecialtyKPI(
            kpi_id="k1", name="Dose Alta", value=120.0,
            threshold_warning=50.0, threshold_critical=100.0,
            severity=KpiSeverity.CRITICAL,
        ))
        dashboard.add_kpi(SpecialtyKPI(
            kpi_id="k2", name="Dose Média", value=75.0,
            threshold_warning=50.0, threshold_critical=100.0,
            severity=KpiSeverity.WARNING,
        ))
        dashboard.add_kpi(SpecialtyKPI(
            kpi_id="k3", name="Dose Baixa", value=25.0,
            threshold_warning=50.0, threshold_critical=100.0,
            severity=KpiSeverity.NORMAL,
        ))

        critical = dashboard.get_kpis(KpiSeverity.CRITICAL)
        assert len(critical) == 1
        assert critical[0].kpi_id == "k1"

    def test_dashboard_chart_filter_by_type(self):
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_chart(SpecialtyChart("c1", "Line Chart", ChartType.LINE))
        dashboard.add_chart(SpecialtyChart("c2", "Bar Chart", ChartType.BAR))
        dashboard.add_chart(SpecialtyChart("c3", "Table", ChartType.TABLE))

        lines = dashboard.get_charts(ChartType.LINE)
        assert len(lines) == 1


# ═══════════════════════════════════════════════════════════════════════
# PART 8: Specialty Agents
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyAgents:
    """Valida integração com Agent Runtime."""

    @pytest.mark.asyncio
    async def test_specialty_agent_subclass(self):
        class TestAgent(SpecialtyAgent):
            def __init__(self):
                super().__init__(
                    agent_id="test_agent",
                    name="Test Agent",
                    version="1.0.0",
                    capabilities=[],
                    required_permissions=[],
                )

            @property
            def specialty_code(self) -> str:
                return "test"

        agent = TestAgent()
        assert agent.specialty_code == "test"

        result = await agent.execute(AgentContext(
            tenant_context=TenantContext(tenant_id="t_001"),
            identity_context=IdentityContext(
                actor_id="user_001", actor_type=ActorType.USER,
                tenant_id="t_001", organization_id="t_001",
            ),
        ))
        assert result.success is True
        assert result.output["specialty_code"] == "test"

    def test_specialty_agent_capabilities(self):
        class TestAgent(SpecialtyAgent):
            def __init__(self):
                super().__init__(
                    agent_id="test_agent",
                    name="Test Agent",
                    version="1.0.0",
                    capabilities=[],
                    required_permissions=[],
                )

            @property
            def specialty_code(self) -> str:
                return "test"

        agent = TestAgent()
        caps = agent.get_specialty_capabilities()
        assert len(caps) >= 2
        assert any(c == AgentCapability.CLINICAL_SUMMARY for c in caps)

    def test_specialty_agent_to_dict(self):
        class TestAgent(SpecialtyAgent):
            def __init__(self):
                super().__init__(
                    agent_id="test_agent",
                    name="Test Agent",
                    version="1.0.0",
                    capabilities=[],
                    required_permissions=[],
                )

            @property
            def specialty_code(self) -> str:
                return "test"

        agent = TestAgent()
        d = agent.to_dict()
        assert d["specialty_code"] == "test"


# ═══════════════════════════════════════════════════════════════════════
# PART 9: First Implementation Stubs
# ═══════════════════════════════════════════════════════════════════════

class TestSpecialtyStubs:
    """Valida stubs das 8 especialidades."""

    def test_all_definitions_present(self):
        assert len(ALL_SPECIALTY_DEFINITIONS) == 8

    def test_cannabis_stub(self):
        assert CANNABIS_DEFINITION.code == "cannabis"
        assert SpecialtyCapability.DOSE_TRACKING in CANNABIS_DEFINITION.capabilities
        profile = CannabisProfile("p1", "t1")
        assert profile.specialty_code == "cannabis"

    def test_nutrology_stub(self):
        assert NUTROLOGY_DEFINITION.code == "nutrology"
        assert NUTROLOGY_DEFINITION.category == SpecialtyCategory.MEDICAL

    def test_psychiatry_stub(self):
        assert PSYCHIATRY_DEFINITION.code == "psychiatry"
        assert SpecialtyCapability.SCALES in PSYCHIATRY_DEFINITION.capabilities
        assert SpecialtyCapability.QUESTIONNAIRES in PSYCHIATRY_DEFINITION.capabilities

    def test_psychology_stub(self):
        assert PSYCHOLOGY_DEFINITION.code == "psychology"
        assert PSYCHOLOGY_DEFINITION.category == SpecialtyCategory.MULTIPROFESSIONAL

    def test_cardiology_stub(self):
        assert CARDIOLOGY_DEFINITION.code == "cardiology"
        assert CARDIOLOGY_DEFINITION.category == SpecialtyCategory.MEDICAL

    def test_nephrology_stub(self):
        assert NEPHROLOGY_DEFINITION.code == "nephrology"

    def test_pulmonology_stub(self):
        assert PULMONOLOGY_DEFINITION.code == "pulmonology"

    def test_infectology_stub(self):
        assert INFECTOLOGY_DEFINITION.code == "infectology"


# ═══════════════════════════════════════════════════════════════════════
# PART 10: Validation — Integration with Platform Layers
# ═══════════════════════════════════════════════════════════════════════

class TestPlatformIntegration:
    """Valida integração com as camadas da plataforma."""

    def test_specialty_registry_with_all_stubs(self):
        """Registro dinâmico de todas as especialidades."""
        registry = SpecialtyRegistry()

        for definition in ALL_SPECIALTY_DEFINITIONS:
            registry.register(definition)

        # Verificar todas registradas
        for definition in ALL_SPECIALTY_DEFINITIONS:
            assert registry.is_registered(definition.code)

        # Verificar categorias
        medical = registry.list_by_category(SpecialtyCategory.MEDICAL)
        assert len(medical) == 6  # nutrology, psychiatry, cardiology, nephrology, pulmonology, infectology

        integrative = registry.list_by_category(SpecialtyCategory.INTEGRATIVE)
        assert len(integrative) == 1  # cannabis

        multiprof = registry.list_by_category(SpecialtyCategory.MULTIPROFESSIONAL)
        assert len(multiprof) == 1  # psychology

    def test_profile_creation_for_all_specialties(self):
        """Criação de perfis especializados."""
        profiles = [
            CannabisProfile("p1", "t1"),
            NutrologyProfile("p1", "t1"),
            PsychiatryProfile("p1", "t1"),
            PsychologyProfile("p1", "t1"),
            CardiologyProfile("p1", "t1"),
            NephrologyProfile("p1", "t1"),
            PulmonologyProfile("p1", "t1"),
            InfectologyProfile("p1", "t1"),
        ]

        for profile in profiles:
            # Adicionar campos e scores
            profile.add_field(SpecialtyField(name="test_field", value="test"))
            profile.add_score(SpecialtyScore(scale_name="test_scale", score=5.0))

            # Validar
            assert profile.is_valid()
            assert len(profile.list_fields()) == 1
            assert len(profile.get_scores()) == 1

            # Verificar definição
            definition = profile.get_definition()
            assert definition.code == profile.specialty_code

    @pytest.mark.asyncio
    async def test_digital_twin_integration(self, env):
        """Integração com Digital Twin."""
        env.create_patient_with_data()

        from araos.clinical.twin.models import PatientDigitalTwinBuilder
        from araos.clinical.repository import InMemoryClinicalRepository

        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)

        # Criar profile especializado com dados do twin
        profile = CannabisProfile(env.patient_id, env.tenant_id)

        # Extrair dados do twin para o profile
        if twin.active_diagnoses:
            profile.add_field(SpecialtyField(
                name="active_diagnoses_count",
                value=len(twin.active_diagnoses),
                field_type="number",
            ))

        if twin.active_medications:
            profile.add_field(SpecialtyField(
                name="active_medications_count",
                value=len(twin.active_medications),
                field_type="number",
            ))

        assert profile.get_field_value("active_diagnoses_count") > 0
        assert profile.get_field_value("active_medications_count") > 0
        assert profile.is_valid()

    def test_knowledge_layer_integration(self):
        """Integração com Knowledge Layer."""
        repo = InMemoryKnowledgeRepository()
        source = SpecialtyKnowledgeSource(repo, "t_001")

        # Indexar protocolos de múltiplas especialidades
        cannabis_protocol = SpecialtyProtocol(
            protocol_id="cp001", specialty_code="cannabis",
            name="Protocolo Cannabis",
        )
        cannabis_protocol.add_step(ProtocolStep(
            step_id="s1", order=1, step_type=ProtocolStepType.ASSESSMENT,
            title="Avaliação",
        ))

        cardiology_protocol = SpecialtyProtocol(
            protocol_id="cardp001", specialty_code="cardiology",
            name="Protocolo HAS",
        )
        cardiology_protocol.add_step(ProtocolStep(
            step_id="s1", order=1, step_type=ProtocolStepType.MEASUREMENT,
            title="Medir PA",
        ))

        source.index_protocol(cannabis_protocol)
        source.index_protocol(cardiology_protocol)

        # Buscar conhecimento específico
        cannabis_docs = source.get_specialty_knowledge("cannabis")
        cardiology_docs = source.get_specialty_knowledge("cardiology")

        assert len(cannabis_docs) == 1
        assert len(cardiology_docs) == 1
        assert "cannabis" in cannabis_docs[0].metadata.tags
        assert "cardiology" in cardiology_docs[0].metadata.tags

    @pytest.mark.asyncio
    async def test_agent_runtime_integration(self):
        """Integração com Agent Runtime."""
        class CannabisSpecialtyAgent(SpecialtyAgent):
            def __init__(self):
                super().__init__(
                    agent_id="cannabis_agent",
                    name="Cannabis Agent",
                    version="1.0.0",
                    capabilities=[],
                    required_permissions=[],
                )

            @property
            def specialty_code(self) -> str:
                return "cannabis"

        agent = CannabisSpecialtyAgent()
        tenant_ctx = TenantContext(tenant_id="t_001")
        identity_ctx = IdentityContext(
            actor_id="user_001", actor_type=ActorType.USER,
            tenant_id="t_001", organization_id="t_001",
        )
        context = AgentContext(tenant_context=tenant_ctx, identity_context=identity_ctx)

        result = await agent.execute(context)
        assert result.success is True
        assert result.output["specialty_code"] == "cannabis"

        specialty_context = agent.get_specialty_context(context)
        assert specialty_context["specialty_code"] == "cannabis"

    def test_timeline_integration(self):
        """Integração de timeline especializada com Clinical Timeline."""
        timeline = SpecialtyTimeline("cannabis", "p_001")

        # Adicionar eventos especializados
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e1", specialty_code="cannabis", event_type="dose_change",
            title="Início THC 10mg", value_after=10.0, unit="mg",
        ))
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e2", specialty_code="cannabis", event_type="dose_change",
            title="Aumento THC 15mg", value_after=15.0, unit="mg",
        ))
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e3", specialty_code="cannabis", event_type="scale_score",
            title="EVA 3/10", value_after=3.0, unit="points",
        ))

        # Converter para TimelineEntry
        entries = timeline.to_timeline_entries("t_001")
        assert len(entries) == 3

        # Verificar que cada entry tem os dados certos
        for entry in entries:
            assert entry.tenant_id == "t_001"
            assert entry.patient_id == "p_001"
            assert entry.event_category == "specialty"
            assert entry.metadata["specialty_event"] is True

    def test_workflow_integration(self):
        """Integração de workflow especializado."""
        # Criar workflow de acompanhamento
        workflow = SpecialtyWorkflow(
            workflow_id="cannabis_followup",
            specialty_code="cannabis",
            name="Acompanhamento Cannabis",
        )

        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp_intake", phase=WorkflowPhase.INTAKE,
            title="Anamnese e avaliação inicial",
            required_fields=["main_complaint", "previous_treatments"],
        ))
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp_start", phase=WorkflowPhase.TREATMENT,
            title="Início do tratamento",
            required_fields=["initial_dose", "prescription_date"],
        ))
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp_7d", phase=WorkflowPhase.MONITORING,
            title="Avaliação 7 dias",
            due_days_from_start=7,
        ))
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp_30d", phase=WorkflowPhase.MONITORING,
            title="Avaliação 30 dias",
            due_days_from_start=30,
        ))

        # Criar instância
        instance = workflow.create_instance("inst_001", "p_001", "t_001")
        assert instance.status == WorkflowStatus.PENDING
        assert instance.current_phase == WorkflowPhase.INTAKE

        # Completar checkpoints
        instance.complete_checkpoint("cp_intake")
        instance.complete_checkpoint("cp_start")
        assert len(instance.completed_checkpoints) == 2
        assert instance.is_checkpoint_completed("cp_intake")
        assert not instance.is_checkpoint_completed("cp_7d")

        # Verificar fases
        phases = workflow.get_phases()
        assert len(phases) == 3  # intake, treatment, monitoring

    def test_dashboard_integration(self):
        """Integração de dashboard especializado."""
        dashboard = SpecialtyDashboard("cannabis", "Dashboard Cannabis Medicinal")

        # KPIs
        dashboard.add_kpi(SpecialtyKPI(
            kpi_id="active_patients", name="Pacientes Ativos",
            value=42, target=50,
        ))
        dashboard.add_kpi(SpecialtyKPI(
            kpi_id="avg_thc_dose", name="Dose Média THC",
            value=22.5, unit="mg", target=20.0,
            threshold_warning=40.0, threshold_critical=80.0,
        ))

        # Métricas
        dashboard.add_metric(SpecialtyMetric(
            metric_id="total_consultations", name="Total de Consultas",
            metric_type=MetricType.COUNT, value=128,
        ))
        dashboard.add_metric(SpecialtyMetric(
            metric_id="avg_pain_reduction", name="Redução Média de Dor",
            metric_type=MetricType.AVERAGE, value=3.2, unit="points",
            trend_direction="up",
        ))

        # Gráficos
        dashboard.add_chart(SpecialtyChart(
            chart_id="dose_evolution", name="Evolução de Dose",
            chart_type=ChartType.LINE,
            data={"months": ["Jan", "Fev", "Mar"], "doses": [10, 15, 20]},
        ))
        dashboard.add_chart(SpecialtyChart(
            chart_id="patient_distribution", name="Distribuição por Indicação",
            chart_type=ChartType.PIE,
            data={"labels": ["Dor", "Ansiedade", "Epilepsia"], "values": [50, 30, 20]},
        ))

        d = dashboard.to_dict()
        assert d["specialty_code"] == "cannabis"
        assert d["kpi_count"] == 2
        assert d["metric_count"] == 2
        assert d["chart_count"] == 2

        # Verificar severidade do KPI
        avg_dose = [k for k in dashboard.get_kpis() if k.kpi_id == "avg_thc_dose"][0]
        assert avg_dose.evaluate() == KpiSeverity.NORMAL  # 22.5 < 40

    def test_full_specialty_lifecycle(self):
        """Ciclo completo de uma especialidade na plataforma."""
        # 1. Registrar especialidade
        registry = SpecialtyRegistry()
        registry.register(CANNABIS_DEFINITION)

        # 2. Criar profile
        profile = CannabisProfile("p_001", "t_001")
        profile.add_field(SpecialtyField(name="thc_dose", value=25.0, unit="mg"))
        profile.add_field(SpecialtyField(name="cbd_dose", value=10.0, unit="mg"))
        profile.add_score(SpecialtyScore(scale_name="EVA", score=3.0, max_score=10.0))

        # 3. Criar timeline
        timeline = SpecialtyTimeline("cannabis", "p_001")
        timeline.add_event(SpecialtyTimelineEvent(
            event_id="e1", specialty_code="cannabis", event_type="dose_change",
            title="Ajuste de dose", value_before=20.0, value_after=25.0, unit="mg",
        ))

        # 4. Criar protocolo
        protocol = SpecialtyProtocol(
            protocol_id="cannabis_001", specialty_code="cannabis",
            name="Protocolo Cannabis Dor Crônica",
        )
        protocol.add_step(ProtocolStep(
            step_id="s1", order=1, step_type=ProtocolStepType.ASSESSMENT,
            title="Avaliação EVA e qualidade de vida",
        ))
        protocol.add_step(ProtocolStep(
            step_id="s2", order=2, step_type=ProtocolStepType.PRESCRIPTION,
            title="Prescrição inicial THC+CBD",
        ))

        # 5. Criar workflow
        workflow = SpecialtyWorkflow(
            workflow_id="cannabis_wf_001", specialty_code="cannabis",
            name="Acompanhamento Cannabis",
        )
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp1", phase=WorkflowPhase.INTAKE, title="Avaliação inicial",
        ))
        workflow.add_checkpoint(WorkflowCheckpoint(
            checkpoint_id="cp2", phase=WorkflowPhase.MONITORING, title="7 dias",
            due_days_from_start=7,
        ))

        # 6. Criar dashboard
        dashboard = SpecialtyDashboard("cannabis")
        dashboard.add_kpi(SpecialtyKPI(kpi_id="k1", name="Pacientes", value=10))
        dashboard.add_metric(SpecialtyMetric(
            metric_id="m1", name="Média EVA", metric_type=MetricType.AVERAGE, value=4.5,
        ))

        # 7. Indexar na Knowledge Layer
        repo = InMemoryKnowledgeRepository()
        knowledge = SpecialtyKnowledgeSource(repo, "t_001")
        knowledge.index_protocol(protocol)

        # 8. Verificar integridade
        assert registry.is_registered("cannabis")
        assert profile.is_valid()
        assert len(timeline.get_events()) == 1
        assert len(protocol.get_steps_ordered()) == 2
        assert len(workflow.get_checkpoints()) == 2
        assert dashboard.get_kpis()[0].value == 10
        assert len(knowledge.get_specialty_knowledge("cannabis")) == 1

        # 9. Converter timeline para entries clínicas
        entries = timeline.to_timeline_entries("t_001")
        assert len(entries) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
