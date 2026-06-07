"""
AraOS Platform — Event Bus Contracts.

Interfaces abstratas para publicação e consumo de eventos.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional, Awaitable

from araos.platform.events.schemas import EventEnvelope


class EventPublisher(ABC):
    """
    Contrato para publicação de eventos.
    
    Implementações:
        - RedisEventPublisher (concreto): Redis Streams
        - KafkaEventPublisher (futuro): Kafka
        - InMemoryEventPublisher (teste): para testes unitários
    """
    
    @abstractmethod
    async def publish(self, event: EventEnvelope) -> str:
        """
        Publica um evento no bus.
        
        Args:
            event: EventEnvelope completo
        
        Returns:
            event_id confirmado
        """
        ...
    
    @abstractmethod
    async def publish_many(self, events: List[EventEnvelope]) -> List[str]:
        """
        Publica múltiplos eventos em batch.
        """
        ...
    
    @abstractmethod
    async def health(self) -> bool:
        """Verifica se o publisher está saudável."""
        ...


class EventConsumer(ABC):
    """
    Contrato para consumo de eventos.
    
    Implementações:
        - RedisEventConsumer (concreto): Consumer Groups do Redis
        - KafkaEventConsumer (futuro): Kafka Consumer
    """
    
    @abstractmethod
    async def subscribe(self, event_types: List[str],
                         consumer_group: str,
                         handler: Callable[[EventEnvelope], Awaitable[None]]) -> None:
        """
        Registra handler para tipos de evento.
        
        Args:
            event_types: Lista de eventos a consumir (ex: ["PATIENT_CREATED"])
            consumer_group: Nome do grupo de consumidores
            handler: Função async que processa o evento
        """
        ...
    
    @abstractmethod
    async def consume(self, consumer_group: str,
                       consumer_name: str,
                       block_ms: int = 5000) -> List[EventEnvelope]:
        """
        Lê eventos pendentes do consumer group.
        
        Returns:
            Lista de eventos não processados
        """
        ...
    
    @abstractmethod
    async def acknowledge(self, event_ids: List[str]) -> None:
        """
        Confirma processamento de eventos.
        
        Sem ACK, eventos são reentregues após timeout.
        """
        ...
    
    @abstractmethod
    async def get_pending(self, consumer_group: str) -> List[EventEnvelope]:
        """
        Retorna eventos pendentes (não ACKed).
        """
        ...


class EventBus(ABC):
    """
    Contrato composto: publisher + consumer + store.
    
    Interface principal do Event Bus.
    """
    
    publisher: EventPublisher
    consumer: EventConsumer
    
    @abstractmethod
    async def publish(self, event: EventEnvelope) -> str:
        """Publica evento."""
        ...
    
    @abstractmethod
    async def subscribe(self, event_types: List[str],
                         consumer_group: str,
                         handler: Callable[[EventEnvelope], Awaitable[None]]) -> None:
        """Registra consumidor."""
        ...
    
    @abstractmethod
    async def get_history(self, aggregate_type: str,
                           aggregate_id: str) -> List[EventEnvelope]:
        """
        Retorna histórico de eventos para um aggregate.
        Útil para Event Sourcing e debugging.
        """
        ...
    
    @abstractmethod
    async def replay(self, aggregate_type: str,
                      aggregate_id: str,
                      from_timestamp: Optional[str] = None) -> List[EventEnvelope]:
        """
        Replay de eventos para reconstrução de estado.
        """
        ...
