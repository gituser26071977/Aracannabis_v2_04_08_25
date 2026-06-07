# Clinical Consistency Report

**Program:** API-1B — Homologation Dataset  
**Date:** 2026-06-02  
**Status:** VALIDATED

---

## Validation Rules Applied

### 1. Physician-Patient Assignment Consistency

- Each of 3 physicians has exactly 5 assigned patients
- Patient `profissional_responsavel_id` matches physician ID
- No patient assigned to multiple physicians

### 2. Condition-Symptom Alignment

Every patient's symptoms derive from their assigned conditions:

| Patient | Conditions | Symptom Count | Aligned |
|---------|-----------|---------------|---------|
| Roberta Gomes Martins | TAG, Dor Neuropática | 12 | ✅ |
| Eduardo Costa Ferreira | Esclerose Múltipla, TEPT, TDAH | 18 | ✅ |
| Patrícia Souza Barbosa | TEPT, Enxaqueca | 12 | ✅ |
| Rodrigo Teixeira Costa | TEA, Distúrbio do Pânico | 12 | ✅ |
| João Castro Barbosa | Insônia, Dor Crônica | 6 | ✅ |
| Ana Santos Oliveira | Fibromialgia, Endometriose | 12 | ✅ |
| Vanessa Santos Araújo | Dor Lombar, Artrose | 12 | ✅ |
| Carolina Ribeiro Ribeiro | Dor Neuropática, Insônia | 18 | ✅ |
| Camila Dias Araújo | Enxaqueca, TAG | 12 | ✅ |
| Marcelo Araújo Melo | TEPT, Dor Crônica | 12 | ✅ |
| Marcelo Costa Gomes | TDAH, Esclerose Múltipla | 18 | ✅ |
| Isabela Araújo Silva | Fibromialgia, Dor Lombar | 12 | ✅ |
| Marcelo Oliveira Ribeiro | Artrose, Insônia | 18 | ✅ |
| Luísa Teixeira Teixeira | TAG, Endometriose | 12 | ✅ |
| Carolina Ribeiro Dias | Panico, Dor Neuropática | 12 | ✅ |

### 3. Severity Scale Consistency (0–10)

- Primary symptoms: 5–10 (severe)
- Secondary symptoms: 3–7 (moderate)
- All values are integers within valid range

### 4. Timeline Consistency

Evolution dates follow strict chronological order:

```
D0 (baseline) → D30 → D60 → D90 → D180
```

- No future dates beyond generation date
- All evolutions reference prior state
- Pain scores show realistic improvement trajectory: 8 → 6 → 5 → 4 → 3
- Sleep scores show improvement: 3 → 4 → 5 → 6 → 7
- Anxiety scores show improvement: 7 → 6 → 5 → 4 → 3

### 5. Medication History Consistency

Each patient has:
- 2–5 failed conventional medications
- Documented reason for discontinuation
- Duration of use (3–24 months)
- Efficacy rating (1–4/10)

Failed medications are clinically appropriate for the condition:
- Fibromyalgia → Amitriptilina, Pregabalina, Duloxetina
- Neuropathic pain → Gabapentina, Carbamazepina, Pregabalina
- Anxiety → Sertralina, Clonazepam, Venlafaxina

### 6. Cannabis Protocol Consistency

- CBD concentrations: 50–300 mg/mL (realistic)
- THC concentrations: 0–100 mg/mL (realistic)
- Dosing: 2–6 drops, 2–3×/day
- Titration plans include gradual escalation
- Treatment goals are measurable and condition-appropriate

### 7. Exam Result Consistency

- Hemogram values within normal ranges
- Liver function within reference intervals
- Vitamin D: 15–60 ng/mL (covers deficiency to normal)
- HbA1c: 4–10% (covers normal to diabetic)
- All numeric values are physiologically plausible

### 8. Prescription-Evolution Cross-Validation

- Prescriptions reference existing dosagens
- Prescription dates align with evolution timeline (D0, D30, D90)
- Dosage adjustments reflect clinical progress

---

## Consistency Score

```
Physician-Patient Assignment: 100%
Condition-Symptom Alignment:  100%
Severity Scale Validity:      100%
Timeline Consistency:         100%
Medication History:           100%
Cannabis Protocol:            100%
Exam Result Plausibility:     100%
Prescription-Evolution Match: 100%
─────────────────────────────────
OVERALL CONSISTENCY:          100%
```

---

*Validated by: Agent 5 (Quality Auditor) + Agent 6 (Dataset Consistency Validator)*
