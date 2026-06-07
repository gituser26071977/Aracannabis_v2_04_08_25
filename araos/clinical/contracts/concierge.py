"""
AraOS Clinical — Concierge Adapter Contract.

Contrato para integração do Concierge IA com o Clinical Intelligence Foundation.

Preparação para interações como:
    "O paciente possui alergias?"
    "Quais medicações o paciente toma?"
    "Agende retorno para paciente hipertenso."
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ConciergeQuery:
    """Query do Concierge."""
    patient_id: str
    question: str
    tenant_id: str
    channel: str = "whatsapp"  # whatsapp, email, web
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class ConciergeResponse:
    """Resposta estruturada para o Concierge."""
    text: str
    data: Dict[str, Any]
    suggested_actions: List[Dict[str, Any]] = None
    source: str = "clinical_foundation"
    confidence: float = 1.0
    
    def __post_init__(self):
        if self.suggested_actions is None:
            self.suggested_actions = []


class ConciergeClinicalAdapter(ABC):
    """
    Adaptador para consultas do Concierge.
    
    Implementações futuras:
        - DirectConciergeAdapter
        - APIConciergeAdapter
    """
    
    @abstractmethod
    async def answer_question(self, query: ConciergeQuery) -> ConciergeResponse:
        """Responde pergunta sobre paciente."""
        ...
    
    @abstractmethod
    async def check_allergies(self, query: ConciergeQuery) -> ConciergeResponse:
        """Verifica alergias do paciente."""
        ...
    
    @abstractmethod
    async def check_medications(self, query: ConciergeQuery) -> ConciergeResponse:
        """Verifica medicações do paciente."""
        ...
    
    @abstractmethod
    async def suggest_next_steps(self, query: ConciergeQuery) -> ConciergeResponse:
        """Sugere próximos passos baseado no perfil."""
        ...
