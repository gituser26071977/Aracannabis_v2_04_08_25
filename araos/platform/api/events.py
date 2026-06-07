"""
AraOS Platform API — Events.

Contrato para endpoints de eventos.

Endpoints:
    POST   /platform/events
    GET    /platform/events/{event_id}
    GET    /platform/events/correlation/{correlation_id}
    POST   /platform/events/replay
    GET    /platform/events/metrics
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class EventAPI(ABC):
    """Contrato para API de eventos."""
    
    @abstractmethod
    async def publish_event(
        self,
        tenant_id: str,
        event_data: Dict[str, Any],
    ) -> str:
        """Publica evento no bus."""
        ...
    
    @abstractmethod
    async def get_event(self, tenant_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """Busca evento por ID."""
        ...
    
    @abstractmethod
    async def get_correlation_chain(
        self,
        tenant_id: str,
        correlation_id: str,
    ) -> List[Dict[str, Any]]:
        """Retorna cadeia de correlação."""
        ...
    
    @abstractmethod
    async def replay_events(
        self,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
    ) -> List[Dict[str, Any]]:
        """Replay de eventos."""
        ...
    
    @abstractmethod
    async def get_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Retorna métricas do event bus."""
        ...
