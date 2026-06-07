# HARDENING-1 — Secure Exams API

**Date:** 2026-06-02  
**Status:** COMPLETE  
**Risk Before:** HIGH  
**Risk After:** LOW

---

## Problem

All exam endpoints (`/api/exames/*`, `/api/pacientes/*/exames`, `/api/imagens/*`, `/api/resultados/*`) were publicly accessible without authentication.

## Changes Made

### File: `routes/exames.py`

1. **Added imports:** `jwt_required`, `get_jwt_identity`, `Profissional`, `CompartilhamentoPaciente`
2. **Added helper:** `verificar_acesso_exame(profissional_id, paciente_id)`
   - Checks admin/superadmin role
   - Checks if professional is the responsible
   - Checks active sharing (`CompartilhamentoPaciente`)
3. **Added `@jwt_required()` to all 16 endpoints:**
   - `POST /api/exames`
   - `GET /api/pacientes/<id>/exames`
   - `GET /api/exames/<id>`
   - `GET /api/exames/<id>/imagens`
   - `GET /api/exames/<id>/resultados`
   - `PUT /api/exames/<id>`
   - `DELETE /api/exames/<id>`
   - `GET /api/imagens/<id>`
   - `DELETE /api/imagens/<id>`
   - `PUT /api/resultados/<id>`
   - `DELETE /api/resultados/<id>`
   - `GET /api/exames/arquivos/<filename>`
   - `GET /api/pacientes/<id>/exames/chart/<titulo>`
   - `GET /api/pacientes/<id>/exames/chartable`
   - `POST /api/exames/<id>/ocr`
   - `GET /api/exames/nomes-unicos`
4. **Added access control checks** on all endpoints that operate on patient-specific data

## Test Coverage

| Test | Status |
|------|--------|
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |
| `REDACTED` | ✅ PASS |

**Test Execution:** `25 passed, 370 warnings in 13.84s`

## Verification

```bash
# Anonymous access denied
curl -s -o /dev/null -w "%{http_code}" http://localhost:5002/api/pacientes/1/exames
# Expected: 401

# Authenticated access allowed
curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer <token>" http://localhost:5002/api/pacientes/1/exames
# Expected: 200
```

## Success Criteria

- [x] All exam endpoints require authentication
- [x] Zero unauthenticated data exposure
- [x] Access control enforced (professional must have patient access)
- [x] Admin/superadmin bypass works
- [x] Regression tests pass
