"""
AraOS Neurodevelopmental — Intervention Aggregate Root.

Modelo único compartilhado para QUALQUER intervenção clínica:
medicamentos, cannabis medicinal, ABA, TO, fonoaudiologia,
psicoterapia, neuromodulação, nutrição, exercício, suporte escolar,
treinamento parental.

Invariantes:
    - State machine: STARTED → ADJUSTED/PAUSED → RESUMED → STOPPED.
    - DISCARDED é terminal (intervenção histórica preservada).
    - Dose value/units/frequency juntos ou ausentes (coerência).
    - start_date obrigatório; end_date somente após STOPPED.

ADR-0002 §2.2.5: 'Intervention = qualquer intervenção clínica (medicamentos,
cannabis, psicoterapia, TO, Fono, ABA, neuromodulação, nutrição, exercício)
— todas compartilham o mesmo modelo conceitual.'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .ids import InterventionId, new_id


class InterventionType(str, Enum):
    """Tipo de intervenção clínica."""

    MEDICATION = "medication"
    CANNABIS = "cannabis"
    PSYCHOTHERAPY = "psychotherapy"
    OCCUPATIONAL_THERAPY = "occupational_therapy"
    SPEECH_THERAPY = "speech_therapy"
    ABA = "aba"
    NEUROMODULATION = "neuromodulation"
    NUTRITION = "nutrition"
    EXERCISE = "exercise"
    SCHOOL_SUPPORT = "school_support"
    PARENT_TRAINING = "parent_training"
    OTHER = "other"

    def __str__(self) -> str:
        return self.value


class InterventionState(str, Enum):
    """State machine do Intervention."""

    STARTED = "started"
    ADJUSTED = "adjusted"
    PAUSED = "paused"
    RESUMED = "resumed"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Dose:
    """
    Value Object — dose de uma intervenção.

    Coerência: value + unit + frequency. Pelo menos um conjunto presente
    (intervenções sem dose, ex: ABA hours/week, não exigem Dose).
    """

    value: Optional[float] = None
    unit: Optional[str] = None
    frequency: Optional[str] = None
    # Ex.: value=20, unit='mg', frequency='2x/day'

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "unit": self.unit,
            "frequency": self.frequency,
        }


@dataclass
class Intervention:
    """
    Aggregate Root — uma intervenção clínica completa.

    Attributes:
        id: InterventionId.
        identity_id: ClinicalIdentityId.
        intervention_type: InterventionType.
        subtype: string livre (ex.: 'methylphenidate', 'risperidone', 'ABA_early_intensive').
        started_by: profissional que iniciou.
        start_date: data de início (ISO date).
        dose: Dose atual (pode ser None para intervenções sem dose).
        indication_condition_code: ConditionCode que indica a intervenção.
        linked_diagnosis_ids: lista de DiagnosisId.
        prescriber_id: ID do prescritor (para medicação/cannabis).
        notes: observações clínicas.
        state: estado atual.
        previous_dose: dose anterior (após ADJUSTED).
        end_date: data de término (após STOPPED).
        stop_reason: 'planned_completion'/'adverse_event'/'ineffectiveness'/'patient_choice'/etc.
        stop_outcome_summary: resumo do desfecho ao parar.
        pause_reason: motivo da pausa.
        expected_resume_date: data esperada de retomada após pausa.
        source_event_ids: lista de event_ids.
    """

    id: InterventionId
    identity_id: str
    intervention_type: InterventionType
    subtype: str
    started_by: str
    start_date: str

    dose: Optional[Dose] = None
    indication_condition_code: Optional[str] = None
    linked_diagnosis_ids: List[str] = field(default_factory=list)
    prescriber_id: Optional[str] = None
    notes: Optional[str] = None

    state: InterventionState = InterventionState.STARTED

    previous_dose: Optional[Dose] = None
    end_date: Optional[str] = None
    stop_reason: Optional[str] = None
    stop_outcome_summary: Optional[str] = None

    pause_reason: Optional[str] = None
    expected_resume_date: Optional[str] = None

    source_event_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.subtype or not self.subtype.strip():
            raise ValueError("Intervention.subtype must be non-empty")
        if not self.source_event_ids:
            raise ValueError(
                "Intervention.source_event_ids must contain at least one event_id."
            )

    # ─── State Transitions ──────────────────────────────────────────────

    def adjust(
        self,
        event_id: str,
        adjusted_by: str,
        new_dose: Dose,
        reason: str,
        when: Optional[datetime] = None,
    ) -> "Intervention":
        """
        Ajusta dose. STARTED/ADJUSTED/RESUMED → ADJUSTED.

        STOPPED não pode ser ajustado (estado terminal).
        """
        if self.state == InterventionState.STOPPED:
            raise ValueError("STOPPED intervention cannot be adjusted.")
        if self.state == InterventionState.PAUSED:
            raise ValueError(
                "PAUSED intervention must be RESUMED before adjustment."
            )
        when = when or datetime.now(timezone.utc)
        self.previous_dose = self.dose
        self.dose = new_dose
        self.state = InterventionState.ADJUSTED
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    def pause(
        self,
        event_id: str,
        paused_by: str,
        reason: str,
        expected_resume_date: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Intervention":
        """STARTED/ADJUSTED → PAUSED."""
        if self.state in (InterventionState.PAUSED, InterventionState.STOPPED):
            raise ValueError(
                f"Cannot pause intervention in state {self.state.value}."
            )
        when = when or datetime.now(timezone.utc)
        self.pause_reason = reason
        self.expected_resume_date = expected_resume_date
        self.state = InterventionState.PAUSED
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    def resume(
        self,
        event_id: str,
        resumed_by: str,
        resume_date: str,
        new_dose: Optional[Dose] = None,
        when: Optional[datetime] = None,
    ) -> "Intervention":
        """PAUSED → RESUMED."""
        if self.state != InterventionState.PAUSED:
            raise ValueError(
                f"Only PAUSED interventions can be resumed. Current: {self.state.value}"
            )
        when = when or datetime.now(timezone.utc)
        if new_dose is not None:
            self.previous_dose = self.dose
            self.dose = new_dose
        self.state = InterventionState.RESUMED
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    def stop(
        self,
        event_id: str,
        stopped_by: str,
        end_date: str,
        reason: str,
        outcome_summary: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Intervention":
        """Qualquer estado → STOPPED (estado terminal)."""
        if self.state == InterventionState.STOPPED:
            raise ValueError("Intervention is already stopped.")
        valid_reasons = {
            "planned_completion",
            "adverse_event",
            "ineffectiveness",
            "patient_choice",
            "access_barrier",
            "other",
        }
        if reason not in valid_reasons:
            raise ValueError(
                f"Invalid stop_reason '{reason}'. "
                f"Expected one of: {sorted(valid_reasons)}"
            )
        when = when or datetime.now(timezone.utc)
        self.end_date = end_date
        self.stop_reason = reason
        self.stop_outcome_summary = outcome_summary
        self.state = InterventionState.STOPPED
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    # ─── Helpers ────────────────────────────────────────────────────────

    def is_active(self) -> bool:
        return self.state != InterventionState.STOPPED

    def is_paused(self) -> bool:
        return self.state == InterventionState.PAUSED

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "intervention_type": self.intervention_type.value,
            "subtype": self.subtype,
            "started_by": self.started_by,
            "start_date": self.start_date,
            "dose": self.dose.to_dict() if self.dose else None,
            "previous_dose": (
                self.previous_dose.to_dict() if self.previous_dose else None
            ),
            "indication_condition_code": self.indication_condition_code,
            "linked_diagnosis_ids": list(self.linked_diagnosis_ids),
            "prescriber_id": self.prescriber_id,
            "notes": self.notes,
            "state": self.state.value,
            "end_date": self.end_date,
            "stop_reason": self.stop_reason,
            "stop_outcome_summary": self.stop_outcome_summary,
            "pause_reason": self.pause_reason,
            "expected_resume_date": self.expected_resume_date,
            "is_active": self.is_active(),
            "is_paused": self.is_paused(),
            "source_event_ids": list(self.source_event_ids),
        }

    # ─── Factory ────────────────────────────────────────────────────────

    @classmethod
    def start(
        cls,
        identity_id: str,
        intervention_type: InterventionType,
        subtype: str,
        started_by: str,
        start_date: str,
        source_event_id: str,
        dose: Optional[Dose] = None,
        indication_condition_code: Optional[str] = None,
        linked_diagnosis_ids: Optional[List[str]] = None,
        prescriber_id: Optional[str] = None,
        notes: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Intervention":
        """Cria nova Intervention em estado STARTED."""
        when = when or datetime.now(timezone.utc)
        return cls(
            id=InterventionId(new_id()),
            identity_id=identity_id,
            intervention_type=intervention_type,
            subtype=subtype,
            started_by=started_by,
            start_date=start_date,
            dose=dose,
            indication_condition_code=indication_condition_code,
            linked_diagnosis_ids=list(linked_diagnosis_ids or []),
            prescriber_id=prescriber_id,
            notes=notes,
            state=InterventionState.STARTED,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )