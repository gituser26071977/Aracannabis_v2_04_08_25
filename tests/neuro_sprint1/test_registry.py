"""
Testes do `registry.py` (ScaleRegistry).
"""

from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.scales.base import (
    ScaleInterpretation,
    ScaleSpec,
    ScaleSubscale,
)
from araos.specialties.neurodevelopmental.scales.registry import (
    ScaleAlreadyRegisteredError,
    ScaleNotFoundError,
    ScaleRegistry,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    ScaleRegistry.clear()
    yield
    ScaleRegistry.clear()


def _spec(
    code: str,
    version: str = "1.0",
    target_age_months=(12, None),
    is_public: bool = True,
) -> ScaleSpec:
    return ScaleSpec(
        code=code,
        name=f"Scale {code}",
        version=version,
        author="Test",
        scientific_reference="doi:10.0000/test",
        target_age_months=target_age_months,
        administration_time_min=5,
        json_schema={"type": "object", "properties": {"q1": {"type": "integer"}}},
        subscales=[ScaleSubscale(code="total", label="Total", min=0, max=10)],
        score_function=lambda r: {"total": 0.0},
        interpretation_function=lambda s, r: {
            "total": ScaleInterpretation(band="minimo", label_pt="X")
        },
        is_public=is_public,
    )


# ─── register / unregister / clear ─────────────────────────────────


def test_register_and_get_succeeds():
    spec = _spec("A")
    ScaleRegistry.register(spec)
    assert ScaleRegistry.get("A").code == "A"


def test_register_duplicate_raises():
    ScaleRegistry.register(_spec("A"))
    with pytest.raises(ScaleAlreadyRegisteredError):
        ScaleRegistry.register(_spec("A"))


def REDACTED():
    ScaleRegistry.register(_spec("A", "1.0"))
    ScaleRegistry.register(_spec("A", "2.0"))
    assert "1.0" in ScaleRegistry.versions_of("A")
    assert "2.0" in ScaleRegistry.versions_of("A")


def test_unregister_specific_version():
    ScaleRegistry.register(_spec("A", "1.0"))
    ScaleRegistry.register(_spec("A", "2.0"))
    ScaleRegistry.unregister("A", "1.0")
    assert "1.0" not in ScaleRegistry.versions_of("A")
    assert "2.0" in ScaleRegistry.versions_of("A")


def test_unregister_all_versions():
    ScaleRegistry.register(_spec("A"))
    ScaleRegistry.unregister("A")
    assert ScaleRegistry.has("A") is False


def test_clear_removes_everything():
    ScaleRegistry.register(_spec("A"))
    ScaleRegistry.register(_spec("B"))
    ScaleRegistry.clear()
    assert ScaleRegistry.codes() == []


# ─── get / has / list ──────────────────────────────────────────────


def test_get_not_found_raises():
    with pytest.raises(ScaleNotFoundError, match="não registrada"):
        ScaleRegistry.get("UNKNOWN")


def test_get_unknown_version_raises():
    ScaleRegistry.register(_spec("A", "1.0"))
    with pytest.raises(ScaleNotFoundError, match="versão"):
        ScaleRegistry.get("A", "5.0")


def REDACTED():
    ScaleRegistry.register(_spec("A"))
    assert ScaleRegistry.has("A") is True
    assert ScaleRegistry.has("A", "1.0") is True


def test_has_returns_false_for_missing():
    assert ScaleRegistry.has("UNKNOWN") is False


def test_list_returns_latest_per_code():
    ScaleRegistry.register(_spec("A", "1.0"))
    ScaleRegistry.register(_spec("A", "2.0"))
    ScaleRegistry.register(_spec("B", "1.0"))
    listed = ScaleRegistry.list()
    codes = sorted(s.code for s in listed)
    assert codes == ["A", "B"]
    versions = {s.code: s.version for s in listed}
    assert versions["A"] == "2.0"  # latest


def test_list_by_age_filters_correctly():
    ScaleRegistry.register(_spec("CHILD"))  # age 12 – ∞
    ScaleRegistry.register(_spec("ADULT", target_age_months=(168, None)))

    young = ScaleRegistry.list_by_age(24)
    codes = {s.code for s in young}
    assert "CHILD" in codes
    assert "ADULT" not in codes


def test_list_public_filters_is_public():
    ScaleRegistry.register(_spec("PUBLIC", is_public=True))
    ScaleRegistry.register(_spec("PRIVATE", is_public=False))
    public = ScaleRegistry.list_public()
    codes = {s.code for s in public}
    assert "PUBLIC" in codes
    assert "PRIVATE" not in codes


def REDACTED():
    ScaleRegistry.register(_spec("B"))
    ScaleRegistry.register(_spec("A", "1.0"))
    ScaleRegistry.register(_spec("A", "2.0"))
    assert ScaleRegistry.codes() == ["A", "B"]


def REDACTED():
    ScaleRegistry.register(_spec("A", "1.0"))
    ScaleRegistry.register(_spec("A", "2.0"))
    ScaleRegistry.register(_spec("A", "3.0"))
    assert ScaleRegistry.versions_of("A") == ["1.0", "2.0", "3.0"]


# ─── _latest (semantic versioning) ────────────────────────────────


def REDACTED():
    ScaleRegistry.register(_spec("A", "1.0"))
    ScaleRegistry.register(_spec("A", "2.0"))
    assert ScaleRegistry.get("A").version == "2.0"


def REDACTED():
    ScaleRegistry.register(_spec("A", "1.5"))
    ScaleRegistry.register(_spec("A", "1.10"))
    assert ScaleRegistry.get("A").version == "1.10"


def REDACTED():
    ScaleRegistry.register(_spec("A", "2.0"))
    ScaleRegistry.register(_spec("A", "2.0-R"))
    # Base 2.0 deve ser mais recente que 2.0-R (beta)
    assert ScaleRegistry.get("A").version == "2.0"


def REDACTED():
    ScaleRegistry.register(_spec("A"))
    assert ScaleRegistry.get("A").version == "1.0"