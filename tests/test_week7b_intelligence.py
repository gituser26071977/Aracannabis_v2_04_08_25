"""
AraOS Week 7B — Intelligence Layer v1 Tests

Valida:
    1. Trust Levels (STRUCTURED_DATA, GENERATED_SUMMARY, AI_INFERENCE)
    2. LLM Providers (Mock, OpenAI stub, Gemini stub, Claude stub)
    3. LLM Router (fallback, métricas)
    4. LLM Runtime (complete, observabilidade, métricas)
    5. Clinical Context Builder (twin → context)
    6. Concierge Agent (intenção, triagem, agendamento)
    7. Voice Copilot Agent (read-only queries)
    8. Observabilidade + Audit Ledger integration
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from araos.intelligence.llm import LLMMessage, LLMRequest, MessageRole
from araos.intelligence.trust.levels import TrustLevel, SourceType, TrustedResponse
from araos.intelligence.providers.mock_provider import MockLLMProvider
from araos.intelligence.providers.openai_provider import OpenAIProvider
from araos.intelligence.providers.gemini_provider import GeminiProvider
from araos.intelligence.providers.claude_provider import ClaudeProvider
from araos.intelligence.providers.router import LLMRouter
from araos.intelligence.runtime.runtime import LLMRuntime
from araos.intelligence.runtime.metrics import LLMMetricsCollector
from araos.intelligence.context.builder import ClinicalContextBuilder
from araos.agents.intelligent.concierge import ConciergeAgent
from araos.agents.intelligent.voice import VoiceCopilotAgent

from araos.demo.demo_base import DemoEnvironment
from araos.demo.concierge_intake_flow import run_concierge_intake_flow
from araos.demo.smart_flow_checkin import run_smart_flow_checkin

from araos.platform.identity.context import IdentityContext, ActorType
from araos.platform.shared.context import TenantContext
from araos.agents.runtime.context import AgentContext, CorrelationContext


@pytest.fixture
def env():
    e = DemoEnvironment().setup()
    yield e
    e.teardown()


@pytest.fixture
def mock_provider():
    return MockLLMProvider()


@pytest.fixture
def router(mock_provider):
    r = LLMRouter()
    r.register("mock", mock_provider, priority=1)
    return r


@pytest.fixture
def llm_runtime(router):
    return LLMRuntime(router=router)


# ═══════════════════════════════════════════════════════════════════════
# PART 1: Trust Levels
# ═══════════════════════════════════════════════════════════════════════

class TestTrustLevels:
    """Valida Trust Levels em todas as respostas."""
    
    def test_structured_data_trust_level(self):
        r = TrustedResponse(
            content="Losartana 50mg",
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
        )
        assert r.is_structured_data()
        assert not r.requires_human_verification()
        assert r.trust_level == TrustLevel.STRUCTURED_DATA
    
    def test_generated_summary_trust_level(self):
        r = TrustedResponse(
            content="Paciente com HAS controlada",
            source_type=SourceType.GENERATED_SUMMARY,
            trust_level=TrustLevel.GENERATED_SUMMARY,
        )
        assert r.is_generated_summary()
        assert not r.requires_human_verification()
    
    def test_ai_inference_trust_level(self):
        r = TrustedResponse(
            content="Sugiro agendar consulta",
            source_type=SourceType.AI_INFERENCE,
            trust_level=TrustLevel.AI_INFERENCE,
        )
        assert r.is_ai_inference()
        assert r.requires_human_verification()
    
    def test_trusted_response_to_dict(self):
        r = TrustedResponse(
            content="test",
            source_type=SourceType.STRUCTURED_DATA,
            trust_level=TrustLevel.STRUCTURED_DATA,
            provider="mock",
            model="test-model",
            metadata={"latency_ms": 10},
        )
        d = r.to_dict()
        assert d["content"] == "test"
        assert d["source_type"] == "structured_data"
        assert d["trust_level"] == "structured_data"
        assert d["provider"] == "mock"


# ═══════════════════════════════════════════════════════════════════════
# PART 2: LLM Providers
# ═══════════════════════════════════════════════════════════════════════

class TestLLMProviders:
    """Valida providers LLM."""
    
    @pytest.mark.asyncio
    async def test_mock_provider_complete(self, mock_provider):
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="resumo do paciente")],
        )
        response = await mock_provider.complete(request)
        assert response.content == "Aqui está o resumo clínico do paciente."
        assert response.model == "mock-model"
        assert response.usage["total_tokens"] > 0
    
    @pytest.mark.asyncio
    async def REDACTED(self, mock_provider):
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="quais medicamentos?")],
        )
        response = await mock_provider.complete(request)
        assert "Losartana" in response.content
    
    @pytest.mark.asyncio
    async def REDACTED(self, mock_provider):
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="tem alergias?")],
        )
        response = await mock_provider.complete(request)
        assert "Penicilina" in response.content
    
    @pytest.mark.asyncio
    async def test_mock_provider_stream(self, mock_provider):
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="hello")],
        )
        chunks = []
        async for chunk in mock_provider.stream(request):
            chunks.append(chunk)
        assert len(chunks) > 0
    
    @pytest.mark.asyncio
    async def test_openai_provider_stub(self):
        provider = OpenAIProvider(api_key=None)
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="test")],
        )
        response = await provider.complete(request)
        assert "Stub" in response.content
        assert response.model == "gpt-4o-mini"
    
    @pytest.mark.asyncio
    async def test_gemini_provider_stub(self):
        provider = GeminiProvider(api_key=None)
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="test")],
        )
        response = await provider.complete(request)
        assert "Stub" in response.content
        assert response.model == "gemini-1.5-flash"
    
    @pytest.mark.asyncio
    async def test_claude_provider_stub(self):
        provider = ClaudeProvider(api_key=None)
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="test")],
        )
        response = await provider.complete(request)
        assert "Stub" in response.content
        assert "claude" in response.model


# ═══════════════════════════════════════════════════════════════════════
# PART 3: LLM Router
# ═══════════════════════════════════════════════════════════════════════

class TestLLMRouter:
    """Valida roteamento e fallback."""
    
    def test_router_registers_providers(self):
        router = LLMRouter()
        mock = MockLLMProvider()
        router.register("mock", mock, priority=1)
        assert "mock" in router.list_providers()
    
    @pytest.mark.asyncio
    async def test_router_routes_to_provider(self):
        router = LLMRouter()
        mock = MockLLMProvider()
        router.register("mock", mock, priority=1)
        
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="resumo")],
        )
        response = await router.route(request)
        assert response.content == "Aqui está o resumo clínico do paciente."
    
    @pytest.mark.asyncio
    async def test_router_fallback(self):
        router = LLMRouter()
        
        # Provider que sempre falha
        class FailingProvider(MockLLMProvider):
            async def complete(self, request):
                raise RuntimeError("API Error")
        
        failing = FailingProvider()
        mock = MockLLMProvider()
        
        router.register("failing", failing, priority=2)
        router.register("mock", mock, priority=1)
        
        request = LLMRequest(
            messages=[LLMMessage(role=MessageRole.USER, content="resumo")],
        )
        response = await router.route(request)
        assert response.content == "Aqui está o resumo clínico do paciente."
        assert router.get_fallback_count() > 0
    
    def test_router_metrics(self):
        router = LLMRouter()
        mock = MockLLMProvider()
        router.register("mock", mock, priority=1)
        
        assert len(router.get_metrics()) == 0
        # Métricas são preenchidas após chamadas async


# ═══════════════════════════════════════════════════════════════════════
# PART 4: LLM Runtime
# ═══════════════════════════════════════════════════════════════════════

class TestLLMRuntime:
    """Valida runtime com métricas e observabilidade."""
    
    @pytest.mark.asyncio
    async def REDACTED(self, llm_runtime):
        messages = [LLMMessage(role=MessageRole.USER, content="resumo")]
        
        result = await llm_runtime.complete(
            messages=messages,
            source_type=SourceType.AI_INFERENCE,
        )
        
        assert isinstance(result, TrustedResponse)
        assert result.content == "Aqui está o resumo clínico do paciente."
        assert result.source_type == SourceType.AI_INFERENCE
        assert result.trust_level == TrustLevel.AI_INFERENCE
        assert result.provider == "mock"
        assert "latency_ms" in result.metadata
    
    @pytest.mark.asyncio
    async def test_runtime_collects_metrics(self, llm_runtime):
        messages = [LLMMessage(role=MessageRole.USER, content="resumo")]
        
        await llm_runtime.complete(
            messages=messages,
            source_type=SourceType.AI_INFERENCE,
        )
        
        summary = llm_runtime.get_metrics_summary()
        assert summary["total_calls"] == 1
        assert summary["successful_calls"] == 1
        assert summary["failed_calls"] == 0
    
    @pytest.mark.asyncio
    async def REDACTED(self, llm_runtime):
        messages = [LLMMessage(role=MessageRole.USER, content="resumo")]
        
        result = await llm_runtime.complete(
            messages=messages,
            source_type=SourceType.STRUCTURED_DATA,
        )
        
        assert not result.requires_human_verification()
        assert result.trust_level == TrustLevel.STRUCTURED_DATA


# ═══════════════════════════════════════════════════════════════════════
# PART 5: Clinical Context Builder
# ═══════════════════════════════════════════════════════════════════════

class TestClinicalContextBuilder:
    """Valida construção de contexto clínico para LLM."""
    
    @pytest.mark.asyncio
    async def REDACTED(self, env):
        env.create_patient_with_data()
        
        from araos.clinical.twin.models import PatientDigitalTwinBuilder
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)
        
        ctx_builder = ClinicalContextBuilder(max_tokens=2000)
        context = ctx_builder.build(twin=twin)
        
        assert "DADOS DO PACIENTE" in context.patient_context
        assert "Hipertensão" in context.patient_context
        assert "Losartana" in context.patient_context
        assert "Penicilina" in context.patient_context
        assert context.metadata["has_twin"] is True
        assert context.metadata["estimated_tokens"] > 0
    
    def REDACTED(self):
        builder = ClinicalContextBuilder()
        ctx = builder.build(twin=None)
        
        assert "NUNCA faça diagnósticos" in ctx.system_prompt
        assert "NUNCA prescreva medicamentos" in ctx.system_prompt
        assert "SEMPRE baseie suas respostas" in ctx.system_prompt


# ═══════════════════════════════════════════════════════════════════════
# PART 6: Concierge Agent
# ═══════════════════════════════════════════════════════════════════════

class TestConciergeAgent:
    """Valida agente Concierge inteligente."""
    
    def _make_context(self, env, message: str, channel: str = "whatsapp") -> AgentContext:
        tenant_ctx = TenantContext(
            tenant_id=env.tenant_id,
            organization_id=env.tenant_id,
        )
        identity_ctx = IdentityContext(
            actor_id="patient_001",
            actor_type=ActorType.USER,
            tenant_id=env.tenant_id,
            organization_id=env.tenant_id,
            permissions=["communication.send", "patient.read", "consultation.schedule"],
        )
        return AgentContext(
            tenant_context=tenant_ctx,
            identity_context=identity_ctx,
            input_data={"message": message, "channel": channel},
            correlation=CorrelationContext(correlation_id="test_corr_001"),
        )
    
    @pytest.mark.asyncio
    async def test_detects_scheduling_intent(self, env, llm_runtime):
        agent = ConciergeAgent(llm_runtime)
        context = self._make_context(env, "Quero agendar uma consulta")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["intent"] == "scheduling"
    
    @pytest.mark.asyncio
    async def test_detects_symptom_intent(self, env, llm_runtime):
        agent = ConciergeAgent(llm_runtime)
        context = self._make_context(env, "Estou com dor de cabeça e tontura")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["intent"] == "symptom_report"
    
    @pytest.mark.asyncio
    async def test_detects_clinical_question(self, env, llm_runtime):
        agent = ConciergeAgent(llm_runtime)
        context = self._make_context(env, "O que é câncer? É grave?")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["intent"] == "clinical_question"
        # Clinical questions must NOT require human verification
        # because they are redirected, not answered by AI
        response = result.output["response"]
        assert "médico" in response["content"].lower() or "profissional" in response["content"].lower()
    
    @pytest.mark.asyncio
    async def test_detects_information_request(self, env, llm_runtime):
        agent = ConciergeAgent(llm_runtime)
        context = self._make_context(env, "Qual o endereço da clínica?")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["intent"] == "information_request"


# ═══════════════════════════════════════════════════════════════════════
# PART 7: Voice Copilot Agent
# ═══════════════════════════════════════════════════════════════════════

class TestVoiceCopilotAgent:
    """Valida agente Voice Copilot read-only."""
    
    async def _make_context(self, env, command: str) -> AgentContext:
        from araos.clinical.twin.models import PatientDigitalTwinBuilder
        
        tenant_ctx = TenantContext(
            tenant_id=env.tenant_id,
            organization_id=env.tenant_id,
        )
        identity_ctx = IdentityContext(
            actor_id=env.doctor_id,
            actor_type=ActorType.PROFESSIONAL,
            tenant_id=env.tenant_id,
            organization_id=env.tenant_id,
            permissions=["voice.use", "patient.read", "consultation.read"],
        )
        
        builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
        twin = await builder.build(env.patient_id, env.tenant_id)
        
        return AgentContext(
            tenant_context=tenant_ctx,
            identity_context=identity_ctx,
            patient_twin=twin,
            input_data={"command": command, "consultation_id": "consulta_001"},
            correlation=CorrelationContext(correlation_id="test_corr_002"),
        )
    
    @pytest.mark.asyncio
    async def test_query_summary(self, env, llm_runtime):
        env.create_patient_with_data()
        agent = VoiceCopilotAgent(llm_runtime)
        context = await self._make_context(env, "Ara, resumo do paciente")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["query_type"] == "summary"
        
        response = result.output["response"]
        assert response["source_type"] == "structured_data" or response["source_type"] == "generated_summary"
        assert response["trust_level"] in ["structured_data", "generated_summary"]
    
    @pytest.mark.asyncio
    async def test_query_medications(self, env, llm_runtime):
        env.create_patient_with_data()
        agent = VoiceCopilotAgent(llm_runtime)
        context = await self._make_context(env, "Ara, quais medicamentos?")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["query_type"] == "medications"
        
        response = result.output["response"]
        assert "Losartana" in response["content"]
        assert response["source_type"] == "structured_data"
        assert not TrustedResponse(**response).requires_human_verification()
    
    @pytest.mark.asyncio
    async def test_query_allergies(self, env, llm_runtime):
        env.create_patient_with_data()
        agent = VoiceCopilotAgent(llm_runtime)
        context = await self._make_context(env, "Ara, tem alergias?")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["query_type"] == "allergies"
        
        response = result.output["response"]
        assert "Penicilina" in response["content"]
        assert response["source_type"] == "structured_data"
    
    @pytest.mark.asyncio
    async def test_query_diagnoses(self, env, llm_runtime):
        env.create_patient_with_data()
        agent = VoiceCopilotAgent(llm_runtime)
        context = await self._make_context(env, "Ara, diagnósticos?")
        
        result = await agent.execute(context)
        assert result.success is True
        assert result.output["query_type"] == "diagnoses"
        
        response = result.output["response"]
        assert "Hipertensão" in response["content"]
    
    @pytest.mark.asyncio
    async def test_missing_twin_returns_error(self, env, llm_runtime):
        agent = VoiceCopilotAgent(llm_runtime)
        
        tenant_ctx = TenantContext(
            tenant_id=env.tenant_id,
            organization_id=env.tenant_id,
        )
        identity_ctx = IdentityContext(
            actor_id=env.doctor_id,
            actor_type=ActorType.PROFESSIONAL,
            tenant_id=env.tenant_id,
            organization_id=env.tenant_id,
            permissions=["voice.use", "patient.read"],
        )
        context = AgentContext(
            tenant_context=tenant_ctx,
            identity_context=identity_ctx,
            patient_twin=None,
            input_data={"command": "resumo", "consultation_id": "c001"},
        )
        
        result = await agent.execute(context)
        assert result.success is False
        assert result.error == "MISSING_TWIN"


# ═══════════════════════════════════════════════════════════════════════
# PART 8: Observabilidade + Métricas
# ═══════════════════════════════════════════════════════════════════════

class TestObservability:
    """Valida observabilidade e métricas."""
    
    def REDACTED(self):
        collector = LLMMetricsCollector()
        
        from araos.intelligence.runtime.metrics import LLMCallMetric
        metric = LLMCallMetric(
            provider="mock",
            model="mock-model",
            latency_ms=15.5,
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            success=True,
        )
        
        collector.record(metric)
        summary = collector.summary()
        
        assert summary["total_calls"] == 1
        assert summary["successful_calls"] == 1
        assert summary["total_tokens"] == 15
    
    def test_metrics_estimated_cost(self):
        from araos.intelligence.runtime.metrics import LLMCallMetric
        
        metric = LLMCallMetric(
            provider="openai",
            model="gpt-4o-mini",
            latency_ms=10.0,
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            success=True,
        )
        
        cost = metric.estimated_cost_usd()
        assert cost > 0
        assert cost < 1.0  # Deve ser barato para gpt-4o-mini
    
    def REDACTED(self, llm_runtime):
        # O runtime já tem o router com mock provider
        # Summary deve estar vazio antes de chamadas
        summary = llm_runtime.get_metrics_summary()
        assert summary["total_calls"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
