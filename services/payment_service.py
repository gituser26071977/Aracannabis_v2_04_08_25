"""
Serviço de pagamentos (mock) para o agente financeiro.

Observação: esta implementação é um stub em memória para demonstração.
Integrações reais (Stripe, Pagar.me, Mercado Pago, Asaas, etc.) devem
substituir os métodos aqui mantendo as assinaturas.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional


class PaymentService:
    """Gerencia cobranças e pagamentos (mock em memória)."""

    def __init__(self) -> None:
        self._charges: Dict[str, Dict] = {}

    def _new_id(self) -> str:
        return str(uuid.uuid4())

    def create_charge(
        self,
        customer_name: str,
        customer_email: str,
        amount: float,
        method: str = "pix",
        description: str = "",
        due_days: int = 3,
    ) -> Dict:
        """Cria uma cobrança mock e retorna dados da cobrança."""
        charge_id = self._new_id()
        due_date = datetime.utcnow() + timedelta(days=due_days)
        payload = {
            "id": charge_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "amount": round(float(amount), 2),
            "currency": "BRL",
            "method": method,
            "description": description,
            "status": "pending",
            "due_date": due_date.isoformat(),
            "boleto_url": f"https://pagamentos.exemplo/boleto/{charge_id}" if method == "boleto" else None,
            "pix_qrcode": f"00020126pix{charge_id}" if method == "pix" else None,
            "card_required": method == "card",
            "created_at": datetime.utcnow().isoformat(),
        }
        self._charges[charge_id] = payload
        return payload

    def mark_paid(self, charge_id: str) -> Dict:
        """Marca uma cobrança como paga."""
        charge = self._charges.get(charge_id)
        if not charge:
            raise ValueError("Cobrança não encontrada")
        charge["status"] = "paid"
        charge["paid_at"] = datetime.utcnow().isoformat()
        return charge

    def update_status(self, charge_id: str, status: str) -> Dict:
        """Atualiza status arbitrário (ex.: canceled, failed)."""
        charge = self._charges.get(charge_id)
        if not charge:
            raise ValueError("Cobrança não encontrada")
        charge["status"] = status
        charge["updated_at"] = datetime.utcnow().isoformat()
        return charge

    def get_status(self, charge_id: str) -> Dict:
        """Retorna status da cobrança."""
        charge = self._charges.get(charge_id)
        if not charge:
            raise ValueError("Cobrança não encontrada")
        return charge


payment_service = PaymentService()
