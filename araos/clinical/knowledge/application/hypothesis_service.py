"""HypothesisService — Application Layer."""

from __future__ import annotations

from typing import Sequence

from ..domain.clinical_genome import ClinicalGenome
from ..domain.correlation import CorrelationResult
from ..domain.hypothesis import ClinicalHypothesis, HypothesisEngine
from .dto import HypothesisRequest
from .hypothesis_id_namespace import namespace_hypothesis_ids


class HypothesisService:
    """Orquestra HypothesisEngine.

    Aplica post-processing tenant-namespacing em hypothesis_id
    (task #197 RC1 pre-requisito) para evitar cross-tenant collision
    entre IDs content-derived.
    """

    def __init__(self, *, engine: HypothesisEngine | None = None) -> None:
        self._engine = engine or HypothesisEngine()

    def execute(self, request: HypothesisRequest) -> tuple[ClinicalHypothesis, ...]:
        raw = self._engine.generate(request.genome, request.correlations)
        return namespace_hypothesis_ids(raw, request.genome.tenant_id)
