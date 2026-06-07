"""
AraOS Clinical — Contracts.

Contratos para integração futura com:
    - Voice Copilot
    - Concierge IA
    - Knowledge Layer (pgvector, Qdrant, Neo4j, OpenAI, Gemini, Claude)

Apenas contratos. Sem implementação de IA/LLM/vector DB/graph DB.
"""

from .voice import VoiceClinicalAdapter
from .concierge import ConciergeClinicalAdapter
from .knowledge import (
    KnowledgeStore,
    VectorStore,
    GraphStore,
    ClinicalQuery,
    KnowledgeResult,
)

__all__ = [
    "VoiceClinicalAdapter",
    "ConciergeClinicalAdapter",
    "KnowledgeStore",
    "VectorStore",
    "GraphStore",
    "ClinicalQuery",
    "KnowledgeResult",
]
