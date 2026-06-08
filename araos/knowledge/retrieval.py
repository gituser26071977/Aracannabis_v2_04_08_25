"""
AraOS Knowledge — Retrieval Engine.

Motor de recuperação de conhecimento.

Week 8 — Knowledge Layer v1
Busca por keyword e metadata. Sem embeddings nesta etapa.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from .models import KnowledgeDocument, KnowledgeChunk
from .types import KnowledgeType, KnowledgeStatus
from .repository import KnowledgeRepository


@dataclass
class RetrievalResult:
    """
    Resultado de uma consulta de recuperação.
    
    Attributes:
        document: Documento encontrado
        matched_chunks: Chunks que corresponderam à busca
        score: Score de relevância (0.0 a 1.0)
        match_type: Tipo de match (title, content, chunk, metadata)
    """
    document: KnowledgeDocument
    matched_chunks: List[KnowledgeChunk] = field(default_factory=list)
    score: float = 0.0
    match_type: str = ""  # title, content, chunk, metadata, tag


class KnowledgeRetrievalEngine:
    """
    Motor de recuperação de conhecimento.
    
    Week 8: busca por keyword e metadata.
    Futuro: busca semântica com embeddings.
    
    Uso:
        engine = KnowledgeRetrievalEngine(repository)
        results = engine.search(
            tenant_id="tenant_001",
            query="protocolo de hipertensão",
            knowledge_type=KnowledgeType.CLINICAL,
        )
    """
    
    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository
    
    def search(
        self,
        tenant_id: str,
        query: str,
        knowledge_type: Optional[KnowledgeType] = None,
        status: Optional[KnowledgeStatus] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[RetrievalResult]:
        """
        Busca conhecimento por keyword e filtros.
        
        Args:
            tenant_id: ID do tenant
            query: Termos de busca
            knowledge_type: Filtrar por tipo
            status: Filtrar por status
            tags: Filtrar por tags
            limit: Máximo de resultados
        
        Returns:
            Lista de RetrievalResult ordenada por relevância
        """
        results: List[RetrievalResult] = []
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        # Buscar documentos do tenant
        documents = self.repository.list_documents(
            tenant_id=tenant_id,
            knowledge_type=knowledge_type,
            status=status or KnowledgeStatus.ACTIVE,
            tags=tags,
        )
        
        for doc in documents:
            result = self._score_document(doc, query_terms, query_lower)
            if result.score > 0:
                results.append(result)
        
        # Ordenar por score decrescente
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results[:limit]
    
    def _score_document(
        self,
        doc: KnowledgeDocument,
        query_terms: List[str],
        query_full: str,
    ) -> RetrievalResult:
        """
        Calcula score de relevância de um documento.
        
        Scoring heurístico (Week 8):
            - Match exato no título: +1.0
            - Termos no título: +0.5 por termo
            - Match exato no conteúdo: +0.3
            - Termos no conteúdo: +0.1 por termo
            - Match em chunk: +0.2
            - Match em tag: +0.4
        """
        score = 0.0
        matched_chunks = []
        match_types = []
        
        title_lower = doc.title.lower()
        content_lower = doc.content.lower()
        
        # Título
        if query_full in title_lower:
            score += 1.0
            match_types.append("title_exact")
        else:
            for term in query_terms:
                if term in title_lower:
                    score += 0.5
                    match_types.append("title_term")
        
        # Conteúdo
        if query_full in content_lower:
            score += 0.3
            match_types.append("content_exact")
        else:
            for term in query_terms:
                if term in content_lower:
                    score += 0.1
                    match_types.append("content_term")
        
        # Chunks
        for chunk in doc.chunks:
            chunk_lower = chunk.content.lower()
            if query_full in chunk_lower:
                score += 0.2
                matched_chunks.append(chunk)
                match_types.append("chunk")
                break
            else:
                for term in query_terms:
                    if term in chunk_lower:
                        score += 0.05
                        matched_chunks.append(chunk)
                        match_types.append("chunk_term")
                        break
        
        # Tags
        for term in query_terms:
            if any(term in tag.lower() for tag in doc.metadata.tags):
                score += 0.4
                match_types.append("tag")
        
        # Normalizar score para 0.0-1.0
        score = min(score, 1.0)
        
        return RetrievalResult(
            document=doc,
            matched_chunks=matched_chunks,
            score=round(score, 3),
            match_type=",".join(set(match_types)) if match_types else "none",
        )
    
    def get_document_by_id(self, document_id: str) -> Optional[KnowledgeDocument]:
        """Busca documento por ID."""
        return self.repository.get_document(document_id)
    
    def list_by_collection(
        self,
        collection_id: str,
    ) -> List[KnowledgeDocument]:
        """Lista documentos de uma coleção."""
        collection = self.repository.get_collection(collection_id)
        if not collection:
            return []
        
        documents = []
        for doc_id in collection.document_ids:
            doc = self.repository.get_document(doc_id)
            if doc:
                documents.append(doc)
        
        return documents
