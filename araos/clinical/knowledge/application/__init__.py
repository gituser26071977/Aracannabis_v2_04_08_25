"""
araos.clinical.knowledge.application — Application Layer.

Sprint 4.4 — Clinical Knowledge Engine v1.0.

Application Services, Command/Query Handlers, Facades e DTOs.

Propósito:
    Orquestrar o Domain Layer para executar casos de uso do Knowledge
    Engine (pipeline Replay → Projection → Correlation → Hypothesis →
    Knowledge Graph → Explainability).

Não introduz lógica de negócio própria: toda lógica reside no Domain.

Componentes:
    - KnowledgeService: facade principal
    - CorrelationService: orquestra CorrelationEngine
    - HypothesisService: orquestra HypothesisEngine
    - CohortService: orquestra CohortBuilder
    - ResearchService: orquestra ResearchWorkspace
    - GraphService: orquestra KnowledgeGraphBuilder
    - DTOs: KnowledgePipelineResult, CorrelationRequest, HypothesisRequest, etc.
"""

from .dto import (
    KnowledgePipelineResult,
    CorrelationRequest,
    HypothesisRequest,
    CohortRequest,
    ResearchRequest,
    GraphRequest,
)
from .knowledge_service import KnowledgeService
from .correlation_service import CorrelationService
from .hypothesis_service import HypothesisService
from .cohort_service import CohortService
from .research_service import ResearchService
from .graph_service import GraphService

__all__ = [
    "KnowledgeService",
    "CorrelationService",
    "HypothesisService",
    "CohortService",
    "ResearchService",
    "GraphService",
    "KnowledgePipelineResult",
    "CorrelationRequest",
    "HypothesisRequest",
    "CohortRequest",
    "ResearchRequest",
    "GraphRequest",
]