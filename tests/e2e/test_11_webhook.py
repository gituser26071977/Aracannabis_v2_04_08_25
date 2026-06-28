"""E2E — Fluxo 11: Webhook (simulação via API)"""
import json
import hmac
import hashlib
import os
import requests

def test_webhook_mercadopago_signature(base_url):
    """POST /api/webhooks/mercadopago com assinatura válida deve retornar 200/4xx (nunca 500)."""
    payload = {"type": "payment", "data": {"id": "12345"}}
    body = json.dumps(payload).encode()
    secret = os.environ.get("MERCADOPAGO_WEBHOOK_SECRET", "staging_test_secret_32_chars_xxx")
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    r = requests.post(
        f"{base_url}/api/webhooks/mercadopago",
        data=body,
        headers={"Content-Type": "application/json", "x-signature": f"sha256={sig}"},
        timeout=10,
    )
    # 200 (processado) ou 4xx (rejeitado por regra de negócio) — nunca 5xx
    assert r.status_code < 500, f"Webhook retornou {r.status_code}: {r.text}"
