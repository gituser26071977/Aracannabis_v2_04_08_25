"""
ClinicalContextProjection — entry point que consome Clinical Events
e atualiza clinical_contexts + clinical_context_relationships.

Idempotência via tabela `processed_events` (Sprint 3.1) — exatamente-uma-vez
por (tenant, sequence).

Reconstruction: se `rebuild=True`, ignora processed_events e reprocessa
do começo (seq inicial) para um tenant — bit-identical a partir do log.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from .handlers import HANDLERS_BY_EVENT_TYPE


logger = logging.getLogger(__name__)


class ClinicalContextProjection:
    """Consome ClinicalEventStore + aplica handlers idempotentemente."""

    CONTEXT_EVENT_TYPES = frozenset(HANDLERS_BY_EVENT_TYPE.keys())

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    # ─── Apply (single-event) ─────────────────────────────────────

    def apply(self, event: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Aplica 1 evento ao projection.

        Returns:
            (processed, reason_if_skipped)
        """
        tenant_id = event.get("tenant_id")
        event_id = event.get("id") or event.get("event_id")
        sequence = event.get("sequence")
        event_type = event.get("event_type")
        if not (tenant_id and event_id and sequence is not None):
            return (False, "missing_required_fields")

        if event_type not in HANDLERS_BY_EVENT_TYPE:
            return (False, "unsupported_event_type")

        handler = HANDLERS_BY_EVENT_TYPE[event_type]

        with self._session_factory() as session:
            # Idempotência: checa processed_events
            existing = session.execute(
                text(
                    "SELECT 1 FROM processed_events WHERE tenant_id = :t AND sequence = :s"
                ),
                {"t": tenant_id, "s": sequence},
            ).first()
            if existing is not None:
                return (False, "already_processed")

            # Executa handler
            try:
                handler(session, event)
                session.execute(
                    text(
                        "INSERT INTO processed_events (id, tenant_id, sequence, "
                        "event_id, event_type, source_module, processed_at) "
                        "VALUES (:id, :t, :s, :e, :et, :sm, :ts)"
                    ),
                    {
                        "id": uuid.uuid4().hex,
                        "t": tenant_id,
                        "s": sequence,
                        "e": event_id,
                        "et": event_type,
                        "sm": event.get("source_module") or "intelligence",
                        "ts": datetime.now(timezone.utc).isoformat(),
                    },
                )
                session.commit()
                return (True, None)
            except Exception as exc:    # pragma: no cover
                session.rollback()
                logger.exception("context_projection_apply_failed")
                return (False, f"handler_exception:{exc}")

    # ─── Replay (rebuild) ─────────────────────────────────────────

    def rebuild(
        self,
        tenant_id: str,
        events: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Limpa projection e reprocessa do início.

        Returns:
            counts: {processed: int, skipped: int, total: int}
        """
        with self._session_factory() as session:
            session.execute(
                text("DELETE FROM REDACTED "
                     "WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
            session.execute(
                text("DELETE FROM clinical_context_relationships "
                     "WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
            session.execute(
                text("DELETE FROM clinical_contexts WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
            session.execute(
                text("DELETE FROM processed_events WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
            session.commit()

        # Processa em ordem de sequence ascendente (Sprint 3.1 garante
        # que sequence é monotônico por tenant, sem buracos).
        ordered = sorted(events, key=lambda e: (e.get("sequence") or 0))
        processed = 0
        skipped = 0
        for ev in ordered:
            ev_with_tenant = dict(ev)
            ev_with_tenant["tenant_id"] = tenant_id
            ok, _ = self.apply(ev_with_tenant)
            if ok:
                processed += 1
            else:
                skipped += 1
        return {"processed": processed, "skipped": skipped, "total": len(ordered)}

    # ─── Snapshot (para testes bit-identical) ──────────────────────

    def snapshot(self, tenant_id: str) -> Dict[str, Any]:
        """Captura estado completo do projection para um tenant.

        Útil para comparar antes/depois de replay.
        """
        with self._session_factory() as session:
            ctx_rows = session.execute(
                text(
                    "SELECT context_id, status, context_type, origin, "
                    "title, aggregate_version, start_date, end_date, "
                    "source_event_ids_json, linked_event_ids_json, "
                    "linked_diagnosis_ids_json, linked_phenotype_ids_json, "
                    "linked_intervention_ids_json, linked_outcome_ids_json, "
                    "linked_assessment_ids_json, professionals_json, "
                    "observations_json, confidence_score, confirmed_by, "
                    "rejected_by, suggestion_id, explanation_id "
                    "FROM clinical_contexts WHERE tenant_id = :t "
                    "ORDER BY context_id"
                ),
                {"t": tenant_id},
            ).all()
            rel_rows = session.execute(
                text(
                    "SELECT relationship_id, source_context_id, target_context_id, "
                    "relationship_type, confidence "
                    "FROM clinical_context_relationships WHERE tenant_id = :t "
                    "ORDER BY relationship_id"
                ),
                {"t": tenant_id},
            ).all()
            proc_rows = session.execute(
                text(
                    "SELECT id, rule_id, event_id, suggestion_id "
                    "FROM REDACTED "
                    "WHERE tenant_id = :t ORDER BY id"
                ),
                {"t": tenant_id},
            ).all()
            return {
                "contexts": [dict(r._mapping) for r in ctx_rows],
                "relationships": [dict(r._mapping) for r in rel_rows],
                "processed_rule_evaluations": [dict(r._mapping) for r in proc_rows],
            }
