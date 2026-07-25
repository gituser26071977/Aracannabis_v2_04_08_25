"""ResearchService — Application Layer."""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from ...genome.domain.aggregate import ClinicalGene
from ..domain.cohort import PatientData
from ..domain.research import (
    AnalysisType,
    ResearchQuery,
    ResearchSession,
    ResearchWorkspace,
)
from .dto import ResearchRequest


class ResearchService:
    """Orquestra ResearchWorkspace."""

    def __init__(self, *, workspace: ResearchWorkspace | None = None) -> None:
        self._workspace = workspace or ResearchWorkspace()

    def execute(
        self,
        request: ResearchRequest,
        *,
        patients: Sequence[PatientData],
        genes_by_patient: dict[str, Sequence[ClinicalGene]],
        cohort_id: str | None = None,
        created_at: datetime | None = None,
    ) -> ResearchSession:
        query = ResearchQuery(
            query_id=f"query_{request.analysis_type.value}",
            cohort_id=cohort_id or request.cohort_id,
            analysis_type=request.analysis_type,
            params=request.params,
            version=request.version,
            created_at=created_at or datetime.now(__import__("datetime").timezone.utc),
        )
        return self._workspace.execute(
            query,
            patients=patients,
            genes_by_patient=genes_by_patient,
        )

    def replay(
        self,
        session: ResearchSession,
        *,
        patients: Sequence[PatientData],
        genes_by_patient: dict[str, Sequence[ClinicalGene]],
    ) -> ResearchSession:
        """Replay: re-executa query idêntica."""
        return self._workspace.replay(
            session.query,
            patients=patients,
            genes_by_patient=genes_by_patient,
        )