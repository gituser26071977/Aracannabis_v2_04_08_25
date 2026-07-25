"""
araos.clinical.knowledge.domain — pure domain layer.

Implementa:
    - ClinicalGenome (projection)
    - Correlation Engine
    - Hypothesis Engine
    - Knowledge Graph
    - Cohort Builder
    - Research Workspace
    - Explainability Pipeline

Invariantes (Foundation Freeze):
    - Nenhum import de flask, sqlalchemy, redis, requests, pydantic,
      numpy, ou qualquer framework.
    - Apenas stdlib + tipos do genome (ClinicalGene, ClinicalExpression,
      DomainEvent, Explanation, ReplayEngine).
"""

from .explainability import (
    InferenceExplanation,
    InferenceType,
    ExplainabilityPipeline,
)
from .clinical_genome import (
    ClinicalGenome,
    ClinicalGenomeBuilder,
    GenomeState,
    build_clinical_genome,
)
from .correlation import (
    CorrelationEngine,
    CorrelationMethod,
    CorrelationResult,
)
from .hypothesis import (
    ClinicalHypothesis,
    HypothesisEngine,
    HypothesisStatus,
)
from .knowledge_graph import (
    EdgeType,
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    KnowledgeGraphBuilder,
    NodeType,
)
from .cohort import (
    Cohort,
    CohortBuilder,
    Criterion,
    CriterionOperator,
    PatientData,
)
from .research import (
    AnalysisType,
    ResearchQuery,
    ResearchSession,
    ResearchWorkspace,
)

__all__ = [
    # Explainability
    "InferenceExplanation",
    "InferenceType",
    "ExplainabilityPipeline",
    # ClinicalGenome
    "ClinicalGenome",
    "ClinicalGenomeBuilder",
    "GenomeState",
    "build_clinical_genome",
    # Correlation
    "CorrelationEngine",
    "CorrelationMethod",
    "CorrelationResult",
    # Hypothesis
    "ClinicalHypothesis",
    "HypothesisEngine",
    "HypothesisStatus",
    # Knowledge Graph
    "EdgeType",
    "GraphEdge",
    "GraphNode",
    "KnowledgeGraph",
    "KnowledgeGraphBuilder",
    "NodeType",
    # Cohort
    "Cohort",
    "CohortBuilder",
    "Criterion",
    "CriterionOperator",
    "PatientData",
    # Research
    "AnalysisType",
    "ResearchQuery",
    "ResearchSession",
    "ResearchWorkspace",
]