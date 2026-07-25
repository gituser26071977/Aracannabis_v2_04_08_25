"""
AraOS Neurodevelopmental — Scale Runner.

Executor de uma escala: recebe `RawResponses` (já validadas contra
o JSON Schema) e produz `ScaleResult` (scores + interpretação).

Funções puras, sem side-effects, sem I/O. Persistência é responsabilidade
do `ScaleResponseStore`.

Uso:

    spec = ScaleRegistry.get("GAD7")
    raw = {"q1": 2, "q2": 3, ..., "q7": 1}
    result = ScaleRunner(spec).run(raw)
    # result.scores == {"total": 12.0}
    # result.interpretation == {"total": ScaleInterpretation(band="moderado", ...)}
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from jsonschema import Draft7Validator

from .base import (
    ComputedScores,
    RawResponses,
    ScaleInterpretation,
    ScaleResult,
    ScaleSpec,
)


class ScaleValidationError(Exception):
    """Respostas brutas não conformes ao JSON Schema da escala."""


class ScaleRunner:
    """
    Executor de uma `ScaleSpec` específica.

    Valida as respostas brutas contra o JSON Schema antes de calcular.
    """

    def __init__(self, spec: ScaleSpec) -> None:
        self.spec = spec
        self._validator = Draft7Validator(spec.json_schema)

    def validate(self, raw_responses: RawResponses) -> None:
        """
        Valida `raw_responses` contra o JSON Schema da escala.

        Raises:
            ScaleValidationError: com lista detalhada de erros.
        """
        errors = sorted(self._validator.iter_errors(raw_responses), key=lambda e: e.path)
        if errors:
            msgs = []
            for err in errors:
                path = ".".join(str(p) for p in err.absolute_path) or "<root>"
                msgs.append(f"{path}: {err.message}")
            raise ScaleValidationError(
                f"Respostas inválidas para escala {self.spec.code} {self.spec.version}: "
                + "; ".join(msgs)
            )

    def compute_scores(self, raw_responses: RawResponses) -> ComputedScores:
        """
        Calcula scores via `spec.score_function`. Assume que `validate` já foi chamado.
        """
        return self.spec.score_function(raw_responses)

    def interpret(
        self,
        scores: ComputedScores,
        raw_responses: RawResponses,
    ) -> Dict[str, ScaleInterpretation]:
        """
        Gera interpretação via `spec.interpretation_function`.
        """
        return self.spec.interpretation_function(scores, raw_responses)

    def run(
        self,
        raw_responses: RawResponses,
        metadata: Optional[Dict[str, Any]] = None,
        validate: bool = True,
    ) -> ScaleResult:
        """
        Pipeline completo: valida → calcula → interpreta.

        Args:
            raw_responses: dict de respostas brutas.
            metadata: campos extras (idade, observador, contexto clínico).
            validate: se True, valida contra JSON Schema antes de calcular.

        Returns:
            ScaleResult com scores + interpretação.
        """
        if validate:
            self.validate(raw_responses)

        scores = self.compute_scores(raw_responses)
        interpretation = self.interpret(scores, raw_responses)

        return ScaleResult(
            scale_code=self.spec.code,
            scale_version=self.spec.version,
            scores=scores,
            interpretation=interpretation,
            metadata=metadata or {},
        )

    def run_safe(
        self,
        raw_responses: RawResponses,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Versão que sempre retorna dict (útil para APIs).
        Erros são serializados em `{"error": ...}`.
        """
        try:
            result = self.run(raw_responses, metadata=metadata)
            return {"ok": True, "result": result.to_dict()}
        except ScaleValidationError as e:
            return {"ok": False, "error": "validation_error", "message": str(e)}
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": "runtime_error", "message": str(e)}

    # ─── Helpers estáticos ──────────────────────────────────────────
    @staticmethod
    def json_schema_default(schema_type: str = "object") -> Dict[str, Any]:
        """Retorna um JSON Schema Draft 7 mínimo para tipo 'object'."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": schema_type,
            "additionalProperties": False,
        }

    @staticmethod
    def likert_question_schema(
        code: str,
        min_val: int = 0,
        max_val: int = 3,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Gera JSON Schema para uma questão tipo Likert (comum em escalas).

        Args:
            code: nome do campo (ex: "q1").
            min_val: menor valor (ex: 0).
            max_val: maior valor (ex: 3).
            description: texto exibido ao aplicador.
        """
        return {
            code: {
                "type": "integer",
                "minimum": min_val,
                "maximum": max_val,
                "description": description,
            }
        }

    @staticmethod
    def merge_schemas(*schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Concatena JSON Schemas de campos em um único schema de objeto."""
        merged: Dict[str, Any] = ScaleRunner.json_schema_default()
        properties: Dict[str, Any] = {}
        required: list = []
        for schema in schemas:
            properties.update(schema.get("properties", schema))
            required.extend(schema.get("required", []))
        merged["properties"] = properties
        if required:
            merged["required"] = sorted(set(required))
        return merged

    @staticmethod
    def dump_schema_for_frontend(schema: Dict[str, Any]) -> str:
        """Serializa JSON Schema para string (uso em APIs)."""
        return json.dumps(schema, ensure_ascii=False, sort_keys=True)