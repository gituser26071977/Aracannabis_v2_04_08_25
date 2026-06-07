"""
AraOS Clinical — Knowledge Layer Contracts.

Preparação para integração futura com:
    - pgvector (PostgreSQL vector extension)
    - Qdrant (vector database)
    - Neo4j (graph database)
    - OpenAI, Gemini, Claude (LLMs)

Apenas contratos. Sem implementação.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ClinicalQuery:
    """Query clínica para o knowledge layer."""
    text: str
    patient_id: Optional[str] = None
    tenant_id: Optional[str] = None
    query_type: str = "retrieval"  # retrieval, reasoning, summarization
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None


@dataclass
class KnowledgeResult:
    """Resultado de uma query ao knowledge layer."""
    text: str
    sources: List[Dict[str, Any]]
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorStore(ABC):
    """
    Contrato para vector store.
    
    Implementações futuras:
        - PGVectorStore (pgvector)
        - QdrantStore (Qdrant)
        - InMemoryVectorStore (testes)
    """
    
    @abstractmethod
    async def index(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """Indexa documento com embeddings."""
        ...
    
    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> List[KnowledgeResult]:
        """Busca semanticamente similar."""
        ...
    
    @abstractmethod
    async def delete(self, document_id: str) -> None:
        """Remove documento do índice."""
        ...


class GraphStore(ABC):
    """
    Contrato para graph store.
    
    Implementações futuras:
        - Neo4jGraphStore
        - InMemoryGraphStore (testes)
    """
    
    @abstractmethod
    async def add_node(self, node_id: str, labels: List[str], properties: Dict[str, Any]) -> None:
        """Adiciona nó ao grafo."""
        ...
    
    @abstractmethod
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Dict[str, Any],
    ) -> None:
        """Adiciona relacionamento ao grafo."""
        ...
    
    @abstractmethod
    async def query(self, cypher: str) -> List[Dict[str, Any]]:
        """Executa query Cypher."""
        ...


class KnowledgeStore(ABC):
    """
    Contrato unificado para knowledge layer.
    
    Combina vector store + graph store + LLM futuro.
    """
    
    @abstractmethod
    async def query(self, query: ClinicalQuery) -> KnowledgeResult:
        """Executa query clínica."""
        ...
    
    @abstractmethod
    async def index_patient(self, patient_id: str) -> None:
        """Indexa todo o conhecimento de um paciente."""
        ...
    
    @abstractmethod
    async def index_document(self, document_id: str, text: str, metadata: Dict[str, Any]) -> None:
        """Indexa documento clínico."""
        ...
