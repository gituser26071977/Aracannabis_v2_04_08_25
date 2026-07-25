"""
ClinicalContext — Aggregate Root unificado para qualquer contexto clínico.

Sprint 4.2 — ADR-0003. Substitui "ClinicalEpisode" como tipo único.

Este agregado representa QUALQUER contexto relevante para a evolução
longitudinal do paciente: episódios clínicos, períodos de medicação,
mudanças escolares, eventos familiares, marcos de desenvolvimento, etc.

Invariantes enforced em __post_init__:
    - context_id, patient_id, title, start_date não-vazios.
    - confidence_score ∈ [0.0, 1.0].
    - Se origin.is_automated, confidence_score < 1.0 permitido.
    - Se origin MANUAL, confidence_score == 1.0 (criação manual é fato).
    - end_date >= start_date (quando presente).
    - status terminal REJECTED não pode ter confirmed_by.
    - status ACTIVE exige confirmed_by/confirmed_at (quando origin automatizada).
    - end_date obrigatório para Completed/Cancelled/Archived.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_status import (
    ContextStatus,
    requires_confirmation,
    requires_end_date,
)
from araos.clinical.context.domain.context_type import ContextType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ClinicalContext:
    """Aggregate Root unificado para ClinicalContext."""

    context_id: str
    tenant_id: str
    patient_id: str
    context_type: ContextType
    status: ContextStatus
    origin: ContextOrigin
    title: str
    start_date: datetime
    confidence_score: float
    created_at: datetime
    created_by: str
    aggregate_version: int = 1

    # Optional fields
    description: str = ""
    reason: str = ""
    observations: List[str] = field(default_factory=list)

    end_date: Optional[datetime] = None

    source_event_ids: List[str] = field(default_factory=list)
    linked_event_ids: List[str] = field(default_factory=list)
    linked_diagnosis_ids: List[str] = field(default_factory=list)
    linked_phenotype_ids: List[str] = field(default_factory=list)
    linked_intervention_ids: List[str] = field(default_factory=list)
    linked_outcome_ids: List[str] = field(default_factory=list)
    linked_assessment_ids: List[str] = field(default_factory=list)

    professionals: List[str] = field(default_factory=list)
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[datetime] = None

    suggestion_id: Optional[str] = None
    explanation_id: Optional[str] = None

    updated_at: Optional[datetime] = None

    # ─── Validation ──────────────────────────────────────────────────

    def __post_init__(self) -> None:
        if not self.context_id:
            raise ValueError("context_id is required")
        if not self.patient_id:
            raise ValueError("patient_id is required")
        if not self.tenant_id:
            raise ValueError("tenant_id is required")
        if not self.title:
            raise ValueError("title is required (non-empty)")
        if not self.created_by:
            raise ValueError("created_by is required")

        # Timezone-awareness
        if self.start_date.tzinfo is None:
            raise ValueError("start_date must be timezone-aware")
        if self.end_date is not None and self.end_date.tzinfo is None:
            raise ValueError("end_date must be timezone-aware")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if self.confirmed_at is not None and self.confirmed_at.tzinfo is None:
            raise ValueError("confirmed_at must be timezone-aware")

        # end_date >= start_date
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError(
                f"end_date ({self.end_date}) < start_date ({self.start_date})"
            )

        # Confidence score range
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError(
                f"confidence_score must be in [0.0, 1.0], got {self.confidence_score}"
            )

        # Manual origin → confidence_score == 1.0
        if self.origin == ContextOrigin.MANUAL and self.confidence_score < 1.0:
            raise ValueError(
                "manual origin requires confidence_score == 1.0 "
                "(manual creation is fact, not hypothesis)"
            )

        # Status invariants
        if self.status == ContextStatus.REJECTED and self.confirmed_by:
            raise ValueError(
                "rejected context cannot have confirmed_by (terminal state)"
            )
        if self.status in (ContextStatus.COMPLETED, ContextStatus.CANCELLED,
                          ContextStatus.ARCHIVED):
            if self.end_date is None:
                raise ValueError(
                    f"end_date is required for status={self.status.value}"
                )
        if (
            self.status == ContextStatus.ACTIVE
            and self.origin.is_automated
            and self.confirmed_by is None
        ):
            raise ValueError(
                "active context from automated origin requires confirmed_by"
            )
        if (
            self.status == ContextStatus.SUGGESTED
            and self.origin != ContextOrigin.RULE_ENGINE
            and self.origin != ContextOrigin.ARTIFICIAL_INTELLIGENCE
        ):
            raise ValueError(
                "status=Suggested requires origin in {rule_engine, ai}"
            )

    # ─── State machine ──────────────────────────────────────────────

    def can_transition_to(self, target: ContextStatus) -> bool:
        return self.status.can_transition_to(target)

    def transition_to(
        self,
        target: ContextStatus,
        actor_id: str,
        at: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        reason: Optional[str] = None,
    ) -> "ClinicalContext":
        """Retorna nova instância com transição aplicada.

        Não muta — frozen dataclass. Service persiste via evento.
        """
        if not self.can_transition_to(target):
            raise ValueError(
                f"invalid transition {self.status.value} → {target.value}"
            )
        at = at or _utcnow()

        new_fields: Dict[str, Any] = {
            "status": target,
            "aggregate_version": self.aggregate_version + 1,
            "updated_at": at,
        }
        if target == ContextStatus.ACTIVE:
            new_fields["confirmed_by"] = actor_id
            new_fields["confirmed_at"] = at
        elif target == ContextStatus.REJECTED:
            new_fields["rejected_by"] = actor_id
            new_fields["rejected_at"] = at
        elif target in (ContextStatus.COMPLETED, ContextStatus.CANCELLED,
                        ContextStatus.ARCHIVED):
            if end_date:
                new_fields["end_date"] = end_date
            elif self.end_date:
                new_fields["end_date"] = self.end_date
        if reason and target == ContextStatus.REJECTED:
            new_fields["reason"] = reason

        return self._replace(**new_fields)

    # ─── Helpers ────────────────────────────────────────────────────

    def _replace(self, **kwargs: Any) -> "ClinicalContext":
        """Substitui campos e retorna nova instância."""
        from dataclasses import asdict, replace

        d = asdict(self)
        d.update(kwargs)
        # Reconstruct ContextType/ContextStatus from value if stringified
        if isinstance(d.get("context_type"), str):
            d["context_type"] = ContextType(d["context_type"])
        if isinstance(d.get("status"), str):
            d["status"] = ContextStatus(d["status"])
        if isinstance(d.get("origin"), str):
            d["origin"] = ContextOrigin(d["origin"])
        return replace(self, **d)

    def is_active_on(self, at: datetime) -> bool:
        """Verifica se o contexto estava ativo em uma data específica."""
        if at.tzinfo is None:
            at = at.replace(tzinfo=timezone.utc)
        if at < self.start_date:
            return False
        if self.end_date is not None and at > self.end_date:
            return False
        return self.status in (ContextStatus.ACTIVE, ContextStatus.SUGGESTED,
                               ContextStatus.PLANNED, ContextStatus.COMPLETED)

    @property
    def is_open(self) -> bool:
        return self.status in (ContextStatus.ACTIVE, ContextStatus.SUGGESTED,
                               ContextStatus.PLANNED)

    @property
    def is_terminal(self) -> bool:
        return self.status.is_terminal

    @property
    def duration_days(self) -> Optional[float]:
        if self.end_date is None:
            return None
        return (self.end_date - self.start_date).total_seconds() / 86400.0

    def link_entity(
        self,
        entity_kind: str,
        entity_id: str,
    ) -> "ClinicalContext":
        """Adiciona link a uma entidade (event/diagnosis/phenotype/etc.)."""
        field_name = f"linked_{entity_kind}_ids"
        if not hasattr(self, field_name):
            raise ValueError(f"unsupported entity_kind: {entity_kind}")
        current = list(getattr(self, field_name))
        if entity_id in current:
            return self  # idempotent
        new_list = current + [entity_id]
        return self._replace(**{field_name: new_list})

    def unlink_entity(
        self,
        entity_kind: str,
        entity_id: str,
    ) -> "ClinicalContext":
        field_name = f"linked_{entity_kind}_ids"
        if not hasattr(self, field_name):
            raise ValueError(f"unsupported entity_kind: {entity_kind}")
        current = list(getattr(self, field_name))
        if entity_id not in current:
            return self
        new_list = [e for e in current if e != entity_id]
        return self._replace(**{field_name: new_list})

    # ─── Serialization ──────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context_id": self.context_id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "context_type": self.context_type.value,
            "status": self.status.value,
            "origin": self.origin.value,
            "title": self.title,
            "description": self.description,
            "reason": self.reason,
            "observations": list(self.observations),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "confidence_score": self.confidence_score,
            "source_event_ids": list(self.source_event_ids),
            "linked_event_ids": list(self.linked_event_ids),
            "linked_diagnosis_ids": list(self.linked_diagnosis_ids),
            "linked_phenotype_ids": list(self.linked_phenotype_ids),
            "linked_intervention_ids": list(self.linked_intervention_ids),
            "linked_outcome_ids": list(self.linked_outcome_ids),
            "linked_assessment_ids": list(self.linked_assessment_ids),
            "professionals": list(self.professionals),
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "suggestion_id": self.suggestion_id,
            "explanation_id": self.explanation_id,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "aggregate_version": self.aggregate_version,
            "is_open": self.is_open,
            "duration_days": self.duration_days,
        }
