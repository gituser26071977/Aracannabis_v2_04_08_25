"""
Trajectory — série histórica bitemporal das Expressions (AS-001 §6.2).

Invariantes:

- AS-001 Requisito 6.2.1 — Append-only.
- AS-001 Requisito 6.2.2 — Ordenação natural por valid_time asc.
- AS-001 Requisito 6.2.3 — Eventos desordenados preservam ordem.
- AS-002 Requisito 4.8.1 — Toda Expression publicada vira snapshot.
- AS-002 Requisito 4.8.2 — Append-only (nenhuma remoção).

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Sequence

from ..expression import ClinicalExpression, ExpressionState


# implements:
#   AS-001-REQ-0062 — Append-only
#   AS-001-REQ-0063 — Ordenação natural por valid_time
#   AS-001-REQ-0064 — Inserção desordenada preserva ordem
#   AS-002-REQ-0068 — Snapshot na Trajectory
#   AS-002-REQ-0069 — Append-only
#   AS-002-REQ-0057 — Substituição preserva histórico


@dataclass(frozen=True)
class TrajectoryPoint:
    """Ponto imutável na Trajectory."""

    expression: ClinicalExpression
    contributing_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.expression, ClinicalExpression):
            raise TypeError(
                f"TrajectoryPoint.expression deve ser ClinicalExpression, "
                f"recebido {type(self.expression).__name__}"
            )
        if not self.contributing_event_ids:
            raise ValueError(
                "TrajectoryPoint.contributing_event_ids SHALL ter ≥ 1 event_id"
            )

    @property
    def valid_time(self) -> datetime:
        return self.expression.valid_time


@dataclass(frozen=True)
class Trajectory:
    """Trajectory append-only com ordenação por valid_time asc.

    Mantida como tupla imutável; inserção retorna nova Trajectory.
    """

    points: tuple[TrajectoryPoint, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        # Valida ordenação crescente por valid_time (AS-001 §6.2.2).
        for i in range(1, len(self.points)):
            if self.points[i].valid_time < self.points[i - 1].valid_time:
                raise ValueError(
                    f"Trajectory SHALL ser ordenada por valid_time ascendente: "
                    f"ponto {i-1} ({self.points[i-1].valid_time}) > ponto {i} "
                    f"({self.points[i].valid_time}) — viola AS-001 §6.2.2"
                )

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self) -> Iterator[TrajectoryPoint]:
        return iter(self.points)

    def append(self, point: TrajectoryPoint) -> "Trajectory":
        """Append novo ponto preservando ordenação por valid_time (AS-001 §6.2.3)."""
        if not isinstance(point, TrajectoryPoint):
            raise TypeError(
                f"Trajectory.append exige TrajectoryPoint, recebido {type(point).__name__}"
            )
        # Insere na posição correta (AS-001 §6.2.3 — desordenado é tolerado).
        new_points = list(self.points)
        inserted = False
        for i, existing in enumerate(new_points):
            if point.valid_time < existing.valid_time:
                new_points.insert(i, point)
                inserted = True
                break
        if not inserted:
            new_points.append(point)
        return Trajectory(tuple(new_points))

    def latest(self) -> TrajectoryPoint | None:
        """Último ponto (maior valid_time). None se vazia."""
        return self.points[-1] if self.points else None

    def at(self, when: datetime) -> TrajectoryPoint | None:
        """Último ponto com valid_time ≤ ``when``. None se vazia."""
        if when.tzinfo is None:
            raise ValueError("Trajectory.at exige timestamp timezone-aware (UTC)")
        result = None
        for p in self.points:
            if p.valid_time <= when:
                result = p
            else:
                break
        return result

    def historical(self) -> Sequence[TrajectoryPoint]:
        """Pontos históricos (exclui o último, que é Current)."""
        if len(self.points) <= 1:
            return ()
        return self.points[:-1]

    def known_at(self, when: datetime) -> set[str]:
        """Conjunto de contributing_event_ids conhecidos em ``when``.

        Implementa a regra de "estado conhecido em uma data" do Sprint
        4.3 Phase 2 — útil para auditoria temporal.
        """
        if when.tzinfo is None:
            raise ValueError("Trajectory.known_at exige timestamp timezone-aware (UTC)")
        events: set[str] = set()
        for p in self.points:
            if p.valid_time <= when:
                events.update(p.contributing_event_ids)
            else:
                break
        return events

    def state_at(self, when: datetime) -> ExpressionState | None:
        """Estado da Expression em ``when``."""
        p = self.at(when)
        return p.expression.state if p else None
