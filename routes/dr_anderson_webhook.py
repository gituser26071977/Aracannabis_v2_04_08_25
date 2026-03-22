from flask import Blueprint, request, jsonify
import logging
import os
from services.dr_anderson_agent import DrAndersonAgent
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

dr_anderson_bp = Blueprint('dr_anderson_webhook', __name__)
agent = DrAndersonAgent()
# Instância dedicada para a secretária virtual do Dr Anderson
dr_anderson_instance = os.environ.get('DR_ANDERSON_WHATSAPP_INSTANCE', 'dr_anderson')
whatsapp = WhatsAppService(instance_name=dr_anderson_instance)

@dr_anderson_bp.route('/webhook', methods=['POST'])
def evolution_webhook():
    """
    Recebe eventos da Evolution API.
    A URL de webhook deve ser configurada na Evolution API apontando para /api/dr-anderson/webhook
    """
    data = request.json
    
    # Validações básicas da Evolution API
    event = data.get('event')
    if event != 'messages.upsert':
        return jsonify({"status": "ignored", "reason": "not_upsert"}), 200
        
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
    if 'g.us' in remote_jid: # Ignorar mensagens em grupo
        return jsonify({"status": "ignored", "reason": "group_message"}), 200

    message_body = message_data.get('message', {})
    
    # Extrair texto
    content = ""
    if 'conversation' in message_body:
        content = message_body['conversation']
    elif 'extendedTextMessage' in message_body:
        content = message_body['extendedTextMessage'].get('text', '')
    
    # Detectar mídia
    media_base64 = None
    mime_type = None
    
    # Em um cenário completo, buscaríamos o base64 da Evolution API via chamada de getMedia
    # Aqui vamos tentar extrair caso a evolution já mande no webhook padrão
    if 'imageMessage' in message_body or 'documentMessage' in message_body:
        # Nota: Normalmente a Evolution API precisa ser chamada de volta para baixar o arquivo
        # Para a versão simplificada, detectamos a mídia e o caption
        if 'imageMessage' in message_body:
            caption = message_body['imageMessage'].get('caption', '')
            content = f"{content} {caption}".strip()
    
    if not content:
        content = "Mensagem recebida sem texto"

    try:
        # Processar com a agente "Lia"
        logger.info(f"Dr. Anderson Agent Processando: {phone} - {content[:50]}...")
        reply = agent.process_message(message=content, phone=phone)
        
        # Enviar resposta usando o serviço existente no SIAP
        success = whatsapp.send_message(phone=phone, message=reply)
        
        return jsonify({
            "status": "processed",
            "reply_sent": success
        }), 200
        
    except Exception as e:
        logger.error(f"Erro no webhook Dr Anderson: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
