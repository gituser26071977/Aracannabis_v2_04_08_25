"""
Testes de regressão das extensões de plataforma:

    - AuditFieldsMixin
    - Permissões neuro.* em Permission
    - 3 roles novas (ROLE_NEURODEVELOPMENTAL_PHYSICIAN, etc.)
    - Entradas de catálogo domain=neurodevelopmental
"""

from __future__ import annotations

import pytest


# ─── AuditFieldsMixin ──────────────────────────────────────────────


def REDACTED():
    """AuditFieldsMixin deve declarar created_by/updated_by/deleted_by."""
    from araos.platform.tenant.models import AuditFieldsMixin

    assert hasattr(AuditFieldsMixin, "created_by")
    assert hasattr(AuditFieldsMixin, "updated_by")
    assert hasattr(AuditFieldsMixin, "deleted_by")


def REDACTED():
    """AuditFieldsMixin pode ser combinado com Base declarativa.

    Verificamos via mecanismo alternativo: a tabela real `NeuroScaleResponseModel`
    herda de ambos e deve ter todas as colunas audit + tenant_id.
    """
    from araos.specialties.neurodevelopmental.db_models import (
        NeuroScaleResponseModel,
    )

    cols = {c.name for c in NeuroScaleResponseModel.__table__.columns}
    assert "created_by" in cols
    assert "updated_by" in cols
    assert "deleted_by" in cols
    # Também garante que a coluna tenant_id está presente (multi-tenant LGPD)
    assert "tenant_id" in cols
    assert "deleted_at" in cols  # soft delete (já existente em Base)


# ─── Permissions neuro.* ──────────────────────────────────────────


NEURO_PERMISSIONS = [
    "neurodevelopmental.profile.read",
    "neurodevelopmental.profile.write",
    "neurodevelopmental.scale.apply",
    "neurodevelopmental.scale.interpret",
    "neurodevelopmental.medication.prescribe",
    "neurodevelopmental.cannabis.prescribe",
    "neurodevelopmental.graph.view",
    "neurodevelopmental.graph.create",
    "neurodevelopmental.report.generate",
    "neurodevelopmental.report.export",
    "neurodevelopmental.ai.use",
    "neurodevelopmental.research.export",
    "neurodevelopmental.observatory.view",
    "neurodevelopmental.dashboard.medical",
    "neurodevelopmental.dashboard.coordinator",
    "neurodevelopmental.dashboard.researcher",
    "neurodevelopmental.dashboard.manager",
    "neurodevelopmental.dashboard.health_secretary",
    "neurodevelopmental.dashboard.financial",
    "neurodevelopmental.dashboard.scientific",
]


@pytest.mark.parametrize("perm", NEURO_PERMISSIONS)
def test_neuro_permission_registered(perm):
    from araos.platform.identity.permissions import Permission, PermissionRegistry

    # Verifica via PermissionRegistry (fonte canônica)
    assert PermissionRegistry.is_valid(perm), (
        f"Permissão {perm!r} deve estar registrada em PermissionRegistry"
    )
    # E está listada em Permission.all()
    assert perm in Permission.all()


def REDACTED():
    from araos.platform.identity.permissions import Permission

    all_perms = Permission.all()
    for perm in NEURO_PERMISSIONS:
        assert perm in all_perms, f"Permissão {perm!r} ausente em Permission.all()"


# ─── Roles novas ──────────────────────────────────────────────────


def REDACTED():
    from araos.platform.identity.permissions import RoleRegistry

    role = RoleRegistry.get("neuro_physician")
    assert role is not None
    assert "neuro_physician" in role.description.lower() or "neurodesenvolvimento" in role.description.lower()


def REDACTED():
    from araos.platform.identity.permissions import RoleRegistry

    role = RoleRegistry.get("neuro_physician")
    assert role.has_permission("patient.read")
    assert role.has_permission("neurodevelopmental.scale.apply")
    assert role.has_permission("neurodevelopmental.cannabis.prescribe")
    assert role.has_permission("neurodevelopmental.ai.use")


def REDACTED():
    from araos.platform.identity.permissions import RoleRegistry

    role = RoleRegistry.get("health_secretary")
    assert role.has_permission("neurodevelopmental.observatory.view")
    # NÃO deve ter permissão de escrita clínica
    assert not role.has_permission("patient.write")
    assert not role.has_permission("neurodevelopmental.scale.apply")


def REDACTED():
    from araos.platform.identity.permissions import RoleRegistry

    role = RoleRegistry.get("scientific_producer")
    assert role.has_permission("neurodevelopmental.research.export")
    assert role.has_permission("neurodevelopmental.dashboard.researcher")
    # Não prescreve medicação
    assert not role.has_permission("neurodevelopmental.medication.prescribe")


def REDACTED():
    from araos.platform.identity.permissions import RoleRegistry

    perms = RoleRegistry.resolve_permissions(["neuro_physician"])
    assert "neurodevelopmental.scale.apply" in perms
    assert "neurodevelopmental.ai.use" in perms


def REDACTED():
    from araos.platform.identity.permissions import RoleRegistry

    assert RoleRegistry.check_permission(
        ["neuro_physician"], "neurodevelopmental.scale.apply"
    )
    assert not RoleRegistry.check_permission(
        ["health_secretary"], "neurodevelopmental.scale.apply"
    )


# ─── Catálogo de eventos ──────────────────────────────────────────


NEURO_EVENT_TYPES = [
    "NEURODEVELOPMENTAL_PROFILE_CREATED",
    "NEURODEVELOPMENTAL_PROFILE_UPDATED",
    "NEURODEVELOPMENTAL_CONDITION_ADDED",
    "REDACTED",
    "NEURODEVELOPMENTAL_SCALE_APPLIED",
    "NEURODEVELOPMENTAL_SCORE_COMPUTED",
    "REDACTED",
    "REDACTED",
    "REDACTED",
    "REDACTED",
    "REDACTED",
    "NEURODEVELOPMENTAL_EVENT_RECORDED",
    "REDACTED",
    "REDACTED",
    "REDACTED",
]


@pytest.mark.parametrize("event_type", NEURO_EVENT_TYPES)
def test_neuro_event_in_catalog(event_type):
    from araos.platform.events.catalog import (
        get_event_definition,
        is_valid_event_type,
    )

    assert is_valid_event_type(event_type)
    defn = get_event_definition(event_type)
    assert defn is not None
    assert defn.domain == "neurodevelopmental"
    assert defn.sensitive is True  # LGPD


def test_neuro_events_listed_in_domain():
    from araos.platform.events.catalog import get_event_definition

    # Pelo menos 15 eventos neurodev registrados
    neuro_events = [
        et
        for et in [
            "NEURODEVELOPMENTAL_PROFILE_CREATED",
            "NEURODEVELOPMENTAL_PROFILE_UPDATED",
            "NEURODEVELOPMENTAL_CONDITION_ADDED",
            "REDACTED",
            "NEURODEVELOPMENTAL_SCALE_APPLIED",
            "NEURODEVELOPMENTAL_SCORE_COMPUTED",
            "REDACTED",
            "REDACTED",
            "REDACTED",
            "REDACTED",
            "REDACTED",
            "NEURODEVELOPMENTAL_EVENT_RECORDED",
            "REDACTED",
            "REDACTED",
            "REDACTED",
        ]
        if get_event_definition(et) is not None
    ]
    assert len(neuro_events) >= 15


def REDACTED():
    from araos.platform.events.catalog import get_event_definition

    defn = get_event_definition("NEURODEVELOPMENTAL_SCALE_APPLIED")
    assert "audit" in defn.consumers
    assert "timeline" in defn.consumers
    assert "observatory_etl" in defn.consumers


# ─── Cross-cutting: nenhuma regressão ────────────────────────────


def REDACTED():
    from araos.platform.events.catalog import get_event_definition

    defn = get_event_definition("CANNABIS_STARTED")
    assert defn is not None
    assert defn.domain == "cannabis"


def REDACTED():
    from araos.platform.identity.permissions import RoleRegistry

    role = RoleRegistry.get("physician")
    assert role.has_permission("patient.read")
    assert role.has_permission("neurodevelopmental.scale.apply") is False  # não-tem