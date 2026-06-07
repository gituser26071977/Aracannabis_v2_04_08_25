"""
AraOS Clinical — Voice Adapter Contract.

Contrato para integração do Voice Copilot com o Clinical Intelligence Foundation.

Preparação para comandos de voz como:
    "Ara, resumo do paciente."
    "Ara, quais as alergias?"
    "Ara, últimos exames."
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class VoiceQuery:
    """Query do Voice Copilot."""
    patient_id: str
    query_type: str  # summary, allergies, medications, exams, timeline, diagnosis
    tenant_id: str
    consultation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@dataclass
class VoiceResponse:
    """Resposta estruturada para o Voice."""
    text: str
    data: Dict[str, Any]
    source: str = "clinical_foundation"
    confidence: float = 1.0


class VoiceClinicalAdapter(ABC):
    """
    Adaptador para comandos de voz clínicos.
    
    Implementações futuras:
        - DirectVoiceAdapter: acessa diretamente os modelos
        - APIVoiceAdapter: acessa via HTTP
    """
    
    @abstractmethod
    async def get_patient_summary(self, query: VoiceQuery) -> VoiceResponse:
        """Retorna resumo clínico do paciente."""
        ...
    
    @abstractmethod
    async def get_allergies(self, query: VoiceQuery) -> VoiceResponse:
        """Retorna alergias do paciente."""
        ...
    
    @abstractmethod
    async def get_medications(self, query: VoiceQuery) -> VoiceResponse:
        """Retorna medicações ativas."""
        ...
    
    @abstractmethod
    async def get_recent_exams(self, query: VoiceQuery) -> VoiceResponse:
        """Retorna exames recentes."""
        ...
    
    @abstractmethod
    async def get_timeline(self, query: VoiceQuery) -> VoiceResponse:
        """Retorna timeline resumida."""
        ...
    
    @abstractmethod
    async def execute_command(
        self,
        query: VoiceQuery,
    ) -> VoiceResponse:
        """
        Roteia query para o handler correto.
        
        Uso:
            response = await adapter.execute_command(
                VoiceQuery(patient_id="pat_123", query_type="summary", tenant_id="org_1")
            )
        """
        ...
