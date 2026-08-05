"""
AraOS Neurodevelopmental — ClinicalIdentity Aggregate Root.

Aggregate Root permanente que representa a identidade clínica longitudinal
do paciente. Sobrevive a TODAS as mudanças clínicas (diagnósticos,
fenótipos, intervenções, desfechos).

Invariantes:
    - 1 ClinicalIdentity por patient_id (no escopo de 1 tenant).
    - Não deleta — apenas ARQUIVA (status = archived).
    - Compõe Diagnosis, Phenotype, Assessment, Intervention, Outcome
      por REFERÊNCIA (IDs), não por cópia.
    - Toda mutação ocorre via Domain Event publicado no Event Store.

ADR-0002 §2.2.1: 'Registry como Aggregate Root permanente. Não deleta —
apenas arquiva. Compõe todas as outras entidades por referência.'
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from .ids import ClinicalIdentityId, new_id


class ClinicalIdentityStatus(str, Enum):
    """Status do Aggregate Root."""

    ACTIVE = "active"
    """Identidade em acompanhamento clínico ativo."""

    ARCHIVED = "archived"
    """Identidade arquivada (transferência, alta, óbito, administrativo).
    Histórico permanece — não deleta."""


@dataclass
class ClinicalIdentity:
    """
    Aggregate Root — identidade clínica longitudinal do paciente.

    Representa o que NÃO muda ao longo da vida clínica:
        - Vinculação 1:1 com patient_id (administrativo).
        - Permanente — não deleta.
        - Compõe todas as outras entidades por referência.

    Attributes:
        id: ClinicalIdentityId.
        patient_id: ID administrativo do paciente (externo).
        status: ACTIVE ou ARCHIVED.
        initial_notes: observações iniciais opcionais.
        archived_at: timestamp do arquivamento (None se ACTIVE).
        archive_reason: motivo do arquivamento.
        diagnosis_ids: lista de DiagnosisId (não por cópia).
        phenotype_ids: lista de PhenotypeId.
        assessment_ids: lista de AssessmentId.
        intervention_ids: lista de InterventionId.
        outcome_ids: lista de OutcomeId.
        source_event_ids: lista de event_ids que originaram este agregado.
        created_at: timestamp de criação.
        updated_at: timestamp da última mudança.
    """

    id: ClinicalIdentityId
    patient_id: str
    status: ClinicalIdentityStatus = ClinicalIdentityStatus.ACTIVE

    initial_notes: Optional[str] = None

    archived_at: Optional[datetime] = None
    archive_reason: Optional[str] = None

    diagnosis_ids: List[str] = field(default_factory=list)
    phenotype_ids: List[str] = field(default_factory=list)
    assessment_ids: List[str] = field(default_factory=list)
    intervention_ids: List[str] = field(default_factory=list)
    outcome_ids: List[str] = field(default_factory=list)

    source_event_ids: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Invariantes de construção."""
        if not self.source_event_ids:
            raise ValueError(
                "ClinicalIdentity.source_event_ids must contain at least one event_id."
            )

    # ─── Aggregate Operations ──────────────────────────────────────────

    def attach_diagnosis(self, diagnosis_id: str, event_id: str) -> "ClinicalIdentity":
        """Vincula um Diagnosis ao aggregate."""
        if diagnosis_id not in self.diagnosis_ids:
            self.diagnosis_ids.append(diagnosis_id)
        self.source_event_ids.append(event_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def attach_phenotype(self, phenotype_id: str, event_id: str) -> "ClinicalIdentity":
        if phenotype_id not in self.phenotype_ids:
            self.phenotype_ids.append(phenotype_id)
        self.source_event_ids.append(event_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def attach_assessment(self, assessment_id: str, event_id: str) -> "ClinicalIdentity":
        if assessment_id not in self.assessment_ids:
            self.assessment_ids.append(assessment_id)
        self.source_event_ids.append(event_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def attach_intervention(self, intervention_id: str, event_id: str) -> "ClinicalIdentity":
        if intervention_id not in self.intervention_ids:
            self.intervention_ids.append(intervention_id)
        self.source_event_ids.append(event_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def attach_outcome(self, outcome_id: str, event_id: str) -> "ClinicalIdentity":
        if outcome_id not in self.outcome_ids:
            self.outcome_ids.append(outcome_id)
        self.source_event_ids.append(event_id)
        self.updated_at = datetime.now(timezone.utc)
        return self

    # ─── Archival ──────────────────────────────────────────────────────

    def archive(
        self,
        event_id: str,
        reason: str,
        when: Optional[datetime] = None,
    ) -> "ClinicalIdentity":
        """
        Arquiva a identidade. Estado terminal — não deleta, apenas ARQUIVA.

        Args:
            event_id: ID do evento CLINICAL_IDENTITY_ARCHIVED.
            reason: 'patient_transferred'/'patient_deceased'/etc.
            when: timestamp (default: now UTC).
        """
        if self.status == ClinicalIdentityStatus.ARCHIVED:
            raise ValueError("ClinicalIdentity is already archived.")
        when = when or datetime.now(timezone.utc)
        self.status = ClinicalIdentityStatus.ARCHIVED
        self.archived_at = when
        self.archive_reason = reason
        self.source_event_ids.append(event_id)
        self.updated_at = when
        return self

    def is_active(self) -> bool:
        return self.status == ClinicalIdentityStatus.ACTIVE

    def is_archived(self) -> bool:
        return self.status == ClinicalIdentityStatus.ARCHIVED

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "status": self.status.value,
            "initial_notes": self.initial_notes,
            "archived_at": (
                self.archived_at.isoformat() if self.archived_at else None
            ),
            "archive_reason": self.archive_reason,
            "diagnosis_count": len(self.diagnosis_ids),
            "phenotype_count": len(self.phenotype_ids),
            "assessment_count": len(self.assessment_ids),
            "intervention_count": len(self.intervention_ids),
            "outcome_count": len(self.outcome_ids),
            "diagnosis_ids": list(self.diagnosis_ids),
            "phenotype_ids": list(self.phenotype_ids),
            "assessment_ids": list(self.assessment_ids),
            "intervention_ids": list(self.intervention_ids),
            "outcome_ids": list(self.outcome_ids),
            "source_event_ids": list(self.source_event_ids),
            "created_at": (
                self.created_at.isoformat() if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at else None
            ),
        }

    # ─── Factory ────────────────────────────────────────────────────────

    @classmethod
    def create(
        cls,
        patient_id: str,
        source_event_id: str,
        initial_notes: Optional[str] = None,
        when: Optional[datetime] = None,
    ) -> "ClinicalIdentity":
        """
        Cria nova ClinicalIdentity em estado ACTIVE.

        Args:
            patient_id: ID administrativo do paciente.
            source_event_id: event_id do CLINICAL_IDENTITY_CREATED.
            initial_notes: observações iniciais opcionais.
            when: timestamp (default: now UTC).
        """
        when = when or datetime.now(timezone.utc)
        return cls(
            id=ClinicalIdentityId(new_id()),
            patient_id=patient_id,
            status=ClinicalIdentityStatus.ACTIVE,
            initial_notes=initial_notes,
            source_event_ids=[source_event_id],
            created_at=when,
            updated_at=when,
        )