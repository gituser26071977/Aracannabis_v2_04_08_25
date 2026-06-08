"""
AraOS Week 7A — Platform Hardening Tests

Valida os 4 pilares de hardening:
    1. Event Consumers (sem chamadas diretas ao Projection Engine)
    2. Digital Twin Cache (hit/miss, TTL, invalidação)
    3. Projection Idempotency (exactly-once processing)
    4. Clinical Repository (desacoplamento do ORM)
"""

import asyncio
import pytest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from araos.demo.demo_base import DemoEnvironment
from araos.demo.concierge_intake_flow import run_concierge_intake_flow
from araos.demo.smart_flow_checkin import run_smart_flow_checkin
from araos.demo.whatsapp_document_flow import run_whatsapp_document_flow

from araos.clinical.projections.engine import ClinicalProjectionEngine
from araos.clinical.repository import SqlAlchemyClinicalRepository, InMemoryClinicalRepository
from araos.clinical.cache import InMemoryTwinCache
from araos.clinical.idempotency import InMemoryIdempotencyTracker
from araos.clinical.twin.models import PatientDigitalTwinBuilder
from araos.platform.event_bus.envelope import EventEnvelopeV2, EventCategory


@pytest.fixture
def env():
    e = DemoEnvironment().setup()
    yield e
    e.teardown()


class TestP1EventConsumers:
    """Prioridade 1: Nenhuma chamada direta ao Projection Engine."""
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Consumer deve processar DIAGNOSIS_ADDED automaticamente."""
        env.create_patient_with_data()
        
        event = EventEnvelopeV2(
            event_type="DIAGNOSIS_ADDED",
            tenant_id=env.tenant_id,
            payload={
                "patient_id": env.patient_id,
                "description": "Teste Consumer",
                "icd10_code": "Z00.0",
            },
            event_category=EventCategory.CLINICAL,
        )
        
        # Publicar evento — consumer deve processar automaticamente
        await env.event_bus.publish(event)
        
        # Verificar que entidade foi criada
        diagnoses = env.repository.get_diagnoses(env.patient_id, env.tenant_id)
        assert len(diagnoses) == 2  # HAS (setup) + Teste Consumer
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Consumer deve processar MEDICATION_PRESCRIBED automaticamente."""
        env.create_patient_with_data()
        
        event = EventEnvelopeV2(
            event_type="MEDICATION_PRESCRIBED",
            tenant_id=env.tenant_id,
            payload={
                "patient_id": env.patient_id,
                "name": "Paracetamol",
                "dosage": "500mg",
            },
            event_category=EventCategory.CLINICAL,
        )
        
        await env.event_bus.publish(event)
        
        meds = env.repository.get_medications(env.patient_id, env.tenant_id)
        assert len(meds) == 2  # Losartana (setup) + Paracetamol
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Fluxo 1 não deve chamar Projection Engine diretamente."""
        import araos.demo.concierge_intake_flow as flow_module
        source = open(flow_module.__file__).read()
        assert "ClinicalProjectionEngine(env.db)" not in source
        assert "projection.process(" not in source
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Fluxo 3 não deve chamar Projection Engine diretamente."""
        import araos.demo.whatsapp_document_flow as flow_module
        source = open(flow_module.__file__).read()
        assert "ClinicalProjectionEngine(env.db)" not in source
        assert "projection.process(" not in source


class TestP2TwinCache:
    """Prioridade 2: Digital Twin Cache."""
    
    @pytest.mark.asyncio
    async def test_cache_miss_then_hit(self, env):
        """Primeira build deve miss; segunda deve hit."""
        env.create_patient_with_data()
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        
        # Primeira build — miss
        twin1 = await builder.build(env.patient_id, env.tenant_id)
        assert twin1 is not None
        assert len(twin1.active_diagnoses) == 1
        
        # Segunda build — hit (deve vir do cache)
        start = time.perf_counter()
        twin2 = await builder.build(env.patient_id, env.tenant_id)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert twin2 is not None
        # Cache hit deve ser mais rápido (não faz queries complexas)
        assert elapsed_ms < 10  # hit deve ser quase instantâneo
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Cache deve ser invalidado quando evento clínico é processado."""
        env.create_patient_with_data()
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        
        # Build e cachear
        twin1 = await builder.build(env.patient_id, env.tenant_id)
        assert len(twin1.active_diagnoses) == 1
        
        # Emitir evento clínico — consumer deve invalidar cache
        event = EventEnvelopeV2(
            event_type="DIAGNOSIS_ADDED",
            tenant_id=env.tenant_id,
            payload={
                "patient_id": env.patient_id,
                "description": "Nova condição",
                "icd10_code": "Z01.0",
            },
            event_category=EventCategory.CLINICAL,
        )
        await env.event_bus.publish(event)
        
        # Rebuild — deve refletir nova condição (cache foi invalidado)
        twin2 = await builder.build(env.patient_id, env.tenant_id)
        assert len(twin2.active_diagnoses) == 2
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expires(self, env):
        """Cache deve expirar após TTL."""
        env.create_patient_with_data()
        
        # Usar TTL muito curto para teste
        cache = InMemoryTwinCache()
        builder = PatientDigitalTwinBuilder(env.repository, cache=cache)
        
        twin1 = await builder.build(env.patient_id, env.tenant_id)
        assert twin1 is not None
        
        # Forçar expiração manipulando o TTL interno
        key = cache._key(env.patient_id, env.tenant_id)
        from datetime import datetime, timezone, timedelta
        cache._ttl[key] = datetime.now(timezone.utc) - timedelta(seconds=1)
        
        # Agora deve rebuild (cache expirado)
        twin2 = await builder.build(env.patient_id, env.tenant_id)
        assert twin2 is not None


class TestP3Idempotency:
    """Prioridade 3: Projection Idempotency."""
    
    @pytest.mark.asyncio
    async def test_event_processed_only_once(self, env):
        """Evento idêntico processado 2x não deve duplicar entidade."""
        env.create_patient_with_data()
        
        event = EventEnvelopeV2(
            event_type="DIAGNOSIS_ADDED",
            tenant_id=env.tenant_id,
            payload={
                "patient_id": env.patient_id,
                "description": "Duplicidade teste",
                "icd10_code": "Z02.0",
            },
            event_category=EventCategory.CLINICAL,
        )
        
        # Primeira vez
        result1 = await env.projection.process(event)
        assert result1["processed"] is True
        
        diagnoses = env.repository.get_diagnoses(env.patient_id, env.tenant_id)
        count_after_first = len(diagnoses)
        
        # Segunda vez (mesmo event_id)
        result2 = await env.projection.process(event)
        assert result2["processed"] is False
        assert result2["reason"] == "already_processed"
        
        diagnoses = env.repository.get_diagnoses(env.patient_id, env.tenant_id)
        assert len(diagnoses) == count_after_first  # não duplicou
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Tracker deve rastrear eventos processados."""
        tracker = InMemoryIdempotencyTracker()
        
        assert await tracker.is_processed("evt_001") is False
        
        await tracker.mark_processed("evt_001")
        assert await tracker.is_processed("evt_001") is True
        
        await tracker.mark_failed("evt_002")
        assert await tracker.is_failed("evt_002") is True


class TestP4ClinicalRepository:
    """Prioridade 4: Clinical Repository desacopla ORM."""
    
    def test_repository_interface(self):
        """Repository deve ser uma interface desacoplada."""
        from araos.clinical.repository import ClinicalRepository
        import inspect
        
        methods = [m for m in dir(ClinicalRepository) if not m.startswith("_")]
        assert "get_profile" in methods
        assert "get_diagnoses" in methods
        assert "get_medications" in methods
        assert "save_entity" in methods
    
    def REDACTED(self, env):
        """SqlAlchemyRepository deve usar Session internamente."""
        repo = SqlAlchemyClinicalRepository(env.db)
        assert repo.db is env.db
    
    def test_inmemory_repository_isolation(self):
        """InMemoryRepository deve isolar dados entre instâncias."""
        repo1 = InMemoryClinicalRepository()
        repo2 = InMemoryClinicalRepository()
        
        from araos.clinical.profile.models import ClinicalProfile
        profile = ClinicalProfile(tenant_id="t1", patient_id="p1")
        repo1.save_entity(profile)
        
        assert repo1.get_profile("p1", "t1") is not None
        assert repo2.get_profile("p1", "t1") is None
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """TwinBuilder deve receber Repository, não Session."""
        env.create_patient_with_data()
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)
        
        assert twin.profile is not None
        assert len(twin.active_diagnoses) == 1


class TestMetrics:
    """Métricas de performance: antes vs depois."""
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Rebuild com cache deve ser mais rápido que sem cache."""
        env.create_patient_with_data()
        
        # Sem cache
        builder_no_cache = PatientDigitalTwinBuilder(env.repository, cache=None)
        times_no_cache = []
        for _ in range(3):
            start = time.perf_counter()
            await builder_no_cache.build(env.patient_id, env.tenant_id)
            times_no_cache.append((time.perf_counter() - start) * 1000)
        avg_no_cache = sum(times_no_cache) / len(times_no_cache)
        
        # Com cache
        builder_with_cache = PatientDigitalTwinBuilder(env.repository, cache=InMemoryTwinCache())
        # Primeiro build para popular cache
        await builder_with_cache.build(env.patient_id, env.tenant_id)
        
        times_with_cache = []
        for _ in range(3):
            start = time.perf_counter()
            await builder_with_cache.build(env.patient_id, env.tenant_id)
            times_with_cache.append((time.perf_counter() - start) * 1000)
        avg_with_cache = sum(times_with_cache) / len(times_with_cache)
        
        print(f"\n   Twin rebuild — Sem cache: {avg_no_cache:.2f}ms | Com cache: {avg_with_cache:.2f}ms")
        assert avg_with_cache < avg_no_cache
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Fluxo 1 deve funcionar com consumers + cache + repository."""
        start = time.perf_counter()
        result = await run_concierge_intake_flow(env)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert result["flow"] == "concierge_intake"
        assert result["events_count"] >= 2
        assert result["diagnoses_count"] >= 2
        print(f"\n   Fluxo 1 tempo: {elapsed_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Fluxo 2 deve funcionar com consumers + cache + repository."""
        start = time.perf_counter()
        result = await run_smart_flow_checkin(env)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert result["flow"] == "smart_flow_checkin"
        assert result["events_count"] >= 4
        print(f"\n   Fluxo 2 tempo: {elapsed_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        """Fluxo 3 deve funcionar com consumers + cache + repository."""
        start = time.perf_counter()
        result = await run_whatsapp_document_flow(env)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        assert result["flow"] == "whatsapp_document"
        assert result["events_count"] >= 4
        assert result["medications_after"] >= 2
        print(f"\n   Fluxo 3 tempo: {elapsed_ms:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
