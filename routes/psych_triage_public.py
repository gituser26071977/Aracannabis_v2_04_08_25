"""Routes públicas — Triagem psiquiátrica conduzida pelo paciente.

Fluxo agêntico: o agente conduz uma pergunta por vez, de forma acolhedora.
Não exige JWT (canal paciente-sozinho). O tenant e o paciente podem ser
informados no início; sem paciente identificado, usa um identificador anônimo
de sessão (status "draft") para vinculação posterior.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

from flask import Blueprint, jsonify, request

from araos.specialties.psychiatry import load_config, parse_config
from araos.specialties.psychiatry.application.triage_service import TriageError, apply_triage
from services.psych_triage_agent import PsychTriageAgent, build_agent
from services.psych_triage_session import get_state, new_session, set_state

logger = logging.getLogger(__name__)

psych_triage_public_bp = Blueprint(
    "psych_triage_public", __name__, url_prefix="/api/public/psych-triage"
)

_AGENTS: Dict[str, PsychTriageAgent] = {}
_LLM_ENABLED = os.getenv("PSYCH_TRIAGE_LLM", "false").lower() in ("1", "true", "yes")


def _agent(version: str) -> PsychTriageAgent:
    if version not in _AGENTS:
        spec_version = version
        if version == "latest":
            from araos.specialties.neurodevelopmental.scales import ScaleRegistry
            from araos.specialties.psychiatry import register_instrument

            register_instrument()
            spec_version = ScaleRegistry.get("PSYCH_TRIAGE").version
        _AGENTS[version] = build_agent(parse_config(load_config(spec_version)))
    return _AGENTS[version]


def _db_session():
    from models import db

    return db.session


def _polish(prompt: str) -> str:
    if not _LLM_ENABLED:
        return prompt
    try:
        from services.ai_agents import ai_manager

        result = ai_manager.chat_completion(
            prompt=prompt,
            system=(
                "Você é um entrevistador clínico acolhedor. Reescreva a pergunta mantendo exatamente "
                "o mesmo sentido e as mesmas opções, em no máximo 2 frases, com tom encorajador. "
                "Não peça dados pessoais e não faça diagnóstico."
            ),
        )
        return result or prompt
    except Exception as exc:  # noqa: BLE001
        logger.warning("psych_triage_public llm falhou: %s", exc)
        return prompt


def _question_payload(agent: PsychTriageAgent, answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    question = agent.next_question(answers)
    if question is None:
        return None
    return {
        "id": question.id,
        "prompt": _polish(question.prompt),
        "kind": question.kind,
        "choices": list(question.choices),
        "section": question.section,
    }


@psych_triage_public_bp.route("/start", methods=["POST"])
def start() -> Tuple[Any, int]:
    body = request.get_json(silent=True) or {}
    tenant_id = str(body.get("tenant_id") or "public")
    patient_id = body.get("patient_id")
    version = body.get("version", "latest")

    token = body.get("token")
    if token:
        from services.psych_triage_invite import verify_invite_token

        data = verify_invite_token(str(token))
        if data is None:
            return jsonify({"error": "invalid_or_expired_token"}), 401
        tenant_id = data["tenant_id"]
        patient_id = data.get("patient_id")
        version = data.get("version", version)

    agent = _agent(version)
    session_id = new_session(tenant_id, patient_id=str(patient_id) if patient_id else None, version=version)
    state = get_state(session_id)
    assert state is not None
    question = _question_payload(agent, state["answers"])
    set_state(session_id, state)
    return (
        jsonify(
            {
                "session_id": session_id,
                "greeting": agent.greeting(),
                "question": question,
                "disclaimer": agent.config.disclaimer,
                "progress": 0.0,
            }
        ),
        201,
    )


@psych_triage_public_bp.route("/<string:session_id>/answer", methods=["POST"])
def answer(session_id: str) -> Tuple[Any, int]:
    state = get_state(session_id)
    if state is None:
        return jsonify({"error": "session_not_found"}), 404
    if state.get("done"):
        return jsonify({"error": "already_done", "response_id": state.get("response_id")}), 409

    body = request.get_json(silent=True) or {}
    message = str(body.get("message") or "").strip()
    if not message:
        return jsonify({"error": "message obrigatória"}), 400

    agent = _agent(state.get("version", "latest"))
    answers = state["answers"]
    question = agent.next_question(answers)
    if question is None:
        return _finalize(session_id, state, agent)

    normalized = agent.normalize(question, message)
    if normalized is None:
        return (
            jsonify(
                {
                    "accepted": False,
                    "hint": "Não consegui entender. Pode tentar de outra forma, com suas palavras?",
                    "question": _question_payload(agent, answers),
                }
            ),
            200,
        )

    answers[question.id] = normalized
    state["history"].append({"question": question.id, "answer": normalized})
    set_state(session_id, state)

    next_question = _question_payload(agent, answers)
    if next_question is None:
        return _finalize(session_id, state, agent)

    return (
        jsonify(
            {
                "accepted": True,
                "question": next_question,
                "progress": agent.progress(answers),
            }
        ),
        200,
    )


@psych_triage_public_bp.route("/<string:session_id>", methods=["GET"])
def status(session_id: str) -> Tuple[Any, int]:
    state = get_state(session_id)
    if state is None:
        return jsonify({"error": "session_not_found"}), 404
    agent = _agent(state.get("version", "latest"))
    return (
        jsonify(
            {
                "session_id": session_id,
                "done": state.get("done", False),
                "response_id": state.get("response_id"),
                "progress": agent.progress(state["answers"]),
                "question": _question_payload(agent, state["answers"]) if not state.get("done") else None,
            }
        ),
        200,
    )


@psych_triage_public_bp.route("/webhook", methods=["POST"])
def whatsapp_webhook() -> Tuple[Any, int]:
    payload = request.get_json(silent=True) or {}
    tenant_id = str(request.args.get("tenant_id") or payload.get("tenant_id") or "public")
    provider = request.args.get("provider")
    try:
        from services.psych_triage_helpdesk import handle_inbound

        result = handle_inbound(payload, tenant_id, provider=provider)
    except Exception:  # noqa: BLE001
        logger.exception("Falha no webhook da triagem psiquiátrica")
        result = {"ok": False}
    return jsonify({"ok": True, "handled": bool(result.get("ok"))}), 200


def _finalize(session_id: str, state: Dict[str, Any], agent: PsychTriageAgent) -> Tuple[Any, int]:
    raw = agent.build_raw(state["answers"])
    patient_id = state.get("patient_id") or f"anon:{session_id}"
    try:
        payload = apply_triage(
            _db_session(),
            tenant_id=state.get("tenant_id") or "public",
            patient_id=patient_id,
            raw_responses=raw,
            applied_by=None,
            source="patient",
            status="final" if state.get("patient_id") else "draft",
            version=state.get("version", "latest"),
            metadata={"channel": "public", "session_id": session_id},
            generate_narrative=True,
            use_llm=_LLM_ENABLED,
        )
    except TriageError as exc:
        return jsonify({"error": exc.code, "message": exc.message}), 400
    except Exception as exc:  # noqa: BLE001
        logger.exception("Falha ao finalizar triagem pública")
        return jsonify({"error": "persistence_error", "message": str(exc)}), 500

    state["done"] = True
    state["response_id"] = payload["id"]
    set_state(session_id, state)

    risk = payload.get("risk", {})
    closing = (
        "Muito obrigado por responder com sinceridade. Suas respostas foram registradas e "
        "serão revisadas por um profissional."
    )
    if risk.get("emergency"):
        closing = (
            "Percebemos sinais que pedem cuidado imediato. Por favor, procure agora um serviço de "
            "emergência ou ligue 188 (CVV). Você não está sozinho."
        )
    return (
        jsonify(
            {
                "done": True,
                "response_id": payload["id"],
                "closing": closing,
                "domain_scores": payload["domain_scores"],
                "risk": risk,
                "emergency": risk.get("emergency", False),
                "narrative": payload.get("narrative", ""),
                "disclaimer": payload.get("disclaimer", ""),
            }
        ),
        201,
    )
