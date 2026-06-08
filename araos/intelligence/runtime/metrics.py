"""
AraOS Intelligence — LLM Metrics.

Coleta métricas de execução de LLM:
    - latência
    - tokens
    - custo estimado
    - falhas
    - fallback
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LLMCallMetric:
    """Métrica de uma chamada LLM."""
    provider: str
    model: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    success: bool
    fallback: bool = False
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Custo estimado (USD por 1K tokens)
    COST_PER_1K: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gemini-1.5-flash": {"input": 0.00035, "output": 0.00105},
        "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
        "mock-model": {"input": 0.0, "output": 0.0},
    })
    
    def estimated_cost_usd(self) -> float:
        """Estima custo da chamada em USD."""
        rates = self.COST_PER_1K.get(self.model, {"input": 0.0, "output": 0.0})
        input_cost = (self.prompt_tokens / 1000) * rates["input"]
        output_cost = (self.completion_tokens / 1000) * rates["output"]
        return round(input_cost + output_cost, 6)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "latency_ms": round(self.latency_ms, 2),
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd(),
            "success": self.success,
            "fallback": self.fallback,
            "error": self.error,
            "timestamp": self.timestamp.isoformat(),
        }


class LLMMetricsCollector:
    """
    Coletor de métricas LLM.
    
    Uso:
        collector = LLMMetricsCollector()
        collector.record(metric)
        
        summary = collector.summary()
        print(summary["total_calls"], summary["avg_latency_ms"])
    """
    
    def __init__(self):
        self._metrics: List[LLMCallMetric] = []
    
    def record(self, metric: LLMCallMetric) -> None:
        """Registra uma métrica."""
        self._metrics.append(metric)
    
    def record_from_response(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        usage: Dict[str, int],
        success: bool,
        fallback: bool = False,
        error: Optional[str] = None,
    ) -> LLMCallMetric:
        """Cria e registra métrica a partir de uma resposta LLM."""
        metric = LLMCallMetric(
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            success=success,
            fallback=fallback,
            error=error,
        )
        self.record(metric)
        return metric
    
    def summary(self) -> Dict[str, Any]:
        """Retorna resumo estatístico."""
        if not self._metrics:
            return {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "fallback_count": 0,
                "avg_latency_ms": 0.0,
                "total_tokens": 0,
                "total_estimated_cost_usd": 0.0,
            }
        
        total = len(self._metrics)
        successful = sum(1 for m in self._metrics if m.success)
        failed = total - successful
        fallbacks = sum(1 for m in self._metrics if m.fallback)
        avg_latency = sum(m.latency_ms for m in self._metrics) / total
        total_tokens = sum(m.total_tokens for m in self._metrics)
        total_cost = sum(m.estimated_cost_usd() for m in self._metrics)
        
        return {
            "total_calls": total,
            "successful_calls": successful,
            "failed_calls": failed,
            "fallback_count": fallbacks,
            "avg_latency_ms": round(avg_latency, 2),
            "total_tokens": total_tokens,
            "total_estimated_cost_usd": round(total_cost, 6),
        }
    
    def get_metrics(self) -> List[LLMCallMetric]:
        """Retorna todas as métricas."""
        return self._metrics.copy()
    
    def clear(self) -> None:
        """Limpa todas as métricas."""
        self._metrics.clear()
