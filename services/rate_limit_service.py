"""
Rate Limit Service por Tenant/Plano (Squad B — Segurança & Acesso)

Implementa rate limiting por profissional_id baseado no plano,
usando Redis quando disponível (persiste entre restarts) ou memória.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from services.feature_flag_service import FeatureFlagService

logger = logging.getLogger(__name__)

# Fallback em memória (apenas para dev/teste sem Redis)
_IN_MEMORY_COUNTERS: Dict[str, list] = {}


def _get_redis_client():
    """Tenta obter cliente Redis a partir do REDIS_URL."""
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url or not redis_url.startswith("redis://"):
        return None
    try:
        import redis as redis_lib

        client = redis_lib.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"Redis não disponível para rate limit: {e}")
        return None


def _make_key(profissional_id: int, window_start: int) -> str:
    return f"siap:ratelimit:ia:{profissional_id}:{window_start}"


def check_ia_rate_limit(profissional_id: int, limit_per_minute: int) -> tuple[bool, int, int]:
    """
    Verifica se o profissional pode fazer mais uma requisição IA neste minuto.

    Returns:
        (allowed: bool, current: int, limit: int)
    """
    if limit_per_minute <= 0:
        return False, 0, 0

    now = int(time.time())
    window_start = now // 60  # janela de 1 minuto
    key = _make_key(profissional_id, window_start)

    redis_client = _get_redis_client()

    if redis_client:
        pipe = redis_client.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        results = pipe.execute()
        current = results[0]
        allowed = current <= limit_per_minute
        return allowed, current, limit_per_minute
    else:
        # Fallback memória
        global _IN_MEMORY_COUNTERS
        cutoff = now - 60
        # Limpa janelas antigas
        for k in list(_IN_MEMORY_COUNTERS.keys()):
            parts = k.split(":")
            if len(parts) >= 2:
                try:
                    k_window = int(parts[-1])
                    if k_window < window_start - 1:
                        del _IN_MEMORY_COUNTERS[k]
                except ValueError:
                    pass
        # Incrementa contador atual
        _IN_MEMORY_COUNTERS[key] = _IN_MEMORY_COUNTERS.get(key, 0) + 1
        current = _IN_MEMORY_COUNTERS[key]
        allowed = current <= limit_per_minute
        return allowed, current, limit_per_minute


def get_ia_rate_limit_for_profissional(profissional_id: int) -> int:
    """
    Retorna o limite de requisições IA por minuto para o profissional.
    - Sem plano ou plano Sem IA: 0
    - Plano Com IA: limite_agentes_ia (ou maior se definido)
    """
    from models import Profissional, Assinatura

    profissional = Profissional.query.get(profissional_id)
    if not profissional:
        return 0

    if profissional.role in ("admin", "superadmin"):
        return 999999  # ilimitado para admin

    assinatura = Assinatura.query.filter_by(profissional_id=profissional_id).first()
    if not assinatura or not assinatura.plano:
        return 0

    plano = assinatura.plano
    if not plano.limite_agentes_ia or plano.limite_agentes_ia <= 0:
        return 0

    return plano.limite_agentes_ia
