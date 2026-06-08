"""
AraOS Intelligence — Observability.

Hooks para auditoria, tracing e logging de chamadas LLM.
Integra com Audit Ledger da plataforma.
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

from ..llm import LLMRequest, LLMResponse
from ..trust.levels import TrustedResponse


@dataclass
class LLMObservabilityEvent:
    """Evento de observabilidade de chamada LLM."""
    provider: str
    model: str
    latency_ms: float
    tokens: Dict[str, int]
    success: bool
    error: Optional[str]
    request_preview: str  # Primeiros 200 chars da última mensagem
    response_preview: str  # Primeiros 200 chars da resposta
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    actor_id: Optional[str] = None


class LLMObservability:
    """
    Observability para chamadas LLM.
    
    Responsabilidades:
        1. Registrar chamadas no Audit Ledger
        2. Emitir métricas para collectors externos
        3. Log structured para debug
    
    Uso:
        obs = LLMObservability()
        obs.on_before_call(request)
        response = await provider.complete(request)
        obs.on_after_call(request, response, latency_ms)
    """
    
    def __init__(self):
        self._hooks: List[Callable] = []
        self._audit_callback: Optional[Callable] = None
    
    def register_hook(self, hook: Callable[[LLMObservabilityEvent], None]) -> None:
        """Registra um hook que será chamado após cada chamada LLM."""
        self._hooks.append(hook)
    
    def set_audit_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Define callback para auditoria.
        
        O callback recebe um dict com os dados da chamada.
        Em produção, isso deve enviar para AuditService.
        """
        self._audit_callback = callback
    
    def emit(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        request: LLMRequest,
        response: Optional[LLMResponse] = None,
        error: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> None:
        """Emite evento de observabilidade."""
        event = LLMObservabilityEvent(
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            tokens=response.usage if response else {},
            success=response is not None and error is None,
            error=error,
            request_preview=request.messages[-1].content[:200] if request.messages else "",
            response_preview=response.content[:200] if response else "",
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
        )
        
        # Chamar hooks
        for hook in self._hooks:
            try:
                hook(event)
            except Exception:
                pass
        
        # Audit callback
        if self._audit_callback:
            try:
                self._audit_callback(event.to_dict())
            except Exception:
                pass
    
    def create_audit_entry(
        self,
        event: LLMObservabilityEvent,
    ) -> Dict[str, Any]:
        """
        Cria entrada de audit ledger a partir de evento LLM.
        
        Returns:
            Dict compatível com AuditEntryData
        """
        return {
            "tenant_id": event.tenant_id or "system",
            "actor_id": event.actor_id or "ai_agent",
            "actor_type": "agent",
            "action": "LLM_INFERENCE",
            "resource_type": "llm_call",
            "resource_id": event.correlation_id or "",
            "before": {
                "request_preview": event.request_preview,
            },
            "after": {
                "response_preview": event.response_preview,
                "provider": event.provider,
                "model": event.model,
                "tokens": event.tokens,
            },
            "changes_summary": f"LLM call via {event.provider}/{event.model} — {event.latency_ms:.0f}ms",
            "correlation_id": event.correlation_id,
        }
