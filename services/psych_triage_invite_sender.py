"""Envio do convite de triagem psiquiátrica (reuso por rota e por agente)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from services.psych_triage_invite import build_invite_link, create_invite_token

logger = logging.getLogger(__name__)


class InviteError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def contact_for(db_session: Any, patient_id: Any, channel: str) -> Optional[str]:
    try:
        from models import Paciente

        paciente = db_session.query(Paciente).get(int(patient_id))
    except Exception:  # noqa: BLE001
        return None
    if paciente is None:
        return None
    if channel == "email":
        return getattr(paciente, "email", None)
    return getattr(paciente, "telefone", None)


def dispatch(channel: str, contact: str, link: str, patient_id: str) -> Tuple[bool, str]:
    try:
        if channel == "email":
            from services.email_service import EmailService

            html = (
                "<p>Olá!</p>"
                "<p>Seu médico disponibilizou uma triagem de saúde mental para você responder com "
                "calma, no seu tempo.</p>"
                f'<p><a href="{link}">Responder a triagem</a></p>'
                "<p>Este link expira em alguns dias. Suas respostas são confidenciais e serão "
                "revisadas por um profissional.</p>"
                "<p>Em caso de urgência, procure atendimento de emergência ou ligue 188 (CVV).</p>"
            )
            return bool(EmailService().send_email(contact, "Triagem de saúde mental", html)), "email"

        text = (
            "Olá! Seu médico disponibilizou uma triagem de saúde mental para você responder.\n"
            f"Acesse: {link}\n"
            "Suas respostas são confidenciais e serão revisadas por um profissional."
        )
        if channel == "whatsapp":
            from services.whatsapp_gateway import default_gateway

            gateway = default_gateway()
            if gateway.template_name and gateway.resolved_provider == "meta":
                ok = gateway.send_template(contact, body_variables=[link])
            else:
                ok = gateway.send_text(contact, text)
            return bool(ok), "whatsapp"

        from services.telegram_service import telegram_service

        return bool(telegram_service.send_message(chat_id=contact, text=text)), channel
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao enviar convite de triagem (%s): %s", channel, exc)
        return False, str(exc)


def send_triage_invite(
    db_session: Any,
    *,
    tenant_id: str,
    patient_id: Any,
    channel: str = "link",
    contact: Optional[str] = None,
    version: str = "latest",
    expires_hours: int = 72,
) -> Dict[str, Any]:
    if not tenant_id:
        raise InviteError("tenant_required", "tenant_id é obrigatório")
    if not patient_id:
        raise InviteError("patient_required", "patient_id é obrigatório")

    token = create_invite_token(tenant_id, patient_id=str(patient_id), version=version)
    link = build_invite_link(token)

    sent = False
    detail = "link_only"
    if channel != "link":
        contact = contact or contact_for(db_session, patient_id, channel)
        if not contact:
            raise InviteError("contact_required", "Informe o contato do paciente")
        sent, detail = dispatch(channel, str(contact), link, str(patient_id))

    return {
        "patient_id": patient_id,
        "channel": channel,
        "link": link,
        "token": token,
        "sent": sent,
        "detail": detail,
        "expires_hours": expires_hours,
    }
