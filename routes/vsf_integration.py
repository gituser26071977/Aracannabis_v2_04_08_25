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
        paciente = Paciente.query.get(int(patient_external_id))
        if not paciente:
            phone = data.get("patient_phone")
            email = data.get("patient_email")
            if phone:
                paciente = Paciente.query.filter_by(telefone=phone).first()
            if not paciente and email:
                paciente = Paciente.query.filter_by(email=email).first()

        if not paciente:
            logger.warning(f"[VSF Webhook] Paciente não encontrado: {patient_external_id}")
            return jsonify({"status": "ignored", "reason": "patient_not_found"}), 200

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
            if appointment_id and not consulta.vsf_appointment_id:
                consulta.vsf_appointment_id = str(appointment_id)
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
    logger.info(f"[VSF Webhook] Paciente entrou na sala: {data.get('patient_id')}")
    return jsonify({"status": "received", "action": "entered_room"}), 200


def _handle_patient_exited_room(data: dict):
    logger.info(f"[VSF Webhook] Paciente saiu da sala: {data.get('patient_id')}")
    return jsonify({"status": "received", "action": "exited_room"}), 200


def _handle_patient_exited_clinic(data: dict):
    logger.info(f"[VSF Webhook] Paciente saiu da clínica: {data.get('patient_id')}")
    return jsonify({"status": "received", "action": "exited_clinic"}), 200


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

        result = vsf_bridge.sincronizar_consulta(
            paciente_nome=paciente.nome,
            paciente_id_araos=str(paciente.id),
            scheduled_for=consulta.data_hora,
            paciente_telefone=paciente.telefone,
            paciente_email=paciente.email,
            paciente_cpf=paciente.cpf,
            convenio_nome=consulta.convenio_nome,
            vsf_patient_id_existente=paciente.vsf_patient_id,
            professional_id=str(consulta.profissional_id) if consulta.profissional_id else None,
            exam_duration_minutes=consulta.duracao_minutos or 30,
        )

        # Salvar IDs do VSF no AraOS
        if result.get("vsf_patient_id"):
            paciente.vsf_patient_id = result["vsf_patient_id"]
        if result.get("vsf_appointment_id"):
            consulta.vsf_appointment_id = result["vsf_appointment_id"]
            consulta.vsf_synced = True
        db.session.commit()

        return jsonify({
            "status": "success",
            "vsf_appointment_id": result.get("vsf_appointment_id"),
            "vsf_patient_id": result.get("vsf_patient_id"),
            "created_patient": result.get("created_patient", False),
            "araos_consulta_id": consulta.id,
        }), 201

    except VSFAuthError as e:
        logger.error(f"Erro de autenticação VSF: {e}")
        return jsonify({"error": "Falha na autenticação VSF"}), 502
    except Exception as e:
        logger.exception("Erro ao sincronizar agendamento com VSF")
        return jsonify({"error": str(e)}), 500


@vsf_bp.route("/enroll-face", methods=["POST"])
@jwt_required()
def enroll_face_vsf():
    """Cadastra face do paciente no VSF.

    Body: {
        "paciente_id": 123,
        "consulta_id": 123,
        "image_base64": "data:image/jpeg;base64,/9j/4AAQ..."
    }
    """
    data = request.get_json() or {}
    paciente_id = data.get("paciente_id")
    consulta_id = data.get("consulta_id")
    image_base64 = data.get("image_base64")

    if not image_base64:
        return jsonify({"error": "image_base64 obrigatório"}), 400

    try:
        paciente = Paciente.query.get(paciente_id) if paciente_id else None
        consulta = Consulta.query.get(consulta_id) if consulta_id else None

        if not paciente and consulta:
            paciente = Paciente.query.get(consulta.paciente_id)

        if not paciente:
            return jsonify({"error": "Paciente não encontrado"}), 404

        # Se paciente ainda não existe no VSF, criar
        if not paciente.vsf_patient_id:
            patient_data = vsf_bridge.criar_paciente(
                name=paciente.nome,
                phone=paciente.telefone,
                email=paciente.email,
                cpf=paciente.cpf,
                face_image_b64=image_base64,
            )
            vsf_patient_id = patient_data.get("id")
            if vsf_patient_id:
                paciente.vsf_patient_id = vsf_patient_id
                paciente.face_enrolled = True
                db.session.commit()
                logger.info(f"Paciente VSF criado e face enrolled: {vsf_patient_id}")
                return jsonify({
                    "status": "success",
                    "vsf_patient_id": vsf_patient_id,
                    "message": "Paciente criado e face cadastrada no VSF",
                }), 200

        # Se paciente já existe no VSF, fazer enrollment via agendamento
        if consulta and consulta.vsf_appointment_id:
            enroll_result = vsf_bridge.enroll_face(
                appointment_id=consulta.vsf_appointment_id,
                image_base64=image_base64,
                consent=True,
            )
            paciente.face_enrolled = True
            db.session.commit()
            return jsonify({
                "status": "success",
                "enrollment": enroll_result,
                "vsf_appointment_id": consulta.vsf_appointment_id,
                "vsf_patient_id": paciente.vsf_patient_id,
            }), 200

        # Precisa criar agendamento primeiro
        if consulta:
            result = vsf_bridge.sincronizar_consulta(
                paciente_nome=paciente.nome,
                paciente_id_araos=str(paciente.id),
                scheduled_for=consulta.data_hora,
                paciente_telefone=paciente.telefone,
                paciente_email=paciente.email,
                paciente_cpf=paciente.cpf,
                convenio_nome=consulta.convenio_nome,
                vsf_patient_id_existente=paciente.vsf_patient_id,
                professional_id=str(consulta.profissional_id) if consulta.profissional_id else None,
                exam_duration_minutes=consulta.duracao_minutos or 30,
            )

            if result.get("vsf_patient_id"):
                paciente.vsf_patient_id = result["vsf_patient_id"]
            if result.get("vsf_appointment_id"):
                consulta.vsf_appointment_id = result["vsf_appointment_id"]
                consulta.vsf_synced = True
            db.session.commit()

            if consulta.vsf_appointment_id:
                enroll_result = vsf_bridge.enroll_face(
                    appointment_id=consulta.vsf_appointment_id,
                    image_base64=image_base64,
                    consent=True,
                )
                paciente.face_enrolled = True
                db.session.commit()
                return jsonify({
                    "status": "success",
                    "enrollment": enroll_result,
                    "vsf_appointment_id": consulta.vsf_appointment_id,
                    "vsf_patient_id": paciente.vsf_patient_id,
                }), 200

        return jsonify({"error": "Não foi possível realizar o enrollment facial"}), 500

    except VSFAuthError as e:
        logger.error(f"Erro de autenticação VSF: {e}")
        return jsonify({"error": "Falha na autenticação VSF"}), 502
    except Exception as e:
        logger.exception("Erro no enrollment facial VSF")
        return jsonify({"error": str(e)}), 500


@vsf_bp.route("/identify-face", methods=["POST"])
def identify_face_vsf():
    """Identifica paciente por foto no VSF.

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

        patient_external_id = result.get("patient_external_id")
        patient_id = result.get("patient_id")

        paciente = None
        # Tenta pelo external_id (ID do AraOS)
        if patient_external_id and patient_external_id.isdigit():
            paciente = Paciente.query.get(int(patient_external_id))

        # Tenta pelo vsf_patient_id
        if not paciente and patient_id:
            paciente = Paciente.query.filter_by(vsf_patient_id=patient_id).first()

        return jsonify({
            "recognized": True,
            "patient_id": patient_id,
            "patient_name": result.get("patient_name"),
            "confidence": result.get("confidence"),
            "method": result.get("method"),
            "patient_external_id": patient_external_id,
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