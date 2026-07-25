"""CorrelationService — Application Layer."""

from __future__ import annotations

from typing import Sequence

from ..domain.clinical_genome import ClinicalGenome
from ..domain.correlation import CorrelationEngine, CorrelationMethod, CorrelationResult
from .dto import CorrelationRequest


class CorrelationService:
    """Orquestra CorrelationEngine para ClinicalGenome."""

    def __init__(self, *, engine: CorrelationEngine | None = None) -> None:
        self._engine = engine or CorrelationEngine()

    def execute(self, request: CorrelationRequest) -> tuple[CorrelationResult, ...]:
        return self._engine.compute(
            request.genome,
            method=request.method,
            min_observations=request.min_observations,
        )

    def execute_all(
        self, genome: ClinicalGenome
    ) -> tuple[CorrelationResult, ...]:
        """Aplica todos os métodos CorrelationMethod."""
        results: list[CorrelationResult] = []
        for method in CorrelationMethod:
            results.extend(self._engine.compute(genome, method=method))
        return tuple(results)