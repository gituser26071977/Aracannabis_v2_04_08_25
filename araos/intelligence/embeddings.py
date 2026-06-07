"""
AraOS Intelligence — Embedding Provider Contract.

Preparação para integração com modelos de embedding.
Apenas contrato. Sem implementação.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Resultado de embedding."""
    text: str
    embedding: List[float]
    model: str
    dimensions: int
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EmbeddingProvider(ABC):
    """
    Contrato para providers de embeddings.
    
    Implementações futuras:
        - OpenAIEmbeddingProvider
        - SentenceTransformersProvider
        - HuggingFaceProvider
    """
    
    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """Gera embedding para texto."""
        ...
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Gera embeddings em batch."""
        ...
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Retorna dimensão dos vetores."""
        ...
