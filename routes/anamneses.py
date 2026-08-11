"""
Rotas para Anamnese no AraOS
Permite CRUD de fichas de anamnese vinculadas ao paciente.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Anamnese, Paciente, Profissional
from sqlalchemy.exc import SQLAlchemyError
import os
import logging
from services.webhook_auth import validate_internal_key

logger = logging.getLogger(__name__)
anamneses_bp = Blueprint("anamneses", __name__)


@anamneses_bp.route("/api/anamneses/paciente/<int:paciente_id>", methods=["GET"])
@jwt_required()
def listar_anamneses_paciente(paciente_id):
    """Lista todas as anamneses de um paciente, mais recentes primeiro."""
    try:
        anamneses = (
            Anamnese.query.filter_by(paciente_id=paciente_id)
            .order_by(Anamnese.data_anamnese.desc())
            .all()
        )
        return jsonify({
            "success": True,
            "anamneses": [a.to_dict() for a in anamneses],
            "total": len(anamneses),
        }), 200
    except Exception as e:
        logger.error(f"Erro ao listar anamneses: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@anamneses_bp.route("/api/anamneses/<int:anamnese_id>", methods=["GET"])
@jwt_required()
def obter_anamnese(anamnese_id):
    """Obtém uma anamnese específica."""
    try:
        anamnese = Anamnese.query.get(anamnese_id)
        if not anamnese:
            return jsonify({"success": False, "error": "Anamnese não encontrada"}), 404
        return jsonify({"success": True, "anamnese": anamnese.to_dict()}), 200
    except Exception as e:
        logger.error(f"Erro ao obter anamnese: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@anamneses_bp.route("/api/anamneses", methods=["POST"])
def criar_anamnese():
    """Cria uma nova anamnese (manual, via LIA ou import).
    Autenticação: JWT (frontend) ou X-Internal-Key (serviços internos)."""
    internal_key = request.headers.get("X-Internal-Key", "")
    expected_internal_key = os.environ.get("INTERNAL_SERVICE_KEY", "")
    is_internal = validate_internal_key(internal_key, expected_internal_key) if expected_internal_key else False
    
    profissional_id = None
    if not is_internal:
        from flask_jwt_extended import verify_jwt_in_request
        try:
            verify_jwt_in_request()
            profissional_id = get_jwt_identity()
        except Exception:
            return jsonify({"success": False, "error": "Não autorizado"}), 401
    """Cria uma nova anamnese (manual ou via LIA)."""
    try:
        data = request.get_json() or {}
        paciente_id = data.get("paciente_id")
        if not paciente_id:
            return jsonify({"success": False, "error": "paciente_id é obrigatório"}), 400

        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({"success": False, "error": "Paciente não encontrado"}), 404

        # Usar profissional_id do JWT ou deixar None (será associado depois)
        if not profissional_id:
            profissional_id = data.get("profissional_id")

        anamnese = Anamnese(
            paciente_id=paciente_id,
            profissional_id=profissional_id,
            condicao_principal=data.get("condicao_principal"),
            sintomas_atuais=data.get("sintomas_atuais"),
            medicamentos_uso=data.get("medicamentos_uso"),
            historico_cannabis=data.get("historico_cannabis"),
            tratamentos_previos=data.get("tratamentos_previos"),
            exames_recentes=data.get("exames_recentes"),
            alergias=data.get("alergias"),
            peso=data.get("peso"),
            altura=data.get("altura"),
            fonte=data.get("fonte", "manual"),
            telefone_origem=data.get("telefone_origem"),
            conversa_id=data.get("conversa_id"),
        )

        db.session.add(anamnese)

        # Atualizar campos resumo no Paciente
        if data.get("condicao_principal"):
            paciente.condicao_medica = data["condicao_principal"]
        if data.get("condicao_principal"):
            paciente.diagnostico = data["condicao_principal"]

        db.session.commit()

        # F2 — wrap: emite Clinical Event canônico (nunca bloqueia o fluxo)
        try:
            from services.araos_event_emitter import default_emitter

            default_emitter().emit(
                event_type="ANAMNESIS_RECORDED",
                patient_id=paciente_id,
                tenant_id=current_app.config.get("DEFAULT_TENANT_SLUG", "default"),
                source_id=anamnese.id,
                payload={
                    "anamnesis_id": anamnese.id,
                    "paciente_id": paciente_id,
                    "condicao_principal": anamnese.condicao_principal,
                    "sintomas_atuais": anamnese.sintomas_atuais,
                    "medicamentos_uso": anamnese.medicamentos_uso,
                    "peso": anamnese.peso,
                    "altura": anamnese.altura,
                    "fonte": anamnese.fonte,
                },
                metadata={"professional_id": str(profissional_id) if profissional_id else None},
            )
        except Exception as exc:  # noqa: BLE001 — wrap nunca quebra o fluxo
            logger.warning("anamnese_event_emit_failed: %s", exc)

        return jsonify({
            "success": True,
            "anamnese": anamnese.to_dict(),
            "message": "Anamnese criada com sucesso",
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao criar anamnese: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Erro inesperado ao criar anamnese: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@anamneses_bp.route("/api/anamneses/<int:anamnese_id>", methods=["PUT"])
@jwt_required()
def atualizar_anamnese(anamnese_id):
    """Atualiza uma anamnese existente."""
    try:
        anamnese = Anamnese.query.get(anamnese_id)
        if not anamnese:
            return jsonify({"success": False, "error": "Anamnese não encontrada"}), 404

        data = request.get_json() or {}
        campos = [
            "condicao_principal", "sintomas_atuais", "medicamentos_uso",
            "historico_cannabis", "tratamentos_previos", "exames_recentes",
            "alergias", "peso", "altura", "fonte", "telefone_origem", "conversa_id",
        ]
        for campo in campos:
            if campo in data:
                setattr(anamnese, campo, data[campo])

        db.session.commit()
        return jsonify({
            "success": True,
            "anamnese": anamnese.to_dict(),
            "message": "Anamnese atualizada com sucesso",
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar anamnese: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@anamneses_bp.route("/api/anamneses/<int:anamnese_id>", methods=["DELETE"])
@jwt_required()
def deletar_anamnese(anamnese_id):
    """Remove uma anamnese."""
    try:
        anamnese = Anamnese.query.get(anamnese_id)
        if not anamnese:
            return jsonify({"success": False, "error": "Anamnese não encontrada"}), 404

        db.session.delete(anamnese)
        db.session.commit()
        return jsonify({"success": True, "message": "Anamnese removida com sucesso"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar anamnese: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
