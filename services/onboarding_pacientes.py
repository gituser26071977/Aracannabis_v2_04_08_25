"""Onboarding de pacientes (padrão SGA) — cadastro administrativo com IA.

- `sugerir_dados(texto)`: extrai nome/telefone/cpf/email/queixa de texto livre
  via LLM (com fallback heurístico por regex).
- `detectar_duplicados(dados)`: busca pacientes por cpf, telefone e nome.
- `registrar_paciente(dados)`: cria direto (sem duplicado e completo) ou abre
  pendência (duplicado / dados incompletos) para o administrativo confirmar.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import or_

from models import db, Paciente, OnboardingPaciente

logger = logging.getLogger(__name__)

MOTIVO_DUPLICADO = "duplicado"
MOTIVO_INCOMPLETO = "dados_incompletos"
MOTIVO_REVISAR = "revisar"
STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_DESCARTADO = "descartado"

_TEL_RE = re.compile(r"\d{10,11}")
_CPF_RE = re.compile(r"\d{11}")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _normalizar_telefone(v: str | None) -> str | None:
    if not v:
        return None
    return "".join(ch for ch in v if ch.isdigit())


def _normalizar_cpf(v: str | None) -> str | None:
    if not v:
        return None
    return "".join(ch for ch in v if ch.isdigit())


def _sugerir_heuristica(texto: str) -> Dict[str, Any]:
    """Fallback por regex quando o LLM não está disponível/falha."""
    sugestao: Dict[str, Any] = {}
    tel = _TEL_RE.search(texto)
    if tel:
        sugestao["telefone"] = tel.group(0)
    cpf = _CPF_RE.search(texto)
    if cpf:
        sugestao["cpf"] = cpf.group(0)
    email = _EMAIL_RE.search(texto)
    if email:
        sugestao["email"] = email.group(0)
    sugestao["queixa"] = texto.strip()[:200]
    return sugestao


def sugerir_dados(texto: str) -> Dict[str, Any]:
    """Extrai dados estruturados do paciente a partir de texto livre."""
    if not texto or not texto.strip():
        return {}
    try:
        from services.ai_agents import AIProviderManager

        ai = AIProviderManager()
        system = (
            "Você é um assistente de cadastro clínico. Extraia do texto os dados "
            "do paciente em JSON com as chaves: nome, telefone, cpf, email, queixa. "
            "Use somente o que estiver presente; não invente."
        )
        response = ai.chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Texto: {texto[:1500]}"},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        content = response.get("content", "")
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?|```$", "", content).strip()
        dados = json.loads(content)
        if not isinstance(dados, dict):
            raise ValueError("resposta não é objeto")
        for k in ("telefone", "cpf"):
            if dados.get(k):
                dados[k] = _normalizar_telefone(dados[k]) if k == "telefone" else _normalizar_cpf(dados[k])
        return dados
    except Exception:  # noqa: BLE001 — LLM indisponível
        logger.warning("REDACTED")
        return _sugerir_heuristica(texto)


def detectar_duplicados(dados: Dict[str, Any]) -> List[Paciente]:
    """Procura pacientes que já existem (cpf, telefone, nome)."""
    cpf = _normalizar_cpf(dados.get("cpf"))
    tel = _normalizar_telefone(dados.get("telefone"))
    nome = (dados.get("nome") or "").strip()

    conds = []
    if cpf:
        conds.append(Paciente.cpf == cpf)
    if tel:
        conds.append(Paciente.telefone == tel)
    if nome:
        conds.append(Paciente.nome == nome)
    if not conds:
        return []
    return Paciente.query.filter(or_(*conds)).all()


def _dados_completos(dados: Dict[str, Any]) -> bool:
    return bool((dados.get("nome") or "").strip())


def registrar_paciente(
    dados: Dict[str, Any],
    *,
    origem: str = "admin",
    criado_por: Optional[str] = None,
) -> Dict[str, Any]:
    """Cadastra paciente ou abre pendência.

    Returns:
        {"status": "criado" | "pendente", "paciente_id"?, "onboarding_id"?, "duplicados": [...]}
    """
    nome = (dados.get("nome") or "").strip()
    cpf = _normalizar_cpf(dados.get("cpf"))
    tel = _normalizar_telefone(dados.get("telefone"))

    duplicados = detectar_duplicados({"nome": nome, "cpf": cpf, "telefone": tel})

    if duplicados:
        pendente = OnboardingPaciente(
            nome=nome or None,
            telefone=tel,
            cpf=cpf,
            email=(dados.get("email") or "").strip() or None,
            queixa=dados.get("queixa"),
            origem=origem,
            dados_sugeridos=dados,
            motivo=MOTIVO_DUPLICADO,
            status=STATUS_PENDENTE,
            duplicado_de=duplicados[0].id,
            criado_por=criado_por,
        )
        db.session.add(pendente)
        db.session.commit()
        return {
            "status": "pendente",
            "onboarding_id": pendente.id,
            "motivo": MOTIVO_DUPLICADO,
            "duplicados": [d.to_dict() for d in duplicados],
        }

    if not _dados_completos(dados):
        pendente = OnboardingPaciente(
            nome=nome or None,
            telefone=tel,
            cpf=cpf,
            email=(dados.get("email") or "").strip() or None,
            queixa=dados.get("queixa"),
            origem=origem,
            dados_sugeridos=dados,
            motivo=MOTIVO_INCOMPLETO,
            status=STATUS_PENDENTE,
            criado_por=criado_por,
        )
        db.session.add(pendente)
        db.session.commit()
        return {"status": "pendente", "onboarding_id": pendente.id, "motivo": MOTIVO_INCOMPLETO}

    paciente = _criar_paciente(dados)
    return {"status": "criado", "paciente_id": paciente.id}


def _criar_paciente(dados: Dict[str, Any]) -> Paciente:
    from datetime import datetime

    data_nasc = None
    if dados.get("data_nascimento"):
        try:
            data_nasc = datetime.strptime(dados["data_nascimento"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            data_nasc = None

    paciente = Paciente(
        nome=(dados.get("nome") or "").strip(),
        cpf=_normalizar_cpf(dados.get("cpf")),
        telefone=_normalizar_telefone(dados.get("telefone")),
        email=(dados.get("email") or "").strip() or None,
        data_nascimento=data_nasc,
        genero=dados.get("genero"),
    )
    db.session.add(paciente)
    db.session.commit()
    return paciente


def confirmar_pendencia(
    onboarding_id: int,
    *,
    acao: str = "criar",  # criar | usar_existente
    dados: Optional[Dict[str, Any]] = None,
    criado_por: Optional[str] = None,
) -> Dict[str, Any]:
    """Confirma um item de pendência: cria paciente ou usa o existente."""
    pendente = OnboardingPaciente.query.get(onboarding_id)
    if not pendente:
        raise ValueError("pendência inexistente")
    if pendente.status != STATUS_PENDENTE:
        raise ValueError("pendência já resolvida")

    payload = dados or (pendente.dados_sugeridos or {})
    payload = {**payload, "nome": payload.get("nome") or pendente.nome}

    if acao == "usar_existente" and pendente.duplicado_de:
        paciente = Paciente.query.get(pendente.duplicado_de)
        if paciente is None:
            raise ValueError("paciente duplicado não encontrado")
        if payload.get("telefone") and not paciente.telefone:
            paciente.telefone = _normalizar_telefone(payload["telefone"])
        if payload.get("email") and not paciente.email:
            paciente.email = payload["email"]
        db.session.commit()
        pendente.status = STATUS_APROVADO
        db.session.commit()
        return {"status": "aprovado", "paciente_id": paciente.id, "usado_existente": True}

    paciente = _criar_paciente(payload)
    pendente.status = STATUS_APROVADO
    pendente.duplicado_de = None
    db.session.commit()
    return {"status": "aprovado", "paciente_id": paciente.id, "usado_existente": False}


def descartar_pendencia(onboarding_id: int, *, criado_por: Optional[str] = None) -> None:
    pendente = OnboardingPaciente.query.get(onboarding_id)
    if not pendente:
        raise ValueError("pendência inexistente")
    pendente.status = STATUS_DESCARTADO
    db.session.commit()


def listar_pendentes(limit: int = 100) -> List[OnboardingPaciente]:
    return (
        OnboardingPaciente.query.filter_by(status=STATUS_PENDENTE)
        .order_by(OnboardingPaciente.created_at.asc())
        .limit(limit)
        .all()
    )
