"""Chat do pré-atendimento — agente entrevista o lead e coleta dados.

Fluxo:
- Estado da conversa por `session_id` (Redis, expira em 1h).
- O agente (DeepSeek) conduz a entrevista: sauda, tira dúvidas sobre o
  instituto e faz as perguntas do questionário, extraindo dados estruturados
  (JSON) ao longo da conversa.
- Imagens (documentos/exames/laudos) são processadas via visão (Gemini):
  o texto extraído é anexado ao contexto e os campos identificados entram
  nos dados do lead.
- `finalizar_pre_atendimento_chat` envia os dados coletados para
  `registrar_pre_atendimento` (cria pendência de pagamento/conferência) —
  a liberação continua condicionada a conferência + pagamento.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis

from services.ai_agents import ai_manager
from services.pre_atendimento import (
    detectar_duplicados_no_tenant,
    registrar_pre_atendimento,
    resolver_tenant_por_slug,
)

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "siap-redis")
r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
STATE_EXPIRY = 3600  # 1h

# Campos que o agente deve extrair (ficha do paciente)
CAMPOS_FICHA = [
    "nome", "telefone", "cpf", "email", "data_nascimento", "genero",
    "queixa_principal", "sintomas_atuais", "medicamentos_uso", "alergias",
    "tratamentos_previos", "exames_recentes",
]

SYSTEM_PROMPT = """Você é {nome}, assistente virtual do {instituto}.

POSICIONAMENTO INSTITUCIONAL:
{posicionamento}

SUA MISSÃO: fazer o PRÉ-ATENDIMENTO de forma acolhedora e conversacional.
- Tire dúvidas sobre o instituto quando o lead perguntar.
- Colete os dados UM POR VEZ, na ordem, fazendo exatamente a pergunta do
  campo atual.
- Ao final, confirme os dados e informe que o envio está pronto.

PERGUNTA DO CAMPO ATUAL: {pergunta_campo}

REGRAS:
- NUNCA se apresente como uma clínica de Cannabis Medicinal.
- NUNCA dê diagnósticos ou prescrições.
- Respostas curtas e naturais (máx 3 frases), como uma conversa de WhatsApp.
- Faça a pergunta do campo atual de forma amigável, uma de cada vez.
"""

PERGUNTAS = {
    "nome": "Para começar, qual é o seu nome completo?",
    "telefone": "Qual é o seu telefone para contato?",
    "cpf": "Qual é o seu CPF?",
    "email": "Qual é o seu melhor e-mail?",
    "data_nascimento": "Qual é a sua data de nascimento? (Ex: 15/03/1985)",
    "genero": "Qual é o seu gênero?",
    "queixa_principal": "Qual é o principal motivo da sua consulta? (O que você gostaria de cuidar?)",
    "sintomas_atuais": "Quais sintomas ou desconfortos você está sentindo no momento?",
    "medicamentos_uso": "Quais medicamentos você usa atualmente?",
    "alergias": "Tem alguma alergia ou reação adversa a medicamentos?",
    "tratamentos_previos": "Já realizou outros tratamentos para essa condição?",
    "exames_recentes": "Possui exames recentes? Se tiver, pode enviar uma foto do laudo.",
}


def get_state(session_id: str) -> Dict:
    key = f"pre_chat:{session_id}"
    state_json = r.get(key)
    if state_json:
        return json.loads(state_json)
    new_state = {
        "slug": "",
        "dados": {},
        "campos_respondidos": [],
        "history": [],
        "docs": [],
        "pronto": False,
        "duplicado": False,
        "duplicados": [],
    }
    set_state(session_id, new_state)
    return new_state


def set_state(session_id: str, state: Dict):
    key = f"pre_chat:{session_id}"
    r.set(key, json.dumps(state), ex=STATE_EXPIRY)


def nova_sessao(slug: str) -> str:
    session_id = uuid.uuid4().hex[:16]
    set_state(session_id, {
        "slug": slug,
        "dados": {},
        "campos_respondidos": [],
        "history": [],
        "docs": [],
        "pronto": False,
        "duplicado": False,
        "duplicados": [],
    })
    return session_id


def _proximo_campo(state: Dict) -> Optional[str]:
    for c in CAMPOS_FICHA:
        if c not in state.get("campos_respondidos", []):
            return c
    return None


def _extrair_historia(history: List[Dict]) -> str:
    return "\n".join(f"{m['role']}: {m['content']}" for m in history[-12:])


def _checar_duplicado(slug: str, dados: Dict) -> List[Dict]:
    """Consulta o banco procurando paciente duplicado no tenant (skill DB).

    Retorna uma lista de pacientes existentes que batem com nome/CPF/telefone
    coletados até agora. O agente usa essa informação para avisar o lead.
    """
    try:
        tenant = resolver_tenant_por_slug(slug)
        if not tenant:
            return []
        assoc = tenant.get("associacao")
        assoc_id = assoc.id if assoc else None
        duplicados = detectar_duplicados_no_tenant(dados, assoc_id)
        return [
            {
                "id": d.id,
                "nome": d.nome,
                "telefone": d.telefone,
                "cpf": d.cpf,
            }
            for d in duplicados
        ]
    except Exception as e:
        logger.warning(f"[pre_chat] checagem de duplicado falhou: {e}")
        return []


def processar_mensagem(session_id: str, mensagem: str, imagem_b64: str = None, mime_type: str = None) -> Dict[str, Any]:
    """Processa uma mensagem do lead (texto e/ou imagem)."""
    state = get_state(session_id)
    slug = state.get("slug") or ""
    tenant = resolver_tenant_por_slug(slug)
    if not tenant:
        raise ValueError("instituto não encontrado")
    prof = tenant["profissional"]
    assoc = tenant["associacao"]
    nome_assoc = assoc.nome if assoc else prof.nome
    nome_instituto = "Instituto Vittalis" if nome_assoc.strip().lower() == "vittalis" else nome_assoc

    from models import ConfiguracaoIA
    cfg = ConfiguracaoIA.query.filter_by(profissional_id=prof.id).first()
    posicionamento = (cfg.regras_adicionais or "").strip() if cfg else ""

    # Se veio imagem, processar via visão (Gemini)
    if imagem_b64:
        texto_imagem = _processar_imagem(imagem_b64, mime_type)
        mensagem = f"{mensagem}\n\n[DOCUMENTO ANEXADO — CONTEÚDO]: {texto_imagem[:1500]}" if mensagem else f"[DOCUMENTO ANEXADO — CONTEÚDO]: {texto_imagem[:1500]}"
        state["docs"].append({"tipo": mime_type, "texto": texto_imagem[:2000]})

    # Guardar mensagem do lead
    state["history"].append({"role": "user", "content": mensagem})

    # Determinar o próximo campo a coletar
    campo = _proximo_campo(state)

    # Prompt do agente com instrução de extração
    system = SYSTEM_PROMPT.format(
        nome=cfg.nome_assistente if cfg else "LIA",
        instituto=nome_instituto,
        posicionamento=posicionamento or "Saúde e bem-estar.",
        pergunta_campo=PERGUNTAS.get(campo, "") if campo else "Todos os dados já foram coletados.",
    )
    system += f"""

Se o lead respondeu ao campo solicitado ({campo}), extraia o valor e responda APENAS com JSON:
{{"campo": "{campo}", "valor": "<valor extraído ou vazio se não souber>", "resposta": "<confirmação curta + a próxima pergunta>", "proximo_campo": "<próximo campo>"}}

Se a mensagem for uma dúvida sobre o instituto (não a resposta do campo), responda APENAS com:
{{"campo": null, "valor": null, "resposta": "<resposta amigável sobre o instituto>"}}

Responda APENAS com o JSON, sem texto extra."""

    messages = [{"role": "system", "content": system}]
    messages += state["history"][-10:]
    resp = ai_manager.chat_completion(messages=messages, temperature=0.4, max_tokens=600)
    content = resp.get("content", "")

    parsed = _parse_json(content)

    resposta_agente = ""
    campo_coletado = None
    if isinstance(parsed, dict):
        if parsed.get("campo"):
            # Marcamos como respondido mesmo se vazio (não travar a entrevista)
            valor = str(parsed.get("valor") or "").strip()
            state["dados"][parsed["campo"]] = valor
            if parsed["campo"] not in state["campos_respondidos"]:
                state["campos_respondidos"].append(parsed["campo"])
            campo_coletado = parsed["campo"]
        resposta_agente = parsed.get("resposta") or ""

        # Garantir que a próxima pergunta apareça na resposta
        proximo = parsed.get("proximo_campo") or _proximo_campo(state)
        if proximo and proximo not in resposta_agente:
            pergunta_prox = PERGUNTAS.get(proximo, "")
            if pergunta_prox and pergunta_prox not in resposta_agente:
                resposta_agente = f"{resposta_agente} {pergunta_prox}".strip()
    else:
        resposta_agente = content

    # ── Skill: checagem de duplicado no banco (nome/telefone/cpf) ──
    if campo_coletado in ("nome", "telefone", "cpf"):
        duplicados = _checar_duplicado(slug, state["dados"])
        if duplicados:
            state["duplicado"] = True
            state["duplicados"] = duplicados
            nomes = ", ".join(f"{d['nome']}" for d in duplicados[:2])
            aviso = (
                "\n\nℹ️ Identificamos que já existe um cadastro com esses dados "
                f"em nosso sistema ({nomes}). Não se preocupe: continuaremos seu "
                "pré-atendimento e nossa equipe fará a conferência. Se você já é "
                "paciente, pode seguir normalmente."
            )
            resposta_agente = f"{resposta_agente}{aviso}"
        elif not state.get("duplicado"):
            state["duplicado"] = False

    # Se todos os campos coletados, marcamos como pronto
    if _proximo_campo(state) is None:
        state["pronto"] = True
        resposta_agente += "\n\n✅ Todos os dados foram coletados! Posso finalizar seu pré-atendimento."

    state["history"].append({"role": "assistant", "content": resposta_agente})
    set_state(session_id, state)

    return {
        "session_id": session_id,
        "resposta": resposta_agente,
        "pronto": state["pronto"],
        "dados_parciais": state["dados"],
        "campos_respondidos": state["campos_respondidos"],
        "duplicado": state.get("duplicado", False),
        "duplicados": state.get("duplicados", []),
    }


def _processar_imagem(imagem_b64: str, mime_type: str = None) -> str:
    """Extrai texto de imagem via visão (Gemini)."""
    try:
        result = ai_manager.vision_completion(
            prompt=(
                "Extraia TODO o texto deste documento/laudo/exame médico. "
                "Se houver dados do paciente (nome, data, resultados, valores, "
                "diagnóstico), inclua tudo. Responda apenas com o texto extraído."
            ),
            image_data=imagem_b64,
        )
        return result.get("content") or ""
    except Exception as e:
        logger.warning(f"[pre_chat] visão falhou: {e}")
        return "[não foi possível ler o documento]"


def finalizar_pre_atendimento_chat(session_id: str) -> Dict[str, Any]:
    """Envia os dados coletados para o registro do pré-atendimento."""
    state = get_state(session_id)
    slug = state.get("slug") or ""
    dados = state.get("dados") or {}

    if not dados.get("nome"):
        raise ValueError("faltam dados essenciais (nome) para finalizar")

    # Anexar documentos extraídos como exames_recentes/observações
    docs = state.get("docs") or []
    if docs and not dados.get("exames_recentes"):
        dados["exames_recentes"] = "\n\n".join(
            f"Documento: {d.get('texto', '')[:800]}" for d in docs
        )

    resultado = registrar_pre_atendimento(slug, dados)

    # Limpar sessão
    r.delete(f"pre_chat:{session_id}")

    return resultado


def _parse_json(content: str) -> Optional[Dict]:
    content = (content or "").strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?|```$", "", content).strip()
    try:
        return json.loads(content)
    except Exception:
        m = re.search(r"\{.*\}", content, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return None
