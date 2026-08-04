"""Serviço de Faturamento Clínico — cálculo e fluxo de contas a receber.

Modalidades:
    - PARTICULAR: lançamento sem convenio_id; valor = servico.valor_particular.
    - CONVÊNIO:    lançamento com convenio_id; valor = tabela_preco_convenios
                   (valor fixo do convênio para o serviço).

Repasse do profissional (percentual por serviço):
    - Linha em `percentuais_repasse` (profissional_id, servico_id).
    - Se não houver, linha global (servico_id NULL) do profissional.
    - Se nada configurado, profissional fica com 100% (solo / padrão seguro).

O lançamento grava os valores já calculados (valor_receber e valor_repasse)
para manter histórico imutável mesmo se a tabela mudar depois.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from models import db, PercentualRepasse, TabelaPrecoConvenio, LancamentoFaturamento, Recebimento

logger = logging.getLogger(__name__)

STATUS_PENDENTE = "pendente"
STATUS_PARCIAL = "parcial"
STATUS_PAGO = "pago"
STATUS_CANCELADO = "cancelado"


def resolver_percentual_repasse(profissional_id: int, servico_id: int) -> float:
    """% do profissional para o serviço. Per-service → global → 100%."""
    per_servico = PercentualRepasse.query.filter_by(
        profissional_id=profissional_id, servico_id=servico_id, ativo=True
    ).first()
    if per_servico:
        return float(per_servico.percentual)

    global_row = PercentualRepasse.query.filter_by(
        profissional_id=profissional_id, servico_id=None, ativo=True
    ).first()
    if global_row:
        return float(global_row.percentual)

    return 100.0


def calcular_valor(servico, convenio_id: Optional[int]) -> float:
    """Valor cobrado do serviço. Convênio: tabela fixa. Particular: tabela base."""
    if convenio_id is not None:
        tabela = TabelaPrecoConvenio.query.filter_by(
            convenio_id=convenio_id, servico_id=servico.id, ativo=True
        ).first()
        if tabela and tabela.valor is not None:
            return float(tabela.valor)
    return float(servico.valor_particular or 0.0)


def criar_lancamento(
    *,
    servico_id: int,
    profissional_id: int,
    convenio_id: Optional[int] = None,
    paciente_id: Optional[int] = None,
    atendimento_id: Optional[int] = None,
    associacao_id: Optional[int] = None,
    desconto: float = 0.0,
    forma_pagamento: str = "dinheiro",
    observacao: Optional[str] = None,
    criado_por: Optional[str] = None,
) -> LancamentoFaturamento:
    """Cria a conta a receber com os valores calculados (imutáveis)."""
    from models import Servico

    servico = Servico.query.get(servico_id)
    if not servico:
        raise ValueError("servico inexistente")

    valor_total = calcular_valor(servico, convenio_id)
    if valor_total <= 0:
        raise ValueError("valor do serviço não definido (particular ou convênio)")

    desconto = float(desconto or 0.0)
    if desconto < 0 or desconto > valor_total:
        raise ValueError("desconto inválido")

    percentual = resolver_percentual_repasse(profissional_id, servico_id)
    valor_receber = round(valor_total - desconto, 2)
    valor_repasse = round(valor_receber * percentual / 100.0, 2)

    lancamento = LancamentoFaturamento(
        associacao_id=associacao_id,
        paciente_id=paciente_id,
        atendimento_id=atendimento_id,
        profissional_id=profissional_id,
        servico_id=servico_id,
        convenio_id=convenio_id,
        valor_total=round(valor_total, 2),
        desconto=desconto,
        valor_receber=valor_receber,
        percentual_repasse=percentual,
        valor_repasse=valor_repasse,
        forma_pagamento=forma_pagamento,
        status=STATUS_PENDENTE,
        observacao=observacao,
        criado_por=criado_por,
    )
    db.session.add(lancamento)
    db.session.commit()
    logger.info("lancamento_faturamento_criado", extra={"id": lancamento.id, "valor": valor_receber})
    return lancamento


def registrar_recebimento(
    lancamento_id: int,
    valor: float,
    *,
    forma_pagamento: str = "dinheiro",
    observacao: Optional[str] = None,
    criado_por: Optional[str] = None,
) -> LancamentoFaturamento:
    """Registra pagamento (parcial/múltiplo). Atualiza status e data."""
    lancamento = LancamentoFaturamento.query.get(lancamento_id)
    if not lancamento:
        raise ValueError("lançamento inexistente")
    if lancamento.status == STATUS_CANCELADO:
        raise ValueError("lançamento cancelado não recebe pagamento")

    valor = float(valor)
    if valor <= 0:
        raise ValueError("valor de recebimento inválido")

    from datetime import datetime

    recebimento = Recebimento(
        lancamento_id=lancamento.id,
        valor=valor,
        forma_pagamento=forma_pagamento,
        observacao=observacao,
        criado_por=criado_por,
        data=datetime.utcnow(),
    )
    db.session.add(recebimento)

    total_recebido = sum(r.valor for r in lancamento.recebimentos) + valor
    if total_recebido >= lancamento.valor_receber - 0.005:
        lancamento.status = STATUS_PAGO
        lancamento.data_recebimento = datetime.utcnow()
    else:
        lancamento.status = STATUS_PARCIAL
        lancamento.data_recebimento = None
    db.session.commit()
    return lancamento


def estornar_lancamento(
    lancamento_id: int,
    *,
    criado_por: Optional[str] = None,
) -> LancamentoFaturamento:
    """Cancela o lançamento (estorno). Não apaga recebimentos (histórico)."""
    lancamento = LancamentoFaturamento.query.get(lancamento_id)
    if not lancamento:
        raise ValueError("lançamento inexistente")
    lancamento.status = STATUS_CANCELADO
    db.session.commit()
    return lancamento


def listar_lancamentos(
    *,
    status: Optional[str] = None,
    profissional_id: Optional[int] = None,
    convenio_id: Optional[int] = None,
    modalidade: Optional[str] = None,
    de: Optional[str] = None,
    ate: Optional[str] = None,
    associacao_id: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[int, List[LancamentoFaturamento]]:
    """Lista lançamentos com filtros. Retorna (total, itens)."""
    from datetime import datetime

    q = LancamentoFaturamento.query
    if status:
        q = q.filter(LancamentoFaturamento.status == status)
    if profissional_id:
        q = q.filter(LancamentoFaturamento.profissional_id == profissional_id)
    if convenio_id:
        q = q.filter(LancamentoFaturamento.convenio_id == convenio_id)
    if modalidade == "particular":
        q = q.filter(LancamentoFaturamento.convenio_id.is_(None))
    elif modalidade == "convenio":
        q = q.filter(LancamentoFaturamento.convenio_id.isnot(None))
    if de:
        q = q.filter(LancamentoFaturamento.data_lancamento >= datetime.fromisoformat(de))
    if ate:
        q = q.filter(LancamentoFaturamento.data_lancamento <= datetime.fromisoformat(ate))
    if associacao_id:
        q = q.filter(LancamentoFaturamento.associacao_id == associacao_id)

    total = q.count()
    itens = (
        q.order_by(LancamentoFaturamento.data_lancamento.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return total, itens
