"""
AraOS Knowledge — Professional Memory.

Armazena conhecimento do profissional:
    - Templates
    - Modelos de laudo
    - Preferências do médico
    - Checklists

Week 8 — Knowledge Layer v1
"""

from typing import List, Optional
import uuid

from araos.knowledge.models import KnowledgeDocument, KnowledgeMetadata, KnowledgeChunk
from araos.knowledge.types import KnowledgeType, KnowledgeSourceType
from araos.knowledge.repository import KnowledgeRepository


def generate_id() -> str:
    return str(uuid.uuid4())


class ProfessionalMemory:
    """
    Gerenciador de memória profissional.
    
    Uso:
        memory = ProfessionalMemory(repository, tenant_id, professional_id)
        
        # Adicionar template
        memory.add_template(
            title="Template de Evolução",
            content="Paciente refere...",
        )
        
        # Buscar templates
        results = memory.search("evolução")
    """
    
    def __init__(
        self,
        repository: KnowledgeRepository,
        tenant_id: str,
        professional_id: str,
    ):
        self.repository = repository
        self.tenant_id = tenant_id
        self.professional_id = professional_id
    
    def add_template(
        self,
        title: str,
        content: str,
        specialty: str = "",
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Adiciona um template de documento."""
        doc = KnowledgeDocument(
            document_id=generate_id(),
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PROFESSIONAL,
            source_type=KnowledgeSourceType.TEMPLATE,
            title=title,
            content=content,
            metadata=KnowledgeMetadata(
                author_id=self.professional_id,
                author_type="professional",
                tags=tags or ["template", specialty] if specialty else ["template"],
            ),
        )
        self._chunk_document(doc)
        self.repository.save_document(doc)
        return doc
    
    def add_checklist(
        self,
        title: str,
        items: List[str],
        specialty: str = "",
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Adiciona um checklist."""
        content = "\n".join(f"- [ ] {item}" for item in items)
        doc = KnowledgeDocument(
            document_id=generate_id(),
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PROFESSIONAL,
            source_type=KnowledgeSourceType.CHECKLIST,
            title=title,
            content=content,
            metadata=KnowledgeMetadata(
                author_id=self.professional_id,
                author_type="professional",
                tags=tags or ["checklist", specialty] if specialty else ["checklist"],
            ),
        )
        self._chunk_document(doc)
        self.repository.save_document(doc)
        return doc
    
    def add_preference(
        self,
        key: str,
        value: str,
        tags: Optional[List[str]] = None,
    ) -> KnowledgeDocument:
        """Adiciona uma preferência do profissional."""
        doc = KnowledgeDocument(
            document_id=generate_id(),
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PROFESSIONAL,
            source_type=KnowledgeSourceType.DOCUMENT,
            title=f"Preferência: {key}",
            content=f"{key}: {value}",
            metadata=KnowledgeMetadata(
                author_id=self.professional_id,
                author_type="professional",
                tags=tags or ["preference"],
            ),
        )
        self.repository.save_document(doc)
        return doc
    
    def search(self, query: str) -> List[KnowledgeDocument]:
        """Busca na memória profissional."""
        return self.repository.search_by_keyword(
            tenant_id=self.tenant_id,
            query=query,
            knowledge_type=KnowledgeType.PROFESSIONAL,
        )
    
    def list_templates(self) -> List[KnowledgeDocument]:
        """Lista todos os templates."""
        return self.repository.list_documents(
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PROFESSIONAL,
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
