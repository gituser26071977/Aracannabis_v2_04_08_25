"""
ActiveContextProjection — projeção read-side que mantém apenas os
Contextos ATIVOS (status in PLANNED/ACTIVE/SUGGESTED) por paciente.

Idempotente. Pode ser reconstruída a partir do log.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from .handlers import HANDLERS_BY_EVENT_TYPE


_ACTIVE_STATUSES = ("planned", "suggested", "active")


class ActiveContextProjection:
    """Projeção read-side dos contextos ativos."""

    TABLE_NAME = "clinical_contexts_active"

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def apply(self, event: Dict[str, Any]) -> bool:
        """Atualiza projection baseado em 1 evento."""
        from .handlers import (
            handle_clinical_context_created,
            REDACTED,
            handle_clinical_context_linked,
            handle_clinical_context_unlinked,
            handle_clinical_context_rejected,
            REDACTED,
            handle_clinical_context_updated,
        )

        event_type = event.get("event_type")
        if event_type not in HANDLERS_BY_EVENT_TYPE:
            return False
        tenant_id = event.get("tenant_id")
        payload = event.get("payload") or {}
        context_id = payload.get("context_id")
        if not (tenant_id and context_id):
            return False

        with self._session_factory() as session:
            if event_type == "CLINICAL_CONTEXT_SUGGESTED":
                return True    # apenas marca processed; a real criação vem
                               # via evento CREATED posterior
            if event_type == "CLINICAL_CONTEXT_CREATED":
                # Inject patient_id from event if not in payload.
                if payload.get("patient_id") is None:
                    payload = {**payload, "patient_id": event.get("patient_id")}
                return self._insert_if_active(session, tenant_id, payload)
            if event_type in (
                "CLINICAL_CONTEXT_ACTIVATED",
                "CLINICAL_CONTEXT_CLOSED",
                "CLINICAL_CONTEXT_REOPENED",
            ):
                # status change → re-sync projection entry
                return self._resync(session, tenant_id, context_id)
            if event_type == "CLINICAL_CONTEXT_REJECTED":
                return self._delete(session, tenant_id, context_id)
            if event_type in (
                "CLINICAL_CONTEXT_LINKED",
                "CLINICAL_CONTEXT_UNLINKED",
            ):
                return True     # relationships handled em outra projection
            if event_type == "CLINICAL_CONTEXT_TYPE_CONFIRMED":
                return self._resync(session, tenant_id, context_id)
            if event_type == "CLINICAL_CONTEXT_UPDATED":
                return self._resync(session, tenant_id, context_id)
        return False

    # ─── Helpers ───────────────────────────────────────────────────

    def _insert_if_active(self, session: Session, tenant_id: str, payload: Dict[str, Any]) -> bool:
        raw_status = payload.get("status")
        # Compare case-insensitive: payload carries canonical capitalized form
        # ("Planned"/"Active"/"Suggested"), _ACTIVE_STATUSES is lowercase canonical.
        if raw_status is None:
            return False
        if str(raw_status).lower() not in _ACTIVE_STATUSES:
            return False
        context_id = payload["context_id"]
        session.execute(
            text(
                f"INSERT OR REPLACE INTO {self.TABLE_NAME} "
                "(context_id, tenant_id, patient_id, context_type, status, "
                " origin, title, start_date, end_date, confidence_score, "
                " suggestion_id, updated_at) VALUES "
                "(:cid, :tid, :pid, :ct, :st, :og, :ti, :sd, :ed, :cf, :sg, :ua)"
            ),
            {
                "cid": context_id,
                "tid": tenant_id,
                "pid": payload.get("patient_id"),
                "ct": payload.get("context_type"),
                "st": payload.get("status"),
                "og": payload.get("origin"),
                "ti": payload.get("title"),
                "sd": payload.get("start_date"),
                "ed": payload.get("end_date"),
                "cf": payload.get("confidence_score") or 1.0,
                "sg": payload.get("suggestion_id"),
                "ua": datetime.now(timezone.utc).isoformat(),
            },
        )
        session.commit()
        return True

    def _resync(self, session: Session, tenant_id: str, context_id: str) -> bool:
        """Re-sincroniza a entrada ativa baseado no aggregate."""
        row = session.execute(
            text(
                "SELECT patient_id, context_type, status, origin, title, "
                "start_date, end_date, confidence_score, suggestion_id "
                "FROM clinical_contexts WHERE context_id = :cid AND tenant_id = :tid"
            ),
            {"cid": context_id, "tid": tenant_id},
        ).first()
        if row is None:
            return False
        d = dict(row._mapping)
        status = d.get("status")
        # Case-insensitive comparison — canonical form in DB is capitalized.
        if status is not None and str(status).lower() in _ACTIVE_STATUSES:
            session.execute(
                text(
                    f"INSERT OR REPLACE INTO {self.TABLE_NAME} "
                    "(context_id, tenant_id, patient_id, context_type, status, "
                    " origin, title, start_date, end_date, confidence_score, "
                    " suggestion_id, updated_at) VALUES "
                    "(:cid, :tid, :pid, :ct, :st, :og, :ti, :sd, :ed, :cf, :sg, :ua)"
                ),
                {
                    "cid": context_id,
                    "tid": tenant_id,
                    "pid": d["patient_id"],
                    "ct": d["context_type"],
                    "st": status,
                    "og": d["origin"],
                    "ti": d["title"],
                    "sd": d["start_date"],
                    "ed": d["end_date"],
                    "cf": d["confidence_score"],
                    "sg": d["suggestion_id"],
                    "ua": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            session.execute(
                text(
                    f"DELETE FROM {self.TABLE_NAME} "
                    "WHERE context_id = :cid AND tenant_id = :tid"
                ),
                {"cid": context_id, "tid": tenant_id},
            )
        session.commit()
        return True

    def _delete(self, session: Session, tenant_id: str, context_id: str) -> bool:
        session.execute(
            text(
                f"DELETE FROM {self.TABLE_NAME} "
                "WHERE context_id = :cid AND tenant_id = :tid"
            ),
            {"cid": context_id, "tid": tenant_id},
        )
        session.commit()
        return True

    # ─── Read ──────────────────────────────────────────────────────

    def list_active_for_patient(
        self,
        tenant_id: str,
        patient_id: str,
    ) -> List[Dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                text(
                    f"SELECT context_id, context_type, status, origin, title, "
                    "start_date, end_date, confidence_score, suggestion_id "
                    f"FROM {self.TABLE_NAME} "
                    "WHERE tenant_id = :tid AND patient_id = :pid "
                    "ORDER BY start_date ASC"
                ),
                {"tid": tenant_id, "pid": patient_id},
            ).all()
            return [dict(r._mapping) for r in rows]
