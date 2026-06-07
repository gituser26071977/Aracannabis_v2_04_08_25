"""
AraOS Integration — Voice Adapter.

Adapter para integração com o Voice Copilot.
Desacopla o Agent Runtime do módulo de voz.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class VoiceCommand:
    """Comando de voz."""
    session_id: str
    patient_id: Optional[str]
    consultation_id: Optional[str]
    command_text: str  # "Ara, resumo do paciente"
    tenant_id: str
    user_id: Optional[str]


@dataclass
class VoiceCommandResult:
    """Resultado de comando de voz."""
    response_text: str
    action_taken: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class VoiceAdapter(ABC):
    """
    Adapter para o módulo de voz.
    
    Implementações futuras:
        - DirectVoiceAdapter: integração direta
        - HTTPVoiceAdapter: via API HTTP
        - WebSocketVoiceAdapter: via WebSocket
    """
    
    @abstractmethod
    async def process_command(self, command: VoiceCommand) -> VoiceCommandResult:
        """Processa comando de voz."""
        ...
    
    @abstractmethod
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Retorna contexto de uma sessão de voz."""
        ...
    
    @abstractmethod
    async def send_response(self, session_id: str, response_text: str) -> None:
        """Envia resposta para sessão de voz."""
        ...
