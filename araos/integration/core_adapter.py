"""
AraOS Integration — Core Adapter.

Adapter para integração com o Core (SIAP).
Desacopla o Agent Runtime do backend principal.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CorePatientQuery:
    """Query para busca de paciente no Core."""
    patient_id: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tenant_id: Optional[str] = None


@dataclass
class CoreConsultation:
    """Dados de consulta do Core."""
    consultation_id: str
    patient_id: str
    doctor_id: str
    clinic_id: str
    scheduled_at: str
    status: str
    notes: Optional[str] = None


class CoreAdapter(ABC):
    """
    Adapter para o Core (SIAP).
    
    Implementações futuras:
        - DirectCoreAdapter: acesso direto aos models
        - HTTPCoreAdapter: via API REST
    """
    
    @abstractmethod
    async def get_patient(self, query: CorePatientQuery) -> Optional[Dict[str, Any]]:
        """Busca paciente no Core."""
        ...
    
    @abstractmethod
    async def create_consultation(self, consultation: CoreConsultation) -> str:
        """Cria consulta no Core."""
        ...
    
    @abstractmethod
    async def get_consultation(self, consultation_id: str) -> Optional[CoreConsultation]:
        """Busca consulta no Core."""
        ...
    
    @abstractmethod
    async def list_professionals(
        self,
        tenant_id: str,
        specialty: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lista profissionais do tenant."""
        ...
    
    @abstractmethod
    async def create_patient(self, patient_data: Dict[str, Any]) -> str:
        """Cria paciente no Core."""
        ...
