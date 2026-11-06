"""Dashboard do Paciente — visão única, curada e consultável.

Expõe ao paciente autenticado (JWT com user_type=patient) uma agregação de
TODOS os seus dados em formato de dashboard:

  GET /me/dashboard                          → resumo + indicadores + recentes
  GET /me/documentos                         → documentos/laudos/exames p/ download
  GET /me/documentos/<tipo>/<ref>/arquivo    → download seguro (posse validada)

Regras de segurança:
  * Escopo sempre por paciente_id do token (nunca por parâmetro de URL).
  * Download só serve arquivo cujo registro pertence ao paciente logado.
  * Contenção de path (realpath + prefixo) e validação de nome.

Reaproveita os endpoints de routes/patient_portal.py e
routes/patient_rastreios.py; aqui apenas agrega e dá acesso a arquivos.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, text

from models import (
    db,
    Paciente,
    Consulta,
    Prescricao,
    Exame,
    ExameImagem,
    Evolucao,
    OnboardingDocumento,
)
from routes.patient_portal import (
    require_patient,
    _exame_paciente,
    _evolucao_curada,
    _prescricao_paciente,
)

patient_dashboard_bp = Blueprint("patient_dashboard", __name__)

# Nome dos laudos de HC gerados pelo HCReportService: laudo_hc_<paciente_id>_<ts>.pdf
_LAUDO_HC_RE = re.compile(r"^laudo_hc_(\d+)_\d{8,14}\.pdf$", re.IGNORECASE)


def _pid() -> int:
    """Id do paciente logado (o JWT traz str)."""
    return int(get_jwt_identity())


def _uploads_dir(sub: str = "exames") -> str:
    """Resolve o diretório de uploads de exames de forma absoluta."""
    base = current_app.config.get("UPLOAD_FOLDER_EXAMES")
    if not base:
        base = os.path.join(os.getcwd(), "uploads", "exames")
    if not os.path.isabs(base):
        base = os.path.join(current_app.root_path, base)
    return base if sub == "exames" else os.path.join(os.path.dirname(base), sub)


def _ext_mime(nome: str) -> str:
    ext = os.path.splitext(nome or "")[1].lower()
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".txt": "text/plain",
    }.get(ext, "application/octet-stream")


def _streak_registros(paciente_id: int):
    """Adesão do check-in: dias seguidos + últimos registros (tabela opcional)."""
    try:
        rows = db.session.execute(text(
            "SELECT data, sintoma, intensidade, observacao FROM patient_registros "
            "WHERE paciente_id=:p ORDER BY data DESC, id DESC LIMIT 30"
        ), {"p": paciente_id}).mappings().all()
    except Exception:  # noqa: BLE001 — tabela pode não existir em bases antigas
        try:
            db.session.rollback()
        except Exception:  # noqa: BLE001
            pass
        return 0, []

    def _iso(v):
        if v is None:
            return None
        return v.isoformat() if hasattr(v, "isoformat") else str(v)[:10]

    dias = {_iso(r["data"]) for r in rows if _iso(r["data"])}
    streak = 0
    cursor = datetime.utcnow().date()
    while cursor.isoformat() in dias:
        streak += 1
        cursor -= timedelta(days=1)
    registros = [{
        "data": _iso(r["data"]),
        "sintoma": r["sintoma"],
        "intensidade": r["intensidade"],
        "observacao": r["observacao"],
    } for r in rows]
    return streak, registros


@patient_dashboard_bp.route("/me/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    """Agrega em uma única chamada o essencial do dashboard do paciente."""
    error = require_patient()
    if error:
        return error

    pid = _pid()
    paciente = Paciente.query.get(pid)
    if not paciente:
        return jsonify({"error": "Paciente não encontrado"}), 404

    consultas = Consulta.query.filter_by(paciente_id=pid).order_by(
        desc(Consulta.data_hora)
    ).all()
    proximas = [c for c in consultas if c.data_hora and c.data_hora > datetime.utcnow()]
    proximas.sort(key=lambda c: c.data_hora)

    exames = Exame.query.filter_by(paciente_id=pid).order_by(
        desc(Exame.data_exame)
    ).limit(6).all()

    evolucoes = Evolucao.query.filter_by(paciente_id=pid).order_by(
        desc(Evolucao.data_evolucao)
    ).limit(3).all()

    prescricoes = Prescricao.query.filter_by(paciente_id=pid).order_by(
        desc(Prescricao.data_emissao)
    ).all()
    prescricoes_ativas = prescricoes  # modelo sem flag `ativo`; exibimos as emitidas

    # Rastreios (reaproveita o histórico já montado no módulo de rastreios).
    try:
        from routes.patient_rastreios import _historico

        rastreios = _historico(pid)[:5]
    except Exception:  # noqa: BLE001
        rastreios = []

    streak, registros = _streak_registros(pid)

    total_documentos = _contar_documentos(pid)

    perfil = paciente.to_dict()
    resumo = {
        "nome": paciente.nome,
        "primeiro_nome": (paciente.nome or "").split(" ")[0],
        "data_nascimento": perfil.get("data_nascimento"),
        "condicao_medica": getattr(paciente, "condicao_medica", None)
        or getattr(paciente, "diagnostico", None),
        "composicao": getattr(paciente, "composicao", None),
        "dosagem": getattr(paciente, "dosagem", None),
        "horarios": getattr(paciente, "horarios", None),
        "profissional_responsavel": getattr(
            getattr(paciente, "profissional_responsavel", None), "nome", None
        ),
    }

    return jsonify({
        "perfil": resumo,
        "indicadores": {
            "consultas": len(consultas),
            "consultas_futuras": len(proximas),
            "exames": Exame.query.filter_by(paciente_id=pid).count(),
            "evolucoes": Evolucao.query.filter_by(paciente_id=pid).count(),
            "prescricoes_ativas": len(prescricoes_ativas),
            "documentos": total_documentos,
            "rastreios": len(rastreios),
            "dias_seguidos_checkin": streak,
        },
        "proximas_consultas": [c.to_dict() for c in proximas[:3]],
        "ultimas_consultas": [c.to_dict() for c in consultas[:3]],
        "ultimos_exames": [_exame_paciente(e) for e in exames],
        "ultimas_evolucoes": [_evolucao_curada(e) for e in evolucoes],
        "prescricoes_ativas": [_prescricao_paciente(p) for p in prescricoes_ativas],
        "ultimos_rastreios": rastreios,
        "ultimos_registros": registros[:5],
    }), 200


# ─── Documentos (exames com arquivo, laudos, documentos de onboarding) ──────

def _listar_documentos(pid: int):
    docs = []

    # 1) Arquivos de exame (imagens + laudos de imagem)
    imagens = (
        db.session.query(ExameImagem, Exame)
        .join(Exame, ExameImagem.exame_id == Exame.id)
        .filter(Exame.paciente_id == pid)
        .all()
    )
    for img, exame in imagens:
        docs.append({
            "tipo": "exame_imagem",
            "ref": str(img.id),
            "titulo": exame.titulo or img.arquivo_nome,
            "nome_arquivo": img.arquivo_nome,
            "categoria": "Exame",
            "data": exame.data_exame.isoformat() if exame.data_exame else None,
            "mime": _ext_mime(img.arquivo_nome),
            "laudo": img.laudo,
            "tem_arquivo": bool(img.arquivo_caminho),
        })

    # 2) Receitas/prescrições em PDF
    prescricoes = Prescricao.query.filter_by(paciente_id=pid).order_by(
        desc(Prescricao.data_emissao)
    ).all()
    for presc in prescricoes:
        if not presc.arquivo_path:
            continue
        nome = presc.arquivo_path
        docs.append({
            "tipo": "prescricao",
            "ref": str(presc.id),
            "titulo": "Receita / Prescrição",
            "nome_arquivo": nome,
            "categoria": "Documento",
            "data": presc.data_emissao.isoformat() if presc.data_emissao else None,
            "mime": "application/pdf",
            "laudo": None,
            "tem_arquivo": True,
        })

    # 3) Documentos enviados no onboarding (vinculados ao paciente)
    onboarding = OnboardingDocumento.query.filter_by(paciente_id=pid).all()
    for doc in onboarding:
        docs.append({
            "tipo": "onboarding",
            "ref": str(doc.id),
            "titulo": doc.nome_original,
            "nome_arquivo": doc.nome_original,
            "categoria": "Documento",
            "data": doc.created_at.isoformat() if doc.created_at else None,
            "mime": doc.mime or _ext_mime(doc.nome_original),
            "laudo": None,
            "tem_arquivo": bool(doc.caminho_arquivo),
        })

    # 4) Laudos de HC gerados para o paciente (arquivos na pasta de exames)
    try:
        pasta = _uploads_dir("exames")
        if os.path.isdir(pasta):
            for nome in os.listdir(pasta):
                m = _LAUDO_HC_RE.match(nome)
                if not m or int(m.group(1)) != pid:
                    continue
                caminho = os.path.join(pasta, nome)
                docs.append({
                    "tipo": "laudo_hc",
                    "ref": nome,
                    "titulo": "Laudo de HC (Habeas Corpus)",
                    "nome_arquivo": nome,
                    "categoria": "Laudo",
                    "data": datetime.fromtimestamp(
                        os.path.getmtime(caminho), tz=timezone.utc
                    ).isoformat(),
                    "mime": "application/pdf",
                    "laudo": None,
                    "tem_arquivo": True,
                })
    except Exception:  # noqa: BLE001
        current_app.logger.warning("patient_dashboard: falha ao varrer laudos HC")

    docs.sort(key=lambda d: d.get("data") or "", reverse=True)
    return docs


def _contar_documentos(pid: int) -> int:
    try:
        return len(_listar_documentos(pid))
    except Exception:  # noqa: BLE001
        return 0


@patient_dashboard_bp.route("/me/documentos", methods=["GET"])
@jwt_required()
def listar_documentos():
    """Documentos do paciente: exames com arquivo, laudos e documentos."""
    error = require_patient()
    if error:
        return error

    pid = _pid()
    docs = _listar_documentos(pid)
    return jsonify({"total": len(docs), "documentos": docs}), 200


@patient_dashboard_bp.route("/me/documentos/<tipo>/<ref>/arquivo", methods=["GET"])
@jwt_required()
def baixar_documento(tipo, ref):
    """Download seguro de um documento do próprio paciente logado."""
    error = require_patient()
    if error:
        return error

    pid = _pid()

    if tipo == "exame_imagem":
        if not str(ref).isdigit():
            return jsonify({"error": "Referência inválida"}), 400
        img = ExameImagem.query.get(int(ref))
        if not img:
            return jsonify({"error": "Documento não encontrado"}), 404
        exame = Exame.query.get(img.exame_id)
        if not exame or int(exame.paciente_id) != pid:
            return jsonify({"error": "Acesso negado"}), 403
        if not img.arquivo_caminho:
            return jsonify({"error": "Arquivo indisponível"}), 404
        return _servir_em(_uploads_dir("exames"), img.arquivo_caminho, img.arquivo_nome)

    if tipo == "onboarding":
        if not str(ref).isdigit():
            return jsonify({"error": "Referência inválida"}), 400
        doc = OnboardingDocumento.query.get(int(ref))
        if not doc:
            return jsonify({"error": "Documento não encontrado"}), 404
        if int(doc.paciente_id or 0) != pid:
            return jsonify({"error": "Acesso negado"}), 403
        caminho = os.path.realpath(doc.caminho_arquivo or "")
        base = os.path.realpath(_uploads_dir("onboarding"))
        if not caminho.startswith(base + os.sep) or not os.path.isfile(caminho):
            return jsonify({"error": "Arquivo indisponível"}), 404
        return send_from_directory(
            base, os.path.basename(caminho),
            mimetype=doc.mime or _ext_mime(doc.nome_original),
            as_attachment=True, download_name=doc.nome_original,
        )

    if tipo == "laudo_hc":
        m = _LAUDO_HC_RE.match(ref or "")
        if not m or int(m.group(1)) != pid:
            return jsonify({"error": "Arquivo inválido"}), 403
        return _servir_em(_uploads_dir("exames"), ref, ref)

    if tipo == "prescricao":
        if not str(ref).isdigit():
            return jsonify({"error": "Referência inválida"}), 400
        presc = Prescricao.query.get(int(ref))
        if not presc:
            return jsonify({"error": "Documento não encontrado"}), 404
        if int(presc.paciente_id) != pid:
            return jsonify({"error": "Acesso negado"}), 403
        if not presc.arquivo_path:
            return jsonify({"error": "Arquivo indisponível"}), 404
        data = presc.data_emissao.strftime("%Y%m%d") if presc.data_emissao else "receita"
        return _servir_em(
            _uploads_dir("exames"), presc.arquivo_path, f"Prescricao_{data}.pdf"
        )

    return jsonify({"error": "Tipo de documento desconhecido"}), 400


def _servir_em(diretorio: str, filename: str, download_name: str):
    """Serve um arquivo contido em `diretorio` (anti path traversal)."""
    base = os.path.realpath(diretorio)
    caminho = os.path.realpath(os.path.join(base, filename))
    if not caminho.startswith(base + os.sep) or not os.path.isfile(caminho):
        return jsonify({"error": "Arquivo não encontrado"}), 404
    return send_from_directory(
        base, os.path.basename(caminho),
        mimetype=_ext_mime(download_name),
        as_attachment=True, download_name=download_name,
    )
