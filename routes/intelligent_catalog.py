"""
Rotas do Motor de Cadastro Inteligente (Produto + Estoque)

Mesma lógica do SGAC (intelligent_onboarding) aplicada a catálogo/estoque:

  POST /api/icatalog/upload            → processa documento (LLM) e cria fila de revisão
  GET  /api/icatalog/reviews           → lista pendentes de revisão humana
  GET  /api/icatalog/reviews/stats     → estatísticas por status
  POST /api/icatalog/reviews/<id>/action → aprovar / rejeitar / atualizar_existente
  GET  /api/icatalog/reviews/<id>      → detalhe de um registro

Fluxo replicado do SGAC: duplicidade (barras → nome similar) → sugestão de
fusão → cadastro automático ou fila de revisão humana.
"""
from __future__ import annotations

import logging
from typing import Optional

from flask import Blueprint, g, jsonify, request
from werkzeug.utils import secure_filename

from models_extra import ICatalogProcess, create_audit_entry
from services.catalogo_document_processor import document_processor
from services.intelligent_catalog import intelligent_catalog_service as icatalog

logger = logging.getLogger(__name__)

icatalog_bp = Blueprint("icatalog", __name__, url_prefix="/api/icatalog")

UPLOAD_DIR = "/tmp/icatalog_uploads"


def _get_profissional_id() -> Optional[int]:
    from flask_jwt_extended import get_jwt_identity
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return identity.get("profissional_id") or identity.get("id")
    return identity


def _get_associacao_id() -> Optional[int]:
    assoc = getattr(g, "current_association", None)
    if assoc is not None:
        return assoc.id
    return request.headers.get("X-Associacao-Id", type=int)


@icatalog_bp.route("/upload", methods=["POST"])
def upload_e_processar():
    """Processa documento (PDF/XLSX/imagem) e cria registros na fila."""
    from flask_jwt_extended import verify_jwt_in_request

    try:
        verify_jwt_in_request()
        profissional_id = _get_profissional_id()
    except Exception:
        return jsonify({"error": "Token inválido ou expirado"}), 401

    if "arquivo" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["arquivo"]
    if not file.filename:
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    filename = secure_filename(file.filename)
    if not document_processor.allowed_file(filename):
        return jsonify({
            "error": "Formato não suportado",
            "message": "Use: PDF, PNG, JPG, XLSX",
        }), 400

    associacao_id = _get_associacao_id() or 1

    file_bytes = file.read()
    mime = file.mimetype or "application/octet-stream"

    resultado = icatalog.processar_arquivo(
        file_bytes=file_bytes,
        filename=filename,
        mime_type=mime,
        profissional_id=profissional_id or 0,
        associacao_id=associacao_id,
    )

    if not resultado.get("success"):
        return jsonify(resultado), 400

    create_audit_entry(
        tenant_id=associacao_id,
        user_id=profissional_id,
        action="icatalog.upload",
        resource_type="catalogo",
        details={"filename": filename, "detected_count": resultado.get("detected_count")},
    )

    return jsonify(resultado), 201


@icatalog_bp.route("/reviews", methods=["GET"])
def listar_revisoes():
    """Lista registros pendentes de revisão humana."""
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Token inválido ou expirado"}), 401

    associacao_id = _get_associacao_id()
    pendentes = icatalog.listar_pendentes(associacao_id=associacao_id)
    return jsonify({"reviews": pendentes, "count": len(pendentes)})


@icatalog_bp.route("/reviews/stats", methods=["GET"])
def estatisticas_revisao():
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Token inválido ou expirado"}), 401

    associacao_id = _get_associacao_id()
    return jsonify(icatalog.estatisticas(associacao_id=associacao_id))


@icatalog_bp.route("/reviews/<int:process_id>", methods=["GET"])
def obter_revisao(process_id: int):
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Token inválido ou expirado"}), 401

    proc = ICatalogProcess.query.get(process_id)
    if not proc:
        return jsonify({"error": "Registro não encontrado"}), 404
    return jsonify(proc.to_dict())


@icatalog_bp.route("/reviews/<int:process_id>/action", methods=["POST"])
def aplicar_acao(process_id: int):
    """Aplica decisão do operador: aprovar | rejeitar | atualizar_existente."""
    try:
        verify_jwt_in_request()
        profissional_id = _get_profissional_id()
    except Exception:
        return jsonify({"error": "Token inválido ou expirado"}), 401

    data = request.get_json(silent=True) or {}
    decisao = (data.get("decisao") or data.get("action") or "").lower()

    resultado = icatalog.aplicar_revisao(
        process_id=process_id,
        decisao=decisao,
        profissional_id=profissional_id or 0,
    )

    if not resultado.get("success"):
        return jsonify(resultado), 400

    proc = ICatalogProcess.query.get(process_id)
    create_audit_entry(
        tenant_id=proc.associacao_id if proc else 1,
        user_id=profissional_id,
        action="icatalog.review",
        resource_type="catalogo",
        resource_id=process_id,
        details={"decisao": decisao, "produto_id": resultado.get("produto_id")},
    )

    return jsonify(resultado)
