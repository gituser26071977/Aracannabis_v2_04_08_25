"""
Routes — Módulo NEURODESENVOLVIMENTO — Escalas Neuropsicológicas (Sprint 1).

Endpoints REST para o subsistema plugin-based de escalas.

Endpoints:
    GET  /api/neuro/scales/catalog          → Lista todas as escalas disponíveis
    GET  /api/neuro/scales/<code>           → Spec de uma escala (JSON Schema)
    POST /api/neuro/scales/<code>/apply     → Aplica escala (valida, calcula, persiste)
    GET  /api/neuro/scales/responses/<id>   → Recupera resposta gravada
    GET  /api/neuro/scales/responses        → Lista respostas (filtro: patient_id, scale_code)

Padrão de autenticação: `@jwt_required()` (Flask-JWT-Extended).
Multi-tenancy: header `X-Association-ID` → `tenant_id` via
`araos.platform.tenant.resolver.TenantContextResolver`.

Sprint 1 inclui:
    - Registry-based catalog (zero hardcode de escalas na rota)
    - Validação JSON Schema por `ScaleRunner`
    - Cálculo + interpretação determinística
    - Persistência via `ScaleResponseStore`
    - Emissão de evento `NEURODEVELOPMENTAL_SCALE_APPLIED` no event bus
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from araos.specialties.neurodevelopmental import (
    ScaleNotFoundError,
    ScaleRegistry,
    ScaleResponseStore,
    ScaleRunner,
    ScaleSpec,
    ScaleValidationError,
)

logger = logging.getLogger(__name__)

neuro_scales_bp = Blueprint("neuro_scales", __name__, url_prefix="/api/neuro/scales")


# ─── Helpers ─────────────────────────────────────────────────────────


def _resolve_tenant_id() -> str:
    """
    Re-export do helper canônico (P0-12): tenant só do JWT / g.current_association,
    NUNCA de `X-Association-ID`/`X-Tenant-ID` (vetor de spoof cross-tenant).
    """
    from routes._helpers import _resolve_tenant_id as _canonical

    return _canonical()


def _get_actor_id() -> Optional[str]:
    """Identifica o ator (profissional / user) que aplicou a escala."""
    try:
        identity = get_jwt_identity()
        if isinstance(identity, dict):
            return str(identity.get("user_id") or identity.get("id") or "")
        return str(identity) if identity else None
    except Exception:  # noqa: BLE001
        return None


def _get_db_session():
    """Acessa a Session SQLAlchemy do app Flask."""
    from models import db

    return db.session


def _publish_scale_applied_event(
    tenant_id: str,
    patient_id: str,
    scale_code: str,
    response_id: str,
    actor_id: Optional[str],
) -> None:
    """
    Publica evento `NEURODEVELOPMENTAL_SCALE_APPLIED` no event bus.

    Falhas de publicação NÃO devem bloquear a resposta HTTP — escala
    já está persistida. Log + métricas ficam para observabilidade.
    """
    try:
        from araos.platform.event_bus.bus import AraOSEventBus
        from araos.platform.event_bus.envelope import (
            EventCategory,
            EventEnvelopeV2,
            EventPriority,
        )

        event = EventEnvelopeV2(
            event_type="NEURODEVELOPMENTAL_SCALE_APPLIED",
            tenant_id=tenant_id,
            payload={
                "patient_id": patient_id,
                "scale_code": scale_code,
                "response_id": response_id,
            },
            event_category=EventCategory.CLINICAL,
            priority=EventPriority.NORMAL,
            actor_id=actor_id,
        )
        AraOSEventBus.publish(event)
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Falha ao publicar evento NEURODEVELOPMENTAL_SCALE_APPLIED: %s", e
        )

    # F2/F5 — wrap: emite o ClinicalEvent canônico para o AraOS (event store)
    # alimentando o Observatório (SCALE_APPLIED → observatory_etl).
    # Never-throw: falha de integração não bloqueia a aplicação da escala.
    try:
        from services.araos_event_emitter import default_emitter

        default_emitter().emit(
            event_type="SCALE_APPLIED",
            patient_id=patient_id,
            tenant_id=tenant_id,
            source_id=response_id,
            payload={
                "scale_code": scale_code,
                "scale_version": "latest",
                "response_id": response_id,
            },
            metadata={"actor_id": actor_id},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Falha ao emitir SCALE_APPLIED para o AraOS: %s", e)


# ─── Endpoints ───────────────────────────────────────────────────────


@neuro_scales_bp.route("/catalog", methods=["GET"])
@jwt_required()
def list_catalog() -> Tuple[Any, int]:
    """
    Lista todas as escalas disponíveis no registry.

    Query params:
        age_months (int, optional): filtra por idade aplicável.

    Returns:
        {
          "scales": [
            {
              "code", "name", "version", "author", "scientific_reference",
              "target_age_months", "administration_time_min",
              "subscales", "is_public", "requires_training", "languages"
            },
            ...
          ],
          "total": int
        }
    """
    age_months_raw = request.args.get("age_months")
    age_months: Optional[int] = None
    if age_months_raw:
        try:
            age_months = int(age_months_raw)
        except ValueError:
            return jsonify({"error": "age_months deve ser inteiro"}), 400

    specs = (
        ScaleRegistry.list_by_age(age_months)
        if age_months is not None
        else ScaleRegistry.list()
    )
    return (
        jsonify({"scales": [s.to_dict() for s in specs], "total": len(specs)}),
        200,
    )


@neuro_scales_bp.route("/<string:code>", methods=["GET"])
@jwt_required()
def get_scale_spec(code: str) -> Tuple[Any, int]:
    """
    Retorna spec completo de uma escala (incluindo JSON Schema).

    Path:
        code: código da escala (ex: GAD7, PHQ9)
    """
    version = request.args.get("version", "latest")
    try:
        spec: ScaleSpec = ScaleRegistry.get(code, version=version)
    except ScaleNotFoundError as e:
        return jsonify({"error": "scale_not_found", "message": str(e)}), 404

    payload = spec.to_dict()
    payload["json_schema"] = spec.json_schema  # redundante mas explícito
    return jsonify(payload), 200


@neuro_scales_bp.route("/<string:code>/apply", methods=["POST"])
@jwt_required()
def apply_scale(code: str) -> Tuple[Any, int]:
    """
    Aplica uma escala a um paciente.

    Body JSON:
        {
          "patient_id": "uuid-do-paciente",
          "raw_responses": {"q1": 2, "q2": 3, ...},
          "metadata": { ... },         # opcional
          "source": "ui" | "ai" | ... # opcional, default "ui"
          "status": "draft" | "final" # opcional, default "final"
          "version": "1.0"            # opcional, default "latest"
        }

    Returns:
        {
          "id": "uuid-da-resposta",
          "scale_code", "scale_version",
          "computed_scores": {...},
          "interpretation": {...},
          "applied_at", "status",
          "metadata"
        }
    """
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return (
            jsonify(
                {
                    "error": "tenant_required",
                    "message": "X-Association-ID header obrigatório",
                }
            ),
            400,
        )

    body = request.get_json(silent=True) or {}
    patient_id = body.get("patient_id")
    raw_responses = body.get("raw_responses")
    metadata = body.get("metadata") or {}
    source = body.get("source", "ui")
    status = body.get("status", "final")
    version = body.get("version", "latest")

    if not patient_id:
        return jsonify({"error": "patient_id obrigatório"}), 400
    if not isinstance(raw_responses, dict):
        return jsonify({"error": "raw_responses deve ser objeto"}), 400

    try:
        spec = ScaleRegistry.get(code, version=version)
    except ScaleNotFoundError as e:
        return jsonify({"error": "scale_not_found", "message": str(e)}), 404

    # Calcula + valida ANTES de persistir (fail-fast)
    runner = ScaleRunner(spec)
    try:
        result = runner.run(raw_responses, metadata=metadata, validate=True)
    except ScaleValidationError as e:
        return (
            jsonify({"error": "validation_error", "message": str(e)}),
            400,
        )
    except ValueError as e:
        return jsonify({"error": "scoring_error", "message": str(e)}), 400

    # Persiste
    db_session = _get_db_session()
    store = ScaleResponseStore(db_session)
    actor_id = _get_actor_id()
    try:
        stored = store.save(
            tenant_id=tenant_id,
            patient_id=str(patient_id),
            scale_code=code,
            raw_responses=raw_responses,
            applied_by=actor_id,
            source=source,
            status=status,
            metadata=metadata,
            validate=False,  # já validado acima
            scale_version=spec.version,
        )
    except Exception as e:  # noqa: BLE001
        logger.exception("Falha ao persistir resposta de escala")
        return jsonify({"error": "persistence_error", "message": str(e)}), 500

    # Publica evento (best-effort)
    _publish_scale_applied_event(
        tenant_id=tenant_id,
        patient_id=str(patient_id),
        scale_code=code,
        response_id=stored.id,
        actor_id=actor_id,
    )

    payload = stored.to_dict()
    payload["scores"] = result.scores
    return jsonify(payload), 201


@neuro_scales_bp.route("/responses/<string:response_id>", methods=["GET"])
@jwt_required()
def get_response(response_id: str) -> Tuple[Any, int]:
    """Recupera resposta de escala por id (tenant-scoped)."""
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400

    db_session = _get_db_session()
    store = ScaleResponseStore(db_session)
    stored = store.get(response_id=response_id, tenant_id=tenant_id)
    if not stored:
        return jsonify({"error": "not_found"}), 404
    return jsonify(stored.to_dict()), 200


@neuro_scales_bp.route("/responses", methods=["GET"])
@jwt_required()
def list_responses() -> Tuple[Any, int]:
    """
    Lista respostas de escalas de um paciente.

    Query params:
        patient_id (str, required)
        scale_code (str, optional)
        limit (int, optional, default 100)
    """
    tenant_id = _resolve_tenant_id()
    if not tenant_id:
        return jsonify({"error": "tenant_required"}), 400

    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id obrigatório"}), 400

    scale_code = request.args.get("scale_code")
    try:
        limit = int(request.args.get("limit", "100"))
    except ValueError:
        return jsonify({"error": "limit deve ser inteiro"}), 400

    db_session = _get_db_session()
    store = ScaleResponseStore(db_session)
    rows = store.list_for_patient(
        tenant_id=tenant_id,
        patient_id=patient_id,
        scale_code=scale_code,
        limit=limit,
    )
    return (
        jsonify({"responses": [r.to_dict() for r in rows], "total": len(rows)}),
        200,
    )