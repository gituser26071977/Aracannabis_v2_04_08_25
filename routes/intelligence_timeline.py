"""
Intelligence Timeline API — Sprint 4.1.

Blueprint: `intelligence_timeline` (prefix /api/intelligence).

Endpoints:
    GET  /timeline/{patient_id}                       → entries ordenadas por sequence
    GET  /timeline/{patient_id}/range                 → entries com since/until
    GET  /aggregates/{aggregate_type}/{aggregate_id}/timeline
    GET  /timeline/{patient_id}/count                 → count only (dashboards)

Reutiliza helpers de `routes/_helpers.py` (Sprint 3.2 pattern).
Lê do ClinicalEventStore (Sprint 3.1) via InMemoryTimelineQuery.
Não escreve no Registry — read-side puro.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from araos.clinical.event_store.store import ClinicalEventStore
from araos.clinical.timeline.application.query import InMemoryTimelineQuery
from araos.clinical.timeline.domain.window import TimeWindow
from routes._helpers import (
    _get_actor_id,
    _parse_isoformat_optional,
    _resolve_tenant_id,
    get_logger,
)


intelligence_timeline_bp = Blueprint(
    "intelligence_timeline", __name__, url_prefix="/api/intelligence",
)
_logger = get_logger("intelligence.timeline")


# ─── Service accessor ─────────────────────────────────────────────────


def _timeline_query() -> InMemoryTimelineQuery:
    """Resolve TimelineQuery a partir do app context.

    Cria um InMemoryTimelineQuery em cima do EventStore configurado.
    Em produção, pode-se trocar por SqlAlchemyTimelineQuery (Sprint 4.5).
    """
    store: Optional[ClinicalEventStore] = current_app.config.get(
        "CLINICAL_EVENT_STORE",
    )
    if store is None:
        raise RuntimeError("CLINICAL_EVENT_STORE not configured in app")
    return InMemoryTimelineQuery(event_store=store)


def _wildcard_match(event_type: str, patterns: List[str]) -> bool:
    """Suporta wildcard: 'DIAGNOSIS_*' matches 'DIAGNOSIS_CONFIRMED'."""
    for pattern in patterns:
        if pattern == event_type:
            return True
        if pattern.endswith("*") and event_type.startswith(pattern[:-1]):
            return True
        if pattern.startswith("*") and event_type.endswith(pattern[1:]):
            return True
    return False


# ─── Endpoints ────────────────────────────────────────────────────────


@intelligence_timeline_bp.route("/timeline/<patient_id>", methods=["GET"])
@jwt_required()
def get_timeline(patient_id: str):
    """Retorna a timeline completa do paciente, ordenada por sequence ASC."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 401
    if not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    event_types_param = request.args.get("event_types")
    event_types: Optional[List[str]] = None
    if event_types_param:
        event_types = [t.strip() for t in event_types_param.split(",") if t.strip()]

    episode_id = request.args.get("episode_id")
    limit = int(request.args.get("limit", "1000"))
    limit = min(max(limit, 1), 5000)            # cap defensivo

    try:
        query = _timeline_query()
        entries = query.for_patient(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_types=event_types,
            episode_id=episode_id,
            limit=limit,
        )
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:                    # pragma: no cover
        _logger.error("timeline_query_failed", extra={"error": str(e)})
        return jsonify({"error": "internal_error"}), 500

    return jsonify({
        "tenant_id": tenant_id,
        "patient_id": patient_id,
        "count": len(entries),
        "entries": [e.to_dict() for e in entries],
    }), 200


@intelligence_timeline_bp.route("/timeline/<patient_id>/range", methods=["GET"])
@jwt_required()
def get_timeline_range(patient_id: str):
    """Retorna timeline dentro de uma janela temporal explícita."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 401
    if not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    since = _parse_isoformat_optional(request.args.get("since"))
    until = _parse_isoformat_optional(request.args.get("until"))
    if since is None or until is None:
        return jsonify({"error": "since and until (ISO 8601) required"}), 400
    if since > until:
        return jsonify({"error": "since must be <= until"}), 400

    event_types_param = request.args.get("event_types")
    event_types: Optional[List[str]] = None
    if event_types_param:
        event_types = [t.strip() for t in event_types_param.split(",") if t.strip()]

    try:
        query = _timeline_query()
        window = TimeWindow(start=since, end=until, label="range_query")
        entries = query.for_patient(
            tenant_id=tenant_id,
            patient_id=patient_id,
            window=window,
            event_types=event_types,
            limit=2000,
        )
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    return jsonify({
        "tenant_id": tenant_id,
        "patient_id": patient_id,
        "window": window.to_dict(),
        "count": len(entries),
        "entries": [e.to_dict() for e in entries],
    }), 200


@intelligence_timeline_bp.route(
    "/aggregates/<aggregate_type>/<aggregate_id>/timeline", methods=["GET"]
)
@jwt_required()
def get_aggregate_timeline(aggregate_type: str, aggregate_id: str):
    """Retorna timeline de um aggregate específico (diagnóstico, intervenção...)."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 401
    if not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    try:
        query = _timeline_query()
        entries = query.for_aggregate(
            tenant_id=tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
        )
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    return jsonify({
        "tenant_id": tenant_id,
        "aggregate_type": aggregate_type,
        "aggregate_id": aggregate_id,
        "count": len(entries),
        "entries": [e.to_dict() for e in entries],
    }), 200


@intelligence_timeline_bp.route("/timeline/<patient_id>/count", methods=["GET"])
@jwt_required()
def get_timeline_count(patient_id: str):
    """Conta entradas (para dashboards)."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 401
    if not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    event_types_param = request.args.get("event_types")
    event_types: Optional[List[str]] = None
    if event_types_param:
        event_types = [t.strip() for t in event_types_param.split(",") if t.strip()]

    try:
        query = _timeline_query()
        count = query.count(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_types=event_types,
        )
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503

    return jsonify({
        "tenant_id": tenant_id,
        "patient_id": patient_id,
        "count": count,
    }), 200