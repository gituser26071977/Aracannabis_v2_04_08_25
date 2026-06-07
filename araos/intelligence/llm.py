"""
AraOS Intelligence — LLM Provider Contract.

Preparação para integração com LLMs:
    - OpenAI GPT
    - Google Gemini
    - Anthropic Claude
    - Modelos locais futuros

Apenas contrato. Sem implementação.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class MessageRole(str, Enum):
    """Papéis em uma conversa."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """Mensagem para LLM."""
    role: MessageRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Resposta de LLM."""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMRequest:
    """Requisição para LLM."""
    messages: List[LLMMessage]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    response_format: Optional[str] = None  # json, text


class LLMProvider(ABC):
    """
    Contrato para providers de LLM.
    
    Implementações futuras:
        - OpenAIProvider
        - GeminiProvider
        - ClaudeProvider
        - LocalLLMProvider
    """
    
    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Gera completion a partir de mensagens."""
        ...
    
    @abstractmethod
    async def stream(self, request: LLMRequest):
        """Stream de tokens (preparação)."""
        ...
    
    @abstractmethod
    def get_models(self) -> List[str]:
        """Retorna modelos disponíveis."""
        ...
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Gera embedding (se provider suportar)."""
        ...
