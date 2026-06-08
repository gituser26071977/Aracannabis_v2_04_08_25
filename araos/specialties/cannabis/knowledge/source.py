"""
AraOS Cannabis Module — Knowledge Source.

Integração com a Knowledge Layer.

Week 11B — Cannabis Module V1
"""

from typing import Dict, Any, List

from araos.knowledge.models import KnowledgeDocument, KnowledgeMetadata, KnowledgeChunk
from araos.knowledge.types import KnowledgeType, KnowledgeSourceType
from araos.knowledge.repository import KnowledgeRepository


class CannabisKnowledgeSource:
    """
    Fonte de conhecimento do módulo Cannabis.

    Armazena e recupera:
        - protocolos
        - produtos
        - escalas
        - documentos
        - literatura institucional

    Integra ao Knowledge Layer via repository.
    """

    def __init__(self, repository: KnowledgeRepository, tenant_id: str):
        self.repository = repository
        self.tenant_id = tenant_id

    def index_protocol(
        self,
        title: str,
        content: str,
        protocol_type: str = "general",
        author_id: str = "system",
    ) -> KnowledgeDocument:
        """Indexa um protocolo clínico."""
        doc = KnowledgeDocument(
            document_id=f"cannabis_protocol_{title.lower().replace(' ', '_')}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title=f"[Cannabis] Protocolo: {title}",
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="system",
                tags=["cannabis", "protocol", protocol_type],
            ),
            source=f"araos://specialty/cannabis/protocol/{protocol_type}",
        )
        self.repository.save_document(doc)
        return doc

    def index_product_info(
        self,
        product_name: str,
        manufacturer: str,
        formulation: str,
        spectrum: str,
        cbd_mg: float,
        thc_mg: float,
        content: str = "",
    ) -> KnowledgeDocument:
        """Indexa informação de produto."""
        doc = KnowledgeDocument(
            document_id=f"cannabis_product_{product_name.lower().replace(' ', '_')}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.DOCUMENT,
            title=f"[Cannabis] Produto: {product_name}",
            content=content or f"Produto: {product_name}\nFabricante: {manufacturer}\nFormulação: {formulation}\nEspectro: {spectrum}\nCBD: {cbd_mg}mg\nTHC: {thc_mg}mg",
            metadata=KnowledgeMetadata(
                author_id="system",
                author_type="system",
                tags=["cannabis", "product", formulation, spectrum],
            ),
            source=f"araos://specialty/cannabis/product/{product_name}",
        )
        self.repository.save_document(doc)
        return doc

    def index_scale(
        self,
        scale_name: str,
        scale_description: str,
        items: List[str],
    ) -> KnowledgeDocument:
        """Indexa uma escala de avaliação."""
        content_lines = [f"Escala: {scale_name}", "", scale_description, "", "Itens:"]
        for i, item in enumerate(items, 1):
            content_lines.append(f"  {i}. {item}")

        doc = KnowledgeDocument(
            document_id=f"cannabis_scale_{scale_name.lower().replace(' ', '_')}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.DOCUMENT,
            title=f"[Cannabis] Escala: {scale_name}",
            content="\n".join(content_lines),
            metadata=KnowledgeMetadata(
                author_id="system",
                author_type="system",
                tags=["cannabis", "scale", "assessment"],
            ),
            source=f"araos://specialty/cannabis/scale/{scale_name}",
        )
        self.repository.save_document(doc)
        return doc

    def search(self, query: str) -> List[KnowledgeDocument]:
        """Busca no conhecimento do módulo Cannabis."""
        results = self.repository.search_by_keyword(
            tenant_id=self.tenant_id,
            query=query,
        )
        return [doc for doc in results if "cannabis" in doc.metadata.tags]

    def get_all_cannabis_knowledge(self) -> List[KnowledgeDocument]:
        """Retorna todo o conhecimento indexado do módulo."""
        all_docs = self.repository.list_documents(tenant_id=self.tenant_id)
        return [doc for doc in all_docs if "cannabis" in doc.metadata.tags]
