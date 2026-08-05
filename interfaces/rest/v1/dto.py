"""Knowledge API — DTOs (Data Transfer Objects).

RC1 Gate 2 — REST translation layer.

These DTOs are independent of:
- ORM models (no SQLAlchemy imports)
- Domain entities (no ClinicalGene / ClinicalGenome imports)
- Persistence layer

Every DTO is a frozen dataclass with primitives + ISO 8601 strings.
Serialization is via ``to_dict()`` which always returns a JSON-safe
mapping (no datetimes, no non-string keys, no class identity leakage).

Versioning rule: V1 DTOs are FROZEN in shape; new optional fields may be
appended in additive manner. New fields MUST NOT rename or remove
existing keys. V2 launches only when shape changes become unavoidable.

This module is referenced by:
- ``mappers.py``  — domain → DTO converters
- ``knowledge.py`` — blueprint handlers (HTTP ↔ DTOs)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Mapping


# ─────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────

def iso(value: Any) -> str:
    """Return a JSON-safe ISO 8601 string for any datetime-like value.

    - ``datetime`` → ``value.isoformat()``
    - ``str``      → returned as-is (already serialized upstream)
    - ``None``     → returned as ``None``
    - other        → ``str(value)`` (best-effort)
    """
    if value is None:
        return None  # type: ignore[return-value]
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _to_json_safe(obj: Any) -> Any:
    """Convert dataclass-like object to a JSON-safe primitive recursively."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (tuple, list)):
        return tuple(_to_json_safe(x) for x in obj)
    if isinstance(obj, Mapping):
        return {str(k): _to_json_safe(v) for k, v in obj.items()}
    if hasattr(obj, "to_dict"):
        return _to_json_safe(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return {k: _to_json_safe(v) for k, v in obj.__dict__.items()}
    return str(obj)


# ─────────────────────────────────────────────────────────────────────
# Request DTOs
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PipelineRunRequest:
    """Body for ``POST /knowledge/pipelines/run``.

    Note: ``tenant_id`` is NEVER present here — tenant comes from JWT only.
    """

    patient_id: str
    window_start: str  # ISO 8601 (e.g. "2026-01-01T00:00:00+00:00")
    window_end: str    # ISO 8601
    window_label: str | None = None
    methods: tuple[str, ...] = ()    # empty = use all CorrelationMethod
    include_graph: bool = True

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "window_label": self.window_label,
            "methods": list(self.methods),
            "include_graph": self.include_graph,
        }


# ─────────────────────────────────────────────────────────────────────
# Response DTOs (entity-shaped)
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HealthData:
    status: str
    version: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GenomeSummary:
    genome_id: str
    tenant_id: str
    patient_id: str
    window_start: str
    window_end: str
    state_hash: str
    built_at: str
    gene_count: int
    has_graph: bool
    window_label: str | None = None
    graph_snapshot_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "genome_id": self.genome_id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "window_label": self.window_label,
            "state_hash": self.state_hash,
            "built_at": self.built_at,
            "graph_snapshot_id": self.graph_snapshot_id,
            "gene_count": self.gene_count,
            "has_graph": self.has_graph,
        }


@dataclass(frozen=True)
class GenomeDetail:
    genome_id: str
    tenant_id: str
    patient_id: str
    window_start: str
    window_end: str
    window_label: str | None
    state_hash: str
    built_at: str
    graph_snapshot_id: str | None
    gene_ids: tuple[str, ...]
    gene_count: int
    correlation_count: int
    hypothesis_count: int
    has_graph: bool
    urn: str

    def to_dict(self) -> dict:
        return {
            "genome_id": self.genome_id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "window_label": self.window_label,
            "state_hash": self.state_hash,
            "built_at": self.built_at,
            "graph_snapshot_id": self.graph_snapshot_id,
            "gene_ids": list(self.gene_ids),
            "gene_count": self.gene_count,
            "correlation_count": self.correlation_count,
            "hypothesis_count": self.hypothesis_count,
            "has_graph": self.has_graph,
            "urn": self.urn,
        }


@dataclass(frozen=True)
class Correlation:
    correlation_id: str
    method: str
    gene_x_id: str
    gene_y_id: str
    coefficient: float
    p_value: float | None
    n_observations: int
    confidence: float
    computed_at: str
    explanation_id: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    claim: str
    confidence: float
    supporting_genes: tuple[str, ...]
    contradicting_genes: tuple[str, ...]
    evidence: tuple[str, ...]
    correlations_used: tuple[str, ...]
    status: str
    rule_id: str
    created_at: str
    explanation_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "claim": self.claim,
            "confidence": self.confidence,
            "supporting_genes": list(self.supporting_genes),
            "contradicting_genes": list(self.contradicting_genes),
            "evidence": list(self.evidence),
            "correlations_used": list(self.correlations_used),
            "status": self.status,
            "rule_id": self.rule_id,
            "created_at": self.created_at,
            "explanation_id": self.explanation_id,
        }


@dataclass(frozen=True)
class GraphNodePayload:
    node_id: str
    node_type: str
    label: str
    urn: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GraphEdgePayload:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    weight: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeGraph:
    graph_id: str
    tenant_id: str
    patient_id: str
    nodes: tuple[GraphNodePayload, ...]
    edges: tuple[GraphEdgePayload, ...]
    built_at: str
    state_hash: str
    urn: str

    def to_dict(self) -> dict:
        return {
            "graph_id": self.graph_id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "nodes": tuple(n.to_dict() for n in self.nodes),
            "edges": tuple(e.to_dict() for e in self.edges),
            "built_at": self.built_at,
            "state_hash": self.state_hash,
            "urn": self.urn,
        }


@dataclass(frozen=True)
class Cohort:
    cohort_id: str
    tenant_id: str
    name: str
    criteria: tuple[dict, ...]
    matched_patient_ids: tuple[str, ...]
    count: int
    built_at: str
    state_hash: str

    def to_dict(self) -> dict:
        return {
            "cohort_id": self.cohort_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "criteria": list(self.criteria),
            "matched_patient_ids": list(self.matched_patient_ids),
            "count": self.count,
            "built_at": self.built_at,
            "state_hash": self.state_hash,
        }


@dataclass(frozen=True)
class ResearchSessionSummary:
    session_id: str
    tenant_id: str
    query_id: str
    cohort_id: str
    analysis_type: str
    started_at: str
    completed_at: str
    duration_seconds: float
    state_hash: str
    reproducible: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ResearchSessionDetail:
    session_id: str
    tenant_id: str
    query_id: str
    cohort_id: str
    analysis_type: str
    started_at: str
    completed_at: str
    duration_seconds: float
    state_hash: str
    reproducible: bool
    result_json: str          # canonical JSON; never parsed server-side
    explanation_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "query_id": self.query_id,
            "cohort_id": self.cohort_id,
            "analysis_type": self.analysis_type,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "state_hash": self.state_hash,
            "reproducible": self.reproducible,
            "result_json": self.result_json,
            "explanation_id": self.explanation_id,
        }


# ─────────────────────────────────────────────────────────────────────
# Pipeline result envelope
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PipelineRunData:
    genome: GenomeDetail
    correlations: tuple[Correlation, ...]
    hypotheses: tuple[Hypothesis, ...]
    graph: KnowledgeGraph | None
    started_at: str
    completed_at: str
    duration_seconds: float

    def to_dict(self) -> dict:
        return {
            "genome": self.genome.to_dict(),
            "correlations": tuple(c.to_dict() for c in self.correlations),
            "hypotheses": tuple(h.to_dict() for h in self.hypotheses),
            "graph": self.graph.to_dict() if self.graph is not None else None,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
        }


# ─────────────────────────────────────────────────────────────────────
# Validation helper (used by handlers, not as part of the wire schema)
# ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ValidationFailure:
    field: str
    error: str
    value: Any = None

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "error": self.error,
            "value": _to_json_safe(self.value),
        }


def parse_pipeline_run(body: Mapping[str, Any]) -> PipelineRunRequest:
    """Parse + validate the body of POST /pipelines/run.

    Raises ``ValueError`` with a deterministic message on the first
    validation failure. The handler converts that to a 400 envelope.
    """
    if not isinstance(body, Mapping):
        raise ValueError("body must be a JSON object")
    missing = [k for k in ("patient_id", "window_start", "window_end") if not body.get(k)]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    start = body.get("window_start")
    end = body.get("window_end")
    try:
        start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"window_start/window_end must be ISO 8601: {exc}") from exc
    if end_dt <= start_dt:
        raise ValueError("window_end must be strictly after window_start")
    methods = body.get("methods") or ()
    if not isinstance(methods, (list, tuple)):
        raise ValueError("methods must be an array of strings")
    return PipelineRunRequest(
        patient_id=str(body["patient_id"]),
        window_start=str(start),
        window_end=str(end),
        window_label=body.get("window_label"),
        methods=tuple(str(m) for m in methods),
        include_graph=bool(body.get("include_graph", True)),
    )


def json_dumps_safe(obj: Any) -> str:
    """JSON-serialize a DTO mapping deterministically (used in audit/details)."""
    return json.dumps(_to_json_safe(obj), sort_keys=True, default=str, ensure_ascii=False)
