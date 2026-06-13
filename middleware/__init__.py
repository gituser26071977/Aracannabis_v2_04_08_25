"""
Middleware Package

Este pacote contém middlewares de segurança e validação para o sistema.
"""
from middleware.patient_access_validator import (
    validate_patient_access,
    check_patient_access,
    require_patient_access,
    get_accessible_patients_query,
    get_profissional_logado,
    log_patient_access
)
from middleware.permission_middleware import (
    register_permission_middleware,
    resolve_effective_permissions,
)

__all__ = [
    'validate_patient_access',
    'check_patient_access',
    'require_patient_access',
    'get_accessible_patients_query',
    'get_profissional_logado',
    'log_patient_access',
    # Fase 1 — RBAC Secretária
    'register_permission_middleware',
    'resolve_effective_permissions',
]
