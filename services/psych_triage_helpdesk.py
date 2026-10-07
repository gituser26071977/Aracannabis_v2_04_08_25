"""Helpdesk de entrada do WhatsApp para a triagem psiquiátrica.

Recebe mensagens (Evolution API ou Meta Cloud API), identifica o paciente
pelo telefone e responde com o link assinado da triagem. Nunca lança:
webhooks devem responder 200 mesmo em erro.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from services.psych_triage_invite import build_invite_link, create_invite_token
from services.whatsapp_gateway import normalize_phone

logger = logging.getLogger(__name__)

_REPLY_TEXT = (
    "Olá! Recebemos sua mensagem. Seu médico disponibilizou uma triagem de saúde mental "
    "para você responder com calma.\nAcesse: {link}\n"
    "Suas respostas são confidenciais. Em caso de urgência, ligue 188 (CVV)."
)
_UNKNOWN_TEXT = (
    "Olá! Não localizamos seu cadastro por este número. "
    "Entre em contato com a clínica para receber o link da triagem."
)


def parse_inbound(payload: Dict[str, Any], provider: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"phone": "", "text": "", "channel": "", "instance": ""}

    if provider == "evolution" or "data" in payload:
        data = payload.get("data") or {}
        key = data.get("key") or {}
        message = data.get("message") or {}
        text = (
            message.get("conversation")
            or (message.get("extendedTextMessage") or {}).get("text")
            or (message.get("imageMessage") or {}).get("caption")
            or ""
        )
        remote = str(key.get("remoteJid") or "")
        return {
            "phone": normalize_phone(remote.split("@")[0]),
            "text": str(text),
            "channel": "evolution",
            "instance": payload.get("instance", ""),
            "from_me": bool(key.get("fromMe")),
        }

    entries = payload.get("entry") or []
    for entry in entries:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            messages = value.get("messages") or []
            if not messages:
                continue
            msg = messages[0]
            text = (msg.get("text") or {}).get("body") or (msg.get("button") or {}).get("text") or ""
            return {
                "phone": normalize_phone(str(msg.get("from") or "")),
                "text": str(text),
                "channel": "meta",
                "instance": str((value.get("metadata") or {}).get("phone_number_id") or ""),
                "from_me": False,
            }
    return {"phone": "", "text": "", "channel": "meta", "instance": "", "from_me": False}


def find_patient_by_phone(phone: str, tenant_id: Optional[str] = None):
    digits = normalize_phone(phone)
    if not digits:
        return None
    tail = digits[-8:]
    try:
        from models import Paciente

        query = Paciente.query.filter(Paciente.telefone.isnot(None))
        if tenant_id:
            from sqlalchemy import text as _text

            try:
                query = query.filter(_text("associacao_id = :tid")).params(tid=int(tenant_id))
            except (TypeError, ValueError):
                pass
        for paciente in query.limit(500):
            if tail and tail in "".join(ch for ch in (paciente.telefone or "") if ch.isdigit()):
                return paciente
    except Exception as exc:  # noqa: BLE001
        logger.warning("psych_triage_helpdesk lookup falhou: %s", exc)
    return None


def handle_inbound(
    payload: Dict[str, Any],
    tenant_id: str,
    *,
    provider: Optional[str] = None,
    sender: Optional[Callable[[str, str], bool]] = None,
    finder: Optional[Callable[[str, Optional[str]], Any]] = None,
) -> Dict[str, Any]:
    parsed = parse_inbound(payload, provider)
    phone = parsed.get("phone")
    if not phone or parsed.get("from_me"):
        return {"ok": False, "reason": "ignored"}

    finder = finder or find_patient_by_phone
    patient = finder(phone, tenant_id)
    if patient is None:
        _reply(phone, _UNKNOWN_TEXT, sender)
        return {"ok": False, "reason": "not_found", "phone": phone}

    patient_id = getattr(patient, "id", None)
    token = create_invite_token(tenant_id, patient_id=str(patient_id))
    link = build_invite_link(token)
    sent = _reply(phone, _REPLY_TEXT.format(link=link), sender)
    return {
        "ok": True,
        "phone": phone,
        "patient_id": patient_id,
        "link": link,
        "sent": sent,
    }


def _reply(phone: str, text: str, sender: Optional[Callable[[str, str], bool]]) -> bool:
    if sender is not None:
        return bool(sender(phone, text))
    try:
        from services.whatsapp_gateway import default_gateway

        return bool(default_gateway().send_text(phone, text))
    except Exception as exc:  # noqa: BLE001
        logger.warning("psych_triage_helpdesk reply falhou: %s", exc)
        return False
