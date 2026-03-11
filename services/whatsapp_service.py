import requests
import os
import logging

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_url = os.environ.get('WHATSAPP_API_URL', 'http://localhost:8080')
        self.instance_name = os.environ.get('WHATSAPP_INSTANCE_NAME', 'siap')
        self.api_key = os.environ.get('WHATSAPP_API_KEY')
        self.admin_phone = os.environ.get('WHATSAPP_ADMIN_PHONE') # Telefone do Super Admin

    def send_message(self, phone, message):
        """
        Envia mensagem de texto via Evolution API
        """
        if not self.api_key:
            logger.warning("WHATSAPP_API_KEY não configurada. Mensagem não enviada.")
            return False

        if not phone:
             logger.warning("Telefone de destino não fornecido.")
             return False

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
            "options": {
                "delay": 1200,
                "presence": "composing",
                "linkPreview": False
            },
            "textMessage": {
                "text": message
            }
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 201 or response.status_code == 200:
                 logger.info(f"Mensagem WhatsApp enviada para {phone}")
                 return True
            else:
                 logger.error(f"Erro ao enviar WhatsApp: {response.text}")
                 return False
        except Exception as e:
            logger.error(f"Exceção ao enviar WhatsApp: {e}")
            return False

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
            f"Seu cadastro no *Aracannabis Prontuário* foi aprovado! ✅\n\n"
            f"Você já pode acessar seu consultório virtual e começar a atender.\n"
            f"Se tiver dúvidas, estamos à disposição."
        )
        self.send_message(phone, msg)
