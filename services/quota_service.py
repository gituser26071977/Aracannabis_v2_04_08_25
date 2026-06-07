"""
Quota Service (Squad B — Segurança & Acesso)

Contador de pacientes, requisições IA e uso de armazenamento por tenant/profissional.
Tudo atrás da feature flag 'plan_enforcement'.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from models import db, Profissional, Assinatura, Paciente, Plano
from services.feature_flag_service import FeatureFlagService

logger = logging.getLogger(__name__)


class QuotaService:
    """Serviço centralizado de quotas e limites do plano."""

    @staticmethod
    def get_profissional_subscription(profissional_id: int):
        """Retorna profissional, assinatura e plano."""
        profissional = Profissional.query.get(profissional_id)
        if not profissional:
            return None, None, None
        assinatura = Assinatura.query.filter_by(profissional_id=profissional_id).first()
        plano = assinatura.plano if assinatura else None
        return profissional, assinatura, plano

    @classmethod
    def get_patient_quota(cls, profissional_id: int) -> Dict:
        """Retorna quota de pacientes (usado/total)."""
        profissional, assinatura, plano = cls.get_profissional_subscription(profissional_id)

        if not profissional:
            return {"used": 0, "limit": 0, "available": 0, "percentage": 0}

        if profissional.role in ("admin", "superadmin"):
            return {"used": 0, "limit": -1, "available": -1, "percentage": 0, "unlimited": True}

        used = Paciente.query.filter_by(profissional_responsavel_id=profissional_id).count()
        limit = plano.limite_pacientes if plano else 50
        if limit is None or limit < 0:
            limit = 999999

        available = max(0, limit - used)
        percentage = round((used / limit) * 100, 2) if limit > 0 else 0

        return {
            "used": used,
            "limit": limit,
            "available": available,
            "percentage": percentage,
            "unlimited": limit >= 999999,
        }

    @classmethod
    def get_ia_quota(cls, profissional_id: int) -> Dict:
        """Retorna quota de requisições IA (usado/total)."""
        profissional, assinatura, plano = cls.get_profissional_subscription(profissional_id)

        if not profissional:
            return {"used": 0, "limit": 0, "available": 0, "percentage": 0, "enabled": False}

        if profissional.role in ("admin", "superadmin"):
            return {
                "used": 0,
                "limit": -1,
                "available": -1,
                "percentage": 0,
                "enabled": True,
                "unlimited": True,
            }

        limit = plano.limite_agentes_ia if plano else 0
        if limit is None or limit < 0:
            limit = 0

        # Contagem de requisições IA nas últimas 24h (aproximada via LogAtividade)
        from models import LogAtividade

        since = datetime.utcnow() - timedelta(hours=24)
        used = (
            LogAtividade.query.filter(
                LogAtividade.profissional_id == profissional_id,
                LogAtividade.acao.in_(["IA", "AI", "Consulta IA", "Chat IA"]),
                LogAtividade.created_at >= since,
            ).count()
        )

        available = max(0, limit - used)
        percentage = round((used / limit) * 100, 2) if limit > 0 else 0

        return {
            "used": used,
            "limit": limit,
            "available": available,
            "percentage": percentage,
            "enabled": limit > 0,
            "unlimited": False,
        }

    @classmethod
    def get_storage_quota(cls, profissional_id: int) -> Dict:
        """Retorna quota de armazenamento em MB (usado/total)."""
        profissional, assinatura, plano = cls.get_profissional_subscription(profissional_id)

        if not profissional:
            return {"used_mb": 0, "limit_mb": 0, "available_mb": 0, "percentage": 0}

        if profissional.role in ("admin", "superadmin"):
            return {
                "used_mb": 0,
                "limit_mb": -1,
                "available_mb": -1,
                "percentage": 0,
                "unlimited": True,
            }

        limit_mb = plano.limite_armazenamento_mb if plano else 1024
        if limit_mb is None or limit_mb < 0:
            limit_mb = 1024

        # Soma tamanho de fotos de pacientes do profissional
        total_bytes = (
            db.session.query(db.func.coalesce(db.func.sum(Paciente.foto_tamanho), 0))
            .filter(Paciente.profissional_responsavel_id == profissional_id)
            .scalar()
        )
        used_mb = round(total_bytes / (1024 * 1024), 2)
        available_mb = round(max(0, limit_mb - used_mb), 2)
        percentage = round((used_mb / limit_mb) * 100, 2) if limit_mb > 0 else 0

        return {
            "used_mb": used_mb,
            "limit_mb": limit_mb,
            "available_mb": available_mb,
            "percentage": percentage,
            "unlimited": limit_mb >= 999999,
        }

    @classmethod
    def get_full_usage(cls, profissional_id: int) -> Dict:
        """Retorna todas as quotas consolidadas."""
        if not FeatureFlagService.is_enabled("plan_enforcement"):
            return {
                "feature_flag_enabled": False,
                "message": "Plan enforcement está desativado.",
                "quotas": {},
            }

        profissional, assinatura, plano = cls.get_profissional_subscription(profissional_id)

        if not profissional:
            return {"error": "Profissional não encontrado"}, 404

        return {
            "feature_flag_enabled": True,
            "profissional_id": profissional_id,
            "plano": plano.to_dict() if plano else None,
            "assinatura": assinatura.to_dict() if assinatura else None,
            "quotas": {
                "pacientes": cls.get_patient_quota(profissional_id),
                "ia_requisicoes_24h": cls.get_ia_quota(profissional_id),
                "armazenamento_mb": cls.get_storage_quota(profissional_id),
            },
        }
