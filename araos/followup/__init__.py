"""
AraOS Follow-up — Adaptive Follow-up Engine.

Motor de acompanhamento longitudinal adaptativo.

Transforma o AraOS de prontuário em plataforma de acompanhamento contínuo.

Week 11A — Adaptive Follow-up Engine
"""

from .core.models import (
    FollowupProgram,
    FollowupPhase,
    FollowupCheckpoint,
    FollowupQuestionnaire,
    FollowupQuestion,
    FollowupResponse,
    FollowupRule,
    FollowupAlert,
    FollowupStatus,
    AlertSeverity,
    AlertStatus,
    QuestionType,
)
from .core.engine import AdaptiveFollowupEngine
from .core.specialty_integration import SpecialtyFollowupProgram
from .rules.engine import FollowupRuleEngine, RuleEvaluationContext
from .observability.metrics import FollowupObservability, FollowupMetric
from .events.events import (
    followup_started_event,
    followup_completed_event,
    followup_response_received_event,
    followup_alert_triggered_event,
    followup_escalated_event,
    followup_phase_changed_event,
)
from .programs.cannabis.program import (
    CANNABIS_FOLLOWUP_PROGRAM,
    build_cannabis_followup_program,
    build_initial_phase,
    build_titration_phase,
    build_stabilization_phase,
    build_maintenance_phase,
)

__all__ = [
    # Core Models
    "FollowupProgram",
    "FollowupPhase",
    "FollowupCheckpoint",
    "FollowupQuestionnaire",
    "FollowupQuestion",
    "FollowupResponse",
    "FollowupRule",
    "FollowupAlert",
    "FollowupStatus",
    "AlertSeverity",
    "AlertStatus",
    "QuestionType",
    # Engine
    "AdaptiveFollowupEngine",
    "SpecialtyFollowupProgram",
    # Rules
    "FollowupRuleEngine",
    "RuleEvaluationContext",
    # Observability
    "FollowupObservability",
    "FollowupMetric",
    # Events
    "followup_started_event",
    "followup_completed_event",
    "followup_response_received_event",
    "followup_alert_triggered_event",
    "followup_escalated_event",
    "followup_phase_changed_event",
    # Cannabis Program
    "CANNABIS_FOLLOWUP_PROGRAM",
    "build_cannabis_followup_program",
    "build_initial_phase",
    "build_titration_phase",
    "build_stabilization_phase",
    "build_maintenance_phase",
]
