"""
AraOS Intelligence Layer.

Week 7B — Intelligence Layer v1

Componentes:
    - LLMProvider: contrato para providers de LLM
    - LLMRuntime: orquestração de execução
    - LLMRouter: roteamento e fallback
    - ClinicalContextBuilder: contexto clínico para LLM
    - Trust Levels: proveniência de todas as respostas
"""

from .llm import LLMProvider, LLMMessage, LLMResponse, LLMRequest, MessageRole
from .embeddings import EmbeddingProvider, EmbeddingResult
from .vector import VectorStoreProvider, VectorSearchResult

from .trust.levels import TrustLevel, SourceType, TrustedResponse

from .providers.mock_provider import MockLLMProvider
from .providers.openai_provider import OpenAIProvider
from .providers.gemini_provider import GeminiProvider
from .providers.claude_provider import ClaudeProvider
from .providers.router import LLMRouter, LLMRouterError

from .runtime.runtime import LLMRuntime
from .runtime.metrics import LLMMetricsCollector, LLMCallMetric
from .runtime.observability import LLMObservability

from .context.builder import ClinicalContextBuilder, ClinicalContext

__all__ = [
    # Contratos
    "LLMProvider",
    "LLMMessage",
    "LLMResponse",
    "LLMRequest",
    "MessageRole",
    "EmbeddingProvider",
    "EmbeddingResult",
    "VectorStoreProvider",
    "VectorSearchResult",
    # Trust
    "TrustLevel",
    "SourceType",
    "TrustedResponse",
    # Providers
    "MockLLMProvider",
    "OpenAIProvider",
    "GeminiProvider",
    "ClaudeProvider",
    "LLMRouter",
    "LLMRouterError",
    # Runtime
    "LLMRuntime",
    "LLMMetricsCollector",
    "LLMCallMetric",
    "LLMObservability",
    # Context
    "ClinicalContextBuilder",
    "ClinicalContext",
]
