"""
AraOS Neurodevelopmental — SQLAlchemy Persisted Models.

Modelos ORM (camada infrastructure) do módulo NEURODESENVOLVIMENTO.

Convenção greenfield AraOS:
    - Herda de `araos.platform.tenant.models.Base` (Declarative).
    - Herda de `AuditFieldsMixin` para `created_by/updated_by/deleted_by`.
    - `tenant_id: String(36)` FK → `araos_organizations.id` (índice).
    - `created_at`, `updated_at (onupdate)`, `deleted_at` (soft delete).

Sprint 1 entrega apenas a tabela de respostas de escalas (núcleo crítico).
Tabelas adicionais virão nos sprints seguintes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from araos.platform.tenant.models import AuditFieldsMixin, Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _now_utc() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc)


class NeuroScaleResponseModel(AuditFieldsMixin, Base):
    """
    Resposta persistida de uma escala neuropsicológica.

    Uma linha por aplicação. Múltiplas aplicações por paciente são
    permitidas (ex: PHQ-9 baseline, mês 1, mês 3, mês 6). Versões
    diferentes da mesma escala coexistem (campo `scale_version`).

    Tabela: `neuro_scale_responses`
    """

    __tablename__ = "neuro_scale_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)

    # Tenant isolation (FK conceitual — string livre para evitar acoplamento
    # ao schema de organizations que pode evoluir; índice garante performance)
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Paciente (referência lógica — o paciente pode estar em qualquer
    # sistema: legacy `pacientes.id` Integer OU AraOS Patient UUID).
    # Mantemos como String(36) para suportar UUIDs; valores legados
    # Integer são convertidos para string pelo service layer.
    patient_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Identificação da escala
    scale_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    scale_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Respostas brutas (validadas contra ScaleSpec.json_schema no runner)
    raw_responses: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Scores calculados (cache — sempre deriváveis de raw_responses)
    computed_scores: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Interpretação (band, label_pt, color, recommendation, references)
    interpretation: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Metadados extras (idade, observador, contexto, flags de segurança)
    extra_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Controle de aplicação
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, index=True
    )
    applied_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="ui")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="final", index=True)

    # Audit fields (herdados de AuditFieldsMixin)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now_utc, onupdate=_now_utc
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_neuro_scale_resp_patient_scale", "patient_id", "scale_code"),
        Index("ix_neuro_scale_resp_tenant_applied", "tenant_id", "applied_at"),
        Index("ix_neuro_scale_resp_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<NeuroScaleResponseModel id={self.id!r} "
            f"tenant_id={self.tenant_id!r} patient_id={self.patient_id!r} "
            f"scale_code={self.scale_code!r} version={self.scale_version!r} "
            f"status={self.status!r}>"
        )