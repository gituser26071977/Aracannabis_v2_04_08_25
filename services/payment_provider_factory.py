"""
Factory para provedores de pagamento.
Retorna o provider ativo baseado em configuração do sistema.
"""
from __future__ import annotations

import os
from typing import Optional

from services.payment_providers import MercadoPagoProvider, StripeProvider, AsaasProvider
from services.payment_providers.base import IPaymentProvider


class PaymentProviderFactory:
    _providers = {
        "mercadopago": MercadoPagoProvider,
        "stripe": StripeProvider,
        "asaas": AsaasProvider,
    }

    @classmethod
    def get_active_provider(cls) -> IPaymentProvider:
        """
        Retorna o provedor configurado via variável de ambiente PAYMENT_PROVIDER.
        Padrão: mercadopago.
        """
        provider_name = os.getenv("PAYMENT_PROVIDER", "mercadopago").lower()
        provider_class = cls._providers.get(provider_name, MercadoPagoProvider)
        return provider_class()

    @classmethod
    def get_provider(cls, name: str) -> Optional[IPaymentProvider]:
        provider_class = cls._providers.get(name.lower())
        return provider_class() if provider_class else None

    @classmethod
    def list_providers(cls) -> list:
        """Lista provedores disponíveis e seus status de configuração."""
        return [
            {"name": name, "configured": provider_class().is_configured()}
            for name, provider_class in cls._providers.items()
        ]
