"""
AraOS Platform — Event Metrics.

Observabilidade do Event Bus.

Métricas:
    - Eventos publicados
    - Eventos consumidos
    - Eventos falhos
    - DLQ size
    - Tempo médio de processamento
    - Eventos por tenant
    - Eventos por módulo
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .envelope import EventEnvelopeV2


@dataclass
class MetricSnapshot:
    """Snapshot de métricas."""
    published_total: int = 0
    consumed_total: int = 0
    failed_total: int = 0
    dlq_size: int = 0
    avg_processing_time_ms: float = 0.0
    events_by_tenant: Dict[str, int] = None
    events_by_module: Dict[str, int] = None
    events_by_type: Dict[str, int] = None
    
    def __post_init__(self):
        if self.events_by_tenant is None:
            self.events_by_tenant = {}
        if self.events_by_module is None:
            self.events_by_module = {}
        if self.events_by_type is None:
            self.events_by_type = {}


class EventMetrics:
    """
    Métricas do Event Bus.
    
    Usa Redis para contadores (rápido) e PostgreSQL para histórico.
    """
    
    METRIC_PREFIX = "araos:metrics:"
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    # ─── Recording ───────────────────────────────────────────────────
    
    async def record_published(self, event: EventEnvelopeV2) -> None:
        """Registra evento publicado."""
        pipe = self.redis.pipeline()
        
        # Contadores globais
        pipe.incr(f"{self.METRIC_PREFIX}published:total")
        pipe.incr(f"{self.METRIC_PREFIX}published:daily:{self._today()}")
        
        # Por tenant
        pipe.incr(f"{self.METRIC_PREFIX}tenant:{event.tenant_id}:published")
        
        # Por tipo
        pipe.incr(f"{self.METRIC_PREFIX}type:{event.event_type}:published")
        
        # Por categoria
        pipe.incr(f"{self.METRIC_PREFIX}category:{event.event_category.value}:published")
        
        # Por módulo (source no metadata)
        source = event.metadata.get("source", "unknown")
        pipe.incr(f"{self.METRIC_PREFIX}module:{source}:published")
        
        await pipe.execute()
    
    async def record_consumed(self, event: EventEnvelopeV2, consumer_group: str) -> None:
        """Registra evento consumido com sucesso."""
        pipe = self.redis.pipeline()
        
        pipe.incr(f"{self.METRIC_PREFIX}consumed:total")
        pipe.incr(f"{self.METRIC_PREFIX}consumer:{consumer_group}:consumed")
        
        await pipe.execute()
    
    async def record_failed(
        self,
        event: EventEnvelopeV2,
        consumer_group: str,
        error: str,
    ) -> None:
        """Registra falha no processamento."""
        pipe = self.redis.pipeline()
        
        pipe.incr(f"{self.METRIC_PREFIX}failed:total")
        pipe.incr(f"{self.METRIC_PREFIX}consumer:{consumer_group}:failed")
        pipe.incr(f"{self.METRIC_PREFIX}type:{event.event_type}:failed")
        
        # Registrar erro
        await self.redis.lpush(
            f"{self.METRIC_PREFIX}errors:recent",
            f"{event.event_type}:{consumer_group}:{error[:100]}",
        )
        await self.redis.ltrim(f"{self.METRIC_PREFIX}errors:recent", 0, 99)
        
        await pipe.execute()
    
    async def record_processing_time(self, event_type: str, duration_ms: float) -> None:
        """Registra tempo de processamento."""
        key = f"{self.METRIC_PREFIX}processing_time:{event_type}"
        await self.redis.lpush(key, duration_ms)
        await self.redis.ltrim(key, 0, 999)  # Mantém últimos 1000
    
    # ─── Querying ────────────────────────────────────────────────────
    
    async def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo de métricas."""
        keys = [
            f"{self.METRIC_PREFIX}published:total",
            f"{self.METRIC_PREFIX}consumed:total",
            f"{self.METRIC_PREFIX}failed:total",
        ]
        
        values = await self.redis.mget(*keys)
        
        published = int(values[0] or 0)
        consumed = int(values[1] or 0)
        failed = int(values[2] or 0)
        
        # DLQ size
        dlq_size = await self._get_dlq_size()
        
        # Tempo médio de processamento
        avg_time = await self._get_avg_processing_time()
        
        return {
            "published_total": published,
            "consumed_total": consumed,
            "failed_total": failed,
            "dlq_size": dlq_size,
            "success_rate": (consumed / (consumed + failed) * 100) if (consumed + failed) > 0 else 100.0,
            "avg_processing_time_ms": round(avg_time, 2),
            "pending": published - consumed,
        }
    
    async def get_by_tenant(self, tenant_id: str) -> Dict[str, int]:
        """Retorna métricas por tenant."""
        published = await self.redis.get(
            f"{self.METRIC_PREFIX}tenant:{tenant_id}:published"
        )
        return {
            "published": int(published or 0),
        }
    
    async def get_by_module(self) -> Dict[str, int]:
        """Retorna métricas por módulo."""
        pattern = f"{self.METRIC_PREFIX}module:*:published"
        keys = await self.redis.keys(pattern)
        
        result = {}
        if keys:
            values = await self.redis.mget(*keys)
            for key, value in zip(keys, values):
                module = key.decode().split(":")[-2] if isinstance(key, bytes) else key.split(":")[-2]
                result[module] = int(value or 0)
        
        return result
    
    async def get_top_event_types(self, limit: int = 10) -> Dict[str, int]:
        """Retorna tipos de evento mais frequentes."""
        pattern = f"{self.METRIC_PREFIX}type:*:published"
        keys = await self.redis.keys(pattern)
        
        result = {}
        if keys:
            values = await self.redis.mget(*keys)
            for key, value in zip(keys, values):
                event_type = key.decode().split(":")[-2] if isinstance(key, bytes) else key.split(":")[-2]
                result[event_type] = int(value or 0)
        
        # Ordenar por frequência
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:limit])
    
    # ─── Helpers ─────────────────────────────────────────────────────
    
    async def _get_dlq_size(self) -> int:
        """Retorna tamanho da DLQ."""
        # Placeholder — em produção consultar DB
        return 0
    
    async def _get_avg_processing_time(self) -> float:
        """Calcula tempo médio de processamento."""
        pattern = f"{self.METRIC_PREFIX}processing_time:*"
        keys = await self.redis.keys(pattern)
        
        if not keys:
            return 0.0
        
        total = 0.0
        count = 0
        for key in keys:
            values = await self.redis.lrange(key, 0, -1)
            for v in values:
                total += float(v)
                count += 1
        
        return total / count if count > 0 else 0.0
    
    def _today(self) -> str:
        """Retorna data atual no formato YYYY-MM-DD."""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%d")
