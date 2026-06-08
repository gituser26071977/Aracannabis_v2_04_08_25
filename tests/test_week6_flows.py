"""
AraOS Week 6 — Testes de Integração dos Fluxos MVP

Valida os 3 fluxos end-to-end:
    1. Concierge → Digital Twin → Voice
    2. Smart Flow → Check-in → Event Bus → Consulta
    3. WhatsApp → Intake → Documentos → Consulta

Regras:
    - Sem LLMs (rules-based only)
    - SQLite em memória
    - Event Bus em memória
    - Valida estrutura, não conteúdo exato
"""

import asyncio
import pytest
import sys
import os

# Garantir que o projeto está no path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from araos.demo.demo_base import DemoEnvironment
from araos.demo.concierge_intake_flow import run_concierge_intake_flow
from araos.demo.smart_flow_checkin import run_smart_flow_checkin
from araos.demo.whatsapp_document_flow import run_whatsapp_document_flow


@pytest.fixture
def env():
    """Fixture com ambiente limpo para cada teste."""
    e = DemoEnvironment().setup()
    yield e
    e.teardown()


class TestFluxo1ConciergeIntake:
    """Fluxo 1: Concierge → Digital Twin → Voice"""
    
    @pytest.mark.asyncio
    async def test_fluxo_completo(self, env):
        result = await run_concierge_intake_flow(env)
        
        assert result["flow"] == "concierge_intake"
        assert result["patient_id"] == env.patient_id
        assert result["events_count"] >= 2  # WHATSAPP_RECEIVED, DIAGNOSIS_ADDED
        assert result["diagnoses_count"] >= 2  # HAS + Cefaleia
        assert result["medications_count"] >= 1  # Losartana
        assert result["allergies_count"] >= 1  # Penicilina
        assert len(result["summary_text"]) > 0
        assert result["correlation_chain_length"] >= 2
    
    @pytest.mark.asyncio
    async def test_correlation_chain(self, env):
        result = await run_concierge_intake_flow(env)
        assert result["correlation_chain_length"] >= 2
    
    @pytest.mark.asyncio
    async def test_digital_twin_builds(self, env):
        result = await run_concierge_intake_flow(env)
        assert result["diagnoses_count"] > 0
        assert result["medications_count"] > 0


class TestFluxo2SmartFlowCheckin:
    """Fluxo 2: Smart Flow → Check-in → Event Bus → Consulta"""
    
    @pytest.mark.asyncio
    async def test_fluxo_completo(self, env):
        result = await run_smart_flow_checkin(env)
        
        assert result["flow"] == "smart_flow_checkin"
        assert result["patient_id"] == env.patient_id
        assert result["consultation_id"] == "demo_consultation_001"
        assert result["events_count"] >= 4  # CHECKIN_DETECTED, CHECKIN_COMPLETED, CONSULTATION_STARTED, EVOLUTION_CREATED
        assert result["correlation_chain_length"] >= 4
        assert result["checkin_method"] == "face"
        assert result["biometric_confidence"] > 0.9
    
    @pytest.mark.asyncio
    async def test_checkin_detected_emits_event(self, env):
        await run_smart_flow_checkin(env)
        events = env.event_bus.get_events("CHECKIN_DETECTED")
        assert len(events) == 1
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        result = await run_smart_flow_checkin(env)
        assert result["consultation_id"].startswith("demo_consultation")


class TestFluxo3WhatsappDocument:
    """Fluxo 3: WhatsApp → Intake → Documentos → Consulta"""
    
    @pytest.mark.asyncio
    async def test_fluxo_completo(self, env):
        result = await run_whatsapp_document_flow(env)
        
        assert result["flow"] == "whatsapp_document"
        assert result["patient_id"] == env.patient_id
        assert result["events_count"] >= 4  # DOCUMENT_UPLOADED, DOCUMENT_PROCESSED, MEDICATION_PRESCRIBED, CONSULTATION_SCHEDULED
        assert result["correlation_chain_length"] >= 4
        assert result["ocr_confidence"] > 0.9
        assert result["consultation_scheduled"].startswith("demo_consultation")
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        result = await run_whatsapp_document_flow(env)
        assert result["medications_after"] >= 2  # Losartana (setup) + Atenolol (OCR)
    
    @pytest.mark.asyncio
    async def test_consultation_auto_scheduled(self, env):
        result = await run_whatsapp_document_flow(env)
        assert "consultation_doc_001" in result["consultation_scheduled"]


class TestTodosOsFluxos:
    """Valida independência e consistência entre fluxos."""
    
    @pytest.mark.asyncio
    async def test_fluxos_sao_independentes(self):
        """Cada fluxo deve funcionar com seu próprio ambiente."""
        env1 = DemoEnvironment().setup()
        env2 = DemoEnvironment().setup()
        env3 = DemoEnvironment().setup()
        
        try:
            result1 = await run_concierge_intake_flow(env1)
            result2 = await run_smart_flow_checkin(env2)
            result3 = await run_whatsapp_document_flow(env3)
            
            assert result1["flow"] == "concierge_intake"
            assert result2["flow"] == "smart_flow_checkin"
            assert result3["flow"] == "whatsapp_document"
            
            # Ambientes isolados
            assert result1["events_count"] == env1.event_bus.get_events().__len__()
            assert result2["events_count"] == env2.event_bus.get_events().__len__()
            assert result3["events_count"] == env3.event_bus.get_events().__len__()
        finally:
            env1.teardown()
            env2.teardown()
            env3.teardown()
    
    @pytest.mark.asyncio
    async def test_event_bus_rastreia_correlacao(self, env):
        """Cadeia de correlação deve rastrear eventos relacionados."""
        await run_concierge_intake_flow(env)
        
        all_events = env.event_bus.get_events()
        assert len(all_events) > 0
        
        # Todos os eventos devem ter correlation_id
        for event in all_events:
            assert event.correlation_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
