# Prescription Content Schema (`conteudo_json`)

**Date:** 2026-06-02  
**Version:** 1.0  
**Status:** DOCUMENTED

---

## Context

The `Prescricao` model stores structured medication data in `conteudo_json`. This field is populated by `services/prescription_service.py` during prescription generation and is critical for MeshOS replay (read-only consumption).

## Database Model

```python
class Prescricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'))
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'))
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'))
    data_emissao = db.Column(db.DateTime, default=datetime.utcnow)
    conteudo_json = db.Column(db.JSON)
    observacoes = db.Column(db.Text)
    # ... timestamps (HARDENING-3)
```

## JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PrescricaoConteudo",
  "type": "object",
  "required": ["medicamentos"],
  "properties": {
    "medicamentos": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["nome", "posologia", "via"],
        "properties": {
          "nome": {
            "type": "string",
            "description": "Medication name + concentration (e.g. 'CBD 20% 30ml')"
          },
          "posologia": {
            "type": "string",
            "description": "Dosage instructions (e.g. '4 gotas, 3 vezes ao dia')"
          },
          "via": {
            "type": "string",
            "description": "Administration route (e.g. 'Sublingual', 'Uso Oral', 'Uso Tópico')"
          },
          "instrucoes": {
            "type": ["string", "null"],
            "description": "Special instructions (e.g. 'Ingerir junto de alimentos fonte de gordura')"
          },
          "concentracao_cbd": {
            "type": ["number", "null"],
            "description": "CBD concentration in mg"
          },
          "concentracao_thc": {
            "type": ["number", "null"],
            "description": "THC concentration in mg"
          }
        }
      }
    },
    "observacoes": {
      "type": ["string", "null"],
      "description": "General prescription observations"
    }
  }
}
```

## Example

```json
{
  "medicamentos": [
    {
      "nome": "CBD 20% 30ml",
      "posologia": "4 gotas, 3 vezes ao dia",
      "via": "Sublingual",
      "instrucoes": "Ingerir junto de alimentos fonte de gordura boa para otimização da absorção.",
      "concentracao_cbd": 6000.0,
      "concentracao_thc": null
    },
    {
      "nome": "THC 5% 30ml",
      "posologia": "2 gotas, 2 vezes ao dia",
      "via": "Sublingual",
      "instrucoes": null,
      "concentracao_cbd": null,
      "concentracao_thc": 1500.0
    }
  ],
  "observacoes": "Ajustar posologia conforme resposta clínica em 14 dias."
}
```

## Data Provenance

- **Source:** `Dosagem` table (products + custom doses)
- **Builder:** `services/prescription_service.py::generate_prescription_pdf()`
- **Consumed by:** `services/crew_agents.py` (patient summary), MeshOS replay

## MeshOS Replay Notes

- **Read-only:** MeshOS never writes prescriptions
- **Key field:** `medicamentos[].nome` for medication identification
- **Key field:** `medicamentos[].posologia` for dosage context
- **Optional enrichment:** `concentracao_cbd`/`concentracao_thc` when available
- **Temporal field:** `data_emissao` (business date), `created_at` (system timestamp)
