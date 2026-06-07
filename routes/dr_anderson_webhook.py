from flask import Blueprint, request, jsonify
import logging
import os
from services.dr_anderson_agent import dr_anderson_agent
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

dr_anderson_bp = Blueprint('dr_anderson_webhook', __name__)

# Instância dedicada para o Dr Anderson
dr_anderson_instance = os.environ.get('DR_ANDERSON_WHATSAPP_INSTANCE', 'dr_anderson')
whatsapp = WhatsAppService(instance_name=dr_anderson_instance)

INTERNAL_SERVICE_KEY = os.environ.get('INTERNAL_SERVICE_KEY', 'dr-anderson-internal-key')


# ──────────────────────────────────────────────
# Endpoint interno: Criação de Lead/Paciente
# ──────────────────────────────────────────────

@dr_anderson_bp.route('/criar-lead', methods=['POST'])
def criar_lead():
    """
    Endpoint interno para o Agente criar automaticamente a ficha do paciente no SIAP.
    Autenticado por chave de serviço interna (X-Internal-Key).
    """
    key = request.headers.get('X-Internal-Key', '')
    if key != INTERNAL_SERVICE_KEY:
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON obrigatório"}), 400

    nome = data.get("nome", "").strip()
    if not nome:
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

    data_nascimento_str = data.get("data_nascimento", "1990-01-01")

    try:
        from models import db, Paciente, Profissional
        from datetime import datetime

        # Buscar Dr. Anderson pelo nome ou usar primeiro admin disponível
        dr_anderson = Profissional.query.filter(
            Profissional.nome.ilike('%anderson%')
        ).first()

        if not dr_anderson:
            dr_anderson = Profissional.query.filter(
                Profissional.role.in_(['admin', 'superadmin'])
            ).first()

        if not dr_anderson:
            dr_anderson = Profissional.query.first()

        if not dr_anderson:
            return jsonify({"error": "Nenhum profissional cadastrado para ser responsável"}), 500

        data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date()

        observacoes_completas = data.get('observacoes', '')
        historico_cannabis = data.get('historico_cannabis') or data.get('historico')
        if historico_cannabis:
            observacoes_completas += f"\n\nHistórico Cannabis: {historico_cannabis}"
        observacoes_completas += "\n\n[Lead captado automaticamente via WhatsApp - Agente LIA Dr. Anderson]"

        novo_paciente = Paciente(
            profissional_responsavel_id=dr_anderson.id,
            nome=nome,
            data_nascimento=data_nascimento,
            telefone=data.get('telefone', ''),
            email=data.get('email', ''),
            diagnostico=data.get('diagnostico', ''),
            observacoes=observacoes_completas.strip(),
            em_tratamento=False,
            consentimento_lgpd=True,
            data_consentimento=datetime.utcnow(),
        )

        db.session.add(novo_paciente)
        db.session.commit()

        logger.info(f"[Dr. Anderson Agent] Paciente criado no SIAP: {nome} (ID {novo_paciente.id})")

        return jsonify({
            "success": True,
            "paciente_id": novo_paciente.id,
            "nome": novo_paciente.nome,
        }), 201

    except Exception as e:
        logger.error(f"Erro ao criar lead no SIAP: {e}")
        try:
            from models import db
            db.session.rollback()
        except Exception:
            pass
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────
# Webhook Evolution API
# ──────────────────────────────────────────────

@dr_anderson_bp.route('/webhook', methods=['POST'])
def evolution_webhook():
    """
    Recebe eventos da Evolution API.
    Configure na Evolution API apontando para /api/dr-anderson/webhook
    """
    data = request.json

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

    if 'g.us' in remote_jid:
        return jsonify({"status": "ignored", "reason": "group_message"}), 200

    message_body = message_data.get('message', {})

    # Extrair texto
    content = ""
    if 'conversation' in message_body:
        content = message_body['conversation']
    elif 'extendedTextMessage' in message_body:
        content = message_body['extendedTextMessage'].get('text', '')

    # Detectar mídia (imagem/documento)
    media_base64 = None
    mime_type = None
    if 'imageMessage' in message_body:
        caption = message_body['imageMessage'].get('caption', '')
        content = f"{content} {caption}".strip()
        # Se a Evolution mandar base64 direto (configurável)
        media_base64 = message_body['imageMessage'].get('base64')
        mime_type = message_body['imageMessage'].get('mimetype', 'image/jpeg')
    elif 'documentMessage' in message_body:
        caption = message_body['documentMessage'].get('caption', '')
        content = f"{content} {caption}".strip()
        media_base64 = message_body['documentMessage'].get('base64')
        mime_type = message_body['documentMessage'].get('mimetype', 'application/pdf')

    if not content:
        content = "(Mensagem sem texto)"

    def process_async():
        try:
            print(f"DEBUG: [Dr. Anderson Webhook] Processando em background: {phone}", flush=True)
            reply = dr_anderson_agent.process_message(
                message=content,
                phone=phone,
                media_base64=media_base64,
                mime_type=mime_type,
            )
            whatsapp.send_message(phone=phone, message=reply)
            print(f"DEBUG: [Dr. Anderson Webhook] Resposta enviada para {phone}", flush=True)
        except Exception as e:
            print(f"DEBUG: [Dr. Anderson Webhook] Erro no background: {e}", flush=True)

    # Iniciar processamento em background e responder 200 OK imediatamente
    import threading
    threading.Thread(target=process_async).start()

    return jsonify({"status": "received", "message": "Processing in background"}), 200
