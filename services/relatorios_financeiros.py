"""Relatórios financeiros (Fase 2) — receita, repasse, inadimplência.

Agregações sobre os lançamentos de faturamento para o gestor financeiro.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func

from models import db, Convenio, LancamentoFaturamento, Profissional

STATUS_NAO_CANCELADO = LancamentoFaturamento.status != "cancelado"
STATUS_EM_ABERTO = LancamentoFaturamento.status.in_(("pendente", "parcial"))
STATUS_PAGO = LancamentoFaturamento.status.in_(("pago", "parcial"))


def _periodo(de: Optional[str], ate: Optional[str]):
    de_dt = datetime.fromisoformat(de) if de else None
    ate_dt = datetime.fromisoformat(ate) if ate else None
    return de_dt, ate_dt


def _base_query(*, de, ate, profissional_id=None, convenio_id=None, modalidade=None):
    q = LancamentoFaturamento.query.filter(STATUS_NAO_CANCELADO)
    de_dt, ate_dt = _periodo(de, ate)
    if de_dt:
        q = q.filter(LancamentoFaturamento.data_lancamento >= de_dt)
    if ate_dt:
        q = q.filter(LancamentoFaturamento.data_lancamento <= ate_dt)
    if profissional_id:
        q = q.filter(LancamentoFaturamento.profissional_id == profissional_id)
    if convenio_id:
        q = q.filter(LancamentoFaturamento.convenio_id == convenio_id)
    if modalidade == "particular":
        q = q.filter(LancamentoFaturamento.convenio_id.is_(None))
    elif modalidade == "convenio":
        q = q.filter(LancamentoFaturamento.convenio_id.isnot(None))
    return q


def resumo(**filtros) -> Dict[str, Any]:
    q = _base_query(**filtros)
    lancamentos = q.all()
    recebido = sum(r.valor for l in lancamentos for r in l.recebimentos)
    lancado = sum(l.valor_receber for l in lancamentos)
    pendente = sum(
        (l.valor_receber - sum(r.valor for r in l.recebimentos))
        for l in lancamentos
        if l.status in ("pendente", "parcial")
    )
    repasse_due = sum(l.valor_repasse for l in lancamentos)
    repasse_pago = sum(
        l.valor_repasse for l in lancamentos if l.status in ("pago", "parcial")
    )
    por_status = {"pendente": 0, "parcial": 0, "pago": 0}
    for l in lancamentos:
        por_status[l.status] = por_status.get(l.status, 0) + 1
    return {
        "lancado": round(lancado, 2),
        "recebido": round(recebido, 2),
        "a_receber": round(max(lancado - recebido, 0), 2),
        "pendente": round(max(pendente, 0), 2),
        "repasse_due": round(repasse_due, 2),
        "repasse_pago": round(repasse_pago, 2),
        "quantidade": len(lancamentos),
        "por_status": por_status,
    }


def receita_por(agrupar: str = "profissional", **filtros) -> List[Dict[str, Any]]:
    """Receita agrupada por profissional, convenio ou mes."""
    q = _base_query(**filtros)
    itens: List[Dict[str, Any]] = []
    if agrupar == "convenio":
        grupos: Dict[int, List[LancamentoFaturamento]] = {}
        for l in q.all():
            grupos.setdefault(l.convenio_id, []).append(l)
        for cid, lst in grupos.items():
            convenio = Convenio.query.get(cid) if cid else None
            itens.append({
                "grupo": convenio.nome if convenio else "Particular",
                "lancado": round(sum(l.valor_receber for l in lst), 2),
                "recebido": round(sum(r.valor for l in lst for r in l.recebimentos), 2),
                "quantidade": len(lst),
            })
    elif agrupar == "mes":
        por_mes: Dict[str, List[LancamentoFaturamento]] = {}
        for l in q.all():
            chave = l.data_lancamento.strftime("%Y-%m") if l.data_lancamento else "sem-data"
            por_mes.setdefault(chave, []).append(l)
        for chave, lst in sorted(por_mes.items()):
            itens.append({
                "grupo": chave,
                "lancado": round(sum(l.valor_receber for l in lst), 2),
                "recebido": round(sum(r.valor for l in lst for r in l.recebimentos), 2),
                "quantidade": len(lst),
            })
    else:  # profissional
        por_prof: Dict[int, List[LancamentoFaturamento]] = {}
        for l in q.all():
            por_prof.setdefault(l.profissional_id, []).append(l)
        for pid, lst in por_prof.items():
            prof = Profissional.query.get(pid)
            itens.append({
                "grupo": prof.nome if prof else f"Profissional {pid}",
                "lancado": round(sum(l.valor_receber for l in lst), 2),
                "recebido": round(sum(r.valor for l in lst for r in l.recebimentos), 2),
                "quantidade": len(lst),
            })
    itens.sort(key=lambda x: x["lancado"], reverse=True)
    return itens


def repasse_por_profissional(**filtros) -> List[Dict[str, Any]]:
    """Repasse devido e pago por profissional."""
    q = _base_query(**filtros)
    por_prof: Dict[int, Dict[str, Any]] = {}
    for l in q.all():
        d = por_prof.setdefault(l.profissional_id, {"repasse_due": 0.0, "repasse_pago": 0.0, "quantidade": 0})
        d["repasse_due"] += l.valor_repasse
        if l.status in ("pago", "parcial"):
            d["repasse_pago"] += l.valor_repasse
        d["quantidade"] += 1
    itens = []
    for pid, d in por_prof.items():
        prof = Profissional.query.get(pid)
        itens.append({
            "profissional_id": pid,
            "profissional": prof.nome if prof else f"Profissional {pid}",
            **{k: round(v, 2) for k, v in d.items() if k in ("repasse_due", "repasse_pago")},
            "quantidade": d["quantidade"],
        })
    itens.sort(key=lambda x: x["repasse_due"], reverse=True)
    return itens


def inadimplencia(**filtros) -> Dict[str, Any]:
    """Contas em aberto (pendentes/parciais) com dias de atraso."""
    q = _base_query(**filtros).filter(STATUS_EM_ABERTO).order_by(LancamentoFaturamento.data_lancamento.asc())
    itens = q.limit(100).all()
    agora = datetime.utcnow()
    linhas = []
    total = 0.0
    for l in itens:
        aberto = l.valor_receber - sum(r.valor for r in l.recebimentos)
        total += max(aberto, 0)
        dias = (agora - l.data_lancamento).days if l.data_lancamento else 0
        linhas.append({
            "lancamento_id": l.id,
            "paciente": l.paciente.nome if l.paciente else None,
            "servico": l.servico.nome if l.servico else None,
            "profissional": l.profissional.nome if l.profissional else None,
            "modalidade": "particular" if l.convenio_id is None else "convenio",
            "valor_aberto": round(max(aberto, 0), 2),
            "dias_atraso": max(dias, 0),
            "data": l.data_lancamento.strftime("%d/%m/%Y") if l.data_lancamento else None,
        })
    return {"total_pendente": round(total, 2), "quantidade": len(linhas), "itens": linhas}
