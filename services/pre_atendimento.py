"""Pré-atendimento por tenant (página pública de cada profissional).

Cada profissional/clínica tem um slug público (`pre_atendimento_slug`,
ex.: 'dr.anderson', 'dr.ueslhe'). O paciente acessa /pre-atendimento/<slug>,
preenche o questionário e o sistema:

1. Resolve o profissional + associação (tenant) pelo slug.
2. Checa duplicado DENTRO do tenant (nome/CPF/telefone filtrado por
   associacao_id).
3. Cria o paciente (se não existe) vinculado ao tenant.
4. Grava a anamnese estruturada com as respostas do questionário.
5. Registra a Pré-Consulta (queixa, intensidade, respostas) com tenant.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import or_

from models import db, Paciente, PreConsulta, Anamnese, Profissional
from models_extra import UsuarioAssociacao
from association.models import Associacao

logger = logging.getLogger(__name__)

# Perguntas padrão do questionário (base para todas as especialidades).
QUESTIONARIO_PADRAO = [
    {"key": "queixa_principal", "pergunta": "Qual é o motivo principal da sua consulta?", "tipo": "texto"},
    {"key": "sintomas_atuais", "pergunta": "Quais sintomas ou desconfortos você está sentindo?", "tipo": "texto"},
    {"key": "medicamentos_uso", "pergunta": "Quais medicamentos você usa atualmente?", "tipo": "texto"},
    {"key": "alergias", "pergunta": "Tem alguma alergia ou reação adversa?", "tipo": "texto"},
    {"key": "tratamentos_previos", "pergunta": "Já realizou outros tratamentos?", "tipo": "texto"},
    {"key": "exames_recentes", "pergunta": "Possui exames recentes?", "tipo": "texto"},
    {"key": "historico_cannabis", "pergunta": "Histórico de tratamentos anteriores?", "tipo": "texto"},
]


def _normalizar_telefone(v):
    return "".join(ch for ch in (v or "") if ch.isdigit()) or None


def _normalizar_cpf(v):
    return "".join(ch for ch in (v or "") if ch.isdigit()) or None


def resolver_tenant_por_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Resolve o profissional + associação (tenant) pelo slug público."""
    if not slug:
        return None
    prof = Profissional.query.filter_by(pre_atendimento_slug=slug.strip().lower()).first()
    if not prof:
        return None
    # Associação ativa do profissional (primeira)
    link = UsuarioAssociacao.query.filter_by(
        profissional_id=prof.id, status="active"
    ).first()
    assoc = link.associacao if link else None
    return {"profissional": prof, "associacao": assoc}


def obter_questionario(profissional_id: int) -> Dict[str, Any]:
    """Retorna o questionário configurado do tenant (ou o padrão)."""
    # TODO: permitir questionário personalizado por tenant (campo JSON).
    # Por ora usa o padrão clínico base.
    return {"perguntas": QUESTIONARIO_PADRAO, "versao": "v1"}


def detectar_duplicados_no_tenant(dados: Dict[str, Any], associacao_id: Optional[int]) -> list:
    """Busca pacientes duplicados DENTRO do tenant."""
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

    q = Paciente.query.filter(or_(*conds))
    if associacao_id:
        q = q.filter(Paciente.associacao_id == associacao_id)
    return q.all()


def processar_pre_atendimento(slug: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Processa o envio do pré-atendimento público por tenant.

    Returns:
        {"status": "criado"|"existente"|"duplicado", "paciente_id", "pre_consulta_id", "anamnese_id"?}
    """
    tenant = resolver_tenant_por_slug(slug)
    if not tenant:
        raise ValueError("slug inválido")

    prof = tenant["profissional"]
    assoc = tenant["associacao"]
    assoc_id = assoc.id if assoc else None

    nome = (dados.get("nome") or "").strip()
    if not nome:
        raise ValueError("nome é obrigatório")

    duplicados = detectar_duplicados_no_tenant(dados, assoc_id)

    if duplicados:
        # Reutiliza o paciente existente (mesmo tenant) e vincula a nova pré-consulta.
        paciente = duplicados[0]
        status = "existente"
        # Atualizar dados que faltam
        if not paciente.telefone and _normalizar_telefone(dados.get("telefone")):
            paciente.telefone = _normalizar_telefone(dados.get("telefone"))
        if not paciente.cpf and _normalizar_cpf(dados.get("cpf")):
            paciente.cpf = _normalizar_cpf(dados.get("cpf"))
        if not paciente.email and (dados.get("email") or "").strip():
            paciente.email = (dados.get("email") or "").strip()
        db.session.commit()
    else:
        data_nasc = None
        if dados.get("data_nascimento"):
            try:
                data_nasc = datetime.strptime(dados["data_nascimento"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                data_nasc = None
        paciente = Paciente(
            nome=nome,
            cpf=_normalizar_cpf(dados.get("cpf")),
            telefone=_normalizar_telefone(dados.get("telefone")),
            email=(dados.get("email") or "").strip() or None,
            data_nascimento=data_nasc,
            genero=dados.get("genero") or None,
            diagnostico=dados.get("queixa_principal") or dados.get("condicao_principal") or None,
            associacao_id=assoc_id,
            profissional_responsavel_id=prof.id,
            consentimento_lgpd=True,
            data_consentimento=datetime.utcnow(),
        )
        db.session.add(paciente)
        db.session.flush()
        status = "criado"

    # Pré-Consulta vinculada (tenant)
    pre = PreConsulta(
        paciente_id=paciente.id,
        associacao_id=assoc_id,
        queixa_principal=dados.get("queixa_principal") or dados.get("condicao_principal"),
        intensidade=dados.get("intensidade"),
        canal="web",
        status="concluida",
    )
    db.session.add(pre)
    db.session.flush()

    # Anamnese estruturada com as respostas do questionário
    anamnese = Anamnese(
        paciente_id=paciente.id,
        profissional_id=prof.id,
        condicao_principal=dados.get("queixa_principal") or dados.get("condicao_principal"),
        sintomas_atuais=dados.get("sintomas_atuais"),
        medicamentos_uso=dados.get("medicamentos_uso"),
        historico_cannabis=dados.get("historico_cannabis"),
        tratamentos_previos=dados.get("tratamentos_previos"),
        exames_recentes=dados.get("exames_recentes"),
        alergias=dados.get("alergias"),
        fonte="pre_atendimento",
    )
    db.session.add(anamnese)
    db.session.commit()

    return {
        "status": status,
        "paciente_id": paciente.id,
        "pre_consulta_id": pre.id,
        "anamnese_id": anamnese.id,
        "associacao_id": assoc_id,
        "profissional": prof.nome,
        "instituto": assoc.nome if assoc else None,
    }
