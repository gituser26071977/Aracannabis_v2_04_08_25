"""
AraOS Platform API — Twin.

Contrato para endpoints do Patient Digital Twin.

Endpoints:
    GET    /platform/twin/{patient_id}
    GET    /platform/twin/{patient_id}/profile
    GET    /platform/twin/{patient_id}/timeline
    GET    /platform/twin/{patient_id}/summary
    GET    /platform/twin/{patient_id}/graph
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class TwinAPI(ABC):
    """Contrato para API de Patient Digital Twin."""
    
    @abstractmethod
    async def get_twin(self, tenant_id: str, patient_id: str) -> Dict[str, Any]:
        """Retorna Digital Twin completo."""
        ...
    
    @abstractmethod
    async def get_profile(self, tenant_id: str, patient_id: str) -> Dict[str, Any]:
        """Retorna Clinical Profile."""
        ...
    
    @abstractmethod
    async def get_timeline(
        self,
        tenant_id: str,
        patient_id: str,
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retorna Clinical Timeline."""
        ...
    
    @abstractmethod
    async def get_summary(self, tenant_id: str, patient_id: str) -> Dict[str, Any]:
        """Retorna resumo clínico."""
        ...
    
    @abstractmethod
    async def get_graph(self, tenant_id: str, patient_id: str) -> Dict[str, Any]:
        """Retorna Clinical Graph."""
        ...
