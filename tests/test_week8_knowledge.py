"""
AraOS Week 8 — Knowledge Layer v1 Tests

Valida:
    1. Knowledge Objects (Document, Chunk, Collection, Source, Metadata)
    2. Knowledge Types (CLINICAL, PROFESSIONAL, ORGANIZATIONAL, PATIENT, SYSTEM)
    3. Repository (CRUD, busca keyword)
    4. Retrieval Engine (scoring, filtros)
    5. Organizational Memory (protocolos, FAQ, políticas, workflows)
    6. Professional Memory (templates, checklists, preferências)
    7. Patient Knowledge (integração com Digital Twin, Timeline, Summary)
    8. LLM Knowledge Adapter (Knowledge → Context → LLM)
    9. Observabilidade (métricas de consulta)
    10. Embedding Contracts (stubs para semantic search futuro)
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from araos.knowledge.types import KnowledgeType, KnowledgeStatus, KnowledgeSourceType
from araos.knowledge.models import (
    KnowledgeDocument, KnowledgeChunk, KnowledgeCollection,
    KnowledgeSource, KnowledgeMetadata,
)
from araos.knowledge.repository import InMemoryKnowledgeRepository
from araos.knowledge.retrieval import KnowledgeRetrievalEngine, RetrievalResult
from araos.knowledge.sources.organizational import OrganizationalMemory
from araos.knowledge.sources.professional import ProfessionalMemory
from araos.knowledge.sources.patient import PatientKnowledgeSource
from araos.knowledge.adapter import LLMKnowledgeAdapter, KnowledgeContext
from araos.knowledge.observability import KnowledgeObservability
from araos.knowledge.embedding_contracts import (
    MockEmbeddingProvider,
    InMemoryEmbeddingIndex,
    EmbeddingVector,
    SemanticSearchResult,
)

from araos.demo.demo_base import DemoEnvironment
from araos.clinical.twin.models import PatientDigitalTwinBuilder
from araos.clinical.summary.engine import ClinicalSummaryEngine


@pytest.fixture
def repo():
    return InMemoryKnowledgeRepository()


@pytest.fixture
def env():
    e = DemoEnvironment().setup()
    yield e
    e.teardown()


# ═══════════════════════════════════════════════════════════════════════
# PART 1: Knowledge Objects
# ═══════════════════════════════════════════════════════════════════════

class TestKnowledgeObjects:
    """Valida objetos de conhecimento."""
    
    def test_knowledge_document_creation(self):
        doc = KnowledgeDocument(
            document_id="doc_001",
            tenant_id="tenant_001",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo de HAS",
            content="1. Medir PA...",
        )
        assert doc.document_id == "doc_001"
        assert doc.knowledge_type == KnowledgeType.CLINICAL
        assert doc.status == KnowledgeStatus.ACTIVE
    
    def test_knowledge_chunk_creation(self):
        chunk = KnowledgeChunk(
            chunk_id="chunk_001",
            document_id="doc_001",
            content="Medir PA em ambos os braços",
            chunk_index=0,
        )
        assert chunk.chunk_id == "chunk_001"
        assert chunk.chunk_index == 0
    
    def test_knowledge_collection(self):
        coll = KnowledgeCollection(
            collection_id="coll_001",
            tenant_id="tenant_001",
            name="Protocolos Cardiologia",
        )
        coll.add_document("doc_001")
        coll.add_document("doc_002")
        assert len(coll.document_ids) == 2
        
        coll.remove_document("doc_001")
        assert len(coll.document_ids) == 1
    
    def test_knowledge_metadata_versioning(self):
        meta = KnowledgeMetadata(version=1)
        meta.bump_version()
        assert meta.version == 2
    
    def test_document_archive(self):
        doc = KnowledgeDocument(
            document_id="doc_001",
            tenant_id="tenant_001",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Test",
            content="Test",
        )
        doc.archive()
        assert doc.status == KnowledgeStatus.ARCHIVED


# ═══════════════════════════════════════════════════════════════════════
# PART 2: Knowledge Types
# ═══════════════════════════════════════════════════════════════════════

class TestKnowledgeTypes:
    """Valida tipos de conhecimento."""
    
    def test_all_knowledge_types_exist(self):
        assert KnowledgeType.CLINICAL.value == "clinical"
        assert KnowledgeType.PROFESSIONAL.value == "professional"
        assert KnowledgeType.ORGANIZATIONAL.value == "organizational"
        assert KnowledgeType.PATIENT.value == "patient"
        assert KnowledgeType.SYSTEM.value == "system"
    
    def test_knowledge_status_values(self):
        assert KnowledgeStatus.ACTIVE.value == "active"
        assert KnowledgeStatus.ARCHIVED.value == "archived"
        assert KnowledgeStatus.DRAFT.value == "draft"
        assert KnowledgeStatus.DEPRECATED.value == "deprecated"
    
    def test_source_type_values(self):
        assert KnowledgeSourceType.DOCUMENT.value == "document"
        assert KnowledgeSourceType.PROTOCOL.value == "protocol"
        assert KnowledgeSourceType.FAQ.value == "faq"
        assert KnowledgeSourceType.DIGITAL_TWIN.value == "digital_twin"


# ═══════════════════════════════════════════════════════════════════════
# PART 3: Repository
# ═══════════════════════════════════════════════════════════════════════

class TestRepository:
    """Valida repositório de conhecimento."""
    
    def test_save_and_get_document(self, repo):
        doc = KnowledgeDocument(
            document_id="doc_001",
            tenant_id="tenant_001",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo HAS",
            content="Conteúdo",
        )
        repo.save_document(doc)
        
        retrieved = repo.get_document("doc_001")
        assert retrieved is not None
        assert retrieved.title == "Protocolo HAS"
    
    def test_delete_document(self, repo):
        doc = KnowledgeDocument(
            document_id="doc_001",
            tenant_id="tenant_001",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Test",
            content="Test",
        )
        repo.save_document(doc)
        assert repo.delete_document("doc_001") is True
        assert repo.get_document("doc_001") is None
    
    def test_list_documents_by_type(self, repo):
        repo.save_document(KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Clinical", content="",
        ))
        repo.save_document(KnowledgeDocument(
            document_id="doc_002", tenant_id="t1",
            knowledge_type=KnowledgeType.ORGANIZATIONAL,
            source_type=KnowledgeSourceType.POLICY,
            title="Org", content="",
        ))
        
        clinical = repo.list_documents("t1", knowledge_type=KnowledgeType.CLINICAL)
        assert len(clinical) == 1
        assert clinical[0].title == "Clinical"
    
    def test_search_by_keyword(self, repo):
        repo.save_document(KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo de Hipertensão",
            content="Tratamento da HAS",
        ))
        repo.save_document(KnowledgeDocument(
            document_id="doc_002", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo de Diabetes",
            content="Tratamento do DM2",
        ))
        
        results = repo.search_by_keyword("t1", "hipertensão")
        assert len(results) == 1
        assert results[0].title == "Protocolo de Hipertensão"
    
    def test_search_by_keyword_in_chunks(self, repo):
        doc = KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo",
            content="Introdução",
        )
        doc.add_chunk(KnowledgeChunk(
            chunk_id="c1", document_id="doc_001",
            content="Tratamento de hipertensão arterial",
            chunk_index=0,
        ))
        repo.save_document(doc)
        
        results = repo.search_by_keyword("t1", "hipertensão")
        assert len(results) == 1


# ═══════════════════════════════════════════════════════════════════════
# PART 4: Retrieval Engine
# ═══════════════════════════════════════════════════════════════════════

class TestRetrievalEngine:
    """Valida motor de recuperação."""
    
    def test_search_with_scoring(self, repo):
        repo.save_document(KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo de Hipertensão",
            content="Tratamento da hipertensão arterial sistêmica",
        ))
        
        engine = KnowledgeRetrievalEngine(repo)
        results = engine.search("t1", "hipertensão")
        
        assert len(results) > 0
        assert results[0].score > 0
        assert results[0].match_type != "none"
    
    def test_search_filters_by_status(self, repo):
        doc = KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo HAS",
            content="Hipertensão",
        )
        doc.archive()
        repo.save_document(doc)
        
        engine = KnowledgeRetrievalEngine(repo)
        results = engine.search("t1", "hipertensão")
        
        assert len(results) == 0  # Arquivado não aparece
    
    def test_search_limits_results(self, repo):
        for i in range(5):
            repo.save_document(KnowledgeDocument(
                document_id=f"doc_{i}", tenant_id="t1",
                knowledge_type=KnowledgeType.CLINICAL,
                source_type=KnowledgeSourceType.PROTOCOL,
                title=f"Protocolo {i}",
                content="Hipertensão arterial",
            ))
        
        engine = KnowledgeRetrievalEngine(repo)
        results = engine.search("t1", "hipertensão", limit=3)
        
        assert len(results) == 3
    
    def test_search_by_knowledge_type(self, repo):
        repo.save_document(KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Clinical Doc",
            content="Hipertensão",
        ))
        repo.save_document(KnowledgeDocument(
            document_id="doc_002", tenant_id="t1",
            knowledge_type=KnowledgeType.ORGANIZATIONAL,
            source_type=KnowledgeSourceType.POLICY,
            title="Org Doc",
            content="Hipertensão",
        ))
        
        engine = KnowledgeRetrievalEngine(repo)
        results = engine.search("t1", "hipertensão", knowledge_type=KnowledgeType.CLINICAL)
        
        assert len(results) == 1
        assert results[0].document.knowledge_type == KnowledgeType.CLINICAL


# ═══════════════════════════════════════════════════════════════════════
# PART 5: Organizational Memory
# ═══════════════════════════════════════════════════════════════════════

class TestOrganizationalMemory:
    """Valida memória organizacional."""
    
    def test_add_protocol(self, repo):
        memory = OrganizationalMemory(repo, "tenant_001")
        doc = memory.add_protocol(
            title="Protocolo de HAS",
            content="1. Medir PA\n2. Prescrever Losartana",
            tags=["cardiologia"],
        )
        
        assert doc.knowledge_type == KnowledgeType.CLINICAL
        assert doc.source_type == KnowledgeSourceType.PROTOCOL
        assert len(doc.chunks) > 0
        assert "cardiologia" in doc.metadata.tags
    
    def test_add_faq(self, repo):
        memory = OrganizationalMemory(repo, "tenant_001")
        doc = memory.add_faq(
            question="Qual o horário de funcionamento?",
            answer="Segunda a sexta, 8h às 18h",
        )
        
        assert doc.source_type == KnowledgeSourceType.FAQ
        assert "8h às 18h" in doc.content
    
    def test_add_policy(self, repo):
        memory = OrganizationalMemory(repo, "tenant_001")
        doc = memory.add_policy(
            title="Política de Privacidade",
            content="Os dados do paciente são confidenciais...",
        )
        
        assert doc.source_type == KnowledgeSourceType.POLICY
        assert doc.knowledge_type == KnowledgeType.ORGANIZATIONAL
    
    def test_add_workflow(self, repo):
        memory = OrganizationalMemory(repo, "tenant_001")
        doc = memory.add_workflow(
            title="Fluxo de Atendimento",
            content="1. Check-in\n2. Triagem\n3. Consulta",
        )
        
        assert doc.source_type == KnowledgeSourceType.WORKFLOW
    
    def test_search_organizational(self, repo):
        memory = OrganizationalMemory(repo, "tenant_001")
        memory.add_protocol(title="Protocolo HAS", content="Hipertensão")
        memory.add_faq(question="Horário?", answer="8h às 18h")
        
        results = memory.search("hipertensão")
        assert len(results) == 1


# ═══════════════════════════════════════════════════════════════════════
# PART 6: Professional Memory
# ═══════════════════════════════════════════════════════════════════════

class TestProfessionalMemory:
    """Valida memória profissional."""
    
    def test_add_template(self, repo):
        memory = ProfessionalMemory(repo, "tenant_001", "dr_001")
        doc = memory.add_template(
            title="Template de Evolução",
            content="Paciente refere melhora...",
            specialty="Clínica Geral",
        )
        
        assert doc.source_type == KnowledgeSourceType.TEMPLATE
        assert doc.knowledge_type == KnowledgeType.PROFESSIONAL
        assert "template" in doc.metadata.tags
    
    def test_add_checklist(self, repo):
        memory = ProfessionalMemory(repo, "tenant_001", "dr_001")
        doc = memory.add_checklist(
            title="Checklist de Consulta",
            items=["Anamnese", "Exame físico", "Prescrição"],
        )
        
        assert doc.source_type == KnowledgeSourceType.CHECKLIST
        assert "Anamnese" in doc.content
        assert "[ ]" in doc.content
    
    def test_add_preference(self, repo):
        memory = ProfessionalMemory(repo, "tenant_001", "dr_001")
        doc = memory.add_preference(
            key="horario_preferido",
            value="manhã",
        )
        
        assert doc.title == "Preferência: horario_preferido"
        assert "manhã" in doc.content
    
    def test_search_professional(self, repo):
        memory = ProfessionalMemory(repo, "tenant_001", "dr_001")
        memory.add_template(title="Template Evolução", content="Evolução diária")
        
        results = memory.search("evolução")
        assert len(results) == 1


# ═══════════════════════════════════════════════════════════════════════
# PART 7: Patient Knowledge
# ═══════════════════════════════════════════════════════════════════════

class TestPatientKnowledge:
    """Valida integração com dados do paciente."""
    
    @pytest.mark.asyncio
    async def test_index_digital_twin(self, repo, env):
        env.create_patient_with_data()
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)
        
        source = PatientKnowledgeSource(repo, env.tenant_id)
        doc = source.index_digital_twin(twin)
        
        assert doc.knowledge_type == KnowledgeType.PATIENT
        assert doc.source_type == KnowledgeSourceType.DIGITAL_TWIN
        assert env.patient_id in doc.document_id
        assert "Hipertensão" in doc.content
        assert "Losartana" in doc.content
        assert "Penicilina" in doc.content
    
    @pytest.mark.asyncio
    async def test_index_timeline(self, repo, env):
        env.create_patient_with_data()
        
        # Criar algumas entradas de timeline
        from araos.clinical.timeline.models import TimelineEntry
        from datetime import datetime, timezone
        
        entries = [
            TimelineEntry(
                tenant_id=env.tenant_id,
                patient_id=env.patient_id,
                event_id="evt_001",
                event_type="DIAGNOSIS_ADDED",
                event_category="clinical",
                title="Hipertensão diagnosticada",
                description="Paciente com PA 160/100",
                event_date=datetime.now(timezone.utc),
            ),
        ]
        
        source = PatientKnowledgeSource(repo, env.tenant_id)
        doc = source.index_timeline_entries(env.patient_id, entries)
        
        assert doc.source_type == KnowledgeSourceType.TIMELINE
        assert "Hipertensão diagnosticada" in doc.content
        assert len(doc.chunks) == 1
    
    @pytest.mark.asyncio
    async def test_index_clinical_summary(self, repo, env):
        env.create_patient_with_data()
        
        from araos.clinical.summary.engine import ClinicalSummaryEngine
        from araos.clinical.twin.models import PatientDigitalTwinBuilder
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)
        
        engine = ClinicalSummaryEngine()
        summary = engine.generate(twin.profile.to_dict())
        
        source = PatientKnowledgeSource(repo, env.tenant_id)
        doc = source.index_clinical_summary(env.patient_id, summary)
        
        assert doc.source_type == KnowledgeSourceType.SUMMARY
        assert doc.knowledge_type == KnowledgeType.PATIENT
        assert len(doc.content) > 0
    
    @pytest.mark.asyncio
    async def test_search_patient_knowledge(self, repo, env):
        env.create_patient_with_data()
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)
        
        source = PatientKnowledgeSource(repo, env.tenant_id)
        source.index_digital_twin(twin)
        
        results = source.search(env.patient_id, "hipertensão")
        assert len(results) == 1
        assert "Hipertensão" in results[0].content
    
    @pytest.mark.asyncio
    async def test_get_patient_knowledge(self, repo, env):
        env.create_patient_with_data()
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)
        
        source = PatientKnowledgeSource(repo, env.tenant_id)
        source.index_digital_twin(twin)
        
        docs = source.get_patient_knowledge(env.patient_id)
        assert len(docs) == 1
        assert docs[0].source_type == KnowledgeSourceType.DIGITAL_TWIN


# ═══════════════════════════════════════════════════════════════════════
# PART 8: LLM Knowledge Adapter
# ═══════════════════════════════════════════════════════════════════════

class TestLLMKnowledgeAdapter:
    """Valida adaptador Knowledge → LLM."""
    
    def REDACTED(self, repo):
        repo.save_document(KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo de Hipertensão",
            content="Tratar com Losartana 50mg",
        ))
        
        adapter = LLMKnowledgeAdapter(repo)
        context = adapter.retrieve("t1", "hipertensão")
        
        assert isinstance(context, KnowledgeContext)
        assert len(context.documents) == 1
        assert context.documents[0].title == "Protocolo de Hipertensão"
        assert "Losartana" in context.context_text
        assert len(context.sources) == 1
    
    def REDACTED(self, repo):
        repo.save_document(KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo HAS",
            content="Hipertensão",
        ))
        repo.save_document(KnowledgeDocument(
            document_id="doc_002", tenant_id="t1",
            knowledge_type=KnowledgeType.ORGANIZATIONAL,
            source_type=KnowledgeSourceType.POLICY,
            title="Política",
            content="Hipertensão",
        ))
        
        adapter = LLMKnowledgeAdapter(repo)
        context = adapter.retrieve(
            "t1", "hipertensão",
            knowledge_types=[KnowledgeType.CLINICAL],
        )
        
        assert len(context.documents) == 1
        assert context.documents[0].knowledge_type == KnowledgeType.CLINICAL
    
    def REDACTED(self, repo):
        adapter = LLMKnowledgeAdapter(repo)
        
        k_context = KnowledgeContext(
            documents=[],
            context_text="Protocolo: usar Losartana",
        )
        
        messages = adapter.build_messages(
            user_question="Como tratar HAS?",
            knowledge_context=k_context,
        )
        
        assert len(messages) == 3  # system + context + user
        assert messages[0].role.value == "system"
        assert messages[1].role.value == "system"
        assert "CONHECIMENTO RELEVANTE" in messages[1].content
        assert messages[2].role.value == "user"
        assert messages[2].content == "Como tratar HAS?"
    
    def REDACTED(self, repo):
        adapter = LLMKnowledgeAdapter(repo)
        
        k_context = KnowledgeContext(documents=[], context_text="")
        messages = adapter.build_messages(
            user_question="Olá",
            knowledge_context=k_context,
        )
        
        assert len(messages) == 2  # system + user (sem context)
    
    def test_get_used_documents(self, repo):
        doc = KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo",
            content="Test",
            metadata=KnowledgeMetadata(author_id="dr_001"),
        )
        
        adapter = LLMKnowledgeAdapter(repo)
        k_context = KnowledgeContext(documents=[doc])
        
        used = adapter.get_used_documents(k_context)
        assert len(used) == 1
        assert used[0]["document_id"] == "doc_001"
        assert used[0]["author"] == "dr_001"


# ═══════════════════════════════════════════════════════════════════════
# PART 9: Observabilidade
# ═══════════════════════════════════════════════════════════════════════

class TestObservability:
    """Valida observabilidade da Knowledge Layer."""
    
    def test_record_query(self):
        obs = KnowledgeObservability()
        
        from araos.knowledge.retrieval import RetrievalResult
        
        doc = KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo", content="Test",
        )
        result = RetrievalResult(document=doc, score=0.85, match_type="title")
        
        metric = obs.record_query(
            query="hipertensão",
            tenant_id="t1",
            results=[result],
            latency_ms=15.5,
        )
        
        assert metric.query == "hipertensão"
        assert metric.document_count == 1
        assert metric.max_score == 0.85
        assert metric.latency_ms == 15.5
    
    def test_summary(self):
        obs = KnowledgeObservability()
        
        doc = KnowledgeDocument(
            document_id="doc_001", tenant_id="t1",
            knowledge_type=KnowledgeType.CLINICAL,
            source_type=KnowledgeSourceType.PROTOCOL,
            title="Protocolo", content="Test",
        )
        result = RetrievalResult(document=doc, score=0.9)
        
        obs.record_query("q1", "t1", [result], latency_ms=10.0)
        obs.record_query("q2", "t1", [result], latency_ms=20.0)
        
        summary = obs.summary()
        assert summary["total_queries"] == 2
        assert summary["avg_latency_ms"] == 15.0
        assert summary["avg_documents_per_query"] == 1.0



# ═══════════════════════════════════════════════════════════════════════
# PART 10: Embedding Contracts
# ═══════════════════════════════════════════════════════════════════════

class TestEmbeddingContracts:
    """Valida contratos de embedding (stubs para semantic search futuro)."""
    
    @pytest.mark.asyncio
    async def test_mock_embedding_provider(self):
        provider = MockEmbeddingProvider(dimension=384)
        
        vector = await provider.embed("hipertensão")
        assert len(vector) == 384
        # Vetor normalizado
        norm = sum(x * x for x in vector) ** 0.5
        assert abs(norm - 1.0) < 0.01
    
    @pytest.mark.asyncio
    async def REDACTED(self):
        provider = MockEmbeddingProvider(dimension=384)
        
        v1 = await provider.embed("texto igual")
        v2 = await provider.embed("texto igual")
        assert v1 == v2
    
    @pytest.mark.asyncio
    async def REDACTED(self):
        provider = MockEmbeddingProvider(dimension=384)
        
        v1 = await provider.embed("hipertensão")
        v2 = await provider.embed("diabetes")
        assert v1 != v2
    
    @pytest.mark.asyncio
    async def test_mock_embedding_batch(self):
        provider = MockEmbeddingProvider(dimension=384)
        
        vectors = await provider.embed_batch(["a", "b", "c"])
        assert len(vectors) == 3
        assert all(len(v) == 384 for v in vectors)
    
    @pytest.mark.asyncio
    async def test_in_memory_embedding_index(self):
        index = InMemoryEmbeddingIndex()
        
        vectors = [
            EmbeddingVector(
                id="v1",
                vector=[1.0, 0.0, 0.0],
                metadata={"tenant_id": "t1", "doc": "doc_001"},
                document_id="doc_001",
            ),
            EmbeddingVector(
                id="v2",
                vector=[0.0, 1.0, 0.0],
                metadata={"tenant_id": "t1", "doc": "doc_002"},
                document_id="doc_002",
            ),
        ]
        
        await index.index(vectors)
        
        # Buscar pelo vetor mais próximo de [1.0, 0.0, 0.0]
        results = await index.search(
            query_vector=[1.0, 0.0, 0.0],
            top_k=2,
        )
        
        assert len(results) == 2
        assert results[0].document_id == "doc_001"
        assert results[0].score > 0.99  # cosine similarity ~1.0
    
    @pytest.mark.asyncio
    async def REDACTED(self):
        index = InMemoryEmbeddingIndex()
        
        vectors = [
            EmbeddingVector(
                id="v1",
                vector=[1.0, 0.0, 0.0],
                metadata={"tenant_id": "t1"},
                document_id="doc_001",
            ),
            EmbeddingVector(
                id="v2",
                vector=[0.0, 1.0, 0.0],
                metadata={"tenant_id": "t2"},
                document_id="doc_002",
            ),
        ]
        
        await index.index(vectors)
        
        results = await index.search(
            query_vector=[1.0, 0.0, 0.0],
            filters={"tenant_id": "t1"},
        )
        
        assert len(results) == 1
        assert results[0].document_id == "doc_001"
    
    @pytest.mark.asyncio
    async def REDACTED(self):
        index = InMemoryEmbeddingIndex()
        
        vectors = [
            EmbeddingVector(
                id="v1",
                vector=[1.0, 0.0, 0.0],
                metadata={},
                document_id="doc_001",
            ),
        ]
        
        await index.index(vectors)
        assert await index.delete("doc_001") is True
        
        health = await index.health()
        assert health["vector_count"] == 0
    
    @pytest.mark.asyncio
    async def REDACTED(self):
        index = InMemoryEmbeddingIndex()
        
        health = await index.health()
        assert health["status"] == "healthy"
        assert health["backend"] == "in_memory"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
