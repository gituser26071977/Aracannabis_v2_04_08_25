"""Cron de follow-up — contata pacientes com documentos pendentes.

Uso (no crontab):
    0 9 * * 1 cd /app && /venv/bin/python scripts/cron_onboarding_followup.py >> logs/followup.log 2>&1

Isso roda toda segunda-feira as 09:00.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_cors_livre import create_app
from models import db, OnboardingPaciente, Paciente
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cron_onboarding_followup")


def follow_up_pendentes():
    """Contata pacientes com pendências antigas (>7 dias) solicitando docs."""
    app = create_app()
    with app.app_context():
        logger.info("Iniciando follow-up de pacientes com pendências...")

        from services.intelligent_onboarding_service import onboarding_service

        corte = datetime.utcnow() - timedelta(days=7)

        pendentes = OnboardingPaciente.query.filter_by(status="pendente").all()
        logger.info(f"Total de pendencias ativas: {len(pendentes)}")

        contatados = 0
        for p in pendentes:
            if p.created_at and p.created_at > corte:
                continue

            paciente_id = p.duplicado_de
            if not paciente_id:
                continue

            paciente = Paciente.query.get(paciente_id)
            if not paciente:
                continue

            try:
                resultado = onboarding_service.follow_up_paciente(paciente_id, canal="whatsapp")
                if resultado.get("status") == "enviado":
                    contatados += 1
                    logger.info(
                        f"Contato enviado para paciente {paciente.nome} "
                        f"(ID={paciente.id}) via {resultado.get('canal')}"
                    )
                else:
                    resultado2 = onboarding_service.follow_up_paciente(paciente_id, canal="email")
                    if resultado2.get("status") == "enviado":
                        contatados += 1
                        logger.info(
                            f"Contato enviado para paciente {paciente.nome} "
                            f"(ID={paciente.id}) via email"
                        )
            except Exception as e:
                logger.error(f"Erro follow-up paciente {paciente_id}: {e}")

        logger.info(f"Follow-up concluido. Pacientes contatados: {contatados}")


if __name__ == "__main__":
    follow_up_pendentes()