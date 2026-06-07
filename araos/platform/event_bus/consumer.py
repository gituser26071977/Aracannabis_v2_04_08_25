"""
AraOS Platform — Event Consumer (Redis Streams).

Implementação concreta de EventConsumer usando Redis Consumer Groups.
"""

import json
import asyncio
from typing import Callable, List, Optional, Dict, Any, Awaitable

from araos.platform.contracts.event_bus import EventConsumer as EventConsumerContract
from .envelope import EventEnvelopeV2


Handler = Callable[[EventEnvelopeV2], Awaitable[None]]


class RedisEventConsumer(EventConsumerContract):
    """
    Consumer de eventos usando Redis Consumer Groups.
    
    Características:
        - Consumer Groups para load balancing
        - Auto-ACK com fallback para manual
        - Block read com timeout
        - Reconexão automática
    
    Uso:
        consumer = RedisEventConsumer(redis_client)
        await consumer.subscribe(["PATIENT_CREATED"], "audit-group", handler)
        await consumer.consume("audit-group", "consumer-1")
    """
    
    STREAM_KEY = "araos:events:all"
    BLOCK_MS = 5000  # 5 segundos
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self._handlers: Dict[str, List[Handler]] = {}
        self._subscribed: bool = False
    
    async def subscribe(
        self,
        event_types: List[str],
        consumer_group: str,
        handler: Handler,
    ) -> None:
        """
        Registra handler para tipos de evento.
        
        Args:
            event_types: Lista de eventos a consumir
            consumer_group: Nome do grupo de consumidores
            handler: Função async que processa o evento
        """
        # Criar consumer group se não existir
        try:
            await self.redis.xgroup_create(
                self.STREAM_KEY,
                consumer_group,
                id="0",  # Começa do início (replay possível)
                mkstream=True,
            )
        except Exception:
            pass  # Group já existe
        
        # Registrar handlers
        for event_type in event_types:
            key = f"{consumer_group}:{event_type}"
            if key not in self._handlers:
                self._handlers[key] = []
            self._handlers[key].append(handler)
        
        self._subscribed = True
    
    async def consume(
        self,
        consumer_group: str,
        consumer_name: str,
        block_ms: int = None,
    ) -> List[EventEnvelopeV2]:
        """
        Lê eventos pendentes do consumer group.
        
        Returns:
            Lista de eventos não processados
        """
        block = block_ms or self.BLOCK_MS
        
        # Ler do stream
        messages = await self.redis.xreadgroup(
            groupname=consumer_group,
            consumername=consumer_name,
            streams={self.STREAM_KEY: ">"},  # Apenas mensagens novas
            count=100,
            block=block,
        )
        
        events = []
        for stream_name, stream_messages in messages:
            for message_id, fields in stream_messages:
                event_data = fields.get(b"event", fields.get("event"))
                if isinstance(event_data, bytes):
                    event_data = event_data.decode("utf-8")
                
                try:
                    event_dict = json.loads(event_data)
                    event = EventEnvelopeV2.from_dict(event_dict)
                    events.append((message_id, event))
                except (json.JSONDecodeError, KeyError):
                    continue
        
        return events
    
    async def acknowledge(self, event_ids: List[str]) -> None:
        """
        Confirma processamento de eventos.
        
        Sem ACK, eventos são reentregues após timeout.
        """
        if event_ids:
            # XACK requer consumer group — precisamos rastrear o group
            # Simplificação: ACK para todos os groups registrados
            for group in self._get_groups():
                await self.redis.xack(self.STREAM_KEY, group, *event_ids)
    
    async def get_pending(
        self,
        consumer_group: str,
    ) -> List[Dict[str, Any]]:
        """
        Retorna eventos pendentes (não ACKed).
        """
        pending = await self.redis.xpending_range(
            self.STREAM_KEY,
            consumer_group,
            min="-",
            max="+",
            count=100,
        )
        return [
            {
                "message_id": p["message_id"],
                "consumer": p["consumer"],
                "idle_time_ms": p["time_since_delivered"],
                "delivery_count": p["times_delivered"],
            }
            for p in (pending or [])
        ]
    
    def _get_groups(self) -> List[str]:
        """Extrai nomes de groups dos handlers registrados."""
        groups = set()
        for key in self._handlers:
            group = key.split(":")[0]
            groups.add(group)
        return list(groups)
    
    async def run(
        self,
        consumer_group: str,
        consumer_name: str,
        handler: Handler,
    ) -> None:
        """
        Loop contínuo de consumo.
        
        Uso:
            asyncio.create_task(consumer.run("audit-group", "worker-1", handler))
        """
        while True:
            try:
                events = await self.consume(consumer_group, consumer_name)
                for message_id, event in events:
                    try:
                        await handler(event)
                        await self.acknowledge([message_id])
                    except Exception as e:
                        # Handler falhou — não faz ACK, evento será reentregue
                        print(f"Handler error for {event.event_type}: {e}")
            except Exception as e:
                print(f"Consumer error: {e}")
                await asyncio.sleep(1)
