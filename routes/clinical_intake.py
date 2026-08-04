"""
Ara Intake → AraOS — consumidor de Clinical Events (Fase 0).

Recebe os eventos de pré-consulta concluída do Ara Intake e grava no
Clinical Event Store do AraOS (`clinical_events`), alimentando a timeline
e o Clinical Genome.

Segurança: valida o header `X-AraOS-Signature` contra o secret configurado
(env `CLINICAL_EVENT_SECRET`). Se ausente, aceita apenas em dev.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Blueprint, current_app, jsonify, request

from araos.clinical.event_store import ClinicalEventPublisher, SqlAlchemyClinicalEventStore

logger = logging.getLogger(__name__)

clinical_intake_bp = Blueprint(
    "clinical_intake",
    __name__,
    url_prefix="/api/v1/clinical",
)


def _publisher() -> ClinicalEventPublisher:
    """Retorna o publisher com store SQLAlchemy.

    Usa `CLINICAL_EVENT_SESSION_FACTORY` se injetada (testes/staging) ou
    o `db.session` do Flask (produção).
    """
    sf = current_app.config.get("CLINICAL_EVENT_SESSION_FACTORY")
    if sf is not None:
        store = SqlAlchemyClinicalEventStore(sf())
        return ClinicalEventPublisher(store=store, validate_payload=False)

    from models import db

    store = SqlAlchemyClinicalEventStore(db.session)
    return ClinicalEventPublisher(store=store, validate_payload=False)


def _signature_valid(raw_body: bytes) -> bool:
    """Valida o secret token do header."""
    secret = current_app.config.get("CLINICAL_EVENT_SECRET")
    if not secret:
        # Sem secret configurado → só aceita em dev
        if current_app.config.get("ENV", "development") == "production":
            return False
        return True
    provided = request.headers.get("X-AraOS-Signature", "")
    expected = hmac.new(
        secret.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(provided, expected)


def _derive_patient_id(event: Dict[str, Any]) -> str:
    """Deriva um patient_id estável a partir do evento do intake.

    Fase 0: ainda não há match com a tabela `pacientes`; usa um hash estável
    de (tenant + telefone/nome) para agregar eventos do mesmo paciente.
    """
    tenant = event.get("tenant_id") or "default"
    evidence = event.get("evidence") or []
    phone = ""
    name = event.get("patient_name") or ""
    for item in evidence:
        if item.get("field_id") == "phone" and item.get("value"):
            phone = item["value"]
            break
    seed = f"{tenant}|{phone}|{name}".strip("|")
    return "intake:" + hashlib.sha256(seed.encode()).hexdigest()[:24]


@clinical_intake_bp.route("/events", methods=["POST"])
def ingest_intake_event():
    """Ingere um Clinical Event do Ara Intake."""
    raw = request.get_data()
    if not _signature_valid(raw):
        return jsonify({"error": "invalid signature"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "invalid json"}), 400

    try:
        occurred_at = datetime.fromisoformat(data.get("occurred_at", ""))
    except (ValueError, TypeError):
        occurred_at = datetime.utcnow()

    patient_id = _derive_patient_id(data)
    tenant_id = data.get("tenant_id") or "default"

    payload: Dict[str, Any] = {
        "evidence": data.get("evidence") or [],
        "gene_expressions": data.get("gene_expressions") or [],
        "form_slug": data.get("form_slug"),
        "form_version": data.get("form_version"),
        "patient_name": data.get("patient_name"),
        "source_id": data.get("source_id"),
    }

    try:
        event_id = _publisher().publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type="INTAKE_INTERVIEW_COMPLETED",
            payload=payload,
            event_datetime=occurred_at,
            source_module="ara_intake",
            metadata={
                "doctor_id": data.get("doctor_id"),
                "source_event_id": data.get("id"),
            },
            aggregate_type="intake_interview",
            aggregate_id=data.get("source_id"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("intake_event_ingest_failed")
        return jsonify({"error": "failed to persist event", "detail": str(exc)}), 500

    logger.info("intake_event_ingested", event_id=event_id, type=data.get("type"))
    return jsonify({"ok": True, "event_id": event_id}), 200
