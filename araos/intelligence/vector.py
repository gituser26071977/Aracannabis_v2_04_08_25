"""
AraOS Intelligence — Vector Store Provider Contract.

Preparação para integração com vector stores:
    - pgvector (PostgreSQL)
    - Qdrant
    - Pinecone
    - Weaviate

Apenas contrato. Sem implementação.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    """Resultado de busca vetorial."""
    document_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorStoreProvider(ABC):
    """
    Contrato para vector stores.
    
    Implementações futuras:
        - PGVectorProvider
        - QdrantProvider
        - PineconeProvider
    """
    
    @abstractmethod
    async def index(
        self,
        document_id: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Indexa documento com embedding."""
        ...
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Busca por similaridade vetorial."""
        ...
    
    @abstractmethod
    async def delete(self, document_id: str) -> None:
        """Remove documento do índice."""
        ...
    
    @abstractmethod
    async def health(self) -> bool:
        """Verifica saúde do vector store."""
        ...
