"""
AraOS Knowledge — Patient Knowledge Source.

Integra Digital Twin, Clinical Timeline e Clinical Summary
como fontes de conhecimento na Knowledge Layer.

Week 8 — Knowledge Layer v1
"""

from typing import Optional, List
import uuid

from araos.knowledge.models import KnowledgeDocument, KnowledgeMetadata, KnowledgeChunk, KnowledgeSource
from araos.knowledge.types import KnowledgeType, KnowledgeSourceType
from araos.knowledge.repository import KnowledgeRepository

from araos.clinical.twin.models import PatientDigitalTwin
from araos.clinical.timeline.models import TimelineEntry
from araos.clinical.summary.engine import SummaryResult


def generate_id() -> str:
    return str(uuid.uuid4())


class PatientKnowledgeSource:
    """
    Fonte de conhecimento do paciente.
    
    Converte dados clínicos (Digital Twin, Timeline, Summary)
    em documentos de conhecimento indexáveis.
    
    Uso:
        source = PatientKnowledgeSource(repository, tenant_id)
        
        # Indexar twin
        source.index_digital_twin(twin)
        
        # Indexar timeline
        source.index_timeline_entries(patient_id, entries)
        
        # Buscar
        results = source.search(patient_id, "hipertensão")
    """
    
    def __init__(self, repository: KnowledgeRepository, tenant_id: str):
        self.repository = repository
        self.tenant_id = tenant_id
    
    def index_digital_twin(self, twin: PatientDigitalTwin) -> KnowledgeDocument:
        """
        Indexa Digital Twin como documento de conhecimento.
        
        O Digital Twin é a fonte primária de conhecimento do paciente.
        """
        content_parts = ["=== DIGITAL TWIN ==="]
        
        if twin.profile:
            content_parts.append(f"Paciente: {twin.patient_id}")
            
            if twin.active_diagnoses:
                content_parts.append("\nDiagnósticos:")
                for d in twin.active_diagnoses:
                    content_parts.append(f"  - {d.get('description', '')} ({d.get('icd10_code', '')})")
            
            if twin.active_medications:
                content_parts.append("\nMedicações:")
                for m in twin.active_medications:
                    content_parts.append(f"  - {m.get('name', '')} {m.get('dosage', '')}")
            
            if twin.allergies:
                content_parts.append("\nAlergias:")
                for a in twin.allergies:
                    content_parts.append(f"  - {a.get('substance', '')} [{a.get('severity', '')}]")
            
            if twin.risk_factors:
                content_parts.append("\nFatores de risco:")
                for r in twin.risk_factors:
                    content_parts.append(f"  - {r.get('factor_type', '')}")
        
        content = "\n".join(content_parts)
        
        doc = KnowledgeDocument(
            document_id=f"twin_{twin.patient_id}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PATIENT,
            source_type=KnowledgeSourceType.DIGITAL_TWIN,
            title=f"Digital Twin — Paciente {twin.patient_id}",
            content=content,
            metadata=KnowledgeMetadata(
                author_id="system",
                author_type="system",
                tags=["patient", "digital_twin", "clinical"],
            ),
            source=f"araos://clinical/twin/{twin.patient_id}",
        )
        
        doc.add_chunk(KnowledgeChunk(
            chunk_id=generate_id(),
            document_id=doc.document_id,
            content=content,
            chunk_index=0,
        ))
        
        self.repository.save_document(doc)
        return doc
    
    def index_timeline_entries(
        self,
        patient_id: str,
        entries: List[TimelineEntry],
    ) -> KnowledgeDocument:
        """
        Indexa entradas da timeline como documento de conhecimento.
        """
        content_parts = [f"=== TIMELINE — Paciente {patient_id} ==="]
        
        for entry in entries:
            content_parts.append(f"\n[{entry.event_type}] {entry.title}")
            if entry.description:
                content_parts.append(f"  {entry.description}")
            if entry.entity_data:
                content_parts.append(f"  Dados: {str(entry.entity_data)[:200]}")
        
        content = "\n".join(content_parts)
        
        doc = KnowledgeDocument(
            document_id=f"timeline_{patient_id}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PATIENT,
            source_type=KnowledgeSourceType.TIMELINE,
            title=f"Timeline — Paciente {patient_id}",
            content=content,
            metadata=KnowledgeMetadata(
                author_id="system",
                author_type="system",
                tags=["patient", "timeline", "history"],
            ),
            source=f"araos://clinical/timeline/{patient_id}",
        )
        
        # Criar chunks por entrada
        for i, entry in enumerate(entries):
            chunk_content = f"[{entry.event_type}] {entry.title}"
            if entry.description:
                chunk_content += f"\n{entry.description}"
            
            doc.add_chunk(KnowledgeChunk(
                chunk_id=generate_id(),
                document_id=doc.document_id,
                content=chunk_content,
                chunk_index=i,
            ))
        
        self.repository.save_document(doc)
        return doc
    
    def index_clinical_summary(
        self,
        patient_id: str,
        summary: SummaryResult,
    ) -> KnowledgeDocument:
        """
        Indexa resumo clínico como documento de conhecimento.
        """
        doc = KnowledgeDocument(
            document_id=f"summary_{patient_id}",
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PATIENT,
            source_type=KnowledgeSourceType.SUMMARY,
            title=f"Resumo Clínico — Paciente {patient_id}",
            content=summary.text,
            metadata=KnowledgeMetadata(
                author_id="system",
                author_type="system",
                tags=["patient", "summary", "clinical"],
            ),
            source=f"araos://clinical/summary/{patient_id}",
        )
        
        doc.add_chunk(KnowledgeChunk(
            chunk_id=generate_id(),
            document_id=doc.document_id,
            content=summary.text,
            chunk_index=0,
        ))
        
        self.repository.save_document(doc)
        return doc
    
    def search(self, patient_id: str, query: str) -> List[KnowledgeDocument]:
        """Busca no conhecimento do paciente."""
        # Buscar todos os documentos do tipo PATIENT
        all_patient_docs = self.repository.list_documents(
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PATIENT,
        )
        
        # Filtrar por patient_id
        patient_docs = [
            d for d in all_patient_docs
            if patient_id in d.document_id or patient_id in d.content
        ]
        
        # Aplicar busca por keyword
        query_lower = query.lower()
        results = []
        
        for doc in patient_docs:
            if query_lower in doc.title.lower() or query_lower in doc.content.lower():
                results.append(doc)
            else:
                for chunk in doc.chunks:
                    if query_lower in chunk.content.lower():
                        results.append(doc)
                        break
        
        return results
    
    def get_patient_knowledge(self, patient_id: str) -> List[KnowledgeDocument]:
        """Retorna todo o conhecimento indexado de um paciente."""
        all_patient_docs = self.repository.list_documents(
            tenant_id=self.tenant_id,
            knowledge_type=KnowledgeType.PATIENT,
        )
        
        return [
            d for d in all_patient_docs
            if patient_id in d.document_id
        ]
