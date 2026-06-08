"""
AraOS Intelligence — LLM Runtime.

Orquestração de execução LLM:
    - Roteamento
    - Métricas
    - Observabilidade
    - Fallback
    - Trust Levels

Week 7B — Intelligence Layer v1
"""

from typing import Dict, Any, Optional, List
import time

from ..llm import LLMProvider, LLMRequest, LLMResponse, LLMMessage, MessageRole
from ..trust.levels import TrustedResponse, SourceType, TrustLevel
from ..providers.router import LLMRouter
from .metrics import LLMMetricsCollector, LLMCallMetric
from .observability import LLMObservability


class LLMRuntime:
    """
    Runtime central para execução de LLM no AraOS.
    
    Responsabilidades:
        1. Orquestrar chamadas LLM via Router
        2. Coletar métricas automaticamente
        3. Registrar observabilidade (audit)
        4. Adicionar Trust Level em todas as respostas
        5. Gerenciar fallback entre providers
    
    Uso:
        runtime = LLMRuntime(router)
        trusted = await runtime.complete(
            messages=[...],
            source_type=SourceType.AI_INFERENCE,
            correlation_id="corr_001",
            tenant_id="tenant_001",
        )
        # → TrustedResponse com proveniência e métricas
    """
    
    def __init__(
        self,
        router: LLMRouter,
        metrics_collector: Optional[LLMMetricsCollector] = None,
        observability: Optional[LLMObservability] = None,
    ):
        self.router = router
        self.metrics = metrics_collector or LLMMetricsCollector()
        self.observability = observability or LLMObservability()
    
    async def complete(
        self,
        messages: List[LLMMessage],
        source_type: SourceType,
        trust_level: Optional[TrustLevel] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        preferred_provider: Optional[str] = None,
    ) -> TrustedResponse:
        """
        Executa completion LLM com observabilidade completa.
        
        Args:
            messages: Lista de mensagens para o LLM
            source_type: Fonte da informação (STRUCTURED_DATA, GENERATED_SUMMARY, AI_INFERENCE)
            trust_level: Nível de confiança (auto-calculado se não informado)
            model: Modelo específico (opcional)
            temperature: Temperatura de sampling
            max_tokens: Máximo de tokens na resposta
            correlation_id: ID de correlação para rastreamento
            tenant_id: ID do tenant
            actor_id: ID do ator
            preferred_provider: Provider preferencial
        
        Returns:
            TrustedResponse com content, source_type, trust_level, métricas
        """
        request = LLMRequest(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        start = time.perf_counter()
        error = None
        response = None
        provider_name = preferred_provider or "default"
        
        try:
            response = await self.router.route(request, preferred_provider)
            provider_name = response.metadata.get("provider_name", provider_name)
        except Exception as e:
            error = str(e)
        
        latency_ms = (time.perf_counter() - start) * 1000
        
        # Registrar métrica
        if response:
            self.metrics.record_from_response(
                provider=provider_name,
                model=response.model,
                latency_ms=latency_ms,
                usage=response.usage,
                success=error is None,
                fallback=self.router.get_fallback_count() > 0,
                error=error,
            )
        else:
            self.metrics.record_from_response(
                provider=provider_name,
                model="",
                latency_ms=latency_ms,
                usage={},
                success=False,
                fallback=self.router.get_fallback_count() > 0,
                error=error,
            )
        
        # Observabilidade
        self.observability.emit(
            provider=provider_name,
            model=response.model if response else "",
            latency_ms=latency_ms,
            request=request,
            response=response,
            error=error,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
        )
        
        # Construir TrustedResponse
        if response:
            content = response.content
        else:
            content = f"[Erro na inferência: {error}]"
        
        # Auto-calcular trust_level se não informado
        if trust_level is None:
            trust_level = self._infer_trust_level(source_type)
        
        return TrustedResponse(
            content=content,
            source_type=source_type,
            trust_level=trust_level,
            provider=provider_name,
            model=response.model if response else "",
            metadata={
                "latency_ms": round(latency_ms, 2),
                "tokens": response.usage if response else {},
                "fallback_used": self.router.get_fallback_count() > 0,
                "correlation_id": correlation_id,
            },
        )
    
    def _infer_trust_level(self, source_type: SourceType) -> TrustLevel:
        """Infere trust level a partir do source type."""
        mapping = {
            SourceType.STRUCTURED_DATA: TrustLevel.STRUCTURED_DATA,
            SourceType.GENERATED_SUMMARY: TrustLevel.GENERATED_SUMMARY,
            SourceType.AI_INFERENCE: TrustLevel.AI_INFERENCE,
        }
        return mapping.get(source_type, TrustLevel.AI_INFERENCE)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retorna resumo de métricas."""
        return self.metrics.summary()
