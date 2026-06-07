"""
AraOS Integration — Smart Flow Adapter.

Adapter para integração com o Visual Smart Flow.
Desacopla o Agent Runtime do módulo de fluxo visual.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class FlowEvent:
    """Evento do Smart Flow."""
    event_type: str  # CHECKIN_COMPLETED, PATIENT_ARRIVED, etc
    patient_id: str
    clinic_id: str
    room_id: Optional[str]
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FlowAction:
    """Ação para o Smart Flow."""
    action_type: str  # notify, update_display, open_door
    target_id: str
    payload: Dict[str, Any]


class SmartFlowAdapter(ABC):
    """
    Adapter para o módulo Smart Flow.
    
    Implementações futuras:
        - DirectSmartFlowAdapter
        - HTTPSmartFlowAdapter
    """
    
    @abstractmethod
    async def get_patient_flow_status(self, patient_id: str) -> Dict[str, Any]:
        """Retorna status do paciente no fluxo."""
        ...
    
    @abstractmethod
    async def send_action(self, action: FlowAction) -> bool:
        """Envia ação para o Smart Flow."""
        ...
    
    @abstractmethod
    async def subscribe_to_events(
        self,
        event_types: List[str],
        handler,
    ) -> None:
        """Inscreve em eventos do Smart Flow."""
        ...
