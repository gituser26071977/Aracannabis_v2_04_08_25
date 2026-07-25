"""
Explainability API — Sprint 4.1.

Blueprint: `explainability` (prefix /api/intelligence).

Endpoints:
    GET /explanations/{id}                  → recupera 1 explanation
    GET /explanations?analysis_id=...       → lista explicações por análise
    GET /explanations?event_id=...          → lista explicações por evento
    GET /explanations?analysis_type=...     → lista por tipo

Toda Explanation registrada no Explainability Registry é consultável
por aqui. Auditoria clínica precisa dessa transparência.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from araos.clinical.explainability import (
    AnalysisType,
    InMemoryExplanationRegistry,
)
from araos.clinical.explainability.registry import ExplanationRegistry
from routes._helpers import (
    _get_actor_id,
    _resolve_tenant_id,
    get_logger,
)


explainability_bp = Blueprint(
    "explainability", __name__, url_prefix="/api/intelligence",
)
_logger = get_logger("intelligence.explainability")


# ─── Service accessor ─────────────────────────────────────────────────


def _registry() -> ExplanationRegistry:
    """Resolve ExplanationRegistry a partir do app context.

    Default: InMemoryExplanationRegistry (para dev/testes sem DB).
    Em produção, deve ser SqlAlchemyExplanationRegistry (configurado
    em app factory via current_app.config["INTELLIGENCE_EXPLANATION_REGISTRY"]).
    """
    reg: Optional[ExplanationRegistry] = current_app.config.get(
        "INTELLIGENCE_EXPLANATION_REGISTRY",
    )
    if reg is None:
        reg = InMemoryExplanationRegistry()
        current_app.config["INTELLIGENCE_EXPLANATION_REGISTRY"] = reg
    return reg


# ─── Endpoints ────────────────────────────────────────────────────────


@explainability_bp.route("/explanations/<explanation_id>", methods=["GET"])
@jwt_required()
def get_explanation(explanation_id: str):
    """Recupera uma Explanation específica."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 401
    if not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    reg = _registry()
    explanation = reg.get(explanation_id)
    if explanation is None:
        return jsonify({"error": "not_found"}), 404
    # Tenant isolation: explanation do tenant errado não pode ser vista
    if explanation.tenant_id and explanation.tenant_id != tenant_id:
        return jsonify({"error": "not_found"}), 404
    return jsonify(explanation.to_dict()), 200


@explainability_bp.route("/explanations", methods=["GET"])
@jwt_required()
def list_explanations():
    """Lista explicações com filtros (analysis_id / event_id / analysis_type)."""
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 401
    if not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    analysis_id = request.args.get("analysis_id")
    event_id = request.args.get("event_id")
    type_param = request.args.get("analysis_type")
    limit = int(request.args.get("limit", "100"))
    limit = min(max(limit, 1), 500)

    reg = _registry()
    explanations = []

    if analysis_id:
        explanations = reg.list_for_analysis(tenant_id, analysis_id)
    elif event_id:
        explanations = reg.list_for_event(tenant_id, event_id)
    elif type_param:
        try:
            analysis_type = AnalysisType(type_param)
        except ValueError:
            return jsonify({
                "error": f"invalid analysis_type: {type_param}",
                "valid_types": [t.value for t in AnalysisType],
            }), 400
        explanations = reg.list_for_type(
            tenant_id, analysis_type, limit=limit,
        )
    else:
        # sem filtro — retorna contagem apenas (sem dump)
        return jsonify({
            "tenant_id": tenant_id,
            "count": reg.count(tenant_id),
            "hint": "use ?analysis_id=, ?event_id= or ?analysis_type= for details",
        }), 200

    return jsonify({
        "tenant_id": tenant_id,
        "count": len(explanations),
        "explanations": [e.to_dict() for e in explanations[:limit]],
    }), 200


@explainability_bp.route("/explanations/<explanation_id>/verify", methods=["GET"])
@jwt_required()
def verify_explanation(explanation_id: str):
    """Verifica invariantes da Explanation (debug + auditoria).

    Retorna 200 se válida, 422 com motivos se inválida.
    """
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 401
    if not actor_id:
        return jsonify({"error": "unauthorized"}), 401

    reg = _registry()
    explanation = reg.get(explanation_id)
    if explanation is None:
        return jsonify({"error": "not_found"}), 404
    if explanation.tenant_id and explanation.tenant_id != tenant_id:
        return jsonify({"error": "not_found"}), 404

    violations: list = []
    if not 0.0 <= explanation.confidence <= 1.0:
        violations.append(f"confidence={explanation.confidence} out of [0,1]")
    if not explanation.variables:
        violations.append("variables is empty")
    if not explanation.limitations:
        violations.append("limitations is empty (mandatory)")
    if not explanation.contributing_event_ids and not any(
        "data" in l.lower() or "events" in l.lower() for l in explanation.limitations
    ):
        violations.append("contributing_event_ids empty + no data scarcity limitation")
    if not explanation.method:
        violations.append("method is empty")

    return jsonify({
        "explanation_id": explanation_id,
        "valid": len(violations) == 0,
        "violations": violations,
    }), 200 if not violations else 422