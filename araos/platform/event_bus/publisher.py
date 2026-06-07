"""
AraOS Platform — Event Publisher (Redis Streams).

Implementação concreta de EventPublisher usando Redis Streams.
"""

import json
from typing import Optional, List, Dict, Any

from araos.platform.contracts.event_bus import EventPublisher as EventPublisherContract
from .envelope import EventEnvelopeV2


class RedisEventPublisher(EventPublisherContract):
    """
    Publisher de eventos usando Redis Streams.
    
    Redis Streams é a escolha atual por:
        - Baixa complexidade operacional
        - Persistência nativa
        - Consumer Groups
        - Fácil upgrade futuro para Kafka
    
    Uso:
        publisher = RedisEventPublisher(redis_client)
        await publisher.publish(event)
    """
    
    STREAM_KEY_PREFIX = "araos:events:"
    DEFAULT_STREAM = "araos:events:all"
    
    def __init__(self, redis_client, stream_key: Optional[str] = None):
        self.redis = redis_client
        self.stream_key = stream_key or self.DEFAULT_STREAM
    
    async def publish(self, event: EventEnvelopeV2) -> str:
        """
        Publica evento no stream Redis.
        
        Args:
            event: EventEnvelopeV2
        
        Returns:
            Message ID do Redis (confirmação)
        """
        # Serializa evento
        payload = json.dumps(event.to_dict(), default=str)
        
        # Publica no stream
        message_id = await self.redis.xadd(
            self.stream_key,
            {"event": payload},
            maxlen=100000,  # Mantém últimos 100k eventos
            approximate=True,
        )
        
        # Publica também em stream específico por tipo
        type_stream = f"{self.STREAM_KEY_PREFIX}{event.event_type.lower()}"
        await self.redis.xadd(
            type_stream,
            {"event": payload},
            maxlen=10000,
            approximate=True,
        )
        
        return message_id
    
    async def publish_many(self, events: List[EventEnvelopeV2]) -> List[str]:
        """
        Publica múltiplos eventos em batch.
        
        Usa pipeline Redis para performance.
        """
        ids = []
        pipe = self.redis.pipeline()
        
        for event in events:
            payload = json.dumps(event.to_dict(), default=str)
            pipe.xadd(self.stream_key, {"event": payload})
        
        results = await pipe.execute()
        return [str(r) for r in results]
    
    async def health(self) -> bool:
        """Verifica se Redis está disponível."""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def get_stream_info(self) -> Dict[str, Any]:
        """Retorna informações do stream para observabilidade."""
        info = await self.redis.xinfo_stream(self.stream_key)
        return {
            "length": info.get("length", 0),
            "radix_tree_keys": info.get("radix-tree-keys", 0),
            "groups": info.get("groups", 0),
            "last_generated_id": info.get("last-generated-id", ""),
        }
