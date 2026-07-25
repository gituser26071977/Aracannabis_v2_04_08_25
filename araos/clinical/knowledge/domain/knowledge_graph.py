"""
Knowledge Graph — Sprint 4.4 Clinical Knowledge Engine v1.0.

PRINCÍPIOS:
    - Knowledge Graph é uma PROJEÇÃO (read-model).
    - Nunca é fonte de verdade.
    - Deve poder ser reconstruído integralmente via replay.

NÓS canônicos:
    - GENE         (ClinicalGene)
    - EXPRESSION   (ClinicalExpression de uma Trajectory)
    - EVIDENCE     (EvidenceReference)
    - HYPOTHESIS   (ClinicalHypothesis)
    - PATIENT      (referência ao tenant+patient)

EDGES canônicos:
    - SUPPORTS         (evidência apoia hypothesis; correlation apoia hypothesis)
    - CONTRADICTS      (refuta)
    - DERIVED_FROM     (Expression deriva de Gene; Hypothesis deriva de Correlation)
    - RELATED_TO       (relação genérica)
    - OBSERVED_WITH    (Expression e Expression co-ocorrem)
    - TEMPORAL_BEFORE  (precedência temporal)
    - TEMPORAL_AFTER   (sucessão temporal)

PURE DOMAIN:
    - Reconstruível via replay (state_hash SHA-256).
    - Adjacency queries in-memory: neighbors, edges_of, find_path (BFS).
    - Sem Neo4j/Cypher; apenas estruturas de dados Python.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from ...genome.domain.aggregate import ClinicalGene
from ...timeline.domain.window import TimeWindow
from .clinical_genome import ClinicalGenome
from .correlation import CorrelationResult
from .explainability import ExplainabilityPipeline, InferenceExplanation, InferenceType
from .hypothesis import ClinicalHypothesis


class NodeType(str, Enum):
    """Tipos canônicos de nós do Knowledge Graph."""

    GENE = "gene"
    EXPRESSION = "expression"
    EVIDENCE = "evidence"
    HYPOTHESIS = "hypothesis"
    PATIENT = "patient"


class EdgeType(str, Enum):
    """Tipos canônicos de arestas do Knowledge Graph."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"
    OBSERVED_WITH = "observed_with"
    TEMPORAL_BEFORE = "temporal_before"
    TEMPORAL_AFTER = "temporal_after"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _content_node_id(prefix: str, *parts: str) -> str:
    """ID determinístico: SHA-256(parts)[:12]"""
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"node_{prefix}_{digest}"


def _content_edge_id(source_id: str, target_id: str, edge_type: str, attrs: dict) -> str:
    """ID determinístico de aresta: SHA-256(source|target|type|sorted_attrs)[:14]"""
    payload = {
        "source": source_id,
        "target": target_id,
        "type": edge_type,
        "attrs": dict(sorted(attrs.items())),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:14]
    return f"edge_{digest}"


def _content_graph_id(tenant_id: str, patient_id: str) -> str:
    """ID determinístico de graph: derivado do tenant + patient."""
    raw = f"{tenant_id}|{patient_id}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"graph_{digest}"


# ============================================================================
# GraphNode
# ============================================================================


@dataclass(frozen=True)
class GraphNode:
    """Nó do Knowledge Graph."""

    node_id: str
    node_type: NodeType
    label: str
    urn: str
    attributes: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("GraphNode.node_id obrigatório")
        if not self.label:
            raise ValueError("GraphNode.label obrigatório")
        if not self.urn:
            raise ValueError("GraphNode.urn obrigatório")


# ============================================================================
# GraphEdge
# ============================================================================


@dataclass(frozen=True)
class GraphEdge:
    """Aresta do Knowledge Graph."""

    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    weight: float                       # ∈ [0.0, 1.0]
    attributes: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    explanation: InferenceExplanation | None = None

    def __post_init__(self) -> None:
        if not self.edge_id:
            raise ValueError("GraphEdge.edge_id obrigatório")
        if not self.source_node_id:
            raise ValueError("GraphEdge.source_node_id obrigatório")
        if not self.target_node_id:
            raise ValueError("GraphEdge.target_node_id obrigatório")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(
                f"GraphEdge.weight deve estar em [0.0, 1.0], recebido {self.weight}"
            )


# ============================================================================
# KnowledgeGraph
# ============================================================================


@dataclass(frozen=True)
class KnowledgeGraph:
    """Projeção grafo integrado de um paciente — sempre reconstruível.

    Invariantes:
        - state_hash SHA-256 da canonical JSON.
        - Para cada edge, source_node_id e target_node_id existem em nodes.
    """

    graph_id: str
    tenant_id: str
    patient_id: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    built_at: datetime
    state_hash: str = ""

    def __post_init__(self) -> None:
        if not self.graph_id:
            raise ValueError("KnowledgeGraph.graph_id obrigatório")
        # Validação de integridade referencial.
        node_ids = {n.node_id for n in self.nodes}
        for edge in self.edges:
            if edge.source_node_id not in node_ids:
                raise ValueError(
                    f"Edge {edge.edge_id} referencia source_node_id "
                    f"{edge.source_node_id} inexistente"
                )
            if edge.target_node_id not in node_ids:
                raise ValueError(
                    f"Edge {edge.edge_id} referencia target_node_id "
                    f"{edge.target_node_id} inexistente"
                )

    # REDACTED
    # Identidade
    # REDACTED

    @property
    def urn(self) -> str:
        return f"urn:araos:graph:{self.tenant_id}:{self.patient_id}:{self.graph_id}"

    # REDACTED
    # Adjacency queries — in-memory BFS
    # REDACTED

    def neighbors(self, node_id: str) -> tuple[GraphNode, ...]:
        """Retorna todos os vizinhos (entrada + saída) do nó."""
        adjacent_ids: set[str] = set()
        for edge in self.edges:
            if edge.source_node_id == node_id:
                adjacent_ids.add(edge.target_node_id)
            if edge.target_node_id == node_id:
                adjacent_ids.add(edge.source_node_id)
        nodes_by_id = {n.node_id: n for n in self.nodes}
        return tuple(nodes_by_id[nid] for nid in adjacent_ids if nid in nodes_by_id)

    def edges_of(self, node_id: str) -> tuple[GraphEdge, ...]:
        """Retorna todas as arestas incidentes ao nó."""
        return tuple(
            e for e in self.edges
            if e.source_node_id == node_id or e.target_node_id == node_id
        )

    def find_path(
        self,
        source_id: str,
        target_id: str,
        *,
        max_depth: int = 10,
    ) -> tuple[str, ...] | None:
        """BFS para encontrar caminho entre source e target.

        Retorna tuple de node_ids (incluindo source e target) ou None
        se não encontrado dentro de max_depth.
        """
        if source_id == target_id:
            return (source_id,)
        # Construir adjacency map.
        adj: dict[str, list[str]] = defaultdict(list)
        for edge in self.edges:
            adj[edge.source_node_id].append(edge.target_node_id)
            adj[edge.target_node_id].append(edge.source_node_id)
        # BFS.
        visited = {source_id}
        queue: deque[tuple[str, tuple[str, ...]]] = deque([(source_id, (source_id,))])
        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue
            for next_node in adj[current]:
                if next_node == target_id:
                    return path + (next_node,)
                if next_node not in visited:
                    visited.add(next_node)
                    queue.append((next_node, path + (next_node,)))
        return None

    def nodes_of_type(self, node_type: NodeType) -> tuple[GraphNode, ...]:
        return tuple(n for n in self.nodes if n.node_type == node_type)

    # REDACTED
    # Canonical JSON + state_hash
    # REDACTED

    def to_canonical_dict(self) -> dict[str, Any]:
        """Canonical dict determinístico.

        Invariante de replay: este dict NÃO inclui built_at (metadado de
        chamada) nem graph_id (que vira id efêmero da reconstrução).
        Inclui apenas conteúdo clínico + IDs derivados de hash do conteúdo,
        garantindo state_hash byte-idêntico entre reconstruções.
        """
        return {
            "type": "KnowledgeGraph",
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "node_type": n.node_type.value,
                    "label": n.label,
                    "urn": n.urn,
                }
                for n in sorted(self.nodes, key=lambda x: x.node_id)
            ],
            "edges": [
                {
                    "edge_id": e.edge_id,
                    "source_node_id": e.source_node_id,
                    "target_node_id": e.target_node_id,
                    "edge_type": e.edge_type.value,
                    "weight": e.weight,
                }
                for e in sorted(self.edges, key=lambda x: x.edge_id)
            ],
        }

    def compute_state_hash(self) -> str:
        canonical = json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def validate_state_hash(self) -> None:
        """Sprint 4.4.5 — Hardening: state_hash MUST ser SHA-256 preenchido."""
        if not self.state_hash:
            raise ValueError(
                "KnowledgeGraph.state_hash MUST ser preenchido após construção "
                "— use KnowledgeGraphBuilder.build"
            )
        if len(self.state_hash) != 64:
            raise ValueError(
                f"KnowledgeGraph.state_hash deve ser SHA-256 hex (64 chars), "
                f"recebido {len(self.state_hash)}"
            )


# ============================================================================
# KnowledgeGraphBuilder — pure function, deterministic
# ============================================================================


class KnowledgeGraphBuilder:
    """Construtor puro de KnowledgeGraph a partir de genome + correlações + hypotheses.

    Uso:
        builder = KnowledgeGraphBuilder()
        graph = builder.build(genome, correlations=..., hypotheses=...)

    Determinismo:
        - IDs de nodes e edges são derivados de hash do conteúdo
          (não UUIDs aleatórios), garantindo state_hash byte-idêntico
          em replays sucessivos.
        - Para reprodutibilidade, ordene entradas externas antes de chamar.
    """

    def build(
        self,
        genome: ClinicalGenome,
        *,
        correlations: Sequence[CorrelationResult] = (),
        hypotheses: Sequence[ClinicalHypothesis] = (),
    ) -> KnowledgeGraph:
        """Constrói KnowledgeGraph integrado."""
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        # 1) Nó PATIENT (raiz).
        patient_node = GraphNode(
            node_id=_content_node_id("patient", genome.tenant_id, genome.patient_id),
            node_type=NodeType.PATIENT,
            label=f"Patient {genome.patient_id}",
            urn=f"urn:araos:patient:{genome.tenant_id}:{genome.patient_id}",
            attributes=MappingProxyType({
                "tenant_id": genome.tenant_id,
                "patient_id": genome.patient_id,
            }),
        )
        nodes[patient_node.node_id] = patient_node

        # 2) Para cada Gene: nó GENE + EXPRESSION nodes + EVIDENCE nodes.
        for gene in sorted(genome.genes, key=lambda g: g.gene_id):
            gene_node = self._make_gene_node(gene)
            nodes[gene_node.node_id] = gene_node
            # Edge PATIENT -[DERIVED_FROM]-> GENE (gene "pertence" ao patient).
            edges.append(self._make_edge(
                patient_node.node_id, gene_node.node_id,
                EdgeType.DERIVED_FROM, weight=1.0,
            ))
            # Expressions e Edges (ordenadas por sequence para determinismo).
            for point in sorted(gene.trajectory, key=lambda p: p.expression.sequence):
                expr_node = self._make_expression_node(gene, point.expression)
                nodes[expr_node.node_id] = expr_node
                edges.append(self._make_edge(
                    gene_node.node_id, expr_node.node_id,
                    EdgeType.DERIVED_FROM, weight=1.0,
                ))
                # Evidence nodes (ordenadas por event_id).
                for ev in sorted(point.expression.evidence_references, key=lambda e: e.event_id):
                    ev_node = self._make_evidence_node(gene, ev)
                    nodes[ev_node.node_id] = ev_node
                    edges.append(self._make_edge(
                        expr_node.node_id, ev_node.node_id,
                        EdgeType.DERIVED_FROM,
                        weight=ev.contributing_weight,
                    ))

        # 3) Correlações como edges entre Gene nodes.
        gene_node_by_id: dict[str, GraphNode] = {
            n.attributes.get("gene_id"): n
            for n in nodes.values()
            if n.node_type == NodeType.GENE
        }
        # Ordenar correlações determinísticamente por (gene_x, gene_y, method, sequence).
        sorted_corrs = sorted(
            correlations,
            key=lambda c: (c.gene_x_id, c.gene_y_id, c.method.value, getattr(c, "computed_at", "")),
        )
        for corr in sorted_corrs:
            gn_x = gene_node_by_id.get(corr.gene_x_id)
            gn_y = gene_node_by_id.get(corr.gene_y_id)
            if gn_x is None or gn_y is None:
                continue
            edge_type = (
                EdgeType.SUPPORTS
                if corr.method.value in ("positive", "temporal_precedence")
                else EdgeType.CONTRADICTS
                if corr.method.value == "mutual_exclusion"
                else EdgeType.OBSERVED_WITH
                if corr.method.value == "co_occurrence"
                else EdgeType.RELATED_TO
            )
            edges.append(self._make_edge(
                gn_x.node_id, gn_y.node_id,
                edge_type, weight=abs(corr.coefficient),
                attributes={"correlation_id": corr.correlation_id, "method": corr.method.value},
                explanation=corr.explanation,
            ))

        # 4) Hipóteses como nodes + edges SUPPORTS/CONTRADICTS para Gene nodes.
        # Ordenar hipóteses determinísticamente por hypothesis_id.
        sorted_hyps = sorted(hypotheses, key=lambda h: h.hypothesis_id)
        for hyp in sorted_hyps:
            hyp_node = self._make_hypothesis_node(hyp)
            nodes[hyp_node.node_id] = hyp_node
            for g in sorted(hyp.supporting_genes):
                gn = gene_node_by_id.get(g)
                if gn:
                    edges.append(self._make_edge(
                        hyp_node.node_id, gn.node_id,
                        EdgeType.SUPPORTS, weight=hyp.confidence,
                        attributes={"hypothesis_id": hyp.hypothesis_id},
                        explanation=hyp.explanation,
                    ))
            for g in sorted(hyp.contradicting_genes):
                gn = gene_node_by_id.get(g)
                if gn:
                    edges.append(self._make_edge(
                        hyp_node.node_id, gn.node_id,
                        EdgeType.CONTRADICTS, weight=hyp.confidence,
                        attributes={"hypothesis_id": hyp.hypothesis_id},
                        explanation=hyp.explanation,
                    ))

        graph = KnowledgeGraph(
            graph_id=_content_graph_id(genome.tenant_id, genome.patient_id),
            tenant_id=genome.tenant_id,
            patient_id=genome.patient_id,
            nodes=tuple(sorted(nodes.values(), key=lambda n: n.node_id)),
            edges=tuple(sorted(edges, key=lambda e: e.edge_id)),
            built_at=_utcnow(),
        )
        # Aplica state_hash.
        return _with_state_hash(graph, graph.compute_state_hash())

    # REDACTED
    # Helpers de construção
    # REDACTED

    def _make_gene_node(self, gene: ClinicalGene) -> GraphNode:
        return GraphNode(
            node_id=_content_node_id("gene", gene.tenant_id, gene.gene_id),
            node_type=NodeType.GENE,
            label=f"Gene {gene.gene_id}",
            urn=gene.urn,
            attributes=MappingProxyType({
                "gene_id": gene.gene_id,
                "version": gene.version,
                "status": gene.status,
            }),
        )

    def _make_expression_node(self, gene: ClinicalGene, expr: Any) -> GraphNode:
        return GraphNode(
            node_id=_content_node_id("expr", gene.tenant_id, gene.gene_id, str(expr.sequence)),
            node_type=NodeType.EXPRESSION,
            label=f"Expression #{expr.sequence} of {gene.gene_id}",
            urn=f"urn:araos:expression:{gene.tenant_id}:{gene.patient_id}:{gene.gene_id}:{expr.sequence}",
            attributes=MappingProxyType({
                "gene_id": gene.gene_id,
                "sequence": expr.sequence,
                "state": expr.state.value,
                "confidence": expr.confidence.value,
            }),
        )

    def _make_evidence_node(self, gene: ClinicalGene, ev: Any) -> GraphNode:
        return GraphNode(
            node_id=_content_node_id("ev", gene.tenant_id, ev.event_id),
            node_type=NodeType.EVIDENCE,
            label=f"Evidence {ev.event_type} #{ev.event_id[:8]}",
            urn=f"urn:araos:evidence:{ev.event_id}",
            attributes=MappingProxyType({
                "event_id": ev.event_id,
                "event_type": ev.event_type,
                "gene_id": gene.gene_id,
            }),
        )

    def _make_hypothesis_node(self, hyp: ClinicalHypothesis) -> GraphNode:
        # ID determinístico do node: derivado do conteúdo clínico
        # (rule + gene_ids ordenados + claim), NÃO do UUID hypothesis_id.
        content_key = "|".join([
            hyp.rule_id,
            ",".join(sorted(hyp.supporting_genes + hyp.contradicting_genes)),
            hyp.claim,
        ])
        digest = hashlib.sha256(content_key.encode("utf-8")).hexdigest()[:12]
        node_id = f"node_hyp_{digest}"
        return GraphNode(
            node_id=node_id,
            node_type=NodeType.HYPOTHESIS,
            label=f"Hypothesis {hyp.rule_id}: {hyp.claim[:50]}",
            urn=f"urn:araos:hypothesis:{node_id}",
            attributes=MappingProxyType({
                "hypothesis_id": hyp.hypothesis_id,
                "rule_id": hyp.rule_id,
                "status": hyp.status.value,
                "confidence": hyp.confidence,
            }),
        )

    def _make_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        *,
        weight: float,
        attributes: Mapping[str, Any] | None = None,
        explanation: InferenceExplanation | None = None,
    ) -> GraphEdge:
        attrs = MappingProxyType(dict(attributes) if attributes else {})
        # Explicação default para edges sem explicação específica.
        # Sprint 4.4.5 — Hardening: GRAPH_EDGE explanation MUST carry
        # participating_genes. Reusa source_id/target_id como genes
        # (eles são node_ids derivados de gene_ids no KnowledgeGraph).
        expl = explanation
        if expl is None:
            expl = ExplainabilityPipeline.begin(
                inference_type=InferenceType.GRAPH_EDGE,
                claim=f"Edge {edge_type.value} entre {source_id} e {target_id}",
                method="graph_builder",
                confidence=weight,
            ).with_genes(source_id, target_id).build()
        # Edge ID derivado do conteúdo (mesma entrada sempre gera mesmo ID).
        edge_id = _content_edge_id(source_id, target_id, edge_type.value, dict(attrs))
        return GraphEdge(
            edge_id=edge_id,
            source_node_id=source_id,
            target_node_id=target_id,
            edge_type=edge_type,
            weight=float(weight),
            attributes=attrs,
            explanation=expl,
        )


def _with_state_hash(
    graph: KnowledgeGraph, state_hash: str
) -> KnowledgeGraph:
    """Reconstroi KnowledgeGraph com state_hash (frozen dataclass)."""
    import dataclasses

    return dataclasses.replace(graph, state_hash=state_hash)


# implements:
#   AS-001 §6.8 — Knowledge Graph como projeção reconstruível
#   AS-001 §7.5 — Explainability cross-cutting (edges com explicação)
#   ADR-0006 §3 — Pure Domain (sem Neo4j)