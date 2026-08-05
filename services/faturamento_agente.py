"""Agente financeiro (Fase 1 — read-only).

Chat em linguagem natural sobre o faturamento:
- classifica a intenção (LLM com fallback heurístico)
- executa a consulta real sobre os lançamentos
- formata a resposta em linguagem natural (LLM com fallback estruturado)

Escopo de leitura:
- perfil administrativo/solo: tudo
- perfil assistencial: apenas os próprios lançamentos (read-only)

Nunca executa ações de escrita (lançar/receber/estornar) — apenas consulta.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from models import Convenio, LancamentoFaturamento, Profissional, Recebimento

logger = logging.getLogger(__name__)

TIPOS = ("receita", "pendentes", "repasse", "resumo", "convenio", "desconhecido")


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _periodo_para_datas(periodo: Optional[str]) -> tuple[Optional[datetime], Optional[datetime]]:
    hoje = _agora_utc()
    if periodo == "hoje":
        inicio = datetime(hoje.year, hoje.month, hoje.day, tzinfo=timezone.utc)
        return inicio, inicio + timedelta(days=1)
    if periodo == "mes_atual":
        inicio = datetime(hoje.year, hoje.month, 1, tzinfo=timezone.utc)
        return inicio, hoje
    if periodo == "mes_passado":
        mes = hoje.month - 1 or 12
        ano = hoje.year if hoje.month > 1 else hoje.year - 1
        inicio = datetime(ano, mes, 1, tzinfo=timezone.utc)
        fim = datetime(hoje.year, hoje.month, 1, tzinfo=timezone.utc)
        return inicio, fim
    return None, None


# ────────────────────────────────────────────────────────────────────
# Intenção (LLM com fallback heurístico)
# ────────────────────────────────────────────────────────────────────

def _classificar_heuristica(pergunta: str) -> Dict[str, Any]:
    q = pergunta.lower()
    if re.search(r"convenio|convênio|operadora|plano de saude|plano de saúde", q):
        return {"tipo": "convenio"}
    if re.search(r"repasse|devido|devo a|quanto .*(dra|dr|médico|medico|profissional)", q):
        return {"tipo": "repasse"}
    if re.search(r"inadimpl|pendente|a receber|nao pagou|não pagou|atrasad", q):
        return {"tipo": "pendentes"}
    if re.search(r"quanto|receb|entrou|fatur|ganh|valor|lucr|arrecad", q):
        return {"tipo": "receita"}
    if re.search(r"resumo|situacao|situação|geral|visao|visão", q):
        return {"tipo": "resumo"}
    return {"tipo": "desconhecido"}


def _periodo_heuristica(pergunta: str) -> Optional[str]:
    q = pergunta.lower()
    if re.search(r"hoje|agora", q):
        return "hoje"
    if re.search(r"mes passado|mês passado|ultimo mes|último mês", q):
        return "mes_passado"
    if re.search(r"esse mes|este mes|deste mes|do mes|do mês|este mês|esse mês|agosto|mes atual|mês atual", q):
        return "mes_atual"
    return None


def classificar_intencao(pergunta: str) -> Dict[str, Any]:
    """Classifica a intenção em {tipo, periodo, profissional, convenio}."""
    if os.environ.get("AGENT_LLM_DISABLED", "").lower() in ("1", "true"):
        dados = _classificar_heuristica(pergunta)
        dados["periodo"] = _periodo_heuristica(pergunta)
        dados.setdefault("profissional", None)
        dados.setdefault("convenio", None)
        return dados
    try:
        from services.ai_agents import AIProviderManager

        ai = AIProviderManager()
        system = (
            "Você é um classificador de intenções financeiras. Responda APENAS com um JSON: "
            '{"tipo": "receita"|"pendentes"|"repasse"|"resumo"|"convenio"|"desconhecido", '
            '"periodo": "hoje"|"mes_atual"|"mes_passado"|null, '
            '"profissional": "nome"|null, "convenio": "nome"|null}'
        )
        response = ai.chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Pergunta: {pergunta[:500]}"},
            ],
            temperature=0.0,
            max_tokens=200,
        )
        content = response.get("content", "")
        if response.get("error"):
            raise ValueError("llm indisponível")
        content = re.sub(r"^```(?:json)?|```$", "", content.strip()).strip()
        dados = json.loads(content)
        if not isinstance(dados, dict) or dados.get("tipo") not in TIPOS:
            raise ValueError("intenção inválida")
        return dados
    except Exception:  # noqa: BLE001
        logger.warning("REDACTED")
        dados = _classificar_heuristica(pergunta)
        dados["periodo"] = _periodo_heuristica(pergunta)
        dados.setdefault("profissional", None)
        dados.setdefault("convenio", None)
        return dados


# ────────────────────────────────────────────────────────────────────
# Consultas
# ────────────────────────────────────────────────────────────────────

def _query_base(profissional: Optional[Profissional]) -> Any:
    q = LancamentoFaturamento.query.filter(LancamentoFaturamento.status != "cancelado")
    # escopo por perfil: assistencial vê só o próprio
    if profissional is not None:
        q = q.filter(LancamentoFaturamento.profissional_id == profissional.id)
    return q


def consultar_receita(profissional: Optional[Profissional], periodo: Optional[str]) -> Dict[str, Any]:
    inicio, fim = _periodo_para_datas(periodo)
    q = _query_base(profissional)
    if inicio:
        q = q.filter(LancamentoFaturamento.data_lancamento >= inicio)
    if fim:
        q = q.filter(LancamentoFaturamento.data_lancamento < fim)
    lancamentos = q.all()
    recebido = sum(r.valor for l in lancamentos for r in l.recebimentos)
    lancado = sum(l.valor_receber for l in lancamentos)
    return {
        "periodo": periodo or "todo",
        "lancado": round(lancado, 2),
        "recebido": round(recebido, 2),
        "a_receber": round(max(lancado - recebido, 0), 2),
        "quantidade": len(lancamentos),
    }


def consultar_pendentes(profissional: Optional[Profissional]) -> Dict[str, Any]:
    q = _query_base(profissional).filter(
        LancamentoFaturamento.status.in_(("pendente", "parcial"))
    ).order_by(LancamentoFaturamento.data_lancamento.asc())
    itens = q.limit(20).all()
    total = sum(l.valor_receber - sum(r.valor for r in l.recebimentos) for l in itens)
    return {
        "quantidade": len(itens),
        "total_pendente": round(total, 2),
        "itens": [
            {
                "paciente": l.paciente.nome if l.paciente else None,
                "servico": l.servico.nome if l.servico else None,
                "profissional": l.profissional.nome if l.profissional else None,
                "valor": round(l.valor_receber - sum(r.valor for r in l.recebimentos), 2),
                "data": l.data_lancamento.strftime("%d/%m/%Y") if l.data_lancamento else None,
                "dias_atraso": (datetime.now(l.data_lancamento.tzinfo) - l.data_lancamento).days
                if l.data_lancamento else None,
            }
            for l in itens
        ],
    }


def consultar_repasse(profissional: Optional[Profissional], nome: Optional[str]) -> Dict[str, Any]:
    q = _query_base(profissional)
    alvo = None
    if nome and profissional is None:
        # escopo aberto (gestor): permite filtrar por outro profissional
        alvo = Profissional.query.filter(Profissional.nome.ilike(f"%{nome}%")).first()
        if alvo:
            q = q.filter(LancamentoFaturamento.profissional_id == alvo.id)
    lancamentos = q.all()
    return {
        "profissional": alvo.nome if alvo else (profissional.nome if profissional else "geral"),
        "repasse_total": round(sum(l.valor_repasse for l in lancamentos), 2),
        "quantidade": len(lancamentos),
    }


def consultar_resumo(profissional: Optional[Profissional]) -> Dict[str, Any]:
    q = _query_base(profissional)
    lancamentos = q.all()
    recebido = sum(r.valor for l in lancamentos for r in l.recebimentos)
    return {
        "lancado": round(sum(l.valor_receber for l in lancamentos), 2),
        "recebido": round(recebido, 2),
        "a_receber": round(max(sum(l.valor_receber for l in lancamentos) - recebido, 0), 2),
        "repasse_total": round(sum(l.valor_repasse for l in lancamentos), 2),
        "quantidade": len(lancamentos),
    }


def consultar_por_convenio(profissional: Optional[Profissional], nome: Optional[str]) -> Dict[str, Any]:
    q = _query_base(profissional).filter(LancamentoFaturamento.convenio_id.isnot(None))
    convenio = None
    if nome:
        convenio = Convenio.query.filter(Convenio.nome.ilike(f"%{nome}%")).first()
        if convenio:
            q = q.filter(LancamentoFaturamento.convenio_id == convenio.id)
    lancamentos = q.all()
    recebido = sum(r.valor for l in lancamentos for r in l.recebimentos)
    return {
        "convenio": convenio.nome if convenio else "todos os convênios",
        "lancado": round(sum(l.valor_receber for l in lancamentos), 2),
        "recebido": round(recebido, 2),
        "quantidade": len(lancamentos),
    }


EXECUTORES = {
    "receita": consultar_receita,
    "pendentes": consultar_pendentes,
    "repasse": consultar_repasse,
    "resumo": consultar_resumo,
    "convenio": consultar_por_convenio,
}


# ────────────────────────────────────────────────────────────────────
# Resposta
# ────────────────────────────────────────────────────────────────────

def _formato_estruturado(tipo: str, dados: Dict[str, Any], pergunta: str) -> str:
    brl = lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if tipo == "receita":
        return (
            f"Receita ({dados['periodo']}): {dados['quantidade']} lançamento(s), "
            f"{brl(dados['lancado'])} lançado, {brl(dados['recebido'])} recebido, "
            f"{brl(dados['a_receber'])} a receber."
        )
    if tipo == "pendentes":
        if not dados["itens"]:
            return "Nenhum lançamento pendente. Tudo em dia!"
        linhas = "; ".join(
            f"{i['paciente']} ({i['servico']}) {brl(i['valor'])}"
            + (f" há {i['dias_atraso']}d" if i["dias_atraso"] else "")
            for i in dados["itens"][:8]
        )
        return f"{dados['quantidade']} pendência(s), total {brl(dados['total_pendente'])}. {linhas}."
    if tipo == "repasse":
        return f"Repasse de {dados['profissional']}: {brl(dados['repasse_total'])} ({dados['quantidade']} lançamentos)."
    if tipo == "convenio":
        return f"{dados['convenio']}: {brl(dados['lancado'])} lançado, {brl(dados['recebido'])} recebido ({dados['quantidade']})."
    if tipo == "resumo":
        return (
            f"Resumo: {brl(dados['lancado'])} lançado, {brl(dados['recebido'])} recebido, "
            f"{brl(dados['a_receber'])} a receber, repasse {brl(dados['repasse_total'])}."
        )
    return "Não consegui entender a pergunta. Tente: 'quanto recebi neste mês?', 'quem está inadimplente?', 'qual o repasse da Dra. X?'."


def _formato_ia(pergunta: str, tipo: str, dados: Dict[str, Any]) -> str:
    if os.environ.get("AGENT_LLM_DISABLED", "").lower() in ("1", "true"):
        return _formato_estruturado(tipo, dados, pergunta)
    try:
        from services.ai_agents import AIProviderManager

        ai = AIProviderManager()
        response = ai.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "Você é o assistente financeiro da clínica. Responda de forma "
                    "concisa e amigável em português, usando apenas os dados fornecidos.",
                },
                {
                    "role": "user",
                    "content": f"Pergunta: {pergunta}\nDados: {json.dumps(dados, ensure_ascii=False)}",
                },
            ],
            temperature=0.3,
            max_tokens=300,
        )
        if response.get("error"):
            raise ValueError("llm indisponível")
        content = (response.get("content") or "").strip()
        if not content:
            raise ValueError("resposta vazia")
        return content
    except Exception:  # noqa: BLE001
        logger.warning("REDACTED")
    return _formato_estruturado(tipo, dados, pergunta)


def responder(
    pergunta: str,
    *,
    perfil: str,
    profissional: Optional[Profissional],
) -> Dict[str, Any]:
    """Responde à pergunta financeira. Somente leitura.

    Privilégios de visibilidade:
    - gestor financeiro (admin/superadmin/manager/solo): vê o financeiro de
      todos os profissionais (inclusive repasse individual).
    - secretária/recepção (administrativo): vê apenas agregados — nunca o
      repasse individual de um médico.
    - assistencial (médico): apenas o próprio financeiro.
    """
    from services.perfil_acesso import eh_gestor_financeiro

    gestor = eh_gestor_financeiro(profissional)
    escopo = None if perfil in ("administrativo", "solo") else profissional

    intencao = classificar_intencao(pergunta)
    tipo = intencao.get("tipo", "desconhecido")

    if tipo == "desconhecido":
        return {
            "tipo": tipo,
            "resposta": _formato_estruturado(tipo, {}, pergunta),
        }

    # Repasse individual de outro médico: somente gestor financeiro.
    # Administrativo (secretária) → negado. Assistencial → sempre o próprio
    # (ignora o nome citado na pergunta).
    if tipo == "repasse" and perfil == "administrativo" and not gestor:
        return {
            "tipo": tipo,
            "resposta": (
                "Você não tem privilégio para ver o repasse individual dos "
                "profissionais. Consulte o gestor financeiro."
            ),
        }

    if tipo == "receita":
        dados = consultar_receita(escopo, intencao.get("periodo"))
    elif tipo == "pendentes":
        dados = consultar_pendentes(escopo)
    elif tipo == "repasse":
        dados = consultar_repasse(escopo, intencao.get("profissional"))
    elif tipo == "convenio":
        dados = consultar_por_convenio(escopo, intencao.get("convenio"))
    else:
        dados = consultar_resumo(escopo)

    # Não-gestor (secretária/recepção): esconde o detalhe por profissional.
    if not gestor and isinstance(dados.get("itens"), list):
        for item in dados["itens"]:
            item.pop("profissional", None)

    resposta = _formato_ia(pergunta, tipo, dados)
    return {"tipo": tipo, "dados": dados, "resposta": resposta}
