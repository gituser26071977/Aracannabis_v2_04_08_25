from flask import Blueprint, request, jsonify
import logging
import os
from services.dr_anderson_agent import dr_anderson_agent
from services.telegram_service import telegram_service
from services.webhook_auth import register_webhook_event
from security_config import limiter

logger = logging.getLogger(__name__)

dr_anderson_bp = Blueprint('dr_anderson_webhook', __name__)

# Chat ID Telegram fixo do Dr. Anderson (substitui WhatsApp instance dr_anderson)
DR_ANDERSON_TELEGRAM_CHAT_ID = os.environ.get(
    "DR_ANDERSON_TELEGRAM_CHAT_ID", ""
).strip()


# ──────────────────────────────────────────────
# Endpoint interno: Criação de Lead/Paciente
# ──────────────────────────────────────────────

from services.webhook_auth import internal_key_required  # noqa: E402


@dr_anderson_bp.route('/criar-lead', methods=['POST'])
@limiter.exempt  # FASE 5A — endpoint interno autenticado por X-Internal-Key
@internal_key_required(env_var="INTERNAL_SERVICE_KEY")
def criar_lead():
    """
    Endpoint interno para o Agente criar automaticamente a ficha do paciente no SIAP.
    Autenticado por chave de serviço interna (X-Internal-Key).
    """
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

        # Usar o profissional informado pelo agente (multi-tenant), com fallback
        # para o Dr. Anderson / primeiro admin (legado).
        profissional_id = data.get('profissional_id')
        dr_anderson = None
        if profissional_id:
            dr_anderson = Profissional.query.get(int(profissional_id))
        if not dr_anderson:
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
            observacoes_completas += f"\n\nHistórico: {historico_cannabis}"
        observacoes_completas += "\n\n[Pré-atendimento captado automaticamente via Agente LIA]"

        # TODO P1-LGPD: revisar criacao automatica de consentimento.
        # O consentimento_lgpd=True abaixo e setado sem aceite real do titular.
        # Em P1, este endpoint deve exigir aceite explicito via portal do titular
        # (art. 8o LGPD) e criar o paciente com consentimento_lgpd=False ate
        # que o titular aceite.
        novo_paciente = Paciente(
            profissional_responsavel_id=dr_anderson.id,
            nome=nome,
            data_nascimento=data_nascimento,
            telefone=data.get('telefone', ''),
            email=data.get('email', ''),
            diagnostico=data.get('diagnostico', ''),
            observacoes=observacoes_completas.strip(),
            em_tratamento=False,
            associacao_id=data.get('associacao_id') or None,
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
# Webhook Telegram — substitui Evolution API (D05k)
# ──────────────────────────────────────────────

@dr_anderson_bp.route('/webhooks/telegram', methods=['POST'])
@limiter.exempt  # FASE 5A — webhook validado por X-Telegram-Bot-Api-Secret-Token
def telegram_webhook():
    """
    Recebe Update do Telegram Bot API para o bot dedicado do Dr. Anderson.

    Validação: header X-Telegram-Bot-Api-Secret-Token comparado via
    compare_digest contra REDACTED.

    Configurar no BotFather/setWebhook o header
    `secret_token=<REDACTED>` apontando para
    https://api.visualsmartflow.com.br/api/dr-anderson/webhooks/telegram.
    """
    import hmac

    # Validação do secret header do Telegram
    expected_secret = os.environ.get(
        "REDACTED", ""
    ).strip()
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")

    if not expected_secret:
        logger.error(
            "[dr_anderson_telegram_webhook] REDACTED "
            "nao configurado"
        )
        return jsonify({"error": "server misconfigured"}), 500
    if not header_secret or not hmac.compare_digest(
        header_secret, expected_secret
    ):
        logger.warning(
            f"[dr_anderson_telegram_webhook] secret invalido (ip={request.remote_addr})"
        )
        return jsonify({"error": "unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    message = data.get("message") or data.get("edited_message")
    if not message:
        return jsonify({"status": "ignored", "reason": "no_message"}), 200

    # Anti-replay atomico via UNIQUE(provider, provider_event_id)
    update_id = data.get("update_id", "")
    event_id = f"telegram_dr_anderson:{update_id}"
    is_replay, _ = register_webhook_event(
        provider="telegram_dr_anderson",
        event_id=event_id,
        event_type="telegram_update",
        payload=data,
    )
    if is_replay:
        logger.info(
            f"[dr_anderson_telegram_webhook] replay detectado update_id={update_id}"
        )
        return jsonify({"status": "ok", "idempotent": True}), 200

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    chat_type = chat.get("type", "private")
    if chat_type in ("group", "supergroup", "channel"):
        return jsonify({"status": "ignored", "reason": "group_message"}), 200
    if not chat_id:
        return jsonify({"status": "ignored", "reason": "no_chat_id"}), 200

    text = message.get("text") or message.get("caption") or ""
    if not text:
        # Mídia sem caption: ignora por enquanto (Telegram entrega mídia por
        # file_id, diferente do base64 inline do Evolution)
        return jsonify({"status": "ignored", "reason": "no_text"}), 200

    phone = str(chat_id)

    def process_async():
        try:
            print(
                f"[Dr. Anderson Telegram Webhook] Processando em background: {phone}",
                flush=True,
            )
            reply = dr_anderson_agent.process_message(message=text, phone=phone)
            telegram_service.send_message(chat_id=phone, text=reply)
            print(
                f"[Dr. Anderson Telegram Webhook] Resposta enviada para {phone}",
                flush=True,
            )
        except Exception as e:
            print(
                f"[Dr. Anderson Telegram Webhook] Erro no background: {e}",
                flush=True,
            )

    import threading
    threading.Thread(target=process_async).start()

    return jsonify({"status": "received", "message": "Processing in background"}), 200


# Backward-compat: rota antiga Evolution retorna 410 Gone.
@dr_anderson_bp.route('/webhook', methods=['POST'])
def evolution_webhook_legacy():
    """DEPRECATED (D05k): Evolution API descontinuada."""
    return jsonify({
        "error": "endpoint_removed",
        "reason": "evolution_api_migrated_to_telegram",
        "new_endpoint": "/api/dr-anderson/webhooks/telegram",
    }), 410