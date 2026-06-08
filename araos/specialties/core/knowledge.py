"""
AraOS Specialty Framework — Specialty Knowledge.

Integração da Knowledge Layer com especialidades.

Week 10 — Specialty Framework Foundation
"""

from typing import Dict, Any, List, Optional

from araos.knowledge.models import KnowledgeDocument, KnowledgeMetadata, KnowledgeChunk
from araos.knowledge.types import KnowledgeType, KnowledgeSourceType
from araos.knowledge.repository import KnowledgeRepository

from .definitions import SpecialtyDefinition, SpecialtyCapability
from .protocol import SpecialtyProtocol


class SpecialtyKnowledgeSource:
    """
    Fonte de conhecimento especializado.

    Integra a Knowledge Layer com especialidades médicas.
    Cada especialidade pode possuir protocolos, templates, escalas,
    documentos e recomendações.

    Uso:
        source = SpecialtyKnowledgeSource(repository, tenant_id)

        # Indexar protocolo
        source.index_protocol(cannabis_protocol)

        # Indexar template
        source.index_template("cannabis", "Evolução Cannabis", "Paciente em uso de...")

        # Buscar
        docs = source.search("cannabis", "protocolo dose")
    """

    def __init__(self, repository: KnowledgeRepository, tenant_id: str):
        self.repository = repository
        self.tenant_id = tenant_id

    def index_protocol(self, protocol: SpecialtyProtocol, author_id: str = "system") -> KnowledgeDocument:
        """
        Indexa um protocolo especializado como conhecimento.
        """
        content_lines = [
            f"Protocolo: {protocol.name}",
            f"Especialidade: {protocol.specialty_code}",
            f"Versão: {protocol.version}",
            "",
            protocol.description,
            "",
            "Passos:",
        ]

        for step in protocol.get_steps_ordered():
            content_lines.append(f"  {step.order}. [{step.step_type.value}] {step.title}")
            if step.description:
                content_lines.append(f"     {step.description}")

        content = "\n".join(content_lines)

        doc = KnowledgeDocument(
            document_id=f"protocol_{protocol.protocol_id}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title=f"Protocolo: {protocol.name}",
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="system",
                tags=[
                    "specialty",
                    protocol.specialty_code,
                    "protocol",
                ],
            ),
            source=f"araos://specialty/{protocol.specialty_code}/protocol/{protocol.protocol_id}",
        )

        # Chunk por passo
        for step in protocol.get_steps_ordered():
            chunk_content = f"{step.title}\n{step.description}"
            doc.add_chunk(KnowledgeChunk(
                chunk_id=f"chunk_{step.step_id}",
                document_id=doc.document_id,
                content=chunk_content,
                chunk_index=step.order,
            ))

        self.repository.save_document(doc)
        return doc

    def index_template(
        self,
        specialty_code: str,
        title: str,
        content: str,
        template_type: str = "document",
        author_id: str = "system",
    ) -> KnowledgeDocument:
        """
        Indexa um template especializado.
        """
        doc = KnowledgeDocument(
            document_id=f"template_{specialty_code}_{title.lower().replace(' ', '_')}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PROFESSIONAL,
            source_type=KnowledgeSourceType.TEMPLATE,
            title=f"Template ({specialty_code}): {title}",
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="system",
                tags=["specialty", specialty_code, "template", template_type],
            ),
            source=f"araos://specialty/{specialty_code}/template/{template_type}",
        )

        doc.add_chunk(KnowledgeChunk(
            chunk_id=f"chunk_{doc.document_id}_0",
            document_id=doc.document_id,
            content=content,
            chunk_index=0,
        ))

        self.repository.save_document(doc)
        return doc

    def index_scale_document(
        self,
        specialty_code: str,
        scale_name: str,
        scale_description: str,
        items: List[str],
        author_id: str = "system",
    ) -> KnowledgeDocument:
        """
        Indexa uma escala de avaliação como documento de conhecimento.
        """
        content_lines = [
            f"Escala: {scale_name}",
            f"Especialidade: {specialty_code}",
            "",
            scale_description,
            "",
            "Itens:",
        ]
        for i, item in enumerate(items, 1):
            content_lines.append(f"  {i}. {item}")

        content = "\n".join(content_lines)

        doc = KnowledgeDocument(
            document_id=f"scale_{specialty_code}_{scale_name.lower().replace(' ', '_')}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.DOCUMENT,
            title=f"Escala ({specialty_code}): {scale_name}",
            content=content,
            metadata=KnowledgeMetadata(
                author_id=author_id,
                author_type="system",
                tags=["specialty", specialty_code, "scale", "assessment"],
            ),
            source=f"araos://specialty/{specialty_code}/scale/{scale_name}",
        )

        self.repository.save_document(doc)
        return doc

    def search(self, specialty_code: str, query: str) -> List[KnowledgeDocument]:
        """
        Busca no conhecimento de uma especialidade.
        """
        results = self.repository.search_by_keyword(
            tenant_id=self.tenant_id,
            query=query,
        )

        # Filtrar por specialty_code nas tags
        return [
            doc for doc in results
            if specialty_code in doc.metadata.tags
        ]

    def get_specialty_knowledge(self, specialty_code: str) -> List[KnowledgeDocument]:
        """
        Retorna todo o conhecimento indexado de uma especialidade.
        """
        all_docs = self.repository.list_documents(tenant_id=self.tenant_id)
        return [
            doc for doc in all_docs
            if specialty_code in doc.metadata.tags
        ]
