"""
Snapshot — forma serializada e imutável do estado do Gene em um instante.

AS-002 §6.3 — Expression Snapshot SHALL ser byte-equivalente em
qualquer serialização subsequente (canonical JSON, ver
``serialization/``).

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json


@dataclass(frozen=True)
class Snapshot:
    """Snapshot imutável do estado canônico de um Gene.

    ``state_hash`` é derivado deterministicamente do conteúdo serializado,
    garantindo byte-equivalência em serializações subsequentes
    (AS-002 §6.3).
    """

    snapshot_id: str
    gene_id: str
    sequence: int                                # sequence per-tenant (ADR-0001)
    valid_time: datetime
    transaction_time: datetime
    state: Mapping[str, object]                  # estado canônico serializado
    state_hash: str
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not self.snapshot_id:
            raise ValueError("Snapshot.snapshot_id obrigatório")
        if not self.gene_id:
            raise ValueError("Snapshot.gene_id obrigatório")
        if self.sequence < 0:
            raise ValueError(f"Snapshot.sequence deve ser >= 0, recebido {self.sequence}")
        if self.valid_time.tzinfo is None:
            raise ValueError("Snapshot.valid_time deve ser timezone-aware (UTC)")
        if self.transaction_time.tzinfo is None:
            raise ValueError("Snapshot.transaction_time deve ser timezone-aware (UTC)")
        if self.transaction_time < self.valid_time:
            raise ValueError(
                "Snapshot.transaction_time não pode ser anterior a valid_time (AS-002 §4.4.2)"
            )
        if not self.state_hash:
            raise ValueError("Snapshot.state_hash obrigatório")
        if self.created_at.tzinfo is None:
            raise ValueError("Snapshot.created_at deve ser timezone-aware (UTC)")

    @staticmethod
    def compute_hash(state: Mapping[str, object]) -> str:
        """SHA-256 do estado canônico (sorted keys)."""
        canonical = json.dumps(state, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
