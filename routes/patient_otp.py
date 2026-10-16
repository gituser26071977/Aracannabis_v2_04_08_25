"""Portal do Paciente — acesso por código (OTP) enviado no WhatsApp.

Fluxo (opção A escolhida pelo Dr. Anderson):
  1. POST /api/patient-auth/otp/request  {"cpf": "..."}      -> envia código de 6 dígitos no WhatsApp
  2. POST /api/patient-auth/otp/verify   {"cpf": "...", "codigo": "..."} -> devolve JWT (user_type=patient)

Sem senha. Resposta do /request é sempre genérica (não revela se o CPF existe).
Tabela própria `patient_otp` (criada por CREATE TABLE IF NOT EXISTS).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from sqlalchemy import text

from models import db, Paciente

logger = logging.getLogger(__name__)

patient_otp_bp = Blueprint("patient_otp", __name__)

OTP_TTL_MIN = 10
OTP_MAX_ATTEMPTS = 5
OTP_COOLDOWN_SEG = 45  # mínimo entre pedidos do mesmo paciente


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _ensure_tables() -> None:
    db.session.execute(text(
        """
        CREATE TABLE IF NOT EXISTS patient_otp (
            id SERIAL PRIMARY KEY,
            paciente_id INTEGER NOT NULL,
            codigo_hash VARCHAR(128) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN NOT NULL DEFAULT FALSE,
            attempts INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
        """
    ))
    db.session.commit()


def _hash(cpf: str, codigo: str) -> str:
    return hmac.new(("otp:" + cpf).encode(), codigo.encode(), hashlib.sha256).hexdigest()


def _buscar_por_cpf(cpf: str):
    from sqlalchemy import func
    cpf_col = func.replace(
        func.replace(func.replace(Paciente.cpf, ".", ""), "-", ""), " ", ""
    )
    return Paciente.query.filter(cpf_col == cpf).first()


def _enviar_whatsapp(telefone: str, mensagem: str) -> bool:
    try:
        from services.whatsapp_service import WhatsAppService
        return bool(WhatsAppService().send_message(telefone, mensagem))
    except Exception as exc:  # noqa: BLE001
        logger.warning("otp_whatsapp_falhou: %s", exc)
        return False


GENERIC_MSG = "Se houver cadastro com este CPF, enviamos um código de acesso no WhatsApp."


@patient_otp_bp.route("/otp/request", methods=["POST"])
def otp_request():
    try:
        _ensure_tables()
    except Exception as exc:  # noqa: BLE001
        logger.exception("patient_otp_ensure_falhou: %s", exc)
        return jsonify({"status": "ok", "message": GENERIC_MSG}), 200

    data = request.get_json(silent=True) or {}
    cpf = _digits(data.get("cpf"))
    if len(cpf) != 11:
        return jsonify({"error": "Informe um CPF válido (11 dígitos)."}), 400

    paciente = _buscar_por_cpf(cpf)
    if not paciente or not paciente.telefone:
        return jsonify({"status": "ok", "message": GENERIC_MSG}), 200

    # cooldown: não reenviar em rajada
    ultimo = db.session.execute(text(
        "SELECT created_at FROM patient_otp WHERE paciente_id=:p ORDER BY id DESC LIMIT 1"
    ), {"p": paciente.id}).fetchone()
    if ultimo and ultimo[0] and (datetime.utcnow() - ultimo[0]).total_seconds() < OTP_COOLDOWN_SEG:
        return jsonify({"status": "ok", "message": "Aguarde um instante antes de pedir outro código."}), 200

    codigo = f"{secrets.randbelow(1_000_000):06d}"
    db.session.execute(text(
        "INSERT INTO patient_otp (paciente_id, codigo_hash, expires_at) VALUES (:p, :h, :e)"
    ), {"p": paciente.id, "h": _hash(cpf, codigo),
        "e": datetime.utcnow() + timedelta(minutes=OTP_TTL_MIN)})
    db.session.commit()

    ok = _enviar_whatsapp(
        paciente.telefone,
        f"🔐 Portal do paciente — seu código de acesso é *{codigo}*. "
        f"Vale por {OTP_TTL_MIN} minutos. Não compartilhe.",
    )
    if not ok:
        return jsonify({"error": "Não foi possível enviar o código agora. Tente novamente."}), 503
    return jsonify({"status": "ok", "message": GENERIC_MSG}), 200


@patient_otp_bp.route("/otp/verify", methods=["POST"])
def otp_verify():
    try:
        _ensure_tables()
    except Exception:  # noqa: BLE001
        pass

    data = request.get_json(silent=True) or {}
    cpf = _digits(data.get("cpf"))
    codigo = (data.get("codigo") or "").strip()
    if len(cpf) != 11 or not codigo:
        return jsonify({"error": "CPF e código são obrigatórios."}), 400

    paciente = _buscar_por_cpf(cpf)
    if not paciente:
        return jsonify({"error": "Código inválido ou expirado."}), 401

    row = db.session.execute(text(
        "SELECT id, codigo_hash, expires_at, used, attempts FROM patient_otp "
        "WHERE paciente_id=:p AND used=false ORDER BY id DESC LIMIT 1"
    ), {"p": paciente.id}).fetchone()

    if not row:
        return jsonify({"error": "Código inválido ou expirado."}), 401
    rid, chash, exp, used, attempts = row
    if exp and exp < datetime.utcnow():
        return jsonify({"error": "Código expirado. Peça um novo."}), 401
    if attempts >= OTP_MAX_ATTEMPTS:
        return jsonify({"error": "Muitas tentativas. Peça um novo código."}), 429

    if not hmac.compare_digest(_hash(cpf, codigo), chash):
        db.session.execute(text("UPDATE patient_otp SET attempts = attempts + 1 WHERE id=:i"), {"i": rid})
        db.session.commit()
        return jsonify({"error": "Código inválido ou expirado."}), 401

    db.session.execute(text("UPDATE patient_otp SET used=true WHERE id=:i"), {"i": rid})
    paciente.last_login_at = datetime.utcnow()
    db.session.commit()

    token = create_access_token(
        identity=str(paciente.id),
        additional_claims={"user_type": "patient"},
        expires_delta=timedelta(hours=12),
    )
    return jsonify({
        "access_token": token,
        "user": {"id": paciente.id, "nome": paciente.nome, "user_type": "patient"},
        "message": "Acesso liberado",
    }), 200
