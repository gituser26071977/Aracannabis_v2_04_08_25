"""
Testes das escalas builtin — GAD-7 e PHQ-9.

Casos de borda cobertos:
    - Limites mínimos (escore 0)
    - Limites máximos (escore 21 / 27)
    - Faixas intermediárias
    - Validação de JSON Schema
    - Item crítico 9 do PHQ-9 (autolesão)
"""

from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.scales.builtins import (
    GAD7_SPEC,
    PHQ9_SPEC,
    _register_all,
)
from araos.specialties.neurodevelopmental.scales.registry import ScaleRegistry
from araos.specialties.neurodevelopmental.scales.runner import (
    ScaleRunner,
    ScaleValidationError,
)


# ─── Auto-registro ─────────────────────────────────────────────────


def REDACTED():
    _register_all()  # idempotente
    assert ScaleRegistry.has("GAD7")
    assert ScaleRegistry.has("PHQ9")


def test_gad7_spec_has_required_fields():
    assert GAD7_SPEC.code == "GAD7"
    assert GAD7_SPEC.target_age_months[0] == 168  # ≥14 anos
    assert len(GAD7_SPEC.subscales) == 1
    assert GAD7_SPEC.subscales[0].max == 21


def test_phq9_spec_has_required_fields():
    assert PHQ9_SPEC.code == "PHQ9"
    assert PHQ9_SPEC.target_age_months[0] == 144  # ≥12 anos
    assert len(PHQ9_SPEC.subscales) == 2


# ─── GAD-7 scoring ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "responses,expected_total",
    [
        # Todos zero
        ({f"q{i}": 0 for i in range(1, 8)}, 0.0),
        # Todos máximo
        ({f"q{i}": 3 for i in range(1, 8)}, 21.0),
        # Misto
        ({"q1": 2, "q2": 3, "q3": 1, "q4": 2, "q5": 0, "q6": 1, "q7": 3}, 12.0),
        # Aleatório
        ({"q1": 1, "q2": 1, "q3": 2, "q4": 0, "q5": 1, "q6": 0, "q7": 1}, 6.0),
    ],
)
def test_gad7_score_function(responses, expected_total):
    runner = ScaleRunner(GAD7_SPEC)
    scores = runner.run(responses).scores
    assert scores["total"] == expected_total


def test_gad7_missing_question_raises():
    """Quando q7 está ausente, o JSON Schema rejeita → ScaleValidationError."""
    runner = ScaleRunner(GAD7_SPEC)
    with pytest.raises(ScaleValidationError, match="q7"):
        runner.run({f"q{i}": 1 for i in range(1, 7)})


def REDACTED():
    """Quando q7 está fora de [0,3], JSON Schema rejeita → ScaleValidationError."""
    runner = ScaleRunner(GAD7_SPEC)
    with pytest.raises(ScaleValidationError, match="(maximum|inteiro)"):
        runner.run({f"q{i}": 1 for i in range(1, 7)} | {"q7": 99})


def REDACTED():
    """Chamando _score_gad7 diretamente (sem JSON Schema), espera ValueError."""
    from araos.specialties.neurodevelopmental.scales.builtins.gad7 import (
        _score_gad7,
    )

    with pytest.raises(ValueError, match="inteiro 0-3"):
        _score_gad7({"q1": 1, "q2": 1, "q3": 1, "q4": 1, "q5": 1, "q6": 1, "q7": 99})


def REDACTED():
    runner = ScaleRunner(GAD7_SPEC)
    with pytest.raises(ScaleValidationError):
        runner.run({f"q{i}": 1 for i in range(1, 8)} | {"q8": 0})


def test_gad7_interpretation_bands():
    runner = ScaleRunner(GAD7_SPEC)
    full = {f"q{i}": 0 for i in range(1, 8)}
    bands = []
    for total in [0, 4, 5, 9, 10, 14, 15, 21]:
        per_q = total // 7
        extra = total % 7
        responses = {f"q{i}": per_q + (1 if i <= extra else 0) for i in range(1, 8)}
        result = runner.run(responses)
        bands.append((total, result.interpretation["total"].band))
    assert bands == [
        (0, "minimo"),
        (4, "minimo"),
        (5, "leve"),
        (9, "leve"),
        (10, "moderado"),
        (14, "moderado"),
        (15, "severo"),
        (21, "severo"),
    ]


def REDACTED():
    runner = ScaleRunner(GAD7_SPEC)
    result = runner.run({f"q{i}": 2 for i in range(1, 8)})
    interp = result.interpretation["total"]
    assert interp.color.startswith("#")
    assert len(interp.color) == 7


# ─── PHQ-9 scoring ─────────────────────────────────────────────────


def test_phq9_score_total_zero():
    runner = ScaleRunner(PHQ9_SPEC)
    result = runner.run({f"q{i}": 0 for i in range(1, 10)})
    assert result.scores["total"] == 0.0


def test_phq9_score_total_max():
    runner = ScaleRunner(PHQ9_SPEC)
    result = runner.run({f"q{i}": 3 for i in range(1, 10)})
    assert result.scores["total"] == 27.0


def REDACTED():
    runner = ScaleRunner(PHQ9_SPEC)
    responses = {f"q{i}": 0 for i in range(1, 9)} | {"q9": 2}
    result = runner.run(responses)
    assert result.scores["item9_self_harm_risk"] == 2.0


@pytest.mark.parametrize(
    "total,expected_band",
    [
        (0, "minimo"),
        (4, "minimo"),
        (5, "leve"),
        (9, "leve"),
        (10, "moderado"),
        (14, "moderado"),
        (15, "moderadamente_severo"),
        (19, "moderadamente_severo"),
        (20, "severo"),
        (27, "severo"),
    ],
)
def test_phq9_interpretation_bands(total, expected_band):
    runner = ScaleRunner(PHQ9_SPEC)
    # Constrói respostas que somam EXATAMENTE `total` com q9 começando em 0.
    # Para totals > 24, q9 precisa ser ≥1 (mas o teste checa só `band`).
    q9 = max(0, total - 24)
    rest = total - q9
    base = rest // 8
    extra = rest % 8
    responses = {
        f"q{i}": min(3, base + (1 if i <= extra else 0))
        for i in range(1, 9)
    }
    responses["q9"] = q9
    result = runner.run(responses)
    assert result.scores["total"] == total, (
        f"Esperado total={total}, obtido {result.scores['total']!r}"
    )
    assert result.interpretation["total"].band == expected_band


def REDACTED():
    runner = ScaleRunner(PHQ9_SPEC)
    responses = {f"q{i}": 0 for i in range(1, 9)} | {"q9": 1}
    result = runner.run(responses)
    rec = result.interpretation["total"].recommendation
    assert "ATENÇÃO" in rec
    assert "autolesão" in rec.lower()


def REDACTED():
    runner = ScaleRunner(PHQ9_SPEC)
    responses = {f"q{i}": 0 for i in range(1, 10)}
    result = runner.run(responses)
    rec = result.interpretation["total"].recommendation
    assert "ATENÇÃO" not in rec


def REDACTED():
    runner = ScaleRunner(PHQ9_SPEC)
    responses = {f"q{i}": 3 for i in range(1, 10)}
    result = runner.run(responses)
    interp = result.interpretation["total"]
    assert interp.band == "severo"
    assert "ATENÇÃO" in interp.recommendation


def REDACTED():
    schema = PHQ9_SPEC.json_schema
    q9_desc = schema["properties"]["q9"]["description"]
    assert "morte" in q9_desc.lower() or "autolesão" in q9_desc.lower()


def REDACTED():
    runner = ScaleRunner(PHQ9_SPEC)
    with pytest.raises(ScaleValidationError):
        runner.run({f"q{i}": 0 for i in range(1, 9)})  # falta q9


def REDACTED():
    runner = ScaleRunner(PHQ9_SPEC)
    responses = {f"q{i}": 0 for i in range(1, 9)} | {"q9": 99}
    with pytest.raises(ScaleValidationError):
        runner.run(responses)


# ─── is_applicable_for_age ────────────────────────────────────────


def REDACTED():
    assert GAD7_SPEC.is_applicable_for_age(120) is False  # 10 anos


def test_gad7_applicable_above_14yo():
    assert GAD7_SPEC.is_applicable_for_age(180) is True  # 15 anos


def REDACTED():
    assert PHQ9_SPEC.is_applicable_for_age(120) is False


def test_phq9_applicable_at_12yo():
    assert PHQ9_SPEC.is_applicable_for_age(144) is True


# ─── Serialização ──────────────────────────────────────────────────


def REDACTED():
    d = GAD7_SPEC.to_dict()
    assert "score_function" not in d
    assert "interpretation_function" not in d
    assert d["code"] == "GAD7"
    assert d["is_public"] is True
    assert "pt-BR" in d["languages"]


def REDACTED():
    d = PHQ9_SPEC.to_dict()
    assert len(d["subscales"]) == 2
    codes = {s["code"] for s in d["subscales"]}
    assert codes == {"total", "item9_self_harm_risk"}