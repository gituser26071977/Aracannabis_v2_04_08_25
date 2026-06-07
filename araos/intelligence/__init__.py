"""
AraOS Intelligence — Provider Contracts.

Preparação para integração futura com:
    - LLMs (OpenAI, Gemini, Claude)
    - Embedding models
    - Vector stores (pgvector, Qdrant)

Apenas contratos. Sem implementação.
"""

from .llm import LLMProvider, LLMMessage, LLMResponse
from .embeddings import EmbeddingProvider, EmbeddingResult
from .vector import VectorStoreProvider, VectorSearchResult

__all__ = [
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "EmbeddingProvider",
    "EmbeddingResult",
    "VectorStoreProvider",
    "VectorSearchResult",
]
