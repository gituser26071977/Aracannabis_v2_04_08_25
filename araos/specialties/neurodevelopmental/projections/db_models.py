"""
AraOS Neurodevelopmental — Registry Projection Tables (SQLAlchemy).

7 tabelas físicas que materializam o Registry. TUDO aqui é derivado
do Event Store — se apagarmos todas, replay deve reconstruir fielmente.

Convenções:
    - tenant_id obrigatório (multi-tenancy).
    - id = aggregate_id (UUID do domain).
    - JSON para campos estruturados (raw_responses, computed_scores, evidence).
    - source_event_ids: lista JSON (rastreabilidade).
    - last_sequence: último sequence aplicado (consistência).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from araos.platform.tenant.models import AuditFieldsMixin, Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _now_utc() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════
# TABLE 1: CLINICAL IDENTITY (Aggregate Root projection)
# ═══════════════════════════════════════════════════════════════════════

class NeuroRegistryClinicalIdentityModel(AuditFieldsMixin, Base):
    """Projeção do Aggregate Root ClinicalIdentity."""

    __tablename__ = "neuro_registry_clinical_identities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    initial_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archive_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Contadores desnormalizados (rápido acesso para listas)
    diagnosis_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    phenotype_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assessment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    intervention_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outcome_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    source_event_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        # 1 ClinicalIdentity por patient_id por tenant
        UniqueConstraint(
            "tenant_id", "patient_id",
            name="REDACTED",
        ),
        Index(
            "REDACTED",
            "tenant_id", "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroRegistryClinicalIdentityModel id={self.id!r} "
            f"tenant={self.tenant_id!r} patient={self.patient_id!r} "
            f"status={self.status!r}>"
        )


# ═══════════════════════════════════════════════════════════════════════
# TABLE 2: DIAGNOSIS (Entity projection)
# ═══════════════════════════════════════════════════════════════════════

class NeuroRegistryDiagnosisModel(AuditFieldsMixin, Base):
    """Projeção do Diagnosis entity."""

    __tablename__ = "neuro_registry_diagnoses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    identity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("neuro_registry_clinical_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    condition_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    # Classification multi-sistema serializada
    classification: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    primary_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    primary_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    severity: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    onset_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    hypothesised_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    confirmation_evidence: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    remission_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    previous_condition_code: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_event_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "REDACTED",
            "identity_id", "state",
        ),
        Index(
            "REDACTED",
            "tenant_id", "state",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroRegistryDiagnosisModel id={self.id!r} "
            f"code={self.condition_code!r} state={self.state!r}>"
        )


# ═══════════════════════════════════════════════════════════════════════
# TABLE 3: PHENOTYPE (Entity projection)
# ═══════════════════════════════════════════════════════════════════════

class NeuroRegistryPhenotypeModel(AuditFieldsMixin, Base):
    """Projeção do Phenotype entity."""

    __tablename__ = "neuro_registry_phenotypes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    identity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("neuro_registry_clinical_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phenotype_code: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    onset_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    linked_diagnosis_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    observed_by: Mapped[str] = mapped_column(String(36), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    resolution_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_event_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "REDACTED",
            "identity_id", "is_active",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroRegistryPhenotypeModel id={self.id!r} "
            f"code={self.phenotype_code!r} active={self.is_active}>"
        )


# ═══════════════════════════════════════════════════════════════════════
# TABLE 4: ASSESSMENT (Entity projection)
# ═══════════════════════════════════════════════════════════════════════

class NeuroRegistryAssessmentModel(AuditFieldsMixin, Base):
    """Projeção do Assessment entity."""

    __tablename__ = "neuro_registry_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    identity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("neuro_registry_clinical_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    scale_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    scale_version: Mapped[str] = mapped_column(String(20), nullable=False)

    applied_by: Mapped[str] = mapped_column(String(36), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    raw_responses: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    computed_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    interpretation: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    linked_diagnosis_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="final")

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    previous_version_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True
    )

    source_event_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "REDACTED",
            "identity_id", "scale_code",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroRegistryAssessmentModel id={self.id!r} "
            f"scale={self.scale_code!r} v={self.scale_version!r}>"
        )


# ═══════════════════════════════════════════════════════════════════════
# TABLE 5: INTERVENTION (Aggregate Root projection)
# ═══════════════════════════════════════════════════════════════════════

class NeuroRegistryInterventionModel(AuditFieldsMixin, Base):
    """Projeção do Intervention aggregate root."""

    __tablename__ = "neuro_registry_interventions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    identity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("neuro_registry_clinical_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    intervention_type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True
    )
    subtype: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    dose: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    previous_dose: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    indication_condition_code: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    linked_diagnosis_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    prescriber_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_by: Mapped[str] = mapped_column(String(36), nullable=False)
    start_date: Mapped[str] = mapped_column(String(10), nullable=False)

    end_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    stop_reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stop_outcome_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pause_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_resume_date: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    is_paused: Mapped[bool] = mapped_column(default=False, nullable=False)

    source_event_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "REDACTED",
            "identity_id", "state",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroRegistryInterventionModel id={self.id!r} "
            f"type={self.intervention_type!r} state={self.state!r}>"
        )


# ═══════════════════════════════════════════════════════════════════════
# TABLE 6: OUTCOME (Entity projection)
# ═══════════════════════════════════════════════════════════════════════

class NeuroRegistryOutcomeModel(AuditFieldsMixin, Base):
    """Projeção do Outcome entity."""

    __tablename__ = "neuro_registry_outcomes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    identity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("neuro_registry_clinical_identities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    outcome_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    observed_by: Mapped[str] = mapped_column(String(36), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    evidence: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    intervention_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    magnitude: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    causality: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    duration_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    responding_domains: Mapped[List[str]] = mapped_column(JSON, default=list)
    non_responding_domains: Mapped[List[str]] = mapped_column(JSON, default=list)
    duration_observed_months: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_event_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    last_sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index(
            "REDACTED",
            "identity_id", "outcome_type",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroRegistryOutcomeModel id={self.id!r} "
            f"type={self.outcome_type!r}>"
        )


# ═══════════════════════════════════════════════════════════════════════
# TABLE 7: PROCESSED EVENTS (idempotency)
# ═══════════════════════════════════════════════════════════════════════

class NeuroRegistryProcessedEventModel(Base):
    """
    Rastro de eventos aplicados ao Registry.

    Usado para:
        1. Idempotência — não aplicar mesmo event_id duas vezes.
        2. Auditoria — quantos eventos foram processados por tenant.
        3. Replay incremental — saber onde parou.
    """

    __tablename__ = "neuro_registry_processed_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    aggregate_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    aggregate_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    sequence: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    event_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )

    __table_args__ = (
        Index(
            "REDACTED",
            "tenant_id", "sequence",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroRegistryProcessedEventModel event_id={self.event_id!r} "
            f"type={self.event_type!r} seq={self.sequence}>"
        )