"""
AraOS Clinical Event Engine — Store.

Interface para persistência e consulta de eventos clínicos.
Duas implementações:
    - InMemoryClinicalEventStore: testes/demos, thread-safe
    - SqlAlchemyClinicalEventStore: produção (PostgreSQL)

Append-only: correções são feitas por novo evento, nunca UPDATE.
Hash chain SHA-256 garante integridade detectável.
"""

from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .hash_chain import (
    GENESIS_HASH,
    compute_event_hash,
    verify_chain,
    find_break,
)


# ═══════════════════════════════════════════════════════════════════════
# INTERFACE ABSTRATA
# ═══════════════════════════════════════════════════════════════════════


class ClinicalEventStore(ABC):
    """Contrato para qualquer implementação de Event Store."""

    @abstractmethod
    def append(
        self,
        tenant_id: str,
        patient_id: str,
        event_type: str,
        event_datetime: datetime,
        source_module: str,
        payload: Dict[str, Any],
        event_version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        created_by: Optional[str] = None,
        created_by_user: Optional[str] = None,
    ) -> str:
        """
        Anexa novo evento ao store.

        Returns:
            event_id (UUID4).
        """
        ...

    @abstractmethod
    def get(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Busca evento por id. Retorna dict ou None."""
        ...

    @abstractmethod
    def query(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        order_by: str = "event_datetime ASC",
        limit: Optional[int] = None,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Consulta eventos com filtros.

        Args:
            event_types: lista de event_types OU padrões com wildcard (ex: 'DIAGNOSIS_*').
            order_by: 'event_datetime ASC' | 'event_datetime DESC' | 'created_at ASC' | 'created_at DESC'
            limit: máximo de eventos retornados (None = sem limite).
        """
        ...

    @abstractmethod
    def last_hash(self, tenant_id: str) -> Optional[str]:
        """Hash do último evento do tenant (None se vazio)."""
        ...

    @abstractmethod
    def verify_chain(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
    ) -> bool:
        """Verifica integridade da hash chain."""
        ...

    @abstractmethod
    def count(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
    ) -> int:
        """Conta eventos (útil para dashboards/ETL)."""
        ...


# ═══════════════════════════════════════════════════════════════════════
# IN-MEMORY (testes/demos)
# ═══════════════════════════════════════════════════════════════════════


class InMemoryClinicalEventStore(ClinicalEventStore):
    """
    Implementação thread-safe em memória.

    Usado em:
        - Testes unitários e de integração
        - Demos
        - Cenários onde a durabilidade do PostgreSQL é dispensável

    Não persiste além do processo. Hash chain é mantida na memória.
    """

    def __init__(self) -> None:
        self._events: List[Dict[str, Any]] = []
        self._by_id: Dict[str, Dict[str, Any]] = {}
        # Per-tenant monotonic sequence counter.
        # next_seq[tenant_id] = próximo sequence a atribuir.
        self._next_seq: Dict[str, int] = {}
        # RLock: append() chama last_hash() internamente — precisa ser re-entrante.
        self._lock = threading.RLock()

    def append(
        self,
        tenant_id: str,
        patient_id: str,
        event_type: str,
        event_datetime: datetime,
        source_module: str,
        payload: Dict[str, Any],
        event_version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        created_by: Optional[str] = None,
        created_by_user: Optional[str] = None,
    ) -> str:
        if event_datetime is None:
            raise ValueError("event_datetime is required")
        if not event_type:
            raise ValueError("event_type is required")
        if not tenant_id or not patient_id:
            raise ValueError("tenant_id and patient_id are required")

        with self._lock:
            event_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            # Sequence monotônico per-tenant (insertion order).
            seq = self._next_seq.get(tenant_id, 1)
            self._next_seq[tenant_id] = seq + 1
            prev_hash = self.last_hash(tenant_id)

            event: Dict[str, Any] = {
                "id": event_id,
                "tenant_id": tenant_id,
                "patient_id": patient_id,
                "event_type": event_type,
                "event_version": event_version,
                "event_datetime": _isoformat(event_datetime),
                "source_module": source_module,
                "payload": dict(payload or {}),
                "metadata": dict(metadata or {}),
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "created_by": created_by,
                "created_by_user": created_by_user,
                "created_at": _isoformat(now),
                "updated_at": None,
                "deleted_at": None,
                "previous_hash": prev_hash,
                "sequence": seq,
            }
            # Hash SEM incluir event_hash (auto-referência)
            event["event_hash"] = compute_event_hash(prev_hash, event)

            self._events.append(event)
            self._by_id[event_id] = event
            return event_id

    def get(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self._by_id.get(event_id)

    def query(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        order_by: str = "sequence ASC",
        limit: Optional[int] = None,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            snapshot = list(self._events)

        results: List[Dict[str, Any]] = []
        for e in snapshot:
            if e["tenant_id"] != tenant_id:
                continue
            if patient_id and e["patient_id"] != patient_id:
                continue
            if event_types and not any(_matches(e["event_type"], t) for t in event_types):
                continue
            if aggregate_type and e.get("aggregate_type") != aggregate_type:
                continue
            if aggregate_id and e.get("aggregate_id") != aggregate_id:
                continue
            if not include_deleted and e.get("deleted_at") is not None:
                continue

            ev_dt = _parse_iso(e["event_datetime"])
            if since and ev_dt and ev_dt < since:
                continue
            if until and ev_dt and ev_dt > until:
                continue

            results.append(e)

        results = _sort_events(results, order_by)
        if limit is not None:
            results = results[:limit]
        return results

    def last_hash(self, tenant_id: str) -> Optional[str]:
        """Hash do último evento do tenant pela SEQUENCE (insertion order)."""
        with self._lock:
            best = None
            for e in self._events:
                if e["tenant_id"] != tenant_id:
                    continue
                if best is None or e["sequence"] > best["sequence"]:
                    best = e
            return best["event_hash"] if best else None

    def verify_chain(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
    ) -> bool:
        """Chain canônica ordenada por SEQUENCE (insertion order).

        event_datetime é atributo de payload (clinical time) — pode ser
        backdated, batch-imported, etc. A chain reflete a sequência de
        registro no sistema.
        """
        events = self.query(
            tenant_id=tenant_id,
            patient_id=patient_id,
            order_by="sequence ASC",
        )
        return verify_chain(events)

    def count(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
    ) -> int:
        return len(
            self.query(tenant_id=tenant_id, patient_id=patient_id, order_by="event_datetime ASC")
        )

    # helpers de debug/teste
    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._by_id.clear()
            self._next_seq.clear()


# ═══════════════════════════════════════════════════════════════════════
# SQLALCHEMY (produção)
# ═══════════════════════════════════════════════════════════════════════


class SqlAlchemyClinicalEventStore(ClinicalEventStore):
    """
    Implementação com SQLAlchemy Session.

    Sequence per-tenant é alocada atomicamente via SELECT ... FOR UPDATE
    em `clinical_event_sequences`. Isto garante:
        - Insertion order determinístico para a hash chain
        - Concurrency-safe (PostgreSQL row lock; SQLite single-threaded)
        - Independência entre tenants

    Chain canônica é ordenada por `sequence` (não event_datetime).
    event_datetime é atributo do payload (clinical time).
    """

    def __init__(self, db_session: Any) -> None:
        self.db = db_session

    def _next_sequence(self, tenant_id: str) -> int:
        """Aloca próximo sequence para o tenant, atomicamente.

        PostgreSQL: SELECT ... FOR UPDATE bloqueia a linha do tracker.
        SQLite: serialized por Session.
        Primeiro evento do tenant: cria a linha do tracker.
        """
        from .models import ClinicalEventSequence
        from sqlalchemy.orm import Session

        # Tenta lock na linha existente
        seq_row = (
            self.db.query(ClinicalEventSequence)
            .filter(ClinicalEventSequence.tenant_id == tenant_id)
            .with_for_update()
            .first()
        )
        if seq_row is None:
            seq_row = ClinicalEventSequence(
                tenant_id=tenant_id,
                last_sequence=1,
            )
            self.db.add(seq_row)
            self.db.flush()
            return 1
        seq_row.last_sequence += 1
        seq_row.updated_at = datetime.now(timezone.utc)
        self.db.flush()
        return seq_row.last_sequence

    def append(
        self,
        tenant_id: str,
        patient_id: str,
        event_type: str,
        event_datetime: datetime,
        source_module: str,
        payload: Dict[str, Any],
        event_version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        created_by: Optional[str] = None,
        created_by_user: Optional[str] = None,
        autocommit: bool = True,
    ) -> str:
        """Append um ClinicalEvent.

        Args:
            autocommit: Se True (default — comportamento legado),
                commita imediatamente após o add. Se False, apenas
                faz flush — caller (UnitOfWork) controla a transação
                atômica. Sprint 4.5 W1.6 introduz este parametro para
                permitir integração com KnowledgeUnitOfWork.
        """
        from .models import ClinicalEventModel

        if event_datetime is None:
            raise ValueError("event_datetime is required")
        if not event_type:
            raise ValueError("event_type is required")
        if not tenant_id or not patient_id:
            raise ValueError("tenant_id and patient_id are required")

        # Garante timezone-aware (PostgreSQL TIMESTAMPTZ)
        if event_datetime.tzinfo is None:
            event_datetime = event_datetime.replace(tzinfo=timezone.utc)

        # 1. Aloca sequence atomicamente (pode criar linha do tracker)
        sequence = self._next_sequence(tenant_id)
        # 2. Busca último hash pela sequence (insertion order canônico)
        prev_hash = self._last_hash_by_sequence(tenant_id)
        event_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Monta dict SEM event_hash para calcular
        event_for_hash: Dict[str, Any] = {
            "id": event_id,
            "tenant_id": tenant_id,
            "patient_id": patient_id,
            "event_type": event_type,
            "event_version": event_version,
            "event_datetime": _isoformat(event_datetime),
            "source_module": source_module,
            "payload": dict(payload or {}),
            "metadata": dict(metadata or {}),
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "created_by": created_by,
            "created_by_user": created_by_user,
            "created_at": _isoformat(now),
            "updated_at": None,
            "deleted_at": None,
            "previous_hash": prev_hash,
            "sequence": sequence,
        }
        event_hash = compute_event_hash(prev_hash, event_for_hash)

        model = ClinicalEventModel(
            id=event_id,
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event_type,
            event_version=event_version,
            event_datetime=event_datetime,
            source_module=source_module,
            payload=dict(payload or {}),
            event_metadata=dict(metadata or {}),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            created_by=created_by,
            created_by_user=created_by_user,
            created_at=now,
            updated_at=None,
            deleted_at=None,
            previous_hash=prev_hash,
            event_hash=event_hash,
            sequence=sequence,
        )
        self.db.add(model)
        if autocommit:
            self.db.commit()
        else:
            self.db.flush()
        return event_id

    def _last_hash_by_sequence(self, tenant_id: str) -> Optional[str]:
        """Hash do evento com maior sequence do tenant (None se vazio)."""
        from .models import ClinicalEventModel

        last_event = (
            self.db.query(ClinicalEventModel)
            .filter(ClinicalEventModel.tenant_id == tenant_id)
            .order_by(ClinicalEventModel.sequence.desc())
            .first()
        )
        return last_event.event_hash if last_event else None

    def get(self, event_id: str) -> Optional[Dict[str, Any]]:
        from .models import ClinicalEventModel
        model = (
            self.db.query(ClinicalEventModel)
            .filter(ClinicalEventModel.id == event_id)
            .first()
        )
        return model.to_dict() if model else None

    def query(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        order_by: str = "sequence ASC",
        limit: Optional[int] = None,
        include_deleted: bool = False,
    ) -> List[Dict[str, Any]]:
        from sqlalchemy import or_

        from .models import ClinicalEventModel

        q = self.db.query(ClinicalEventModel).filter(
            ClinicalEventModel.tenant_id == tenant_id
        )
        if patient_id:
            q = q.filter(ClinicalEventModel.patient_id == patient_id)
        if aggregate_type:
            q = q.filter(ClinicalEventModel.aggregate_type == aggregate_type)
        if aggregate_id:
            q = q.filter(ClinicalEventModel.aggregate_id == aggregate_id)
        if not include_deleted:
            q = q.filter(ClinicalEventModel.deleted_at.is_(None))
        if since:
            q = q.filter(ClinicalEventModel.event_datetime >= since)
        if until:
            q = q.filter(ClinicalEventModel.event_datetime <= until)

        # Filtro event_types com wildcard support
        if event_types:
            type_conditions = []
            for t in event_types:
                if t.endswith("*"):
                    prefix = t[:-1]
                    type_conditions.append(
                        ClinicalEventModel.event_type.like(f"{prefix}%")
                    )
                else:
                    type_conditions.append(ClinicalEventModel.event_type == t)
            if type_conditions:
                q = q.filter(or_(*type_conditions))

        # Ordenação (whitelist).
        # Default = sequence ASC (insertion order canônico da chain).
        if order_by == "event_datetime ASC":
            q = q.order_by(
                ClinicalEventModel.event_datetime.asc(),
                ClinicalEventModel.sequence.asc(),
            )
        elif order_by == "event_datetime DESC":
            q = q.order_by(
                ClinicalEventModel.event_datetime.desc(),
                ClinicalEventModel.sequence.desc(),
            )
        elif order_by == "created_at ASC":
            q = q.order_by(
                ClinicalEventModel.created_at.asc(),
                ClinicalEventModel.sequence.asc(),
            )
        elif order_by == "created_at DESC":
            q = q.order_by(
                ClinicalEventModel.created_at.desc(),
                ClinicalEventModel.sequence.desc(),
            )
        elif order_by == "sequence DESC":
            q = q.order_by(ClinicalEventModel.sequence.desc())
        else:
            # default: sequence ASC
            q = q.order_by(ClinicalEventModel.sequence.asc())

        if limit is not None:
            q = q.limit(limit)

        return [m.to_dict() for m in q.all()]

    def last_hash(self, tenant_id: str) -> Optional[str]:
        """Hash do último evento pela SEQUENCE (insertion order canônico)."""
        return self._last_hash_by_sequence(tenant_id)

    def verify_chain(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
    ) -> bool:
        """Chain canônica ordenada por SEQUENCE (insertion order).

        event_datetime é atributo de payload — pode ser backdated,
        batch-imported, registrado com delay. A sequence é a verdade
        imutável de "quando o sistema tomou conhecimento".
        """
        events = self.query(
            tenant_id=tenant_id,
            patient_id=patient_id,
            order_by="sequence ASC",
        )
        return verify_chain(events)

    def count(
        self,
        tenant_id: str,
        patient_id: Optional[str] = None,
    ) -> int:
        from .models import ClinicalEventModel
        from sqlalchemy import func

        q = self.db.query(func.count(ClinicalEventModel.id)).filter(
            ClinicalEventModel.tenant_id == tenant_id
        )
        if patient_id:
            q = q.filter(ClinicalEventModel.patient_id == patient_id)
        return int(q.scalar() or 0)


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════


def _matches(event_type: str, pattern: str) -> bool:
    """Suporta wildcard: 'DIAGNOSIS_*' casa com 'DIAGNOSIS_ADDED' e
    também com 'DIAGNOSIS_' (asterisco inclui sequência vazia, semântica SQL LIKE)."""
    if pattern == event_type:
        return True
    if pattern.endswith("*"):
        return event_type.startswith(pattern[:-1])
    return False


def _sort_events(
    events: List[Dict[str, Any]],
    order_by: str,
) -> List[Dict[str, Any]]:
    if order_by == "event_datetime DESC":
        return sorted(
            events,
            key=lambda e: _parse_iso(e["event_datetime"]) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    if order_by == "created_at ASC":
        return sorted(
            events,
            key=lambda e: _parse_iso(e["created_at"]) or datetime.min.replace(tzinfo=timezone.utc),
        )
    if order_by == "created_at DESC":
        return sorted(
            events,
            key=lambda e: _parse_iso(e["created_at"]) or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    if order_by == "sequence ASC":
        return sorted(events, key=lambda e: e.get("sequence", 0))
    if order_by == "sequence DESC":
        return sorted(events, key=lambda e: e.get("sequence", 0), reverse=True)
    # default: event_datetime ASC
    return sorted(
        events,
        key=lambda e: _parse_iso(e["event_datetime"]) or datetime.min.replace(tzinfo=timezone.utc),
    )


def _isoformat(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        # Suporta tanto '...+00:00' quanto '...Z'
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except ValueError:
        return None
