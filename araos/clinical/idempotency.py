"""
AraOS Clinical — Idempotency Tracker.

Garante exactly-once processing lógico de eventos clínicos.
"""

from typing import Optional
from abc import ABC, abstractmethod


class IdempotencyTracker(ABC):
    """
    Contrato para rastreamento de eventos processados.
    
    Implementações:
        - RedisIdempotencyTracker: produção (Redis Set com TTL)
        - InMemoryIdempotencyTracker: testes/demos
    """
    
    @abstractmethod
    async def is_processed(self, event_id: str) -> bool:
        """Verifica se evento já foi processado."""
        ...
    
    @abstractmethod
    async def mark_processed(self, event_id: str, ttl_seconds: int = 86400) -> None:
        """Marca evento como processado."""
        ...
    
    @abstractmethod
    async def mark_failed(self, event_id: str, ttl_seconds: int = 3600) -> None:
        """Marca evento como falho (para retry controlado)."""
        ...
    
    @abstractmethod
    async def is_failed(self, event_id: str) -> bool:
        """Verifica se evento falhou recentemente."""
        ...


class InMemoryIdempotencyTracker(IdempotencyTracker):
    """
    Implementação em memória para testes/demos.
    """
    
    def __init__(self):
        self._processed: set = set()
        self._failed: set = set()
    
    async def is_processed(self, event_id: str) -> bool:
        return event_id in self._processed
    
    async def mark_processed(self, event_id: str, ttl_seconds: int = 86400) -> None:
        self._processed.add(event_id)
        if event_id in self._failed:
            self._failed.discard(event_id)
    
    async def mark_failed(self, event_id: str, ttl_seconds: int = 3600) -> None:
        self._failed.add(event_id)
    
    async def is_failed(self, event_id: str) -> bool:
        return event_id in self._failed
    
    def clear(self) -> None:
        self._processed.clear()
        self._failed.clear()


class RedisIdempotencyTracker(IdempotencyTracker):
    """
    Implementação com Redis Set + TTL.
    
    Keys:
        araos:projections:processed  (Set)
        araos:projections:failed     (Set)
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.PROCESSED_KEY = "araos:projections:processed"
        self.FAILED_KEY = "araos:projections:failed"
    
    async def is_processed(self, event_id: str) -> bool:
        result = await self.redis.sismember(self.PROCESSED_KEY, event_id)
        return bool(result)
    
    async def mark_processed(self, event_id: str, ttl_seconds: int = 86400) -> None:
        await self.redis.sadd(self.PROCESSED_KEY, event_id)
        # Redis Sets não suportam TTL por membro; usamos expire no key
        # Isso limpa todo o set, não apenas o membro
        await self.redis.expire(self.PROCESSED_KEY, ttl_seconds)
        await self.redis.srem(self.FAILED_KEY, event_id)
    
    async def mark_failed(self, event_id: str, ttl_seconds: int = 3600) -> None:
        await self.redis.sadd(self.FAILED_KEY, event_id)
        await self.redis.expire(self.FAILED_KEY, ttl_seconds)
    
    async def is_failed(self, event_id: str) -> bool:
        result = await self.redis.sismember(self.FAILED_KEY, event_id)
        return bool(result)
