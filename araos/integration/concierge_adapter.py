"""
AraOS Integration — Concierge Adapter.

Adapter para integração com o Concierge.
Desacopla o Agent Runtime do módulo de atendimento.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ConciergeMessage:
    """Mensagem do Concierge."""
    message_id: str
    channel: str  # whatsapp, email, web
    sender_id: str
    patient_id: Optional[str]
    text: str
    tenant_id: str
    session_id: Optional[str] = None


@dataclass
class ConciergeResponse:
    """Resposta para o Concierge."""
    response_text: str
    recipient_id: str
    channel: str
    suggested_actions: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


class ConciergeAdapter(ABC):
    """
    Adapter para o módulo Concierge.
    
    Implementações futuras:
        - DirectConciergeAdapter
        - HTTPConciergeAdapter
        - WebSocketConciergeAdapter
    """
    
    @abstractmethod
    async def process_message(self, message: ConciergeMessage) -> ConciergeResponse:
        """Processa mensagem recebida."""
        ...
    
    @abstractmethod
    async def send_message(self, response: ConciergeResponse) -> None:
        """Envia mensagem de resposta."""
        ...
    
    @abstractmethod
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retorna histórico de conversa."""
        ...
