"""
AraOS Clinical Event Engine — Validators.

Validação de payloads contra JSON Schema Draft 7.

Lança `jsonschema.ValidationError` em caso de payload inválido.
"""

from __future__ import annotations

from typing import Any, Dict

import jsonschema

from .catalog import ClinicalEventDefinition


def validate_event_payload(
    payload: Dict[str, Any],
    definition: ClinicalEventDefinition,
) -> None:
    """
    Valida payload do evento contra o JSON Schema registrado.

    Args:
        payload: dict a ser validado
        definition: definição do event_type (carrega json_schema)

    Raises:
        jsonschema.ValidationError: se payload inválido
        jsonschema.SchemaError: se o próprio schema é inválido
    """
    schema = definition.json_schema
    if not schema:
        # Sem schema → payload é "opaco" para o motor.
        # Validação fica a cargo do produtor.
        return
    jsonschema.validate(payload, schema)


def is_valid_payload(
    payload: Dict[str, Any],
    definition: ClinicalEventDefinition,
) -> bool:
    """Versão não-throwing de validate_event_payload."""
    try:
        validate_event_payload(payload, definition)
        return True
    except jsonschema.ValidationError:
        return False
    except jsonschema.SchemaError:
        return False
