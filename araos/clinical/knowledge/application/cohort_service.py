"""CohortService — Application Layer."""

from __future__ import annotations

from typing import Sequence

from ..domain.cohort import Cohort, CohortBuilder, PatientData
from .dto import CohortRequest


class CohortService:
    """Orquestra CohortBuilder."""

    def __init__(self, *, builder: CohortBuilder | None = None) -> None:
        self._builder = builder or CohortBuilder()

    def execute(self, request: CohortRequest) -> Cohort:
        return self._builder.evaluate(
            patients=request.patients,
            tenant_id=request.tenant_id,
            name=request.name,
            criteria=request.criteria,
        )