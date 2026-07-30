"""
SQL persistence para Clinical Context Engine (Sprint 4.2 / ADR-0003).

Camadas:
    1. ORM Models:
        - ClinicalContextModel     (write-side aggregate)
        - ContextRelationshipModel (graph edge)
        - ProcessedRuleEvaluationModel (idempotência)
    2. Converters row ↔ domain.
    3. SqlAlchemyClinicalContextQuery (read-side).
    4. REDACTED (write-side — usado pela API/projection).
    5. REDACTED (relationship CRUD).

Padrão (Sprint 3.2 + 4.1):
    - AuditFieldsMixin + Base de araos.platform.tenant.models.
    - tenant_id sempre presente + indexado.
    - Idempotência via id (context_id / relationship_id / composite key).
    - Read-side puro — não muta ClinicalContext (devolve cópias imutáveis).
    - Conversão defensiva pra SQLite (datetimes naive).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Session, Mapped, mapped_column

from araos.clinical.context.application.query import (
    ClinicalContextQuery,
    _ensure_tz,
)
from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_relationship import (
    ContextRelationship,
    RelationshipType,
)
from araos.clinical.context.domain.context_status import ContextStatus
from araos.clinical.context.domain.context_type import ContextType
from araos.platform.tenant.models import AuditFieldsMixin, Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _now() -> datetime:
    # SQLite-friendly: insertada com tz-naive UTC por baixo, mas devolvemos
    # tz-aware sempre via _ensure_tz_aware na leitura.
    return _utcnow()


def _ensure_tz_aware(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ═══════════════════════════════════════════════════════════════════════
# ORM MODELS
# ═══════════════════════════════════════════════════════════════════════


class ClinicalContextModel(AuditFieldsMixin, Base):
    """Materializa um ClinicalContext Aggregate Root."""

    __tablename__ = "clinical_contexts"

    context_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    context_type: Mapped[str] = mapped_column(String(48), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    origin: Mapped[str] = mapped_column(String(24), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    observations_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Source provenance
    source_event_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    linked_event_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    linked_diagnosis_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    linked_phenotype_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    linked_intervention_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    linked_outcome_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    linked_assessment_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    professionals_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)

    # Confirmation / rejection
    confirmed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Provenance to suggester + explainability
    suggestion_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    explanation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_ctx_tenant_patient_status", "tenant_id", "patient_id", "status"),
        Index("ix_ctx_tenant_patient_type", "tenant_id", "patient_id", "context_type"),
        Index("ix_ctx_tenant_created", "tenant_id", "created_at"),
        Index("ix_ctx_status_origin", "status", "origin"),
    )


class ContextRelationshipModel(AuditFieldsMixin, Base):
    """Edge no grafo entre ClinicalContexts."""

    __tablename__ = "clinical_context_relationships"

    relationship_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_context_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_context_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    evidence_event_ids_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
    )

    __table_args__ = (
        Index("ix_crel_tenant_source", "tenant_id", "source_context_id"),
        Index("ix_crel_tenant_target", "tenant_id", "target_context_id"),
        Index("ix_crel_tenant_type", "tenant_id", "relationship_type"),
    )


class ProcessedRuleEvaluationModel(Base):
    """Idempotência para execuções do Rule Engine.

    PK: (tenant_id, patient_id, event_id, rule_id)
    Impede que a mesma avaliação produza Suggestions duplicadas em replay.
    """

    __tablename__ = "REDACTED"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: uuid.uuid4().hex)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    suggestion_id: Mapped[str] = mapped_column(String(64), nullable=False)
    context_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "patient_id", "rule_id", "event_id",
            name="uq_ctx_processed_rule_eval",
        ),
        Index("ix_ctx_processed_tenant_patient", "tenant_id", "patient_id"),
    )


# ═══════════════════════════════════════════════════════════════════════
# ROW → DOMAIN conversion
# ═══════════════════════════════════════════════════════════════════════


def _row_to_context(row: ClinicalContextModel) -> ClinicalContext:
    return ClinicalContext(
        context_id=row.context_id,
        tenant_id=row.tenant_id,
        patient_id=row.patient_id,
        context_type=ContextType(row.context_type),
        status=ContextStatus(row.status),
        origin=ContextOrigin(row.origin),
        title=row.title,
        description=row.description or "",
        reason=row.reason or "",
        observations=list(row.observations_json or []),
        start_date=_ensure_tz_aware(row.start_date),    # type: ignore[arg-type]
        end_date=_ensure_tz_aware(row.end_date),
        confidence_score=row.confidence_score,
        source_event_ids=list(row.source_event_ids_json or []),
        linked_event_ids=list(row.linked_event_ids_json or []),
        linked_diagnosis_ids=list(row.linked_diagnosis_ids_json or []),
        linked_phenotype_ids=list(row.linked_phenotype_ids_json or []),
        linked_intervention_ids=list(row.linked_intervention_ids_json or []),
        linked_outcome_ids=list(row.linked_outcome_ids_json or []),
        linked_assessment_ids=list(row.linked_assessment_ids_json or []),
        professionals=list(row.professionals_json or []),
        confirmed_by=row.confirmed_by,
        confirmed_at=_ensure_tz_aware(row.confirmed_at),
        rejected_by=row.rejected_by,
        rejected_at=_ensure_tz_aware(row.rejected_at),
        suggestion_id=row.suggestion_id,
        explanation_id=row.explanation_id,
        created_at=_ensure_tz_aware(row.created_at),    # type: ignore[arg-type]
        updated_at=_ensure_tz_aware(row.updated_at),
        aggregate_version=row.aggregate_version,
        created_by=row.created_by or "system",
    )


def _context_to_row(ctx: ClinicalContext) -> ClinicalContextModel:
    return ClinicalContextModel(
        context_id=ctx.context_id,
        tenant_id=ctx.tenant_id,
        patient_id=ctx.patient_id,
        context_type=ctx.context_type.value,
        status=ctx.status.value,
        origin=ctx.origin.value,
        title=ctx.title,
        description=ctx.description or "",
        reason=ctx.reason or "",
        observations_json=list(ctx.observations),
        start_date=ctx.start_date,
        end_date=ctx.end_date,
        confidence_score=ctx.confidence_score,
        source_event_ids_json=list(ctx.source_event_ids),
        linked_event_ids_json=list(ctx.linked_event_ids),
        linked_diagnosis_ids_json=list(ctx.linked_diagnosis_ids),
        linked_phenotype_ids_json=list(ctx.linked_phenotype_ids),
        linked_intervention_ids_json=list(ctx.linked_intervention_ids),
        linked_outcome_ids_json=list(ctx.linked_outcome_ids),
        linked_assessment_ids_json=list(ctx.linked_assessment_ids),
        professionals_json=list(ctx.professionals),
        confirmed_by=ctx.confirmed_by,
        confirmed_at=ctx.confirmed_at,
        rejected_by=ctx.rejected_by,
        rejected_at=ctx.rejected_at,
        suggestion_id=ctx.suggestion_id,
        explanation_id=ctx.explanation_id,
        created_at=ctx.created_at,
        updated_at=ctx.updated_at,
        aggregate_version=ctx.aggregate_version,
        created_by=ctx.created_by,
    )


def _row_to_relationship(row: ContextRelationshipModel) -> ContextRelationship:
    return ContextRelationship(
        relationship_id=row.relationship_id,
        tenant_id=row.tenant_id,
        source_context_id=row.source_context_id,
        target_context_id=row.target_context_id,
        relationship_type=RelationshipType(row.relationship_type),
        confidence=row.confidence,
        evidence_event_ids=list(row.evidence_event_ids_json or []),
        created_at=_ensure_tz_aware(row.created_at),    # type: ignore[arg-type]
        created_by=row.created_by or "system",
    )


# ═══════════════════════════════════════════════════════════════════════
# SQL Query (read-side)
# ═══════════════════════════════════════════════════════════════════════


class SqlAlchemyClinicalContextQuery(ClinicalContextQuery):
    """Implementação SQL do ClinicalContextQuery.

    Cada método abre transação curta. Sem cache — freshness é crítica para
    apresentação clínica.
    """

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        status: Optional[ContextStatus] = None,
        context_type: Optional[ContextType] = None,
    ) -> List[ClinicalContext]:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = (
                select(ClinicalContextModel)
                .where(
                    ClinicalContextModel.tenant_id == tenant_id,
                    ClinicalContextModel.patient_id == patient_id,
                )
                .order_by(ClinicalContextModel.start_date.asc())
            )
            if status is not None:
                stmt = stmt.where(ClinicalContextModel.status == status.value)
            if context_type is not None:
                stmt = stmt.where(ClinicalContextModel.context_type == context_type.value)
            rows = session.execute(stmt).scalars().all()
            return [_row_to_context(r) for r in rows]

    def get(self, tenant_id: str, context_id: str) -> Optional[ClinicalContext]:
        with self._session_factory() as session:
            row = session.get(ClinicalContextModel, context_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            return _row_to_context(row)

    def active_at(
        self,
        tenant_id: str,
        patient_id: str,
        at_date: datetime,
    ) -> List[ClinicalContext]:
        """Contextos cujo start ≤ at_date e (end_date IS NULL ou end_date ≥ at_date)."""
        from sqlalchemy import select
        at_date = _ensure_tz(at_date)
        with self._session_factory() as session:
            stmt = (
                select(ClinicalContextModel)
                .where(
                    ClinicalContextModel.tenant_id == tenant_id,
                    ClinicalContextModel.patient_id == patient_id,
                    ClinicalContextModel.start_date <= at_date,
                )
                .order_by(ClinicalContextModel.start_date.asc())
            )
            rows = session.execute(stmt).scalars().all()
            result = []
            for r in rows:
                ctx = _row_to_context(r)
                if ctx.status not in (
                    ContextStatus.ACTIVE,
                    ContextStatus.SUGGESTED,
                    ContextStatus.PLANNED,
                    ContextStatus.COMPLETED,
                ):
                    continue
                if ctx.end_date is not None and ctx.end_date < at_date:
                    continue
                result.append(ctx)
            return result

    def co_occurred(
        self,
        tenant_id: str,
        patient_id: str,
        date_a: datetime,
        date_b: datetime,
    ) -> List[Tuple[ClinicalContext, ClinicalContext]]:
        a_active = self.active_at(tenant_id, patient_id, date_a)
        b_active = self.active_at(tenant_id, patient_id, date_b)
        pairs: List[Tuple[ClinicalContext, ClinicalContext]] = []
        for a in a_active:
            for b in b_active:
                if a.context_id == b.context_id:
                    continue
                pairs.append((a, b))
        return pairs

    def influenced_outcome(
        self,
        tenant_id: str,
        outcome_id: str,
    ) -> List[ClinicalContext]:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = select(ClinicalContextModel).where(
                ClinicalContextModel.tenant_id == tenant_id,
            )
            rows = session.execute(stmt).scalars().all()
            return [
                _row_to_context(r) for r in rows
                if outcome_id in (r.linked_outcome_ids_json or [])
            ]

    def preceded_improvement(
        self,
        tenant_id: str,
        patient_id: str,
        window_days: int = 30,
    ) -> List[ClinicalContext]:
        """Contextos cujo end_date cai nos últimos `window_days` dias
        relativamente a um OUTCOME_IMPROVEMENT do paciente.

        Para implementação production-grade precisa do Event Store acoplado;
        aqui delegamos ao ClinicalEventStore se injetado, senão retornamos [].
        """
        # Por ora, sem Event Store acoplado, retornamos contextos fechados
        # nos últimos window_days. O componente de evento é responsabilidade
        # do módulo de Timeline (futuro acoplamento).
        from datetime import timedelta
        from sqlalchemy import select

        now = _utcnow()
        lower = now - timedelta(days=window_days)
        with self._session_factory() as session:
            stmt = (
                select(ClinicalContextModel)
                .where(
                    ClinicalContextModel.tenant_id == tenant_id,
                    ClinicalContextModel.patient_id == patient_id,
                    ClinicalContextModel.status.in_([
                        ContextStatus.COMPLETED.value,
                        ContextStatus.ARCHIVED.value,
                    ]),
                    ClinicalContextModel.end_date.isnot(None),
                    ClinicalContextModel.end_date >= lower,
                )
            )
            rows = session.execute(stmt).scalars().all()
            return [_row_to_context(r) for r in rows]

    def active_during(
        self,
        tenant_id: str,
        intervention_id: str,
    ) -> List[ClinicalContext]:
        """Análogo à InMemory. Sem Event Store, retorna []."""
        return []


# ═══════════════════════════════════════════════════════════════════════
# Repository (write-side)
# ═══════════════════════════════════════════════════════════════════════


class REDACTED:
    """Repository para persistência/recuperação de ClinicalContext.

    Write-side puro. Não emite eventos — emissão é responsabilidade
    do ClinicalContextService que delega ao EventPublisher.
    """

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    # ─── Write ────────────────────────────────────────────────────

    def upsert(self, ctx: ClinicalContext) -> str:
        """Insere ou atualiza um ClinicalContext. Retorna context_id."""
        with self._session_factory() as session:
            row = session.get(ClinicalContextModel, ctx.context_id)
            if row is None:
                session.add(_context_to_row(ctx))
            else:
                # Atualiza todos os campos
                fresh = _context_to_row(ctx)
                # Mantém audit mixin
                fresh.created_by = row.created_by
                fresh.created_at = row.created_at
                for col in (
                    "tenant_id", "patient_id", "context_type", "status", "origin",
                    "title", "description", "reason", "observations_json",
                    "start_date", "end_date", "confidence_score",
                    "source_event_ids_json", "linked_event_ids_json",
                    "linked_diagnosis_ids_json", "linked_phenotype_ids_json",
                    "linked_intervention_ids_json", "linked_outcome_ids_json",
                    "linked_assessment_ids_json", "professionals_json",
                    "confirmed_by", "confirmed_at", "rejected_by", "rejected_at",
                    "suggestion_id", "explanation_id", "updated_at",
                    "aggregate_version",
                ):
                    setattr(row, col, getattr(fresh, col))
            session.commit()
            return ctx.context_id

    def delete(self, tenant_id: str, context_id: str) -> bool:
        with self._session_factory() as session:
            row = session.get(ClinicalContextModel, context_id)
            if row is None or row.tenant_id != tenant_id:
                return False
            session.delete(row)
            session.commit()
            return True

    # ─── Read ─────────────────────────────────────────────────────

    def get(self, tenant_id: str, context_id: str) -> Optional[ClinicalContext]:
        with self._session_factory() as session:
            row = session.get(ClinicalContextModel, context_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            return _row_to_context(row)

    def list_for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        status: Optional[ContextStatus] = None,
        context_type: Optional[ContextType] = None,
        origin: Optional[ContextOrigin] = None,
    ) -> List[ClinicalContext]:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = (
                select(ClinicalContextModel)
                .where(
                    ClinicalContextModel.tenant_id == tenant_id,
                    ClinicalContextModel.patient_id == patient_id,
                )
                .order_by(ClinicalContextModel.start_date.asc())
            )
            if status is not None:
                stmt = stmt.where(ClinicalContextModel.status == status.value)
            if context_type is not None:
                stmt = stmt.where(ClinicalContextModel.context_type == context_type.value)
            if origin is not None:
                stmt = stmt.where(ClinicalContextModel.origin == origin.value)
            rows = session.execute(stmt).scalars().all()
            return [_row_to_context(r) for r in rows]

    def list_suggested_for_confirmation(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ClinicalContext]:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = (
                select(ClinicalContextModel)
                .where(
                    ClinicalContextModel.tenant_id == tenant_id,
                    ClinicalContextModel.status == ContextStatus.SUGGESTED.value,
                )
                .order_by(ClinicalContextModel.created_at.asc())
                .limit(limit)
            )
            if patient_id is not None:
                stmt = stmt.where(ClinicalContextModel.patient_id == patient_id)
            rows = session.execute(stmt).scalars().all()
            return [_row_to_context(r) for r in rows]

    # ─── Idempotência ─────────────────────────────────────────────

    def mark_rule_evaluation_processed(
        self,
        tenant_id: str,
        patient_id: str,
        rule_id: str,
        event_id: str,
        suggestion_id: str,
        context_id: Optional[str] = None,
    ) -> bool:
        """Registra (tenant, patient, rule, event) como processado.

        Retorna True se inseriu pela primeira vez; False se já existia.
        Idempotência via UniqueConstraint.
        """
        from sqlalchemy.exc import IntegrityError
        with self._session_factory() as session:
            row = ProcessedRuleEvaluationModel(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                patient_id=patient_id,
                rule_id=rule_id,
                event_id=event_id,
                suggestion_id=suggestion_id,
                context_id=context_id,
                processed_at=_now(),
            )
            session.add(row)
            try:
                session.commit()
                return True
            except IntegrityError:
                session.rollback()
                return False

    def was_rule_evaluation_processed(
        self,
        tenant_id: str,
        patient_id: str,
        rule_id: str,
        event_id: str,
    ) -> bool:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = select(ProcessedRuleEvaluationModel).where(
                ProcessedRuleEvaluationModel.tenant_id == tenant_id,
                ProcessedRuleEvaluationModel.patient_id == patient_id,
                ProcessedRuleEvaluationModel.rule_id == rule_id,
                ProcessedRuleEvaluationModel.event_id == event_id,
            )
            row = session.execute(stmt).scalars().first()
            return row is not None


# ═══════════════════════════════════════════════════════════════════════
# Relationship Repository
# ═══════════════════════════════════════════════════════════════════════


class REDACTED:
    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def upsert(self, rel: ContextRelationship) -> str:
        with self._session_factory() as session:
            existing = session.get(ContextRelationshipModel, rel.relationship_id)
            if existing is None:
                row = ContextRelationshipModel(
                    relationship_id=rel.relationship_id,
                    tenant_id=rel.tenant_id,
                    source_context_id=rel.source_context_id,
                    target_context_id=rel.target_context_id,
                    relationship_type=rel.relationship_type.value,
                    confidence=rel.confidence,
                    evidence_event_ids_json=list(rel.evidence_event_ids),
                    created_at=rel.created_at,
                    created_by=rel.created_by,
                )
                session.add(row)
            else:
                existing.relationship_type = rel.relationship_type.value
                existing.confidence = rel.confidence
                existing.evidence_event_ids_json = list(rel.evidence_event_ids)
            session.commit()
            return rel.relationship_id

    def get(self, tenant_id: str, relationship_id: str) -> Optional[ContextRelationship]:
        with self._session_factory() as session:
            row = session.get(ContextRelationshipModel, relationship_id)
            if row is None or row.tenant_id != tenant_id:
                return None
            return _row_to_relationship(row)

    def list_for_context(
        self,
        tenant_id: str,
        context_id: str,
    ) -> List[ContextRelationship]:
        from sqlalchemy import or_, select
        with self._session_factory() as session:
            stmt = select(ContextRelationshipModel).where(
                ContextRelationshipModel.tenant_id == tenant_id,
                or_(
                    ContextRelationshipModel.source_context_id == context_id,
                    ContextRelationshipModel.target_context_id == context_id,
                ),
            )
            rows = session.execute(stmt).scalars().all()
            return [_row_to_relationship(r) for r in rows]

    def delete(self, tenant_id: str, relationship_id: str) -> bool:
        with self._session_factory() as session:
            row = session.get(ContextRelationshipModel, relationship_id)
            if row is None or row.tenant_id != tenant_id:
                return False
            session.delete(row)
            session.commit()
            return True

    def list_relationship_types(
        self,
        tenant_id: str,
        type_filter: Optional[RelationshipType] = None,
        limit: int = 1000,
    ) -> List[ContextRelationship]:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = (
                select(ContextRelationshipModel)
                .where(ContextRelationshipModel.tenant_id == tenant_id)
                .limit(limit)
            )
            if type_filter is not None:
                stmt = stmt.where(
                    ContextRelationshipModel.relationship_type == type_filter.value
                )
            rows = session.execute(stmt).scalars().all()
            return [_row_to_relationship(r) for r in rows]
