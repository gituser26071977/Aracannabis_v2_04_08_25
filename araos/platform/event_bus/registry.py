"""
AraOS Platform — Handler Registry.

Registro de handlers de eventos.
Usado para descoberta e documentação de consumers.
"""

from typing import Dict, List, Callable, Optional, Any, Awaitable, Set
from dataclasses import dataclass

from .envelope import EventEnvelopeV2

Handler = Callable[[EventEnvelopeV2], Awaitable[None]]


@dataclass
class HandlerRegistration:
    """Registro de um handler."""
    handler: Handler
    event_types: List[str]
    consumer_group: str
    description: str = ""
    auto_dlq: bool = True


class HandlerRegistry:
    """
    Registro central de handlers.
    
    Usado para:
        - Documentação automática
        - Descoberta de consumers
        - Validação de coverage
        - Health checks
    """
    
    def __init__(self):
        self._handlers: Dict[str, HandlerRegistration] = {}
        self._event_coverage: Dict[str, Set[str]] = {}  # event_type -> consumer_groups
    
    def register(
        self,
        handler: Handler,
        event_types: List[str],
        consumer_group: str,
        description: str = "",
        auto_dlq: bool = True,
    ) -> None:
        """
        Registra handler no registry.
        
        Args:
            handler: Função async que processa eventos
            event_types: Tipos de evento suportados
            consumer_group: Grupo de consumidores
            description: Descrição do handler
            auto_dlq: Se True, usa DLQ em falhas
        """
        handler_id = f"{consumer_group}:{handler.__name__}"
        self._handlers[handler_id] = HandlerRegistration(
            handler=handler,
            event_types=event_types,
            consumer_group=consumer_group,
            description=description,
            auto_dlq=auto_dlq,
        )
        
        # Registrar coverage
        for event_type in event_types:
            if event_type not in self._event_coverage:
                self._event_coverage[event_type] = set()
            self._event_coverage[event_type].add(consumer_group)
    
    def get_handlers_for(self, event_type: str) -> List[HandlerRegistration]:
        """Retorna handlers para um tipo de evento."""
        return [
            reg for reg in self._handlers.values()
            if event_type in reg.event_types
        ]
    
    def get_coverage(self, event_type: str) -> List[str]:
        """Retorna consumer groups que consomem um evento."""
        return list(self._event_coverage.get(event_type, set()))
    
    def list_all(self) -> List[Dict[str, Any]]:
        """Lista todos os handlers registrados."""
        return [
            {
                "handler_id": hid,
                "event_types": reg.event_types,
                "consumer_group": reg.consumer_group,
                "description": reg.description,
                "auto_dlq": reg.auto_dlq,
            }
            for hid, reg in self._handlers.items()
        ]
    
    def get_uncovered_events(self, all_event_types: List[str]) -> List[str]:
        """
        Retorna eventos sem consumers.
        
        Útil para garantir que todo evento tem pelo menos um handler.
        """
        return [
            et for et in all_event_types
            if et not in self._event_coverage
        ]
