"""
AraOS Knowledge — Repository.

Persistência e recuperação de objetos de conhecimento.

Week 8 — Knowledge Layer v1
"""

from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from .models import KnowledgeDocument, KnowledgeCollection, KnowledgeChunk, KnowledgeSource
from .types import KnowledgeType, KnowledgeStatus, KnowledgeSourceType


class KnowledgeRepository(ABC):
    """
    Contrato para repositório de conhecimento.
    
    Implementações:
        - InMemoryKnowledgeRepository: testes/demos
        - PostgresKnowledgeRepository: produção (futuro)
    """
    
    @abstractmethod
    def save_document(self, document: KnowledgeDocument) -> None:
        ...
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        ...
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        ...
    
    @abstractmethod
    def list_documents(
        self,
        tenant_id: str,
        knowledge_type: Optional[KnowledgeType] = None,
        status: Optional[KnowledgeStatus] = None,
        tags: Optional[List[str]] = None,
    ) -> List[KnowledgeDocument]:
        ...
    
    @abstractmethod
    def search_by_keyword(
        self,
        tenant_id: str,
        query: str,
        knowledge_type: Optional[KnowledgeType] = None,
    ) -> List[KnowledgeDocument]:
        ...
    
    @abstractmethod
    def save_collection(self, collection: KnowledgeCollection) -> None:
        ...
    
    @abstractmethod
    def get_collection(self, collection_id: str) -> Optional[KnowledgeCollection]:
        ...
    
    @abstractmethod
    def list_collections(self, tenant_id: str) -> List[KnowledgeCollection]:
        ...


class InMemoryKnowledgeRepository(KnowledgeRepository):
    """
    Repositório em memória para testes e demonstrações.
    """
    
    def __init__(self):
        self._documents: Dict[str, KnowledgeDocument] = {}
        self._collections: Dict[str, KnowledgeCollection] = {}
        self._sources: Dict[str, KnowledgeSource] = {}
    
    def save_document(self, document: KnowledgeDocument) -> None:
        self._documents[document.document_id] = document
    
    def get_document(self, document_id: str) -> Optional[KnowledgeDocument]:
        return self._documents.get(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False
    
    def list_documents(
        self,
        tenant_id: str,
        knowledge_type: Optional[KnowledgeType] = None,
        status: Optional[KnowledgeStatus] = None,
        tags: Optional[List[str]] = None,
    ) -> List[KnowledgeDocument]:
        results = [
            d for d in self._documents.values()
            if d.tenant_id == tenant_id
        ]
        
        if knowledge_type:
            results = [d for d in results if d.knowledge_type == knowledge_type]
        
        if status:
            results = [d for d in results if d.status == status]
        
        if tags:
            results = [
                d for d in results
                if any(tag in d.metadata.tags for tag in tags)
            ]
        
        return results
    
    def search_by_keyword(
        self,
        tenant_id: str,
        query: str,
        knowledge_type: Optional[KnowledgeType] = None,
    ) -> List[KnowledgeDocument]:
        """
        Busca por keyword em título e conteúdo.
        
        Week 8: busca simples por substring.
        Futuro: busca semântica com embeddings.
        """
        query_lower = query.lower()
        results = []
        
        for doc in self._documents.values():
            if doc.tenant_id != tenant_id:
                continue
            
            if knowledge_type and doc.knowledge_type != knowledge_type:
                continue
            
            if doc.status != KnowledgeStatus.ACTIVE:
                continue
            
            # Busca em título e conteúdo
            if query_lower in doc.title.lower() or query_lower in doc.content.lower():
                results.append(doc)
                continue
            
            # Busca em chunks
            for chunk in doc.chunks:
                if query_lower in chunk.content.lower():
                    results.append(doc)
                    break
        
        return results
    
    def save_collection(self, collection: KnowledgeCollection) -> None:
        self._collections[collection.collection_id] = collection
    
    def get_collection(self, collection_id: str) -> Optional[KnowledgeCollection]:
        return self._collections.get(collection_id)
    
    def list_collections(self, tenant_id: str) -> List[KnowledgeCollection]:
        return [
            c for c in self._collections.values()
            if c.tenant_id == tenant_id
        ]
    
    def save_source(self, source: KnowledgeSource) -> None:
        self._sources[source.source_id] = source
    
    def get_source(self, source_id: str) -> Optional[KnowledgeSource]:
        return self._sources.get(source_id)
    
    def clear(self) -> None:
        self._documents.clear()
        self._collections.clear()
        self._sources.clear()
