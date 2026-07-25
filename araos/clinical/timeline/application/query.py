"""
TimelineQuery — interface para consulta da timeline clínica.

Reutiliza ClinicalEventStore (Sprint 3.1) como source-of-truth.
NÃO duplica dados — apenas lê + ordena + filtra.

Implementações:
    - InMemoryTimelineQuery: opera sobre InMemoryClinicalEventStore
      (testes + cenários simples).
    - SqlAlchemyTimelineQuery: opera sobre SqlAlchemyClinicalEventStore
      com queries SQL otimizadas (produção).

Padrão de ordenação: SEMPRE por (sequence ASC) — canônico,
não por event_datetime (late-arriving events).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from araos.clinical.event_store.store import ClinicalEventStore
from araos.clinical.timeline.domain.entries import TimelineEntry
from araos.clinical.timeline.domain.window import TimeWindow


class TimelineQuery(ABC):
    """Interface para consulta temporal."""

    @abstractmethod
    def for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        window: Optional[TimeWindow] = None,
        event_types: Optional[List[str]] = None,
        episode_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[TimelineEntry]:
        """Retorna entradas da timeline do paciente, ordenadas por sequence ASC.

        Args:
            tenant_id: tenant (multi-tenancy).
            patient_id: paciente.
            window: filtro temporal (start/end inclusive).
            event_types: filtro por tipos de evento (suporta wildcard 'X_*').
            episode_id: filtra apenas eventos de um episódio (Sprint 4.2+).
            limit: máximo de entradas retornadas.
        """

    @abstractmethod
    def for_aggregate(
        self,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
    ) -> List[TimelineEntry]:
        """Retorna entradas da timeline de um aggregate específico.

        Útil para "histórico de um diagnóstico" ou "histórico de uma
        intervenção" sem precisar carregar o paciente inteiro.
        """

    @abstractmethod
    def count(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
    ) -> int:
        """Conta entradas (sem materializar lista — eficiente para dashboards)."""


class InMemoryTimelineQuery(TimelineQuery):
    """Implementação InMemory que opera sobre ClinicalEventStore.

    Strategy: delega para ClinicalEventStore.query() e converte via
    TimelineEntry.from_event(). Mantém o snapshot "puro" — sem cache
    adicional (cache é responsabilidade de outras camadas).
    """

    def __init__(self, event_store: ClinicalEventStore) -> None:
        self._event_store = event_store

    def for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        window: Optional[TimeWindow] = None,
        event_types: Optional[List[str]] = None,
        episode_id: Optional[str] = None,
        limit: int = 1000,
    ) -> List[TimelineEntry]:
        events = self._event_store.query(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_types=event_types,
            order_by="sequence ASC",
            limit=limit,
        )
        entries: List[TimelineEntry] = []
        for ev in events:
            try:
                entry = TimelineEntry.from_event(ev)
            except (ValueError, KeyError):
                # Evento malformado — pula (não crasha timeline inteira)
                continue
            if window is not None and not window.contains(entry.event_datetime):
                continue
            if episode_id is not None and entry.episode_id != episode_id:
                continue
            entries.append(entry)
        return entries

    def for_aggregate(
        self,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
    ) -> List[TimelineEntry]:
        events = self._event_store.query(
            tenant_id=tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            order_by="sequence ASC",
        )
        return [
            TimelineEntry.from_event(ev)
            for ev in events
            if self._is_valid_event(ev)
        ]

    def count(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
    ) -> int:
        if not event_types:
            return self._event_store.count(
                tenant_id=tenant_id,
                patient_id=patient_id,
            )
        # event_types informado → conta sobre query materializada (com
        # wildcard handling já garantido pela camada store)
        return len(self._event_store.query(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_types=event_types,
            order_by="sequence ASC",
        ))

    @staticmethod
    def _is_valid_event(event: Dict[str, Any]) -> bool:
        try:
            TimelineEntry.from_event(event)
            return True
        except (ValueError, KeyError):
            return False