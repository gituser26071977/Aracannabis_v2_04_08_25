"""
Clinical Context Engine — Application Layer (Sprint 4.2 / ADR-0003).
"""

from araos.clinical.context.application.builtin_rules import (
    DEFAULT_RULES,
    BehavioralCrisisRule,
    CrisisEpisodeRule,
    FamilyEngagementRule,
    MedicationStartRule,
    SchoolTransitionRule,
    SleepPatternRule,
    default_rules,
)
from araos.clinical.context.application.context_service import (
    ClinicalContextService,
    CreateContextCommand,
)
from araos.clinical.context.application.query import (
    ClinicalContextQuery,
    InMemoryClinicalContextQuery,
)
from araos.clinical.context.application.rule_engine import (
    RuleEngine,
    RuleEvaluationResult,
)
from araos.clinical.context.application.suggester import ContextSuggester


__all__ = [
    "ClinicalContextService",
    "CreateContextCommand",
    "ClinicalContextQuery",
    "InMemoryClinicalContextQuery",
    "RuleEngine",
    "RuleEvaluationResult",
    "ContextSuggester",
    "DEFAULT_RULES",
    "default_rules",
    "MedicationStartRule",
    "SchoolTransitionRule",
    "FamilyEngagementRule",
    "CrisisEpisodeRule",
    "BehavioralCrisisRule",
    "SleepPatternRule",
]
