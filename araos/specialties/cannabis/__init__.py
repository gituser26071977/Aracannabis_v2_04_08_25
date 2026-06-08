"""
AraOS Cannabis Module V1.

Primeiro módulo especializado operacional do AraOS.

Integra:
    - Specialty Framework
    - Follow-up Engine
    - Digital Twin
    - Knowledge Layer
    - Intelligence Layer

Week 11B — Cannabis Module V1
"""

from .profile.models import CannabisProfile, CannabisTherapeuticGoal
from .medication.models import CannabisProduct, CannabisMedication, CannabinoidProfile
from .dose.models import CannabisDoseEntry, CannabisDoseTimeline
from .outcome.engine import CannabisOutcome, OutcomeScore, OutcomeAnalysis, OutcomeEngine, TrendDirection
from .alerts.models import CannabisAlert, CannabisAlertManager, CannabisAlertType
from .knowledge.source import CannabisKnowledgeSource
from .agent.agent import CannabisAgent
from .dashboard.models import (
    CannabisDashboardBuilder,
    SymptomEvolutionData,
    DoseEvolutionData,
    AdherenceData,
    ClinicalResponseData,
    AlertSummaryData,
)
from .events.events import (
    cannabis_started_event,
    cannabis_product_added_event,
    cannabis_product_changed_event,
    cannabis_dose_changed_event,
    cannabis_outcome_recorded_event,
    cannabis_alert_triggered_event,
    cannabis_discontinued_event,
)

__all__ = [
    # Profile
    "CannabisProfile",
    "CannabisTherapeuticGoal",
    # Medication
    "CannabisProduct",
    "CannabisMedication",
    "CannabinoidProfile",
    # Dose
    "CannabisDoseEntry",
    "CannabisDoseTimeline",
    # Outcome
    "CannabisOutcome",
    "OutcomeScore",
    "OutcomeAnalysis",
    "OutcomeEngine",
    "TrendDirection",
    # Alerts
    "CannabisAlert",
    "CannabisAlertManager",
    "CannabisAlertType",
    # Knowledge
    "CannabisKnowledgeSource",
    # Agent
    "CannabisAgent",
    # Dashboard
    "CannabisDashboardBuilder",
    "SymptomEvolutionData",
    "DoseEvolutionData",
    "AdherenceData",
    "ClinicalResponseData",
    "AlertSummaryData",
    # Events
    "cannabis_started_event",
    "cannabis_product_added_event",
    "cannabis_product_changed_event",
    "cannabis_dose_changed_event",
    "cannabis_outcome_recorded_event",
    "cannabis_alert_triggered_event",
    "cannabis_discontinued_event",
]
