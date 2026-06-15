"""
intelligent_import.py — Endpoints para IntelligentImportService

Endpoints:
  POST /api/intelligent-import/analyze   → recebe arquivo, retorna preview (não persiste)
  POST /api/intelligent-import/apply     → aplica preview validado (persiste Profissional / Consultorio / Disponibilidade)
  GET  /api/intelligent-import/options   → lista intents suportados + descrição

Tenant scoping: usa `g.current_association` (populado pelo tenant_middleware).
Apenas gestores (admin), secretárias e profissionais da clínica podem importar.
Aplica auditoria via models_extra.create_audit_entry.

Parte da feature feat/intelligent-import (fase I4).
"""
from __future__ import annotations

import io
import logging
from datetime import datetime, time
from typing import Any, Dict, List, Optional

from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from models import (
    Consultorio,
    Disponibilidade,
    Profissional,
    SolicitacoesCadastro,
    db,
)
from models_extra import UsuarioAssociacao, create_audit_entry
from services.conselho_validator import (
    CONSELHO_NONE,
    inferir_tipo_pela_role,
    normalizar_tipo_conselho,
)
from services.intelligent_import_service import (
    ImportIntent,
    IntelligentImportService,
    ImportPreview,
)

logger = logging.getLogger(__name__)

intelligent_import_bp = Blueprint("intelligent_import", __name__)

# Roles que podem importar na clínica
ALLOWED_ROLES = {"admin", "secretary", "secretaria", "manager", "gestor", "profissional", "auxiliar"}


# REDACTED
# Helpers
# REDACTED
def _current_user_id() -> int:
    return int(get_jwt_identity())


def _require_association() -> Optional[Any]:
    assoc = getattr(g, "current_association", None)
    if assoc is None:
        return None
    return assoc


def _role_allows(role: Optional[str]) -> bool:
    if not role:
        return False
    return role.lower() in ALLOWED_ROLES


# REDACTED
# GET /options — listar intents suportados
# REDACTED
@intelligent_import_bp.route("/intelligent-import/options", methods=["GET"])
@jwt_required()
def list_options():
    """Lista intents suportados para popular dropdown no frontend."""
    options = [
        {
            "intent": ImportIntent.PROFISSIONAIS_SAUDE.value,
            "label": "Profissionais de Saúde",
            "description": "Médicos, psicólogos, enfermeiros, nutricionistas, fisioterapeutas",
            "campos_esperados": ["nome", "email", "telefone", "conselho_tipo",
                                "conselho_numero", "uf", "especialidade"],
        },
        {
            "intent": ImportIntent.EQUIPE_ADMIN.value,
            "label": "Equipe Administrativa",
            "description": "Secretárias, gestores, recepcionistas",
            "campos_esperados": ["nome", "email", "telefone", "funcao"],
        },
        {
            "intent": ImportIntent.DISPONIBILIDADE.value,
            "label": "Disponibilidade / Horários",
            "description": "Grade de horários de atendimento por profissional",
            "campos_esperados": ["profissional", "dia_semana", "hora_inicio",
                                "hora_fim", "intervalo_min", "consultorio"],
        },
        {
            "intent": ImportIntent.CONSULTORIOS.value,
            "label": "Consultórios / Salas",
            "description": "Salas, andares, recursos da clínica",
            "campos_esperados": ["nome", "andar", "ala", "capacidade", "recursos"],
        },
    ]
    return jsonify({"success": True, "intents": options}), 200


# REDACTED
# POST /analyze — recebe arquivo, retorna preview (NÃO persiste)
# REDACTED
@intelligent_import_bp.route("/intelligent-import/analyze", methods=["POST"])
@jwt_required()
def analyze_file():
    """Recebe um arquivo (multipart/form-data), extrai dados via LLM e
    retorna preview estruturado para o frontend confirmar antes de aplicar.

    Form fields:
      - file: arquivo (PDF/XLSX/CSV/DOCX/TXT)
      - intent (opcional): força um intent; senão é detectado por heurística
    """
    assoc = _require_association()
    if assoc is None:
        return jsonify({
            "success": False,
            "error": "Usuário não vinculado a nenhuma clínica. Crie ou entre em uma clínica para importar dados.",
        }), 403

    if not _role_allows(getattr(g, "user_role", None)):
        return jsonify({
            "success": False,
            "error": f"Role '{g.user_role}' não autorizada a importar dados. Use um perfil de gestor/secretária/profissional.",
        }), 403

    if "file" not in request.files:
        return jsonify({"success": False, "error": "Campo 'file' é obrigatório (multipart/form-data)."}), 400

    uploaded = request.files["file"]
    if not uploaded.filename:
        return jsonify({"success": False, "error": "Arquivo sem nome."}), 400

    file_bytes = uploaded.read()
    if not file_bytes:
        return jsonify({"success": False, "error": "Arquivo vazio."}), 400

    intent_override = request.form.get("intent") or None

    svc = IntelligentImportService()
    if not svc.allowed_file(uploaded.filename):
        return jsonify({
            "success": False,
            "error": f"Formato não suportado. Aceitos: {sorted(svc.ALLOWED_EXTENSIONS)}",
        }), 400

    try:
        preview: ImportPreview = svc.analyze(
            file_bytes=file_bytes,
            filename=uploaded.filename,
            intent_override=intent_override,
        )
    except Exception as exc:
        logger.exception("Falha inesperada no analyze")
        return jsonify({"success": False, "error": f"Erro ao analisar: {exc}"}), 500

    # Auditoria (best-effort; não bloqueia resposta)
    try:
        create_audit_entry(
            tenant_id=assoc.id,
            user_id=_current_user_id(),
            action="intelligent_import.analyze",
            resource_type="file",
            resource_id=uploaded.filename,
            details={
                "intent": preview.intent,
                "intent_confianca": preview.intent_confianca,
                "total_registros": preview.total_registros,
                "validos": preview.validos,
                "invalidos": preview.invalidos,
                "ai_provider": preview.ai_provider,
                "ai_model": preview.ai_model,
            },
            ip=request.remote_addr,
        )
    except Exception as exc:
        logger.warning("Falha ao registrar audit (analyze): %s", exc)

    return jsonify({
        "success": True,
        "preview": {
            "intent": preview.intent,
            "intent_confianca": preview.intent_confianca,
            "filename": preview.filename,
            "total_registros": preview.total_registros,
            "validos": preview.validos,
            "invalidos": preview.invalidos,
            "headers_detectados": preview.headers_detectados,
            "resumo_erros": preview.resumo_erros,
            "records": preview.records,
            "ai_provider": preview.ai_provider,
            "ai_model": preview.ai_model,
        },
    }), 200


# REDACTED
# POST /apply — aplica preview (cliente envia os records validados)
# REDACTED
@intelligent_import_bp.route("/intelligent-import/apply", methods=["POST"])
@jwt_required()
def apply_import():
    """Aplica um preview já analisado e confirmado pelo usuário.

    Body JSON:
      {
        "intent": "profissionais_saude" | "equipe_admin" | "disponibilidade" | "consultorios",
        "records": [...]  // mesma estrutura de preview.records
      }

    Para profissionais/equipe: cria Profissional (se não existir) + UsuarioAssociacao.
    Para consultorios: cria Consultorio vinculado à associação.
    Para disponibilidade: cria Disponibilidade por profissional (precisa do nome
    resolver para profissional_id; se não achar, registra aviso).
    """
    assoc = _require_association()
    if assoc is None:
        return jsonify({"success": False, "error": "Usuário sem clínica vinculada."}), 403

    if not _role_allows(getattr(g, "user_role", None)):
        return jsonify({"success": False, "error": "Sem permissão para aplicar importação."}), 403

    data = request.get_json(silent=True) or {}
    intent_str = data.get("intent")
    records = data.get("records") or []

    if not intent_str or not records:
        return jsonify({"success": False, "error": "Campos 'intent' e 'records' são obrigatórios."}), 400

    try:
        intent = ImportIntent(intent_str)
    except ValueError:
        return jsonify({"success": False, "error": f"Intent inválido: {intent_str}"}), 400

    # Filtra apenas válidos (defesa em profundidade)
    valid_records = [r for r in records if r.get("valid")]
    invalid_records = [r for r in records if not r.get("valid")]
    if not valid_records:
        return jsonify({
            "success": False,
            "error": "Nenhum registro válido para aplicar.",
            "invalid_count": len(invalid_records),
        }), 400

    try:
        if intent == ImportIntent.PROFISSIONAIS_SAUDE:
            resultado = _apply_profissionais(assoc, valid_records)
        elif intent == ImportIntent.EQUIPE_ADMIN:
            resultado = _apply_equipe(assoc, valid_records)
        elif intent == ImportIntent.CONSULTORIOS:
            resultado = _apply_consultorios(assoc, valid_records)
        elif intent == ImportIntent.DISPONIBILIDADE:
            resultado = _apply_disponibilidade(assoc, valid_records)
        else:
            return jsonify({"success": False, "error": f"Intent não implementado: {intent_str}"}), 400

        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        logger.exception("IntegrityError no apply")
        return jsonify({"success": False, "error": f"Conflito de dados: {exc.orig}"}), 409
    except Exception as exc:
        db.session.rollback()
        logger.exception("Erro inesperado no apply")
        return jsonify({"success": False, "error": f"Erro ao aplicar: {exc}"}), 500

    # Auditoria
    try:
        create_audit_entry(
            tenant_id=assoc.id,
            user_id=_current_user_id(),
            action="intelligent_import.apply",
            resource_type="import",
            resource_id=intent_str,
            details={
                "intent": intent_str,
                "aplicados": resultado.get("criados", 0),
                "vinculados": resultado.get("vinculados", 0),
                "ignorados": resultado.get("ignorados", 0),
                "warnings": resultado.get("warnings", []),
                "invalid_skipped": len(invalid_records),
            },
            ip=request.remote_addr,
        )
    except Exception as exc:
        logger.warning("Falha ao registrar audit (apply): %s", exc)

    return jsonify({
        "success": True,
        "intent": intent_str,
        "aplicados": resultado.get("criados", 0),
        "vinculados": resultado.get("vinculados", 0),
        "ignorados": resultado.get("ignorados", 0),
        "warnings": resultado.get("warnings", []),
        "invalid_skipped": len(invalid_records),
    }), 200


# REDACTED
# Aplicadores por intent
# REDACTED
def _generate_temp_password() -> str:
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))


def _ensure_usuario_vinculo(profissional: Profissional, assoc, role: str) -> str:
    """Garante UsuarioAssociacao ativo entre profissional e assoc. Retorna status."""
    link = UsuarioAssociacao.query.filter_by(
        profissional_id=profissional.id, associacao_id=assoc.id
    ).first()
    if link is None:
        link = UsuarioAssociacao(
            profissional_id=profissional.id,
            associacao_id=assoc.id,
            role=role,
            status="active",
        )
        db.session.add(link)
        return "criado"
    if link.status != "active":
        link.status = "active"
        return "reativado"
    return "ja_vinculado"


def _apply_profissionais(assoc, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    criados = 0
    vinculados = 0
    ignorados = 0
    warnings: List[str] = []

    for rec in records:
        norm = rec.get("normalized") or {}
        email = (norm.get("email") or "").lower().strip()
        nome = (norm.get("nome") or "").strip()
        if not email or not nome:
            ignorados += 1
            continue

        conselho_tipo = normalizar_tipo_conselho(norm.get("conselho_tipo") or "CRM")
        role = norm.get("role") or inferir_tipo_pela_role("profissional")

        # 1) Garante Profissional
        prof = Profissional.query.filter_by(email=email).first()
        if prof is None:
            usuario_base = email.split("@")[0]
            usuario = usuario_base
            contador = 1
            while Profissional.query.filter_by(usuario=usuario).first():
                usuario = f"{usuario_base}{contador}"
                contador += 1
            prof = Profissional(
                nome=nome,
                email=email,
                usuario=usuario,
                crm=norm.get("conselho_numero") if conselho_tipo != CONSELHO_NONE else None,
                uf_crm=norm.get("uf") or None,
                conselho_tipo=conselho_tipo,
                telefone=norm.get("telefone"),
                especialidade=norm.get("especialidade"),
                role=role,
                senha=generate_password_hash(_generate_temp_password()),
                status_cadastro="aprovado",
                data_aprovacao=datetime.utcnow(),
                aprovado_por="intelligent_import",
                onboarding_completed=False,  # precisa aceitar convite na clínica
            )
            db.session.add(prof)
            db.session.flush()
            criados += 1
        else:
            # Atualiza conselho_tipo se vazio/errado
            if not prof.conselho_tipo:
                prof.conselho_tipo = conselho_tipo
            if conselho_tipo != CONSELHO_NONE and not prof.crm and norm.get("conselho_numero"):
                prof.crm = norm["conselho_numero"]
                prof.uf_crm = norm.get("uf") or prof.uf_crm

        # 2) Garante vínculo com a clínica
        status_vinculo = _ensure_usuario_vinculo(prof, assoc, "member")
        if status_vinculo in ("criado", "reativado"):
            vinculados += 1
        elif status_vinculo == "ja_vinculado":
            warnings.append(f"{email}: já estava vinculado a esta clínica")

    return {
        "criados": criados,
        "vinculados": vinculados,
        "ignorados": ignorados,
        "warnings": warnings,
    }


def _apply_equipe(assoc, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    criados = 0
    vinculados = 0
    ignorados = 0
    warnings: List[str] = []

    for rec in records:
        norm = rec.get("normalized") or {}
        email = (norm.get("email") or "").lower().strip()
        nome = (norm.get("nome") or "").strip()
        funcao = norm.get("funcao") or "secretary"
        if not email or not nome:
            ignorados += 1
            continue

        # Para staff, role no Profissional é 'secretary' ou 'manager'
        role = funcao if funcao in ("secretary", "manager", "auxiliar") else "secretary"

        prof = Profissional.query.filter_by(email=email).first()
        if prof is None:
            usuario_base = email.split("@")[0]
            usuario = usuario_base
            contador = 1
            while Profissional.query.filter_by(usuario=usuario).first():
                usuario = f"{usuario_base}{contador}"
                contador += 1
            prof = Profissional(
                nome=nome,
                email=email,
                usuario=usuario,
                telefone=norm.get("telefone"),
                conselho_tipo=CONSELHO_NONE,
                role=role,
                senha=generate_password_hash(_generate_temp_password()),
                status_cadastro="aprovado",
                data_aprovacao=datetime.utcnow(),
                aprovado_por="intelligent_import",
                onboarding_completed=False,
            )
            db.session.add(prof)
            db.session.flush()
            criados += 1
        elif prof.role not in ("secretary", "manager", "auxiliar"):
            warnings.append(f"{email}: já é {prof.role}, não alterado para {role}")

        status_vinculo = _ensure_usuario_vinculo(prof, assoc, "member")
        if status_vinculo in ("criado", "reativado"):
            vinculados += 1

    return {
        "criados": criados,
        "vinculados": vinculados,
        "ignorados": ignorados,
        "warnings": warnings,
    }


def _apply_consultorios(assoc, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    criados = 0
    vinculados = 0
    ignorados = 0
    warnings: List[str] = []

    for rec in records:
        norm = rec.get("normalized") or {}
        nome = (norm.get("nome") or "").strip()
        if not nome:
            ignorados += 1
            continue

        existing = Consultorio.query.filter_by(
            associacao_id=assoc.id, nome=nome
        ).first()
        if existing is not None:
            warnings.append(f"Sala '{nome}' já existe nesta clínica")
            continue

        cons = Consultorio(
            associacao_id=assoc.id,
            nome=nome,
            andar=norm.get("andar") or None,
            ala=norm.get("ala") or None,
            capacidade=int(norm.get("capacidade") or 1),
            recursos=norm.get("recursos") or None,
        )
        db.session.add(cons)
        criados += 1

    return {
        "criados": criados,
        "vinculados": 0,
        "ignorados": ignorados,
        "warnings": warnings,
    }


_DIA_SEMANA_MAP = {
    "domingo": 0, "dom": 0,
    "segunda": 1, "seg": 1,
    "terca": 2, "terça": 2, "ter": 2,
    "quarta": 3, "qua": 3,
    "quinta": 4, "qui": 4,
    "sexta": 5, "sex": 5,
    "sabado": 6, "sábado": 6, "sab": 6,
}


def _apply_disponibilidade(assoc, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    criados = 0
    vinculados = 0
    ignorados = 0
    warnings: List[str] = []

    # Profissionais vinculados a esta clínica
    membros_ids = [ua.profissional_id for ua in UsuarioAssociacao.query.filter_by(
        associacao_id=assoc.id, status="active"
    ).all()]
    membros_map = {p.nome.lower().strip(): p for p in Profissional.query.filter(
        Profissional.id.in_(membros_ids)
    ).all()} if membros_ids else {}

    for rec in records:
        norm = rec.get("normalized") or {}
        prof_nome = (norm.get("profissional") or "").lower().strip()
        dia_str = (norm.get("dia_semana") or "").lower().strip()
        dia_int = _DIA_SEMANA_MAP.get(dia_str)
        hi_str = norm.get("hora_inicio")
        hf_str = norm.get("hora_fim")
        if not prof_nome or dia_int is None or not hi_str or not hf_str:
            ignorados += 1
            continue

        prof = membros_map.get(prof_nome)
        if prof is None:
            warnings.append(f"Profissional '{prof_nome}' não vinculado a esta clínica — ignorado")
            ignorados += 1
            continue

        try:
            hi_h, hi_m = hi_str.split(":")
            hf_h, hf_m = hf_str.split(":")
            hora_inicio = time(int(hi_h), int(hi_m))
            hora_fim = time(int(hf_h), int(hf_m))
        except (ValueError, AttributeError):
            ignorados += 1
            warnings.append(f"Horário inválido para {prof_nome}: {hi_str}-{hf_str}")
            continue

        disp = Disponibilidade(
            profissional_id=prof.id,
            dia_semana=dia_int,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            duracao_consulta_minutos=int(norm.get("intervalo_min") or 30),
        )
        db.session.add(disp)
        criados += 1

    return {
        "criados": criados,
        "vinculados": 0,
        "ignorados": ignorados,
        "warnings": warnings,
    }


__all__ = ["intelligent_import_bp"]
