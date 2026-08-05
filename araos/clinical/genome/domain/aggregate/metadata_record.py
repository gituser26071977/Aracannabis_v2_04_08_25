"""
MetadataRecord — extensão não-canônica (labels livres, hints UI).

AS-001 §6.9 — Metadata SHALL ser tratada como não-canônica.
Operações de inferência SHALL NOT depender do conteúdo de Metadata.
Atualizações produzem nova entrada em History (append-only).

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True)
class MetadataRecord:
    """Registro de Metadata (append-only)."""

    record_id: str
    content: Mapping[str, Any]
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    origin_event_id: str | None = None

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("MetadataRecord.record_id obrigatório")
        if self.created_at.tzinfo is None:
            raise ValueError("MetadataRecord.created_at deve ser timezone-aware (UTC)")
        # Garante imutabilidade do content.
        object.__setattr__(self, "content", MappingProxyType(dict(self.content)))
