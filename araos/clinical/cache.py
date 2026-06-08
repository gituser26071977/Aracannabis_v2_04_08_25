"""
AraOS Clinical — Digital Twin Cache.

Cacheia reconstruções do Patient Digital Twin.
Invalidação por eventos clínicos.
"""

import json
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta


class TwinCache(ABC):
    """
    Contrato para cache do Digital Twin.
    
    Implementações:
        - RedisTwinCache: produção (Redis JSON/Hash com TTL)
        - InMemoryTwinCache: testes/demos
    """
    
    DEFAULT_TTL_SECONDS = 300  # 5 minutos
    
    @abstractmethod
    async def get(self, patient_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Busca twin cacheado como dict serializado."""
        ...
    
    @abstractmethod
    async def set(self, patient_id: str, tenant_id: str, twin_dict: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ...
    
    @abstractmethod
    async def invalidate(self, patient_id: str, tenant_id: str) -> None:
        """Invalida cache de um paciente."""
        ...
    
    @abstractmethod
    async def invalidate_all(self) -> None:
        """Invalida todo o cache (útil em deploys)."""
        ...
    
    def _key(self, patient_id: str, tenant_id: str) -> str:
        return f"araos:twin:{tenant_id}:{patient_id}"


class InMemoryTwinCache(TwinCache):
    """
    Implementação em memória para testes/demos.
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl: Dict[str, datetime] = {}
    
    async def get(self, patient_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        key = self._key(patient_id, tenant_id)
        expires_at = self._ttl.get(key)
        if expires_at and datetime.now(timezone.utc) > expires_at:
            self._cache.pop(key, None)
            self._ttl.pop(key, None)
            return None
        return self._cache.get(key)
    
    async def set(self, patient_id: str, tenant_id: str, twin_dict: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        key = self._key(patient_id, tenant_id)
        self._cache[key] = twin_dict
        ttl = ttl_seconds or self.DEFAULT_TTL_SECONDS
        self._ttl[key] = datetime.now(timezone.utc) + timedelta(seconds=ttl)
    
    async def invalidate(self, patient_id: str, tenant_id: str) -> None:
        key = self._key(patient_id, tenant_id)
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
    
    async def invalidate_all(self) -> None:
        self._cache.clear()
        self._ttl.clear()
    
    def hit_ratio(self) -> float:
        """Métrica para testes."""
        return 0.0  # InMemory não rastreia hits/misses automaticamente


class RedisTwinCache(TwinCache):
    """
    Implementação com Redis Hash + TTL.
    
    Serializa o twin como JSON string.
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def get(self, patient_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        key = self._key(patient_id, tenant_id)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set(self, patient_id: str, tenant_id: str, twin_dict: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        key = self._key(patient_id, tenant_id)
        ttl = ttl_seconds or self.DEFAULT_TTL_SECONDS
        await self.redis.setex(key, ttl, json.dumps(twin_dict, default=str))
    
    async def invalidate(self, patient_id: str, tenant_id: str) -> None:
        key = self._key(patient_id, tenant_id)
        await self.redis.delete(key)
    
    async def invalidate_all(self) -> None:
        pattern = "araos:twin:*"
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break
