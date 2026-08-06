"""Onboarding de pacientes (padrão SGA) — cadastro administrativo com IA.

- `sugerir_dados(texto)`: extrai nome/telefone/cpf/email/queixa de texto livre
  via LLM (com fallback heurístico por regex).
- `sugerir_dados_de_documento(arquivo, nome)`: OCR de imagem/PDF + sugestão.
- `salvar_documento(...)` / `vincular_documento(...)`: guarda o documento e
  vincula ao paciente quando cadastrado.
- `detectar_duplicados(dados)`: busca pacientes por cpf, telefone e nome.
- `registrar_paciente(dados)`: cria direto (sem duplicado e completo) ou abre
  pendência (duplicado / dados incompletos) para o administrativo confirmar.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_

from models import db, Paciente, OnboardingPaciente, OnboardingDocumento

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

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
    documento_id: Optional[int] = None,
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
            dados_sugeridos={**dados, "documento_id": documento_id} if documento_id else dados,
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
            dados_sugeridos={**dados, "documento_id": documento_id} if documento_id else dados,
            motivo=MOTIVO_INCOMPLETO,
            status=STATUS_PENDENTE,
            criado_por=criado_por,
        )
        db.session.add(pendente)
        db.session.commit()
        return {"status": "pendente", "onboarding_id": pendente.id, "motivo": MOTIVO_INCOMPLETO}

    paciente = _criar_paciente(dados)
    if documento_id:
        vincular_documento(documento_id, paciente.id)
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
        _vincular_doc_pendente(pendente, paciente.id)
        return {"status": "aprovado", "paciente_id": paciente.id, "usado_existente": True}

    paciente = _criar_paciente(payload)
    pendente.status = STATUS_APROVADO
    pendente.duplicado_de = None
    db.session.commit()
    _vincular_doc_pendente(pendente, paciente.id)
    return {"status": "aprovado", "paciente_id": paciente.id, "usado_existente": False}


def _vincular_doc_pendente(pendente: OnboardingPaciente, paciente_id: int) -> None:
    doc_id = (pendente.dados_sugeridos or {}).get("documento_id")
    if doc_id:
        vincular_documento(int(doc_id), paciente_id)


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


# ────────────────────────────────────────────────────────────────────
# Documentos (upload → OCR → sugestão)
# ────────────────────────────────────────────────────────────────────

def _extensao(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _ocr_imagem(arquivo_bytes: bytes) -> Tuple[str, float]:
    """OCR de imagem via Tesseract (por+eng). Retorna (texto, confianca)."""
    from services.ocr_service import OCRService

    b64 = base64.b64encode(arquivo_bytes).decode("ascii")
    resultado = OCRService().extract_text_from_base64(b64)
    texto = (resultado.get("texto") or "").strip()
    confianca = float(resultado.get("confianca") or 0)
    return texto, confianca


def _ocr_pdf(arquivo_bytes: bytes) -> Tuple[str, float]:
    """OCR de PDF (cada página via pdf2image + Tesseract)."""
    import tempfile

    from pdf2image import convert_from_bytes

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(arquivo_bytes)
        tmp_path = tmp.name
    try:
        paginas = convert_from_bytes(arquivo_bytes, dpi=200)
        textos: List[str] = []
        confs: List[float] = []
        for img in paginas:
            import io

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            t, c = _ocr_imagem(buf.getvalue())
            if t:
                textos.append(t)
            confs.append(c)
        return "\n".join(textos), (sum(confs) / len(confs) if confs else 0)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def extrair_texto_arquivo(arquivo_bytes: bytes, filename: str) -> Tuple[str, float]:
    """Extrai texto de imagem ou PDF. Retorna (texto, confianca)."""
    ext = _extensao(filename)
    if ext == "pdf":
        return _ocr_pdf(arquivo_bytes)
    return _ocr_imagem(arquivo_bytes)


def sugerir_dados_de_documento(arquivo_bytes: bytes, filename: str) -> Dict[str, Any]:
    """OCR do documento + sugestão estruturada do paciente.

    Returns:
        {"sugestao": {...}, "texto_extraido": str, "confianca": float}
    """
    texto, confianca = extrair_texto_arquivo(arquivo_bytes, filename)
    sugestao = sugerir_dados(texto) if texto else {}
    return {"sugestao": sugestao, "texto_extraido": texto, "confianca": confianca}


def salvar_documento(
    arquivo_bytes: bytes,
    filename: str,
    *,
    mime: str | None,
    texto_extraido: str,
    confianca: float,
    criado_por: Optional[str] = None,
) -> OnboardingDocumento:
    """Salva o arquivo em uploads/onboarding/ e cria o registro."""
    ext = _extensao(filename)
    nome_salvo = f"{uuid.uuid4().hex[:16]}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
    from werkzeug.utils import secure_filename

    pasta = os.path.join(
        os.getcwd(), "uploads", "onboarding"
    )
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, nome_salvo)
    with open(caminho, "wb") as f:
        f.write(arquivo_bytes)

    doc = OnboardingDocumento(
        nome_original=secure_filename(filename) or filename,
        caminho_arquivo=caminho,
        mime=mime,
        texto_extraido=texto_extraido[:5000] if texto_extraido else None,
        confianca=round(confianca, 2) if confianca else None,
        criado_por=criado_por,
    )
    db.session.add(doc)
    db.session.commit()
    return doc


def vincular_documento(documento_id: int, paciente_id: int) -> None:
    """Vincula o documento ao paciente (após cadastro/confirmação)."""
    doc = OnboardingDocumento.query.get(documento_id)
    if doc is None:
        raise ValueError("documento inexistente")
    doc.paciente_id = paciente_id
    db.session.commit()
