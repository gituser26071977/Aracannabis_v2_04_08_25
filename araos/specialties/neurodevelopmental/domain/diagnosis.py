"""
AraOS Neurodevelopmental — Diagnosis Entity + State Machine.

Estado de um Diagnosis segue ciclo de vida clínico real:

    HYPOTHESIS ──┬──→ INVESTIGATING ──┬──→ CONFIRMED ──┬──→ REVISED
                 │                    │                ├──→ IN_REMISSION
                 │                    │                └──→ DISCARDED
                 ↓                    ↓
              DISCARDED           DISCARDED

    CONFIRMED pode também ir direto para DISCARDED (erro diagnóstico tardio).
    REVISED gera um NOVO diagnosis (re-inicia ciclo); o anterior é arquivado
    conceitualmente (estado final = REVISED).

ADR-0002 §2.2.2: 'Diagnosis = ciclo de vida com 6 estados: Hipótese,
Em investigação, Confirmado, Revisado, Remissão, Descartado. Cada mudança
gera Clinical Event. Nunca atualizar silenciosamente.'

Invariantes:
    - Transições inválidas → InvalidDiagnosisTransitionError.
    - `confirmed_at` requer `confirmation_evidence` não-vazio.
    - source_event_ids sempre presente (lista, pode ter 1 item).
    - classification.validate() é chamada em estados CONFIRMED/REVISED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .classification import DiagnosisClassification
from .condition import ConditionCode
from .ids import DiagnosisId, new_id


class InvalidDiagnosisTransitionError(ValueError):
    """Transição de estado inválida para o Diagnosis."""

    def __init__(self, from_state: str, to_state: str) -> None:
        super().__init__(
            f"Invalid diagnosis state transition: {from_state} → {to_state}"
        )
        self.from_state = from_state
        self.to_state = to_state


class DiagnosisState(str, Enum):
    """6 estados do ciclo de vida de um Diagnosis."""

    HYPOTHESIS = "hypothesis"
    """Hipótese clínica inicial — ainda sem evidência suficiente."""

    INVESTIGATING = "investigating"
    """Coleta ativa de evidência para confirmar ou descartar."""

    CONFIRMED = "confirmed"
    """Diagnóstico confirmado com evidência documentada."""

    REVISED = "revised"
    """Diagnóstico revisado (mudança de condição ou severidade)."""

    IN_REMISSION = "in_remission"
    """Em remissão (parcial ou total). Não deleta — pode recidivar."""

    DISCARDED = "discarded"
    """Descartado (hipótese rejeitada, erro diagnóstico, recuperação)."""

    def __str__(self) -> str:
        return self.value


# Matriz de transições válidas. Encapsulada no módulo (serviço usa via
# DiagnosisTransitionService.validate()).
_VALID_TRANSITIONS: Dict[DiagnosisState, frozenset[DiagnosisState]] = {
    DiagnosisState.HYPOTHESIS: frozenset(
        {
            DiagnosisState.INVESTIGATING,
            DiagnosisState.CONFIRMED,  # evidência direta, pula investigação
            DiagnosisState.DISCARDED,
        }
    ),
    DiagnosisState.INVESTIGATING: frozenset(
        {
            DiagnosisState.CONFIRMED,
            DiagnosisState.DISCARDED,
            DiagnosisState.HYPOTHESIS,  # volta para refinar hipótese
        }
    ),
    DiagnosisState.CONFIRMED: frozenset(
        {
            DiagnosisState.REVISED,
            DiagnosisState.IN_REMISSION,
            DiagnosisState.DISCARDED,  # erro diagnóstico tardio
        }
    ),
    DiagnosisState.REVISED: frozenset(
        {
            DiagnosisState.IN_REMISSION,
            DiagnosisState.DISCARDED,
        }
    ),
    DiagnosisState.IN_REMISSION: frozenset(
        {
            DiagnosisState.CONFIRMED,  # recidiva
            DiagnosisState.REVISED,
            DiagnosisState.DISCARDED,
        }
    ),
    DiagnosisState.DISCARDED: frozenset(),  # estado terminal
}


@dataclass
class Diagnosis:
    """
    Entity — um diagnóstico dentro de uma ClinicalIdentity.

    Cada mudança de estado gera Domain Event publicado no Event Store.
    Mutações no objeto representam estado RECONSTRUÍDO a partir do log.

    Attributes:
        id: DiagnosisId (imutável).
        identity_id: ClinicalIdentityId ao qual pertence.
        condition_code: ConditionCode do catálogo interno.
        state: estado atual.
        classification: classificação multi-sistema (pode estar vazia).
        hypothesised_at: datetime da hipótese inicial.
        confirmed_at: datetime da confirmação (None se ainda não confirmado).
        confirmation_evidence: dict com assessment_ids, exam_ids, criteria_met.
        severity: severidade clínica ('mild'/'moderate'/'severe'/'profound').
        onset_date: data de início clínico (pode ser anterior à hipótese).
        remission_type: 'partial'/'complete' (somente em IN_REMISSION).
        previous_condition_code: condition_code anterior (REVISED only).
        rationale: justificativa clínica textual.
        source_event_ids: lista de event_ids que originaram este estado.
        created_at: timestamp de criação (no Event Store).
        updated_at: timestamp da última mudança.
    """

    id: DiagnosisId
    identity_id: str
    condition_code: ConditionCode
    state: DiagnosisState

    classification: DiagnosisClassification = field(
        default_factory=DiagnosisClassification.empty
    )

    hypothesised_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    confirmation_evidence: Dict[str, Any] = field(default_factory=dict)
    severity: Optional[str] = None

    onset_date: Optional[str] = None  # ISO date string
    remission_type: Optional[str] = None
    previous_condition_code: Optional[str] = None

    rationale: Optional[str] = None

    source_event_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Invariantes de construção."""
        if not self.source_event_ids:
            raise ValueError(
                "Diagnosis.source_event_ids must contain at least one event_id "
                "(provenance obrigatório — toda entidade nasce de um evento)."
            )

    # ─── Invariantes ────────────────────────────────────────────────────

    def _ensure_valid_state(self, current: DiagnosisState, target: DiagnosisState) -> None:
        """Levanta InvalidDiagnosisTransitionError se transição inválida."""
        valid_targets = _VALID_TRANSITIONS.get(current, frozenset())
        if target not in valid_targets:
            raise InvalidDiagnosisTransitionError(
                from_state=current.value, to_state=target.value
            )

    def _ensure_can_confirm(self) -> None:
        """Invariante: CONFIRMED exige confirmation_evidence não-vazio."""
        if not self.confirmation_evidence:
            raise ValueError(
                "Cannot transition to CONFIRMED without confirmation_evidence "
                "(assessment_ids, exam_ids, or clinical_criteria_met required)."
            )

    def REDACTED(self) -> None:
        """CONFIRMED e REVISED exigem classificação com pelo menos 1 entry."""
        if self.state in (DiagnosisState.CONFIRMED, DiagnosisState.REVISED):
            self.classification.validate()

    # ─── State Transitions (aplicam invariantes + retornam self) ─────────

    def start_investigation(self, event_id: str, when: Optional[datetime] = None) -> "Diagnosis":
        """HYPOTHESIS → INVESTIGATING."""
        self._ensure_valid_state(self.state, DiagnosisState.INVESTIGATING)
        when = when or datetime.now(timezone.utc)
        self.state = DiagnosisState.INVESTIGATING
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    def confirm(
        self,
        event_id: str,
        confirmed_by: str,
        confirmation_evidence: Dict[str, Any],
        severity: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Diagnosis":
        """
        HYPOTHESIS ou INVESTIGATING → CONFIRMED.

        Args:
            event_id: ID do evento DIAGNOSIS_CONFIRMED que origina a mudança.
            confirmed_by: ID do profissional (audit).
            confirmation_evidence: dict não-vazio com assessment_ids/exam_ids/criteria_met.
            severity: 'mild'/'moderate'/'severe'/'profound' (opcional).
            when: timestamp (default: now UTC).
        """
        self._ensure_valid_state(self.state, DiagnosisState.CONFIRMED)
        when = when or datetime.now(timezone.utc)
        self.confirmation_evidence = confirmation_evidence
        if severity is not None:
            self.severity = severity
        self.state = DiagnosisState.CONFIRMED
        self.confirmed_at = when
        self.source_event_ids.append(event_id)
        self.updated_at = when
        # Invariante pós-transição
        self._ensure_can_confirm()
        self.REDACTED()
        return self

    def revise(
        self,
        event_id: str,
        new_condition_code: ConditionCode,
        revised_by: str,
        reason: str,
        when: Optional[datetime] = None,
    ) -> "Diagnosis":
        """
        CONFIRMED → REVISED.

        Args:
            event_id: ID do evento DIAGNOSIS_REVISED.
            new_condition_code: novo ConditionCode.
            revised_by: profissional responsável.
            reason: justificativa clínica.
        """
        self._ensure_valid_state(self.state, DiagnosisState.REVISED)
        when = when or datetime.now(timezone.utc)
        self.previous_condition_code = str(self.condition_code)
        self.condition_code = new_condition_code
        self.rationale = reason
        self.state = DiagnosisState.REVISED
        self.source_event_ids.append(event_id)
        self.updated_at = when
        self.REDACTED()
        return self

    def mark_in_remission(
        self,
        event_id: str,
        remission_type: str,
        marked_by: str,
        evidence: Optional[Dict[str, Any]] = None,
        when: Optional[datetime] = None,
    ) -> "Diagnosis":
        """
        CONFIRMED ou REVISED → IN_REMISSION.

        Args:
            event_id: ID do evento DIAGNOSIS_IN_REMISSION.
            remission_type: 'partial' ou 'complete'.
            marked_by: profissional.
            evidence: dict opcional com assessment_ids.
        """
        self._ensure_valid_state(self.state, DiagnosisState.IN_REMISSION)
        if remission_type not in ("partial", "complete"):
            raise ValueError(
                f"Invalid remission_type: '{remission_type}'. "
                "Expected 'partial' or 'complete'."
            )
        when = when or datetime.now(timezone.utc)
        self.remission_type = remission_type
        self.state = DiagnosisState.IN_REMISSION
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    def discard(
        self,
        event_id: str,
        discarded_by: str,
        reason: str,
        when: Optional[datetime] = None,
    ) -> "Diagnosis":
        """
        HYPOTHESIS/INVESTIGATING/CONFIRMED/IN_REMISSION → DISCARDED.

        Estado terminal.
        """
        self._ensure_valid_state(self.state, DiagnosisState.DISCARDED)
        when = when or datetime.now(timezone.utc)
        self.rationale = reason
        self.state = DiagnosisState.DISCARDED
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    # ─── Classifications (mutate self.classification) ───────────────────

    def add_classification(
        self, event_id: str, classification: DiagnosisClassification
    ) -> "Diagnosis":
        """
        Adiciona classificação. Substitui self.classification (imutável).
        """
        self.classification = classification
        self.source_event_ids.append(event_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def remove_classification(
        self, event_id: str, classification: DiagnosisClassification
    ) -> "Diagnosis":
        """
        Remove classificação. Substitui self.classification (imutável).
        """
        self.classification = classification
        self.source_event_ids.append(event_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    # ─── Helpers ────────────────────────────────────────────────────────

    def is_terminal(self) -> bool:
        """DISCARDED é estado terminal."""
        return self.state == DiagnosisState.DISCARDED

    def to_dict(self) -> Dict[str, Any]:
        """Serialização para JSON."""
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "condition_code": str(self.condition_code),
            "state": self.state.value,
            "classification": self.classification.to_dict(),
            "hypothesised_at": (
                self.hypothesised_at.isoformat() if self.hypothesised_at else None
            ),
            "confirmed_at": (
                self.confirmed_at.isoformat() if self.confirmed_at else None
            ),
            "severity": self.severity,
            "onset_date": self.onset_date,
            "remission_type": self.remission_type,
            "previous_condition_code": self.previous_condition_code,
            "rationale": self.rationale,
            "source_event_ids": list(self.source_event_ids),
        }

    # ─── Factory ────────────────────────────────────────────────────────

    @classmethod
    def hypothesise(
        cls,
        identity_id: str,
        condition_code: ConditionCode,
        hypothesised_by: str,
        source_event_id: str,
        reason: Optional[str] = None,
        onset_date: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Diagnosis":
        """
        Cria novo Diagnosis em estado HYPOTHESIS.

        Args:
            identity_id: ClinicalIdentityId à qual pertence.
            condition_code: ConditionCode do catálogo.
            hypothesised_by: ID do profissional.
            source_event_id: event_id do DIAGNOSIS_HYPOTHESIZED.
            reason: justificativa clínica.
            onset_date: data de início clínico (ISO date).
            when: timestamp (default: now UTC).
        """
        when = when or datetime.now(timezone.utc)
        return cls(
            id=DiagnosisId(new_id()),
            identity_id=identity_id,
            condition_code=condition_code,
            state=DiagnosisState.HYPOTHESIS,
            hypothesised_at=when,
            onset_date=onset_date,
            rationale=reason,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )