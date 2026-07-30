"""
SQL persistence para Explainability Core.

Fornece:
    - IntelligenceExplanationModel — SQLAlchemy 2.0 model espelhando
      a tabela `intelligence_explanations` (Sprint 4.1).
    - SqlAlchemyExplanationRegistry — implementação production-ready
      do ExplanationRegistry ABC.

Padrão (Sprint 3.2):
    - AuditFieldsMixin + Base de araos.platform.tenant.models.
    - tenant_id sempre presente + indexado.
    - Idempotência via id (explanation_id único).

NOTA: Sprint 4.1 entrega o model + registry. Eventos derivados
(EXPLANATION_REGISTERED publish via ClinicalEventPublisher) serão
integrados quando Sprint 4.2+ introduzir análise writers.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Float,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from araos.clinical.explainability.domain.explanation import (
    AnalysisType,
    Explanation,
)
from araos.clinical.explainability.registry import ExplanationRegistry
from araos.clinical.timeline.domain.variable import VariableSpec
from araos.clinical.timeline.domain.window import TimeWindow
from araos.platform.tenant.models import AuditFieldsMixin, Base


# ─── ORM Model ────────────────────────────────────────────────────────


class IntelligenceExplanationModel(AuditFieldsMixin, Base):
    """SQL projection de uma Explanation.

    Espelha a tabela `intelligence_explanations` definida na migration
    REDACTED.
    """

    __tablename__ = "intelligence_explanations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)         # explanation_id
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    analysis_id: Mapped[str] = mapped_column(String(64), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(64), nullable=False)
    data_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_window_label: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    variables_json: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    contributing_event_ids_json: Mapped[List[str]] = mapped_column(
        JSON, nullable=False, default=list,
    )
    assumptions_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    limitations_json: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    analyst: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("REDACTED", "tenant_id", "analysis_id"),
        Index("ix_intel_explanations_tenant_type", "tenant_id", "analysis_type"),
        Index("REDACTED", "tenant_id", "created_at"),
        Index("REDACTED", "correlation_id"),
    )


class REDACTED(Base):
    """Tracker de queries pesadas do Timeline (idempotência + auditoria)."""

    __tablename__ = "REDACTED"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    query_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    query_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    source_event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "query_kind", "query_hash", "source_event_id",
            name="uq_intel_query_processed",
        ),
        Index("ix_intel_query_tenant_kind", "tenant_id", "query_kind"),
    )


# ─── Conversion helpers ──────────────────────────────────────────────


def _ensure_tz_aware(dt: datetime) -> datetime:
    """Garante tz-aware (UTC). SQLite devolve naive datetimes mesmo com
    DateTime(timezone=True); isto é uma correção defensiva de leitura."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _row_to_explanation(row: IntelligenceExplanationModel) -> Explanation:
    """Converte uma row SQLAlchemy em value object Explanation."""
    variables: List[VariableSpec] = []
    for v in (row.variables_json or []):
        try:
            variables.append(VariableSpec(
                name=v["name"],
                source=v.get("source", "event_payload"),
                source_event_type=v["source_event_type"],
                value_extractor=v["value_extractor"],
                description=v.get("description"),
                unit=v.get("unit"),
                filter_clause=v.get("filter_clause") or {},
            ))
        except (KeyError, ValueError):
            # Variable spec inválido — pula silenciosamente
            continue

    window = TimeWindow(
        start=_ensure_tz_aware(row.data_window_start),
        end=_ensure_tz_aware(row.data_window_end),
        label=row.data_window_label,
    )

    return Explanation(
        explanation_id=row.id,
        analysis_id=row.analysis_id,
        analysis_type=AnalysisType(row.analysis_type),
        question=row.question,
        answer=row.answer,
        confidence=row.confidence,
        method=row.method,
        data_window=window,
        variables=variables,
        contributing_event_ids=list(row.contributing_event_ids_json or []),
        assumptions=list(row.assumptions_json or []),
        limitations=list(row.limitations_json or []),
        created_at=_ensure_tz_aware(row.created_at),
        analyst=row.analyst,
        tenant_id=row.tenant_id,
        correlation_id=row.correlation_id,
        metadata=dict(row.metadata_json or {}),
    )


def _explanation_to_row(explanation: Explanation) -> IntelligenceExplanationModel:
    """Converte value object Explanation em row SQLAlchemy."""
    return IntelligenceExplanationModel(
        id=explanation.explanation_id,
        tenant_id=explanation.tenant_id,
        analysis_id=explanation.analysis_id,
        analysis_type=explanation.analysis_type.value,
        question=explanation.question,
        answer=explanation.answer,
        confidence=explanation.confidence,
        method=explanation.method,
        data_window_start=explanation.data_window.start,
        data_window_end=explanation.data_window.end,
        data_window_label=explanation.data_window.label,
        variables_json=[v.to_dict() for v in explanation.variables],
        contributing_event_ids_json=list(explanation.contributing_event_ids),
        assumptions_json=list(explanation.assumptions),
        limitations_json=list(explanation.limitations),
        analyst=explanation.analyst,
        correlation_id=explanation.correlation_id,
        metadata_json=dict(explanation.metadata),
        created_at=explanation.created_at,
    )


# ─── SQL Registry impl ───────────────────────────────────────────────


class SqlAlchemyExplanationRegistry(ExplanationRegistry):
    """Registry de explicações persistido em PostgreSQL/SQLite.

    Padrão: cada operação abre uma transação curta. Não há cache em
    memória — Explainability é write-rare, read-often, e freshness é
    crítica (clínico precisa ver explicação atualizada imediatamente).
    """

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def register(self, explanation: Explanation) -> str:
        if not isinstance(explanation, Explanation):
            raise TypeError("explanation must be Explanation instance")
        with self._session_factory() as session:
            row = _explanation_to_row(explanation)
            session.add(row)
            session.commit()
            return explanation.explanation_id

    def get(self, explanation_id: str) -> Optional[Explanation]:
        with self._session_factory() as session:
            row = session.get(IntelligenceExplanationModel, explanation_id)
            if row is None:
                return None
            return _row_to_explanation(row)

    def list_for_analysis(
        self,
        tenant_id: str,
        analysis_id: str,
    ) -> List[Explanation]:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = (
                select(IntelligenceExplanationModel)
                .where(
                    IntelligenceExplanationModel.tenant_id == tenant_id,
                    IntelligenceExplanationModel.analysis_id == analysis_id,
                )
                .order_by(IntelligenceExplanationModel.created_at.asc())
            )
            rows = session.execute(stmt).scalars().all()
            return [_row_to_explanation(r) for r in rows]

    def list_for_event(
        self,
        tenant_id: str,
        event_id: str,
    ) -> List[Explanation]:
        """Lista explicações que citaram este evento como contributing."""
        from sqlalchemy import select
        with self._session_factory() as session:
            # JSON containment query — assume Postgres jsonb or SQLite json1.
            # Para produção, recomenda-se um índice GIN no contributing_event_ids_json.
            stmt = select(IntelligenceExplanationModel).where(
                IntelligenceExplanationModel.tenant_id == tenant_id,
            )
            rows = session.execute(stmt).scalars().all()
            return [
                _row_to_explanation(r) for r in rows
                if event_id in (r.contributing_event_ids_json or [])
            ]

    def list_for_type(
        self,
        tenant_id: str,
        analysis_type: AnalysisType,
        limit: int = 100,
    ) -> List[Explanation]:
        from sqlalchemy import select
        with self._session_factory() as session:
            stmt = (
                select(IntelligenceExplanationModel)
                .where(
                    IntelligenceExplanationModel.tenant_id == tenant_id,
                    IntelligenceExplanationModel.analysis_type == analysis_type.value,
                )
                .order_by(IntelligenceExplanationModel.created_at.desc())
                .limit(limit)
            )
            rows = session.execute(stmt).scalars().all()
            return [_row_to_explanation(r) for r in rows]

    def count(self, tenant_id: str) -> int:
        from sqlalchemy import func, select
        with self._session_factory() as session:
            stmt = select(func.count()).select_from(IntelligenceExplanationModel).where(
                IntelligenceExplanationModel.tenant_id == tenant_id,
            )
            return int(session.execute(stmt).scalar_one())