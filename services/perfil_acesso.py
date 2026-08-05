"""Controle de acesso por perfil — Assistencial × Administrativo × Solo.

Perfis:
    - 'assistencial'   : prontuário clínico (médicos, psicólogos, fisioterapeutas...)
    - 'administrativo' : agenda, faturamento, convênios, cadastros (recepcionista, gestor, financeiro)
    - 'solo'           : acesso pleno (assinante autônomo ou admin)

Regra de resolução (perfil efetivo):
    1. Se `Profissional.perfil_acesso` estiver definido → usa.
    2. admin/superadmin → 'solo' (acesso pleno).
    3. role 'auxiliar' → 'administrativo'.
    4. Assinante de plano individual (sem gestão de clínica) → 'solo'.
    5. Caso contrário → 'assistencial'.

Áreas de rota: prefixos de /api/* classificados por esfera. Prefixos fora das
listas ficam abertos a qualquer perfil autenticado (não são clínicos nem
administrativos centrais).
"""

from __future__ import annotations

import logging
from typing import Optional

from models import Profissional

logger = logging.getLogger(__name__)

PERFIL_ASSISTENCIAL = "assistencial"
PERFIL_ADMINISTRATIVO = "administrativo"
PERFIL_SOLO = "solo"

PERFIS_VALIDOS = {PERFIL_ASSISTENCIAL, PERFIL_ADMINISTRATIVO, PERFIL_SOLO}

# Rotas de LEITURA financeira do próprio profissional (exceção p/ assistencial)
REDACTED = [
    "/api/faturamento/minha-situacao",
    "/api/faturamento/agente",
]

# Esfera ASSISTENCIAL — prontuário/atendimento clínico
AREA_ASSISTENCIAL = [
    "/api/pacientes",
    "/api/consultas",
    "/api/evolucoes",
    "/api/prescricoes",
    "/api/exames",
    "/api/anamneses",
    "/api/dosagens",
    "/api/sintomas",
    "/api/resultados",
    "/api/imagens",
    "/api/beck-depression",
    "/api/gad7",
    "/api/phq9",
    "/api/snap-iv",
    "/api/cannabis",
    "/api/neuro",
]

# Esfera ADMINISTRATIVA — agenda, financeiro, cadastros, configurações
AREA_ADMINISTRATIVA = [
    "/api/faturamento",
    "/api/convenios",
    "/api/billing",
    "/api/planos",
    "/api/mercadopago",
    "/api/modulos",
    "/api/meus-modulos",
    "/api/profissionais",
    "/api/admin",
    "/api/cadastro_profissionais",
    "/api/ai-config",
    "/api/prescricao-config",
    "/api/tenant-config",
    "/api/anuncios",
    "/api/import-export",
    "/api/usage",
    "/api/lgpd",
    "/api/onboarding",
]


def area_da_rota(path: str) -> Optional[str]:
    """Classifica o path em 'assistencial' | 'administrativo' | None."""
    # Exceção controlada: o assistencial pode LER a própria situação financeira
    # (endpoints read-only de faturamento do próprio profissional).
    for prefixo in REDACTED:
        if path == prefixo or path.startswith(prefixo + "/"):
            return PERFIL_ASSISTENCIAL
    for prefixo in AREA_ASSISTENCIAL:
        if path == prefixo or path.startswith(prefixo + "/"):
            return PERFIL_ASSISTENCIAL
    for prefixo in AREA_ADMINISTRATIVA:
        if path == prefixo or path.startswith(prefixo + "/"):
            return PERFIL_ADMINISTRATIVO
    return None


def _tem_plano_solo(profissional: Profissional) -> bool:
    """True se o usuário tem assinatura ativa de plano individual (sem gestão de clínica)."""
    from models import Assinatura

    assinatura = Assinatura.query.filter_by(
        profissional_id=profissional.id
    ).order_by(Assinatura.id.desc()).first()
    if not assinatura:
        return False
    if assinatura.status not in ("ativa", "trial", "pending"):
        return False
    if not assinatura.plano:
        return False
    return not bool(getattr(assinatura.plano, "permite_gestao_clinica", True))


def resolver_perfil(profissional: Profissional) -> str:
    """Resolve o perfil de acesso efetivo do usuário."""
    if profissional is None:
        return PERFIL_ASSISTENCIAL
    if profissional.perfil_acesso in PERFIS_VALIDOS:
        return profissional.perfil_acesso
    if profissional.role in ("admin", "superadmin"):
        return PERFIL_SOLO
    if profissional.role == "auxiliar":
        return PERFIL_ADMINISTRATIVO
    if _tem_plano_solo(profissional):
        return PERFIL_SOLO
    return PERFIL_ASSISTENCIAL


def tem_acesso(perfil: str, area: str) -> bool:
    """Verifica se o perfil tem acesso à área (solo = pleno)."""
    if perfil == PERFIL_SOLO:
        return True
    return perfil == area


def verificar_acesso(profissional: Profissional, path: str) -> bool:
    """True se o usuário pode acessar a rota. None (sem área) = liberado."""
    area = area_da_rota(path)
    if area is None:
        return True
    perfil = resolver_perfil(profissional)
    return tem_acesso(perfil, area)
