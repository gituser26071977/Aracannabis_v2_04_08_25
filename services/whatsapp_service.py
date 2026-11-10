import requests
import os
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self, instance_name: str = None):
        self.api_url = os.environ.get('WHATSAPP_API_URL', 'http://localhost:8080')
        # A instância ativa no Evolution pode estar configurada em
        # WHATSAPP_INSTANCE_NAME ou, no deploy atual, em
        # DR_ANDERSON_WHATSAPP_INSTANCE (ex.: "EuSouLIA").
        self.instance_name = (
            instance_name
            or os.environ.get('WHATSAPP_INSTANCE_NAME')
            or os.environ.get('DR_ANDERSON_WHATSAPP_INSTANCE')
            or 'siap'
        )
        self.api_key = os.environ.get('WHATSAPP_API_KEY')
        self.admin_phone = os.environ.get('WHATSAPP_ADMIN_PHONE') # Telefone do Super Admin

    def send_text(self, phone, message):
        """
        Envia mensagem de texto via Evolution API.

        Retorna um dict: {ok, status_code, data, provider_id, erro}.
        """
        if not self.api_key:
            logger.warning("WHATSAPP_API_KEY não configurada. Mensagem não enviada.")
            return {"ok": False, "erro": "WHATSAPP_API_KEY não configurada"}

        if not phone:
            logger.warning("Telefone de destino não fornecido.")
            return {"ok": False, "erro": "Telefone de destino não fornecido"}

        # Formatar telefone (ex: remover +)
        phone = phone.replace('+', '').replace('-', '').replace(' ', '')
        # Garantir DDI 55 se não tiver (assumindo Brasil por padrão para este sistema)
        if len(phone) <= 11 and not phone.startswith('55'):
            phone = '55' + phone

        url = f"{self.api_url}/message/sendText/{self.instance_name}"
        headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "number": phone,
            "delay": 1200,
            "text": message
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            try:
                data = response.json()
            except Exception:  # noqa: BLE001
                data = None

            ok = response.status_code in (201, 200)
            provider_id = None
            if isinstance(data, dict):
                provider_id = (data.get("key") or {}).get("id")

            if ok:
                logger.info(f"Mensagem WhatsApp enviada para {phone}")
            else:
                logger.error(f"Erro ao enviar WhatsApp: {response.text}")

            return {
                "ok": ok,
                "status_code": response.status_code,
                "data": data,
                "provider_id": provider_id,
                "erro": None if ok else response.text[:500],
            }
        except Exception as e:
            logger.error(f"Exceção ao enviar WhatsApp: {e}")
            return {"ok": False, "erro": str(e)}

    def send_message(self, phone, message):
        """Compatibilidade: envia texto e retorna bool."""
        return bool(self.send_text(phone, message).get("ok"))

    def check_numbers(self, numbers):
        """Consulta na Evolution se os números existem no WhatsApp.

        Retorna um dict {numero: {"exists": bool, "jid": str, ...}}.
        Números ausentes no retorno são considerados inexistentes.
        """
        if not self.api_key or not numbers:
            return {}
        url = f"{self.api_url}/chat/whatsappNumbers/{self.instance_name}"
        headers = {"apikey": self.api_key, "Content-Type": "application/json"}
        try:
            response = requests.post(
                url, headers=headers, json={"numbers": list(numbers)}, timeout=20
            )
            if response.status_code != 200:
                logger.error(
                    "Erro ao verificar números no WhatsApp: %s", response.text[:300]
                )
                return {}
            data = response.json()
            if not isinstance(data, list):
                return {}
            return {
                str(item.get("number")): item
                for item in data
                if isinstance(item, dict)
            }
        except Exception as e:  # noqa: BLE001
            logger.error("Exceção ao verificar números no WhatsApp: %s", e)
            return {}

    def notify_admin_new_registration(self, nome, email, crm, uf_crm, auto_approved=False):
        """
        Notifica o admin sobre novo cadastro
        """
        if not self.admin_phone:
             logger.warning("WHATSAPP_ADMIN_PHONE não configurado.")
             return

        status_text = "✅ *APROVADO AUTOMATICAMENTE*" if auto_approved else "⚠️ *AGUARDANDO APROVAÇÃO*"
        
        msg = (
            f"🔔 *Novo Cadastro de Médico*\n\n"
            f"Nome: {nome}\n"
            f"CRM: {crm}/{uf_crm}\n"
            f"Email: {email}\n"
            f"Status: {status_text}\n\n"
            f"🔍 *Validar no CFM:* https://portal.cfm.org.br/busca-medicos\n\n"
            f"Acesse o painel para detalhes."
        )
        self.send_message(self.admin_phone, msg)

    def notify_doctor_approval(self, phone, nome):
        """
        Notifica o médico que seu cadastro foi aprovado
        """
        if not phone:
            return
            
        msg = (
            f"Olá Dr(a). {nome}, tudo bem? 👋\n\n"
            f"Seu cadastro no *AraOS* foi aprovado! ✅\n\n"
            f"Você já pode acessar seu consultório virtual e começar a atender.\n"
            f"Se tiver dúvidas, estamos à disposição."
        )
        self.send_message(phone, msg)


whatsapp_service = WhatsAppService()
