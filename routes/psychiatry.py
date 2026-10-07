"""Routes — Módulo Psiquiatria — Triagem e apoio à avaliação.

Endpoints (JWT + tenant canônico via `routes._helpers`):
    GET  /api/psychiatry/triage/meta                    → disclaimer + versões
    GET  /api/psychiatry/triage/catalog                 → spec do instrumento
    GET  /api/psychiatry/triage/instrument              → banco de itens para UI/agente
    POST /api/psychiatry/triage/apply                   → aplica, pontua, persiste, narra
    GET  /api/psychiatry/triage/responses/<id>          → recupera resposta
    GET  /api/psychiatry/triage/responses               → lista por paciente
    GET  /api/psychiatry/triage/responses/<id>/explain  → explicabilidade
    GET  /api/psychiatry/triage/longitudinal            → série por domínio

Persistência reaproveita `neuro_scale_responses` via `ScaleResponseStore`.
"""

from __future__ import annotations

import logging
from typing import Any, Tuple

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from araos.specialties.neurodevelopmental.scales import (
    ScaleNotFoundError,
    ScaleRegistry,
    ScaleResponseStore,
)
from araos.specialties.psychiatry import explain, load_config, parse_config
from araos.specialties.psychiatry.application.triage_service import (
    INSTRUMENT_CODE,
    TriageError,
    apply_triage,
)

logger = logging.getLogger(__name__)

psychiatry_triage_bp = Blueprint(
    "psychiatry_triage", __name__, url_prefix="/api/psychiatry/triage"
)


def _resolve_tenant_id() -> str:
    from routes._helpers import _resolve_tenant_id as _canonical

    return _canonical()


def _get_actor_id():
    from routes._helpers import _get_actor_id as _canonical

    return _canonical()


def _get_db_session():
    from models import db

    return db.session


def _load_cfg(version: str):
    from araos.specialties.psychiatry import register_instrument

    register_instrument()
    spec = ScaleRegistry.get(INSTRUMENT_CODE, version=version)
    return spec, parse_config(load_config(spec.version))


@psychiatry_triage_bp.route("/meta", methods=["GET"])
@jwt_required()
def get_meta() -> Tuple[Any, int]:
    _, cfg = _load_cfg(request.args.get("version", "latest"))
    return (
        jsonify(
            {
                "code": cfg.code,
                "name": cfg.name,
                "model_version": cfg.version,
                "criteria_base": ["DSM-5-TR", "CID-11"],
                "criteria_version": cfg.criteria_version,
                "updated_at": cfg.updated_at,
                "disclaimer": cfg.disclaimer,
                "domains": [{"code": d.code, "label": d.label} for d in cfg.domains],
            }
        ),
        200,
    )


@psychiatry_triage_bp.route("/catalog", methods=["GET"])
@jwt_required()
def get_catalog() -> Tuple[Any, int]:
    from araos.specialties.psychiatry import register_instrument

    register_instrument()
    try:
        spec = ScaleRegistry.get(INSTRUMENT_CODE, version=request.args.get("version", "latest"))
    except ScaleNotFoundError as exc:
        return jsonify({"error": "instrument_not_found", "message": str(exc)}), 404
    return jsonify(spec.to_dict()), 200


@psychiatry_triage_bp.route("/instrument", methods=["GET"])
@jwt_required()
def get_instrument() -> Tuple[Any, int]:
    try:
        spec, cfg = _load_cfg(request.args.get("version", "latest"))
    except ScaleNotFoundError as exc:
        return jsonify({"error": "instrument_not_found", "message": str(exc)}), 404
    return (
        jsonify(
            {
                "code": cfg.code,
                "version": cfg.version,
                "criteria_version": cfg.criteria_version,
                "disclaimer": cfg.disclaimer,
                "domains": [{"code": d.code, "label": d.label} for d in cfg.domains],
                "items": [
                    {
                        "id": item.id,
                        "label": item.label,
                        "domains": list(item.domains),
                        "specificity": item.specificity,
                        "temporal_mode": item.temporal_mode,
                        "requires_context": list(item.requires_context),
                    }
                    for item in cfg.items
                ],
                "json_schema": spec.json_schema,
            }
        ),
        200,
    )


@psychiatry_triage_bp.route("/apply", methods=["POST"])
@jwt_required()
def apply_route() -> Tuple[Any, int]:
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400

    body = request.get_json(silent=True) or {}
    try:
        payload = apply_triage(
            _get_db_session(),
            tenant_id=tenant_id,
            patient_id=str(body.get("patient_id") or ""),
            raw_responses=body.get("raw_responses"),
            applied_by=_get_actor_id(),
            source=body.get("source", "ui"),
            status=body.get("status", "final"),
            version=body.get("version", "latest"),
            metadata=body.get("metadata") or {},
            generate_narrative=bool(body.get("narrative", True)),
            use_llm=bool(body.get("llm", False)),
        )
    except TriageError as exc:
        status_code = 404 if exc.code == "instrument_not_found" else 400
        return jsonify({"error": exc.code, "message": exc.message}), status_code
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao aplicar triagem psiquiátrica")
        return jsonify({"error": "persistence_error", "message": str(exc)}), 500
    return jsonify(payload), 201


@psychiatry_triage_bp.route("/responses/<string:response_id>", methods=["GET"])
@jwt_required()
def get_response(response_id: str) -> Tuple[Any, int]:
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400
    stored = ScaleResponseStore(_get_db_session()).get(response_id=response_id, tenant_id=tenant_id)
    if not stored:
        return jsonify({"error": "not_found"}), 404
    return jsonify(stored.to_dict()), 200


@psychiatry_triage_bp.route("/responses", methods=["GET"])
@jwt_required()
def list_responses() -> Tuple[Any, int]:
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id obrigatório"}), 400
    try:
        limit = int(request.args.get("limit", "100"))
    except ValueError:
        return jsonify({"error": "limit deve ser inteiro"}), 400
    rows = ScaleResponseStore(_get_db_session()).list_for_patient(
        tenant_id=tenant_id, patient_id=patient_id, scale_code=INSTRUMENT_CODE, limit=limit
    )
    return jsonify({"responses": [r.to_dict() for r in rows], "total": len(rows)}), 200


@psychiatry_triage_bp.route("/responses/<string:response_id>/explain", methods=["GET"])
@jwt_required()
def explain_response(response_id: str) -> Tuple[Any, int]:
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400
    stored = ScaleResponseStore(_get_db_session()).get(response_id=response_id, tenant_id=tenant_id)
    if not stored:
        return jsonify({"error": "not_found"}), 404
    cfg = parse_config(load_config(stored.scale_version))
    return (
        jsonify(
            {
                "response_id": stored.id,
                "explainability": explain(stored.raw_responses, cfg),
                "domain_scores": stored.computed_scores,
            }
        ),
        200,
    )


@psychiatry_triage_bp.route("/longitudinal", methods=["GET"])
@jwt_required()
def longitudinal() -> Tuple[Any, int]:
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id obrigatório"}), 400
    try:
        limit = int(request.args.get("limit", "100"))
    except ValueError:
        return jsonify({"error": "limit deve ser inteiro"}), 400
    rows = ScaleResponseStore(_get_db_session()).list_for_patient(
        tenant_id=tenant_id, patient_id=patient_id, scale_code=INSTRUMENT_CODE, limit=limit
    )
    series = []
    for row in reversed(rows):
        meta = (row.metadata or {}).get("psych_triage", {})
        risk = meta.get("risk", {})
        series.append(
            {
                "id": row.id,
                "applied_at": row.applied_at.isoformat() if row.applied_at else None,
                "domain_scores": row.computed_scores,
                "risk_level": risk.get("level"),
                "risk_score": risk.get("score"),
            }
        )
    return jsonify({"patient_id": patient_id, "series": series, "total": len(series)}), 200


def _dispatch(channel: str, contact: str, link: str, patient_id: str) -> Tuple[bool, str]:
    from services.psych_triage_invite_sender import dispatch

    return dispatch(channel, contact, link, patient_id)


@psychiatry_triage_bp.route("/invite", methods=["POST"])
@jwt_required()
def create_invite() -> Tuple[Any, int]:
    from services.psych_triage_invite_sender import InviteError, send_triage_invite

    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400

    body = request.get_json(silent=True) or {}
    try:
        result = send_triage_invite(
            _get_db_session(),
            tenant_id=tenant_id,
            patient_id=body.get("patient_id"),
            channel=str(body.get("channel", "link")),
            contact=body.get("contact"),
            version=body.get("version", "latest"),
            expires_hours=int(body.get("expires_hours", 72)),
        )
    except InviteError as exc:
        return jsonify({"error": exc.code, "message": exc.message}), 400

    return jsonify(result), 201
