"""
Projeção do Clinical Genome (Fase 0).

Lê os eventos clínicos reais do Ara Intake (``INTAKE_INTERVIEW_COMPLETED``)
gravados no Clinical Event Store e projeta o estado por Clinical Gene:
valor atual (0-10), tendência e histórico de Expressões.

Fonte da verdade = event store (append-only, hash chain). A projeção é
derivada e reproduzível — nunca é origem.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

INTAKE_EVENT_TYPE = "INTAKE_INTERVIEW_COMPLETED"


def project_genome(
    db_session: Any,
    tenant_id: str,
    patient_id: str,
) -> Dict[str, Any]:
    """Projeta o genome do paciente a partir dos eventos de pré-consulta.

    Returns:
        {
          "patient_id": ...,
          "genes": {
             "sono":  {"value": 4.0, "label": "...", "direction": "...",
                        "history": [{"value": ..., "at": "..."}]},
             ...
          },
          "updated_at": ...,
          "events_count": N
        }
    """
    from araos.clinical.event_store import SqlAlchemyClinicalEventStore

    store = SqlAlchemyClinicalEventStore(db_session)
    events = store.query(
        tenant_id=tenant_id,
        patient_id=patient_id,
        event_types=[INTAKE_EVENT_TYPE],
        order_by="event_datetime ASC",
    )

    genes: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

    for ev in events:
        payload = ev.get("payload") if isinstance(ev, dict) else (ev.payload or {})
        gene_exprs = payload.get("gene_expressions") or []
        occurred = _event_dt(ev)
        for g in gene_exprs:
            gene = g.get("gene")
            if not gene:
                continue
            entry = genes.setdefault(
                gene,
                {
                    "gene": gene,
                    "value": None,
                    "label": None,
                    "direction": "neutral",
                    "history": [],
                },
            )
            value = g.get("value")
            try:
                value = float(value) if value is not None else None
            except (TypeError, ValueError):
                value = None
            entry["value"] = value
            entry["label"] = g.get("label") or entry["label"]
            entry["direction"] = g.get("direction") or entry["direction"]
            if value is not None:
                entry["history"].append({"value": value, "at": occurred})

    # Tendência: primeiro vs último valor disponível
    for entry in genes.values():
        hist = entry["history"]
        if len(hist) >= 2:
            first = hist[0]["value"]
            last = hist[-1]["value"]
            if last is not None and first is not None:
                if last - first > 0.5:
                    entry["trend"] = "improving"
                elif first - last > 0.5:
                    entry["trend"] = "worsening"
                else:
                    entry["trend"] = "stable"
        else:
            entry["trend"] = "first_measurement"

    last_at = None
    if events:
        last_at = _event_dt(events[-1])

    return {
        "patient_id": patient_id,
        "tenant_id": tenant_id,
        "genes": dict(genes),
        "updated_at": last_at,
        "events_count": len(events),
        "source": "ara_intake",
    }


def _event_dt(ev: Any) -> Optional[str]:
    """Retorna o event_datetime como string ISO (dict ou model)."""
    if isinstance(ev, dict):
        dt = ev.get("event_datetime")
        if isinstance(dt, str):
            return dt
        return dt.isoformat() if dt is not None else None
    dt = getattr(ev, "event_datetime", None)
    if isinstance(dt, str):
        return dt
    return dt.isoformat() if dt is not None else None
