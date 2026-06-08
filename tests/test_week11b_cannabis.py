"""
AraOS Week 11B — Cannabis Module V1 Tests

Valida:
    1. Cannabis Profile (condição, CID, objetivos, status, Digital Twin)
    2. Cannabis Medication Registry (produto, fabricante, canabinoides, via)
    3. Cannabis Dose Timeline (entries, events)
    4. Outcome Engine (melhora%, piora%, tendência, estabilidade)
    5. Outcome Timeline (score inicial, atual, melhor, pior, velocidade)
    6. Follow-up Integration (AdaptiveFollowupEngine)
    7. Alerts (AE, no response, adherence, patient request)
    8. Knowledge Integration (protocolos, produtos, escalas)
    9. Cannabis Agent (resumo, evolução, histórico, trust levels)
    10. Dashboard Models (sintomas, dose, adesão, resposta, alertas)
    11. Event Bus (7 novos eventos CANNABIS)
    12. Trust Levels em todas as respostas
"""

import pytest
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from araos.specialties.cannabis.profile.models import CannabisProfile, CannabisTherapeuticGoal
from araos.specialties.cannabis.medication.models import (
    CannabisProduct, CannabisMedication, CannabinoidProfile,
)
from araos.specialties.cannabis.dose.models import CannabisDoseEntry, CannabisDoseTimeline
from araos.specialties.cannabis.outcome.engine import (
    CannabisOutcome, OutcomeScore, OutcomeAnalysis, OutcomeEngine, TrendDirection,
)
from araos.specialties.cannabis.alerts.models import CannabisAlert, CannabisAlertManager, CannabisAlertType
from araos.specialties.cannabis.knowledge.source import CannabisKnowledgeSource
from araos.specialties.cannabis.agent.agent import CannabisAgent
from araos.specialties.cannabis.dashboard.models import (
    CannabisDashboardBuilder,
    SymptomEvolutionData,
    DoseEvolutionData,
    AdherenceData,
    ClinicalResponseData,
    AlertSummaryData,
)
from araos.specialties.cannabis.events.events import (
    cannabis_started_event,
    cannabis_product_added_event,
    cannabis_product_changed_event,
    cannabis_dose_changed_event,
    cannabis_outcome_recorded_event,
    cannabis_alert_triggered_event,
    cannabis_discontinued_event,
)

from araos.knowledge.repository import InMemoryKnowledgeRepository
from araos.followup.core.models import AlertSeverity, AlertStatus
from araos.intelligence.trust.levels import TrustLevel, SourceType
from araos.platform.events.catalog import EventCatalog


# ═══════════════════════════════════════════════════════════════════════
# PART 1: Cannabis Profile
# ═══════════════════════════════════════════════════════════════════════

class TestCannabisProfile:
    """Valida perfil especializado Cannabis."""

    def test_profile_creation(self):
        profile = CannabisProfile("p_001", "t_001")
        assert profile.specialty_code == "cannabis"
        assert profile.patient_id == "p_001"

    def test_main_condition(self):
        profile = CannabisProfile("p_001", "t_001")
        profile.set_main_condition("Dor Crônica", "M79.2")
        assert profile.get_field_value("main_condition") == "Dor Crônica"
        assert profile.get_field_value("main_condition_icd10") == "M79.2"

    def test_associated_conditions(self):
        profile = CannabisProfile("p_001", "t_001")
        profile.add_associated_condition("Ansiedade", "F41.1")
        conditions = profile.get_field_value("associated_conditions")
        assert len(conditions) == 1
        assert conditions[0]["condition"] == "Ansiedade"

    def test_therapeutic_goals(self):
        profile = CannabisProfile("p_001", "t_001")
        goal = CannabisTherapeuticGoal(
            goal_id="g1",
            description="Reduzir dor",
            target_symptom="pain",
            baseline_score=8.0,
            target_score=4.0,
        )
        profile.add_therapeutic_goal(goal)
        assert len(profile.get_goals()) == 1
        assert profile.get_goals("pain")[0].target_symptom == "pain"

    def test_profile_validation(self):
        profile = CannabisProfile("p_001", "t_001")
        errors = profile.validate()
        assert len(errors) > 0  # Sem dados = inválido

        profile.set_main_condition("Dor")
        profile.set_responsible_physician("dr_001")
        profile.add_therapeutic_goal(CannabisTherapeuticGoal(goal_id="g1", description="Reduzir dor"))
        assert len(profile.validate()) == 0

    def test_profile_to_dict(self):
        profile = CannabisProfile("p_001", "t_001")
        profile.set_main_condition("Dor")
        profile.add_therapeutic_goal(CannabisTherapeuticGoal(goal_id="g1", description="Reduzir dor"))
        d = profile.to_dict()
        assert d["specialty_code"] == "cannabis"
        assert "therapeutic_goals" in d


# ═══════════════════════════════════════════════════════════════════════
# PART 2: Cannabis Medication Registry
# ═══════════════════════════════════════════════════════════════════════

class TestCannabisMedication:
    """Valida registro de medicações."""

    def test_product_creation(self):
        product = CannabisProduct(
            product_id="prod_001",
            name="Cannabis Oil 500mg",
            manufacturer="GrowMed",
            formulation="oil",
            spectrum="full_spectrum",
            cannabinoids=CannabinoidProfile(cbd_mg=300, thc_mg=200),
            concentration="500mg/30ml",
            volume_ml=30.0,
            route="sublingual",
        )
        assert product.name == "Cannabis Oil 500mg"
        assert product.is_full_spectrum()
        assert not product.is_isolate()
        assert product.cannabinoids.cbd_mg == 300

    def test_cannabinoid_total(self):
        cp = CannabinoidProfile(cbd_mg=100, thc_mg=50, cbg_mg=25)
        assert cp.total_cannabinoids_mg() == 175

    def test_medication_lifecycle(self):
        product = CannabisProduct(product_id="p1", name="Test")
        med = CannabisMedication(
            medication_id="med_001",
            patient_id="pat_001",
            tenant_id="t_001",
            product=product,
            prescribed_dose_mg=25.0,
            frequency="2x/dia",
        )
        assert med.status == "active"
        med.pause()
        assert med.status == "paused"
        med.stop("adverse_effect")
        assert med.status == "discontinued"
        assert med.stopped_reason == "adverse_effect"

    def test_dose_calculation(self):
        product = CannabisProduct(
            product_id="p1", name="Test",
            cannabinoids=CannabinoidProfile(cbd_mg=300, thc_mg=200),
            volume_ml=30.0,
        )
        med = CannabisMedication(
            medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            product=product, prescribed_dose_mg=15.0,
        )
        # 15mg / 30ml = 0.5 ratio
        # THC: 200 * 0.5 = 100mg
        # CBD: 300 * 0.5 = 150mg
        assert med.get_thc_dose_mg() == 100.0
        assert med.get_cbd_dose_mg() == 150.0


# ═══════════════════════════════════════════════════════════════════════
# PART 3: Cannabis Dose Timeline
# ═══════════════════════════════════════════════════════════════════════

class TestCannabisDoseTimeline:
    """Valida timeline de doses."""

    def test_timeline_creation(self):
        timeline = CannabisDoseTimeline("pat_001", "t_001")
        assert timeline.patient_id == "pat_001"

    def test_add_entries(self):
        timeline = CannabisDoseTimeline("pat_001", "t_001")
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e1", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=10.0, thc_mg=5.0, cbd_mg=5.0, entry_type="initial",
        ))
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e2", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=15.0, thc_mg=7.5, cbd_mg=7.5, entry_type="increase",
        ))

        assert len(timeline.get_entries()) == 2
        current = timeline.get_current_dose()
        assert current.dose_mg == 15.0

    def test_titration_summary(self):
        timeline = CannabisDoseTimeline("pat_001", "t_001")
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e1", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=10.0, thc_mg=5.0, cbd_mg=5.0, entry_type="initial",
        ))
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e2", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=20.0, thc_mg=10.0, cbd_mg=10.0, entry_type="increase",
        ))

        summary = timeline.calculate_titration_summary()
        assert summary["initial_dose_mg"] == 10.0
        assert summary["current_dose_mg"] == 20.0
        assert summary["dose_change_mg"] == 10.0
        assert summary["dose_change_percent"] == 100.0
        assert summary["total_adjustments"] == 1

    def test_dose_changes_filter(self):
        timeline = CannabisDoseTimeline("pat_001", "t_001")
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e1", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=10.0, entry_type="initial",
        ))
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e2", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=15.0, entry_type="increase",
        ))
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e3", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=20.0, entry_type="increase",
        ))

        changes = timeline.get_dose_changes()
        assert len(changes) == 2

    def test_max_dose(self):
        timeline = CannabisDoseTimeline("pat_001", "t_001")
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e1", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=10.0, entry_type="initial",
        ))
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e2", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=25.0, entry_type="increase",
        ))

        max_dose = timeline.get_max_dose()
        assert max_dose.dose_mg == 25.0


# ═══════════════════════════════════════════════════════════════════════
# PART 4: Outcome Engine
# ═══════════════════════════════════════════════════════════════════════

class TestOutcomeEngine:
    """Valida análise matemática de outcomes."""

    def test_score_normalization(self):
        score = OutcomeScore(score_id="s1", metric_name="pain", score=5.0, max_score=10.0)
        assert score.normalized() == 0.5

    def test_improvement_calculation(self):
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(
            score_id="s1", metric_name="pain", score=8.0, max_score=10.0,
            context="baseline", recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ))
        outcome.add_score(OutcomeScore(
            score_id="s2", metric_name="pain", score=5.0, max_score=10.0,
            context="followup", recorded_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
        ))
        outcome.add_score(OutcomeScore(
            score_id="s3", metric_name="pain", score=3.0, max_score=10.0,
            context="followup", recorded_at=datetime(2026, 1, 20, tzinfo=timezone.utc),
        ))

        engine = OutcomeEngine()
        analysis = engine.analyze(outcome, "pain")

        assert analysis is not None
        assert analysis.baseline_score == 8.0
        assert analysis.current_score == 3.0
        assert analysis.change_percent > 0  # Melhora é positiva
        assert analysis.trend == TrendDirection.IMPROVING
        assert analysis.is_significant is True

    def test_worsening_detection(self):
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(
            score_id="s1", metric_name="pain", score=3.0, max_score=10.0,
            context="baseline", recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ))
        outcome.add_score(OutcomeScore(
            score_id="s2", metric_name="pain", score=5.0, max_score=10.0,
            context="followup", recorded_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
        ))
        outcome.add_score(OutcomeScore(
            score_id="s3", metric_name="pain", score=7.0, max_score=10.0,
            context="followup", recorded_at=datetime(2026, 1, 20, tzinfo=timezone.utc),
        ))

        engine = OutcomeEngine()
        analysis = engine.analyze(outcome, "pain")

        assert analysis.change_percent < 0  # Piora é negativa
        assert analysis.trend == TrendDirection.WORSENING

    def test_stable_detection(self):
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(
            score_id="s1", metric_name="pain", score=5.0, max_score=10.0,
            context="baseline", recorded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ))
        outcome.add_score(OutcomeScore(
            score_id="s2", metric_name="pain", score=5.1, max_score=10.0,
            context="followup", recorded_at=datetime(2026, 1, 10, tzinfo=timezone.utc),
        ))
        outcome.add_score(OutcomeScore(
            score_id="s3", metric_name="pain", score=5.0, max_score=10.0,
            context="followup", recorded_at=datetime(2026, 1, 20, tzinfo=timezone.utc),
        ))
        outcome.add_score(OutcomeScore(
            score_id="s4", metric_name="pain", score=5.2, max_score=10.0,
            context="followup", recorded_at=datetime(2026, 1, 30, tzinfo=timezone.utc),
        ))

        engine = OutcomeEngine()
        analysis = engine.analyze(outcome, "pain")

        assert analysis.trend == TrendDirection.STABLE

    def test_qol_improvement(self):
        # QoL: maior = melhor
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(
            score_id="s1", metric_name="qol", score=4.0, max_score=10.0,
            context="baseline",
        ))
        outcome.add_score(OutcomeScore(
            score_id="s2", metric_name="qol", score=7.0, max_score=10.0,
            context="followup",
        ))

        engine = OutcomeEngine()
        analysis = engine.analyze(outcome, "qol")

        assert analysis.change_percent > 0  # Melhora é positiva

    def test_best_and_worst_scores(self):
        outcome = CannabisOutcome("pat_001", "t_001")
        for i, score in enumerate([8.0, 6.0, 3.0, 5.0, 4.0]):
            outcome.add_score(OutcomeScore(
                score_id=f"s{i}", metric_name="pain", score=score, max_score=10.0,
            ))

        assert outcome.get_best("pain").score == 3.0
        assert outcome.get_worst("pain").score == 8.0

    def test_summary_text(self):
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="s2", metric_name="pain", score=5.0, context="followup"))
        outcome.add_score(OutcomeScore(score_id="s3", metric_name="pain", score=3.0, context="followup"))

        engine = OutcomeEngine()
        analysis = engine.analyze(outcome, "pain")
        text = engine.generate_summary_text(analysis)

        assert "pain" in text
        assert "8.0" in text
        assert "3.0" in text
        assert "melhora" in text


# ═══════════════════════════════════════════════════════════════════════
# PART 5: Outcome Timeline
# ═══════════════════════════════════════════════════════════════════════

class TestOutcomeTimeline:
    """Valida timeline de outcomes."""

    def test_multiple_metrics(self):
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="s2", metric_name="anxiety", score=7.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="s3", metric_name="sleep", score=4.0, context="baseline"))

        assert len(outcome.get_scores("pain")) == 1
        assert len(outcome.get_scores("anxiety")) == 1
        assert len(outcome.get_scores("sleep")) == 1

    def test_to_dict(self):
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0))
        outcome.add_score(OutcomeScore(score_id="s2", metric_name="pain", score=6.0))

        d = outcome.to_dict()
        assert d["patient_id"] == "pat_001"
        assert d["total_scores"] == 2
        assert "pain" in d["metrics_tracked"]


# ═══════════════════════════════════════════════════════════════════════
# PART 6: Follow-up Integration
# ═══════════════════════════════════════════════════════════════════════

class TestFollowupIntegration:
    """Valida integração com Adaptive Follow-up Engine."""

    def test_followup_program_exists(self):
        from araos.followup.programs.cannabis.program import CANNABIS_FOLLOWUP_PROGRAM
        assert CANNABIS_FOLLOWUP_PROGRAM.specialty_code == "cannabis"
        assert len(CANNABIS_FOLLOWUP_PROGRAM._phases) == 4

    def test_create_patient_program(self):
        from araos.followup.programs.cannabis.program import CANNABIS_FOLLOWUP_PROGRAM
        program = CANNABIS_FOLLOWUP_PROGRAM.create_program("cannabis_pat001", "pat001", "t001")
        assert program.program_id == "cannabis_pat001"
        assert len(program.phases) == 4


# ═══════════════════════════════════════════════════════════════════════
# PART 7: Alerts
# ═══════════════════════════════════════════════════════════════════════

class TestCannabisAlerts:
    """Valida alertas do módulo Cannabis."""

    def test_alert_creation(self):
        alert = CannabisAlert(
            alert_id="a1", patient_id="pat_001", tenant_id="t_001",
            alert_type=CannabisAlertType.ADVERSE_EFFECT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Efeito Adverso Grave",
        )
        assert alert.is_open() is True
        assert alert.alert_type == "adverse_effect_detected"

    def test_alert_escalation(self):
        alert = CannabisAlert(
            alert_id="a1", patient_id="pat_001", tenant_id="t_001",
            alert_type=CannabisAlertType.ADVERSE_EFFECT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Teste",
        )
        alert.escalate(level=2)
        assert alert.escalation_level == 2
        assert alert.status == AlertStatus.ESCALATED

    def test_alert_resolution(self):
        alert = CannabisAlert(
            alert_id="a1", patient_id="pat_001", tenant_id="t_001",
            alert_type=CannabisAlertType.ADVERSE_EFFECT_DETECTED,
            severity=AlertSeverity.HIGH,
            title="Teste",
        )
        alert.resolve("dr_001")
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_by == "dr_001"

    def test_alert_manager(self):
        manager = CannabisAlertManager()
        manager.create_alert(
            alert_id="a1", patient_id="pat_001", tenant_id="t_001",
            alert_type=CannabisAlertType.ADVERSE_EFFECT_DETECTED,
            severity=AlertSeverity.CRITICAL,
            title="AE Grave",
        )
        manager.create_alert(
            alert_id="a2", patient_id="pat_001", tenant_id="t_001",
            alert_type=CannabisAlertType.ADHERENCE_PROBLEM,
            severity=AlertSeverity.MEDIUM,
            title="Adesão",
        )

        all_alerts = manager.get_alerts(patient_id="pat_001")
        assert len(all_alerts) == 2

        critical = manager.get_open_critical_alerts("pat_001")
        assert len(critical) == 1

        summary = manager.summary()
        assert summary["total_alerts"] == 2
        assert summary["critical_alerts"] == 1


# ═══════════════════════════════════════════════════════════════════════
# PART 8: Knowledge Integration
# ═══════════════════════════════════════════════════════════════════════

class TestCannabisKnowledge:
    """Valida integração com Knowledge Layer."""

    def test_index_protocol(self):
        repo = InMemoryKnowledgeRepository()
        source = CannabisKnowledgeSource(repo, "t_001")
        doc = source.index_protocol("Protocolo de Iniciação", "Conteúdo do protocolo...")
        assert "cannabis" in doc.metadata.tags
        assert doc.source_type.value == "protocol"

    def test_index_product(self):
        repo = InMemoryKnowledgeRepository()
        source = CannabisKnowledgeSource(repo, "t_001")
        doc = source.index_product_info(
            product_name="Cannabis Oil 500mg",
            manufacturer="GrowMed",
            formulation="oil",
            spectrum="full_spectrum",
            cbd_mg=300,
            thc_mg=200,
        )
        assert "product" in doc.metadata.tags
        assert "Cannabis Oil 500mg" in doc.content

    def test_search_cannabis_knowledge(self):
        repo = InMemoryKnowledgeRepository()
        source = CannabisKnowledgeSource(repo, "t_001")
        source.index_protocol("Protocolo A", "Conteúdo A")
        source.index_protocol("Protocolo B", "Conteúdo B")

        results = source.search("protocolo")
        assert len(results) == 2

    def test_get_all_knowledge(self):
        repo = InMemoryKnowledgeRepository()
        source = CannabisKnowledgeSource(repo, "t_001")
        source.index_protocol("P1", "C1")
        source.index_product_info("Prod1", "Fab", "oil", "full", 100, 50)

        all_docs = source.get_all_cannabis_knowledge()
        assert len(all_docs) == 2


# ═══════════════════════════════════════════════════════════════════════
# PART 9: Cannabis Agent
# ═══════════════════════════════════════════════════════════════════════

class TestCannabisAgent:
    """Valida agente especializado Cannabis."""

    def test_agent_creation(self):
        agent = CannabisAgent()
        assert agent.agent_id == "cannabis_specialist"
        assert agent.name == "AraOS Cannabis Specialist"

    def test_therapeutic_summary(self):
        agent = CannabisAgent()
        profile = CannabisProfile("pat_001", "t_001")
        profile.set_main_condition("Dor Crônica")
        profile.set_therapeutic_status("active")

        dose_timeline = CannabisDoseTimeline("pat_001", "t_001")
        dose_timeline.add_entry(CannabisDoseEntry(
            entry_id="e1", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=10.0, thc_mg=5.0, cbd_mg=5.0, entry_type="initial",
        ))

        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="s2", metric_name="pain", score=4.0, context="followup"))

        alert_manager = CannabisAlertManager()

        summary = agent.generate_therapeutic_summary(profile, dose_timeline, outcome, alert_manager)
        assert summary.trust_level == TrustLevel.GENERATED_SUMMARY
        assert not summary.requires_human_verification()
        assert "Dor Crônica" in summary.content

    def test_longitudinal_evolution(self):
        agent = CannabisAgent()
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="s2", metric_name="pain", score=4.0))

        response = agent.answer_longitudinal_evolution(outcome, "pain")
        assert response.trust_level == TrustLevel.STRUCTURED_DATA
        assert "Baseline: 8.0" in response.content
        assert "Atual: 4.0" in response.content

    def test_dose_history(self):
        agent = CannabisAgent()
        timeline = CannabisDoseTimeline("pat_001", "t_001")
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e1", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=10.0, entry_type="initial",
        ))
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e2", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=20.0, entry_type="increase",
        ))

        response = agent.answer_dose_history(timeline)
        assert response.trust_level == TrustLevel.STRUCTURED_DATA
        assert "Dose Inicial: 10.0" in response.content
        assert "Dose Atual: 20.0" in response.content


# ═══════════════════════════════════════════════════════════════════════
# PART 10: Dashboard Models
# ═══════════════════════════════════════════════════════════════════════

class TestDashboardModels:
    """Valida modelos de dashboard."""

    def test_dashboard_builder(self):
        builder = CannabisDashboardBuilder()
        dashboard = builder.build(
            patient_id="pat_001",
            symptom_data=SymptomEvolutionData(
                symptom_name="Dor",
                dates=["2026-01-01", "2026-01-15"],
                scores=[8.0, 4.0],
                baseline_score=8.0,
                current_score=4.0,
                change_percent=-50.0,
            ),
            dose_data=DoseEvolutionData(
                dates=["2026-01-01", "2026-01-15"],
                doses_mg=[10.0, 20.0],
                current_dose_mg=20.0,
                total_adjustments=1,
            ),
            adherence_data=AdherenceData(
                total_checkpoints=10,
                completed_checkpoints=8,
                missed_checkpoints=2,
                adherence_rate=0.8,
            ),
            alert_data=AlertSummaryData(
                total_alerts=3,
                open_alerts=1,
                critical_alerts=0,
                by_type={"adverse_effect": 1, "adherence": 2},
            ),
        )

        assert dashboard.specialty_code == "cannabis"
        assert len(dashboard.get_kpis()) == 4
        assert len(dashboard.get_metrics()) == 2
        assert len(dashboard.get_charts()) == 4

    def test_symptom_evolution_data(self):
        data = SymptomEvolutionData(
            symptom_name="Dor",
            dates=["2026-01-01", "2026-01-15"],
            scores=[8.0, 4.0],
            change_percent=-50.0,
        )
        d = data.to_dict()
        assert d["symptom_name"] == "Dor"
        assert d["change_percent"] == -50.0

    def test_adherence_data(self):
        data = AdherenceData(
            total_checkpoints=10,
            completed_checkpoints=7,
            missed_checkpoints=3,
            adherence_rate=0.7,
        )
        d = data.to_dict()
        assert d["adherence_rate"] == 0.7
        assert d["trend"] == "stable"


# ═══════════════════════════════════════════════════════════════════════
# PART 11: Event Bus
# ═══════════════════════════════════════════════════════════════════════

class TestCannabisEvents:
    """Valida eventos no Event Bus."""

    def test_events_in_catalog(self):
        catalog = EventCatalog()
        events = [
            "CANNABIS_STARTED",
            "CANNABIS_PRODUCT_ADDED",
            "CANNABIS_PRODUCT_CHANGED",
            "CANNABIS_DOSE_CHANGED",
            "CANNABIS_OUTCOME_RECORDED",
            "CANNABIS_ALERT_TRIGGERED",
            "CANNABIS_DISCONTINUED",
        ]
        for event_type in events:
            assert catalog.is_valid(event_type), f"{event_type} not in catalog"

    def test_event_domains(self):
        catalog = EventCatalog()
        assert catalog.get_definition("CANNABIS_STARTED").domain == "cannabis"
        assert catalog.get_definition("CANNABIS_DOSE_CHANGED").domain == "cannabis"

    def test_cannabis_started_event(self):
        evt = cannabis_started_event("pat_001", "t_001", "med_001", "Cannabis Oil", 10.0)
        assert evt.event_type == "CANNABIS_STARTED"
        assert evt.payload["initial_dose_mg"] == 10.0

    def test_cannabis_dose_changed_event(self):
        evt = cannabis_dose_changed_event("pat_001", "t_001", "med_001", 10.0, 20.0, "titration")
        assert evt.event_type == "CANNABIS_DOSE_CHANGED"
        assert evt.payload["previous_dose_mg"] == 10.0
        assert evt.payload["new_dose_mg"] == 20.0

    def test_cannabis_alert_event_priority(self):
        from araos.platform.event_bus.envelope import EventPriority
        evt = cannabis_alert_triggered_event("pat_001", "t_001", "ae", "critical", "Teste")
        assert evt.priority == EventPriority.HIGH

        evt2 = cannabis_alert_triggered_event("pat_001", "t_001", "ae", "low", "Teste")
        assert evt2.priority == EventPriority.NORMAL

    def test_cannabis_discontinued_event(self):
        evt = cannabis_discontinued_event("pat_001", "t_001", "med_001", "adverse_effect")
        assert evt.event_type == "CANNABIS_DISCONTINUED"
        assert evt.payload["reason"] == "adverse_effect"


# ═══════════════════════════════════════════════════════════════════════
# PART 12: Trust Levels
# ═══════════════════════════════════════════════════════════════════════

class TestTrustLevels:
    """Valida Trust Levels em todas as respostas."""

    def test_agent_uses_structured_data(self):
        agent = CannabisAgent()
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="s2", metric_name="pain", score=4.0))

        response = agent.answer_longitudinal_evolution(outcome, "pain")
        assert response.trust_level == TrustLevel.STRUCTURED_DATA
        assert response.source_type == SourceType.STRUCTURED_DATA
        assert not response.requires_human_verification()

    def test_agent_uses_generated_summary(self):
        agent = CannabisAgent()
        profile = CannabisProfile("pat_001", "t_001")
        profile.set_main_condition("Dor")
        profile.set_therapeutic_status("active")

        dose_timeline = CannabisDoseTimeline("pat_001", "t_001")
        outcome = CannabisOutcome("pat_001", "t_001")
        alert_manager = CannabisAlertManager()

        response = agent.generate_therapeutic_summary(profile, dose_timeline, outcome, alert_manager)
        assert response.trust_level == TrustLevel.GENERATED_SUMMARY
        assert response.source_type == SourceType.GENERATED_SUMMARY
        assert not response.requires_human_verification()

    def test_no_ai_inference_without_explicit_marking(self):
        """Nenhuma resposta do agente deve ter trust_level AI_INFERENCE sem marcação."""
        agent = CannabisAgent()
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="s2", metric_name="pain", score=4.0))

        response = agent.answer_longitudinal_evolution(outcome, "pain")
        assert response.trust_level != TrustLevel.AI_INFERENCE

        timeline = CannabisDoseTimeline("pat_001", "t_001")
        timeline.add_entry(CannabisDoseEntry(
            entry_id="e1", medication_id="med_001", patient_id="pat_001", tenant_id="t_001",
            dose_mg=10.0, entry_type="initial",
        ))
        response2 = agent.answer_dose_history(timeline)
        assert response2.trust_level != TrustLevel.AI_INFERENCE


# ═══════════════════════════════════════════════════════════════════════
# FULL INTEGRATION
# ═══════════════════════════════════════════════════════════════════════

class TestFullCannabisIntegration:
    """Valida integração completa do módulo Cannabis."""

    def test_patient_journey(self):
        """Jornada completa de um paciente no módulo Cannabis."""
        patient_id = "pat_cannabis_001"
        tenant_id = "t_001"

        # 1. Criar profile
        profile = CannabisProfile(patient_id, tenant_id)
        profile.set_main_condition("Dor Neuropática", "M79.2")
        profile.add_associated_condition("Insônia", "G47.0")
        profile.set_responsible_physician("dr_001", "Dr. Silva")
        profile.set_therapeutic_status("titrating")
        profile.add_therapeutic_goal(CannabisTherapeuticGoal(
            goal_id="g1", description="Reduzir dor", target_symptom="pain",
            baseline_score=8.0, target_score=3.0,
        ))
        profile.add_therapeutic_goal(CannabisTherapeuticGoal(
            goal_id="g2", description="Melhorar sono", target_symptom="sleep",
            baseline_score=3.0, target_score=7.0,
        ))

        # 2. Prescrever medicação
        product = CannabisProduct(
            product_id="prod_001", name="Cannabis Oil 500mg",
            manufacturer="GrowMed", formulation="oil",
            spectrum="full_spectrum",
            cannabinoids=CannabinoidProfile(cbd_mg=300, thc_mg=200),
            volume_ml=30.0, route="sublingual",
        )
        medication = CannabisMedication(
            medication_id="med_001", patient_id=patient_id, tenant_id=tenant_id,
            product=product, prescribed_dose_mg=15.0, frequency="2x/dia",
        )
        medication.start()

        # 3. Registrar timeline de doses
        dose_timeline = CannabisDoseTimeline(patient_id, tenant_id)
        dose_timeline.add_entry(CannabisDoseEntry(
            entry_id="de_001", medication_id="med_001", patient_id=patient_id, tenant_id=tenant_id,
            dose_mg=15.0, thc_mg=100.0, cbd_mg=150.0, entry_type="initial",
        ))
        dose_timeline.add_entry(CannabisDoseEntry(
            entry_id="de_002", medication_id="med_001", patient_id=patient_id, tenant_id=tenant_id,
            dose_mg=20.0, thc_mg=133.0, cbd_mg=200.0, entry_type="increase",
            reason="Resposta parcial",
        ))

        # 4. Registrar outcomes
        outcome = CannabisOutcome(patient_id, tenant_id)
        outcome.add_score(OutcomeScore(score_id="os_001", metric_name="pain", score=8.0, max_score=10.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="os_002", metric_name="pain", score=6.0, max_score=10.0, context="followup"))
        outcome.add_score(OutcomeScore(score_id="os_003", metric_name="pain", score=4.0, max_score=10.0, context="followup"))
        outcome.add_score(OutcomeScore(score_id="os_004", metric_name="sleep", score=3.0, max_score=10.0, context="baseline"))
        outcome.add_score(OutcomeScore(score_id="os_005", metric_name="sleep", score=4.0, max_score=10.0, context="followup"))
        outcome.add_score(OutcomeScore(score_id="os_006", metric_name="sleep", score=6.0, max_score=10.0, context="followup"))

        # 5. Verificar outcome engine
        engine = OutcomeEngine()
        pain_analysis = engine.analyze(outcome, "pain")
        assert pain_analysis.trend == TrendDirection.IMPROVING
        assert pain_analysis.is_significant is True

        sleep_analysis = engine.analyze(outcome, "sleep")
        assert sleep_analysis.trend == TrendDirection.IMPROVING

        # 6. Criar alertas
        alert_manager = CannabisAlertManager()
        alert_manager.create_alert(
            alert_id="ca_001", patient_id=patient_id, tenant_id=tenant_id,
            alert_type=CannabisAlertType.ADVERSE_EFFECT_DETECTED,
            severity=AlertSeverity.MEDIUM,
            title="Boca seca leve",
        )

        # 7. Gerar resumo terapêutico via agente
        agent = CannabisAgent()
        summary = agent.generate_therapeutic_summary(profile, dose_timeline, outcome, alert_manager)
        assert summary.trust_level == TrustLevel.GENERATED_SUMMARY
        assert "Dor Neuropática" in summary.content
        assert not summary.requires_human_verification()

        # 8. Verificar dose timeline
        dose_summary = dose_timeline.calculate_titration_summary()
        assert dose_summary["total_adjustments"] == 1
        assert dose_summary["dose_change_percent"] == 33.3

        # 9. Verificar alertas
        open_alerts = alert_manager.get_alerts(patient_id=patient_id, open_only=True)
        assert len(open_alerts) == 1

        # 10. Gerar dashboard
        dashboard_builder = CannabisDashboardBuilder()
        dashboard = dashboard_builder.build(
            patient_id=patient_id,
            symptom_data=SymptomEvolutionData(
                symptom_name="Dor",
                dates=["2026-01-01", "2026-01-15", "2026-02-01"],
                scores=[8.0, 6.0, 4.0],
                baseline_score=8.0,
                current_score=4.0,
                change_percent=-50.0,
            ),
            dose_data=DoseEvolutionData(
                dates=["2026-01-01", "2026-01-15"],
                doses_mg=[15.0, 20.0],
                current_dose_mg=20.0,
                total_adjustments=1,
            ),
            adherence_data=AdherenceData(
                total_checkpoints=4,
                completed_checkpoints=4,
                adherence_rate=1.0,
            ),
            alert_data=AlertSummaryData(
                total_alerts=1,
                open_alerts=1,
                by_type={"adverse_effect": 1},
            ),
        )
        assert len(dashboard.get_kpis()) == 4
        assert len(dashboard.get_charts()) == 4

    def test_module_integrates_all_layers(self):
        """Verifica que o módulo integra todas as camadas da plataforma."""
        # Specialty Framework
        from araos.specialties.stubs.cannabis import CANNABIS_DEFINITION
        assert CANNABIS_DEFINITION.code == "cannabis"

        # Follow-up Engine
        from araos.followup.programs.cannabis.program import CANNABIS_FOLLOWUP_PROGRAM
        assert CANNABIS_FOLLOWUP_PROGRAM.specialty_code == "cannabis"

        # Knowledge Layer
        repo = InMemoryKnowledgeRepository()
        knowledge = CannabisKnowledgeSource(repo, "t_001")
        doc = knowledge.index_protocol("Protocolo Cannabis", "Conteúdo")
        assert "cannabis" in doc.metadata.tags

        # Event Bus
        catalog = EventCatalog()
        assert catalog.is_valid("CANNABIS_STARTED")
        assert catalog.is_valid("CANNABIS_DISCONTINUED")

        # Trust Levels
        agent = CannabisAgent()
        outcome = CannabisOutcome("pat_001", "t_001")
        outcome.add_score(OutcomeScore(score_id="s1", metric_name="pain", score=8.0, context="baseline"))
        response = agent.answer_longitudinal_evolution(outcome, "pain")
        assert response.trust_level in (TrustLevel.STRUCTURED_DATA, TrustLevel.GENERATED_SUMMARY)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
