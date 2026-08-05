"""
AraOS Neurodevelopmental — Assessment Entity.

Aplicação de escala neuropsicológica. Assessment produz EVIDÊNCIA —
não mutua estado clínico do paciente diretamente.

Invariantes:
    - raw_responses sempre presente (validado contra ScaleSpec.json_schema).
    - computed_scores sempre presente (cache derivável).
    - source_event_ids sempre presente.
    - Updated assessments preservam versão anterior no log (Event Store).

ADR-0002 §2.2.4: 'Assessment = aplicações de escalas, nunca altera
diretamente o estado do paciente.'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .ids import AssessmentId, new_id


class AssessmentStatus(str, Enum):
    """Status da aplicação."""

    DRAFT = "draft"
    FINAL = "final"
    AMENDED = "amended"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class AssessmentScore:
    """
    Value Object — score calculado de uma subescala ou agregado.

    Attributes:
        subscale: nome da subescala (ou 'total').
        value: valor numérico.
        min_value: limite inferior.
        max_value: limite superior.
        interpretation: rótulo interpretativo (ex.: 'moderate_anxiety').
    """

    subscale: str
    value: float
    min_value: float = 0.0
    max_value: float = 100.0
    interpretation: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "subscale": self.subscale,
            "value": self.value,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "interpretation": self.interpretation,
        }


@dataclass
class Assessment:
    """
    Entity — uma aplicação de escala neuropsicológica.

    Attributes:
        id: AssessmentId.
        identity_id: ClinicalIdentityId.
        scale_code: código da escala (GAD7, PHQ9, MCHAT, etc.).
        scale_version: versão semântica da escala.
        applied_by: ID do profissional que aplicou.
        applied_at: timestamp de aplicação.
        raw_responses: dict com respostas brutas (validadas contra schema).
        computed_scores: dict com scores calculados (AssessmentScore serializado).
        interpretation: dict com interpretação textual (band, label_pt, recommendation).
        linked_diagnosis_ids: lista de DiagnosisId que esta evidência suporta.
        status: DRAFT/FINAL/AMENDED.
        version: incrementa a cada update (1, 2, 3...).
        previous_version_id: AssessmentId da versão anterior (se amended).
        source_event_ids: lista de event_ids.
    """

    id: AssessmentId
    identity_id: str
    scale_code: str
    scale_version: str
    applied_by: str

    raw_responses: Dict[str, Any] = field(default_factory=dict)
    computed_scores: Dict[str, Any] = field(default_factory=dict)
    interpretation: Dict[str, Any] = field(default_factory=dict)

    linked_diagnosis_ids: List[str] = field(default_factory=list)
    status: AssessmentStatus = AssessmentStatus.FINAL

    version: int = 1
    previous_version_id: Optional[str] = None

    applied_at: Optional[datetime] = None
    source_event_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.scale_code or not self.scale_code.strip():
            raise ValueError("scale_code must be non-empty")
        if not self.scale_version or not self.scale_version.strip():
            raise ValueError("scale_version must be non-empty")
        if not self.source_event_ids:
            raise ValueError(
                "Assessment.source_event_ids must contain at least one event_id."
            )

    # ─── Operations ─────────────────────────────────────────────────────

    def amend(
        self,
        event_id: str,
        updated_by: str,
        new_raw_responses: Optional[Dict[str, Any]] = None,
        new_computed_scores: Optional[Dict[str, Any]] = None,
        new_interpretation: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> Assessment:
        """
        Cria nova versão (amendment). Assessment é imutável — retorna nova instância.

        Returns:
            Nova Assessment com version+1, status=AMENDED.
        """
        when = when or datetime.now(timezone.utc)
        amended = Assessment(
            id=AssessmentId(new_id()),
            identity_id=self.identity_id,
            scale_code=self.scale_code,
            scale_version=self.scale_version,
            applied_by=updated_by,
            raw_responses=new_raw_responses or self.raw_responses,
            computed_scores=new_computed_scores or self.computed_scores,
            interpretation=new_interpretation or self.interpretation,
            linked_diagnosis_ids=list(self.linked_diagnosis_ids),
            status=AssessmentStatus.AMENDED,
            version=self.version + 1,
            previous_version_id=str(self.id),
            applied_at=when,
            source_event_ids=[event_id],
            created_at=when,
            updated_at=when,
        )
        return amended

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "scale_code": self.scale_code,
            "scale_version": self.scale_version,
            "applied_by": self.applied_by,
            "applied_at": (
                self.applied_at.isoformat() if self.applied_at else None
            ),
            "raw_responses": dict(self.raw_responses),
            "computed_scores": dict(self.computed_scores),
            "interpretation": dict(self.interpretation),
            "linked_diagnosis_ids": list(self.linked_diagnosis_ids),
            "status": self.status.value,
            "version": self.version,
            "previous_version_id": self.previous_version_id,
            "source_event_ids": list(self.source_event_ids),
        }

    # ─── Factory ────────────────────────────────────────────────────────

    @classmethod
    def apply(
        cls,
        identity_id: str,
        scale_code: str,
        scale_version: str,
        applied_by: str,
        raw_responses: Dict[str, Any],
        computed_scores: Dict[str, Any],
        interpretation: Dict[str, Any],
        source_event_id: str,
        linked_diagnosis_ids: Optional[List[str]] = None,
        status: AssessmentStatus = AssessmentStatus.FINAL,
        when: Optional[datetime] = None,
    ) -> "Assessment":
        """Cria nova Assessment (versão 1)."""
        when = when or datetime.now(timezone.utc)
        return cls(
            id=AssessmentId(new_id()),
            identity_id=identity_id,
            scale_code=scale_code,
            scale_version=scale_version,
            applied_by=applied_by,
            raw_responses=dict(raw_responses),
            computed_scores=dict(computed_scores),
            interpretation=dict(interpretation),
            linked_diagnosis_ids=list(linked_diagnosis_ids or []),
            status=status,
            version=1,
            applied_at=when,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )