"""
Clinical Context API — Sprint 4.2 / ADR-0003.

Blueprint: `clinical_context` (prefix /api/intelligence).

Endpoints (18):
    # ── CRUD ─────────────────────────────────────────────────────
    POST   /contexts                                  → cria (manual ou from-suggestion)
    GET    /contexts/{id}                             → recupera
    GET    /patients/{patient_id}/contexts            → lista contextos do paciente
    PATCH  /contexts/{id}                             → atualiza metadados
    DELETE /contexts/{id}                             → exclui (soft? hard? — hard, mas audit)

    # ── State Transitions ────────────────────────────────────────
    POST   /contexts/{id}/activate                    → planned/suggested → active
    POST   /contexts/{id}/close                       → active → completed/cancelled/archived
    POST   /contexts/{id}/reopen                      → completed → active
    POST   /contexts/{id}/reject                      → suggested → rejected
    POST   /contexts/{id}/confirm                     → suggested → active (+ optional type override)

    # ── Suggestions (Rule Engine + Explainability) ──────────────
    POST   /patients/{patient_id}/contexts/suggest    → executa Rule Engine + emite Suggestions
    GET    /patients/{patient_id}/contexts/suggested  → lista SUGGESTED para confirmação
    POST   /contexts/suggestions/{suggestion_id}/confirm → confirma → ativa ClinicalContext

    # ── Relationships ───────────────────────────────────────────
    POST   /contexts/{id}/relationships              → cria edge
    GET    /contexts/{id}/relationships              → lista vizinhos
    DELETE /contexts/{id}/relationships/{rel_id}     → remove edge
    GET    /contexts/{id}/neighbors?depth=2          → grafo BFS

    # ── Queries ──────────────────────────────────────────────────
    GET    /patients/{patient_id}/contexts/active-at?at=ISO   → active_at()
    GET    /patients/{patient_id}/contexts/co-occurred?date_a=&date_b= → co_occurred()

Padrão de auth: `@jwt_required()` + tenant via header.
Resposta HTTP 202 Accepted para writes (Event Sourcing semantics).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from araos.clinical.context.application import (
    ClinicalContextService,
    ClinicalContextQuery,
    ContextSuggester,
    InMemoryClinicalContextQuery,
    RuleEngine,
    default_rules,
)
from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_relationship import RelationshipType
from araos.clinical.context.domain.context_status import ContextStatus
from araos.clinical.context.domain.context_type import ContextType
from araos.clinical.context.sql import (
    SqlAlchemyClinicalContextQuery,
    REDACTED,
    REDACTED,
)
from araos.clinical.event_store import ClinicalEventPublisher
from routes._helpers import _get_actor_id, _resolve_tenant_id, get_logger


clinical_context_bp = Blueprint(
    "clinical_context", __name__, url_prefix="/api/intelligence",
)
_logger = get_logger("intelligence.context")


# ─── Service/Repository accessors ────────────────────────────────────


def _session_factory():
    """Resolve SQLAlchemy session factory from app config.

    Ordem:
        1. REDACTED (injetada no app factory)
        2. None → retorna None (modo in-memory).
    """
    return current_app.config.get("REDACTED")


def _publisher() -> Optional[ClinicalEventPublisher]:
    pub: Optional[ClinicalEventPublisher] = current_app.config.get(
        "INTELLIGENCE_CONTEXT_PUBLISHER",
    )
    return pub


def _repo() -> REDACTED:
    sf = _session_factory()
    if sf is None:
        raise RuntimeError(
            "REDACTED not configured. "
            "In-memory mode requires explicit setup; production requires DB."
        )
    return REDACTED(sf)


def _rel_repo() -> REDACTED:
    sf = _session_factory()
    if sf is None:
        raise RuntimeError(
            "REDACTED not configured"
        )
    return REDACTED(sf)


def _query() -> ClinicalContextQuery:
    sf = _session_factory()
    if sf is None:
        # Fallback in-memory for tests/dev sem SQL — usa cache local.
        if "INTELLIGENCE_CONTEXT_INMEM_QUERY" not in current_app.config:
            current_app.config["INTELLIGENCE_CONTEXT_INMEM_QUERY"] = (
                InMemoryClinicalContextQuery()
            )
        return current_app.config["INTELLIGENCE_CONTEXT_INMEM_QUERY"]
    return SqlAlchemyClinicalContextQuery(sf)


def _service() -> ClinicalContextService:
    return ClinicalContextService(event_publisher=_publisher())


def _suggester() -> ContextSuggester:
    sf = _session_factory()
    if "INTELLIGENCE_CONTEXT_SUGGESTER" not in current_app.config:
        from araos.clinical.explainability.registry import (
            InMemoryExplanationRegistry,
        )
        # If a SQL-backed registry is configured, prefer it; else InMemory.
        try:
            from araos.clinical.explainability.registry import (
                SqlAlchemyExplanationRegistry,
            )
            registry = (
                SqlAlchemyExplanationRegistry(sf)
                if sf is not None
                else InMemoryExplanationRegistry()
            )
        except ImportError:
            registry = InMemoryExplanationRegistry()
        engine = RuleEngine(rules=default_rules())
        current_app.config["INTELLIGENCE_CONTEXT_SUGGESTER"] = ContextSuggester(
            rule_engine=engine,
            explanation_registry=registry,
            event_publisher=_publisher(),
        )
    return current_app.config["INTELLIGENCE_CONTEXT_SUGGESTER"]


# ─── Helpers ─────────────────────────────────────────────────────────


def _isoformat(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    if isinstance(s, datetime):
        return s if s.tzinfo else s.replace(tzinfo=timezone.utc)
    raw = s.replace("Z", "+00:00") if s.endswith("Z") else s
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _require_tenant_and_actor() -> Tuple[Optional[str], Optional[str], Optional[Any]]:
    tenant_id = _resolve_tenant_id()
    actor_id = _get_actor_id()
    if not tenant_id:
        return None, None, (jsonify({"error": "tenant_id required"}), 401)
    if not actor_id:
        return None, None, (jsonify({"error": "unauthorized"}), 401)
    return tenant_id, actor_id, None


# ─── CRUD ──────────────────────────────────────────────────────────────


@clinical_context_bp.route("/contexts", methods=["POST"])
@jwt_required()
def create_context():
    """Cria novo ClinicalContext."""
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    try:
        ctx_type = ContextType(body["context_type"])
    except (KeyError, ValueError) as e:
        return jsonify({"error": f"invalid context_type: {e}"}), 400

    start_dt = _parse_dt(body.get("start_date"))
    if not start_dt:
        return jsonify({"error": "start_date (ISO 8601) is required"}), 400

    origin_raw = body.get("origin", "manual")
    try:
        origin = ContextOrigin(origin_raw)
    except ValueError as e:
        return jsonify({"error": f"invalid origin: {e}"}), 400

    title = body.get("title")
    if not title:
        return jsonify({"error": "title is required"}), 400

    end_dt = _parse_dt(body.get("end_date"))
    confidence = float(body.get("confidence_score", 1.0))
    patient_id = body.get("patient_id")
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400

    from araos.clinical.context.application.context_service import (
        CreateContextCommand,
    )

    cmd = CreateContextCommand(
        tenant_id=tenant_id,
        patient_id=patient_id,
        context_type=ctx_type,
        title=title,
        start_date=start_dt,
        created_by=actor_id,
        description=body.get("description", ""),
        reason=body.get("reason", ""),
        observations=body.get("observations") or [],
        end_date=end_dt,
        origin=origin,
        confidence_score=confidence,
        source_event_ids=body.get("source_event_ids") or [],
        professionals=body.get("professionals") or [],
        suggestion_id=body.get("suggestion_id"),
        explanation_id=body.get("explanation_id"),
    )
    svc = _service()
    try:
        ctx = svc.create(cmd)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Persist se SQL disponível
    sf = _session_factory()
    if sf is not None:
        try:
            _repo().upsert(ctx)
        except Exception as exc:    # pragma: no cover
            _logger.exception("context_persist_failed")
            return jsonify({"error": f"persist_failed: {exc}"}), 500

    return jsonify(ctx.to_dict()), 201


@clinical_context_bp.route("/contexts/<context_id>", methods=["GET"])
@jwt_required()
def get_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    ctx = _repo().get(tenant_id, context_id)
    if ctx is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(ctx.to_dict()), 200


@clinical_context_bp.route("/patients/<patient_id>/contexts", methods=["GET"])
@jwt_required()
def list_contexts_for_patient(patient_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    status = request.args.get("status")
    ctx_type = request.args.get("context_type")
    status_enum = ContextStatus(status) if status else None
    type_enum = ContextType(ctx_type) if ctx_type else None

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    items = _repo().list_for_patient(
        tenant_id, patient_id,
        status=status_enum, context_type=type_enum,
    )
    return jsonify({
        "patient_id": patient_id,
        "tenant_id": tenant_id,
        "items": [c.to_dict() for c in items],
        "count": len(items),
    }), 200


@clinical_context_bp.route("/contexts/<context_id>", methods=["PATCH"])
@jwt_required()
def update_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    repo = _repo()
    existing = repo.get(tenant_id, context_id)
    if existing is None:
        return jsonify({"error": "not_found"}), 404

    svc = _service()
    try:
        new_ctx = svc.update(existing, actor_id, body)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    repo.upsert(new_ctx)
    return jsonify(new_ctx.to_dict()), 200


@clinical_context_bp.route("/contexts/<context_id>", methods=["DELETE"])
@jwt_required()
def delete_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    deleted = _repo().delete(tenant_id, context_id)
    if not deleted:
        return jsonify({"error": "not_found"}), 404
    return "", 204


# ─── State Transitions ────────────────────────────────────────────────


@clinical_context_bp.route("/contexts/<context_id>/activate", methods=["POST"])
@jwt_required()
def activate_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    repo = _repo()
    existing = repo.get(tenant_id, context_id)
    if existing is None:
        return jsonify({"error": "not_found"}), 404
    svc = _service()
    try:
        new_ctx = svc.activate(existing, actor_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    repo.upsert(new_ctx)
    return jsonify(new_ctx.to_dict()), 200


@clinical_context_bp.route("/contexts/<context_id>/close", methods=["POST"])
@jwt_required()
def close_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    status_raw = body.get("new_status", "completed")
    try:
        new_status = ContextStatus(status_raw)
    except ValueError as e:
        return jsonify({"error": f"invalid new_status: {e}"}), 400

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    repo = _repo()
    existing = repo.get(tenant_id, context_id)
    if existing is None:
        return jsonify({"error": "not_found"}), 404
    svc = _service()
    try:
        new_ctx = svc.close(
            existing, actor_id, new_status,
            end_date=_parse_dt(body.get("end_date")),
            summary=body.get("summary"),
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    repo.upsert(new_ctx)
    return jsonify(new_ctx.to_dict()), 200


@clinical_context_bp.route("/contexts/<context_id>/reopen", methods=["POST"])
@jwt_required()
def reopen_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    repo = _repo()
    existing = repo.get(tenant_id, context_id)
    if existing is None:
        return jsonify({"error": "not_found"}), 404
    svc = _service()
    try:
        new_ctx = svc.reopen(existing, actor_id, reason=body.get("reason", ""))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    repo.upsert(new_ctx)
    return jsonify(new_ctx.to_dict()), 200


@clinical_context_bp.route("/contexts/<context_id>/reject", methods=["POST"])
@jwt_required()
def reject_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    reason = body.get("reason", "")
    if not reason:
        return jsonify({"error": "reason is required"}), 400

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    repo = _repo()
    existing = repo.get(tenant_id, context_id)
    if existing is None:
        return jsonify({"error": "not_found"}), 404
    svc = _service()
    try:
        new_ctx = svc.reject(existing, actor_id, reason)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    repo.upsert(new_ctx)
    return jsonify(new_ctx.to_dict()), 200


@clinical_context_bp.route("/contexts/<context_id>/confirm", methods=["POST"])
@jwt_required()
def confirm_context(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    confirmed_type_raw = body.get("confirmed_type")
    confirmed_type = ContextType(confirmed_type_raw) if confirmed_type_raw else None

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    repo = _repo()
    existing = repo.get(tenant_id, context_id)
    if existing is None:
        return jsonify({"error": "not_found"}), 404
    svc = _service()
    try:
        new_ctx = svc.confirm_suggestion(existing, actor_id, confirmed_type)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    repo.upsert(new_ctx)
    return jsonify(new_ctx.to_dict()), 200


# ─── Suggestions ──────────────────────────────────────────────────────


@clinical_context_bp.route("/patients/<patient_id>/contexts/suggest", methods=["POST"])
@jwt_required()
def suggest_contexts(patient_id: str):
    """Executa Rule Engine + ExplanationRegistry + emite CLINICAL_CONTEXT_SUGGESTED."""
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    events = body.get("events") or []

    sf = _session_factory()
    existing_contexts: List = []
    if sf is not None:
        existing_contexts = _repo().list_for_patient(tenant_id, patient_id)

    suggester = _suggester()
    suggestions = suggester.suggest(
        tenant_id=tenant_id,
        patient_id=patient_id,
        events=events,
        existing_contexts=existing_contexts,
        analyst=actor_id or "system",
    )

    return jsonify({
        "patient_id": patient_id,
        "tenant_id": tenant_id,
        "suggestions": [s.to_dict() for s in suggestions],
        "count": len(suggestions),
        "rules_evaluated": len(suggester._rule_engine.rules),
    }), 200


@clinical_context_bp.route("/patients/<patient_id>/contexts/suggested", methods=["GET"])
@jwt_required()
def list_suggested_for_patient(patient_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    items = _repo().list_suggested_for_confirmation(tenant_id, patient_id)
    return jsonify({
        "patient_id": patient_id,
        "tenant_id": tenant_id,
        "items": [c.to_dict() for c in items],
        "count": len(items),
    }), 200


# ─── Relationships ────────────────────────────────────────────────────


@clinical_context_bp.route("/contexts/<context_id>/relationships", methods=["POST"])
@jwt_required()
def create_relationship(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    body = request.get_json(force=True, silent=True) or {}
    target_id = body.get("target_context_id")
    if not target_id:
        return jsonify({"error": "target_context_id is required"}), 400
    try:
        rel_type = RelationshipType(body.get("relationship_type", "related_to"))
    except ValueError as e:
        return jsonify({"error": f"invalid relationship_type: {e}"}), 400

    svc = _service()
    # Look up source context to get patient_id (needed for event publish).
    src = _repo().get(tenant_id, context_id)
    patient_id = src.patient_id if src is not None else ""
    rel = svc.link(
        tenant_id=tenant_id,
        source_context_id=context_id,
        target_context_id=target_id,
        relationship_type=rel_type,
        created_by=actor_id,
        confidence=float(body.get("confidence", 1.0)),
        evidence_event_ids=body.get("evidence_event_ids") or [],
        patient_id=patient_id,
    )

    sf = _session_factory()
    if sf is not None:
        try:
            _rel_repo().upsert(rel)
        except Exception as exc:    # pragma: no cover
            _logger.exception("relationship_persist_failed")
            return jsonify({"error": f"persist_failed: {exc}"}), 500

    return jsonify({
        "relationship_id": rel.relationship_id,
        "source_context_id": rel.source_context_id,
        "target_context_id": rel.target_context_id,
        "relationship_type": rel.relationship_type.value,
        "confidence": rel.confidence,
        "created_at": _isoformat(rel.created_at),
    }), 201


@clinical_context_bp.route("/contexts/<context_id>/relationships", methods=["GET"])
@jwt_required()
def list_relationships(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    rels = _rel_repo().list_for_context(tenant_id, context_id)
    return jsonify({
        "context_id": context_id,
        "tenant_id": tenant_id,
        "items": [{
            "relationship_id": r.relationship_id,
            "source_context_id": r.source_context_id,
            "target_context_id": r.target_context_id,
            "relationship_type": r.relationship_type.value,
            "confidence": r.confidence,
            "created_at": _isoformat(r.created_at),
        } for r in rels],
        "count": len(rels),
    }), 200


@clinical_context_bp.route(
    "/contexts/<context_id>/relationships/<rel_id>", methods=["DELETE"]
)
@jwt_required()
def delete_relationship(context_id: str, rel_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    repo = _rel_repo()
    rel = repo.get(tenant_id, rel_id)
    if rel is None:
        return jsonify({"error": "not_found"}), 404
    svc = _service()
    # Look up source context to get patient_id for event publish.
    src = _repo().get(tenant_id, rel.source_context_id)
    patient_id = src.patient_id if src is not None else ""
    svc.unlink(rel, actor_id, patient_id=patient_id)
    repo.delete(tenant_id, rel_id)
    return "", 204


@clinical_context_bp.route("/contexts/<context_id>/neighbors", methods=["GET"])
@jwt_required()
def get_neighbors(context_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    depth = int(request.args.get("depth", 1))
    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    from araos.clinical.context.projections import (
        RelationshipProjection,
    )
    proj = RelationshipProjection(_session_factory())
    items = proj.neighbors(tenant_id, context_id, depth=depth)
    return jsonify({
        "context_id": context_id,
        "depth": depth,
        "neighbors": items,
        "count": len(items),
    }), 200


# ─── Queries ──────────────────────────────────────────────────────────


@clinical_context_bp.route(
    "/patients/<patient_id>/contexts/active-at", methods=["GET"]
)
@jwt_required()
def contexts_active_at(patient_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    at_dt = _parse_dt(request.args.get("at"))
    if not at_dt:
        return jsonify({"error": "at (ISO 8601) is required"}), 400

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    items = _query().active_at(tenant_id, patient_id, at_dt)
    return jsonify({
        "patient_id": patient_id,
        "tenant_id": tenant_id,
        "at": _isoformat(at_dt),
        "items": [c.to_dict() for c in items],
        "count": len(items),
    }), 200


@clinical_context_bp.route(
    "/patients/<patient_id>/contexts/co-occurred", methods=["GET"]
)
@jwt_required()
def contexts_co_occurred(patient_id: str):
    tenant_id, actor_id, err = _require_tenant_and_actor()
    if err:
        return err

    date_a = _parse_dt(request.args.get("date_a"))
    date_b = _parse_dt(request.args.get("date_b"))
    if not (date_a and date_b):
        return jsonify({"error": "date_a and date_b (ISO 8601) are required"}), 400

    sf = _session_factory()
    if sf is None:
        return jsonify({"error": "no backing store configured"}), 503

    pairs = _query().co_occurred(tenant_id, patient_id, date_a, date_b)
    return jsonify({
        "patient_id": patient_id,
        "tenant_id": tenant_id,
        "pairs": [
            {"context_a": a.to_dict(), "context_b": b.to_dict()}
            for a, b in pairs
        ],
        "count": len(pairs),
    }), 200
