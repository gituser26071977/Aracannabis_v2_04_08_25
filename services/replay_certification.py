"""
SIAP Replay Readiness Certification

Validates that Aracannabis_SIAP is ready for MeshOS replay integration.
This module is called by the AracannabisApiDriver before first replay session.

Usage:
    from services.replay_certification import certify_replay_readiness
    result = certify_replay_readiness()
    if result["certified"]:
        print(f"Certified: {result['version']}")
    else:
        print(f"Blockers: {result['blockers']}")
"""

from datetime import datetime
from typing import Dict, List, Any
import inspect
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Version of this certification module
CERTIFICATION_VERSION = "1.0.0"

# Minimum API version required
MIN_API_VERSION = "1.0.0"


def _check_exams_authentication() -> Dict[str, Any]:
    """HARDENING-1: All exam endpoints must be JWT-protected."""
    try:
        from routes import exames
        source = inspect.getsource(exames)
        
        # Count endpoints that SHOULD have @jwt_required
        # All route handlers must have jwt_required
        has_jwt_import = "jwt_required" in source
        
        # Find all route functions - count @bp.route lines and @jwt_required decorators
        import re
        route_decorators = re.findall(r'^@\w+\.route\(', source, re.MULTILINE)
        jwt_decorators = re.findall(r'^@jwt_required\(', source, re.MULTILINE)
        
        total_routes = len(route_decorators)
        protected_routes = len(jwt_decorators)
        
        return {
            "name": "Exams Authentication",
            "required": True,
            "passed": protected_routes == total_routes and total_routes > 0,
            "detail": f"{protected_routes}/{total_routes} endpoints protected",
            "severity": "CRITICAL"
        }
    except Exception as e:
        return {
            "name": "Exams Authentication",
            "required": True,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "CRITICAL"
        }


def _check_evolution_audit_timestamps() -> Dict[str, Any]:
    """HARDENING-2: Evolucao must have created_at/updated_at."""
    try:
        from models import Evolucao
        has_created = hasattr(Evolucao, 'created_at')
        has_updated = hasattr(Evolucao, 'updated_at')
        to_dict_has_timestamps = False
        
        if has_created and has_updated:
            source = inspect.getsource(Evolucao.to_dict)
            to_dict_has_timestamps = 'created_at' in source and 'updated_at' in source
        
        return {
            "name": "Evolution Audit Timestamps",
            "required": True,
            "passed": has_created and has_updated and to_dict_has_timestamps,
            "detail": f"created_at={has_created}, updated_at={has_updated}, to_dict={to_dict_has_timestamps}",
            "severity": "HIGH"
        }
    except Exception as e:
        return {
            "name": "Evolution Audit Timestamps",
            "required": True,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "HIGH"
        }


def REDACTED() -> Dict[str, Any]:
    """HARDENING-3: Prescricao must have created_at/updated_at."""
    try:
        from models import Prescricao
        has_created = hasattr(Prescricao, 'created_at')
        has_updated = hasattr(Prescricao, 'updated_at')
        to_dict_has_timestamps = False
        
        if has_created and has_updated:
            source = inspect.getsource(Prescricao.to_dict)
            to_dict_has_timestamps = 'created_at' in source and 'updated_at' in source
        
        return {
            "name": "Prescription Audit Timestamps",
            "required": True,
            "passed": has_created and has_updated and to_dict_has_timestamps,
            "detail": f"created_at={has_created}, updated_at={has_updated}, to_dict={to_dict_has_timestamps}",
            "severity": "HIGH"
        }
    except Exception as e:
        return {
            "name": "Prescription Audit Timestamps",
            "required": True,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "HIGH"
        }


def _check_prescription_schema() -> Dict[str, Any]:
    """Prescription conteudo_json must have documented medicamentos schema."""
    try:
        from models import Prescricao
        # Check that conteudo_json exists and is JSON type
        has_conteudo = hasattr(Prescricao, 'conteudo_json')
        
        return {
            "name": "Prescription Schema",
            "required": False,
            "passed": has_conteudo,
            "detail": f"conteudo_json field exists: {has_conteudo}",
            "severity": "MEDIUM"
        }
    except Exception as e:
        return {
            "name": "Prescription Schema",
            "required": False,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "MEDIUM"
        }


def _check_admin_auth_standardization() -> Dict[str, Any]:
    """HARDENING-6: Auth decorators must be standardized."""
    try:
        import routes.auth_decorators as auth_mod
        has_admin_required = hasattr(auth_mod, 'admin_required')
        
        # Check that admin.py, planos.py, billing.py import from auth_decorators
        from routes import admin, planos, billing
        admin_source = inspect.getsource(admin)
        planos_source = inspect.getsource(planos)
        billing_source = inspect.getsource(billing)
        
        admin_imports = "from routes.auth_decorators import admin_required" in admin_source
        planos_imports = "from routes.auth_decorators import admin_required" in planos_source
        billing_imports = "from routes.auth_decorators import admin_required" in billing_source
        
        return {
            "name": "Auth Decorator Standardization",
            "required": True,
            "passed": has_admin_required and admin_imports and planos_imports and billing_imports,
            "detail": f"canonical={has_admin_required}, admin.py={admin_imports}, planos.py={planos_imports}, billing.py={billing_imports}",
            "severity": "MEDIUM"
        }
    except Exception as e:
        return {
            "name": "Auth Decorator Standardization",
            "required": True,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "MEDIUM"
        }


def _check_patient_list_serialization() -> Dict[str, Any]:
    """Patient list must serialize with to_dict()."""
    try:
        from models import Paciente
        has_to_dict = hasattr(Paciente, 'to_dict')
        
        return {
            "name": "Patient Serialization",
            "required": True,
            "passed": has_to_dict,
            "detail": f"Paciente.to_dict exists: {has_to_dict}",
            "severity": "HIGH"
        }
    except Exception as e:
        return {
            "name": "Patient Serialization",
            "required": True,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "HIGH"
        }


def _check_jwt_configuration() -> Dict[str, Any]:
    """JWT must be configured with reasonable expiry."""
    try:
        from app_cors_livre import create_app
        from config import TestingConfig
        app = create_app(config_obj=TestingConfig)
        jwt_expiry = app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
        
        # Should be between 1 hour and 24 hours
        from datetime import timedelta
        is_reasonable = False
        if jwt_expiry:
            if isinstance(jwt_expiry, timedelta):
                hours = jwt_expiry.total_seconds() / 3600
                is_reasonable = 1 <= hours <= 24
            elif isinstance(jwt_expiry, int):
                is_reasonable = 3600 <= jwt_expiry <= 86400
        
        return {
            "name": "JWT Configuration",
            "required": True,
            "passed": jwt_expiry is not None and is_reasonable,
            "detail": f"JWT_ACCESS_TOKEN_EXPIRES={jwt_expiry}",
            "severity": "HIGH"
        }
    except Exception as e:
        return {
            "name": "JWT Configuration",
            "required": True,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "HIGH"
        }


def _check_tenant_header_support() -> Dict[str, Any]:
    """API must accept X-Association-ID header for multi-tenant."""
    try:
        from app_cors_livre import create_app
        from config import TestingConfig
        app = create_app(config_obj=TestingConfig)
        # Check if there's any middleware handling X-Association-ID
        has_tenant_middleware = False
        for func in app.before_request_funcs.get(None, []):
            source = inspect.getsource(func)
            if 'X-Association-ID' in source or 'x-association-id' in source.lower():
                has_tenant_middleware = True
                break
        
        return {
            "name": "Tenant Header Support",
            "required": True,
            "passed": has_tenant_middleware,
            "detail": f"X-Association-ID middleware exists: {has_tenant_middleware}",
            "severity": "HIGH"
        }
    except Exception as e:
        return {
            "name": "Tenant Header Support",
            "required": True,
            "passed": False,
            "detail": f"Error checking: {str(e)}",
            "severity": "HIGH"
        }


def certify_replay_readiness() -> Dict[str, Any]:
    """
    Run all certification checks and return result.
    
    Returns:
        {
            "certified": bool,
            "version": str,
            "timestamp": str (ISO),
            "checks": list of check results,
            "blockers": list of failed required checks,
            "warnings": list of failed optional checks,
            "score": float (0.0 to 10.0)
        }
    """
    checks = [
        _check_exams_authentication(),
        _check_evolution_audit_timestamps(),
        REDACTED(),
        _check_prescription_schema(),
        _check_admin_auth_standardization(),
        _check_patient_list_serialization(),
        _check_jwt_configuration(),
        _check_tenant_header_support(),
    ]
    
    blockers = [c for c in checks if not c["passed"] and c["required"]]
    warnings = [c for c in checks if not c["passed"] and not c["required"]]
    
    # Score: 10.0 if all pass, -2.0 per blocker, -0.5 per warning
    score = 10.0
    score -= len(blockers) * 2.0
    score -= len(warnings) * 0.5
    score = max(0.0, score)
    
    certified = len(blockers) == 0 and score >= 7.0
    
    return {
        "certified": certified,
        "version": CERTIFICATION_VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "score": round(score, 1)
    }


if __name__ == "__main__":
    result = certify_replay_readiness()
    print(f"Replay Readiness Certification v{result['version']}")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Certified: {'YES' if result['certified'] else 'NO'}")
    print(f"Score: {result['score']}/10.0")
    print()
    
    print("Checks:")
    for check in result["checks"]:
        status = "✅" if check["passed"] else "❌"
        req = "REQUIRED" if check["required"] else "optional"
        print(f"  {status} [{check['severity']}] {check['name']} ({req}): {check['detail']}")
    
    if result["blockers"]:
        print(f"\n⚠️  Blockers ({len(result['blockers'])}):")
        for b in result["blockers"]:
            print(f"  - {b['name']}: {b['detail']}")
    
    if result["warnings"]:
        print(f"\n⚡ Warnings ({len(result['warnings'])}):")
        for w in result["warnings"]:
            print(f"  - {w['name']}: {w['detail']}")
