"""
Provider Asaas — Assinaturas API via REST.
Documentação: https://docs.asaas.com/
"""
from __future__ import annotations

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import requests

from .base import IPaymentProvider, CustomerResult, SubscriptionResult, InvoiceResult

logger = logging.getLogger(__name__)


class AsaasProvider(IPaymentProvider):
    def __init__(self):
        self.api_key = os.getenv("ASAAS_API_KEY")
        env = os.getenv("ASAAS_ENV", "sandbox")
        self.base_url = "https://api.asaas.com/v3" if env == "production" else "https://sandbox.asaas.com/api/v3"

    @property
    def name(self) -> str:
        return "asaas"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _request(self, method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {
            "access_token": self.api_key,
            "Content-Type": "application/json",
        }
        try:
            resp = requests.request(method, url, headers=headers, json=json_data, timeout=30)
            return {"success": resp.status_code in (200, 201, 204), "status_code": resp.status_code, "data": resp.json() if resp.text else {}}
        except Exception as e:
            logger.error(f"Erro Asaas {method} {endpoint}: {e}")
            return {"success": False, "error": str(e)}

    def create_customer(self, email: str, name: str, doc: Optional[str] = None, **kwargs) -> CustomerResult:
        if not self.is_configured():
            return CustomerResult(success=False, error="Asaas não configurado")
        payload = {"name": name, "email": email}
        if doc:
            payload["cpfCnpj"] = doc
        result = self._request("POST", "/customers", payload)
        if result["success"]:
            data = result.get("data", {})
            return CustomerResult(success=True, customer_id=data.get("id"), email=email, raw=data)
        return CustomerResult(success=False, error=result.get("error", "Erro ao criar customer Asaas"), raw=result)

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
            return SubscriptionResult(success=False, error="Asaas não configurado")

        cycle = self._map_periodicity(periodicity)
        payload = {
            "customer": customer_id,
            "billingType": kwargs.get("billing_type", "PIX"),
            "value": float(amount),
            "cycle": cycle,
            "description": description,
            "nextDueDate": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
        }
        result = self._request("POST", "/subscriptions", payload)
        if result["success"]:
            data = result.get("data", {})
            next_billing = None
            if data.get("nextDueDate"):
                try:
                    next_billing = datetime.strptime(data["nextDueDate"], "%Y-%m-%d")
                except Exception:
                    pass
            return SubscriptionResult(
                success=True,
                subscription_id=data.get("id"),
                status=data.get("status"),
                next_billing_date=next_billing,
                checkout_url=data.get("invoiceUrl"),
                raw=data,
            )
        return SubscriptionResult(success=False, error=result.get("error", "Erro ao criar assinatura Asaas"), raw=result)

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
            return InvoiceResult(success=False, error="Asaas não configurado")

        billing_type = "PIX"
        if method == "boleto":
            billing_type = "BOLETO"
        elif method == "card":
            billing_type = "CREDIT_CARD"

        payload = {
            "customer": customer_id,
            "billingType": billing_type,
            "value": float(amount),
            "dueDate": (datetime.utcnow() + timedelta(days=due_days)).strftime("%Y-%m-%d"),
            "description": description,
        }
        result = self._request("POST", "/payments", payload)
        if result["success"]:
            data = result.get("data", {})
            return InvoiceResult(
                success=True,
                invoice_id=data.get("id"),
                status=data.get("status"),
                amount=amount,
                due_date=datetime.utcnow() + timedelta(days=due_days),
                payment_url=data.get("invoiceUrl"),
                pix_qrcode=data.get("pixQrCodeId"),
                boleto_url=data.get("bankSlipUrl"),
                raw=data,
            )
        return InvoiceResult(success=False, error=result.get("error", "Erro ao criar cobrança Asaas"), raw=result)

    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        result = self._request("DELETE", f"/subscriptions/{subscription_id}")
        return {"success": result["success"], "data": result.get("data"), "error": result.get("error")}

    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        result = self._request("GET", f"/subscriptions/{subscription_id}")
        return {"success": result["success"], "data": result.get("data"), "error": result.get("error")}

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        event = payload.get("event", "")
        payment = payload.get("payment", {})

        normalized = {
            "event_type": "unknown",
            "provider_subscription_id": None,
            "provider_invoice_id": None,
            "provider_payment_id": None,
            "amount": None,
            "status": None,
            "payload": payload,
        }

        if event.startswith("PAYMENT."):
            normalized["provider_invoice_id"] = payment.get("id")
            normalized["provider_subscription_id"] = payment.get("subscription")
            normalized["amount"] = payment.get("value")
            normalized["status"] = payment.get("status")
            if event == "PAYMENT.RECEIVED" or event == "PAYMENT.CONFIRMED":
                normalized["event_type"] = "invoice.paid"
            elif event == "PAYMENT.OVERDUE":
                normalized["event_type"] = "invoice.payment_failed"
            elif event == "PAYMENT.DELETED":
                normalized["event_type"] = "invoice.canceled"
            else:
                normalized["event_type"] = "invoice.updated"
        elif event.startswith("SUBSCRIPTION."):
            sub = payload.get("subscription", {})
            normalized["provider_subscription_id"] = sub.get("id")
            normalized["status"] = sub.get("status")
            if event == "SUBSCRIPTION.DELETED":
                normalized["event_type"] = "subscription.canceled"
            else:
                normalized["event_type"] = "subscription.updated"

        return normalized

    def _map_periodicity(self, periodicity: str) -> str:
        mapping = {
            "mensal": "MONTHLY",
            "trimestral": "QUARTERLY",
            "semestral": "SEMIANNUALLY",
            "anual": "YEARLY",
        }
        return mapping.get(periodicity, "MONTHLY")
