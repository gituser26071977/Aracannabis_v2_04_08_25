"""
AraOS Neurodevelopmental — Phenotype Entity.

Fenótipo = manifestação funcional observável. Independente do diagnóstico:
pode existir ANTES (sinal de alerta), DURANTE (acompanhamento),
ou DEPOIS (residual, persistência).

Invariantes:
    - source_event_ids sempre presente.
    - severity ∈ {'mild', 'moderate', 'severe', 'profound'}.
    - Resolved phenotypes têm resolved_at preenchido; ativos, não.

ADR-0002 §2.2.3: 'Phenotype = manifestações funcionais observáveis,
pode existir antes do diagnóstico, pode persistir após mudança diagnóstica.'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from .ids import PhenotypeId, new_id


class PhenotypeSeverity(str, Enum):
    """Severidade observada do fenótipo."""

    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    PROFOUND = "profound"

    def __str__(self) -> str:
        return self.value


@dataclass
class Phenotype:
    """
    Entity — manifestação funcional observável.

    Attributes:
        id: PhenotypeId.
        identity_id: ClinicalIdentityId à qual pertence.
        phenotype_code: código do catálogo interno (ex: 'SOCIAL_DEFICIT',
                        'SENSORY_HYPERSENSITIVITY', 'COMMUNICATION_DELAY').
        severity: PhenotypeSeverity.
        onset_date: data de início (ISO date string).
        linked_diagnosis_ids: lista de DiagnosisId correlacionados (opcional).
        context: descrição textual do contexto de observação.
        observed_at: timestamp de observação inicial.
        observed_by: profissional.
        resolved_at: timestamp de resolução (None se ativo).
        resolved_by: profissional que resolveu.
        resolution_reason: justificativa.
        source_event_ids: lista de event_ids.
        created_at: timestamp de criação.
        updated_at: timestamp da última mudança.
    """

    id: PhenotypeId
    identity_id: str
    phenotype_code: str
    severity: PhenotypeSeverity
    observed_by: str

    onset_date: Optional[str] = None
    linked_diagnosis_ids: List[str] = field(default_factory=list)
    context: Optional[str] = None

    observed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_reason: Optional[str] = None

    source_event_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.phenotype_code or not self.phenotype_code.strip():
            raise ValueError("phenotype_code must be non-empty")
        if not self.source_event_ids:
            raise ValueError(
                "Phenotype.source_event_ids must contain at least one event_id."
            )

    # ─── Operations ─────────────────────────────────────────────────────

    def resolve(
        self,
        event_id: str,
        resolved_by: str,
        reason: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Phenotype":
        """
        Marca fenótipo como resolvido. Não deleta — histórico preservado.
        """
        if self.resolved_at is not None:
            raise ValueError(
                f"Phenotype {self.id} is already resolved at {self.resolved_at.isoformat()}"
            )
        when = when or datetime.now(timezone.utc)
        self.resolved_at = when
        self.resolved_by = resolved_by
        self.resolution_reason = reason
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    def is_active(self) -> bool:
        return self.resolved_at is None

    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "identity_id": self.identity_id,
            "phenotype_code": self.phenotype_code,
            "severity": self.severity.value,
            "onset_date": self.onset_date,
            "linked_diagnosis_ids": list(self.linked_diagnosis_ids),
            "context": self.context,
            "observed_at": (
                self.observed_at.isoformat() if self.observed_at else None
            ),
            "observed_by": self.observed_by,
            "resolved_at": (
                self.resolved_at.isoformat() if self.resolved_at else None
            ),
            "resolved_by": self.resolved_by,
            "resolution_reason": self.resolution_reason,
            "is_active": self.is_active(),
            "source_event_ids": list(self.source_event_ids),
        }

    # ─── Factory ────────────────────────────────────────────────────────

    @classmethod
    def observe(
        cls,
        identity_id: str,
        phenotype_code: str,
        severity: PhenotypeSeverity,
        observed_by: str,
        source_event_id: str,
        onset_date: Optional[str] = None,
        linked_diagnosis_ids: Optional[List[str]] = None,
        context: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "Phenotype":
        """Cria novo Phenotype em estado ativo."""
        when = when or datetime.now(timezone.utc)
        return cls(
            id=PhenotypeId(new_id()),
            identity_id=identity_id,
            phenotype_code=phenotype_code,
            severity=severity,
            observed_by=observed_by,
            onset_date=onset_date,
            linked_diagnosis_ids=list(linked_diagnosis_ids or []),
            context=context,
            observed_at=when,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )