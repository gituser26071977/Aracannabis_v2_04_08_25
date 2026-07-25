"""
Clinical Context Engine — Projections (Sprint 4.2 / ADR-0003).
"""

from araos.clinical.context.projections.projection import (
    ClinicalContextProjection,
)
from araos.clinical.context.projections.active_projection import (
    ActiveContextProjection,
)
from araos.clinical.context.projections.relationship_projection import (
    RelationshipProjection,
)
from araos.clinical.context.projections.handlers import (
    HANDLERS_BY_EVENT_TYPE,
)


__all__ = [
    "ClinicalContextProjection",
    "ActiveContextProjection",
    "RelationshipProjection",
    "HANDLERS_BY_EVENT_TYPE",
]
