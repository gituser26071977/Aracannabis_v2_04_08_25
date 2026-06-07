"""
Provider Mercado Pago — suporta Preferences (pagamento único) e Preapproval (recorrência).
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .base import IPaymentProvider, CustomerResult, SubscriptionResult, InvoiceResult

logger = logging.getLogger(__name__)


class MercadoPagoProvider(IPaymentProvider):
    def __init__(self):
        self.access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
        self.public_key = os.getenv("MERCADOPAGO_PUBLIC_KEY")
        self.sandbox = os.getenv("MERCADOPAGO_SANDBOX", "True").lower() == "true"
        self.base_url = "https://api.mercadopago.com"
        self._sdk = None

        if self.access_token:
            try:
                import mercadopago
                self._sdk = mercadopago.SDK(self.access_token)
            except Exception as e:
                logger.warning(f"SDK Mercado Pago não disponível: {e}")

    @property
    def name(self) -> str:
        return "mercadopago"

    def is_configured(self) -> bool:
        return bool(self.access_token)

    def _request(self, method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        import requests
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        try:
            resp = requests.request(method, url, headers=headers, json=json_data, timeout=30)
            return {"success": resp.status_code in (200, 201, 204), "status_code": resp.status_code, "data": resp.json() if resp.text else {}}
        except Exception as e:
            logger.error(f"Erro na requisição MP {method} {endpoint}: {e}")
            return {"success": False, "error": str(e)}

    def create_customer(self, email: str, name: str, doc: Optional[str] = None, **kwargs) -> CustomerResult:
        if not self.is_configured():
            return CustomerResult(success=False, error="Mercado Pago não configurado")
        payload = {"email": email, "first_name": name}
        if doc:
            payload["identification"] = {"type": "CPF", "number": doc}
        result = self._request("POST", "/v1/customers", payload)
        if result["success"]:
            data = result.get("data", {})
            return CustomerResult(success=True, customer_id=str(data.get("id")), email=email, raw=data)
        return CustomerResult(success=False, error=result.get("error", "Erro ao criar customer"), raw=result)

    def create_subscription(
        self,
        customer_id: str,
        plan_identifier: str,
        periodicity: str,
        amount: float,
        description: str,
        **kwargs
    ) -> SubscriptionResult:
        if not self.is_configured():
            return SubscriptionResult(success=False, error="Mercado Pago não configurado")

        # Mercado Pago Preapproval API para recorrência
        frequency, frequency_type = self._map_periodicity(periodicity)
        payload = {
            "preapproval_plan_id": None,
            "reason": description,
            "external_reference": kwargs.get("external_reference", ""),
            "payer_email": kwargs.get("payer_email", ""),
            "card_token_id": kwargs.get("card_token_id"),
            "auto_recurring": {
                "frequency": frequency,
                "frequency_type": frequency_type,
                "transaction_amount": float(amount),
                "currency_id": "BRL",
            },
            "back_url": kwargs.get("back_url", "https://app.aracannabis.com.br/pagamento-sucesso"),
            "status": "pending",
        }
        result = self._request("POST", "/preapproval", payload)
        if result["success"]:
            data = result.get("data", {})
            next_billing = None
            if data.get("auto_recurring", {}).get("end_date"):
                try:
                    next_billing = datetime.fromisoformat(data["auto_recurring"]["end_date"].replace("Z", "+00:00"))
                except Exception:
                    pass
            return SubscriptionResult(
                success=True,
                subscription_id=str(data.get("id")),
                status=data.get("status", "pending"),
                next_billing_date=next_billing,
                checkout_url=data.get("init_point") or data.get("sandbox_init_point"),
                raw=data,
            )
        return SubscriptionResult(success=False, error=result.get("error", "Erro ao criar assinatura"), raw=result)

    def create_invoice(
        self,
        customer_id: str,
        amount: float,
        description: str,
        due_days: int = 3,
        method: str = "pix",
        **kwargs
    ) -> InvoiceResult:
        if not self.is_configured():
            return InvoiceResult(success=False, error="Mercado Pago não configurado")

        # Preferência de pagamento (pagamento único)
        payload = {
            "items": [
                {
                    "title": description,
                    "quantity": 1,
                    "currency_id": "BRL",
                    "unit_price": float(amount),
                }
            ],
            "payer": {"email": kwargs.get("payer_email", ""), "name": kwargs.get("payer_name", "")},
            "external_reference": kwargs.get("external_reference", ""),
            "notification_url": kwargs.get("notification_url"),
            "payment_methods": {"excluded_payment_types": [] if method == "card" else [{"id": "credit_card"}, {"id": "debit_card"}]},
        }

        if method == "pix":
            payload["payment_methods"]["excluded_payment_types"] = [{"id": "credit_card"}, {"id": "debit_card"}, {"id": "ticket"}]
        elif method == "boleto":
            payload["payment_methods"]["excluded_payment_types"] = [{"id": "credit_card"}, {"id": "debit_card"}, {"id": "bank_transfer"}]

        result = self._request("POST", "/checkout/preferences", payload)
        if result["success"]:
            data = result.get("data", {})
            return InvoiceResult(
                success=True,
                invoice_id=str(data.get("id")),
                status="pending",
                amount=amount,
                due_date=datetime.utcnow() + timedelta(days=due_days),
                payment_url=data.get("init_point") or data.get("sandbox_init_point"),
                raw=data,
            )
        return InvoiceResult(success=False, error=result.get("error", "Erro ao criar fatura"), raw=result)

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        result = self._request("PUT", f"/preapproval/{subscription_id}", {"status": "cancelled"})
        return {"success": result["success"], "data": result.get("data"), "error": result.get("error")}

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        result = self._request("GET", f"/preapproval/{subscription_id}")
        return {"success": result["success"], "data": result.get("data"), "error": result.get("error")}

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        topic = payload.get("topic") or payload.get("type")
        resource = payload.get("resource") or payload.get("data", {}).get("id")

        normalized = {
            "event_type": "unknown",
            "provider_subscription_id": None,
            "provider_invoice_id": None,
            "provider_payment_id": None,
            "amount": None,
            "status": None,
            "payload": payload,
        }

        if topic == "payment" or topic == "payment.updated":
            payment_data = self._fetch_payment(resource)
            if payment_data:
                normalized["event_type"] = "invoice.paid" if payment_data.get("status") == "approved" else "invoice.updated"
                normalized["provider_payment_id"] = str(payment_data.get("id"))
                normalized["amount"] = payment_data.get("transaction_amount")
                normalized["status"] = payment_data.get("status")
                # Tentar encontrar external_reference ou metadata com subscription_id
                ext_ref = payment_data.get("external_reference", "")
                metadata = payment_data.get("metadata", {})
                normalized["provider_subscription_id"] = metadata.get("subscription_id")
        elif topic == "preapproval" or topic == "preapproval.updated":
            sub_data = self._fetch_preapproval(resource)
            if sub_data:
                normalized["event_type"] = "subscription.updated"
                normalized["provider_subscription_id"] = str(sub_data.get("id"))
                normalized["status"] = sub_data.get("status")

        return normalized

    def _fetch_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        result = self._request("GET", f"/v1/payments/{payment_id}")
        return result.get("data") if result["success"] else None

    def _fetch_preapproval(self, preapproval_id: str) -> Optional[Dict[str, Any]]:
        result = self._request("GET", f"/preapproval/{preapproval_id}")
        return result.get("data") if result["success"] else None

    def _map_periodicity(self, periodicity: str):
        mapping = {
            "mensal": (1, "months"),
            "trimestral": (3, "months"),
            "semestral": (6, "months"),
            "anual": (12, "months"),
        }
        return mapping.get(periodicity, (1, "months"))
