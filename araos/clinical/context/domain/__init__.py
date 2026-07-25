"""
Clinical Context Engine — Domain Layer (Sprint 4.2 / ADR-0003).

Re-exports para uso externo.
"""

from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_relationship import (
    ContextRelationship,
    RelationshipType,
)
from araos.clinical.context.domain.context_status import (
    ContextStatus,
    TERMINAL_STATUSES,
    is_terminal,
    requires_confirmation,
    requires_end_date,
)
from araos.clinical.context.domain.context_type import ContextType
from araos.clinical.context.domain.rule import ContextSuggestion, Rule


__all__ = [
    "ClinicalContext",
    "ContextType",
    "ContextStatus",
    "ContextOrigin",
    "ContextRelationship",
    "RelationshipType",
    "Rule",
    "ContextSuggestion",
    "TERMINAL_STATUSES",
    "is_terminal",
    "requires_confirmation",
    "requires_end_date",
]
