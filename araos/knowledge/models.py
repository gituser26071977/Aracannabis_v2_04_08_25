"""
AraOS Knowledge — Knowledge Objects.

Modelos de dados da Knowledge Layer.

Week 8 — Knowledge Layer v1
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .types import KnowledgeType, KnowledgeStatus, KnowledgeSourceType


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class KnowledgeMetadata:
    """
    Metadados de um objeto de conhecimento.
    
    Attributes:
        author_id: Quem criou o conhecimento
        author_type: Tipo do autor (user, agent, system)
        created_at: Data de criação
        updated_at: Data de última atualização
        version: Versão do documento
        tags: Tags para categorização
        language: Idioma (pt, en, etc.)
        confidentiality: Nível de confidencialidade
    """
    author_id: str = ""
    author_type: str = "system"
    created_at: datetime = field(default_factory=now_utc)
    updated_at: datetime = field(default_factory=now_utc)
    version: int = 1
    tags: List[str] = field(default_factory=list)
    language: str = "pt"
    confidentiality: str = "normal"  # normal, restricted, confidential
    
    def bump_version(self) -> None:
        """Incrementa versão e atualiza timestamp."""
        self.version += 1
        self.updated_at = now_utc()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "author_id": self.author_id,
            "author_type": self.author_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "tags": self.tags,
            "language": self.language,
            "confidentiality": self.confidentiality,
        }


@dataclass
class KnowledgeChunk:
    """
    Fragmento de conhecimento.
    
    Um documento é dividido em chunks para indexação e recuperação.
    
    Attributes:
        chunk_id: ID único do chunk
        document_id: ID do documento pai
        content: Conteúdo textual do chunk
        chunk_index: Índice sequencial no documento
        metadata: Metadados específicos do chunk
    """
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }


@dataclass
class KnowledgeDocument:
    """
    Documento de conhecimento.
    
    A unidade principal de armazenamento na Knowledge Layer.
    
    Attributes:
        document_id: ID único
        tenant_id: ID da organização
        knowledge_type: Tipo de conhecimento
        source_type: Tipo de fonte
        title: Título do documento
        content: Conteúdo completo
        chunks: Fragmentos do documento
        metadata: Metadados
        status: Status atual
        source: Origem do conhecimento
    """
    document_id: str
    tenant_id: str
    knowledge_type: KnowledgeType
    source_type: KnowledgeSourceType
    title: str
    content: str
    chunks: List[KnowledgeChunk] = field(default_factory=list)
    metadata: KnowledgeMetadata = field(default_factory=KnowledgeMetadata)
    status: KnowledgeStatus = KnowledgeStatus.ACTIVE
    source: Optional[str] = None  # URI, path, ou identificador da fonte
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "knowledge_type": self.knowledge_type.value,
            "source_type": self.source_type.value,
            "title": self.title,
            "content_preview": self.content[:300] + "..." if len(self.content) > 300 else self.content,
            "chunk_count": len(self.chunks),
            "metadata": self.metadata.to_dict(),
            "status": self.status.value,
            "source": self.source,
        }
    
    def add_chunk(self, chunk: KnowledgeChunk) -> None:
        """Adiciona um chunk ao documento."""
        self.chunks.append(chunk)
    
    def archive(self) -> None:
        """Arquiva o documento."""
        self.status = KnowledgeStatus.ARCHIVED
    
    def deprecate(self) -> None:
        """Marca como deprecado."""
        self.status = KnowledgeStatus.DEPRECATED


@dataclass
class KnowledgeCollection:
    """
    Coleção de documentos de conhecimento.
    
    Agrupa documentos relacionados (ex: "Protocolos de Cardiologia",
    "Templates do Dr. Silva").
    
    Attributes:
        collection_id: ID único
        tenant_id: ID da organização
        name: Nome da coleção
        description: Descrição
        knowledge_type: Tipo predominante
        document_ids: IDs dos documentos
        metadata: Metadados
    """
    collection_id: str
    tenant_id: str
    name: str
    description: str = ""
    knowledge_type: KnowledgeType = KnowledgeType.ORGANIZATIONAL
    document_ids: List[str] = field(default_factory=list)
    metadata: KnowledgeMetadata = field(default_factory=KnowledgeMetadata)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "collection_id": self.collection_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "description": self.description,
            "knowledge_type": self.knowledge_type.value,
            "document_count": len(self.document_ids),
            "metadata": self.metadata.to_dict(),
        }
    
    def add_document(self, document_id: str) -> None:
        """Adiciona documento à coleção."""
        if document_id not in self.document_ids:
            self.document_ids.append(document_id)
    
    def remove_document(self, document_id: str) -> None:
        """Remove documento da coleção."""
        if document_id in self.document_ids:
            self.document_ids.remove(document_id)


@dataclass
class KnowledgeSource:
    """
    Fonte de conhecimento.
    
    Representa uma origem de dados que alimenta a Knowledge Layer.
    
    Attributes:
        source_id: ID único
        tenant_id: ID da organização
        name: Nome da fonte
        source_type: Tipo de fonte
        config: Configuração da fonte
        last_sync: Última sincronização
        document_count: Quantidade de documentos
    """
    source_id: str
    tenant_id: str
    name: str
    source_type: KnowledgeSourceType
    config: Dict[str, Any] = field(default_factory=dict)
    last_sync: Optional[datetime] = None
    document_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "source_type": self.source_type.value,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "document_count": self.document_count,
        }
    
    def mark_synced(self) -> None:
        """Marca fonte como sincronizada."""
        self.last_sync = now_utc()
