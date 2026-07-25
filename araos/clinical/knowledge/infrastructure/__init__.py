"""
araos.clinical.knowledge.infrastructure — Infrastructure Adapters.

Sprint 4.4 — Clinical Knowledge Engine v1.0.
Sprint 4.5 — Infrastructure Layer (tenant-bound ABC + SQL repository).

Conforme escopo definido:
    Implementar:
        - InMemory repositories
        - InMemory projections
        - InMemory graph
        - KnowledgeRepository ABC (tenant-bound, G3)
        - SQLKnowledgeRepository (PostgreSQL, W1.3)

    NÃO implementar:
        - Redis, Elastic
        - RabbitMQ, Kafka
        - GraphQL
"""

from .in_memory import InMemoryKnowledgeRepository
from .repository import KnowledgeRepository

__all__ = [
    "KnowledgeRepository",
    "InMemoryKnowledgeRepository",
]
