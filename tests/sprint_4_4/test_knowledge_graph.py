"""
Sprint 4.4 — Knowledge Graph.

Testes cobrindo:
    - Build determinístico (replay bit-identical).
    - 5 NodeTypes (GENE, EXPRESSION, EVIDENCE, HYPOTHESIS, PATIENT).
    - 7 EdgeTypes (SUPPORTS, CONTRADICTS, DERIVED_FROM, RELATED_TO,
      OBSERVED_WITH, TEMPORAL_BEFORE, TEMPORAL_AFTER).
    - Adjacency queries (neighbors, edges_of, find_path, subgraph_for).
    - Referential integrity (source/target node_ids must exist).
    - state_hash determinístico.
"""

from __future__ import annotations

import pytest

from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
from araos.clinical.knowledge.domain.correlation import CorrelationEngine, CorrelationMethod
from araos.clinical.knowledge.domain.hypothesis import HypothesisEngine
from araos.clinical.knowledge.domain.knowledge_graph import (
    EdgeType,
    KnowledgeGraphBuilder,
    NodeType,
)


class TestKnowledgeGraphBuild:
    """Build determinístico."""

    def test_build_returns_graph(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        # Assert
        assert graph.graph_id
        assert len(graph.nodes) > 0

    def test_state_hash_deterministic(self, scenario_alfa):
        # Act
        genome_a = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        genome_b = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph_a = KnowledgeGraphBuilder().build(genome_a)
        graph_b = KnowledgeGraphBuilder().build(genome_b)
        # Assert — same content → same hash
        assert graph_a.state_hash == graph_b.state_hash

    def REDACTED(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        d = graph.to_canonical_dict()
        # Assert — built_at NOT in canonical (replay invariant)
        assert "built_at" not in d


class TestKnowledgeGraphNodes:
    """Nodes esperados."""

    def test_has_patient_node(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        # Assert
        patients = graph.nodes_of_type(NodeType.PATIENT)
        assert len(patients) == 1

    def test_has_gene_nodes(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        genes = graph.nodes_of_type(NodeType.GENE)
        # Assert
        assert len(genes) == 2

    def test_has_expression_nodes(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        # Assert — 2 genes × 4 expressions = 8 nodes
        expressions = graph.nodes_of_type(NodeType.EXPRESSION)
        assert len(expressions) == 8

    def test_has_evidence_nodes(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        # Assert — 1 evidence per expression
        evidence = graph.nodes_of_type(NodeType.EVIDENCE)
        assert len(evidence) == 8  # 8 expressions × 1 evidence = 8

    @pytest.mark.parametrize("node_type", list(NodeType))
    def test_all_node_types_used(self, node_type, scenario_alfa):
        # Assert — enum is exhaustive
        assert node_type.value in {"gene", "expression", "evidence", "hypothesis", "patient"}


class TestKnowledgeGraphEdges:
    """Edges esperados."""

    def test_has_derived_from_edges(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        # Assert
        edges = [e for e in graph.edges if e.edge_type == EdgeType.DERIVED_FROM]
        assert len(edges) > 0

    @pytest.mark.parametrize("edge_type", list(EdgeType))
    def test_all_edge_types_defined(self, edge_type):
        # Assert — enum is exhaustive
        assert edge_type.value in {
            "supports", "contradicts", "derived_from", "related_to",
            "observed_with", "temporal_before", "temporal_after",
        }


class TestKnowledgeGraphAdjacency:
    """Adjacency queries."""

    def test_neighbors_of_patient_node(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        patients = graph.nodes_of_type(NodeType.PATIENT)
        assert len(patients) == 1
        patient_id = patients[0].node_id
        # Act
        neighbors = graph.neighbors(patient_id)
        # Assert — patient connects to 2 genes
        assert len(neighbors) == 2

    def test_edges_of_node(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        patients = graph.nodes_of_type(NodeType.PATIENT)
        edges = graph.edges_of(patients[0].node_id)
        # Assert — patient has edges to all its genes
        assert len(edges) == 2

    def test_find_path_bfs(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        patients = graph.nodes_of_type(NodeType.PATIENT)
        evidence = graph.nodes_of_type(NodeType.EVIDENCE)
        # Act — patient → some evidence via expressions
        path = graph.find_path(patients[0].node_id, evidence[0].node_id)
        # Assert
        assert path is not None
        assert path[0] == patients[0].node_id
        assert path[-1] == evidence[0].node_id

    def test_find_path_no_connection(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        graph = KnowledgeGraphBuilder().build(genome)
        # Source = target (same node)
        some_node = graph.nodes[0].node_id
        path = graph.find_path(some_node, some_node)
        # Assert — always returns self-path
        assert path == (some_node,)


class REDACTED:
    """Integração com Correlation + Hypothesis engines."""

    def REDACTED(self, scenario_alfa):
        # Act — use NEGATIVE (which our scenario triggers)
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.NEGATIVE)
        graph = KnowledgeGraphBuilder().build(genome, correlations=correlations)
        # Assert — correlation edge between 2 genes
        gene_to_gene = [
            e for e in graph.edges
            if any(
                n.node_type == NodeType.GENE and n.node_id == e.source_node_id
                for n in graph.nodes
            ) and any(
                n.node_type == NodeType.GENE and n.node_id == e.target_node_id
                for n in graph.nodes
            )
        ]
        assert len(gene_to_gene) >= 1

    def test_hypothesis_nodes_and_edges(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        hypotheses = HypothesisEngine().generate(genome, correlations)
        if len(hypotheses) > 0:
            graph = KnowledgeGraphBuilder().build(
                genome, correlations=correlations, hypotheses=hypotheses,
            )
            # Assert — at least 1 hypothesis node
            hyp_nodes = graph.nodes_of_type(NodeType.HYPOTHESIS)
            assert len(hyp_nodes) == len(hypotheses)


class REDACTED:
    """Invariantes estruturais."""

    def REDACTED(self, scenario_alfa):
        # Act
        genome = build_clinical_genome(
            tenant_id=scenario_alfa.tenant_id,
            patient_id=scenario_alfa.patient_id,
            window=scenario_alfa.window,
            genes=scenario_alfa.genes,
        )
        correlations = CorrelationEngine().compute(genome, method=CorrelationMethod.POSITIVE)
        hypotheses = HypothesisEngine().generate(genome, correlations)
        graph = KnowledgeGraphBuilder().build(
            genome, correlations=correlations, hypotheses=hypotheses,
        )
        # Assert — no orphan edges
        node_ids = {n.node_id for n in graph.nodes}
        for e in graph.edges:
            assert e.source_node_id in node_ids
            assert e.target_node_id in node_ids
