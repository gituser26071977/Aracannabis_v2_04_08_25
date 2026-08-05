"""
ClinicalGene — Aggregate Root.

Reference Implementation — Sprint 4.3 Phase 2.

Esta é a peça central da Reference Implementation. Orquestra todas as 9
componentes internas (Expression, Trajectory, History, Evidence, Hypotheses,
Relationships, Context, Metadata, Snapshots) e oferece:

- Identidade canônica (tenant_id, patient_id, gene_id) por URN.
- Versionamento SemVer (AS-001 §8).
- Status lifecycle (ACTIVE / ARCHIVED).
- Replay bit-identical a partir dos Domain Events (AS-001 §7.7.1).
- Substituição de Expression (AS-002 §6.5).
- Explicabilidade via ``Expression.why()`` (cross-cutting).
- Snapshots configuráveis (AS-001 §6.4).
- Bitemporalidade com ``state_at()`` e ``known_at()``.

A invariante central (AS-001 §7.7.1):
    O estado reconstruído por ``replay(events)`` SHALL ser bit-equivalente
    ao estado construído via chamadas diretas de ``replace_expression`` etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from ..expression import ClinicalExpression, ExpressionState, Confidence, Trend, Volatility
from ..explainability import Explanation
from ..expression.clinical_expression import ExplanationSummary
from .context_dependency import ContextDependency
from .evidence import EvidenceReference
from .history import History, HistoryEntry
from .hypothesis import Hypothesis
from .metadata_record import MetadataRecord
from .relationship import Relationship
from .snapshot import Snapshot
from .snapshot_policy import SnapshotPolicy
from .trajectory import Trajectory, TrajectoryPoint


# REDACTED
# Reference Implementation — Declarative Traceability
# REDACTED
#
# implements:
#   AS-001-REQ-0001 — Identidade canônica (tenant_id, patient_id, gene_id)
#   AS-001-REQ-0002 — URN urn:araos:gene:{tenant}:{patient}:{gene}
#   AS-001-REQ-0003 — Versionamento SemVer
#   AS-001-REQ-0004 — Status lifecycle (ACTIVE, ARCHIVED)
#   AS-001-REQ-0005 — Created_at / updated_at imutáveis em criação
#   AS-001-REQ-0006 — Trajectory como série histórica
#   AS-001-REQ-0007 — History como audit chain canônico
#   AS-001-REQ-0008 — Metadata como registros imutáveis
#   AS-001-REQ-0009 — Replay bit-identical a partir dos eventos
#   AS-001-REQ-0010 — Snapshots como pontos de materialização
#   AS-001-REQ-0011 — Evidência preservada
#   AS-001-REQ-0012 — Hipóteses como conhecimento ativo
#   AS-001-REQ-0013 — Relacionamentos com tipos canônicos
#   AS-001-REQ-0014 — Contexto referenciado por ID
#   AS-001-REQ-0015 — Substituição de Expression preserva histórico
#   AS-001-REQ-0016 — Bitemporalidade via valid_time + transaction_time
#   AS-001-REQ-0017 — Multi-tenancy estrito
#   AS-002-REQ-0001 — Composição Expression-imutável por Gene
#   AS-002-REQ-0002 — Replacement Event Sourced
#   AS-002-REQ-0003 — Bitemporalidade preservada
# REDACTED


# Status canônicos (AS-001 §6.4).
class GeneStatus:
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_gene_id(name: str) -> str:
    """Gera gene_id a partir do nome canônico.

    AS-001 §5.1.2 — nome canônico é a chave de registro. Esta função apenas
    canonicaliza; o ID de instância é (tenant_id, patient_id, gene_id).
    """
    if not name:
        raise ValueError("Gene name obrigatório")
    return name.strip().upper().replace(" ", "_")


def build_urn(tenant_id: str, patient_id: str, gene_id: str) -> str:
    """URN canônico conforme AS-001 §5.1.2."""
    return f"urn:araos:gene:{tenant_id}:{patient_id}:{gene_id}"


@dataclass(frozen=True)
class ClinicalGene:
    """Aggregate Root imutável — Sprint 4.3 Phase 2 Reference Implementation."""

    tenant_id: str
    patient_id: str
    gene_id: str
    version: str                    # SemVer "1.0.0"
    status: str                     # ACTIVE / ARCHIVED
    created_at: datetime
    updated_at: datetime
    trajectory: Trajectory
    history: History
    metadata: tuple[MetadataRecord, ...]
    evidence: tuple[EvidenceReference, ...] = field(default_factory=tuple)
    hypotheses: tuple[Hypothesis, ...] = field(default_factory=tuple)
    relationships: tuple[Relationship, ...] = field(default_factory=tuple)
    context: tuple[ContextDependency, ...] = field(default_factory=tuple)
    snapshots: tuple[Snapshot, ...] = field(default_factory=tuple)
    snapshot_policy: SnapshotPolicy = field(default_factory=SnapshotPolicy.never)
    last_event_id: str | None = None
    last_sequence: int = -1

    # REDACTED
    # Identity & URIs
    # REDACTED

    @property
    def urn(self) -> str:
        """URN canônico (AS-001 §5.1.2)."""
        return build_urn(self.tenant_id, self.patient_id, self.gene_id)

    @property
    def id(self) -> tuple[str, str, str]:
        """Identidade canônica (tenant_id, patient_id, gene_id)."""
        return (self.tenant_id, self.patient_id, self.gene_id)

    # REDACTED
    # Current state
    # REDACTED

    @property
    def current_expression(self) -> ClinicalExpression | None:
        """Expression atual (última da Trajectory)."""
        latest = self.trajectory.latest()
        return latest.expression if latest else None

    def current_state(self) -> ExpressionState | None:
        expr = self.current_expression
        return expr.state if expr else None

    def has_expression(self) -> bool:
        return self.current_expression is not None

    # REDACTED
    # Append-only operations — retornam NOVO ClinicalGene
    # REDACTED

    def replace_expression(
        self,
        new_expression: ClinicalExpression,
        *,
        event_id: str,
        event_type: str,
        explanation: Explanation,
        correlation_id: str | None = None,
    ) -> "ClinicalGene":
        """Substitui Expression atual preservando histórico (AS-002 §6.5).

        A Expression anterior permanece na Trajectory (append-only).
        A HistoryEntry é adicionada para auditoria.
        """
        self._assert_consistent_identity(new_expression)
        if self.status == GeneStatus.ARCHIVED:
            raise ValueError(
                "ClinicalGene arquivado não pode ter Expression substituída "
                "(AS-001 §6.4 — arquivamento é terminal)"
            )
        if not event_id:
            raise ValueError("event_id obrigatório para auditoria")
        if not isinstance(explanation, Explanation):
            raise TypeError(
                f"replace_expression exige Explanation, recebido "
                f"{type(explanation).__name__}"
            )

        point = TrajectoryPoint(
            expression=new_expression,
            contributing_event_ids=(event_id,),
        )
        new_trajectory = self.trajectory.append(point)

        payload_summary = (
            f"{event_type}: gene={self.gene_id} state={new_expression.state.value} "
            f"value={new_expression.observed_value.data} "
            f"confidence={new_expression.confidence.value:.2f}"
        )
        allocated_sequence = self.last_sequence + 1
        entry = HistoryEntry(
            event_id=event_id,
            sequence=allocated_sequence,
            event_type=event_type,
            occurred_at=new_expression.valid_time,
            recorded_at=new_expression.transaction_time,
            payload_summary=payload_summary,
            origin=new_expression.metadata.get("origin", "system") if new_expression.metadata else "system",
        )
        new_history = self.history.append(entry)

        new_metadata = self.metadata + (
            MetadataRecord(
                record_id=f"meta_{event_id[:8]}",
                content=MappingProxyType({
                    "kind": "expression_replaced",
                    "explanation_id": explanation.explanation_id,
                    "correlation_id": correlation_id or "",
                }),
                created_at=new_expression.transaction_time,
                origin_event_id=event_id,
            ),
        )

        return self._with(
            trajectory=new_trajectory,
            history=new_history,
            metadata=new_metadata,
            updated_at=new_expression.transaction_time,
            last_event_id=event_id,
            last_sequence=allocated_sequence,
        )

    def add_hypothesis(
        self,
        hypothesis: Hypothesis,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        if any(h.hypothesis_id == hypothesis.hypothesis_id for h in self.hypotheses):
            # Idempotência — não duplica hipóteses com mesmo ID.
            return self
        new_hypotheses = self.hypotheses + (hypothesis,)
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="HYPOTHESIS_ADDED",
            occurred_at=_utcnow(),
            recorded_at=_utcnow(),
            payload_summary=f"HYPOTHESIS_ADDED: id={hypothesis.hypothesis_id} weight={hypothesis.weight:.2f}",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            hypotheses=new_hypotheses,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def deactivate_hypothesis(
        self,
        hypothesis_id: str,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        new_hypotheses = tuple(
            h.deactivate() if h.hypothesis_id == hypothesis_id else h
            for h in self.hypotheses
        )
        if new_hypotheses == self.hypotheses:
            return self
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="HYPOTHESIS_DEACTIVATED",
            occurred_at=_utcnow(),
            recorded_at=_utcnow(),
            payload_summary=f"HYPOTHESIS_DEACTIVATED: id={hypothesis_id}",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            hypotheses=new_hypotheses,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def add_relationship(
        self,
        relationship: Relationship,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        new_relationships = self.relationships + (relationship,)
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="RELATIONSHIP_ADDED",
            occurred_at=_utcnow(),
            recorded_at=_utcnow(),
            payload_summary=f"RELATIONSHIP_ADDED: target={relationship.target_gene_id} type={relationship.relationship_type}",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            relationships=new_relationships,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def add_context(
        self,
        context: ContextDependency,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        new_context = self.context + (context,)
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="CONTEXT_ADDED",
            occurred_at=_utcnow(),
            recorded_at=_utcnow(),
            payload_summary=f"CONTEXT_ADDED: id={context.context_id} type={context.context_type}",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            context=new_context,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def remove_context(
        self,
        context_id: str,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        new_context = tuple(c for c in self.context if c.context_id != context_id)
        if new_context == self.context:
            return self
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="CONTEXT_REMOVED",
            occurred_at=_utcnow(),
            recorded_at=_utcnow(),
            payload_summary=f"CONTEXT_REMOVED: id={context_id}",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            context=new_context,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def add_evidence(
        self,
        evidence: EvidenceReference,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        new_evidence = self.evidence + (evidence,)
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="EVIDENCE_RECORDED",
            occurred_at=evidence.observed_at,
            recorded_at=_utcnow(),
            payload_summary=f"EVIDENCE_RECORDED: id={evidence.event_id} weight={evidence.contributing_weight:.2f}",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            evidence=new_evidence,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def add_metadata(
        self,
        record: MetadataRecord,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        if any(r.record_id == record.record_id for r in self.metadata):
            return self
        new_metadata = self.metadata + (record,)
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="METADATA_RECORDED",
            occurred_at=record.created_at,
            recorded_at=_utcnow(),
            payload_summary=f"METADATA_RECORDED: id={record.record_id}",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            metadata=new_metadata,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def take_snapshot(
        self,
        snapshot: Snapshot,
        *,
        event_id: str,
    ) -> "ClinicalGene":
        if not event_id:
            raise ValueError("event_id obrigatório")
        new_snapshots = self.snapshots + (snapshot,)
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="SNAPSHOT_TAKEN",
            occurred_at=snapshot.valid_time,
            recorded_at=_utcnow(),
            payload_summary=f"SNAPSHOT_TAKEN: id={snapshot.snapshot_id} hash={snapshot.state_hash[:12]}...",
            origin="system",
        )
        new_history = self.history.append(entry)
        return self._with(
            snapshots=new_snapshots,
            history=new_history,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    def archive(
        self,
        *,
        event_id: str,
        reason: str,
    ) -> "ClinicalGene":
        """Arquiva o Gene (AS-001 §6.4 — terminal)."""
        if not event_id:
            raise ValueError("event_id obrigatório")
        if self.status == GeneStatus.ARCHIVED:
            return self
        entry = HistoryEntry(
            event_id=event_id,
            sequence=self.last_sequence + 1,
            event_type="GENE_ARCHIVED",
            occurred_at=_utcnow(),
            recorded_at=_utcnow(),
            payload_summary=f"GENE_ARCHIVED: reason={reason}",
            origin="system",
        )
        new_history = self.history.append(entry)
        new_metadata = self.metadata + (
            MetadataRecord(
                record_id=f"archive_{event_id[:8]}",
                content=MappingProxyType({"kind": "archived", "reason": reason}),
                created_at=_utcnow(),
                origin_event_id=event_id,
            ),
        )
        return self._with(
            status=GeneStatus.ARCHIVED,
            history=new_history,
            metadata=new_metadata,
            updated_at=entry.recorded_at,
            last_event_id=event_id,
            last_sequence=entry.sequence,
        )

    # REDACTED
    # Bitemporal queries (AS-001 §7.4 + AS-002 §6.3)
    # REDACTED

    def state_at(self, when: datetime) -> ExpressionState | None:
        return self.trajectory.state_at(when)

    def known_at(self, when: datetime) -> set[str]:
        return self.trajectory.known_at(when)

    # REDACTED
    # Explainability (cross-cutting)
    # REDACTED

    def why(self) -> ExplanationSummary:
        """Explica o estado atual do Gene.

        Delega para ``ClinicalExpression.why()`` se houver Expression atual.
        Caso contrário, retorna summary com explanation_reference vazio.
        """
        expr = self.current_expression
        if expr is None:
            return ExplanationSummary(
                explanation_reference=f"summary_no_expr_{self.gene_id}",
                evidence=[],
                contexts=[],
                confidence=Confidence.zero(),
                valid_time=self.created_at,
                transaction_time=self.updated_at,
                trend=Trend.UNKNOWN,
                volatility=Volatility.UNKNOWN,
                state=ExpressionState.UNKNOWN,
            )
        return expr.why()

    # REDACTED
    # Internal helper
    # REDACTED

    def _assert_consistent_identity(self, expression: ClinicalExpression) -> None:
        if expression.tenant_id != self.tenant_id:
            raise ValueError(
                f"Expression.tenant_id={expression.tenant_id} != Gene.tenant_id={self.tenant_id}"
            )
        if expression.patient_id != self.patient_id:
            raise ValueError(
                f"Expression.patient_id={expression.patient_id} != Gene.patient_id={self.patient_id}"
            )
        if expression.gene_id != self.gene_id:
            raise ValueError(
                f"Expression.gene_id={expression.gene_id} != Gene.gene_id={self.gene_id}"
            )

    def _with(self, **changes: Any) -> "ClinicalGene":
        """Retorna novo ClinicalGene com campos atualizados."""
        return dataclasses_replace(self, **changes)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClinicalGene):
            return NotImplemented
        return (
            self.tenant_id == other.tenant_id
            and self.patient_id == other.patient_id
            and self.gene_id == other.gene_id
            and self.version == other.version
            and self.status == other.status
            and self.trajectory == other.trajectory
            and self.history == other.history
            and self.metadata == other.metadata
            and self.evidence == other.evidence
            and self.hypotheses == other.hypotheses
            and self.relationships == other.relationships
            and self.context == other.context
            and self.snapshots == other.snapshots
        )

    def __hash__(self) -> int:
        return hash(self.urn)


def dataclasses_replace(instance: ClinicalGene, **changes: Any) -> ClinicalGene:
    """dataclasses.replace wrapper para ClinicalGene."""
    import dataclasses
    return dataclasses.replace(instance, **changes)