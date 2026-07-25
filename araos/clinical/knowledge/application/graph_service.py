"""GraphService — Application Layer."""

from __future__ import annotations

from typing import Sequence

from ..domain.clinical_genome import ClinicalGenome
from ..domain.correlation import CorrelationResult
from ..domain.hypothesis import ClinicalHypothesis
from ..domain.knowledge_graph import KnowledgeGraph, KnowledgeGraphBuilder
from .dto import GraphRequest


class GraphService:
    """Orquestra KnowledgeGraphBuilder."""

    def __init__(self, *, builder: KnowledgeGraphBuilder | None = None) -> None:
        self._builder = builder or KnowledgeGraphBuilder()

    def execute(self, request: GraphRequest) -> KnowledgeGraph:
        return self._builder.build(
            request.genome,
            correlations=request.correlations,
            hypotheses=request.hypotheses,
        )