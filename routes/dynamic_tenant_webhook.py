from flask import Blueprint, request, jsonify
import logging
import threading

from models import ConfiguracaoIA
from services.dynamic_tenant_agent import DynamicTenantAgent
from services.telegram_service import TelegramService
from services.webhook_auth import register_webhook_event
from security_config import limiter

logger = logging.getLogger(__name__)

tenant_webhook_bp = Blueprint('tenant_webhook', __name__)


@tenant_webhook_bp.route('/webhooks/telegram', methods=['POST'])
@limiter.exempt  # FASE 5A — webhook validado por X-Telegram-Bot-Api-Secret-Token
def telegram_webhook_multi_tenant():
    """
    Recebe Update do Telegram para múltiplos tenants (cada clínica = 1 bot).

    Auth: header X-Telegram-Bot-Api-Secret-Token comparado contra o secret
    do tenant que estiver cadastrado em ConfiguracaoIA. Sem match → 401.

    Multi-tenant: o token do bot identifica o tenant (cada bot dedicado aponta
    para este mesmo endpoint; o Telegram envia X-Telegram-Bot-Api-Secret-Token
    e validamos contra ConfiguracaoIA.telegram_webhook_secret).
    """
    import hmac

    data = request.get_json(silent=True) or {}
    message = data.get("message") or data.get("edited_message")
    if not message:
        return jsonify({"status": "ignored", "reason": "no_message"}), 200

    # Anti-replay atomico via UNIQUE(provider, provider_event_id).
    update_id = data.get("update_id", "")
    event_id = f"telegram_tenant:{update_id}"
    is_replay, _ = register_webhook_event(
        provider="telegram_tenant",
        event_id=event_id,
        event_type="telegram_update",
        payload=data,
    )
    if is_replay:
        logger.info(
            f"[telegram_tenant_webhook] replay detectado update_id={update_id}"
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
        return jsonify({"status": "ignored", "reason": "no_text"}), 200

    # Identifica tenant via header secret: bate contra ConfiguracaoIA.telegram_webhook_secret
    header_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    config = _resolve_tenant_by_secret(header_secret)
    if not config or not config.ativo:
        # Tenant nao cadastrado / bot nao provisionado
        logger.warning(
            f"[telegram_tenant_webhook] tenant nao encontrado ou inativo "
            f"(ip={request.remote_addr})"
        )
        return jsonify({"error": "unauthorized"}), 401

    phone = str(chat_id)

    def process_async(prof_id, inst_token, user_phone, user_msg):
        try:
            logger.info(
                f"[Multi-Tenant Telegram Webhook] Atendendo {user_phone} "
                f"para Prof{prof_id}"
            )
            agent = DynamicTenantAgent(profissional_id=prof_id)
            reply = agent.process_message(message=user_msg, phone=user_phone)

            # Envia resposta usando o token do bot dedicado da clínica
            svc = TelegramService(bot_token=inst_token)
            svc.send_message(chat_id=user_phone, text=reply)
        except Exception as e:
            logger.error(f"[Multi-Tenant Telegram Webhook] Erro fatal: {e}")

    threading.Thread(
        target=process_async,
        args=(config.profissional_id, config.telegram_bot_token, phone, text),
    ).start()

    return jsonify({"status": "received", "message": "Dispatched to DynamicTenantAgent"}), 200


def _resolve_tenant_by_secret(provided_secret: str):
    """Busca ConfiguracaoIA cujo telegram_webhook_secret bate com o header.

    Multi-tenant: cada bot dedicado tem seu próprio secret no setWebhook.
    """
    if not provided_secret:
        return None
    # Itera sobre todas as configs (volume baixo; indice dedicado pode ser
    # adicionado se a tabela crescer muito)
    for cfg in ConfiguracaoIA.query.filter(ConfiguracaoIA.telegram_webhook_secret.isnot(None)).all():
        import hmac as _hmac
        if _hmac.compare_digest(provided_secret, cfg.telegram_webhook_secret or ""):
            return cfg
    return None


# Backward-compat: rota antiga Evolution retorna 410 Gone.
@tenant_webhook_bp.route('/webhook', methods=['POST'])
def evolution_webhook_legacy():
    """DEPRECATED (D05k): Evolution API descontinuada."""
    return jsonify({
        "error": "endpoint_removed",
        "reason": "evolution_api_migrated_to_telegram",
        "new_endpoint": "/api/tenant/webhooks/telegram",
    }), 410