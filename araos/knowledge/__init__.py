"""
AraOS Knowledge Layer v1.

Camada de conhecimento da plataforma AraOS.

Responsabilidades:
    - Armazenar conhecimento institucional, profissional e clínico
    - Indexar Digital Twin, Timeline e Summary como conhecimento
    - Recuperar conhecimento por keyword e metadata
    - Fornecer contexto para o LLM via Knowledge Adapter

Week 8 — Knowledge Layer v1
"""

from .types import KnowledgeType, KnowledgeStatus, KnowledgeSourceType
from .models import (
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeSource,
    KnowledgeMetadata,
)
from .repository import KnowledgeRepository, InMemoryKnowledgeRepository
from .retrieval import KnowledgeRetrievalEngine, RetrievalResult
from .adapter import LLMKnowledgeAdapter, KnowledgeContext
from .observability import KnowledgeObservability, KnowledgeQueryMetric
from .embedding_contracts import (
    EmbeddingProvider,
    EmbeddingIndex,
    SemanticRetriever,
    EmbeddingVector,
    SemanticSearchResult,
    MockEmbeddingProvider,
    InMemoryEmbeddingIndex,
)

__all__ = [
    # Types
    "KnowledgeType",
    "KnowledgeStatus",
    "KnowledgeSourceType",
    # Models
    "KnowledgeDocument",
    "KnowledgeChunk",
    "KnowledgeCollection",
    "KnowledgeSource",
    "KnowledgeMetadata",
    # Repository
    "KnowledgeRepository",
    "InMemoryKnowledgeRepository",
    # Retrieval
    "KnowledgeRetrievalEngine",
    "RetrievalResult",
    # Adapter
    "LLMKnowledgeAdapter",
    "KnowledgeContext",
    # Observability
    "KnowledgeObservability",
    "KnowledgeQueryMetric",
    # Embedding Contracts (Part 8)
    "EmbeddingProvider",
    "EmbeddingIndex",
    "SemanticRetriever",
    "EmbeddingVector",
    "SemanticSearchResult",
    "MockEmbeddingProvider",
    "InMemoryEmbeddingIndex",
]
