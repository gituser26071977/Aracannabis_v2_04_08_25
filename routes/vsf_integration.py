"""
Integração AraOS ↔ Visual Smart Flow (VSF)

Endpoints:
- POST /vsf/webhook           → Recebe eventos do VSF (check-in, entrada em sala, etc)
- POST /vsf/sync-appointment  → Sincroniza agendamento AraOS → VSF
- POST /vsf/enroll-face       → Cadastra face do paciente no VSF
- POST /vsf/identify-face     → Identifica paciente por foto no VSF
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from typing import Optional
import logging

from models import db, Paciente, Consulta
from services.vsf_bridge import vsf_bridge, VSFAuthError

logger = logging.getLogger(__name__)

vsf_bp = Blueprint("vsf_integration", __name__)

VSF_WEBHOOK_SECRET = "vsf-araos-webhook-secret-2026"


# ──────────────────────────────────────────────
# Webhook VSF → AraOS
# ──────────────────────────────────────────────

@vsf_bp.route("/webhook", methods=["POST"])
def vsf_webhook():
    """Recebe eventos do Visual Smart Flow.

    Eventos suportados:
    - patient_arrived: paciente reconhecido na recepção
    - patient_entered_room: paciente entrou na sala de exame
    - patient_exited_room: paciente saiu da sala
    - patient_exited_clinic: paciente saiu da clínica
    """
    try:
        data = request.get_json() or {}
        event_type = data.get("event_type") or data.get("event")

        if not event_type:
            return jsonify({"error": "event_type obrigatório"}), 400

        # Opcional: validar secret
        secret = request.headers.get("X-VSF-Secret", "")
        if secret and secret != VSF_WEBHOOK_SECRET:
            return jsonify({"error": "secret inválido"}), 401

        logger.info(f"[VSF Webhook] Evento recebido: {event_type}")

        if event_type == "patient_arrived":
            return _handle_patient_arrived(data)
        elif event_type == "patient_entered_room":
            return _handle_patient_entered_room(data)
        elif event_type == "patient_exited_room":
            return _handle_patient_exited_room(data)
        elif event_type == "patient_exited_clinic":
            return _handle_patient_exited_clinic(data)

        return jsonify({"status": "ignored", "event": event_type}), 200

    except Exception as e:
        logger.exception("Erro no webhook VSF")
        return jsonify({"error": str(e)}), 500


def _handle_patient_arrived(data: dict):
    """Paciente reconhecido na recepção. Atualiza consulta no AraOS."""
    patient_external_id = data.get("patient_external_id") or data.get("patient_id")
    appointment_id = data.get("appointment_id")
    patient_name = data.get("patient_name")
    confidence = data.get("confidence")
    sensor_id = data.get("sensor_id", "vsf-sensor")

    if not patient_external_id:
        return jsonify({"error": "patient_external_id obrigatório"}), 400

    try:
        # patient_external_id deve ser o ID do paciente no AraOS
        paciente = Paciente.query.get(int(patient_external_id))
        if not paciente:
            # Tenta buscar por telefone ou email
            phone = data.get("patient_phone")
            email = data.get("patient_email")
            if phone:
                paciente = Paciente.query.filter_by(telefone=phone).first()
            if not paciente and email:
                paciente = Paciente.query.filter_by(email=email).first()

        if not paciente:
            logger.warning(f"[VSF Webhook] Paciente não encontrado: {patient_external_id}")
            return jsonify({"status": "ignored", "reason": "patient_not_found"}), 200

        # Busca consulta agendada para hoje
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        amanha = hoje.replace(day=hoje.day + 1)

        consulta = Consulta.query.filter(
            Consulta.paciente_id == paciente.id,
            Consulta.status.in_(["agendada", "confirmada"]),
            Consulta.data_hora >= hoje,
            Consulta.data_hora < amanha,
        ).order_by(Consulta.data_hora).first()

        if consulta:
            consulta.status = "paciente_presente"
            consulta.observacoes = (consulta.observacoes or "") + f"\n[VSF] Paciente reconhecido por visão computacional às {datetime.now().strftime('%H:%M')} (sensor: {sensor_id}, confiança: {confidence})"
            db.session.commit()
            logger.info(f"[VSF Webhook] Consulta {consulta.id} atualizada: paciente_presente")
            return jsonify({
                "status": "success",
                "action": "check_in",
                "paciente_id": paciente.id,
                "consulta_id": consulta.id,
                "confidence": confidence,
            }), 200

        logger.info(f"[VSF Webhook] Nenhuma consulta agendada hoje para paciente {paciente.id}")
        return jsonify({"status": "ignored", "reason": "no_appointment_today"}), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Erro ao processar patient_arrived")
        return jsonify({"error": str(e)}), 500


def _handle_patient_entered_room(data: dict):
    """Paciente entrou na sala de exame."""
    # Futuro: registrar tempo de espera, enviar notificação
    logger.info(f"[VSF Webhook] Paciente entrou na sala: {data.get('patient_id')}")
    return jsonify({"status": "received", "action": "entered_room"}), 200


def _handle_patient_exited_room(data: dict):
    """Paciente saiu da sala de exame."""
    logger.info(f"[VSF Webhook] Paciente saiu da sala: {data.get('patient_id')}")
    return jsonify({"status": "received", "action": "exited_room"}), 200


def _handle_patient_exited_clinic(data: dict):
    """Paciente saiu da clínica."""
    logger.info(f"[VSF Webhook] Paciente saiu da clínica: {data.get('patient_id')}")
    return jsonify({"status": "received", "action": "exited_clinic"}), 200


# ──────────────────────────────────────────────
# AraOS → VSF: Sincronizar Agendamento
# ──────────────────────────────────────────────

@vsf_bp.route("/sync-appointment", methods=["POST"])
@jwt_required()
def sync_appointment_to_vsf():
    """Sincroniza uma consulta do AraOS para o VSF."""
    data = request.get_json() or {}
    consulta_id = data.get("consulta_id")

    if not consulta_id:
        return jsonify({"error": "consulta_id obrigatório"}), 400

    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({"error": "Consulta não encontrada"}), 404

        paciente = Paciente.query.get(consulta.paciente_id)
        if not paciente:
            return jsonify({"error": "Paciente não encontrado"}), 404

        result = vsf_bridge.criar_agendamento(
            patient_name=paciente.nome,
            patient_external_id=str(paciente.id),
            scheduled_for=consulta.data_hora,
            exam_type="consulta",
            professional_id=str(consulta.profissional_id) if consulta.profissional_id else None,
            exam_duration_minutes=consulta.duracao_minutos or 30,
        )

        return jsonify({
            "status": "success",
            "vsf_appointment_id": str(result.get("appointment_id")),
            "araos_consulta_id": consulta.id,
        }), 201

    except VSFAuthError as e:
        logger.error(f"Erro de autenticação VSF: {e}")
        return jsonify({"error": "Falha na autenticação VSF"}), 502
    except Exception as e:
        logger.exception("Erro ao sincronizar agendamento com VSF")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# AraOS → VSF: Enrollment Facial
# ──────────────────────────────────────────────

@vsf_bp.route("/enroll-face", methods=["POST"])
@jwt_required()
def enroll_face_vsf():
    """Cadastra face do paciente no VSF.

    Body: {
        "consulta_id": 123,
        "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
    }
    """
    data = request.get_json() or {}
    consulta_id = data.get("consulta_id")
    image_base64 = data.get("image_base64")

    if not consulta_id or not image_base64:
        return jsonify({"error": "consulta_id e image_base64 obrigatórios"}), 400

    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({"error": "Consulta não encontrada"}), 404

        # Criar agendamento no VSF primeiro se ainda não existir
        paciente = Paciente.query.get(consulta.paciente_id)
        if not paciente:
            return jsonify({"error": "Paciente não encontrado"}), 404

        vsf_apt = vsf_bridge.criar_agendamento(
            patient_name=paciente.nome,
            patient_external_id=str(paciente.id),
            scheduled_for=consulta.data_hora,
            exam_type="consulta",
            professional_id=str(consulta.profissional_id) if consulta.profissional_id else None,
            exam_duration_minutes=consulta.duracao_minutos or 30,
        )

        appointment_id = str(vsf_apt.get("appointment_id"))

        # Fazer enrollment facial
        enroll_result = vsf_bridge.enroll_face(
            appointment_id=appointment_id,
            image_base64=image_base64,
            consent=True,
        )

        return jsonify({
            "status": "success",
            "vsf_appointment_id": appointment_id,
            "enrollment": enroll_result,
        }), 200

    except VSFAuthError as e:
        logger.error(f"Erro de autenticação VSF: {e}")
        return jsonify({"error": "Falha na autenticação VSF"}), 502
    except Exception as e:
        logger.exception("Erro no enrollment facial VSF")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# AraOS → VSF: Identificação Facial
# ──────────────────────────────────────────────

@vsf_bp.route("/identify-face", methods=["POST"])
def identify_face_vsf():
    """Identifica paciente por foto no VSF (pode ser usado sem login para check-in).

    Body: {
        "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
    }
    """
    data = request.get_json() or {}
    image_base64 = data.get("image_base64")

    if not image_base64:
        return jsonify({"error": "image_base64 obrigatório"}), 400

    try:
        result = vsf_bridge.identify_by_face(image_base64)
        if not result:
            return jsonify({"recognized": False, "message": "Nenhum paciente reconhecido"}), 200

        recognized = result.get("recognized", False)
        if not recognized:
            return jsonify({"recognized": False, "message": "Rosto não reconhecido"}), 200

        patient_id = result.get("patient_id")

        # Buscar paciente no AraOS
        paciente = Paciente.query.get(int(patient_id)) if patient_id and patient_id.isdigit() else None

        return jsonify({
            "recognized": True,
            "patient_id": patient_id,
            "patient_name": result.get("patient_name"),
            "confidence": result.get("confidence"),
            "method": result.get("method"),
            "araos_paciente": {
                "id": paciente.id if paciente else None,
                "nome": paciente.nome if paciente else None,
                "telefone": paciente.telefone if paciente else None,
                "email": paciente.email if paciente else None,
            },
        }), 200

    except VSFAuthError as e:
        logger.error(f"Erro de autenticação VSF: {e}")
        return jsonify({"error": "Falha na autenticação VSF"}), 502
    except Exception as e:
        logger.exception("Erro na identificação facial VSF")
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Teste de conexão
# ──────────────────────────────────────────────

@vsf_bp.route("/health", methods=["GET"])
def vsf_health():
    """Verifica se a conexão com o VSF está funcionando."""
    try:
        token = vsf_bridge.get_token()
        return jsonify({
            "status": "ok",
            "vsf_authenticated": bool(token),
            "araos_vsf_bridge": "active",
        }), 200
    except VSFAuthError as e:
        return jsonify({"status": "error", "message": str(e)}), 502
