"""
AAP — Arapath Agent Protocol
Endpoints Flask para o protocolo AAP no SIAP.
"""

import os
import json
import uuid
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify, Response, current_app

from services.aap_protocol import (
    AAPClient,
    verify_aap_request,
    build_agent_card,
    AAP_API_KEY,
)
from services.aap_registry import get_registry

aap_bp = Blueprint("aap", __name__)

# ── Task Manager (thread-safe, fallback memória) ──
_task_lock = threading.Lock()
_tasks: Dict[str, Dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _create_task(task_id: str, capability_id: str, method: str, params: dict,
                 callback_url: Optional[str] = None) -> Dict[str, Any]:
    task = {
        "task_id": task_id,
        "capability_id": capability_id,
        "method": method,
        "params": params,
        "status": "submitted",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "result": None,
        "error": None,
        "callback_url": callback_url,
        "events": [],
    }
    with _task_lock:
        _tasks[task_id] = task
    return task


def _update_task(task_id: str, status: str, result: Any = None, error: str = None):
    with _task_lock:
        if task_id in _tasks:
            _tasks[task_id]["status"] = status
            _tasks[task_id]["updated_at"] = _now_iso()
            if result is not None:
                _tasks[task_id]["result"] = result
            if error is not None:
                _tasks[task_id]["error"] = error
            _tasks[task_id]["events"].append({
                "status": status,
                "timestamp": _now_iso(),
                "message": error or (result if isinstance(result, str) else None),
            })


def _get_task(task_id: str) -> Optional[Dict[str, Any]]:
    with _task_lock:
        return _tasks.get(task_id)


def _require_aap_auth():
    """Decorator-like helper para verificar auth AAP."""
    body = request.get_data(as_text=True)
    if not verify_aap_request(dict(request.headers), body):
        return jsonify({"error": "Unauthorized", "message": "Invalid or missing AAP credentials"}), 401
    return None


# ── Agent Card ──

@aap_bp.route("/.well-known/agent.json", methods=["GET"])
def agent_card():
    """Retorna o Agent Card do SIAP."""
    card = build_agent_card(
        name="siap-aracannabis",
        version="1.0.0",
        description="Sistema Integrado de Acompanhamento de Pacientes (SIAP) — Aracannabis",
        url=os.getenv("SIAP_PUBLIC_URL", "https://siap.arapath.com.br"),
        capabilities=[
            {
                "id": "patient.sync",
                "name": "Sincronizar Paciente",
                "description": "Recebe dados de paciente de outro sistema e sincroniza",
                "methods": ["sync_patient"],
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "nome": {"type": "string"},
                        "cpf": {"type": "string"},
                        "email": {"type": "string"},
                        "telefone": {"type": "string"},
                        "endereco": {"type": "string"},
                        "data_nascimento": {"type": "string", "format": "date"},
                    },
                    "required": ["nome", "cpf"]
                },
                "async": False,
            },
            {
                "id": "patient.get_by_cpf",
                "name": "Buscar Paciente por CPF",
                "description": "Retorna dados do paciente pelo CPF",
                "methods": ["get_patient_by_cpf"],
                "input_schema": {
                    "type": "object",
                    "properties": {"cpf": {"type": "string"}},
                    "required": ["cpf"]
                },
                "async": False,
            },
            {
                "id": "prescription.get",
                "name": "Obter Prescrição",
                "description": "Retorna prescrição ativa de um paciente",
                "methods": ["get_prescription"],
                "input_schema": {
                    "type": "object",
                    "properties": {"patient_id": {"type": "integer"}},
                    "required": ["patient_id"]
                },
                "async": False,
            }
        ]
    )
    return jsonify(card)


# ── Health ──

@aap_bp.route("/aap/health", methods=["GET"])
def aap_health():
    return jsonify({"status": "healthy", "service": "siap-aap", "version": "1.0.0"})


# ── Tasks ──

@aap_bp.route("/aap/tasks", methods=["POST"])
def submit_task():
    """Recebe uma task delegada por outro agente."""
    auth_error = _require_aap_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id") or str(uuid.uuid4())
    capability_id = data.get("capability_id")
    method = data.get("method")
    params = data.get("params", {})
    callback_url = data.get("callback_url")

    if not capability_id or not method:
        return jsonify({"error": "Bad Request", "message": "capability_id and method are required"}), 400

    task = _create_task(task_id, capability_id, method, params, callback_url)

    # Processamento assíncrono (thread) para não bloquear a resposta
    def _process():
        try:
            _update_task(task_id, "working")
            result = _execute_capability(capability_id, method, params)
            _update_task(task_id, "completed", result=result)
            _notify_callback(task, "completed", result=result)
        except Exception as e:
            _update_task(task_id, "failed", error=str(e))
            _notify_callback(task, "failed", error=str(e))

    threading.Thread(target=_process, daemon=True).start()

    return jsonify({
        "task_id": task_id,
        "status": "submitted",
        "created_at": task["created_at"],
        "events_url": f"/aap/tasks/{task_id}/events",
    }), 202


@aap_bp.route("/aap/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    auth_error = _require_aap_auth()
    if auth_error:
        return auth_error

    task = _get_task(task_id)
    if not task:
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404

    return jsonify({
        "task_id": task["task_id"],
        "status": task["status"],
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
        "result": task["result"],
        "error": task["error"],
    })


@aap_bp.route("/aap/tasks/<task_id>/cancel", methods=["POST"])
def cancel_task(task_id):
    auth_error = _require_aap_auth()
    if auth_error:
        return auth_error

    task = _get_task(task_id)
    if not task:
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404

    if task["status"] in ("completed", "failed", "cancelled"):
        return jsonify({"error": "Conflict", "message": f"Task already {task['status']}"}), 409

    _update_task(task_id, "cancelled")
    return jsonify({"task_id": task_id, "status": "cancelled"})


@aap_bp.route("/aap/tasks/<task_id>/events", methods=["GET"])
def task_events(task_id):
    """SSE stream de eventos de uma task."""
    auth_error = _require_aap_auth()
    if auth_error:
        return auth_error

    task = _get_task(task_id)
    if not task:
        return jsonify({"error": "Not Found", "message": "Task not found"}), 404

    def event_stream():
        import time
        last_index = 0
        while True:
            with _task_lock:
                events = list(_tasks.get(task_id, {}).get("events", []))
            new_events = events[last_index:]
            for ev in new_events:
                yield f"event: status_change\ndata: {json.dumps(ev)}\n\n"
            last_index = len(events)

            # Se task terminou, envia evento final e encerra
            current_status = _tasks.get(task_id, {}).get("status")
            if current_status in ("completed", "failed", "cancelled"):
                yield f"event: done\ndata: {{\"status\":\"{current_status}\"}}\n\n"
                break
            time.sleep(1)

    return Response(event_stream(), mimetype="text/event-stream")


# ── Webhook Receiver ──

@aap_bp.route("/aap/webhooks/<agent_name>", methods=["POST"])
def receive_webhook(agent_name):
    """Recebe callbacks de outros agentes."""
    auth_error = _require_aap_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    task_id = data.get("task_id")
    status = data.get("status")
    result = data.get("result")
    error = data.get("error")

    print(f"[AAP Webhook] Agent={agent_name} Task={task_id} Status={status}")

    # Atualiza task local se existir
    if task_id and _get_task(task_id):
        _update_task(task_id, status, result=result, error=error)

    return jsonify({"received": True, "agent": agent_name, "task_id": task_id})


# ── Registry Admin ──

@aap_bp.route("/aap/registry", methods=["GET"])
def list_registry():
    """Lista agentes registrados (útil para debug/admin)."""
    auth_error = _require_aap_auth()
    if auth_error:
        return auth_error

    registry = get_registry()
    return jsonify({"agents": registry.list_agents()})


@aap_bp.route("/aap/registry/<agent_name>", methods=["POST"])
def register_agent(agent_name):
    """Registra um Agent Card manualmente."""
    auth_error = _require_aap_auth()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    registry = get_registry()
    registry.register(agent_name, data)
    return jsonify({"registered": True, "agent": agent_name})


# ── Execução Interna de Capabilities ──

def _execute_capability(capability_id: str, method: str, params: dict) -> Any:
    """Executa uma capability local do SIAP."""
    from models import Paciente, db
    from sqlalchemy import or_

    if capability_id == "patient.sync":
        # Sincroniza paciente recebido de outro sistema
        with current_app.app_context():
            cpf = params.get("cpf", "").replace(".", "").replace("-", "")
            paciente = Paciente.query.filter_by(cpf=cpf).first()
            if paciente:
                paciente.nome = params.get("nome", paciente.nome)
                paciente.email = params.get("email", paciente.email)
                paciente.telefone = params.get("telefone", paciente.telefone)
                paciente.endereco = params.get("endereco", paciente.endereco)
                db.session.commit()
                return {"action": "updated", "patient_id": paciente.id}
            else:
                novo = Paciente(
                    nome=params["nome"],
                    cpf=cpf,
                    email=params.get("email"),
                    telefone=params.get("telefone"),
                    endereco=params.get("endereco"),
                )
                db.session.add(novo)
                db.session.commit()
                return {"action": "created", "patient_id": novo.id}

    elif capability_id == "patient.get_by_cpf":
        with current_app.app_context():
            cpf = params.get("cpf", "").replace(".", "").replace("-", "")
            paciente = Paciente.query.filter_by(cpf=cpf).first()
            if paciente:
                return {
                    "id": paciente.id,
                    "nome": paciente.nome,
                    "cpf": paciente.cpf,
                    "email": paciente.email,
                    "telefone": paciente.telefone,
                    "endereco": paciente.endereco,
                }
            return None

    elif capability_id == "prescription.get":
        # Stub — pode ser implementado com Prescricao model
        return {"prescription_id": None, "message": "Prescription capability not yet implemented"}

    else:
        raise ValueError(f"Capability não implementada: {capability_id}")


def _notify_callback(task: dict, status: str, result: Any = None, error: str = None):
    """Envia callback para o agente cliente, se configurado."""
    callback_url = task.get("callback_url")
    if not callback_url:
        return

    payload = {
        "task_id": task["task_id"],
        "status": status,
        "result": result,
        "error": error,
        "agent": "siap-aracannabis",
    }
    try:
        client = AAPClient(callback_url, api_key=AAP_API_KEY)
        client.session.post(
            callback_url,
            json=payload,
            headers=client._headers(json.dumps(payload)),
            timeout=10
        )
    except Exception as e:
        print(f"[AAP] Falha ao enviar callback para {callback_url}: {e}")
