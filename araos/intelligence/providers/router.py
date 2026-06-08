"""
AraOS Intelligence — LLM Router.

Seleciona o provider mais adequado para cada requisição.
Implementa fallback chain para resiliência.
"""

from typing import List, Dict, Any, Optional
import time

from ..llm import LLMProvider, LLMRequest, LLMResponse
from ..trust.levels import TrustedResponse, SourceType, TrustLevel


class LLMRouter:
    """
    Roteador de LLM providers.
    
    Responsabilidades:
        1. Selecionar provider por capacidade/custo/latência
        2. Implementar fallback chain
        3. Registrar métricas de cada chamada
    
    Uso:
        router = LLMRouter()
        router.register("openai", OpenAIProvider(api_key=...), priority=1)
        router.register("gemini", GeminiProvider(api_key=...), priority=2)
        
        response = await router.route(request)
    """
    
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._priorities: Dict[str, int] = {}
        self._metrics: List[Dict[str, Any]] = []
        self._fallback_count = 0
    
    def register(
        self,
        name: str,
        provider: LLMProvider,
        priority: int = 0,
    ) -> None:
        """Registra um provider no roteador."""
        self._providers[name] = provider
        self._priorities[name] = priority
    
    def unregister(self, name: str) -> None:
        """Remove um provider."""
        self._providers.pop(name, None)
        self._priorities.pop(name, None)
    
    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Retorna provider por nome."""
        return self._providers.get(name)
    
    def list_providers(self) -> List[str]:
        """Lista providers ordenados por prioridade."""
        return sorted(
            self._providers.keys(),
            key=lambda n: self._priorities.get(n, 0),
            reverse=True,
        )
    
    async def route(
        self,
        request: LLMRequest,
        preferred_provider: Optional[str] = None,
    ) -> LLMResponse:
        """
        Rota requisição para o provider mais adequado.
        
        Args:
            request: Requisição LLM
            preferred_provider: Nome do provider preferido (opcional)
        
        Returns:
            LLMResponse do primeiro provider que responder com sucesso
        """
        providers = self._get_provider_chain(preferred_provider)
        
        last_error = None
        for name, provider in providers:
            start = time.perf_counter()
            try:
                response = await provider.complete(request)
                latency_ms = (time.perf_counter() - start) * 1000
                
                self._record_metric(
                    provider=name,
                    model=response.model,
                    latency_ms=latency_ms,
                    tokens=response.usage.get("total_tokens", 0),
                    success=True,
                    fallback=self._fallback_count > 0,
                )
                
                # Adicionar provider name aos metadados
                response.metadata["provider_name"] = name
                return response
                
            except Exception as e:
                latency_ms = (time.perf_counter() - start) * 1000
                self._record_metric(
                    provider=name,
                    model="",
                    latency_ms=latency_ms,
                    tokens=0,
                    success=False,
                    error=str(e),
                )
                last_error = e
                self._fallback_count += 1
                continue
        
        # Todos os providers falharam
        raise LLMRouterError(
            f"Todos os providers falharam. Último erro: {last_error}"
        )
    
    def _get_provider_chain(
        self,
        preferred: Optional[str] = None,
    ) -> List[tuple]:
        """Retorna lista de (name, provider) ordenada por prioridade."""
        names = self.list_providers()
        
        if preferred and preferred in names:
            names.remove(preferred)
            names.insert(0, preferred)
        
        return [(n, self._providers[n]) for n in names]
    
    def _record_metric(self, **kwargs) -> None:
        """Registra métrica de chamada."""
        self._metrics.append(kwargs)
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """Retorna todas as métricas registradas."""
        return self._metrics.copy()
    
    def get_fallback_count(self) -> int:
        """Retorna número de fallbacks ocorridos."""
        return self._fallback_count
    
    def clear_metrics(self) -> None:
        """Limpa métricas."""
        self._metrics.clear()
        self._fallback_count = 0


class LLMRouterError(Exception):
    """Erro quando todos os providers falham."""
    pass
