# API Insertion Plan

**Program:** API-1B — Homologation Dataset  
**Date:** 2026-06-02  
**Status:** EXECUTED

---

## API Schema Discovery

All endpoints were discovered by reading `routes/*.py` source code.

### Authentication Endpoints

```
POST /api/auth/login
  Body: { "usuario": string, "senha": string }
  Returns: { "access_token": JWT }

POST /api/auth/register
  Body: { "nome", "crm", "uf_crm", "usuario", "senha", "email" }
  Returns: { "profissional": { "id", ... } }
```

### Patient Endpoints

```
POST /api/pacientes/
  Body: {
    "nome": string (required),
    "data_nascimento": "YYYY-MM-DD" (required),
    "cpf": string,
    "genero": string,
    "telefone": string,
    "email": string,
    "endereco": string,
    "diagnostico": string,
    "observacoes": string,
    "em_tratamento": boolean
  }
  Returns: { "paciente": { "id", ... } }

GET /api/pacientes/<id>
  Returns: { "paciente": { full record } }
```

### Symptom Endpoints

```
POST /api/sintomas/paciente/<paciente_id>
  Body: {
    "data": "YYYY-MM-DD" (required),
    "sintoma": string (required),
    "intensidade": integer 0-10 (required),
    "observacoes": string
  }
```

### Dosage Endpoints

```
POST /api/dosagens/paciente/<paciente_id>
  Body: {
    "data": "YYYY-MM-DD" (required),
    "dosagem": string (required),
    "via_administracao": string,
    "gotas": integer,
    "frequencia_diaria": integer,
    "concentracao_cbd": number,
    "concentracao_thc": number,
    "instrucoes_uso": string,
    "observacoes": string
  }
```

### Evolution Endpoints

```
POST /api/evolucoes/paciente/<paciente_id>
  Body: {
    "nota_evolucao": string (required),
    "data_evolucao": "YYYY-MM-DD",
    "use_ai_processing": false
  }
```

### Exam Endpoints

```
POST /api/exames
  Content-Type: multipart/form-data
  Fields: {
    "paciente_id": string (required),
    "profissional_id": string (required),
    "data_exame": "YYYY-MM-DD",
    "tipo_exame": "texto" | "arquivo" | "numerico",
    "titulo": string (required),
    "descricao": string (for 'texto'),
    "valor": string (for 'numerico'),
    "unidade": string (for 'numerico')
  }
```

### Consultation Endpoints

```
POST /api/consultas/
  Body: {
    "paciente_id": integer (required),
    "data_hora": "YYYY-MM-DD HH:MM:SS" (required),
    "tipo": string,
    "status": string,
    "observacoes": string
  }
```

### Prescription Endpoints

```
POST /api/prescricoes/gerar
  Body: {
    "paciente_id": integer (required),
    "dosagens_ids": [integer] (required),
    "observacoes": string
  }
  Returns: { "success": true, "data": { prescription record } }
```

## Insertion Order (Dependency Graph)

```
Physician ──→ Patient ──→ Symptom
              │           ├── Dosage ──→ Prescription
              │           ├── Evolution
              │           ├── Exam
              │           └── Consultation
```

## Field Mapping Precision

| Target Field | API Field | Source | Verified |
|-------------|-----------|--------|----------|
| Patient name | `nome` | Synthetic generator | ✅ |
| Birth date | `data_nascimento` | `date.strftime("%Y-%m-%d")` | ✅ |
| CPF | `cpf` | `generate_cpf()` | ✅ |
| Gender | `genero` | "Feminino" / "Masculino" | ✅ |
| Diagnosis | `diagnostico` | Condition names joined | ✅ |
| Symptom name | `sintoma` | From condition template | ✅ |
| Severity | `intensidade` | Random 0–10 | ✅ |
| Evolution text | `nota_evolucao` | Generated narrative | ✅ |
| Exam title | `titulo` | From EXAM_TEMPLATES | ✅ |
| Exam value | `valor` | Random within reference | ✅ |
| Dosage name | `dosagem` | Product name | ✅ |
| CBD mg | `concentracao_cbd` | Product × 30 | ✅ |
| THC mg | `concentracao_thc` | Product × 30 | ✅ |

## No Assumptions, No Guessing

Every field was verified against:
1. Source code of route handlers
2. Model column definitions
3. API response validation
4. Database schema confirmation

---

*Schema verified by: Manual code inspection of routes/auth.py, routes/pacientes.py, routes/sintomas.py, routes/dosagens.py, routes/evolucoes.py, routes/exames.py, routes/consultas.py, routes/prescricoes.py*
