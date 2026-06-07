# HARDENING-6 — Auth Decorator Standardization

**Date:** 2026-06-02  
**Status:** COMPLETE  
**Risk Before:** MEDIUM (3 duplicate implementations, inconsistent behavior)  
**Risk After:** LOW

---

## Problem

Three different `admin_required` implementations existed:

| File | Implementation | Issues |
|------|---------------|--------|
| `routes/admin.py` | Decorator factory, checks `g.user_role` | Duplicated |
| `routes/planos.py` | Decorator, checks `g.current_user.role` | Different attribute name, inconsistent |
| `routes/billing.py` | Inline function `admin_required()` | Not a decorator, different signature |

## Impact

- **Inconsistent behavior:** Some routes allowed `superadmin`, others only `admin`
- **Maintenance burden:** Fix in one place not reflected in others
- **Security risk:** Inconsistent role checks could create gaps

## Changes Made

### New File: `routes/auth_decorators.py`

```python
from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import Profissional

def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        effective_role = getattr(g, 'user_role', None)
        if not effective_role:
            try:
                claims = get_jwt()
                effective_role = claims.get('role')
            except Exception:
                pass
        if not effective_role:
            current_user_id = get_jwt_identity()
            try:
                if current_user_id is not None:
                    profissional = Profissional.query.get(int(current_user_id))
                    if profissional:
                        effective_role = profissional.role
            except Exception:
                pass
        if effective_role not in ['admin', 'superadmin']:
            return jsonify({'error': 'Acesso negado. Permissão de administrador ou superadministrador necessária.'}), 403
        return f(*args, **kwargs)
    return decorated_function
```

### Updated: `routes/admin.py`

- Removed local `admin_required` definition
- Added `from routes.auth_decorators import admin_required`

### Updated: `routes/planos.py`

- Removed local `admin_required` definition
- Added `from routes.auth_decorators import admin_required`

### Updated: `routes/billing.py`

- Removed inline `def admin_required():`
- Added `from routes.auth_decorators import admin_required`
- Converted function calls to `@admin_required` decorator

## Tenant Awareness

The canonical decorator checks `effective_role` from three sources (in order):
1. `g.user_role` (set by app-level before_request)
2. JWT claims (`get_jwt()`)
3. Database fallback (`Profissional.query.get()`)

This ensures it works regardless of how authentication context is established.

## Test Coverage

| Test | Status |
|------|--------|
| `REDACTED` | ✅ PASS |
| `test_decorator_nao_admin_negado` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |

**Test Execution:** `25 passed, 370 warnings in 13.84s`

## Success Criteria

- [x] Single canonical `admin_required` implementation
- [x] All three modules import from `auth_decorators.py`
- [x] Consistent behavior: accepts `admin` and `superadmin`
- [x] Tenant-aware (checks g, JWT, DB in order)
- [x] No code duplication
- [x] Tests pass
