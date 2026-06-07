"""
Interface base para provedores de pagamento.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class CustomerResult:
    success: bool
    customer_id: Optional[str] = None
    email: Optional[str] = None
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriptionResult:
    success: bool
    subscription_id: Optional[str] = None
    status: Optional[str] = None
    next_billing_date: Optional[datetime] = None
    checkout_url: Optional[str] = None
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InvoiceResult:
    success: bool
    invoice_id: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    due_date: Optional[datetime] = None
    payment_url: Optional[str] = None
    pix_qrcode: Optional[str] = None
    pix_qrcode_base64: Optional[str] = None
    boleto_url: Optional[str] = None
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


class IPaymentProvider(ABC):
    """Interface que todo provedor de pagamento deve implementar."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome identificador do provedor."""
        pass

    @abstractmethod
    def create_customer(self, email: str, name: str, doc: Optional[str] = None, **kwargs) -> CustomerResult:
        """Cria um cliente no provedor."""
        pass

    @abstractmethod
    def create_subscription(
        self,
        customer_id: str,
        plan_identifier: str,
        periodicity: str,  # mensal, trimestral, semestral, anual
        amount: float,
        description: str,
        **kwargs
    ) -> SubscriptionResult:
        """Cria uma assinatura recorrente."""
        pass

    @abstractmethod
    def create_invoice(
        self,
        customer_id: str,
        amount: float,
        description: str,
        due_days: int = 3,
        method: str = "pix",
        **kwargs
    ) -> InvoiceResult:
        """Cria uma fatura/cobrança avulsa."""
        pass

    @abstractmethod
    def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Cancela uma assinatura ativa."""
        pass

    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Consulta uma assinatura."""
        pass

    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza um webhook recebido para um dict padronizado:
        {
            'event_type': 'subscription.paid' | 'subscription.payment_failed' | 'invoice.paid' | ...,
            'provider_subscription_id': str,
            'provider_invoice_id': str,
            'amount': float,
            'status': str,
            'payload': dict,
        }
        """
        pass

    def is_configured(self) -> bool:
        """Verifica se o provedor está devidamente configurado."""
        return True
