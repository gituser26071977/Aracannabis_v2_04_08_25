"""Gateway de WhatsApp com providers plugáveis.

Suporta:
    - Meta WhatsApp Cloud API (oficial): texto livre (janela de 24h) e
      template (mensagens iniciadas pela empresa).
    - Evolution API (legado/self-hosted): texto livre.

Seleção por `WHATSAPP_PROVIDER` ("meta" | "evolution" | "auto").
Nunca lança: falha de envio retorna False e é registrada em log.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_META_BASE = "https://graph.facebook.com"


def normalize_phone(phone: str, default_country: str = "55") -> str:
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    if not digits:
        return ""
    if default_country and not digits.startswith(default_country) and len(digits) <= 11:
        digits = default_country + digits
    return digits


class WhatsAppGateway:
    def __init__(
        self,
        *,
        provider: Optional[str] = None,
        session: Optional[Any] = None,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: Optional[str] = None,
        template_name: Optional[str] = None,
        template_lang: Optional[str] = None,
        evolution_url: Optional[str] = None,
        evolution_instance: Optional[str] = None,
        evolution_key: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        self.provider = (provider or os.getenv("WHATSAPP_PROVIDER", "auto")).lower()
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.api_version = api_version or os.getenv("WHATSAPP_API_VERSION", "v21.0")
        self.template_name = template_name or os.getenv("WHATSAPP_TEMPLATE_NAME")
        self.template_lang = template_lang or os.getenv("WHATSAPP_TEMPLATE_LANG", "pt_BR")
        self.evolution_url = (evolution_url or os.getenv("WHATSAPP_API_URL", "")).rstrip("/")
        self.evolution_instance = evolution_instance or os.getenv("WHATSAPP_INSTANCE_NAME", "siap")
        self.evolution_key = evolution_key or os.getenv("WHATSAPP_API_KEY")
        self.timeout = timeout
        self._session = session

    def _resolve_provider(self) -> Optional[str]:
        if self.provider in ("meta", "evolution"):
            return self.provider
        if self.phone_number_id and self.access_token:
            return "meta"
        if self.evolution_url and self.evolution_key:
            return "evolution"
        return None

    def is_configured(self) -> bool:
        return self._resolve_provider() is not None

    @property
    def resolved_provider(self) -> Optional[str]:
        return self._resolve_provider()

    def _post(self, url: str, *, json: Dict[str, Any], headers: Dict[str, str]) -> Optional[Any]:
        requester = self._session or __import__("requests")
        response = requester.post(url, json=json, headers=headers, timeout=self.timeout)
        if response.status_code in (200, 201):
            return response
        logger.error("whatsapp_send_failed status=%s body=%s", response.status_code, response.text)
        return None

    def send_text(self, to: str, text: str) -> bool:
        provider = self._resolve_provider()
        if provider is None:
            logger.warning("WhatsApp não configurado; mensagem não enviada.")
            return False
        phone = normalize_phone(to)
        if not phone:
            logger.warning("Telefone de destino inválido.")
            return False

        if provider == "meta":
            url = f"{_META_BASE}/{self.api_version}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone,
                "type": "text",
                "text": {"preview_url": True, "body": text},
            }
        else:
            url = f"{self.evolution_url}/message/sendText/{self.evolution_instance}"
            headers = {"apikey": self.evolution_key or "", "Content-Type": "application/json"}
            payload = {"number": phone, "delay": 1200, "text": text}

        try:
            return self._post(url, json=payload, headers=headers) is not None
        except Exception as exc:  # noqa: BLE001
            logger.error("whatsapp_gateway_error: %s", exc)
            return False

    def send_template(
        self,
        to: str,
        *,
        template_name: Optional[str] = None,
        lang: Optional[str] = None,
        body_variables: Optional[List[str]] = None,
        url_button_suffix: Optional[str] = None,
    ) -> bool:
        provider = self._resolve_provider()
        name = template_name or self.template_name
        if provider != "meta" or not name:
            return self.send_text(to, (body_variables or [""])[0])

        phone = normalize_phone(to)
        if not phone:
            return False
        url = f"{_META_BASE}/{self.api_version}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        components: List[Dict[str, Any]] = []
        if body_variables:
            components.append(
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": v} for v in body_variables],
                }
            )
        if url_button_suffix:
            components.append(
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": url_button_suffix}],
                }
            )
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": name,
                "language": {"code": lang or self.template_lang},
                "components": components,
            },
        }
        try:
            return self._post(url, json=payload, headers=headers) is not None
        except Exception as exc:  # noqa: BLE001
            logger.error("whatsapp_template_error: %s", exc)
            return False


def default_gateway() -> WhatsAppGateway:
    return WhatsAppGateway()
