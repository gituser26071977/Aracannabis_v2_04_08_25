"""
AraOS Neurodevelopmental — Outcome Entity.

Resultado clínico derivado de eventos. Outcomes são SEMPRE derivados:
nunca criados a partir de inputs diretos, mas sim de avaliação
clínica baseada em evidência acumulada.

Invariantes:
    - observed_by obrigatório.
    - outcome_type enums: improvement/worsening/partial_response/remission/no_change/adverse_event.
    - magnitude ∈ {'small', 'moderate', 'large'} (exceto adverse_event).
    - severity ∈ {'mild', 'moderate', 'severe', 'life_threatening', 'fatal'}
      (somente para adverse_event).
    - causality ∈ {'definite', 'probable', 'possible', 'unlikely', 'unrelated'}
      (somente para adverse_event).

ADR-0002 §2.2.6: 'Outcome = resultados clínicos derivados de eventos.'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .ids import OutcomeId, new_id


class OutcomeType(str, Enum):
    """Tipo de outcome clínico."""

    IMPROVEMENT = "improvement"
    WORSENING = "worsening"
    PARTIAL_RESPONSE = "partial_response"
    REMISSION = "remission"
    NO_CHANGE = "no_change"
    ADVERSE_EVENT = "adverse_event"

    def __str__(self) -> str:
        return self.value


class OutcomeMagnitude(str, Enum):
    """Magnitude da mudança (improvement/worsening)."""

    SMALL = "small"
    MODERATE = "moderate"
    LARGE = "large"

    def __str__(self) -> str:
        return self.value


class OutcomeSeverity(str, Enum):
    """Severidade do adverse_event."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    LIFE_THREATENING = "life_threatening"
    FATAL = "fatal"

    def __str__(self) -> str:
        return self.value


class OutcomeCausality(str, Enum):
    """Causalidade do adverse_event em relação à intervention."""

    DEFINITE = "definite"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    UNLIKELY = "unlikely"
    UNRELATED = "unrelated"

    def __str__(self) -> str:
        return self.value


@dataclass
class Outcome:
    """
    Entity — resultado clínico observado.

    Attributes:
        id: OutcomeId.
        identity_id: ClinicalIdentityId.
        outcome_type: OutcomeType.
        observed_by: profissional.
        observed_at: timestamp de observação.
        evidence: dict com assessment_ids, phenotype_ids.
        intervention_id: InterventionId relacionado (opcional).
        magnitude: OutcomeMagnitude (improvement/worsening).
        severity: OutcomeSeverity (adverse_event).
        causality: OutcomeCausality (adverse_event).
        action_taken: ação tomada (adverse_event).
        description: descrição textual (obrigatória para adverse_event).
        duration_months: duração observada (remission).
        responding_domains: domínios que responderam (partial_response).
        non_responding_domains: domínios que não responderam.
        duration_observed_months: duração sem mudança (no_change).
        notes: observações.
        source_event_ids: lista de event_ids.
    """

    id: OutcomeId
    identity_id: str
    outcome_type: OutcomeType
    observed_by: str

    observed_at: Optional[datetime] = None

    evidence: Dict[str, Any] = field(default_factory=dict)
    intervention_id: Optional[str] = None
    magnitude: Optional[OutcomeMagnitude] = None
    severity: Optional[OutcomeSeverity] = None
    causality: Optional[OutcomeCausality] = None
    action_taken: Optional[str] = None
    description: Optional[str] = None
    duration_months: Optional[int] = None
    responding_domains: List[str] = field(default_factory=list)
    non_responding_domains: List[str] = field(default_factory=list)
    duration_observed_months: Optional[int] = None
    notes: Optional[str] = None

    source_event_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.source_event_ids:
            raise ValueError(
                "Outcome.source_event_ids must contain at least one event_id."
            )
        # Invariantes por tipo
        if self.outcome_type == OutcomeType.ADVERSE_EVENT:
            if not self.severity:
                raise ValueError(
                    "ADVERSE_EVENT outcome must have severity."
                )
            if not self.description or not self.description.strip():
                raise ValueError(
                    "ADVERSE_EVENT outcome must have description."
                )
        if self.outcome_type in (OutcomeType.IMPROVEMENT, OutcomeType.WORSENING):
            if self.magnitude is None:
                # magnitude é opcional mas recomendado
                pass

    # ─── Operations ─────────────────────────────────────────────────────

    def link_assessment(self, assessment_id: str) -> "Outcome":
        """Vincula assessment como evidência."""
        ids = self.evidence.setdefault("assessment_ids", [])
        if assessment_id not in ids:
            ids.append(assessment_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def link_phenotype(self, phenotype_id: str) -> "Outcome":
        """Vincula phenotype como evidência."""
        ids = self.evidence.setdefault("phenotype_ids", [])
        if phenotype_id not in ids:
            ids.append(phenotype_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "outcome_type": self.outcome_type.value,
            "observed_by": self.observed_by,
            "observed_at": (
                self.observed_at.isoformat() if self.observed_at else None
            ),
            "evidence": dict(self.evidence),
            "intervention_id": self.intervention_id,
            "magnitude": self.magnitude.value if self.magnitude else None,
            "severity": self.severity.value if self.severity else None,
            "causality": self.causality.value if self.causality else None,
            "action_taken": self.action_taken,
            "description": self.description,
            "duration_months": self.duration_months,
            "responding_domains": list(self.responding_domains),
            "non_responding_domains": list(self.non_responding_domains),
            "duration_observed_months": self.duration_observed_months,
            "notes": self.notes,
            "source_event_ids": list(self.source_event_ids),
        }

    # ─── Factories ───────────────────────────────────────────────────────

    @classmethod
    def improvement(
        cls,
        identity_id: str,
        observed_by: str,
        evidence: Dict[str, Any],
        source_event_id: str,
        magnitude: Optional[OutcomeMagnitude] = None,
        intervention_id: Optional[str] = None,
        notes: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Outcome":
        when = when or datetime.now(timezone.utc)
        return cls(
            id=OutcomeId(new_id()),
            identity_id=identity_id,
            outcome_type=OutcomeType.IMPROVEMENT,
            observed_by=observed_by,
            observed_at=when,
            evidence=dict(evidence),
            magnitude=magnitude,
            intervention_id=intervention_id,
            notes=notes,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )

    @classmethod
    def worsening(
        cls,
        identity_id: str,
        observed_by: str,
        evidence: Dict[str, Any],
        source_event_id: str,
        magnitude: Optional[OutcomeMagnitude] = None,
        intervention_id: Optional[str] = None,
        notes: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Outcome":
        when = when or datetime.now(timezone.utc)
        return cls(
            id=OutcomeId(new_id()),
            identity_id=identity_id,
            outcome_type=OutcomeType.WORSENING,
            observed_by=observed_by,
            observed_at=when,
            evidence=dict(evidence),
            magnitude=magnitude,
            intervention_id=intervention_id,
            notes=notes,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )

    @classmethod
    def adverse_event(
        cls,
        identity_id: str,
        observed_by: str,
        severity: OutcomeSeverity,
        description: str,
        source_event_id: str,
        intervention_id: Optional[str] = None,
        causality: Optional[OutcomeCausality] = None,
        action_taken: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Outcome":
        when = when or datetime.now(timezone.utc)
        return cls(
            id=OutcomeId(new_id()),
            identity_id=identity_id,
            outcome_type=OutcomeType.ADVERSE_EVENT,
            observed_by=observed_by,
            observed_at=when,
            severity=severity,
            description=description,
            causality=causality,
            action_taken=action_taken,
            intervention_id=intervention_id,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )