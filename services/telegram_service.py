"""
Telegram Bot API wrapper for SIAP.

Substitui o antigo WhatsAppService (Evolution API) por uma integração
oficial com o Telegram Bot HTTP API.

Env vars:
- TELEGRAM_DEFAULT_BOT_TOKEN   (required para notify_admin_*) — bot fixo
                                do Dr. Anderson (admin geral).
- TELEGRAM_ADMIN_CHAT_ID       (required para notify_admin_*) — chat_id
                                do admin que recebe notificações.
- TELEGRAM_BOT_TOKEN_<SLUG>    (opcional, per-tenant) — bot dedicado
                                de uma clínica específica.

Decisão D05k: admin notif usa bot único Dr.Anderson (não multi-tenant),
para preservar simplicidade do fluxo de cadastro.
"""
import os
import re
import logging
import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


class TelegramService:
    """Envia mensagens via Telegram Bot HTTP API."""

    def __init__(self, bot_token: str = None):
        self.token = (
            bot_token
            or os.environ.get("TELEGRAM_DEFAULT_BOT_TOKEN", "").strip()
        )
        if not self.token:
            logger.warning(
                "[TelegramService] TELEGRAM_DEFAULT_BOT_TOKEN não configurado"
            )

    @classmethod
    def for_tenant(cls, slug: str) -> "TelegramService":
        """Resolve token do tenant via env var TELEGRAM_BOT_TOKEN_<SLUG>."""
        env_var = f"TELEGRAM_BOT_TOKEN_{slug.upper()}"
        token = os.environ.get(env_var, "").strip()
        return cls(bot_token=token)

    def send_message(
        self, chat_id: str | int, text: str, parse_mode: str = "HTML"
    ) -> bool:
        """POST /sendMessage. Returns True em 2xx. Fallback plain text em 400 parse."""
        if not self.token:
            logger.error("[TelegramService] no token, cannot send")
            return False
        if not chat_id:
            logger.warning("[TelegramService] chat_id ausente")
            return False

        url = f"{API_BASE}/bot{self.token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": self._escape_html(text),
            "parse_mode": parse_mode,
        }
        try:
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 400 and "parse" in r.text.lower():
                logger.warning(
                    "[TelegramService] parse error, retrying as plain text"
                )
                payload.pop("parse_mode", None)
                payload["text"] = text  # sem escape no plain retry
                r = requests.post(url, json=payload, timeout=15)
            r.raise_for_status()
            return True
        except Exception as exc:
            logger.error(
                f"[TelegramService] send falhou para chat_id={chat_id}: {exc}"
            )
            return False

    @staticmethod
    def _escape_html(text: str) -> str:
        """HTML escape mínimo; preserva tags Telegram <b>, <i>, <br>."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    # ────────────────────────────────────────────────────────────
    # Compat shim — mantém API do antigo WhatsAppService para
    # os call-sites em routes/cadastro_profissionais.py.
    # Em vez de telefone (WhatsApp), agora usa chat_id Telegram.
    # ────────────────────────────────────────────────────────────
    def notify_admin_new_registration(
        self, nome, email, crm, uf_crm, auto_approved=False
    ):
        """Notifica o admin (Dr.Anderson) sobre novo cadastro de médico."""
        admin_chat_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID", "").strip()
        if not admin_chat_id:
            logger.warning(
                "[TelegramService] TELEGRAM_ADMIN_CHAT_ID não configurado"
            )
            return
        if not self.token:
            logger.warning(
                "[TelegramService] token ausente — pulando notify_admin_new_registration"
            )
            return

        status_text = (
            "✅ <b>APROVADO AUTOMATICAMENTE</b>"
            if auto_approved
            else "⚠️ <b>AGUARDANDO APROVAÇÃO</b>"
        )
        msg = (
            f"🔔 <b>Novo Cadastro de Médico</b>\n\n"
            f"Nome: {nome}\n"
            f"CRM: {crm}/{uf_crm}\n"
            f"Email: {email}\n"
            f"Status: {status_text}\n\n"
            f"🔍 <b>Validar no CFM:</b> https://portal.cfm.org.br/busca-medicos\n\n"
            f"Acesse o painel para detalhes."
        )
        self.send_message(admin_chat_id, msg)

    def notify_doctor_approval(self, chat_id, nome):
        """Notifica o médico que seu cadastro foi aprovado."""
        if not chat_id:
            return
        if not self.token:
            return
        msg = (
            f"Olá Dr(a). {nome}, tudo bem? 👋\n\n"
            f"Seu cadastro no <b>AraOS</b> foi aprovado! ✅\n\n"
            f"Você já pode acessar seu consultório virtual e começar a atender.\n"
            f"Se tiver dúvidas, estamos à disposição."
        )
        self.send_message(chat_id, msg)


# Singleton — padrão igual ao antigo whatsapp_service.
telegram_service = TelegramService()