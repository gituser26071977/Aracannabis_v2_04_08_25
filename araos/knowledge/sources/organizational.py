"""
AraOS Knowledge — Organizational Memory.

Armazena conhecimento institucional:
    - Protocolos
    - Fluxos internos
    - Documentos
    - FAQ
    - Políticas

Week 8 — Knowledge Layer v1
"""

from typing import List, Optional
import uuid

from araos.knowledge.models import KnowledgeDocument, KnowledgeMetadata, KnowledgeChunk
from araos.knowledge.types import KnowledgeType, KnowledgeSourceType, KnowledgeStatus
from araos.knowledge.repository import KnowledgeRepository


def generate_id() -> str:
    return str(uuid.uuid4())


class OrganizationalMemory:
    """
    Gerenciador de memória organizacional.
    
    Uso:
        memory = OrganizationalMemory(repository, tenant_id)
        
        # Adicionar protocolo
        memory.add_protocol(
            title="Protocolo de Hipertensão",
            content="1. Medir PA...",
            tags=["cardiologia", "protocolo"],
        )
        
        # Buscar
        results = memory.search("hipertensão")
    """
    
    def __init__(self, repository: KnowledgeRepository, tenant_id: str):
        self.repository = repository
        self.tenant_id = tenant_id
    
    def add_protocol(
        self,
        title: str,
        content: str,
        author_id: str = "system",
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Adiciona um protocolo clínico."""
        doc = KnowledgeDocument(
            document_id=generate_id(),
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title=title,
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="professional",
                tags=tags or ["protocol"],
            ),
        )
        self._chunk_document(doc)
        self.repository.save_document(doc)
        return doc
    
    def add_faq(
        self,
        question: str,
        answer: str,
        author_id: str = "system",
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Adiciona uma entrada de FAQ."""
        content = f"Q: {question}\nA: {answer}"
        doc = KnowledgeDocument(
            document_id=generate_id(),
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.ORGANIZATIONAL,
            source_type=KnowledgeSourceType.FAQ,
            title=question,
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="system",
                tags=tags or ["faq"],
            ),
        )
        self._chunk_document(doc)
        self.repository.save_document(doc)
        return doc
    
    def add_policy(
        self,
        title: str,
        content: str,
        author_id: str = "system",
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Adiciona uma política institucional."""
        doc = KnowledgeDocument(
            document_id=generate_id(),
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.ORGANIZATIONAL,
            source_type=KnowledgeSourceType.POLICY,
            title=title,
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="system",
                tags=tags or ["policy"],
            ),
        )
        self._chunk_document(doc)
        self.repository.save_document(doc)
        return doc
    
    def add_workflow(
        self,
        title: str,
        content: str,
        author_id: str = "system",
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Adiciona um fluxo de trabalho."""
        doc = KnowledgeDocument(
            document_id=generate_id(),
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.ORGANIZATIONAL,
            source_type=KnowledgeSourceType.WORKFLOW,
            title=title,
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="system",
                tags=tags or ["workflow"],
            ),
        )
        self._chunk_document(doc)
        self.repository.save_document(doc)
        return doc
    
    def search(self, query: str) -> List[KnowledgeDocument]:
        """Busca na memória organizacional."""
        return self.repository.search_by_keyword(
            tenant_id=self.tenant_id,
            query=query,
        )
    
    def _chunk_document(self, doc: KnowledgeDocument, chunk_size: int = 1000) -> None:
        """Divide documento em chunks."""
        content = doc.content
        if len(content) <= chunk_size:
            doc.add_chunk(KnowledgeChunk(
                chunk_id=generate_id(),
                document_id=doc.document_id,
                content=content,
                chunk_index=0,
            ))
            return
        
        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk_content = content[i:i + chunk_size]
            chunks.append(KnowledgeChunk(
                chunk_id=generate_id(),
                document_id=doc.document_id,
                content=chunk_content,
                chunk_index=len(chunks),
            ))
        
        for chunk in chunks:
            doc.add_chunk(chunk)
