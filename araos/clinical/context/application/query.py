"""
ClinicalContextQuery — 5 query types para análise clínica.

Sprint 4.2 — ADR-0003.

Queries:
    - for_patient              — todos os contextos de um paciente
    - active_at                — contextos ativos em uma data
    - co_occurred              — pares de contextos que coexistiram
    - influenced_outcome       — contextos que influenciaram um outcome
    - preceded_improvement     — contextos que precederam melhora clínica
    - active_during            — contextos ativos durante intervenção
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from araos.clinical.context.domain.clinical_context import ClinicalContext


def _ensure_tz(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class ClinicalContextQuery(ABC):
    """Interface para consultas sobre ClinicalContexts."""

    @abstractmethod
    def for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        status: Optional[Any] = None,
        context_type: Optional[Any] = None,
    ) -> List[ClinicalContext]:
        """Lista contextos do paciente (opcionalmente filtrado)."""

    @abstractmethod
    def get(self, tenant_id: str, context_id: str) -> Optional[ClinicalContext]:
        """Busca por ID (None se não encontrado)."""

    @abstractmethod
    def active_at(
        self,
        tenant_id: str,
        patient_id: str,
        at_date: datetime,
    ) -> List[ClinicalContext]:
        """Contextos ativos na data especificada."""

    @abstractmethod
    def co_occurred(
        self,
        tenant_id: str,
        patient_id: str,
        date_a: datetime,
        date_b: datetime,
    ) -> List[Tuple[ClinicalContext, ClinicalContext]]:
        """Pares (A, B) onde A estava ativo em date_a e B em date_b."""

    @abstractmethod
    def influenced_outcome(
        self,
        tenant_id: str,
        outcome_id: str,
    ) -> List[ClinicalContext]:
        """Contextos linked a um outcome."""

    @abstractmethod
    def preceded_improvement(
        self,
        tenant_id: str,
        patient_id: str,
        window_days: int = 30,
    ) -> List[ClinicalContext]:
        """Contextos closed nos N dias antes de um OUTCOME_IMPROVEMENT."""

    @abstractmethod
    def active_during(
        self,
        tenant_id: str,
        intervention_id: str,
    ) -> List[ClinicalContext]:
        """Contextos ativos durante o período de uma intervenção."""


# ─── InMemory implementation (testes + dev) ──────────────────────────


class InMemoryClinicalContextQuery(ClinicalContextQuery):
    """Implementação in-memory. Para testes + dev."""

    def __init__(self, contexts: Optional[List[ClinicalContext]] = None) -> None:
        self._contexts: List[ClinicalContext] = list(contexts or [])
        self._events: List[Dict[str, Any]] = []

    def add(self, ctx: ClinicalContext) -> None:
        self._contexts.append(ctx)

    def set_events(self, events: List[Dict[str, Any]]) -> None:
        self._events = list(events)

    # ─── Read ──────────────────────────────────────────────────────

    def for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        status: Optional[Any] = None,
        context_type: Optional[Any] = None,
    ) -> List[ClinicalContext]:
        result = [
            c for c in self._contexts
            if c.tenant_id == tenant_id and c.patient_id == patient_id
        ]
        if status is not None:
            result = [c for c in result if c.status == status]
        if context_type is not None:
            result = [c for c in result if c.context_type == context_type]
        return sorted(result, key=lambda c: c.start_date)

    def get(self, tenant_id: str, context_id: str) -> Optional[ClinicalContext]:
        for c in self._contexts:
            if c.tenant_id == tenant_id and c.context_id == context_id:
                return c
        return None

    # ─── Queries ───────────────────────────────────────────────────

    def active_at(
        self,
        tenant_id: str,
        patient_id: str,
        at_date: datetime,
    ) -> List[ClinicalContext]:
        at_date = _ensure_tz(at_date)
        return [
            c for c in self.for_patient(tenant_id, patient_id)
            if c.is_active_on(at_date)
        ]

    def co_occurred(
        self,
        tenant_id: str,
        patient_id: str,
        date_a: datetime,
        date_b: datetime,
    ) -> List[Tuple[ClinicalContext, ClinicalContext]]:
        date_a = _ensure_tz(date_a)
        date_b = _ensure_tz(date_b)
        contexts = self.for_patient(tenant_id, patient_id)
        a_active = [c for c in contexts if c.is_active_on(date_a)]
        b_active = [c for c in contexts if c.is_active_on(date_b)]
        pairs: List[Tuple[ClinicalContext, ClinicalContext]] = []
        for a in a_active:
            for b in b_active:
                if a.context_id == b.context_id:
                    continue
                # Em co_ocorrência ambos os pares (A,B) e (B,A) contam
                pairs.append((a, b))
        return pairs

    def influenced_outcome(
        self,
        tenant_id: str,
        outcome_id: str,
    ) -> List[ClinicalContext]:
        return [
            c for c in self._contexts
            if c.tenant_id == tenant_id and outcome_id in c.linked_outcome_ids
        ]

    def preceded_improvement(
        self,
        tenant_id: str,
        patient_id: str,
        window_days: int = 30,
    ) -> List[ClinicalContext]:
        from datetime import timedelta
        # Encontra eventos OUTCOME_IMPROVEMENT do paciente
        improvements = [
            ev for ev in self._events
            if ev.get("event_type") == "OUTCOME_IMPROVEMENT"
            and ev.get("tenant_id") == tenant_id
            and ev.get("patient_id") == patient_id
        ]
        if not improvements:
            return []
        # Janela: [improvement_date - window_days, improvement_date)
        result: List[ClinicalContext] = []
        for ev in improvements:
            ev_dt_raw = ev.get("event_datetime")
            if isinstance(ev_dt_raw, str):
                s = ev_dt_raw.rstrip("Z") + ("+00:00" if ev_dt_raw.endswith("Z") else "")
                improvement_dt = datetime.fromisoformat(s)
                if improvement_dt.tzinfo is None:
                    improvement_dt = improvement_dt.replace(tzinfo=timezone.utc)
            elif isinstance(ev_dt_raw, datetime):
                improvement_dt = _ensure_tz(ev_dt_raw)
            else:
                continue
            window_start = improvement_dt - timedelta(days=window_days)
            for c in self._contexts:
                if c.tenant_id != tenant_id or c.patient_id != patient_id:
                    continue
                cs = _ensure_tz(c.start_date)
                ce = _ensure_tz(c.end_date) if c.end_date else None
                # contexto precede a melhora: terminou dentro da janela
                if ce is not None and window_start <= ce < improvement_dt:
                    result.append(c)
        # Dedup por context_id
        seen: set = set()
        deduped: List[ClinicalContext] = []
        for c in result:
            if c.context_id not in seen:
                seen.add(c.context_id)
                deduped.append(c)
        return deduped

    def active_during(
        self,
        tenant_id: str,
        intervention_id: str,
    ) -> List[ClinicalContext]:
        # Encontra o aggregate da intervenção (via eventos INTERVENTION_STARTED)
        for ev in self._events:
            if (
                ev.get("event_type") == "INTERVENTION_STARTED"
                and ev.get("tenant_id") == tenant_id
            ):
                agg_id = ev.get("aggregate_id")
                if agg_id == intervention_id:
                    ev_dt_raw = ev.get("event_datetime")
                    if isinstance(ev_dt_raw, str):
                        s = ev_dt_raw.rstrip("Z") + ("+00:00" if ev_dt_raw.endswith("Z") else "")
                        start = datetime.fromisoformat(s)
                        if start.tzinfo is None:
                            start = start.replace(tzinfo=timezone.utc)
                    elif isinstance(ev_dt_raw, datetime):
                        start = _ensure_tz(ev_dt_raw)
                    else:
                        continue
                    # busca intervenção STOPPED correspondente
                    end_dt = None
                    for ev2 in self._events:
                        if (
                            ev2.get("event_type") == "INTERVENTION_STOPPED"
                            and ev2.get("aggregate_id") == intervention_id
                            and ev2.get("tenant_id") == tenant_id
                        ):
                            ev2_dt = ev2.get("event_datetime")
                            if isinstance(ev2_dt, str):
                                s2 = ev2_dt.rstrip("Z") + ("+00:00" if ev2_dt.endswith("Z") else "")
                                end_dt = datetime.fromisoformat(s2)
                                if end_dt.tzinfo is None:
                                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                            elif isinstance(ev2_dt, datetime):
                                end_dt = _ensure_tz(ev2_dt)
                            break
                    patient_id = ev.get("patient_id", "")
                    return [
                        c for c in self._contexts
                        if c.tenant_id == tenant_id
                        and c.patient_id == patient_id
                        and c.is_active_on(start)
                        and (end_dt is None or c.is_active_on(end_dt))
                    ]
        return []
