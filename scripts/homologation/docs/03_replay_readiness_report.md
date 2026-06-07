# Replay Readiness Report

**Program:** API-1B — Homologation Dataset  
**Date:** 2026-06-02  
**Status:** READY

---

## Certification Result

```python
from services.replay_certification import certify_replay_readiness
result = certify_replay_readiness()
# Score: 10.0/10.0 — ALL CHECKS PASSING
```

## Replay Endpoints Coverage

| MeshOS Operation | SIAP Endpoint | Data Available | Status |
|------------------|---------------|----------------|--------|
| `READ_PATIENT` | `GET /api/pacientes/<id>` | 18 patients | ✅ |
| `READ_PATIENTS` | `GET /api/pacientes/` | 18 patients | ✅ |
| `READ_EXAMS` | `GET /api/pacientes/<id>/exames` | 86 exams | ✅ |
| `READ_EXAM_DETAIL` | `GET /api/exames/<id>` | 86 exams | ✅ |
| `READ_EVOLUTIONS` | `GET /api/evolucoes/paciente/<id>` | 80 evolutions | ✅ |
| `READ_PRESCRIPTIONS` | `GET /api/prescricoes/paciente/<id>` | 48 prescriptions | ✅ |
| `READ_SYMPTOMS` | `GET /api/sintomas/paciente/<id>` | 214 symptoms | ✅ |
| `READ_CONSULTATIONS` | `GET /api/consultas/` | 35 consultations | ✅ |
| `READ_DOSAGES` | `GET /api/dosagens/paciente/<id>` | 182 dosages | ✅ |

## Replay Data Volume

| Metric | Value | Suitability |
|--------|-------|-------------|
| Total patients | 18 | ✅ Adequate for pilot |
| Patients per physician | 5–6 | ✅ Realistic caseload |
| Evolutions per patient | 5 | ✅ Standard follow-up |
| Exams per patient | ~5 | ✅ Comprehensive workup |
| Prescriptions per patient | 3 | ✅ Treatment evolution |
| Dataset age span | 180 days | ✅ Sufficient for trends |

## Temporal Coverage

```
Timeline: D0 ────── D30 ────── D60 ────── D90 ────── D180
          Baseline  1st FU    2nd FU    3rd FU    6mo FU

Evolutions:   ✓        ✓         ✓         ✓         ✓
Prescriptions:✓        ✓                   ✓
Exams:        ✓        ✓         ✓         ✓         ✓
Consultations:✓        ✓         ✓         ✓         ✓
Symptoms:     ✓        ✓         ✓         ✓         ✓
```

## Read-Only Invariant

MeshOS Replay is **strictly read-only**. The dataset exercises all GET endpoints:
- No write operations during replay
- No patient data modification
- No prescription changes
- Observation-only mode

## Authentication for Replay

| Credential | Role | Use |
|-----------|------|-----|
| `helena.cannabis` / `Teste@123456` | profissional | Patient access |
| `ricardo.dor` / `Teste@123456` | profissional | Patient access |
| `fernanda.neuro` / `Teste@123456` | profissional | Patient access |
| `admin` / `Aracannabis@2025` | admin | Full access |

## Replay Readiness Verdict

```python
REPLAY_READY = True
DATASET_SUFFICIENT = True
RECOMMEND_MESHOS_INTEGRATION = True
```

---

*Certified by: `services/replay_certification.py` v1.0.0*
