"""
SQLKnowledgeRepository — Sprint 4.5 W1.3 (RC1 Gate 1).

Implementação SQLAlchemy 2.0 do contrato ``KnowledgeRepository`` ABC
(tenant-bound, session-bound, commit-free).

Princípios:

    1. **Session-bound, commit-free.**
       O repositório recebe uma ``Session`` no construtor e NUNCA
       chama ``session.commit()`` nem ``session.rollback()``.
       Transações são responsabilidade do caller
       (``knowledge_composition`` context manager — Sprint 4.5 W2.1).

    2. **Tenant-bound.**
       Herda ``_assert_same_tenant`` do ABC. Cross-tenant access
       levanta ``PermissionError`` antes de qualquer I/O.

    3. **Composite PKs (tenant_id, ...) — arquitetura.**
       Cross-tenant queries IMPOSSÍVEIS via estrutura da chave.

    4. **Mappers lossless.**
       Toda serialização via ``infrastructure/mappers.py``.
       ``to_canonical_dict`` é round-trip byte-exact.

    5. **Sem dependência circular.**
       Modelos SQL são definidos neste módulo e referenciados via
       ``araos.platform.tenant.models.Base`` para evitar criar
       tabelas órfãs no metadata global.

ORM Models definidos aqui:

    - ClinicalGeneModel             → clinical_genes
    - ClinicalGenomeModel           → clinical_genomes
    - KnowledgeCorrelationModel     → knowledge_correlations
    - KnowledgeHypothesisModel      → knowledge_hypotheses
    - KnowledgeCohortModel          → knowledge_cohorts
    - KnowledgeResearchSessionModel → knowledge_research_sessions
    - KnowledgeGraphModel           → knowledge_graphs

Migration Alembic correspondente:

    migrations/versions/REDACTED.py

Compatibilidade:

    - SQLAlchemy 2.0+ declarativo.
    - PostgreSQL (produção) e SQLite (testes).
    - Sem Flask-SQLAlchemy; aceita qualquer session_factory callable.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, List

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from araos.platform.tenant.models import AuditFieldsMixin, Base

from ...genome.domain.aggregate import ClinicalGene
from . import mappers as _mappers
from .in_memory import InMemoryKnowledgeRepository
from .repository import KnowledgeRepository


# ============================================================================
# Helpers
# ============================================================================


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_tz_aware(dt: datetime | None) -> datetime | None:
    """SQLite devolve naive datetime; PostgreSQL devolve aware. Normaliza."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ============================================================================
# ORM Models
# ============================================================================


class ClinicalGeneModel(AuditFieldsMixin, Base):
    """Materialização persistente de ClinicalGene (Sprint 4.4 + 4.5)."""

    __tablename__ = "clinical_genes"

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    gene_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    trajectory_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    history_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sql_cgenes_tenant_state_hash", "tenant_id", "state_hash"),
        Index("ix_sql_cgenes_tenant_patient", "tenant_id", "patient_id"),
    )


class ClinicalGenomeModel(AuditFieldsMixin, Base):
    """Materialização persistente de ClinicalGenome."""

    __tablename__ = "clinical_genomes"

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    genome_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_label: Mapped[str] = mapped_column(String(32), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    graph_snapshot_id: Mapped[str | None] = mapped_column(String(96), nullable=True)
    genes_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    correlations_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    hypotheses_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sql_cgenomes_tenant_state_hash", "tenant_id", "state_hash"),
        Index("ix_sql_cgenomes_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_sql_cgenomes_tenant_built_at", "tenant_id", "built_at"),
        # Composite covering index for list_genomes ORDER BY
        # (patient_id ASC, window_start ASC, window_end ASC, genome_id ASC).
        Index(
            "REDACTED",
            "tenant_id",
            "patient_id",
            "window_start",
            "window_end",
        ),
    )


class KnowledgeCorrelationModel(AuditFieldsMixin, Base):
    """Materialização persistente de CorrelationResult."""

    __tablename__ = "knowledge_correlations"

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    gene_x_id: Mapped[str] = mapped_column(String(96), nullable=False)
    gene_y_id: Mapped[str] = mapped_column(String(96), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    coefficient: Mapped[float] = mapped_column(Float, nullable=False)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sql_kcorr_tenant_state_hash", "tenant_id", "state_hash"),
        Index("ix_sql_kcorr_tenant_patient", "tenant_id", "patient_id"),
        # Composite covering index for list_correlations ORDER BY
        # (patient_id ASC, correlation_id ASC).
        Index(
            "ix_sql_kcorr_tenant_patient_corr",
            "tenant_id",
            "patient_id",
            "correlation_id",
        ),
    )


class KnowledgeHypothesisModel(AuditFieldsMixin, Base):
    """Materialização persistente de ClinicalHypothesis.

    Nota: hypothesis_id é tenant-namespaced (task #197 — RC1 pre-requisito).
    """

    __tablename__ = "knowledge_hypotheses"

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    hypothesis_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(96), nullable=False)
    claim: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    correlations_used_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sql_khyp_tenant_state_hash", "tenant_id", "state_hash"),
        Index("ix_sql_khyp_tenant_patient", "tenant_id", "patient_id"),
        # Composite covering index for list_hypotheses ORDER BY
        # (patient_id ASC, hypothesis_id ASC).
        Index(
            "ix_sql_khyp_tenant_patient_hyp",
            "tenant_id",
            "patient_id",
            "hypothesis_id",
        ),
    )


class KnowledgeCohortModel(AuditFieldsMixin, Base):
    """Materialização persistente de Cohort."""

    __tablename__ = "knowledge_cohorts"

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cohort_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    criteria_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    matched_patient_ids_json: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sql_kcohort_tenant_state_hash", "tenant_id", "state_hash"),
        Index("ix_sql_kcohort_tenant_built_at", "tenant_id", "built_at"),
    )


class KnowledgeResearchSessionModel(AuditFieldsMixin, Base):
    """Materialização persistente de ResearchSession.

    ``result_json`` é TEXT — preserva canonical JSON byte-exact.
    """

    __tablename__ = "knowledge_research_sessions"

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    query_id: Mapped[str] = mapped_column(String(96), nullable=False)
    cohort_id: Mapped[str] = mapped_column(String(96), nullable=False)
    analysis_type: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    reproducible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    explanation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sql_krsess_tenant_state_hash", "tenant_id", "state_hash"),
        Index("ix_sql_krsess_tenant_cohort", "tenant_id", "cohort_id"),
    )


class KnowledgeGraphModel(AuditFieldsMixin, Base):
    """Materialização persistente de KnowledgeGraph (ADR-0008 Opção A — JSON blob)."""

    __tablename__ = "knowledge_graphs"

    tenant_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    graph_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), nullable=False)
    state_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    graph_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    built_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_sql_kgraphs_tenant_state_hash", "tenant_id", "state_hash"),
        Index("ix_sql_kgraphs_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_sql_kgraphs_tenant_built_at", "tenant_id", "built_at"),
        # Composite covering index for list_graphs ORDER BY
        # (patient_id ASC, graph_id ASC).
        Index(
            "REDACTED",
            "tenant_id",
            "patient_id",
            "graph_id",
        ),
    )


# ============================================================================
# Row → Domain conversions
# ============================================================================


def _row_to_gene(row: ClinicalGeneModel) -> ClinicalGene:
    """Reconstrói ClinicalGene a partir da row.

    Usa o mapper domain para garantir lossless. ClinicalGene não tem
    ``tenant_id`` explícito no payload JSON — derivamos do row.
    Converte datetime para ISO string antes de passar ao mapper
    (formato esperado pelos ``_from_dict`` helpers).
    """
    registered = _ensure_tz_aware(row.registered_at)
    updated = _ensure_tz_aware(row.updated_at)
    payload = {
        "tenant_id": row.tenant_id,
        "patient_id": row.patient_id,
        "gene_id": row.gene_id,
        "version": row.metadata_json.get("version", "1.0.0"),
        "status": row.metadata_json.get("status", "active"),
        "created_at": registered.isoformat() if registered else None,
        "updated_at": updated.isoformat() if updated else (registered.isoformat() if registered else None),
        "trajectory": row.trajectory_json,
        "history": row.history_json,
        "metadata": row.metadata_json.get("records", ()),
        "evidence": row.metadata_json.get("evidence", ()),
        "hypotheses": row.metadata_json.get("hypotheses", ()),
        "relationships": row.metadata_json.get("relationships", ()),
        "context": row.metadata_json.get("context", ()),
        "snapshots": row.metadata_json.get("snapshots", ()),
        "snapshot_policy": row.metadata_json.get("snapshot_policy", "never"),
        "last_event_id": row.metadata_json.get("last_event_id"),
        "last_sequence": row.metadata_json.get("last_sequence", -1),
    }
    return _mappers.clinical_gene_from_dict(payload)


# ============================================================================
# SQLKnowledgeRepository — implementa ABC
# ============================================================================


class SQLKnowledgeRepository(KnowledgeRepository):
    """Repository SQL session-bound.

    SEMPRE bound a um tenant. NÃO chama commit/rollback. Transações
    são responsabilidade do context manager ``knowledge_composition``
    (Sprint 4.5 W2.1).

    Args:
        session: SQLAlchemy Session ativa (caller controla transação).
        tenant_id: identificador do tenant (organização).
    """

    def __init__(self, session: Session, tenant_id: str) -> None:
        super().__init__(tenant_id)
        self._session = session

    # REDACTED
    # Genes
    # REDACTED

    def save_genes(
        self, patient_id: str, genes: Iterable[ClinicalGene]
    ) -> None:
        genes_tuple = tuple(genes)
        for gene in genes_tuple:
            self._assert_same_tenant(gene.tenant_id, "ClinicalGene")
            if gene.patient_id != patient_id:
                raise ValueError(
                    f"ClinicalGene.patient_id={gene.patient_id!r} "
                    f"diverge de save_genes(patient_id={patient_id!r})"
                )
        # Wipe anterior (single-genome-per-patient semantic).
        # NOTA: sem flush() intermediário — o flush() ao final do save
        # garante atomicidade do conjunto DELETE + INSERT em uma única
        # round-trip ao DB. Removido na Foundation Freeze (Gate 1.5).
        existing = (
            self._session.query(ClinicalGeneModel)
            .filter(
                ClinicalGeneModel.tenant_id == self._tenant_id,
                ClinicalGeneModel.patient_id == patient_id,
            )
            .all()
        )
        for row in existing:
            self._session.delete(row)
        for gene in genes_tuple:
            gene_dict = _mappers.clinical_gene_to_dict(gene)
            row = ClinicalGeneModel(
                tenant_id=self._tenant_id,
                patient_id=patient_id,
                gene_id=gene.gene_id,
                state_hash=gene.state_hash if hasattr(gene, "state_hash") else "",
                trajectory_json=list(gene_dict.get("trajectory") or []),
                history_json=list(gene_dict.get("history") or []),
                metadata_json={
                    "version": gene.version,
                    "status": gene.status,
                    "records": list(gene_dict.get("metadata") or ()),
                    "evidence": list(gene_dict.get("evidence") or ()),
                    "hypotheses": list(gene_dict.get("hypotheses") or ()),
                    "relationships": list(gene_dict.get("relationships") or ()),
                    "context": list(gene_dict.get("context") or ()),
                    "snapshots": list(gene_dict.get("snapshots") or ()),
                    "snapshot_policy": gene_dict.get("snapshot_policy", "never"),
                    "last_event_id": gene_dict.get("last_event_id"),
                    "last_sequence": gene_dict.get("last_sequence", -1),
                },
                registered_at=gene.created_at,
                created_at=gene.created_at,
            )
            self._session.add(row)
        self._session.flush()

    def load_genes(self, patient_id: str) -> tuple[ClinicalGene, ...]:
        rows = (
            self._session.query(ClinicalGeneModel)
            .filter(
                ClinicalGeneModel.tenant_id == self._tenant_id,
                ClinicalGeneModel.patient_id == patient_id,
            )
            .order_by(ClinicalGeneModel.gene_id.asc())
            .all()
        )
        return tuple(_row_to_gene(r) for r in rows)

    def list_patient_ids(self) -> tuple[str, ...]:
        rows = (
            self._session.query(ClinicalGeneModel.patient_id)
            .filter(ClinicalGeneModel.tenant_id == self._tenant_id)
            .distinct()
            .order_by(ClinicalGeneModel.patient_id.asc())
            .all()
        )
        return tuple(r[0] for r in rows)

    # REDACTED
    # Genomes
    # REDACTED

    def save_genome(self, genome) -> None:  # type: ignore[no-untyped-def]
        from ..domain.clinical_genome import ClinicalGenome

        if not isinstance(genome, ClinicalGenome):
            raise TypeError(f"Expected ClinicalGenome, got {type(genome).__name__}")
        self._assert_same_tenant(genome.tenant_id, "ClinicalGenome")
        existing = self._session.get(
            ClinicalGenomeModel, (self._tenant_id, genome.genome_id)
        )
        genes_json = [
            _mappers.clinical_gene_to_dict(g) for g in genome.genes
        ]
        correlations_json = [
            _mappers.correlation_result_to_dict(c)
            for c in genome.correlation_results
        ]
        hypotheses_json = [
            _mappers.clinical_hypothesis_to_dict(h)
            for h in genome.hypotheses
        ]
        if existing is None:
            row = ClinicalGenomeModel(
                tenant_id=self._tenant_id,
                genome_id=genome.genome_id,
                patient_id=genome.patient_id,
                window_start=genome.window.start,
                window_end=genome.window.end,
                window_label=genome.window.label or "",
                state_hash=genome.state_hash,
                built_at=genome.built_at,
                graph_snapshot_id=genome.graph_snapshot_id,
                genes_json=genes_json,
                correlations_json=correlations_json,
                hypotheses_json=hypotheses_json,
                created_at=_utcnow(),
            )
            self._session.add(row)
        else:
            existing.patient_id = genome.patient_id
            existing.window_start = genome.window.start
            existing.window_end = genome.window.end
            existing.window_label = genome.window.label or ""
            existing.state_hash = genome.state_hash
            existing.built_at = genome.built_at
            existing.graph_snapshot_id = genome.graph_snapshot_id
            existing.genes_json = genes_json
            existing.correlations_json = correlations_json
            existing.hypotheses_json = hypotheses_json
            existing.updated_at = _utcnow()
        self._session.flush()

    def load_genome(self, genome_id: str):
        from ..domain.clinical_genome import ClinicalGenome

        row = self._session.get(
            ClinicalGenomeModel, (self._tenant_id, genome_id)
        )
        if row is None:
            return None
        ws = _ensure_tz_aware(row.window_start).isoformat()
        we = _ensure_tz_aware(row.window_end).isoformat()
        return ClinicalGenome(
            genome_id=row.genome_id,
            tenant_id=row.tenant_id,
            patient_id=row.patient_id,
            window=_mappers.time_window_from_dict(
                {
                    "start": ws,
                    "end": we,
                    "label": row.window_label,
                }
            ),
            genes=tuple(
                _mappers.clinical_gene_from_dict(g) for g in (row.genes_json or [])
            ),
            correlation_results=tuple(
                _mappers.correlation_result_from_dict(c)
                for c in (row.correlations_json or [])
            ),
            hypotheses=tuple(
                _mappers.clinical_hypothesis_from_dict(h)
                for h in (row.hypotheses_json or [])
            ),
            graph_snapshot_id=row.graph_snapshot_id,
            built_at=_ensure_tz_aware(row.built_at),
            state_hash=row.state_hash,
        )

    def list_genomes(self):
        from ..domain.clinical_genome import ClinicalGenome

        rows = (
            self._session.query(ClinicalGenomeModel)
            .filter(ClinicalGenomeModel.tenant_id == self._tenant_id)
            .order_by(
                ClinicalGenomeModel.patient_id.asc(),
                ClinicalGenomeModel.window_start.asc(),
                ClinicalGenomeModel.window_end.asc(),
                ClinicalGenomeModel.genome_id.asc(),
            )
            .all()
        )
        result: List[Any] = []
        for row in rows:
            ws = _ensure_tz_aware(row.window_start).isoformat()
            we = _ensure_tz_aware(row.window_end).isoformat()
            result.append(
                ClinicalGenome(
                    genome_id=row.genome_id,
                    tenant_id=row.tenant_id,
                    patient_id=row.patient_id,
                    window=_mappers.time_window_from_dict(
                        {
                            "start": ws,
                            "end": we,
                            "label": row.window_label,
                        }
                    ),
                    genes=tuple(
                        _mappers.clinical_gene_from_dict(g)
                        for g in (row.genes_json or [])
                    ),
                    correlation_results=tuple(
                        _mappers.correlation_result_from_dict(c)
                        for c in (row.correlations_json or [])
                    ),
                    hypotheses=tuple(
                        _mappers.clinical_hypothesis_from_dict(h)
                        for h in (row.hypotheses_json or [])
                    ),
                    graph_snapshot_id=row.graph_snapshot_id,
                    built_at=_ensure_tz_aware(row.built_at),
                    state_hash=row.state_hash,
                )
            )
        return tuple(result)

    # REDACTED
    # Correlations
    # REDACTED

    def save_correlation(self, correlation) -> None:  # type: ignore[no-untyped-def]
        from ..domain.correlation import CorrelationResult

        if not isinstance(correlation, CorrelationResult):
            raise TypeError(
                f"Expected CorrelationResult, got {type(correlation).__name__}"
            )
        payload = _mappers.correlation_result_to_dict(correlation)
        existing = self._session.get(
            KnowledgeCorrelationModel,
            (self._tenant_id, correlation.correlation_id),
        )
        if existing is None:
            row = KnowledgeCorrelationModel(
                tenant_id=self._tenant_id,
                correlation_id=correlation.correlation_id,
                patient_id=getattr(correlation, "patient_id", "") or "",
                method=correlation.method.value,
                gene_x_id=correlation.gene_x_id,
                gene_y_id=correlation.gene_y_id,
                window_start=correlation.window.start,
                window_end=correlation.window.end,
                coefficient=correlation.coefficient,
                p_value=correlation.p_value,
                state_hash=correlation.explanation.state_hash if hasattr(correlation.explanation, "state_hash") else "",
                payload_json=payload,
                created_at=_utcnow(),
            )
            self._session.add(row)
        else:
            existing.patient_id = getattr(correlation, "patient_id", "") or ""
            existing.method = correlation.method.value
            existing.gene_x_id = correlation.gene_x_id
            existing.gene_y_id = correlation.gene_y_id
            existing.window_start = correlation.window.start
            existing.window_end = correlation.window.end
            existing.coefficient = correlation.coefficient
            existing.p_value = correlation.p_value
            existing.payload_json = payload
            existing.updated_at = _utcnow()
        self._session.flush()

    def load_correlation(self, correlation_id: str):
        from ..domain.correlation import CorrelationResult

        row = self._session.get(
            KnowledgeCorrelationModel,
            (self._tenant_id, correlation_id),
        )
        if row is None:
            return None
        return _mappers.correlation_result_from_dict(row.payload_json)

    def list_correlations(self):
        from ..domain.correlation import CorrelationResult

        rows = (
            self._session.query(KnowledgeCorrelationModel)
            .filter(KnowledgeCorrelationModel.tenant_id == self._tenant_id)
            .order_by(
                KnowledgeCorrelationModel.patient_id.asc(),
                KnowledgeCorrelationModel.correlation_id.asc(),
            )
            .all()
        )
        return tuple(
            _mappers.correlation_result_from_dict(r.payload_json) for r in rows
        )

    # REDACTED
    # Hypotheses
    # REDACTED

    def save_hypothesis(self, hypothesis) -> None:  # type: ignore[no-untyped-def]
        from ..domain.hypothesis import ClinicalHypothesis

        if not isinstance(hypothesis, ClinicalHypothesis):
            raise TypeError(
                f"Expected ClinicalHypothesis, got {type(hypothesis).__name__}"
            )
        payload = _mappers.clinical_hypothesis_to_dict(hypothesis)
        existing = self._session.get(
            KnowledgeHypothesisModel,
            (self._tenant_id, hypothesis.hypothesis_id),
        )
        if existing is None:
            row = KnowledgeHypothesisModel(
                tenant_id=self._tenant_id,
                hypothesis_id=hypothesis.hypothesis_id,
                patient_id=hypothesis.patient_id,
                rule_id=hypothesis.rule_id,
                claim=hypothesis.claim,
                confidence=hypothesis.confidence,
                status=hypothesis.status.value,
                correlations_used_json=list(hypothesis.correlations_used),
                state_hash=hypothesis.explanation.state_hash if hasattr(hypothesis.explanation, "state_hash") else "",
                payload_json=payload,
                created_at=_utcnow(),
            )
            self._session.add(row)
        else:
            existing.patient_id = hypothesis.patient_id
            existing.rule_id = hypothesis.rule_id
            existing.claim = hypothesis.claim
            existing.confidence = hypothesis.confidence
            existing.status = hypothesis.status.value
            existing.correlations_used_json = list(hypothesis.correlations_used)
            existing.payload_json = payload
            existing.updated_at = _utcnow()
        self._session.flush()

    def load_hypothesis(self, hypothesis_id: str):
        from ..domain.hypothesis import ClinicalHypothesis

        row = self._session.get(
            KnowledgeHypothesisModel,
            (self._tenant_id, hypothesis_id),
        )
        if row is None:
            return None
        return _mappers.clinical_hypothesis_from_dict(row.payload_json)

    def list_hypotheses(self):
        from ..domain.hypothesis import ClinicalHypothesis

        rows = (
            self._session.query(KnowledgeHypothesisModel)
            .filter(KnowledgeHypothesisModel.tenant_id == self._tenant_id)
            .order_by(
                KnowledgeHypothesisModel.patient_id.asc(),
                KnowledgeHypothesisModel.hypothesis_id.asc(),
            )
            .all()
        )
        return tuple(
            _mappers.clinical_hypothesis_from_dict(r.payload_json) for r in rows
        )

    # REDACTED
    # Cohorts
    # REDACTED

    def save_cohort(self, cohort) -> None:  # type: ignore[no-untyped-def]
        from ..domain.cohort import Cohort

        if not isinstance(cohort, Cohort):
            raise TypeError(f"Expected Cohort, got {type(cohort).__name__}")
        self._assert_same_tenant(cohort.tenant_id, "Cohort")
        existing = self._session.get(
            KnowledgeCohortModel,
            (self._tenant_id, cohort.cohort_id),
        )
        criteria_json = [
            _mappers.criterion_to_dict(c) for c in cohort.criteria
        ]
        matched = list(cohort.matched_patient_ids)
        if existing is None:
            row = KnowledgeCohortModel(
                tenant_id=self._tenant_id,
                cohort_id=cohort.cohort_id,
                name=cohort.name,
                criteria_json=criteria_json,
                matched_patient_ids_json=matched,
                count=len(matched),
                state_hash=cohort.state_hash,
                built_at=cohort.built_at,
                created_at=_utcnow(),
            )
            self._session.add(row)
        else:
            existing.name = cohort.name
            existing.criteria_json = criteria_json
            existing.matched_patient_ids_json = matched
            existing.count = len(matched)
            existing.state_hash = cohort.state_hash
            existing.built_at = cohort.built_at
            existing.updated_at = _utcnow()
        self._session.flush()

    def load_cohort(self, cohort_id: str):
        from ..domain.cohort import Cohort

        row = self._session.get(
            KnowledgeCohortModel,
            (self._tenant_id, cohort_id),
        )
        if row is None:
            return None
        return Cohort(
            cohort_id=row.cohort_id,
            tenant_id=row.tenant_id,
            name=row.name,
            criteria=tuple(
                _mappers.criterion_from_dict(c) for c in (row.criteria_json or [])
            ),
            matched_patient_ids=tuple(row.matched_patient_ids_json or ()),
            built_at=_ensure_tz_aware(row.built_at),
            state_hash=row.state_hash,
        )

    def list_cohorts(self):
        from ..domain.cohort import Cohort

        rows = (
            self._session.query(KnowledgeCohortModel)
            .filter(KnowledgeCohortModel.tenant_id == self._tenant_id)
            .order_by(
                KnowledgeCohortModel.built_at.asc(),
                KnowledgeCohortModel.cohort_id.asc(),
            )
            .all()
        )
        result: List[Any] = []
        for row in rows:
            result.append(
                Cohort(
                    cohort_id=row.cohort_id,
                    tenant_id=row.tenant_id,
                    name=row.name,
                    criteria=tuple(
                        _mappers.criterion_from_dict(c)
                        for c in (row.criteria_json or [])
                    ),
                    matched_patient_ids=tuple(row.matched_patient_ids_json or ()),
                    built_at=_ensure_tz_aware(row.built_at),
                    state_hash=row.state_hash,
                )
            )
        return tuple(result)

    # REDACTED
    # Research sessions
    # REDACTED

    def save_session(self, session) -> None:  # type: ignore[no-untyped-def]
        from ..domain.research import ResearchSession

        if not isinstance(session, ResearchSession):
            raise TypeError(
                f"Expected ResearchSession, got {type(session).__name__}"
            )
        existing = self._session.get(
            KnowledgeResearchSessionModel,
            (self._tenant_id, session.session_id),
        )
        explanation_payload = _mappers.inference_explanation_to_dict(
            session.explanation
        )
        if existing is None:
            row = KnowledgeResearchSessionModel(
                tenant_id=self._tenant_id,
                session_id=session.session_id,
                query_id=session.query.query_id,
                cohort_id=session.query.cohort_id,
                analysis_type=session.query.analysis_type.value,
                version=session.version,
                started_at=session.started_at,
                completed_at=session.completed_at,
                result_json=session.result_json,
                state_hash=session.state_hash,
                reproducible=session.reproducible,
                explanation_json=explanation_payload,
                created_at=_utcnow(),
            )
            self._session.add(row)
        else:
            existing.query_id = session.query.query_id
            existing.cohort_id = session.query.cohort_id
            existing.analysis_type = session.query.analysis_type.value
            existing.version = session.version
            existing.started_at = session.started_at
            existing.completed_at = session.completed_at
            existing.result_json = session.result_json
            existing.state_hash = session.state_hash
            existing.reproducible = session.reproducible
            existing.explanation_json = explanation_payload
            existing.updated_at = _utcnow()
        self._session.flush()

    def load_session(self, session_id: str):
        from ..domain.research import ResearchSession

        row = self._session.get(
            KnowledgeResearchSessionModel,
            (self._tenant_id, session_id),
        )
        if row is None:
            return None
        explanation = _mappers.inference_explanation_from_dict(row.explanation_json or {})
        return ResearchSession(
            session_id=row.session_id,
            query=_mappers.research_query_from_dict(
                {
                    "query_id": row.query_id,
                    "cohort_id": row.cohort_id,
                    "analysis_type": row.analysis_type,
                    "params": {},
                    "version": row.version,
                    "created_at": row.started_at.isoformat(),
                }
            ),
            version=row.version,
            started_at=_ensure_tz_aware(row.started_at),
            completed_at=_ensure_tz_aware(row.completed_at),
            result_json=row.result_json,
            state_hash=row.state_hash,
            reproducible=row.reproducible,
            explanation=explanation,
        )

    def list_sessions(self):
        from ..domain.research import ResearchSession

        rows = (
            self._session.query(KnowledgeResearchSessionModel)
            .filter(KnowledgeResearchSessionModel.tenant_id == self._tenant_id)
            .order_by(
                KnowledgeResearchSessionModel.started_at.asc(),
                KnowledgeResearchSessionModel.session_id.asc(),
            )
            .all()
        )
        result: List[Any] = []
        for row in rows:
            explanation = _mappers.inference_explanation_from_dict(
                row.explanation_json or {}
            )
            result.append(
                ResearchSession(
                    session_id=row.session_id,
                    query=_mappers.research_query_from_dict(
                        {
                            "query_id": row.query_id,
                            "cohort_id": row.cohort_id,
                            "analysis_type": row.analysis_type,
                            "params": {},
                            "version": row.version,
                            "created_at": row.started_at.isoformat(),
                        }
                    ),
                    version=row.version,
                    started_at=_ensure_tz_aware(row.started_at),
                    completed_at=_ensure_tz_aware(row.completed_at),
                    result_json=row.result_json,
                    state_hash=row.state_hash,
                    reproducible=row.reproducible,
                    explanation=explanation,
                )
            )
        return tuple(result)

    # REDACTED
    # Knowledge graphs
    # REDACTED

    def save_graph(self, graph) -> None:  # type: ignore[no-untyped-def]
        from ..domain.knowledge_graph import KnowledgeGraph

        if not isinstance(graph, KnowledgeGraph):
            raise TypeError(
                f"Expected KnowledgeGraph, got {type(graph).__name__}"
            )
        self._assert_same_tenant(graph.tenant_id, "KnowledgeGraph")
        existing = self._session.get(
            KnowledgeGraphModel,
            (self._tenant_id, graph.graph_id),
        )
        graph_json = _mappers.knowledge_graph_to_dict(graph)
        if existing is None:
            row = KnowledgeGraphModel(
                tenant_id=self._tenant_id,
                graph_id=graph.graph_id,
                patient_id=graph.patient_id,
                state_hash=graph.state_hash,
                graph_json=graph_json,
                built_at=graph.built_at,
                created_at=_utcnow(),
            )
            self._session.add(row)
        else:
            existing.patient_id = graph.patient_id
            existing.state_hash = graph.state_hash
            existing.graph_json = graph_json
            existing.built_at = graph.built_at
            existing.updated_at = _utcnow()
        self._session.flush()

    def load_graph(self, graph_id: str):
        from ..domain.knowledge_graph import KnowledgeGraph

        row = self._session.get(
            KnowledgeGraphModel,
            (self._tenant_id, graph_id),
        )
        if row is None:
            return None
        return _mappers.knowledge_graph_from_dict(row.graph_json)

    def list_graphs(self):
        from ..domain.knowledge_graph import KnowledgeGraph

        rows = (
            self._session.query(KnowledgeGraphModel)
            .filter(KnowledgeGraphModel.tenant_id == self._tenant_id)
            .order_by(
                KnowledgeGraphModel.patient_id.asc(),
                KnowledgeGraphModel.graph_id.asc(),
            )
            .all()
        )
        return tuple(
            _mappers.knowledge_graph_from_dict(r.graph_json) for r in rows
        )

    # REDACTED
    # Convenience: in-memory snapshot (for benchmarking / fallback)
    # REDACTED

    def to_in_memory(self) -> InMemoryKnowledgeRepository:
        """Cria um InMemoryKnowledgeRepository com o mesmo conteúdo.

        Útil para shadow-compare em testes.
        """
        inmem = InMemoryKnowledgeRepository(tenant_id=self._tenant_id)
        for pid in self.list_patient_ids():
            inmem.save_genes(pid, self.load_genes(pid))
        for g in self.list_genomes():
            inmem.save_genome(g)
        for c in self.list_correlations():
            inmem.save_correlation(c)
        for h in self.list_hypotheses():
            inmem.save_hypothesis(h)
        for c in self.list_cohorts():
            inmem.save_cohort(c)
        for s in self.list_sessions():
            inmem.save_session(s)
        for g in self.list_graphs():
            inmem.save_graph(g)
        return inmem
