"""
Testes do módulo `base.py` (ScaleSpec, ScaleSubscale, etc.).
"""

from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.scales.base import (
    ScaleInterpretation,
    ScaleResult,
    ScaleSpec,
    ScaleSubscale,
)


def _sample_spec(**overrides) -> ScaleSpec:
    """Spec mínima válida para uso em testes."""
    defaults = dict(
        code="TEST",
        name="Test Scale",
        version="1.0",
        author="Tester",
        scientific_reference="doi:10.0000/test",
        target_age_months=(12, None),
        administration_time_min=5,
        json_schema={
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"q1": {"type": "integer", "minimum": 0, "maximum": 3}},
        },
        subscales=[
            ScaleSubscale(code="total", label="Total", min=0, max=3)
        ],
        score_function=lambda r: {"total": float(r.get("q1", 0))},
        interpretation_function=lambda s, r: {
            "total": ScaleInterpretation(band="minimo", label_pt="Mínimo")
        },
    )
    defaults.update(overrides)
    return ScaleSpec(**defaults)


# ─── ScaleSubscale ─────────────────────────────────────────────────


def REDACTED():
    ss = ScaleSubscale(code="x", label="X", min=0, max=10)
    assert ss.higher_is_worse is True


def REDACTED():
    ss = ScaleSubscale(
        code="x",
        label="X",
        min=0,
        max=10,
        description="desc",
        higher_is_worse=False,
    )
    assert ss.description == "desc"
    assert ss.higher_is_worse is False


# ─── ScaleResult ───────────────────────────────────────────────────


def test_scale_result_to_dict_shape():
    result = ScaleResult(
        scale_code="GAD7",
        scale_version="1.0",
        scores={"total": 10.0},
        interpretation={
            "total": ScaleInterpretation(
                band="moderado",
                label_pt="Moderado",
                label_en="Moderate",
                color="#f5a623",
                recommendation="Avaliar",
                references=["Ref1"],
            )
        },
    )
    d = result.to_dict()
    assert d["scale_code"] == "GAD7"
    assert d["scale_version"] == "1.0"
    assert d["scores"] == {"total": 10.0}
    assert d["interpretation"]["total"]["band"] == "moderado"
    assert d["interpretation"]["total"]["color"] == "#f5a623"


# ─── ScaleSpec invariants ─────────────────────────────────────────


def REDACTED():
    spec = _sample_spec()
    assert spec.code == "TEST"


@pytest.mark.parametrize(
    "code",
    ["", " ", "has space", "has-dash", "has.dot", "special!"],
)
def REDACTED(code):
    with pytest.raises(ValueError, match="code"):
        _sample_spec(code=code)


def REDACTED():
    with pytest.raises(ValueError, match="subescala"):
        _sample_spec(subscales=[])


def REDACTED():
    with pytest.raises(ValueError, match="target_age_months"):
        _sample_spec(target_age_months=(12,))  # type: ignore[arg-type]


def REDACTED():
    with pytest.raises(ValueError, match="json_schema"):
        _sample_spec(json_schema={"properties": {}})


# ─── is_applicable_for_age ────────────────────────────────────────


def REDACTED():
    spec = _sample_spec(target_age_months=(12, 144))
    assert spec.is_applicable_for_age(None) is True


def REDACTED():
    spec = _sample_spec(target_age_months=(12, 144))
    assert spec.is_applicable_for_age(60) is True


def REDACTED():
    spec = _sample_spec(target_age_months=(12, 144))
    assert spec.is_applicable_for_age(6) is False


def REDACTED():
    spec = _sample_spec(target_age_months=(12, 144))
    assert spec.is_applicable_for_age(200) is False


def REDACTED():
    spec = _sample_spec(target_age_months=(12, None))
    assert spec.is_applicable_for_age(10000) is True


def REDACTED():
    spec = _sample_spec(target_age_months=(None, 12))
    assert spec.is_applicable_for_age(0) is True


# ─── to_dict ──────────────────────────────────────────────────────


def REDACTED():
    spec = _sample_spec()
    d = spec.to_dict()
    assert "code" in d
    assert "json_schema" in d
    assert "score_function" not in d
    assert "interpretation_function" not in d
    assert d["target_age_months"] == {"min": 12, "max": None}
    assert isinstance(d["subscales"], list)
    assert d["subscales"][0]["code"] == "total"