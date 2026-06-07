"""
Rotas unificadas de webhook para todos os provedores de pagamento.
Endpoint: /api/webhooks/{provider}
"""
from flask import Blueprint, request, jsonify
import logging

from services.webhook_handler import webhook_handler
from services.feature_flag_service import FeatureFlagService

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/<provider>', methods=['POST'])
def receber_webhook(provider):
    """
    Recebe webhooks de Mercado Pago, Stripe ou Asaas.
    """
    if not FeatureFlagService.is_enabled("new_billing_v2"):
        return jsonify({"status": "ignored", "reason": "new_billing_v2 desativado"}), 200

    provider = provider.lower()
    if provider not in ("mercadopago", "stripe", "asaas"):
        return jsonify({"error": "Provedor não suportado"}), 400

    payload = request.get_json(silent=True) or {}
    if not payload:
        # Tentar form data
        payload = dict(request.form)

    logger.info(f"Webhook recebido de {provider}: {payload}")

    resultado = webhook_handler.process(provider, payload)
    if resultado.get("success"):
        return jsonify({"status": "ok", "idempotent": resultado.get("idempotent", False)}), 200
    else:
        # Retornar 200 mesmo em erro para evitar reenvios agressivos dos providers
        logger.error(f"Erro no webhook {provider}: {resultado.get('error')}")
        return jsonify({"status": "error", "error": resultado.get("error")}), 200
