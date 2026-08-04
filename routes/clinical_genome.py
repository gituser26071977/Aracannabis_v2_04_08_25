"""
Clinical Genome — API de leitura da projeção (Fase 0).

Expõe o estado do genome de um paciente (Expressões por Clinical Gene)
derivado dos eventos de pré-consulta do Ara Intake.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required

logger = logging.getLogger(__name__)

clinical_genome_bp = Blueprint(
    "clinical_genome",
    __name__,
    url_prefix="/api/v1/clinical",
)


def _session():
    """Retorna a session SQLAlchemy (db.session do Flask)."""
    from models import db

    return db.session


@clinical_genome_bp.route("/patients/<patient_id>/genome", methods=["GET"])
@jwt_required()
def get_patient_genome(patient_id: str):
    """Retorna a projeção do genome do paciente (Expressões por Gene)."""
    from services.clinical_genome_view import project_genome

    tenant_id = current_app.config.get("DEFAULT_TENANT_SLUG") or "vittalis"
    try:
        genome = project_genome(_session(), tenant_id=tenant_id, patient_id=patient_id)
    except Exception:  # noqa: BLE001
        logger.exception("genome_projection_failed")
        return jsonify({"error": "falha ao projetar genome"}), 500

    return jsonify(genome), 200
