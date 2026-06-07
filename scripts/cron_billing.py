#!/usr/bin/env python3
"""
Script de cron para cobrança recorrente.
Deve ser executado diariamente (ex: via cron ou scheduler do sistema).

Exemplo de execução:
    python scripts/cron_billing.py

Recomendação: executar às 06:00 todos os dias.
"""
import sys
import os

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from models import db, Assinatura
from services.billing_service_v2 import billing_service_v2
from services.feature_flag_service import FeatureFlagService


def run_billing_cron():
    print(f"[CRON BILLING] Iniciado em {datetime.utcnow().isoformat()}")

    if not FeatureFlagService.is_enabled("recurring_payments"):
        print("[CRON BILLING] Feature recurring_payments desativada. Encerrando.")
        return

    if not FeatureFlagService.is_enabled("new_billing_v2"):
        print("[CRON BILLING] Feature new_billing_v2 desativada. Encerrando.")
        return

    hoje = datetime.utcnow().date()
    assinaturas = Assinatura.query.filter(
        Assinatura.status.in_(["ativa", "trial"]),
        Assinatura.renovacao_em != None,
        Assinatura.provedor != None,
        Assinatura.provider_subscription_id != None,
    ).all()

    processadas = 0
    for assinatura in assinaturas:
        if assinatura.renovacao_em and assinatura.renovacao_em.date() <= hoje:
            try:
                resultado = billing_service_v2.processar_renovacao_assinatura(assinatura)
                print(f"[CRON BILLING] Assinatura {assinatura.id}: {resultado}")
                processadas += 1
            except Exception as e:
                print(f"[CRON BILLING] ERRO na assinatura {assinatura.id}: {e}")
                db.session.rollback()

    print(f"[CRON BILLING] Finalizado. {processadas} assinaturas processadas.")


if __name__ == "__main__":
    from app_cors_livre import create_app
    app = create_app()
    with app.app_context():
        run_billing_cron()
