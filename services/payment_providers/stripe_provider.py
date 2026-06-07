"""
Provider Stripe — Subscriptions API via REST.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import requests

from .base import IPaymentProvider, CustomerResult, SubscriptionResult, InvoiceResult

logger = logging.getLogger(__name__)


class StripeProvider(IPaymentProvider):
    def __init__(self):
        self.api_key = os.getenv("STRIPE_SECRET_KEY")
        self.base_url = "https://api.stripe.com/v1"

    @property
    def name(self) -> str:
        return "stripe"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            if method in ("POST", "PUT", "PATCH") and isinstance(data, dict):
                resp = requests.request(method, url, headers=headers, data=data, timeout=30)
            else:
                resp = requests.request(method, url, headers=headers, params=data, timeout=30)
            json_data = resp.json() if resp.text else {}
            return {"success": resp.status_code in (200, 201, 204), "status_code": resp.status_code, "data": json_data}
        except Exception as e:
            logger.error(f"Erro Stripe {method} {endpoint}: {e}")
            return {"success": False, "error": str(e)}

    def create_customer(self, email: str, name: str, doc: Optional[str] = None, **kwargs) -> CustomerResult:
        if not self.is_configured():
            return CustomerResult(success=False, error="Stripe não configurado")
        payload = {"email": email, "name": name}
        if doc:
            payload["tax_id_data[0][type]"] = "br_cpf"
            payload["tax_id_data[0][value]"] = doc
        result = self._request("POST", "/customers", payload)
        if result["success"]:
            data = result.get("data", {})
            return CustomerResult(success=True, customer_id=data.get("id"), email=email, raw=data)
        return CustomerResult(success=False, error=result.get("error", "Erro ao criar customer Stripe"), raw=result)

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
            return SubscriptionResult(success=False, error="Stripe não configurado")

        # Stripe trabalha com Price objects. Criamos um Price dinâmico.
        interval, interval_count = self._map_periodicity(periodicity)
        price_payload = {
            "unit_amount": str(int(amount * 100)),  # centavos
            "currency": "brl",
            "recurring[interval]": interval,
            "recurring[interval_count]": str(interval_count),
            "product_data[name]": description,
        }
        price_result = self._request("POST", "/prices", price_payload)
        if not price_result["success"]:
            return SubscriptionResult(success=False, error="Erro ao criar Price no Stripe", raw=price_result)

        price_id = price_result["data"].get("id")
        sub_payload = {
            "customer": customer_id,
            "items[0][price]": price_id,
            "payment_behavior": "default_incomplete",
            "expand[]": "latest_invoice.payment_intent",
        }
        sub_result = self._request("POST", "/subscriptions", sub_payload)
        if sub_result["success"]:
            data = sub_result.get("data", {})
            next_billing = None
            if data.get("current_period_end"):
                try:
                    next_billing = datetime.utcfromtimestamp(data["current_period_end"])
                except Exception:
                    pass
            checkout_url = None
            pi = data.get("latest_invoice", {}).get("payment_intent", {})
            if pi.get("client_secret"):
                checkout_url = f"https://checkout.stripe.com/pay/{pi.get('client_secret')}"
            return SubscriptionResult(
                success=True,
                subscription_id=data.get("id"),
                status=data.get("status"),
                next_billing_date=next_billing,
                checkout_url=checkout_url,
                raw=data,
            )
        return SubscriptionResult(success=False, error="Erro ao criar assinatura Stripe", raw=sub_result)

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
            return InvoiceResult(success=False, error="Stripe não configurado")

        # Criar InvoiceItem + Invoice para cobrança avulsa
        item_payload = {
            "customer": customer_id,
            "amount": str(int(amount * 100)),
            "currency": "brl",
            "description": description,
        }
        item_result = self._request("POST", "/invoiceitems", item_payload)
        if not item_result["success"]:
            return InvoiceResult(success=False, error="Erro ao criar invoice item", raw=item_result)

        inv_payload = {
            "customer": customer_id,
            "collection_method": "send_invoice",
            "days_until_due": str(due_days),
            "payment_settings[payment_method_types][]": "pix" if method == "pix" else "card",
        }
        inv_result = self._request("POST", "/invoices", inv_payload)
        if inv_result["success"]:
            data = inv_result.get("data", {})
            return InvoiceResult(
                success=True,
                invoice_id=data.get("id"),
                status=data.get("status"),
                amount=amount,
                due_date=datetime.utcnow() + timedelta(days=due_days),
                payment_url=data.get("hosted_invoice_url"),
                raw=data,
            )
        return InvoiceResult(success=False, error="Erro ao criar invoice Stripe", raw=inv_result)

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        result = self._request("DELETE", f"/subscriptions/{subscription_id}")
        return {"success": result["success"], "data": result.get("data"), "error": result.get("error")}

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        result = self._request("GET", f"/subscriptions/{subscription_id}")
        return {"success": result["success"], "data": result.get("data"), "error": result.get("error")}

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event_type = payload.get("type", "")
        data_obj = payload.get("data", {}).get("object", {})

        normalized = {
            "event_type": "unknown",
            "provider_subscription_id": None,
            "provider_invoice_id": None,
            "provider_payment_id": None,
            "amount": None,
            "status": None,
            "payload": payload,
        }

        if event_type.startswith("invoice."):
            normalized["provider_invoice_id"] = data_obj.get("id")
            normalized["provider_subscription_id"] = data_obj.get("subscription")
            normalized["amount"] = data_obj.get("amount_due", 0) / 100.0
            normalized["status"] = data_obj.get("status")
            if event_type == "invoice.payment_succeeded":
                normalized["event_type"] = "invoice.paid"
            elif event_type == "invoice.payment_failed":
                normalized["event_type"] = "invoice.payment_failed"
            else:
                normalized["event_type"] = "invoice.updated"
        elif event_type.startswith("customer.subscription."):
            normalized["provider_subscription_id"] = data_obj.get("id")
            normalized["status"] = data_obj.get("status")
            if event_type == "customer.subscription.deleted":
                normalized["event_type"] = "subscription.canceled"
            else:
                normalized["event_type"] = "subscription.updated"

        return normalized

    def _map_periodicity(self, periodicity: str):
        mapping = {
            "mensal": ("month", 1),
            "trimestral": ("month", 3),
            "semestral": ("month", 6),
            "anual": ("year", 1),
        }
        return mapping.get(periodicity, ("month", 1))
