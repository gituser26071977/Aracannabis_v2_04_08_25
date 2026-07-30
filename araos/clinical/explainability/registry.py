"""
ExplanationRegistry — interface para registro e consulta de explicações.

Toda análise (correlation, trend, anomaly, hypothesis, episode_suggestion,
cohort_evaluation) DEVE chamar `register()` após computar.

Invariantes:
    - Toda Explanation registrada tem explanation_id único.
    - register() retorna o explanation_id.
    - get() retorna None se não encontrada.
    - list_for_analysis() retorna todas as explicações de uma análise
      (uma análise pode ter múltiplas explicações se houve tentativa
      com diferentes métodos).
    - list_for_event() retorna explicações que citaram este evento
      como contributing.

Implementações:
    - InMemoryExplanationRegistry — thread-safe com RLock, para testes.
    - SqlAlchemyExplanationRegistry — produção (Sprint 4.5+).
"""

from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.explainability.domain.explanation import (
    AnalysisType,
    Explanation,
)


class ExplanationRegistry(ABC):
    """Interface para registro de explicações."""

    @abstractmethod
    def register(self, explanation: Explanation) -> str:
        """Registra uma Explanation e retorna explanation_id."""

    @abstractmethod
    def get(self, explanation_id: str) -> Optional[Explanation]:
        """Recupera uma Explanation por id. None se não encontrada."""

    @abstractmethod
    def list_for_analysis(
        self,
        tenant_id: str,
        analysis_id: str,
    ) -> List[Explanation]:
        """Lista explicações associadas a uma análise."""

    @abstractmethod
    def list_for_event(
        self,
        tenant_id: str,
        event_id: str,
    ) -> List[Explanation]:
        """Lista explicações que citaram este evento como contributing."""

    @abstractmethod
    def list_for_type(
        self,
        tenant_id: str,
        analysis_type: AnalysisType,
        limit: int = 100,
    ) -> List[Explanation]:
        """Lista explicações por tipo (correlation, trend, etc.)."""

    @abstractmethod
    def count(self, tenant_id: str) -> int:
        """Conta explicações registradas."""


class InMemoryExplanationRegistry(ExplanationRegistry):
    """Registry em memória, thread-safe. Para testes + dev."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._by_id: Dict[str, Explanation] = {}
        self._by_analysis: Dict[str, Dict[str, Explanation]] = {}
        self._by_event: Dict[str, Dict[str, Explanation]] = {}
        self._by_type: Dict[str, Dict[str, Explanation]] = {}

    def register(self, explanation: Explanation) -> str:
        if not isinstance(explanation, Explanation):
            raise TypeError("explanation must be Explanation instance")
        with self._lock:
            self._by_id[explanation.explanation_id] = explanation
            self._by_analysis \
                .setdefault(explanation.analysis_id, {})[explanation.explanation_id] = explanation
            for ev_id in explanation.contributing_event_ids:
                self._by_event \
                    .setdefault(ev_id, {})[explanation.explanation_id] = explanation
            type_key = explanation.analysis_type.value
            self._by_type \
                .setdefault(type_key, {})[explanation.explanation_id] = explanation
            return explanation.explanation_id

    def get(self, explanation_id: str) -> Optional[Explanation]:
        with self._lock:
            return self._by_id.get(explanation_id)

    def list_for_analysis(
        self,
        tenant_id: str,
        analysis_id: str,
    ) -> List[Explanation]:
        with self._lock:
            entries = self._by_analysis.get(analysis_id, {}).values()
            return [e for e in entries if e.tenant_id == tenant_id]

    def list_for_event(
        self,
        tenant_id: str,
        event_id: str,
    ) -> List[Explanation]:
        with self._lock:
            entries = self._by_event.get(event_id, {}).values()
            return [e for e in entries if e.tenant_id == tenant_id]

    def list_for_type(
        self,
        tenant_id: str,
        analysis_type: AnalysisType,
        limit: int = 100,
    ) -> List[Explanation]:
        with self._lock:
            entries = self._by_type.get(analysis_type.value, {}).values()
            scoped = [e for e in entries if e.tenant_id == tenant_id]
        return scoped[:limit]

    def count(self, tenant_id: str) -> int:
        with self._lock:
            return sum(
                1 for e in self._by_id.values() if e.tenant_id == tenant_id
            )

    def clear(self) -> None:
        """Limpa registry (testes)."""
        with self._lock:
            self._by_id.clear()
            self._by_analysis.clear()
            self._by_event.clear()
            self._by_type.clear()


def new_explanation_id() -> str:
    """Gera ULID-like ID para explicação. UUID4 suficiente para Sprint 4.1."""
    return f"exp_{uuid.uuid4().hex[:16]}"