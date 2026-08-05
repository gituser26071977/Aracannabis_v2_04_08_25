"""LGPD — coleta e anonimização de dados do paciente (art. 18).

Exportação (acesso/portabilidade) e eliminação/anonimização de dados do
titular. Registros clínicos e financeiros são RETIDOS (obrigação legal/
médica) mas desvinculados da identidade: o Paciente é anonimizado (nome
trocado e PII removida), e dados acessórios de coleta (pré-consulta e
pendências de onboarding) são excluídos.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from models import (
    db,
    Paciente,
    PreConsulta,
    Consulta,
    Evolucao,
    Dosagem,
    Sintoma,
    Prescricao,
    Exame,
    LancamentoFaturamento,
    Recebimento,
    OnboardingPaciente,
)

logger = logging.getLogger(__name__)

NOME_ANONIMIZADO = "TITULAR ANONIMIZADO"


def _itens(rows) -> list[Dict[str, Any]]:
    return [r.to_dict() if hasattr(r, "to_dict") else r.__dict__ for r in rows]


def coletar_dados_paciente(paciente_id: int) -> Dict[str, Any]:
    """Coleta todos os dados do paciente (acesso/portabilidade)."""
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        raise ValueError("paciente inexistente")

    def q(model, **filtros):
        return model.query.filter_by(**filtros).all()

    return {
        "paciente": paciente.to_dict(),
        "pre_consultas": _itens(q(PreConsulta, paciente_id=paciente_id)),
        "consultas": _itens(q(Consulta, paciente_id=paciente_id)),
        "evolucoes": _itens(q(Evolucao, paciente_id=paciente_id)),
        "dosagens": _itens(q(Dosagem, paciente_id=paciente_id)),
        "sintomas": _itens(q(Sintoma, paciente_id=paciente_id)),
        "prescricoes": _itens(q(Prescricao, paciente_id=paciente_id)),
        "exames": _itens(q(Exame, paciente_id=paciente_id)),
        "faturamento": _itens(q(LancamentoFaturamento, paciente_id=paciente_id)),
        "onboarding": [
            o.to_dict()
            for o in OnboardingPaciente.query.filter(
                (OnboardingPaciente.cpf == paciente.cpf)
                | (OnboardingPaciente.telefone == paciente.telefone)
            ).all()
        ],
    }


def anonimizar_paciente(paciente_id: int) -> Dict[str, Any]:
    """Anonimiza o paciente e exclui dados acessórios de coleta."""
    paciente = Paciente.query.get(paciente_id)
    if not paciente:
        raise ValueError("paciente inexistente")

    # 1. Exclui pré-consultas (dados coletados pelo intake)
    PreConsulta.query.filter_by(paciente_id=paciente_id).delete()

    # 2. Exclui pendências de onboarding que identifiquem o titular
    for ob in OnboardingPaciente.query.filter(
        (OnboardingPaciente.cpf == paciente.cpf)
        | (OnboardingPaciente.telefone == paciente.telefone)
    ).all():
        db.session.delete(ob)

    # 3. Anonimiza a identidade (registros clínicos/financeiros retidos por
    #    obrigação legal, agora sem vínculo com identidade real).
    paciente.nome = NOME_ANONIMIZADO
    paciente.cpf = None
    paciente.telefone = None
    paciente.email = None
    paciente.endereco = None
    if hasattr(paciente, "diagnostico"):
        paciente.diagnostico = None

    db.session.commit()
    logger.info("lgpd_anonimizado", extra={"paciente_id": paciente_id})
    return {"status": "anonimizado", "paciente_id": paciente_id}
