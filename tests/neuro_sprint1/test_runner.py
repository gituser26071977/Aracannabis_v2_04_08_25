"""
Testes do `runner.py` (ScaleRunner).
"""

from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.scales.base import (
    ScaleInterpretation,
    ScaleSpec,
    ScaleSubscale,
)
from araos.specialties.neurodevelopmental.scales.runner import (
    ScaleRunner,
    ScaleValidationError,
)


def _spec(schema: dict) -> ScaleSpec:
    return ScaleSpec(
        code="T",
        name="T",
        version="1.0",
        author="t",
        scientific_reference="r",
        target_age_months=(0, None),
        administration_time_min=1,
        json_schema=schema,
        subscales=[ScaleSubscale(code="total", label="Total", min=0, max=10)],
        score_function=lambda r: {"total": float(r.get("q1", 0))},
        interpretation_function=lambda s, r: {
            "total": ScaleInterpretation(band="ok", label_pt="OK")
        },
    )


def REDACTED():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}, "required": ["q1"]}
    runner = ScaleRunner(_spec(schema))
    runner.validate({"q1": 3})  # no exception


def REDACTED():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}, "required": ["q1"]}
    runner = ScaleRunner(_spec(schema))
    with pytest.raises(ScaleValidationError) as exc:
        runner.validate({})
    assert "q1" in str(exc.value)


def test_validate_rejects_wrong_type():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}, "required": ["q1"]}
    runner = ScaleRunner(_spec(schema))
    with pytest.raises(ScaleValidationError):
        runner.validate({"q1": "not_an_integer"})


def test_validate_rejects_out_of_range():
    schema = {
        "type": "object",
        "properties": {"q1": {"type": "integer", "minimum": 0, "maximum": 3}},
        "required": ["q1"],
    }
    runner = ScaleRunner(_spec(schema))
    with pytest.raises(ScaleValidationError):
        runner.validate({"q1": 99})


def REDACTED():
    schema = {
        "type": "object",
        "properties": {"q1": {"type": "integer"}, "q2": {"type": "integer"}},
        "required": ["q1", "q2"],
    }
    runner = ScaleRunner(_spec(schema))
    with pytest.raises(ScaleValidationError) as exc:
        runner.validate({})
    msg = str(exc.value)
    assert "q1" in msg
    assert "q2" in msg


def REDACTED():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}}
    runner = ScaleRunner(_spec(schema))
    scores = runner.compute_scores({"q1": 7})
    assert scores == {"total": 7.0}


def REDACTED():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}, "required": ["q1"]}
    runner = ScaleRunner(_spec(schema))
    result = runner.run({"q1": 5}, metadata={"x": 1})
    assert result.scale_code == "T"
    assert result.scores == {"total": 5.0}
    assert "total" in result.interpretation


def REDACTED():
    schema = {
        "type": "object",
        "properties": {"q1": {"type": "integer", "minimum": 0, "maximum": 3}},
        "required": ["q1"],
    }
    runner = ScaleRunner(_spec(schema))
    # q1=99 viola o schema mas validate=False pula a validação
    result = runner.run({"q1": 99}, validate=False)
    assert result.scores == {"total": 99.0}


def REDACTED():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}, "required": ["q1"]}
    runner = ScaleRunner(_spec(schema))
    payload = runner.run_safe({})
    assert payload["ok"] is False
    assert payload["error"] == "validation_error"


def REDACTED():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}, "required": ["q1"]}
    runner = ScaleRunner(_spec(schema))
    payload = runner.run_safe({"q1": 1})
    assert payload["ok"] is True
    assert "result" in payload


def test_run_safe_wraps_runtime_errors():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}, "required": ["q1"]}

    def _bad_score(_):
        raise RuntimeError("kaboom")

    spec = _spec(schema)
    spec = ScaleSpec(
        code=spec.code,
        name=spec.name,
        version=spec.version,
        author=spec.author,
        scientific_reference=spec.scientific_reference,
        target_age_months=spec.target_age_months,
        administration_time_min=spec.administration_time_min,
        json_schema=spec.json_schema,
        subscales=spec.subscales,
        score_function=_bad_score,
        interpretation_function=spec.interpretation_function,
    )
    runner = ScaleRunner(spec)
    payload = runner.run_safe({"q1": 1})
    assert payload["ok"] is False
    assert payload["error"] == "runtime_error"


# ─── Helpers estáticos ──────────────────────────────────────────────


def REDACTED():
    schema = ScaleRunner.json_schema_default()
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False


def test_likert_question_schema_bounds():
    q = ScaleRunner.likert_question_schema("q1", min_val=0, max_val=3)
    assert q["q1"]["minimum"] == 0
    assert q["q1"]["maximum"] == 3
    assert q["q1"]["type"] == "integer"


def REDACTED():
    s1 = {"properties": {"a": {"type": "integer"}}, "required": ["a"]}
    s2 = {"properties": {"b": {"type": "string"}}, "required": ["b"]}
    merged = ScaleRunner.merge_schemas(s1, s2)
    assert "a" in merged["properties"]
    assert "b" in merged["properties"]
    assert set(merged["required"]) == {"a", "b"}


def REDACTED():
    schema = {"type": "object", "properties": {"q1": {"type": "integer"}}}
    s = ScaleRunner.dump_schema_for_frontend(schema)
    assert isinstance(s, str)
    assert "q1" in s