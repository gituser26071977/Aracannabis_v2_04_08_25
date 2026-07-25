"""
Canonical JSON Serialization para Clinical Gene Engine.

Reference Implementation — Sprint 4.3 Phase 2.

Invariantes enforced:

- AS-002 §6.3 — Canonical JSON SHALL produzir serialização byte-equivalente
  para o mesmo estado.
- AS-002 §6.4 — Round-trip SHALL preservar estrutura.
- SHA-256 state_hash SHALL ser determinístico (independente de ambiente).

O serializer cobre:
- DomainEvent → JSON
- ClinicalGene → JSON (via decomposition recursiva de VOs)
- Snapshot.state_hash via SHA-256 (AS-002 §6.3)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

from ...domain.aggregate import (
    ClinicalGene,
    ContextDependency,
    EvidenceReference,
    HistoryEntry,
    Hypothesis,
    MetadataRecord,
    Relationship,
    Snapshot,
    TrajectoryPoint,
)
from ...domain.events import DomainEvent
from ...domain.expression import (
    ClinicalExpression,
    Confidence,
    ExpressionState,
    ObservedValue,
    Trend,
    Volatility,
)


# implements:
#   AS-002-REQ-0073 — Serialização Canônica JSON
#   AS-002-REQ-0074 — Round-trip preserva estrutura
#   AS-002-REQ-0075 — SHA-256 state_hash determinístico


def _datetime_to_iso(dt: datetime) -> str:
    """ISO-8601 com timezone UTC explícito."""
    if dt.tzinfo is None:
        from datetime import timezone
        dt = dt.replace(tzinfo=timezone.utc)
    s = dt.isoformat()
    # Garante que termina com +00:00 (não Z) para parse round-trip estável.
    if s.endswith("+00:00"):
        return s
    return s


def _datetime_from_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


# REDACTED
# Serializers por tipo
# REDACTED


def serialize_confidence(c: Confidence) -> dict[str, Any]:
    return {"type": "Confidence", "value": c.value}


def deserialize_confidence(d: Mapping[str, Any]) -> Confidence:
    return Confidence(value=float(d["value"]))


def serialize_observed_value(ov: ObservedValue) -> dict[str, Any]:
    return {
        "type": "ObservedValue",
        "data": ov.data,
        "unit": ov.unit,
        "qualifier": ov.qualifier,
    }


def deserialize_observed_value(d: Mapping[str, Any]) -> ObservedValue:
    return ObservedValue(
        data=d.get("data"),
        unit=d.get("unit", ""),
        qualifier=d.get("qualifier", ""),
    )


def serialize_clinical_expression(expr: ClinicalExpression) -> dict[str, Any]:
    return {
        "type": "ClinicalExpression",
        "gene_id": expr.gene_id,
        "tenant_id": expr.tenant_id,
        "patient_id": expr.patient_id,
        "observed_value": serialize_observed_value(expr.observed_value),
        "confidence": serialize_confidence(expr.confidence),
        "trend": expr.trend.value,
        "volatility": expr.volatility.value,
        "last_update": _datetime_to_iso(expr.last_update),
        "valid_time": _datetime_to_iso(expr.valid_time),
        "transaction_time": _datetime_to_iso(expr.transaction_time),
        "explanation_reference": expr.explanation_reference,
        "evidence_references": [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "observed_at": _datetime_to_iso(e.observed_at),
                "contributing_weight": e.contributing_weight,
            }
            for e in expr.evidence_references
        ],
        "context_references": [
            {
                "context_id": c.context_id,
                "context_type": c.context_type,
                "effective_from": _datetime_to_iso(c.effective_from),
                "effective_until": (
                    _datetime_to_iso(c.effective_until) if c.effective_until else None
                ),
                "weight": c.weight,
            }
            for c in expr.context_references
        ],
        "state": expr.state.value,
        "sequence": expr.sequence,
    }


def deserialize_clinical_expression(d: Mapping[str, Any]) -> ClinicalExpression:
    return ClinicalExpression(
        gene_id=d["gene_id"],
        tenant_id=d["tenant_id"],
        patient_id=d["patient_id"],
        observed_value=deserialize_observed_value(d["observed_value"]),
        confidence=deserialize_confidence(d["confidence"]),
        trend=Trend(d["trend"]),
        volatility=Volatility(d["volatility"]),
        last_update=_datetime_from_iso(d["last_update"]),
        valid_time=_datetime_from_iso(d["valid_time"]),
        transaction_time=_datetime_from_iso(d["transaction_time"]),
        explanation_reference=d["explanation_reference"],
        evidence_references=tuple(
            EvidenceReference(
                event_id=e["event_id"],
                event_type=e["event_type"],
                observed_at=_datetime_from_iso(e["observed_at"]),
                contributing_weight=float(e["contributing_weight"]),
            )
            for e in d.get("evidence_references", [])
        ),
        context_references=tuple(
            ContextDependency(
                context_id=c["context_id"],
                context_type=c["context_type"],
                effective_from=_datetime_from_iso(c["effective_from"]),
                effective_until=(
                    _datetime_from_iso(c["effective_until"]) if c.get("effective_until") else None
                ),
                weight=float(c["weight"]),
            )
            for c in d.get("context_references", [])
        ),
        state=ExpressionState(d["state"]),
        sequence=int(d.get("sequence", 0)),
    )


def serialize_trajectory_point(point: TrajectoryPoint) -> dict[str, Any]:
    return {
        "type": "TrajectoryPoint",
        "expression": serialize_clinical_expression(point.expression),
        "contributing_event_ids": list(point.contributing_event_ids),
    }


def serialize_history_entry(entry: HistoryEntry) -> dict[str, Any]:
    return {
        "type": "HistoryEntry",
        "event_id": entry.event_id,
        "sequence": entry.sequence,
        "event_type": entry.event_type,
        "occurred_at": _datetime_to_iso(entry.occurred_at),
        "recorded_at": _datetime_to_iso(entry.recorded_at),
        "payload_summary": entry.payload_summary,
        "origin": entry.origin,
    }


def serialize_metadata_record(rec: MetadataRecord) -> dict[str, Any]:
    return {
        "type": "MetadataRecord",
        "record_id": rec.record_id,
        "content": dict(rec.content),
        "created_at": _datetime_to_iso(rec.created_at),
        "origin_event_id": rec.origin_event_id,
    }


def serialize_hypothesis(h: Hypothesis) -> dict[str, Any]:
    return {
        "type": "Hypothesis",
        "hypothesis_id": h.hypothesis_id,
        "description": h.description,
        "weight": h.weight,
        "supporting_event_ids": list(h.supporting_event_ids),
        "confidence": h.confidence,
        "is_active": h.is_active,
    }


def serialize_relationship(r: Relationship) -> dict[str, Any]:
    return {
        "type": "Relationship",
        "target_gene_id": r.target_gene_id,
        "relationship_type": r.relationship_type,
        "confidence": r.confidence,
        "evidence_event_ids": list(r.evidence_event_ids),
        "created_at": _datetime_to_iso(r.created_at),
        "is_directed": r.is_directed,
        "is_active": r.is_active,
    }


def serialize_context_dependency(c: ContextDependency) -> dict[str, Any]:
    return {
        "type": "ContextDependency",
        "context_id": c.context_id,
        "context_type": c.context_type,
        "effective_from": _datetime_to_iso(c.effective_from),
        "effective_until": _datetime_to_iso(c.effective_until) if c.effective_until else None,
        "weight": c.weight,
    }


def serialize_evidence(e: EvidenceReference) -> dict[str, Any]:
    return {
        "type": "EvidenceReference",
        "event_id": e.event_id,
        "event_type": e.event_type,
        "observed_at": _datetime_to_iso(e.observed_at),
        "contributing_weight": e.contributing_weight,
    }


def serialize_snapshot(snap: Snapshot) -> dict[str, Any]:
    return {
        "type": "Snapshot",
        "snapshot_id": snap.snapshot_id,
        "gene_id": snap.gene_id,
        "sequence": snap.sequence,
        "valid_time": _datetime_to_iso(snap.valid_time),
        "transaction_time": _datetime_to_iso(snap.transaction_time),
        "state": dict(snap.state),
        "state_hash": snap.state_hash,
    }


def serialize_clinical_gene(gene: ClinicalGene) -> dict[str, Any]:
    """Serializa Gene inteiro para dict (ordem canônica)."""
    return {
        "type": "ClinicalGene",
        "version": "1.0",
        "tenant_id": gene.tenant_id,
        "patient_id": gene.patient_id,
        "gene_id": gene.gene_id,
        "semantic_version": gene.version,
        "status": gene.status,
        "created_at": _datetime_to_iso(gene.created_at),
        "updated_at": _datetime_to_iso(gene.updated_at),
        "trajectory": [serialize_trajectory_point(p) for p in gene.trajectory],
        "history": [serialize_history_entry(e) for e in gene.history],
        "metadata": [serialize_metadata_record(r) for r in gene.metadata],
        "evidence": [serialize_evidence(e) for e in gene.evidence],
        "hypotheses": [serialize_hypothesis(h) for h in gene.hypotheses],
        "relationships": [serialize_relationship(r) for r in gene.relationships],
        "context": [serialize_context_dependency(c) for c in gene.context],
        "snapshots": [serialize_snapshot(s) for s in gene.snapshots],
        "last_event_id": gene.last_event_id,
        "last_sequence": gene.last_sequence,
    }


def serialize_domain_event(event: DomainEvent) -> dict[str, Any]:
    return {
        "type": "DomainEvent",
        "event_id": event.event_id,
        "event_type": event.event_type,
        "tenant_id": event.tenant_id,
        "patient_id": event.patient_id,
        "gene_id": event.gene_id,
        "sequence": event.sequence,
        "valid_time": _datetime_to_iso(event.valid_time),
        "transaction_time": _datetime_to_iso(event.transaction_time),
        "payload": dict(event.payload),
        "origin": event.origin,
        "correlation_id": event.correlation_id,
        "metadata": dict(event.metadata),
    }


# REDACTED
# Top-level: gene_to_canonical_json / gene_from_canonical_json
# REDACTED


def gene_to_canonical_json(gene: ClinicalGene) -> str:
    """Serializa Gene para JSON canônico (ordem determinística de chaves).

    Usa ``sort_keys=True`` para garantir representação byte-equivalente
    para o mesmo estado (AS-002 §6.3).
    """
    return json.dumps(
        serialize_clinical_gene(gene),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )


def event_to_canonical_json(event: DomainEvent) -> str:
    return json.dumps(
        serialize_domain_event(event),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )


def events_to_canonical_json(events: list[DomainEvent]) -> str:
    return json.dumps(
        [serialize_domain_event(e) for e in events],
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )


def compute_state_hash(gene: ClinicalGene) -> str:
    """SHA-256 do estado serializado canonicamente (AS-002 §6.3).

    Hash é byte-equivalente para o mesmo estado — independe de ambiente,
    timestamp de execução ou versão de Python.
    """
    canonical = gene_to_canonical_json(gene)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def gene_from_canonical_json(s: str) -> ClinicalGene:
    """Rehidrata Gene a partir de JSON canônico (AS-002 §6.4).

    Phase 2B: round-trip completo. Todos os componentes são reconstruídos
    (Trajectory, History, Evidence, Hypotheses, Relationships, Context,
    Metadata, Snapshots).
    """
    d = json.loads(s)
    if d.get("type") != "ClinicalGene":
        raise ValueError(f"Tipo esperado ClinicalGene, recebido {d.get('type')}")
    trajectory_pts = []
    for p in d.get("trajectory", []):
        trajectory_pts.append(
            TrajectoryPoint(
                expression=deserialize_clinical_expression(p["expression"]),
                contributing_event_ids=tuple(p["contributing_event_ids"]),
            )
        )
    from ...domain.aggregate import History, Trajectory
    history_entries = []
    for e in d.get("history", []):
        history_entries.append(
            HistoryEntry(
                event_id=e["event_id"],
                sequence=e["sequence"],
                event_type=e["event_type"],
                occurred_at=_datetime_from_iso(e["occurred_at"]),
                recorded_at=_datetime_from_iso(e["recorded_at"]),
                payload_summary=e["payload_summary"],
                origin=e["origin"],
            )
        )
    evidence = tuple(
        EvidenceReference(
            event_id=e["event_id"],
            event_type=e["event_type"],
            observed_at=_datetime_from_iso(e["observed_at"]),
            contributing_weight=float(e["contributing_weight"]),
        )
        for e in d.get("evidence", [])
    )
    hypotheses = tuple(
        Hypothesis(
            hypothesis_id=h["hypothesis_id"],
            description=h.get("description", ""),
            weight=float(h.get("weight", 0.0)),
            supporting_event_ids=tuple(h.get("supporting_event_ids", ())),
            confidence=float(h.get("confidence", 0.0)),
            is_active=bool(h.get("is_active", True)),
        )
        for h in d.get("hypotheses", [])
    )
    relationships = tuple(
        Relationship(
            target_gene_id=r["target_gene_id"],
            relationship_type=r["relationship_type"],
            confidence=float(r.get("confidence", 0.0)),
            evidence_event_ids=tuple(r.get("evidence_event_ids", ())),
            created_at=_datetime_from_iso(r["created_at"]),
            is_directed=bool(r.get("is_directed", True)),
            is_active=bool(r.get("is_active", True)),
        )
        for r in d.get("relationships", [])
    )
    context = tuple(
        ContextDependency(
            context_id=c["context_id"],
            context_type=c["context_type"],
            effective_from=_datetime_from_iso(c["effective_from"]),
            effective_until=(
                _datetime_from_iso(c["effective_until"]) if c.get("effective_until") else None
            ),
            weight=float(c.get("weight", 1.0)),
        )
        for c in d.get("context", [])
    )
    snapshots = tuple(
        Snapshot(
            snapshot_id=s["snapshot_id"],
            gene_id=s["gene_id"],
            sequence=int(s["sequence"]),
            valid_time=_datetime_from_iso(s["valid_time"]),
            transaction_time=_datetime_from_iso(s["transaction_time"]),
            state=dict(s.get("state", {})),
            state_hash=s["state_hash"],
        )
        for s in d.get("snapshots", [])
    )
    return ClinicalGene(
        tenant_id=d["tenant_id"],
        patient_id=d["patient_id"],
        gene_id=d["gene_id"],
        version=d["semantic_version"],
        status=d["status"],
        created_at=_datetime_from_iso(d["created_at"]),
        updated_at=_datetime_from_iso(d["updated_at"]),
        trajectory=Trajectory(tuple(trajectory_pts)),
        history=History(tuple(history_entries)),
        metadata=tuple(
            MetadataRecord(
                record_id=r["record_id"],
                content=dict(r["content"]),
                created_at=_datetime_from_iso(r["created_at"]),
                origin_event_id=r["origin_event_id"],
            )
            for r in d.get("metadata", [])
        ),
        evidence=evidence,
        hypotheses=hypotheses,
        relationships=relationships,
        context=context,
        snapshots=snapshots,
        last_event_id=d.get("last_event_id"),
        last_sequence=d.get("last_sequence", -1),
    )