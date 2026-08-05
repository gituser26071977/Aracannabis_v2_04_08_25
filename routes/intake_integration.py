"""Integração Ara Intake → SIAP — cadastro automático de paciente.

Quando a pré-consulta é concluída no intake (web/Telegram), o intake chama
`POST /api/intake/patient` para:
  1. Criar/atualizar o Paciente no SIAP (upsert por telefone ou CPF).
  2. Registrar a Pré-Consulta vinculada (queixa, intensidade, canal, gene).

Segurança: header `X-Intake-Token` == env `INTAKE_SERVICE_TOKEN`
(em dev sem token configurado, aceita).
"""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from models import db, Paciente, PreConsulta

logger = logging.getLogger(__name__)

intake_integration_bp = Blueprint("intake_integration", __name__)


def _token_valido() -> bool:
    import os

    expected = os.environ.get("INTAKE_SERVICE_TOKEN", "")
    if not expected:
        return True  # dev: sem token configurado
    provided = request.headers.get("X-Intake-Token", "")
    import hmac

    return hmac.compare_digest(provided, expected)


def _normalizar_telefone(phone: str | None) -> str | None:
    if not phone:
        return None
    return "".join(ch for ch in phone if ch.isdigit())


def _encontrar_paciente(data: dict) -> Paciente | None:
    phone = _normalizar_telefone(data.get("phone"))
    cpf = (data.get("cpf") or "").replace(".", "").replace("-", "")
    q = Paciente.query
    conds = []
    if cpf:
        conds.append(Paciente.cpf == cpf)
    if phone:
        conds.append(Paciente.telefone == phone)
    if not conds:
        return None
    return q.filter(or_(*conds)).first()


@intake_integration_bp.route("/intake/patient", methods=["POST"])
def receber_paciente_intake():
    if not _token_valido():
        return jsonify({"error": "token inválido"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data.get("patient_name"):
        return jsonify({"error": "patient_name é obrigatório"}), 400

    paciente = _encontrar_paciente(data)
    criado = False
    if paciente is None:
        paciente = Paciente(
            nome=data["patient_name"],
            cpf=(data.get("cpf") or "").replace(".", "").replace("-", "") or None,
            telefone=_normalizar_telefone(data.get("phone")),
            email=data.get("email") or None,
            data_nascimento=None,
        )
        db.session.add(paciente)
        criado = True
    else:
        if data.get("patient_name"):
            paciente.nome = data["patient_name"]
        if data.get("phone") and not paciente.telefone:
            paciente.telefone = _normalizar_telefone(data["phone"])

    db.session.flush()  # gera id do paciente

    # Pré-Consulta vinculada (idempotente por intake_interview_id)
    interview_id = data.get("interview_id")
    pre = None
    if interview_id:
        pre = PreConsulta.query.filter_by(intake_interview_id=interview_id).first()
    if pre is None:
        pre = PreConsulta(
            paciente_id=paciente.id,
            intake_interview_id=interview_id or None,
            canal=data.get("canal", "web"),
            status="concluida",
        )
        db.session.add(pre)
    pre.queixa_principal = data.get("queixa_principal")
    pre.intensidade = data.get("intensidade")
    pre.araos_patient_id = data.get("araos_patient_id")
    pre.gene_expressions = data.get("gene_expressions")

    db.session.commit()
    logger.info(
        "intake_paciente_registrado",
        extra={"paciente_id": paciente.id, "criado": criado, "interview_id": interview_id},
    )
    return jsonify(
        {
            "ok": True,
            "paciente_id": paciente.id,
            "pre_consulta_id": pre.id,
            "criado": criado,
        }
    ), 201 if criado else 200
