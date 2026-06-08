"""
AraOS Knowledge — Embedding Contracts.

Contratos abstratos para busca semântica.
Sem implementação real nesta etapa (Week 8).

Preparação para:
    - PGVector (PostgreSQL extension)
    - Qdrant
    - Pinecone
    - Weaviate

Week 8 — Knowledge Layer v1 (Part 8)
"""

from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmbeddingVector:
    """Vetor de embedding com metadados."""
    id: str
    vector: List[float]
    metadata: Dict[str, Any]
    document_id: str
    chunk_index: int = 0


@dataclass
class SemanticSearchResult:
    """Resultado de busca semântica."""
    document_id: str
    chunk_index: int
    score: float  # cosine similarity
    metadata: Dict[str, Any]


class EmbeddingProvider(ABC):
    """
    Contrato para provedor de embeddings.
    
    Responsabilidade: gerar vetores numéricos a partir de texto.
    
    Implementações futuras:
        - OpenAIEmbeddingProvider (text-embedding-ada-002)
        - LocalEmbeddingProvider (sentence-transformers)
        - HuggingFaceEmbeddingProvider
    """
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Gera embedding para um texto."""
        ...
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Gera embeddings para múltiplos textos."""
        ...
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensão dos vetores gerados."""
        ...
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Nome do modelo de embedding."""
        ...


class EmbeddingIndex(ABC):
    """
    Contrato para índice de embeddings.
    
    Responsabilidade: armazenar e buscar vetores de embedding.
    
    Implementações futuras:
        - PGVectorIndex (PostgreSQL + pgvector)
        - QdrantIndex
        - PineconeIndex
        - InMemoryEmbeddingIndex (testes)
    """
    
    @abstractmethod
    async def index(self, vectors: List[EmbeddingVector]) -> None:
        """Indexa vetores no store."""
        ...
    
    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SemanticSearchResult]:
        """
        Busca os vetores mais similares.
        
        Args:
            query_vector: Vetor de consulta
            top_k: Número de resultados
            filters: Filtros de metadata (ex: {"tenant_id": "t1"})
        """
        ...
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Remove todos os vetores de um documento."""
        ...
    
    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Retorna status do índice."""
        ...


class SemanticRetriever(ABC):
    """
    Contrato para recuperador semântico.
    
    Responsabilidade: orquestrar embedding + índice para busca semântica.
    
    Este é o componente de alto nível que será usado pelo
    KnowledgeRetrievalEngine quando embeddings estiverem disponíveis.
    """
    
    @abstractmethod
    async def retrieve_by_embedding(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        knowledge_types: Optional[List[str]] = None,
    ) -> List[SemanticSearchResult]:
        """
        Recupera documentos por similaridade semântica.
        
        Fluxo:
            1. Gera embedding da query via EmbeddingProvider
            2. Busca no EmbeddingIndex
            3. Retorna resultados ordenados por score
        """
        ...
    
    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        top_k: int = 5,
        knowledge_types: Optional[List[str]] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> List[SemanticSearchResult]:
        """
        Busca híbrida: combina semântica + keyword.
        
        Args:
            semantic_weight: Peso da busca semântica (0.0-1.0)
            keyword_weight: Peso da busca por keyword (0.0-1.0)
        """
        ...


# ═══════════════════════════════════════════════════════════════════════
# Stubs para testes e desenvolvimento
# ═══════════════════════════════════════════════════════════════════════

class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock de EmbeddingProvider para testes.
    
    Gera vetores determinísticos baseados no hash do texto.
    """
    
    def __init__(self, dimension: int = 384):
        self._dimension = dimension
    
    async def embed(self, text: str) -> List[float]:
        import hashlib
        # Vetor determinístico baseado no hash do texto
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        import random
        rng = random.Random(seed)
        vector = [rng.uniform(-1, 1) for _ in range(self._dimension)]
        # Normalizar
        norm = sum(x * x for x in vector) ** 0.5
        return [x / norm for x in vector] if norm > 0 else vector
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.embed(t) for t in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return "mock-embedding-v1"


class InMemoryEmbeddingIndex(EmbeddingIndex):
    """
    Índice de embeddings em memória para testes.
    
    Busca por força bruta (cálculo de cosine similarity).
    Não usar em produção.
    """
    
    def __init__(self):
        self._vectors: Dict[str, EmbeddingVector] = {}
    
    async def index(self, vectors: List[EmbeddingVector]) -> None:
        for v in vectors:
            self._vectors[v.id] = v
    
    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SemanticSearchResult]:
        results = []
        
        for v in self._vectors.values():
            # Aplicar filtros
            if filters:
                skip = False
                for key, value in filters.items():
                    if v.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue
            
            # Cosine similarity
            score = self._cosine_similarity(query_vector, v.vector)
            results.append(SemanticSearchResult(
                document_id=v.document_id,
                chunk_index=v.chunk_index,
                score=score,
                metadata=v.metadata,
            ))
        
        # Ordenar por score decrescente
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]
    
    async def delete(self, document_id: str) -> bool:
        ids_to_remove = [
            vid for vid, v in self._vectors.items()
            if v.document_id == document_id
        ]
        for vid in ids_to_remove:
            del self._vectors[vid]
        return len(ids_to_remove) > 0
    
    async def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "vector_count": len(self._vectors),
            "backend": "in_memory",
        }
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
