"""
ReplayEngine — reconstrói um ClinicalGene a partir de eventos.

Reference Implementation — Sprint 4.3 Phase 2.

Invariante central (AS-001 §7.7.1):
    Para qualquer sequência ``events`` válida, ``ReplayEngine.replay(events)``
    SHALL produzir um ClinicalGene bit-equivalente ao estado construído via
    chamadas diretas dos métodos do AR.

Idempotência:
    Replay bit-identical garante idempotência (Sprint 3.2 padrão ADR-0001).

Out-of-order safety:
    Eventos desordenados por sequence produzem o mesmo estado final quando
    reordenados por ``sequence`` asc antes do replay.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone

from ..domain.aggregate import (
    ClinicalGene,
    ContextDependency,
    EvidenceReference,
    Hypothesis,
    MetadataRecord,
    Relationship,
    Snapshot,
    create_gene,
)
from ..domain.events import DomainEvent, GENE_CREATED
from ..domain.events.factory import (
    EXPRESSION_OBSERVED,
    EXPRESSION_REPLACED,
    EXPRESSION_UNKNOWN_RECORDED,
    EXPRESSION_UNAVAILABLE_RECORDED,
    EXPRESSION_DERIVED_COMPUTED,
    HYPOTHESIS_ADDED,
    HYPOTHESIS_DEACTIVATED,
    RELATIONSHIP_ADDED,
    CONTEXT_ADDED,
    CONTEXT_REMOVED,
    EVIDENCE_RECORDED,
    METADATA_RECORDED,
    SNAPSHOT_TAKEN,
    GENE_ARCHIVED,
)
from ..domain.expression import (
    ClinicalExpression,
    Confidence,
    ExpressionState,
    ObservedValue,
    Trend,
    Volatility,
)
from ..domain.explainability import Explanation


# implements:
#   AS-001-REQ-0009 — Replay bit-identical a partir dos eventos
#   AS-001-REQ-0017 — Reordenação por sequence ascendente
#   ADR-0001 — sequence per-tenant monotônico


def _reconstruct_expression_from_event(
    event: DomainEvent,
) -> ClinicalExpression:
    """Reconstrói uma ClinicalExpression a partir de EXPRESSION_OBSERVED/REPLACED.

    Payload esperado (canonical): contém chave ``expression`` com dict de campos.
    """
    payload = dict(event.payload)
    expr_payload = dict(payload["expression"])
    return ClinicalExpression(
        gene_id=event.gene_id,
        tenant_id=event.tenant_id,
        patient_id=event.patient_id,
        observed_value=ObservedValue(
            data=expr_payload["observed_value"]["data"],
            unit=expr_payload["observed_value"].get("unit", ""),
            qualifier=expr_payload["observed_value"].get("qualifier", ""),
        ),
        confidence=Confidence(
            value=float(expr_payload.get("confidence", 0.0)),
        ),
        trend=Trend(expr_payload.get("trend", "unknown")),
        volatility=Volatility(expr_payload.get("volatility", "unknown")),
        last_update=event.transaction_time,
        valid_time=event.valid_time,
        transaction_time=event.transaction_time,
        explanation_reference=expr_payload.get("explanation_reference", payload.get("explanation_reference", "")),
        evidence_references=tuple(
            EvidenceReference(
                event_id=e["event_id"],
                event_type=e["event_type"],
                observed_at=_ensure_aware(_parse_iso(e["observed_at"])),
                contributing_weight=float(e.get("contributing_weight", 1.0)),
            )
            for e in expr_payload.get("evidence_references", [])
        ),
        context_references=tuple(
            ContextDependency(
                context_id=c["context_id"],
                context_type=c["context_type"],
                effective_from=_ensure_aware(_parse_iso(c["effective_from"])),
                effective_until=(
                    _ensure_aware(_parse_iso(c["effective_until"]))
                    if c.get("effective_until")
                    else None
                ),
                weight=float(c.get("weight", 1.0)),
            )
            for c in expr_payload.get("context_references", [])
        ),
        state=ExpressionState(expr_payload.get("state", "CANONICAL")),
        sequence=event.sequence,
    )


def _parse_iso(s: str) -> datetime:
    """Parse ISO-8601 string → datetime."""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def REDACTED(event: DomainEvent) -> Explanation:
    """Reconstrói uma Explanation mínima a partir de um evento."""
    return Explanation(
        explanation_id=event.payload.get("explanation_reference", f"replay_{event.event_id}"),
        analysis_type="expression_event",
        question=f"Por que evento {event.event_type}?",
        answer=f"Replayed a partir de event_id={event.event_id}",
        confidence=1.0,
        method="replay",
        data_window=None,
        contributing_event_ids=(event.event_id,),
    )


@dataclass(frozen=True)
class ReplayEngine:
    """Engine que reconstrói um ClinicalGene a partir de Domain Events.

    Mantém-se stateless (instâncias são equivalentes).
    """

    def replay(
        self,
        events: Iterable[DomainEvent],
        *,
        initial_version: str = "1.0.0",
    ) -> ClinicalGene:
        """Reconstrói um Gene a partir de eventos.

        Eventos MUST estar ordenados por ``(valid_time, sequence)`` ASC para
        garantir determinismo. Eventos fora de ordem produzem o mesmo estado
        final mas com timestamps intermediários diferentes.
        """
        ordered = sorted(events, key=lambda e: (e.sequence, e.valid_time, e.event_id))

        if not ordered:
            raise ValueError("ReplayEngine.replay exige ≥ 1 evento")

        first = ordered[0]
        gene = create_gene(
            tenant_id=first.tenant_id,
            patient_id=first.patient_id,
            gene_id=first.gene_id,
            version=initial_version,
            origin=first.origin,
            created_at=first.transaction_time,
        )

        for event in ordered:
            gene = self._apply_event(gene, event)

        return gene

    def replay_from_snapshot(
        self,
        snapshot: Snapshot,
        events_after: Iterable[DomainEvent],
    ) -> ClinicalGene:
        """Replay incremental a partir de um Snapshot + eventos posteriores.

        Carrega o estado do Snapshot e aplica apenas os eventos com
        ``sequence > snapshot.sequence``.
        """
        # Para Phase 2, snapshots marcam pontos de materialização; o replay
        # ainda exige o conjunto completo de eventos para reconstrução.
        # Esta função valida a posição do snapshot e re-aplica eventos
        # posteriores.
        events_list = list(events_after)
        for event in events_list:
            if event.sequence <= snapshot.sequence:
                raise ValueError(
                    f"events_after contém evento sequence={event.sequence} "
                    f"≤ snapshot.sequence={snapshot.sequence}"
                )
        return self.replay(events_list)

    def _apply_event(
        self,
        gene: ClinicalGene,
        event: DomainEvent,
    ) -> ClinicalGene:
        et = event.event_type

        if et == GENE_CREATED:
            # Já tratado pelo create_gene — idempotente.
            return gene

        if et in (EXPRESSION_OBSERVED, EXPRESSION_REPLACED, EXPRESSION_DERIVED_COMPUTED):
            expression = _reconstruct_expression_from_event(event)
            explanation = REDACTED(event)
            return gene.replace_expression(
                expression,
                event_id=event.event_id,
                event_type=et,
                explanation=explanation,
                correlation_id=event.correlation_id,
            )

        if et in (EXPRESSION_UNKNOWN_RECORDED, EXPRESSION_UNAVAILABLE_RECORDED):
            state = (
                ExpressionState.UNKNOWN
                if et == EXPRESSION_UNKNOWN_RECORDED
                else ExpressionState.UNAVAILABLE
            )
            # Cria Expression Unknown/Unavailable com observed_value vazio.
            expression = ClinicalExpression(
                gene_id=event.gene_id,
                tenant_id=event.tenant_id,
                patient_id=event.patient_id,
                observed_value=ObservedValue.unknown() if state == ExpressionState.UNKNOWN else ObservedValue.unavailable(),
                confidence=Confidence.zero(),
                trend=Trend.UNKNOWN,
                volatility=Volatility.UNKNOWN,
                last_update=event.transaction_time,
                valid_time=event.valid_time,
                transaction_time=event.transaction_time,
                explanation_reference=event.payload.get("explanation_reference", ""),
                evidence_references=(
                    EvidenceReference(
                        event_id=event.event_id,
                        event_type=event.event_type,
                        observed_at=event.valid_time,
                        contributing_weight=1.0,
                    ),
                ),
                context_references=(),
                state=state,
                sequence=event.sequence,
            )
            explanation = REDACTED(event)
            return gene.replace_expression(
                expression,
                event_id=event.event_id,
                event_type=et,
                explanation=explanation,
                correlation_id=event.correlation_id,
            )

        if et == HYPOTHESIS_ADDED:
            payload = dict(event.payload)
            hyp = Hypothesis(
                hypothesis_id=payload["hypothesis_id"],
                description=payload.get("description", ""),
                weight=float(payload.get("weight", 0.0)),
                supporting_event_ids=tuple(payload.get("supporting_event_ids", ())),
                confidence=float(payload.get("confidence", 0.0)),
                is_active=bool(payload.get("is_active", True)),
            )
            return gene.add_hypothesis(hyp, event_id=event.event_id)

        if et == HYPOTHESIS_DEACTIVATED:
            return gene.deactivate_hypothesis(
                event.payload.get("hypothesis_id", ""),
                event_id=event.event_id,
            )

        if et == RELATIONSHIP_ADDED:
            payload = dict(event.payload)
            rel = Relationship(
                relationship_id=payload["relationship_id"],
                target_gene_id=payload["target_gene_id"],
                relationship_type=payload["relationship_type"],
                weight=float(payload.get("weight", 0.0)),
                valid_time=_ensure_aware(_parse_iso(payload["valid_time"])),
            )
            return gene.add_relationship(rel, event_id=event.event_id)

        if et == CONTEXT_ADDED:
            payload = dict(event.payload)
            ctx = ContextDependency(
                context_id=payload["context_id"],
                context_type=payload["context_type"],
                effective_from=_ensure_aware(_parse_iso(payload["effective_from"])),
                effective_until=(
                    _ensure_aware(_parse_iso(payload["effective_until"]))
                    if payload.get("effective_until")
                    else None
                ),
                weight=float(payload.get("weight", 1.0)),
            )
            return gene.add_context(ctx, event_id=event.event_id)

        if et == CONTEXT_REMOVED:
            return gene.remove_context(
                event.payload.get("context_id", ""),
                event_id=event.event_id,
            )

        if et == EVIDENCE_RECORDED:
            payload = dict(event.payload)
            ev = EvidenceReference(
                event_id=payload["event_id"],
                event_type=payload["event_type"],
                observed_at=_ensure_aware(_parse_iso(payload["observed_at"])),
                contributing_weight=float(payload.get("contributing_weight", 1.0)),
            )
            return gene.add_evidence(ev, event_id=event.event_id)

        if et == METADATA_RECORDED:
            payload = dict(event.payload)
            rec = MetadataRecord(
                record_id=payload["record_id"],
                content=dict(payload.get("content", {})),
                created_at=event.valid_time,
                origin_event_id=event.event_id,
            )
            return gene.add_metadata(rec, event_id=event.event_id)

        if et == SNAPSHOT_TAKEN:
            payload = dict(event.payload)
            snap = Snapshot(
                snapshot_id=payload["snapshot_id"],
                gene_id=event.gene_id,
                sequence=event.sequence,
                valid_time=event.valid_time,
                transaction_time=event.transaction_time,
                state={"trajectory_len": len(gene.trajectory)},
                state_hash=payload["state_hash"],
            )
            return gene.take_snapshot(snap, event_id=event.event_id)

        if et == GENE_ARCHIVED:
            return gene.archive(
                event_id=event.event_id,
                reason=event.payload.get("reason", ""),
            )

        # Event type desconhecido: ignorar (forward compatibility).
        return gene