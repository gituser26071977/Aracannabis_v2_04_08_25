from flask import Blueprint, request, jsonify
import logging
import threading

from models import ConfiguracaoIA
from services.dynamic_tenant_agent import DynamicTenantAgent
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

tenant_webhook_bp = Blueprint('tenant_webhook', __name__)

@tenant_webhook_bp.route('/webhook', methods=['POST'])
def evolution_webhook_multi_tenant():
    """
    Recebe eventos da Evolution API para TODAS as instâncias conectadas.
    Ele consulta o banco de dados para ver de qual médico é aquela instância.
    """
    data = request.json
    
    event = data.get('event')
    if event != 'messages.upsert':
        return jsonify({"status": "ignored", "reason": "not_upsert"}), 200

    instance_name = data.get('instance')
    if not instance_name:
        return jsonify({"status": "ignored", "reason": "no_instance_name"}), 200

    # 1. Buscar configuração da IA correspondente a esta instância no DB
    config = ConfiguracaoIA.query.filter_by(instance_name=instance_name).first()
    
    if not config or not config.ativo:
        # A clínica não ativou a IA ou a instância não bate com o banco.
        return jsonify({"status": "ignored", "reason": "ai_not_configured_or_inactive"}), 200

    message_data = data.get('data', {})
    if isinstance(message_data, list):
        if not message_data:
            return jsonify({"status": "empty_list"}), 200
        message_data = message_data[0]

    key = message_data.get('key', {})
    if key.get('fromMe', False):
        return jsonify({"status": "ignored", "reason": "sent_by_me"}), 200

    remote_jid = key.get('remoteJid', '')
    phone = remote_jid.split('@')[0]

    if 'g.us' in remote_jid:
        return jsonify({"status": "ignored", "reason": "group_message"}), 200

    message_body = message_data.get('message', {})
    
    # Extrair texto da mensagem
    content = ""
    if 'conversation' in message_body:
        content = message_body['conversation']
    elif 'extendedTextMessage' in message_body:
        content = message_body['extendedTextMessage'].get('text', '')

    # Extrair captions de imagens/documentos
    if 'imageMessage' in message_body:
        caption = message_body['imageMessage'].get('caption', '')
        content = f"{content} {caption} [IMAGEM RECEBIDA]".strip()
    elif 'documentMessage' in message_body:
        caption = message_body['documentMessage'].get('caption', '')
        content = f"{content} {caption} [DOCUMENTO RECEBIDO]".strip()

    if not content:
        content = "[MENSAGEM DE TIPO DESCONHECIDO/ÁUDIO]"

    # 2. Processar assincronamente injetando o contexto do Tenants
    def process_async(prof_id, inst_name, user_phone, user_msg):
        try:
            logger.info(f"[Multi-Tenant Webhook] Atendendo {user_phone} para Prof{prof_id} via {inst_name}")
            
            # Instancia o motor genérico com os dados daquele médico específico
            agent = DynamicTenantAgent(profissional_id=prof_id)
            reply = agent.process_message(message=user_msg, phone=user_phone)
            
            # Envia a resposta usando a instância WhatsApp correta da Evolution API
            whatsapp = WhatsAppService(instance_name=inst_name)
            whatsapp.send_message(phone=user_phone, message=reply)
            
        except Exception as e:
            logger.error(f"[Multi-Tenant Webhook] Erro fatal: {e}")

    threading.Thread(
        target=process_async, 
        args=(config.profissional_id, instance_name, phone, content)
    ).start()

    return jsonify({"status": "received", "message": "Dispatched to DynamicTenantAgent"}), 200
