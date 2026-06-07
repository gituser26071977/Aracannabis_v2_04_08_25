"""
AraOS Platform — Event Router.

Roteia eventos para handlers baseado no tipo.
Suporta:
    - Roteamento por event_type
    - Roteamento por event_category
    - Roteamento por tenant_id (filtro)
    - Roteamento por priority
"""

from typing import Dict, List, Callable, Optional, Any, Awaitable

from .envelope import EventEnvelopeV2, EventCategory, EventPriority

Handler = Callable[[EventEnvelopeV2], Awaitable[None]]


class EventRouter:
    """
    Roteador de eventos.
    
    Uso:
        router = EventRouter()
        router.on("PATIENT_CREATED", patient_handler)
        router.on_category("clinical", clinical_handler)
        
        await router.route(event)
    """
    
    def __init__(self):
        self._type_handlers: Dict[str, List[Handler]] = {}
        self._category_handlers: Dict[EventCategory, List[Handler]] = {}
        self._catch_all: List[Handler] = []
        self._filters: List[Callable[[EventEnvelopeV2], bool]] = []
    
    def on(self, event_type: str, handler: Handler) -> None:
        """Registra handler para tipo específico."""
        if event_type not in self._type_handlers:
            self._type_handlers[event_type] = []
        self._type_handlers[event_type].append(handler)
    
    def on_category(self, category: EventCategory, handler: Handler) -> None:
        """Registra handler para categoria."""
        if category not in self._category_handlers:
            self._category_handlers[category] = []
        self._category_handlers[category].append(handler)
    
    def on_all(self, handler: Handler) -> None:
        """Registra handler para todos os eventos."""
        self._catch_all.append(handler)
    
    def add_filter(self, filter_fn: Callable[[EventEnvelopeV2], bool]) -> None:
        """
        Adiciona filtro global.
        
        Se filtro retornar False, evento não é roteado.
        """
        self._filters.append(filter_fn)
    
    async def route(self, event: EventEnvelopeV2) -> int:
        """
        Roteia evento para todos os handlers matching.
        
        Returns:
            Número de handlers invocados
        """
        # Aplicar filtros
        for filter_fn in self._filters:
            if not filter_fn(event):
                return 0
        
        count = 0
        handlers = set()
        
        # Por tipo
        for h in self._type_handlers.get(event.event_type, []):
            handlers.add(h)
        
        # Por categoria
        for h in self._category_handlers.get(event.event_category, []):
            handlers.add(h)
        
        # Catch-all
        for h in self._catch_all:
            handlers.add(h)
        
        # Invocar
        for handler in handlers:
            try:
                await handler(event)
                count += 1
            except Exception:
                # Erro em handler não bloqueia outros
                pass
        
        return count
