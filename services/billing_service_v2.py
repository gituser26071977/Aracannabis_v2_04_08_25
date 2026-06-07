"""
BillingService v2 — cobrança real com múltiplos provedores e recorrência.
Toda a lógica nova está protegida por feature flags.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from models import db, Plano, Assinatura, Fatura, PagamentoRegistro, Profissional
from services.payment_provider_factory import PaymentProviderFactory
from services.feature_flag_service import FeatureFlagService

import logging

logger = logging.getLogger(__name__)


class BillingServiceV2:
    """Serviço de billing que integra com provedores reais de pagamento."""

    def _get_provider(self):
        return PaymentProviderFactory.get_active_provider()

    def _calcular_preco(self, plano: Plano, periodicidade: str) -> float:
        base = plano.preco_mensal or 0.0
        multiplicadores = {
            "mensal": 1,
            "trimestral": 3,
            "semestral": 6,
            "anual": 12,
        }
        descontos = {
            "mensal": 0,
            "trimestral": 0.05,
            "semestral": 0.08,
            "anual": 0.12,
        }
        mult = multiplicadores.get(periodicidade, 1)
        desc = descontos.get(periodicidade, 0)
        return round(base * mult * (1 - desc), 2)

    def _calcular_next_billing(self, periodicidade: str) -> datetime:
        agora = datetime.utcnow()
        deltas = {
            "mensal": timedelta(days=30),
            "trimestral": timedelta(days=90),
            "semestral": timedelta(days=180),
            "anual": timedelta(days=365),
        }
        return agora + deltas.get(periodicidade, timedelta(days=30))

    def criar_assinatura(
        self,
        profissional_id: int,
        plano_id: int,
        metodo: str = "pix",
        periodicidade: str = "mensal",
    ) -> Dict[str, Any]:
        plano = Plano.query.get(plano_id)
        if not plano or not plano.ativo:
            return {"error": "Plano não encontrado ou inativo"}

        profissional = Profissional.query.get(profissional_id)
        if not profissional:
            return {"error": "Profissional não encontrado"}

        # Verificar se já existe assinatura ativa
        assinatura_ativa = Assinatura.query.filter_by(
            profissional_id=profissional_id, status="ativa"
        ).first()
        if assinatura_ativa:
            return {"error": "Já existe uma assinatura ativa"}

        provider = self._get_provider()
        valor = self._calcular_preco(plano, periodicidade)

        # Criar/atualizar customer no provedor
        customer_result = provider.create_customer(
            email=profissional.email or f"user_{profissional_id}@aracannabis.com",
            name=profissional.nome or "Cliente",
        )
        if not customer_result.success:
            logger.error(f"Erro ao criar customer: {customer_result.error}")
            return {"error": f"Erro no provedor de pagamento: {customer_result.error}"}

        # Feature flag: recurring_payments
        if FeatureFlagService.is_enabled("recurring_payments"):
            sub_result = provider.create_subscription(
                customer_id=customer_result.customer_id,
                plan_identifier=str(plano_id),
                periodicity=periodicidade,
                amount=valor,
                description=f"Assinatura {plano.nome} - {periodicidade}",
                payer_email=profissional.email,
                external_reference=f"aracannabis_sub_{profissional_id}_{plano_id}",
            )
            if not sub_result.success:
                return {"error": f"Erro ao criar assinatura: {sub_result.error}"}

            nova_assinatura = Assinatura(
                profissional_id=profissional_id,
                plano_id=plano_id,
                status="ativa" if sub_result.status == "active" else "pending",
                trial_ends_at=datetime.utcnow() + timedelta(days=7),
                renovacao_em=sub_result.next_billing_date or self._calcular_next_billing(periodicidade),
                provedor=provider.name,
                provider_subscription_id=sub_result.subscription_id,
                periodicidade=periodicidade,
            )
            db.session.add(nova_assinatura)
            db.session.commit()

            # Criar fatura inicial vinculada
            fatura = Fatura(
                assinatura_id=nova_assinatura.id,
                valor=valor,
                status="pendente",
                vencimento=sub_result.next_billing_date or self._calcular_next_billing(periodicidade),
                metodo=metodo,
                provedor=provider.name,
            )
            db.session.add(fatura)
            db.session.commit()

            return {
                "assinatura": nova_assinatura.to_dict(),
                "fatura": fatura.to_dict(),
                "checkout_url": sub_result.checkout_url,
                "provider": provider.name,
            }
        else:
            # Modo não-recorrente: criar invoice avulsa (mantém compatibilidade)
            invoice_result = provider.create_invoice(
                customer_id=customer_result.customer_id,
                amount=valor,
                description=f"Pagamento {plano.nome} - {periodicidade}",
                due_days=3,
                method=metodo,
                payer_email=profissional.email,
                payer_name=profissional.nome,
                external_reference=f"aracannabis_inv_{profissional_id}_{plano_id}",
            )
            if not invoice_result.success:
                return {"error": f"Erro ao criar cobrança: {invoice_result.error}"}

            nova_assinatura = Assinatura(
                profissional_id=profissional_id,
                plano_id=plano_id,
                status="trial",
                trial_ends_at=datetime.utcnow() + timedelta(days=7),
                renovacao_em=self._calcular_next_billing(periodicidade),
                provedor=provider.name,
                periodicidade=periodicidade,
            )
            db.session.add(nova_assinatura)
            db.session.commit()

            fatura = Fatura(
                assinatura_id=nova_assinatura.id,
                valor=valor,
                status="pendente",
                vencimento=invoice_result.due_date,
                cobranca_id=invoice_result.invoice_id,
                metodo=metodo,
                provedor=provider.name,
            )
            db.session.add(fatura)
            db.session.commit()

            pagamento = PagamentoRegistro(
                fatura_id=fatura.id,
                status="pending",
                metodo=metodo,
                valor=valor,
                referencia_psp=invoice_result.invoice_id,
                payload=invoice_result.raw,
            )
            db.session.add(pagamento)
            db.session.commit()

            return {
                "assinatura": nova_assinatura.to_dict(),
                "fatura": fatura.to_dict(),
                "checkout_url": invoice_result.payment_url,
                "provider": provider.name,
            }

    def pagar_fatura(self, fatura_id: int) -> Dict[str, Any]:
        fatura = Fatura.query.get(fatura_id)
        if not fatura:
            return {"error": "Fatura não encontrada"}

        fatura.status = "paga"
        db.session.commit()

        pagamento = PagamentoRegistro.query.filter_by(fatura_id=fatura.id).order_by(
            PagamentoRegistro.created_at.desc()
        ).first()
        if pagamento:
            pagamento.status = "paid"
            db.session.commit()

        assinatura = Assinatura.query.get(fatura.assinatura_id)
        if assinatura:
            assinatura.status = "ativa"
            assinatura.renovacao_em = self._calcular_next_billing(
                assinatura.periodicidade or "mensal"
            )
            db.session.commit()

        return {
            "fatura": fatura.to_dict(),
            "assinatura": assinatura.to_dict() if assinatura else None,
        }

    def processar_renovacao_assinatura(self, assinatura: Assinatura) -> Dict[str, Any]:
        """
        Gera nova fatura para uma assinatura e, se necessário, cobra automaticamente.
        Usado pelo cron diário.
        """
        if not FeatureFlagService.is_enabled("recurring_payments"):
            return {"skipped": True, "reason": "recurring_payments desativado"}

        if assinatura.status not in ("ativa", "trial"):
            return {"skipped": True, "reason": "assinatura não ativa"}

        if not assinatura.provedor or not assinatura.provider_subscription_id:
            return {"skipped": True, "reason": "assinatura sem provider vinculado"}

        provider = PaymentProviderFactory.get_provider(assinatura.provedor)
        if not provider:
            return {"error": f"Provedor {assinatura.provedor} não encontrado"}

        plano = Plano.query.get(assinatura.plano_id)
        if not plano:
            return {"error": "Plano não encontrado"}

        valor = self._calcular_preco(plano, assinatura.periodicidade or "mensal")
        next_billing = self._calcular_next_billing(assinatura.periodicidade or "mensal")

        # Para assinaturas recorrentes, o provedor já gera a cobrança automaticamente.
        # Criamos apenas a fatura local para rastreamento.
        fatura = Fatura(
            assinatura_id=assinatura.id,
            valor=valor,
            status="pendente",
            vencimento=next_billing,
            metodo="pix",  # default, será atualizado pelo webhook
            provedor=provider.name,
        )
        db.session.add(fatura)
        db.session.commit()

        # Atualizar próxima data de cobrança
        assinatura.renovacao_em = next_billing
        db.session.commit()

        return {
            "success": True,
            "fatura_id": fatura.id,
            "assinatura_id": assinatura.id,
            "next_billing": next_billing.isoformat(),
        }

    def cancelar_assinatura(self, assinatura_id: int) -> Dict[str, Any]:
        assinatura = Assinatura.query.get(assinatura_id)
        if not assinatura:
            return {"error": "Assinatura não encontrada"}

        if assinatura.provedor and assinatura.provider_subscription_id:
            provider = PaymentProviderFactory.get_provider(assinatura.provedor)
            if provider:
                try:
                    provider.cancel_subscription(assinatura.provider_subscription_id)
                except Exception as e:
                    logger.error(f"Erro ao cancelar no provider: {e}")

        assinatura.status = "cancelada"
        db.session.commit()
        return {"success": True, "assinatura": assinatura.to_dict()}

    def listar_faturas_profissional(self, profissional_id: int) -> list:
        assinaturas = Assinatura.query.filter_by(profissional_id=profissional_id).all()
        ids = [a.id for a in assinaturas]
        if not ids:
            return []
        faturas = Fatura.query.filter(Fatura.assinatura_id.in_(ids)).order_by(Fatura.created_at.desc()).all()
        return [f.to_dict() for f in faturas]


billing_service_v2 = BillingServiceV2()
