"""
Webhook Handler Unificado — processa callbacks de MP, Stripe e Asaas
com idempotência garantida (FASE 4.1: registro atomico via register_webhook_event).
"""
from __future__ import annotations

import logging
from typing import Dict, Any
from datetime import datetime

from models import db, Assinatura, Fatura, PagamentoRegistro
from models_extra import WebhookLog
from services.payment_provider_factory import PaymentProviderFactory
from services.feature_flag_service import FeatureFlagService
from services.webhook_auth import register_webhook_event

logger = logging.getLogger(__name__)


class WebhookHandler:
    def process(self, provider_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa um webhook de qualquer provedor.
        Retorna dict com status do processamento.
        """
        # Feature flag obrigatória
        if not FeatureFlagService.is_enabled("new_billing_v2"):
            return {"success": False, "error": "new_billing_v2 desativado"}

        provider = PaymentProviderFactory.get_provider(provider_name)
        if not provider:
            return {"success": False, "error": f"Provedor {provider_name} não encontrado"}

        # Normalizar evento
        normalized = provider.parse_webhook(payload)
        event_type = normalized.get("event_type", "unknown")
        provider_event_id = self._extract_event_id(provider_name, payload)

        # FASE 4.1 — idempotência atômica via UNIQUE constraint.
        # Substitui o padrão frágil SELECT+INSERT (race condition) por um
        # INSERT direto: UNIQUE(provider, provider_event_id) faz a deduplicação
        # no banco. Requests simultâneas: 2ª pega IntegrityError → replay=True.
        is_replay, log_id = register_webhook_event(
            provider=provider_name,
            event_id=provider_event_id,
            event_type=event_type,
            payload=payload,
        )
        if is_replay:
            logger.info(
                f"Webhook {provider_name}/{provider_event_id} já registrado. "
                f"Idempotente (log_id={log_id})."
            )
            return {"success": True, "idempotent": True, "webhook_log_id": log_id}

        log = WebhookLog.query.get(log_id) if log_id else None
        if log is None:
            # Fallback defensivo: registro atomic falhou silenciosamente,
            # buscar para obter referencia (caminho raro)
            log = WebhookLog.query.filter_by(
                provider=provider_name, provider_event_id=provider_event_id
            ).first()

        try:
            result = self._handle_event(provider_name, normalized, payload)
            log.processed = True
            if result.get("fatura_id"):
                log.fatura_id = result["fatura_id"]
            if result.get("assinatura_id"):
                log.assinatura_id = result["assinatura_id"]
            db.session.commit()
            logger.info(f"Webhook {provider_name}/{provider_event_id} processado com sucesso: {result}")
            return {"success": True, "result": result, "webhook_log_id": log.id}
        except Exception as e:
            db.session.rollback()
            log.error_message = str(e)
            db.session.commit()
            logger.error(f"Erro ao processar webhook {provider_name}/{provider_event_id}: {e}")
            return {"success": False, "error": str(e), "webhook_log_id": log.id}

    def _extract_event_id(self, provider_name: str, payload: Dict[str, Any]) -> str:
        if provider_name == "stripe":
            return payload.get("id", "unknown")
        elif provider_name == "mercadopago":
            return str(payload.get("data", {}).get("id", payload.get("id", "unknown")))
        elif provider_name == "asaas":
            return payload.get("event", "unknown") + "_" + str(payload.get("payment", {}).get("id", "unknown"))
        return str(payload.get("id", "unknown"))

    def _handle_event(self, provider_name: str, normalized: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
        event_type = normalized.get("event_type")

        if event_type == "invoice.paid":
            return self._handle_invoice_paid(provider_name, normalized, raw)
        elif event_type == "invoice.payment_failed":
            return self._handle_invoice_failed(provider_name, normalized, raw)
        elif event_type == "subscription.canceled":
            return self._handle_subscription_canceled(provider_name, normalized, raw)
        elif event_type == "subscription.updated":
            return self._handle_subscription_updated(provider_name, normalized, raw)
        elif event_type == "invoice.updated":
            return self._handle_invoice_updated(provider_name, normalized, raw)

        return {"handled": False, "event_type": event_type}

    def _handle_invoice_paid(self, provider_name: str, normalized: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
        subscription_id = normalized.get("provider_subscription_id")
        payment_id = normalized.get("provider_payment_id") or normalized.get("provider_invoice_id")
        amount = normalized.get("amount")

        assinatura = None
        if subscription_id:
            assinatura = Assinatura.query.filter_by(
                provedor=provider_name, provider_subscription_id=str(subscription_id)
            ).first()

        if not assinatura and payment_id:
            # Tentar encontrar via PagamentoRegistro
            pag_reg = PagamentoRegistro.query.filter_by(referencia_psp=str(payment_id)).first()
            if pag_reg:
                assinatura = Assinatura.query.get(pag_reg.fatura.assinatura_id) if pag_reg.fatura else None

        if not assinatura:
            return {"handled": True, "warning": "Assinatura não encontrada para o pagamento", "subscription_id": subscription_id}

        # Marcar fatura mais recente como paga
        fatura = Fatura.query.filter_by(assinatura_id=assinatura.id).order_by(Fatura.created_at.desc()).first()
        if fatura:
            fatura.status = "paga"
            if payment_id and not fatura.provider_invoice_id:
                fatura.provider_invoice_id = str(payment_id)
            db.session.commit()

            # Criar registro de pagamento
            pagamento = PagamentoRegistro(
                fatura_id=fatura.id,
                status="paid",
                metodo=fatura.metodo or "pix",
                valor=amount or fatura.valor,
                referencia_psp=str(payment_id) if payment_id else None,
                payload=raw,
            )
            db.session.add(pagamento)
            db.session.commit()

        # Atualizar assinatura
        assinatura.status = "ativa"
        assinatura.renovacao_em = self._calcular_next_billing(assinatura.periodicidade or "mensal")
        db.session.commit()

        return {
            "handled": True,
            "event": "invoice.paid",
            "assinatura_id": assinatura.id,
            "fatura_id": fatura.id if fatura else None,
        }

    def _handle_invoice_failed(self, provider_name: str, normalized: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
        subscription_id = normalized.get("provider_subscription_id")
        assinatura = Assinatura.query.filter_by(
            provedor=provider_name, provider_subscription_id=str(subscription_id)
        ).first() if subscription_id else None

        if assinatura:
            # Não cancela imediatamente, marca como inadimplente após N dias (futuro)
            fatura = Fatura.query.filter_by(assinatura_id=assinatura.id, status="pendente").order_by(Fatura.created_at.desc()).first()
            if fatura:
                fatura.status = "cancelada"
                db.session.commit()
                return {"handled": True, "event": "invoice.payment_failed", "assinatura_id": assinatura.id, "fatura_id": fatura.id}

        return {"handled": True, "event": "invoice.payment_failed", "warning": "Assinatura não encontrada"}

    def _handle_subscription_canceled(self, provider_name: str, normalized: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
        subscription_id = normalized.get("provider_subscription_id")
        assinatura = Assinatura.query.filter_by(
            provedor=provider_name, provider_subscription_id=str(subscription_id)
        ).first() if subscription_id else None

        if assinatura:
            assinatura.status = "cancelada"
            db.session.commit()
            return {"handled": True, "event": "subscription.canceled", "assinatura_id": assinatura.id}
        return {"handled": True, "event": "subscription.canceled", "warning": "Assinatura não encontrada"}

    def _handle_subscription_updated(self, provider_name: str, normalized: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
        subscription_id = normalized.get("provider_subscription_id")
        status = normalized.get("status")
        assinatura = Assinatura.query.filter_by(
            provedor=provider_name, provider_subscription_id=str(subscription_id)
        ).first() if subscription_id else None

        if assinatura and status:
            # Mapear status do provider para nossos status
            if status in ("active", "authorized", "trialing"):
                assinatura.status = "ativa"
            elif status in ("paused", "pending"):
                assinatura.status = "trial"
            elif status in ("cancelled", "canceled"):
                assinatura.status = "cancelada"
            db.session.commit()
            return {"handled": True, "event": "subscription.updated", "assinatura_id": assinatura.id, "new_status": assinatura.status}
        return {"handled": True, "event": "subscription.updated", "warning": "Assinatura não encontrada"}

    def _handle_invoice_updated(self, provider_name: str, normalized: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
        # Atualiza informações da fatura sem marcar como paga
        payment_id = normalized.get("provider_payment_id") or normalized.get("provider_invoice_id")
        if payment_id:
            fatura = Fatura.query.filter_by(provider_invoice_id=str(payment_id)).first()
            if not fatura:
                fatura = Fatura.query.filter_by(cobranca_id=str(payment_id)).first()
            if fatura:
                fatura.provedor = provider_name
                db.session.commit()
                return {"handled": True, "event": "invoice.updated", "fatura_id": fatura.id}
        return {"handled": True, "event": "invoice.updated", "warning": "Fatura não encontrada"}

    def _calcular_next_billing(self, periodicidade: str) -> datetime:
        from datetime import timedelta
        agora = datetime.utcnow()
        deltas = {
            "mensal": timedelta(days=30),
            "trimestral": timedelta(days=90),
            "semestral": timedelta(days=180),
            "anual": timedelta(days=365),
        }
        return agora + deltas.get(periodicidade, timedelta(days=30))


webhook_handler = WebhookHandler()
