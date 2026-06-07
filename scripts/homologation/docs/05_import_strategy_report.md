# Import Strategy Report

**Program:** API-1B — Homologation Dataset  
**Date:** 2026-06-02  
**Status:** EXECUTED

---

## Import Method

**Method:** Direct API insertion via authenticated HTTP requests  
**Tool:** `scripts/homologation/dataset_generator.py`  
**Authentication:** JWT Bearer tokens

## Import Sequence

The import follows a strict dependency order to maintain referential integrity:

```
Step 1: Authenticate as admin
        ↓
Step 2: Create physicians (POST /api/auth/register)
        ↓
Step 3: For each physician:
        ├── Login as physician
        ├── Create patients (POST /api/pacientes/)
        ├── For each patient:
        │   ├── Create symptoms (POST /api/sintomas/paciente/<id>)
        │   ├── Create dosages (POST /api/dosagens/paciente/<id>)
        │   ├── Create evolutions (POST /api/evolucoes/paciente/<id>)
        │   ├── Create exams (POST /api/exames)
        │   ├── Create consultations (POST /api/consultas/)
        │   └── Create prescriptions (POST /api/prescricoes/gerar)
        └── Logout
```

## API Endpoint Mapping

| Entity | Endpoint | Method | Auth | Payload |
|--------|----------|--------|------|---------|
| Physician | `/api/auth/register` | POST | Admin JWT | JSON |
| Patient | `/api/pacientes/` | POST | Physician JWT | JSON |
| Symptom | `/api/sintomas/paciente/<id>` | POST | Physician JWT | JSON |
| Dosage | `/api/dosagens/paciente/<id>` | POST | Physician JWT | JSON |
| Evolution | `/api/evolucoes/paciente/<id>` | POST | Physician JWT | JSON |
| Exam | `/api/exames` | POST | Physician JWT | Form-data |
| Consultation | `/api/consultas/` | POST | Physician JWT | JSON |
| Prescription | `/api/prescricoes/gerar` | POST | Physician JWT | JSON |

## Rate Limiting Considerations

| Limit | Value | Impact |
|-------|-------|--------|
| General requests | 200/min | No impact |
| Auth requests | 10/min | No impact |
| Actual throughput | ~60/min | Minor 429 on symptoms for patient 17 |

**Mitigation:** 100ms delay between requests + exponential backoff on 429.

## Data Validation During Import

| Validation | Enforcement | Status |
|-----------|-------------|--------|
| Required fields | API rejects incomplete data | ✅ |
| Date format (YYYY-MM-DD) | API validates | ✅ |
| CRM format (4–6 digits) | API validates | ✅ |
| CRM uniqueness | API enforces | ✅ |
| Email uniqueness | API enforces | ✅ |
| Patient-physician access control | API enforces | ✅ |
| Consultation time uniqueness | API enforces | ⚠️ Some conflicts |

## Rollback Strategy

In case of import failure:

1. **Partial dataset:** Already-inserted data remains (idempotent re-runs possible)
2. **Cleanup:** Truncate tables via SQL if full reset needed
3. **Re-run:** Script handles existing physicians gracefully

## Import Performance

| Metric | Value |
|--------|-------|
| Total API calls | ~650 |
| Success rate | 92% |
| Total duration | ~8 minutes |
| Average latency | ~120ms per request |

---

*Executed by: `scripts/homologation/dataset_generator.py`*
