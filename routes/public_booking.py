"""
Public Booking API — agendamento público multi-tenant com integração VSF

Endpoints públicos (sem JWT) para o fluxo de agendamento:
- Listar clínicas/associações ativas
- Listar profissionais de uma clínica
- Buscar slots disponíveis
- Verificar/cadastrar paciente por CPF
- Criar agendamento
- Enrollment facial pós-agendamento

Todos os endpoints estão sob /api/public/booking/ (bypass do tenant middleware).
"""

from flask import Blueprint, request, jsonify
from models import db, Paciente, Consulta, Profissional, Disponibilidade, Associacao
from models_extra import SalaAmbiente, UsuarioAssociacao
from datetime import datetime, date, time, timedelta
import logging
import re

from services.vsf_bridge import vsf_bridge, VSFAuthError

logger = logging.getLogger(__name__)

public_booking_bp = Blueprint("public_booking", __name__)

DIAS_SEMANA = {
    "dom": 0, "domingo": 0,
    "seg": 1, "segunda": 1,
    "ter": 2, "terca": 2,
    "qua": 3, "quarta": 3,
    "qui": 4, "quinta": 4,
    "sex": 5, "sexta": 5,
    "sab": 6, "sabado": 6,
}


def _is_valid_cpf(cpf: str) -> bool:
    cpf = re.sub(r"\D", "", cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * (i + 1 - j) for j in range(i))
        digito = (soma * 10 % 11) % 11
        if int(cpf[i]) != digito:
            return False
    return True


def _resolve_associacao(slug: str) -> Associacao | None:
    return Associacao.query.filter_by(slug=slug, ativo=True).first()


# ── Listar clínicas ativas ──────────────────────────────────────────────


@public_booking_bp.route("/clinicas", methods=["GET"])
def listar_clinicas():
    """Lista todas as clínicas/associações ativas para o seletor multi-tenant."""
    clinicas = Associacao.query.filter_by(ativo=True).order_by(Associacao.nome).all()
    return jsonify({
        "clinicas": [
            {
                "id": c.id,
                "nome": c.nome,
                "slug": c.slug,
                "telefone": c.telefone,
                "email": c.email,
                "endereco": c.endereco,
            }
            for c in clinicas
        ]
    }), 200


# ── Listar profissionais de uma clínica ─────────────────────────────────


@public_booking_bp.route("/<slug>/profissionais", methods=["GET"])
def listar_profissionais(slug: str):
    """Lista profissionais ativos vinculados a uma clínica."""
    associacao = _resolve_associacao(slug)
    if not associacao:
        return jsonify({"error": "Clínica não encontrada"}), 404

    vinculos = UsuarioAssociacao.query.filter_by(
        associacao_id=associacao.id, status="active"
    ).all()

    profissionais = []
    for v in vinculos:
        prof = Profissional.query.get(v.profissional_id)
        if prof and prof.status_cadastro == "aprovado":
            profissionais.append({
                "id": prof.id,
                "nome": prof.nome,
                "crm": prof.crm,
                "uf_crm": prof.uf_crm,
                "especialidade": prof.validation_data.get("especialidade") if prof.validation_data else None,
                "slug": prof.pre_atendimento_slug,
            })

    return jsonify({"profissionais": profissionais}), 200


# ── Listar salas/ambientes de uma clínica ────────────────────────────────


@public_booking_bp.route("/<slug>/salas", methods=["GET"])
def listar_salas(slug: str):
    """Lista salas ativas do tipo consultorio de uma clínica."""
    associacao = _resolve_associacao(slug)
    if not associacao:
        return jsonify({"error": "Clínica não encontrada"}), 404

    salas = SalaAmbiente.query.filter_by(
        associacao_id=associacao.id, ativo=True, tipo="consultorio"
    ).all()

    return jsonify({
        "salas": [
            {
                "id": s.id,
                "nome": s.nome,
                "vsf_room_key": s.vsf_room_key,
                "capacidade": s.capacidade,
            }
            for s in salas
        ]
    }), 200


# ── Disponibilidades de um profissional ──────────────────────────────────


@public_booking_bp.route("/<slug>/profissional/<int:prof_id>/disponibilidade", methods=["GET"])
def listar_disponibilidade_profissional(slug: str, prof_id: int):
    """Lista a grade de horários de um profissional."""
    associacao = _resolve_associacao(slug)
    if not associacao:
        return jsonify({"error": "Clínica não encontrada"}), 404

    dispens = Disponibilidade.query.filter_by(
        profissional_id=prof_id, ativo=True
    ).all()

    return jsonify({
        "disponibilidades": [d.to_dict() for d in dispens]
    }), 200


# ── Slots disponíveis ────────────────────────────────────────────────────


@public_booking_bp.route("/<slug>/profissional/<int:prof_id>/slots", methods=["GET"])
def slots_disponiveis(slug: str, prof_id: int):
    """Retorna horários disponíveis para um profissional em um período."""
    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")

    if not data_inicio_str:
        data_inicio = date.today()
    else:
        data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()

    if data_fim_str:
        data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
    else:
        data_fim = data_inicio + timedelta(days=14)

    dispens = Disponibilidade.query.filter_by(
        profissional_id=prof_id, ativo=True
    ).all()

    if not dispens:
        return jsonify({"horarios": []}), 200

    consultas_existentes = Consulta.query.filter(
        Consulta.profissional_id == prof_id,
        Consulta.status.in_(["agendada", "confirmada"]),
        Consulta.data_hora >= datetime.combine(data_inicio, time.min),
        Consulta.data_hora <= datetime.combine(data_fim, time.max),
    ).all()

    horarios_ocupados = {}
    for c in consultas_existentes:
        data_key = c.data_hora.date()
        if data_key not in horarios_ocupados:
            horarios_ocupados[data_key] = []
        horarios_ocupados[data_key].append(c.data_hora)

    horarios_disponiveis = []
    current_date = data_inicio

    while current_date <= data_fim:
        dia_semana = current_date.weekday()
        dia_semana_modelo = 6 if dia_semana == 6 else dia_semana + 1

        for disp in dispens:
            if disp.dia_semana == dia_semana_modelo:
                duracao = disp.duracao_consulta_minutos
                current_time = disp.hora_inicio

                while current_time < disp.hora_fim:
                    slot_datetime = datetime.combine(current_date, current_time)

                    is_occupied = False
                    if current_date in horarios_ocupados:
                        for occupied_time in horarios_ocupados[current_date]:
                            occupied_start = occupied_time
                            occupied_end = occupied_start + timedelta(minutes=duracao)
                            slot_end = slot_datetime + timedelta(minutes=duracao)
                            if (
                                slot_datetime >= occupied_start and slot_datetime < occupied_end
                            ) or (
                                occupied_start >= slot_datetime and occupied_start < slot_end
                            ):
                                is_occupied = True
                                break

                    if not is_occupied:
                        horarios_disponiveis.append({
                            "data": current_date.strftime("%Y-%m-%d"),
                            "hora": current_time.strftime("%H:%M"),
                            "duracao_minutos": duracao,
                        })

                    current_time = (
                        datetime.combine(date.today(), current_time)
                        + timedelta(minutes=duracao)
                    ).time()

        current_date += timedelta(days=1)

    return jsonify({
        "data_inicio": data_inicio.strftime("%Y-%m-%d"),
        "data_fim": data_fim.strftime("%Y-%m-%d"),
        "horarios": horarios_disponiveis,
    }), 200


# ── Verificar paciente por CPF ──────────────────────────────────────────


@public_booking_bp.route("/paciente/check", methods=["POST"])
def check_paciente():
    """Verifica se paciente já existe pelo CPF.
    Se existir, retorna dados. Se não, retorna disponível para cadastro.
    """
    data = request.get_json() or {}
    cpf = re.sub(r"\D", "", data.get("cpf", ""))

    if not cpf:
        return jsonify({"error": "CPF obrigatório"}), 400
    if not _is_valid_cpf(cpf):
        return jsonify({"error": "CPF inválido"}), 400

    paciente = Paciente.query.filter_by(cpf=cpf).first()

    if paciente:
        return jsonify({
            "exists": True,
            "paciente": {
                "id": paciente.id,
                "nome": paciente.nome,
                "cpf": paciente.cpf,
                "telefone": paciente.telefone,
                "email": paciente.email,
                "data_nascimento": paciente.data_nascimento.isoformat() if paciente.data_nascimento else None,
                "face_enrolled": paciente.face_enrolled,
                "vsf_patient_id": paciente.vsf_patient_id,
            }
        }), 200

    return jsonify({"exists": False}), 200


# ── Cadastrar paciente (público) ────────────────────────────────────────


@public_booking_bp.route("/paciente/register", methods=["POST"])
def register_paciente_public():
    """Cadastra um novo paciente via fluxo público de agendamento.
    Não requer JWT — o paciente se auto-cadastra.
    """
    data = request.get_json() or {}
    cpf = re.sub(r"\D", "", data.get("cpf", ""))
    nome = (data.get("nome") or "").strip()
    telefone = (data.get("telefone") or "").strip()
    email = (data.get("email") or "").strip()
    data_nascimento_str = data.get("data_nascimento")
    consentimento = data.get("consentimento_lgpd", False)

    if not cpf or not _is_valid_cpf(cpf):
        return jsonify({"error": "CPF inválido"}), 400
    if not nome or len(nome) < 2:
        return jsonify({"error": "Nome deve ter ao menos 2 caracteres"}), 400

    if Paciente.query.filter_by(cpf=cpf).first():
        return jsonify({"error": "CPF já cadastrado"}), 409

    data_nasc = None
    if data_nascimento_str:
        try:
            data_nasc = datetime.strptime(data_nascimento_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    paciente = Paciente(
        nome=nome,
        cpf=cpf,
        telefone=telefone,
        email=email,
        data_nascimento=data_nasc,
        consentimento_lgpd=consentimento,
        data_consentimento=datetime.utcnow() if consentimento else None,
    )
    db.session.add(paciente)
    db.session.commit()

    logger.info(f"Paciente público cadastrado: {paciente.id} - {nome}")

    return jsonify({
        "message": "Paciente cadastrado com sucesso",
        "paciente": {
            "id": paciente.id,
            "nome": paciente.nome,
            "cpf": paciente.cpf,
            "telefone": paciente.telefone,
            "email": paciente.email,
        }
    }), 201


# ── Criar agendamento (público) ──────────────────────────────────────────


@public_booking_bp.route("/<slug>/agendar", methods=["POST"])
def criar_agendamento_publico(slug: str):
    """Cria agendamento público com integração VSF.

    Body: {
        "paciente_id": 123,
        "profissional_id": 1,
        "sala_id": 1 (opcional),
        "data_hora": "2026-09-15T14:00:00",
        "duracao_minutos": 60,
        "convenio_nome": "Particular" (opcional),
        "observacoes": "" (opcional)
    }
    """
    associacao = _resolve_associacao(slug)
    if not associacao:
        return jsonify({"error": "Clínica não encontrada"}), 404

    data = request.get_json() or {}

    paciente_id = data.get("paciente_id")
    profissional_id = data.get("profissional_id")
    data_hora_str = data.get("data_hora")

    if not paciente_id or not profissional_id or not data_hora_str:
        return jsonify({"error": "paciente_id, profissional_id e data_hora obrigatórios"}), 400

    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({"error": "Paciente não encontrado"}), 404

    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return jsonify({"error": "Profissional não encontrado"}), 404

    try:
        data_hora = datetime.fromisoformat(data_hora_str.replace("Z", "+00:00"))
    except ValueError:
        return jsonify({"error": "Formato de data_hora inválido"}), 400

    consulta_existente = Consulta.query.filter(
        Consulta.data_hora == data_hora,
        Consulta.profissional_id == profissional_id,
        Consulta.status.in_(["agendada", "confirmada"]),
    ).first()
    if consulta_existente:
        return jsonify({"error": "Já existe agendamento para este horário"}), 400

    sala_id = data.get("sala_id")
    sala = None
    if sala_id:
        sala = SalaAmbiente.query.get(sala_id)

    consulta = Consulta(
        paciente_id=paciente_id,
        associacao_id=associacao.id,
        profissional_id=profissional_id,
        data_hora=data_hora,
        duracao_minutos=data.get("duracao_minutos", 60),
        tipo_consulta="presencial",
        status="agendada",
        observacoes=data.get("observacoes", ""),
        convenio_nome=data.get("convenio_nome", "Particular"),
    )
    db.session.add(consulta)
    db.session.commit()

    logger.info(f"Agendamento público criado: consulta {consulta.id} para paciente {paciente_id}")

    # Sincronizar com VSF
    vsf_result = {}
    try:
        result = vsf_bridge.sincronizar_consulta(
            paciente_nome=paciente.nome,
            paciente_id_araos=str(paciente.id),
            scheduled_for=data_hora,
            paciente_telefone=paciente.telefone,
            paciente_email=paciente.email,
            paciente_cpf=paciente.cpf,
            convenio_nome=consulta.convenio_nome,
            vsf_patient_id_existente=paciente.vsf_patient_id,
            professional_id=str(profissional_id),
            room_id=data.get("room_id") or (sala.vsf_room_key if sala else None),
            exam_duration_minutes=consulta.duracao_minutos or 30,
        )
        if result.get("vsf_patient_id"):
            paciente.vsf_patient_id = result["vsf_patient_id"]
        if result.get("vsf_appointment_id"):
            consulta.vsf_appointment_id = result["vsf_appointment_id"]
            consulta.vsf_synced = True
        db.session.commit()
        vsf_result = result
    except Exception as e:
        logger.warning(f"Falha ao sincronizar agendamento {consulta.id} com VSF: {e}")

    return jsonify({
        "message": "Agendamento criado com sucesso",
        "consulta": consulta.to_dict(),
        "vsf_sync": vsf_result,
        "precisa_enroll_face": not paciente.face_enrolled,
    }), 201


# ── Enrollment facial pós-agendamento ─────────────────────────────────────


@public_booking_bp.route("/enroll-face", methods=["POST"])
def enroll_face_public():
    """Enrollment facial após agendamento (público, sem JWT).

    Body: {
        "paciente_id": 123,
        "consulta_id": 456 (opcional),
        "image_base64": "data:image/jpeg;base64,..."
    }
    """
    data = request.get_json() or {}
    paciente_id = data.get("paciente_id")
    consulta_id = data.get("consulta_id")
    image_base64 = data.get("image_base64")

    if not paciente_id or not image_base64:
        return jsonify({"error": "paciente_id e image_base64 obrigatórios"}), 400

    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        return jsonify({"error": "Paciente não encontrado"}), 404

    if paciente.face_enrolled:
        return jsonify({
            "status": "already_enrolled",
            "message": "Paciente já possui cadastro facial.",
            "vsf_patient_id": paciente.vsf_patient_id,
        }), 200

    consulta = None
    if consulta_id:
        consulta = Consulta.query.get(consulta_id)

    try:
        # 1. Criar paciente no VSF se não existir
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
                return jsonify({
                    "status": "success",
                    "vsf_patient_id": vsf_patient_id,
                    "message": "Paciente criado e face cadastrada no VSF.",
                }), 200

        # 2. Se já tem patient_id no VSF e tem consulta, fazer enrollment
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
                "message": "Face cadastrada com sucesso.",
            }), 200

        # 3. Se tem patient_id mas não tem consulta vinculada, criar agendamento dummy
        if paciente.vsf_patient_id:
            apt_data = vsf_bridge.criar_agendamento(
                patient_name=paciente.nome,
                patient_external_id=str(paciente.id),
                scheduled_for=datetime.utcnow() + timedelta(days=365),
                exam_type="enrollment",
                exam_duration_minutes=15,
            )
            apt_id = apt_data.get("appointment_id")
            if apt_id:
                enroll_result = vsf_bridge.enroll_face(
                    appointment_id=str(apt_id),
                    image_base64=image_base64,
                    consent=True,
                )
                paciente.face_enrolled = True
                db.session.commit()
                return jsonify({
                    "status": "success",
                    "enrollment": enroll_result,
                    "message": "Face cadastrada com sucesso.",
                }), 200

        return jsonify({"error": "Não foi possível realizar o enrollment facial"}), 500

    except VSFAuthError as e:
        logger.error(f"Erro de autenticação VSF: {e}")
        return jsonify({"error": "Falha na autenticação VSF"}), 502
    except Exception as e:
        logger.exception(f"Erro no enrollment facial público: {e}")
        return jsonify({"error": str(e)}), 500


# ── Health check ──────────────────────────────────────────────────────────


@public_booking_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "module": "public_booking"}), 200