"""Knowledge API — DTO mappers.

RC1 Gate 2 — REST translation layer.

This module converts domain entities (``ClinicalGenome``, ``CorrelationResult``,
``ClinicalHypothesis``, ``KnowledgeGraph``, ``Cohort``, ``ResearchSession``)
into the immutable DTOs defined in ``dto.py``.

Mappers are kept THIN:
- One function per entity type.
- No side effects, no I/O, no persistence.
- They never RETURN a domain entity — only DTOs.
- They never MODIFY a domain entity.

The mappers import ONLY domain types (read access); they must NOT import
anything from ``araos.clinical.*/infrastructure/`` or anything that pulls
SQLAlchemy transitively.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from interfaces.rest.v1.dto import (
    Cohort,
    Correlation,
    GraphEdgePayload,
    GraphNodePayload,
    GenomeDetail,
    GenomeSummary,
    Hypothesis,
    KnowledgeGraph,
    ResearchSessionDetail,
    ResearchSessionSummary,
    iso,
)


# ─────────────────────────────────────────────────────────────────────
# Genome
# ─────────────────────────────────────────────────────────────────────

def genome_to_summary(genome: Any) -> GenomeSummary:
    """Build a lightweight summary (no correlations/hypotheses embedded)."""
    return GenomeSummary(
        genome_id=str(getattr(genome, "genome_id")),
        tenant_id=str(getattr(genome, "tenant_id")),
        patient_id=str(getattr(genome, "patient_id")),
        window_start=iso(getattr(genome.window, "start")),
        window_end=iso(getattr(genome.window, "end")),
        window_label=getattr(genome.window, "label", None),
        state_hash=str(getattr(genome, "state_hash")),
        built_at=iso(getattr(genome, "built_at")),
        graph_snapshot_id=getattr(genome, "graph_snapshot_id", None),
        gene_count=len(tuple(getattr(genome, "genes", ()))),
        has_graph=bool(getattr(genome, "has_graph")() if hasattr(genome, "has_graph") else False),
    )


def genome_to_detail(genome: Any) -> GenomeDetail:
    """Build full detail including urn and counts from domain methods."""
    gene_ids = tuple(genome.gene_ids()) if hasattr(genome, "gene_ids") else tuple(
        getattr(g, "gene_id", "") for g in getattr(genome, "genes", ())
    )
    gene_count = len(tuple(getattr(genome, "genes", ())))
    correlations = tuple(getattr(genome, "correlation_results", ())) or ()
    hypotheses = tuple(getattr(genome, "hypotheses", ())) or ()
    has_graph = bool(genome.has_graph() if hasattr(genome, "has_graph") else False)
    urn = str(genome.urn) if hasattr(genome, "urn") else f"urn:araos:genome:{getattr(genome, 'genome_id')}"
    return GenomeDetail(
        genome_id=str(genome.genome_id),
        tenant_id=str(genome.tenant_id),
        patient_id=str(genome.patient_id),
        window_start=iso(genome.window.start),
        window_end=iso(genome.window.end),
        window_label=getattr(genome.window, "label", None),
        state_hash=str(genome.state_hash),
        built_at=iso(genome.built_at),
        graph_snapshot_id=getattr(genome, "graph_snapshot_id", None),
        gene_ids=gene_ids,
        gene_count=gene_count,
        correlation_count=len(correlations),
        hypothesis_count=len(hypotheses),
        has_graph=has_graph,
        urn=urn,
    )


# ─────────────────────────────────────────────────────────────────────
# Correlation
# ─────────────────────────────────────────────────────────────────────

def correlation_to_dto(c: Any) -> Correlation:
    explanation_id = None
    expl = getattr(c, "explanation", None)
    if expl is not None:
        explanation_id = str(getattr(expl, "explanation_id", None) or getattr(expl, "id", None) or "")
        if explanation_id == "":
            explanation_id = None
    return Correlation(
        correlation_id=str(c.correlation_id),
        method=str(getattr(c.method, "name", getattr(c.method, "value", str(c.method)))),
        gene_x_id=str(c.gene_x_id),
        gene_y_id=str(c.gene_y_id),
        coefficient=float(c.coefficient),
        p_value=float(c.p_value) if getattr(c, "p_value", None) is not None else None,
        n_observations=int(c.n_observations),
        confidence=float(c.confidence),
        computed_at=iso(getattr(c, "computed_at", None)),
        explanation_id=explanation_id,
    )


def correlations_to_dtos(iterable: Iterable[Any]) -> tuple[Correlation, ...]:
    return tuple(correlation_to_dto(c) for c in iterable)


# ─────────────────────────────────────────────────────────────────────
# Hypothesis
# ─────────────────────────────────────────────────────────────────────

def hypothesis_to_dto(h: Any) -> Hypothesis:
    explanation_id = None
    expl = getattr(h, "explanation", None)
    if expl is not None:
        explanation_id = str(getattr(expl, "explanation_id", None) or getattr(expl, "id", None) or "")
        if explanation_id == "":
            explanation_id = None
    return Hypothesis(
        hypothesis_id=str(h.hypothesis_id),
        claim=str(h.claim),
        confidence=float(h.confidence),
        supporting_genes=tuple(str(x) for x in getattr(h, "supporting_genes", ())),
        contradicting_genes=tuple(str(x) for x in getattr(h, "contradicting_genes", ())),
        evidence=tuple(str(x) for x in getattr(h, "evidence", ())),
        correlations_used=tuple(str(x) for x in getattr(h, "correlations_used", ())),
        status=str(getattr(h.status, "name", getattr(h.status, "value", str(h.status)))),
        rule_id=str(getattr(h, "rule_id", "")),
        created_at=iso(getattr(h, "created_at", None)),
        explanation_id=explanation_id,
    )


def hypotheses_to_dtos(iterable: Iterable[Any]) -> tuple[Hypothesis, ...]:
    return tuple(hypothesis_to_dto(h) for h in iterable)


# ─────────────────────────────────────────────────────────────────────
# Knowledge Graph
# ─────────────────────────────────────────────────────────────────────

def graphnode_to_dto(n: Any) -> GraphNodePayload:
    return GraphNodePayload(
        node_id=str(n.node_id),
        node_type=str(getattr(n.node_type, "name", getattr(n.node_type, "value", str(n.node_type)))),
        label=str(getattr(n, "label", "")),
        urn=str(getattr(n, "urn", f"urn:araos:graph:node:{getattr(n, 'node_id', '')}")),
    )


def graphedge_to_dto(e: Any) -> GraphEdgePayload:
    return GraphEdgePayload(
        edge_id=str(e.edge_id),
        source_node_id=str(e.source_node_id),
        target_node_id=str(e.target_node_id),
        edge_type=str(getattr(e.edge_type, "name", getattr(e.edge_type, "value", str(e.edge_type)))),
        weight=float(getattr(e, "weight", 0.0)),
    )


def graph_to_dto(g: Any) -> KnowledgeGraph:
    return KnowledgeGraph(
        graph_id=str(g.graph_id),
        tenant_id=str(g.tenant_id),
        patient_id=str(g.patient_id),
        nodes=tuple(graphnode_to_dto(n) for n in getattr(g, "nodes", ())),
        edges=tuple(graphedge_to_dto(e) for e in getattr(g, "edges", ())),
        built_at=iso(getattr(g, "built_at", None)),
        state_hash=str(getattr(g, "state_hash", "")),
        urn=str(getattr(g, "urn", f"urn:araos:graph:{getattr(g, 'graph_id', '')}")),
    )


# ─────────────────────────────────────────────────────────────────────
# Cohort
# ─────────────────────────────────────────────────────────────────────

def _criterion_to_dict(c: Any) -> dict:
    """Render a Criterion-like object to a public dict.

    Public shape:
        {"field": ..., "operator": ..., "value": ..., "window": {...}|null}
    """
    window = getattr(c, "window", None)
    window_dict = None
    if window is not None:
        window_dict = {
            "start": iso(getattr(window, "start", None)),
            "end": iso(getattr(window, "end", None)),
            "label": getattr(window, "label", None),
        }
    return {
        "field": str(getattr(c, "field", "")),
        "operator": str(getattr(c.operator, "name", getattr(c.operator, "value", str(c.operator)))),
        "value": getattr(c, "value", None),
        "window": window_dict,
    }


def cohort_to_dto(co: Any) -> Cohort:
    return Cohort(
        cohort_id=str(co.cohort_id),
        tenant_id=str(co.tenant_id),
        name=str(getattr(co, "name", "")),
        criteria=tuple(_criterion_to_dict(c) for c in getattr(co, "criteria", ())),
        matched_patient_ids=tuple(str(p) for p in getattr(co, "matched_patient_ids", ())),
        count=int(getattr(co, "count", len(getattr(co, "matched_patient_ids", ())))),
        built_at=iso(getattr(co, "built_at", None)),
        state_hash=str(getattr(co, "state_hash", "")),
    )


# ─────────────────────────────────────────────────────────────────────
# Research Session
# ─────────────────────────────────────────────────────────────────────

def research_session_summary(s: Any) -> ResearchSessionSummary:
    q = getattr(s, "query", None)
    return ResearchSessionSummary(
        session_id=str(s.session_id),
        tenant_id=str(getattr(s, "tenant_id", q.tenant_id if q and hasattr(q, "tenant_id") else "") or ""),
        query_id=str(getattr(q, "query_id", "")),
        cohort_id=str(getattr(q, "cohort_id", "")),
        analysis_type=str(getattr(getattr(q, "analysis_type", None), "name",
                                   getattr(getattr(q, "analysis_type", None), "value",
                                            getattr(q, "analysis_type", ""))) if q else ""),
        started_at=iso(getattr(s, "started_at", None)),
        completed_at=iso(getattr(s, "completed_at", None)),
        duration_seconds=float(getattr(s, "duration_seconds", 0.0)),
        state_hash=str(getattr(s, "state_hash", "")),
        reproducible=bool(getattr(s, "reproducible", False)),
    )


def research_session_detail(s: Any) -> ResearchSessionDetail:
    summary = research_session_summary(s)
    explanation_id = None
    expl = getattr(s, "explanation", None)
    if expl is not None:
        explanation_id = str(getattr(expl, "explanation_id", None) or getattr(expl, "id", None) or "")
        if explanation_id == "":
            explanation_id = None
    return ResearchSessionDetail(
        **summary.__dict__,
        result_json=str(getattr(s, "result_json", "{}")),
        explanation_id=explanation_id,
    )
