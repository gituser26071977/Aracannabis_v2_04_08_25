"""
AraOS Clinical Event Engine — SQLAlchemy Model.

Tabela `clinical_events` cross-specialty.

Single source of truth para:
    - Timeline clínica
    - Dashboards
    - IA clínica
    - Relatórios
    - Observatório Sergipano
    - Pesquisa científica

Todas as specialties (Neuro, Cannabis, Fisio, Fono, TO, Psicologia, etc.)
escrevem nesta mesma tabela. `source_module` separa domínios.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    String, DateTime, JSON, Index, ForeignKey, BigInteger, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from araos.platform.tenant.models import (
    AuditFieldsMixin,
    Base,
    generate_uuid,
    now_utc,
)


def _isoformat_utc(dt: Optional[datetime]) -> Optional[str]:
    """
    Serializa datetime para ISO 8601 com timezone UTC explícito.

    Garante formato idêntico independente do banco (PostgreSQL preserva
    tzinfo; SQLite descarta). Sem este helper, hashes de eventos
    re-lidos do banco ficam inconsistentes com hashes da inserção.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


class ClinicalEventModel(Base, AuditFieldsMixin):
    """
    Evento clínico canônico (ADR-0001).

    Campos obrigatórios (mapeados 1:1 com a decisão arquitetural):
        - id (UUID PK)
        - tenant_id (FK araos_organizations)
        - patient_id (FK conceitual, aceita UUIDs AraOS ou IDs legacy)
        - event_type (ref ao catálogo)
        - event_version (schema version do payload)
        - event_datetime (quando aconteceu clinicamente)
        - source_module ('neurodevelopmental', 'cannabis', 'core', ...)
        - payload (JSON específico do evento)
        - metadata (JSON: correlation_id, causation_id, tags)
        - aggregate_type (opcional: 'scale', 'medication', 'diagnosis')
        - aggregate_id (opcional: id do objeto afetado)
        - created_by (ator clínico: médico, fono, etc.)
        - created_by_user (user account que executou)
        - created_at, updated_at, deleted_at (audit + soft delete LGPD)
        - previous_hash, event_hash (SHA-256 chain)

    Toda escrita é append-only. Correções são feitas por appending novo
    evento (ex: SCALE_UPDATED, DIAGNOSIS_REMOVED).
    """

    __tablename__ = "clinical_events"

    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid,
    )

    # Tenant isolation
    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("araos_organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Patient reference (sem FK rígida para suportar UUIDs AraOS + IDs legacy)
    patient_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True,
    )

    # Event identity
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_version: Mapped[str] = mapped_column(
        String(16), nullable=False, default="1.0",
    )
    event_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    source_module: Mapped[str] = mapped_column(String(32), nullable=False)

    # Data
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict,
    )
    # 'event_metadata' para não colidir com SQLAlchemy `Base.metadata`
    event_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict,
    )

    # Aggregate (opcional)
    aggregate_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True,
    )
    aggregate_id: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True,
    )

    # Actor (clínico + sistema distintos)
    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True,
    )
    created_by_user: Mapped[Optional[str]] = mapped_column(
        String(36), nullable=True,
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Hash chain
    previous_hash: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
    )
    event_hash: Mapped[str] = mapped_column(
        String(64), nullable=False,
    )

    # Sequence per-tenant (insertion order, monotonic).
    # Define a ordem canônica da hash chain (independente de event_datetime).
    # Garante integridade da chain mesmo quando múltiplos eventos têm o
    # mesmo event_datetime (ex.: 3 escalas aplicadas na mesma consulta) ou
    # quando SQLite trunca precisão de timestamp.
    sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False,
    )

    __table_args__ = (
        # Queries típicas: "todos os eventos do paciente X ordenados por data"
        Index(
            "REDACTED",
            "tenant_id", "patient_id", "event_datetime",
        ),
        # Filtros por tipo (dashboards, IA)
        Index("ix_clinical_events_event_type", "event_type"),
        # Reconstrução de projeções a partir de aggregate
        Index(
            "ix_clinical_events_aggregate",
            "aggregate_type", "aggregate_id",
        ),
        # ETL do observatório
        Index(
            "ix_clinical_events_source_module",
            "source_module", "event_datetime",
        ),
        # Hot path do hash chain (last_hash por tenant — sequence DESC)
        Index(
            "ix_clinical_events_tenant_sequence",
            "tenant_id", "sequence",
        ),
        # Soft delete queries (LGPD)
        Index(
            "ix_clinical_events_deleted_at",
            "deleted_at",
        ),
        # Unicidade da sequence por tenant (integridade da chain)
        UniqueConstraint(
            "tenant_id", "sequence",
            name="uq_clinical_events_tenant_sequence",
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dict (JSON-safe, formato público).

        IMPORTANTE: datetimes são sempre serializados com timezone UTC
        explícito (`+00:00`) para garantir reprodutibilidade do hash.
        SQLite descarta tzinfo no round-trip — sem este cuidado,
        recomputação do hash falha.
        """
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "event_datetime": _isoformat_utc(self.event_datetime),
            "source_module": self.source_module,
            "payload": self.payload,
            "metadata": self.event_metadata,
            "aggregate_type": self.aggregate_type,
            "aggregate_id": self.aggregate_id,
            "created_by": self.created_by,
            "created_by_user": self.created_by_user,
            "created_at": _isoformat_utc(self.created_at),
            "updated_at": _isoformat_utc(self.updated_at),
            "deleted_at": _isoformat_utc(self.deleted_at),
            "previous_hash": self.previous_hash,
            "event_hash": self.event_hash,
            "sequence": self.sequence,
        }


# ═══════════════════════════════════════════════════════════════════════
# SEQUENCE TRACKER
# ═══════════════════════════════════════════════════════════════════════


class ClinicalEventSequence(Base):
    """
    Contador monotônico per-tenant para eventos clínicos.

    Cada tenant tem no máximo uma linha nesta tabela. `last_sequence`
    é o maior sequence já atribuído a um evento daquele tenant. O
    próximo sequence = `last_sequence + 1`.

    Atualizado atomicamente dentro da transação do `append()`:
        SELECT ... FOR UPDATE  →  bloqueia linha
        UPDATE last_sequence   →  incrementa
        INSERT INTO clinical_events (sequence=last_sequence+1)

    Decisão arquitetural:
        A chain canônica do Event Store é ordenada por sequence
        (insertion order), NÃO por event_datetime (clinical time).
        event_datetime é um atributo do payload — pode ser backdated,
        batch-imported, ou registrado com delay. A sequence é a
        verdade imutável de "quando o sistema tomou conhecimento".

    Multi-tenant isolation:
        PK em `tenant_id` garante que sequences são independentes
        entre tenants. Cascade delete com `araos_organizations`.
    """

    __tablename__ = "clinical_event_sequences"

    tenant_id: Mapped[str] = mapped_column(
        ForeignKey("araos_organizations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    last_sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now_utc,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=now_utc,
    )
