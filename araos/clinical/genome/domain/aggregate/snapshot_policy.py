"""
SnapshotPolicy — regras configuráveis para criação automática de snapshots.

Sprint 4.3 Phase 2 — Replay SHALL funcionar tanto com snapshot
quanto sem (Gene.replay() pode usar snapshot+tail de eventos ou
eventos completos).

A política decide QUANDO criar snapshot automático:
- A cada N eventos.
- A cada M segundos transcorridos desde o último snapshot.
- Em eventos críticos (ExpressionReplaced).

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SnapshotPolicy:
    """Política de snapshot automático.

    Attributes:
        every_n_events: cria snapshot a cada N eventos (0 = desabilitado).
        on_expression_replaced: cria snapshot ao substituir Expression.
        on_hypothesis_added: cria snapshot ao adicionar Hypothesis.
        on_relationship_added: cria snapshot ao adicionar Relationship.
    """

    every_n_events: int = 0
    on_expression_replaced: bool = True
    on_hypothesis_added: bool = False
    on_relationship_added: bool = False

    def __post_init__(self) -> None:
        if self.every_n_events < 0:
            raise ValueError(
                f"SnapshotPolicy.every_n_events deve ser >= 0, recebido {self.every_n_events}"
            )

    @classmethod
    def never(cls) -> "SnapshotPolicy":
        """Política desabilitada (sem snapshots automáticos)."""
        return cls(every_n_events=0, on_expression_replaced=False)

    @classmethod
    def aggressive(cls) -> "SnapshotPolicy":
        """Snapshot a cada evento significativo."""
        return cls(
            every_n_events=1,
            on_expression_replaced=True,
            on_hypothesis_added=True,
            on_relationship_added=True,
        )

    @classmethod
    def every_ten(cls) -> "SnapshotPolicy":
        """Snapshot a cada 10 eventos + em ExpressionReplaced."""
        return cls(every_n_events=10, on_expression_replaced=True)
