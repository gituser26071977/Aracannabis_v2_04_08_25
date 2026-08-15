"""Pré-atendimento por tenant (página pública de cada profissional).

Cada profissional/clínica tem um slug público (`pre_atendimento_slug`,
ex.: 'dr.anderson', 'dr.ueslhe'). O paciente acessa /pre-atendimento/<slug>
e preenche o questionário.

Fluxo com conferência + pagamento:
1. Envio público -> cria PreConsulta com status `pendente_pagamento`
   (NÃO cria paciente ainda). Guarda as respostas e gera link de pagamento
   (Mercado Pago quando configurado).
2. Admin/médico confere os dados e confirma o pagamento recebido ->
   cria o Paciente (tenant) + anamnese estruturada + marca pré-consulta
   como `liberado`.
3. Sem conferência e pagamento confirmados, o pré-atendimento não vira
   paciente ativo.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import func, or_

from models import db, Paciente, PreConsulta, Anamnese, Profissional
from models_extra import UsuarioAssociacao

logger = logging.getLogger(__name__)

# Status do pré-atendimento
STATUS_PENDENTE_PAGAMENTO = "pendente_pagamento"
STATUS_LIBERADO = "liberado"
STATUS_REJEITADO = "rejeitado"

STATUS_PAG_PENDENTE = "pendente"
STATUS_PAG_PAGO = "pago"
STATUS_PAG_DISPENSADO = "dispensado"

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
    """Resolve o profissional + associação (tenant) pelo slug público.

    Quando o profissional pertence a mais de uma associação ativa, prioriza
    o instituto/clínica (a associação com mais membros ativos) — assim a
    saudação e o tenant de dados são uniformes (ex.: Instituto Vittalis).
    """
    if not slug:
        return None
    prof = Profissional.query.filter_by(pre_atendimento_slug=slug.strip().lower()).first()
    if not prof:
        return None
    links = UsuarioAssociacao.query.filter_by(
        profissional_id=prof.id, status="active"
    ).all()
    if not links:
        return {"profissional": prof, "associacao": None}

    if len(links) > 1:
        contagem = (
            db.session.query(UsuarioAssociacao.associacao_id, func.count(UsuarioAssociacao.profissional_id).label("n"))
            .filter(UsuarioAssociacao.status == "active")
            .group_by(UsuarioAssociacao.associacao_id)
            .all()
        )
        contagem_map = {cid: n for cid, n in contagem}
        links_sorted = sorted(
            links,
            key=lambda l: contagem_map.get(l.associacao_id, 0),
            reverse=True,
        )
        link = links_sorted[0]
    else:
        link = links[0]

    assoc = link.associacao
    return {"profissional": prof, "associacao": assoc}


def obter_questionario(profissional_id: int) -> Dict[str, Any]:
    """Retorna o questionário configurado do tenant (ou o padrão)."""
    return {"perguntas": QUESTIONARIO_PADRAO, "versao": "v1"}


def _gerar_link_pagamento(profissional, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Gera link de pagamento (Mercado Pago se configurado).

    Retorna {"link": ..., "preferencia_id": ..., "valor": ...}.
    Sem MP configurado, gera um link placeholder apontando para o próprio
    front de pagamento (a conferência manual confirma o recebimento).
    """
    valor = None
    try:
        from models import ConfiguracaoIA
        cfg = ConfiguracaoIA.query.filter_by(profissional_id=profissional.id).first()
        if cfg and cfg.valor_consulta:
            # valor_consulta pode ser "R$ 250,00" ou número
            import re
            nums = re.findall(r"\d+[.,]?\d*", cfg.valor_consulta or "")
            if nums:
                valor = float(nums[0].replace(".", "").replace(",", ".")) if "," in nums[0] else float(nums[0])
    except Exception:
        valor = None

    preferencia_id = None
    link = None
    try:
        from services.mercadopago_service import MercadoPagoService
        mp = MercadoPagoService()
        if mp.sdk and valor:
            resultado = mp.criar_preferencia_pagamento({
                "plano": "consulta",
                "periodo": "avulsa",
                "nome": dados.get("nome"),
                "email": dados.get("email") or "",
                "telefone": dados.get("telefone") or "",
                "user_id": f"pre_{profissional.id}",
            })
            if resultado.get("success"):
                preferencia_id = resultado.get("preference_id")
                link = resultado.get("init_point") or resultado.get("sandbox_init_point")
    except Exception as e:
        logger.warning(f"[pre_atendimento] MP indisponível: {e}")

    return {"link": link, "preferencia_id": preferencia_id, "valor": valor}


def registrar_pre_atendimento(slug: str, dados: Dict[str, Any]) -> Dict[str, Any]:
    """Registra o pré-atendimento (pendente de pagamento/conferência).

    NÃO cria o paciente ativo. Guarda as respostas e gera link de pagamento.
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

    pag = _gerar_link_pagamento(prof, dados)

    pre = PreConsulta(
        paciente_id=None,  # só é criado após conferência + pagamento
        associacao_id=assoc_id,
        queixa_principal=dados.get("queixa_principal") or dados.get("condicao_principal"),
        intensidade=dados.get("intensidade"),
        canal="web",
        status=STATUS_PENDENTE_PAGAMENTO,
        dados_solicitacao={
            **dados,
            "slug": slug,
            "profissional_id": prof.id,
            "profissional": prof.nome,
        },
        status_pagamento=STATUS_PAG_PENDENTE,
        valor_consulta=pag["valor"],
        preferencia_id=pag["preferencia_id"],
        link_pagamento=pag["link"],
    )
    db.session.add(pre)
    db.session.commit()

    return {
        "status": STATUS_PENDENTE_PAGAMENTO,
        "pre_consulta_id": pre.id,
        "associacao_id": assoc_id,
        "profissional": prof.nome,
        "instituto": _nome_instituto(assoc),
        "link_pagamento": pag["link"],
        "valor_consulta": pag["valor"],
        "mensagem": "Pré-atendimento recebido! Após a confirmação do pagamento e conferência, você será liberado(a).",
    }


def _nome_instituto(assoc) -> str:
    if not assoc:
        return ""
    if assoc.nome.strip().lower() == "vittalis":
        return "Instituto Vittalis"
    return assoc.nome


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

    # skip_tenant: o filtro é aplicado manualmente via associacao_id (P0-09).
    q = Paciente.query.execution_options(skip_tenant=True).filter(or_(*conds))
    if associacao_id:
        q = q.filter(Paciente.associacao_id == associacao_id)
    return q.all()


def conferir_pre_atendimento(
    pre_id: int,
    *,
    acao: str = "liberar",  # liberar | rejeitar
    pagamento_confirmado: bool = False,
    dispensar_pagamento: bool = False,
    conferido_por: Optional[str] = None,
    motivo: Optional[str] = None,
) -> Dict[str, Any]:
    """Confere um pré-atendimento: libera (cria paciente) ou rejeita.

    A liberação exige que o pagamento esteja confirmado (ou dispensado).
    """
    pre = PreConsulta.query.execution_options(skip_tenant=True).get(pre_id)
    if not pre:
        raise ValueError("pré-atendimento inexistente")
    if pre.status == STATUS_LIBERADO:
        raise ValueError("pré-atendimento já liberado")

    if acao == "rejeitar":
        pre.status = STATUS_REJEITADO
        pre.rejeitado_motivo = motivo
        pre.conferido_por = conferido_por
        pre.conferido_em = datetime.utcnow()
        db.session.commit()
        return {"status": STATUS_REJEITADO, "pre_consulta_id": pre.id}

    # Liberar: exige pagamento confirmado OU dispensado
    if not (pagamento_confirmado or dispensar_pagamento):
        return {
            "status": "aguardando_pagamento",
            "pre_consulta_id": pre.id,
            "erro": "Pagamento ainda não confirmado. Confirme o pagamento para liberar o paciente.",
        }

    dados = pre.dados_solicitacao or {}
    assoc_id = pre.associacao_id
    prof = Profissional.query.get(dados.get("profissional_id")) if dados.get("profissional_id") else None
    prof_id = prof.id if prof else None

    duplicados = detectar_duplicados_no_tenant(dados, assoc_id)
    if duplicados:
        paciente = duplicados[0]
        status_paciente = "existente"
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
            nome=(dados.get("nome") or "").strip(),
            cpf=_normalizar_cpf(dados.get("cpf")),
            telefone=_normalizar_telefone(dados.get("telefone")),
            email=(dados.get("email") or "").strip() or None,
            data_nascimento=data_nasc,
            genero=dados.get("genero") or None,
            diagnostico=dados.get("queixa_principal") or dados.get("condicao_principal") or None,
            associacao_id=assoc_id,
            profissional_responsavel_id=prof_id,
            consentimento_lgpd=True,
            data_consentimento=datetime.utcnow(),
        )
        db.session.add(paciente)
        db.session.flush()
        status_paciente = "criado"

    # Anamnese estruturada com as respostas
    anamnese = Anamnese(
        paciente_id=paciente.id,
        profissional_id=prof_id,
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

    # Vincular a pré-consulta ao paciente liberado
    pre.paciente_id = paciente.id
    pre.status = STATUS_LIBERADO
    pre.status_pagamento = STATUS_PAG_DISPENSADO if dispensar_pagamento else STATUS_PAG_PAGO
    pre.conferido_por = conferido_por
    pre.conferido_em = datetime.utcnow()
    pre.pagamento_confirmado_em = datetime.utcnow()
    db.session.commit()

    return {
        "status": STATUS_LIBERADO,
        "status_paciente": status_paciente,
        "paciente_id": paciente.id,
        "anamnese_id": anamnese.id,
        "pre_consulta_id": pre.id,
        "associacao_id": assoc_id,
    }


def listar_pre_atendimentos(tenant_ids=None, status=None, limit: int = 100) -> list:
    """Lista pré-atendimentos (fila de conferência).

    Usa skip_tenant=True para que o profissional consulte os pré-atendimentos
    de TODAS as associações que ele pertence (mesmo padrão P0-09 de
    obter_pacientes_acessiveis em routes/pacientes.py). O filtro de tenant é
    aplicado manualmente via `tenant_ids` (associações ativas do usuário).
    """
    q = PreConsulta.query.execution_options(skip_tenant=True).filter(
        PreConsulta.paciente_id.is_(None)
    )
    if status:
        q = q.filter(PreConsulta.status == status)
    if tenant_ids:
        q = q.filter(PreConsulta.associacao_id.in_(tenant_ids))
    return q.order_by(PreConsulta.data_pre_consulta.asc()).limit(limit).all()
