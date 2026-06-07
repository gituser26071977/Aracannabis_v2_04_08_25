"""
AraOS Agents — Event Catalog.

Eventos específicos do runtime de agentes.

Novos eventos:
    AGENT_STARTED
    AGENT_COMPLETED
    AGENT_FAILED
    AGENT_ACTION_EXECUTED
    AGENT_CONTEXT_LOADED

Integração:
    Estes eventos são adicionados ao catálogo oficial da plataforma.
"""

from typing import Set


class AgentEventCatalog:
    """Catálogo de eventos de agentes."""
    
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_COMPLETED = "AGENT_COMPLETED"
    AGENT_FAILED = "AGENT_FAILED"
    AGENT_ACTION_EXECUTED = "AGENT_ACTION_EXECUTED"
    AGENT_CONTEXT_LOADED = "AGENT_CONTEXT_LOADED"
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_UNREGISTERED = "AGENT_UNREGISTERED"
    
    ALL_AGENT_EVENTS: Set[str] = {
        AGENT_STARTED,
        AGENT_COMPLETED,
        AGENT_FAILED,
        AGENT_ACTION_EXECUTED,
        AGENT_CONTEXT_LOADED,
        AGENT_REGISTERED,
        AGENT_UNREGISTERED,
    }
    
    @classmethod
    def is_agent_event(cls, event_type: str) -> bool:
        """Verifica se é um evento de agente."""
        return event_type in cls.ALL_AGENT_EVENTS
    
    @classmethod
    def register_in_platform_catalog(cls) -> None:
        """
        Registra eventos de agente no catálogo oficial.
        
        Nota: O catálogo oficial usa dict, então esta função
        adiciona os eventos dinamicamente.
        """
        from araos.platform.events.catalog import _EVENT_CATALOG, EventDefinition
        
        definitions = {
            cls.AGENT_STARTED: EventDefinition(
                event_type=cls.AGENT_STARTED,
                domain="agent",
                action="started",
                aggregate_type="agent_session",
                description="Agente iniciou execução",
                consumers=["audit", "monitoring"],
            ),
            cls.AGENT_COMPLETED: EventDefinition(
                event_type=cls.AGENT_COMPLETED,
                domain="agent",
                action="completed",
                aggregate_type="agent_session",
                description="Agente completou execução",
                consumers=["audit", "monitoring"],
            ),
            cls.AGENT_FAILED: EventDefinition(
                event_type=cls.AGENT_FAILED,
                domain="agent",
                action="failed",
                aggregate_type="agent_session",
                description="Agente falhou na execução",
                consumers=["audit", "monitoring"],
            ),
            cls.AGENT_ACTION_EXECUTED: EventDefinition(
                event_type=cls.AGENT_ACTION_EXECUTED,
                domain="agent",
                action="executed",
                aggregate_type="agent_action",
                description="Agente executou uma ação",
                consumers=["audit"],
            ),
            cls.AGENT_CONTEXT_LOADED: EventDefinition(
                event_type=cls.AGENT_CONTEXT_LOADED,
                domain="agent",
                action="loaded",
                aggregate_type="agent_context",
                description="Contexto do agente carregado",
                consumers=["audit"],
            ),
            cls.AGENT_REGISTERED: EventDefinition(
                event_type=cls.AGENT_REGISTERED,
                domain="agent",
                action="registered",
                aggregate_type="agent",
                description="Agente registrado no runtime",
                consumers=["audit"],
            ),
            cls.AGENT_UNREGISTERED: EventDefinition(
                event_type=cls.AGENT_UNREGISTERED,
                domain="agent",
                action="unregistered",
                aggregate_type="agent",
                description="Agente removido do runtime",
                consumers=["audit"],
            ),
        }
        
        _EVENT_CATALOG.update(definitions)


# Auto-registrar na importação
AgentEventCatalog.register_in_platform_catalog()
