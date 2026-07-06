"""
Serviço de billing/assinaturas (camada fina sobre PaymentService + modelos).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from models import db, Plano, Assinatura, Fatura, PagamentoRegistro
from .payment_service import payment_service
from .subscription_expiration_service import SubscriptionExpirationService


class BillingService:
    def criar_assinatura(self, profissional_id: int, plano_id: int, metodo: str = "pix") -> dict:
        plano = Plano.query.get(plano_id)
        if not plano or not plano.ativo:
            return {"error": "Plano não encontrado ou inativo"}

        assinatura = Assinatura.query.filter_by(profissional_id=profissional_id, status='ativa').first()
        if assinatura:
            return {"error": "Já existe uma assinatura ativa"}

        # D05l (trial 14d): usa constante centralizada
        nova_assinatura = Assinatura(
            profissional_id=profissional_id,
            plano_id=plano_id,
            status='trial',
            trial_ends_at=datetime.utcnow() + timedelta(days=SubscriptionExpirationService.TRIAL_DAYS),
            renovacao_em=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(nova_assinatura)
        db.session.commit()

        fatura = self._criar_fatura(nova_assinatura.id, plano.preco_mensal, metodo)
        return {
            "assinatura": nova_assinatura.to_dict(),
            "fatura": fatura.to_dict() if fatura else None
        }

    def _criar_fatura(self, assinatura_id: int, valor: float, metodo: str) -> Optional[Fatura]:
        vencimento = datetime.utcnow() + timedelta(days=3)
        fatura = Fatura(
            assinatura_id=assinatura_id,
            valor=valor,
            status='pendente',
            vencimento=vencimento,
            metodo=metodo
        )
        db.session.add(fatura)
        db.session.commit()

        charge = payment_service.create_charge(
            customer_name="Cliente",
            customer_email="cliente@example.com",
            amount=valor,
            method=metodo,
            description="Assinatura AraOS"
        )
        fatura.cobranca_id = charge.get("id")
        db.session.commit()

        pagamento = PagamentoRegistro(
            fatura_id=fatura.id,
            status=charge.get("status", "pending"),
            metodo=metodo,
            valor=valor,
            referencia_psp=charge.get("id"),
            payload=charge
        )
        db.session.add(pagamento)
        db.session.commit()

        return fatura

    def pagar_fatura(self, fatura_id: int) -> dict:
        fatura = Fatura.query.get(fatura_id)
        if not fatura:
            return {"error": "Fatura não encontrada"}
        fatura.status = 'paga'
        db.session.commit()

        pagamento = PagamentoRegistro.query.filter_by(fatura_id=fatura.id).order_by(PagamentoRegistro.created_at.desc()).first()
        if pagamento:
            pagamento.status = 'paid'
            db.session.commit()

        assinatura = Assinatura.query.get(fatura.assinatura_id)
        if assinatura:
            assinatura.status = 'ativa'
            assinatura.renovacao_em = datetime.utcnow() + timedelta(days=30)
            db.session.commit()

        return {
            "fatura": fatura.to_dict(),
            "assinatura": assinatura.to_dict() if assinatura else None
        }


billing_service = BillingService()
