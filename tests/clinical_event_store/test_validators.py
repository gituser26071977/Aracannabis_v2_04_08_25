"""
Testes dos Validators do Clinical Event Engine.

Cobertura:
    - validate_event_payload (com schema registrado)
    - is_valid_payload (versão booleana)
    - Schema ausente → qualquer payload é aceito
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import jsonschema
import pytest

from araos.clinical.event_store.catalog import ClinicalEventDefinition
from araos.clinical.event_store.validators import (
    is_valid_payload,
    validate_event_payload,
)


# Helper: cria definição com schema
def _definition(
    schema: Dict[str, Any],
    event_type: str = "TEST",
) -> ClinicalEventDefinition:
    return ClinicalEventDefinition(
        event_type=event_type,
        domain="clinical",
        producer="core",
        description="Test event",
        json_schema=schema,
    )


# Schema simples usado em vários testes
SCALE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "scale_code": {"type": "string"},
        "total_score": {"type": "number", "minimum": 0},
        "interpretation": {
            "type": "string",
            "enum": ["baixo", "moderado", "alto"],
        },
    },
    "required": ["scale_code", "total_score"],
    "additionalProperties": False,
}


# ═══════════════════════════════════════════════════════════════════════
# validate_event_payload — happy paths
# ═══════════════════════════════════════════════════════════════════════


class TestValidatePayloadAccepts:
    def test_valid_payload_passes(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {
            "scale_code": "GAD7",
            "total_score": 12.5,
            "interpretation": "moderado",
        }
        # Não deve lançar
        validate_event_payload(payload, defn)

    def REDACTED(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {"scale_code": "PHQ9", "total_score": 0}
        validate_event_payload(payload, defn)

    def test_no_schema_accepts_any(self):
        defn = _definition(schema={})  # schema vazio
        # Qualquer payload é aceito
        validate_event_payload({"anything": True}, defn)
        validate_event_payload({}, defn)

    def test_complex_nested_schema(self):
        schema = {
            "type": "object",
            "properties": {
                "patient": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "age_months": {"type": "integer", "minimum": 0},
                    },
                    "required": ["id"],
                },
                "scores": {
                    "type": "array",
                    "items": {"type": "number"},
                },
            },
            "required": ["patient", "scores"],
        }
        defn = _definition(schema)
        payload = {
            "patient": {"id": "p1", "age_months": 36},
            "scores": [1.0, 2.0, 3.5],
        }
        validate_event_payload(payload, defn)


# ═══════════════════════════════════════════════════════════════════════
# validate_event_payload — error cases
# ═══════════════════════════════════════════════════════════════════════


class TestValidatePayloadRejects:
    def test_missing_required_field(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {"scale_code": "GAD7"}  # falta total_score
        with pytest.raises(jsonschema.ValidationError):
            validate_event_payload(payload, defn)

    def test_wrong_type(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {"scale_code": "GAD7", "total_score": "string-not-number"}
        with pytest.raises(jsonschema.ValidationError):
            validate_event_payload(payload, defn)

    def test_below_minimum(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {"scale_code": "GAD7", "total_score": -1}
        with pytest.raises(jsonschema.ValidationError):
            validate_event_payload(payload, defn)

    def test_enum_violation(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {
            "scale_code": "GAD7",
            "total_score": 5,
            "interpretation": "nope",
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_event_payload(payload, defn)

    def REDACTED(self):
        defn = _definition(SCALE_SCHEMA)  # additionalProperties: False
        payload = {
            "scale_code": "GAD7",
            "total_score": 5,
            "extra_field": "not_allowed",
        }
        with pytest.raises(jsonschema.ValidationError):
            validate_event_payload(payload, defn)


# ═══════════════════════════════════════════════════════════════════════
# is_valid_payload — versão booleana
# ═══════════════════════════════════════════════════════════════════════


class TestIsValidPayload:
    def test_valid_returns_true(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {"scale_code": "GAD7", "total_score": 5}
        assert is_valid_payload(payload, defn) is True

    def test_invalid_returns_false(self):
        defn = _definition(SCALE_SCHEMA)
        payload = {"scale_code": "GAD7"}  # falta total_score
        assert is_valid_payload(payload, defn) is False

    def test_no_schema_returns_true(self):
        defn = _definition(schema={})
        assert is_valid_payload({"anything": True}, defn) is True

    def REDACTED(self):
        # Schema inválido (schema error, não payload error)
        defn = _definition(schema={"type": "invalid_type"})
        # jsonschema.SchemaError é capturada, retorna False
        assert is_valid_payload({}, defn) is False
