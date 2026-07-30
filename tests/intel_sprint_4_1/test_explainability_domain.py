"""
test_explainability_domain.py — pure domain tests para Explanation.

Cobre:
    - Construção + validação de invariantes
    - to_dict() (serialização canônica)
    - Casos inválidos (confidence fora de range, sem limitations, etc.)
    - contributing_event_ids empty com limitation explicando (regra de escape)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.explainability.domain.explanation import (
    AnalysisType,
    Explanation,
)
from araos.clinical.timeline.domain.variable import (
    VariableSource,
    VariableSpec,
)
from araos.clinical.timeline.domain.window import TimeWindow


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _window() -> TimeWindow:
    return TimeWindow.between(_now(), _now() + timedelta(days=30))


def _var() -> VariableSpec:
    return VariableSpec(
        name="CARS2_total",
        source=VariableSource.EVENT_PAYLOAD,
        source_event_type="ASSESSMENT_APPLIED",
        value_extractor="computed_scores.total",
        filter_clause={"scale_code": "CARS2"},
    )


def _explanation(**overrides) -> Explanation:
    defaults = dict(
        explanation_id="exp-1",
        analysis_id="ana-1",
        analysis_type=AnalysisType.TREND,
        question="CARS2 está melhorando?",
        answer="Slope negativo (p<0.05), sugerindo melhora.",
        confidence=0.85,
        method="linear_regression",
        data_window=_window(),
        variables=[_var()],
        contributing_event_ids=["ev-1", "ev-2"],
        assumptions=["Linearidade", "Independência dos pontos"],
        limitations=[
            "Correlação não implica causalidade",
            "N=10 pontos (pequeno para significância robusta)",
        ],
        created_at=_now(),
        analyst="system",
        tenant_id="t1",
        correlation_id="corr-1",
    )
    defaults.update(overrides)
    return Explanation(**defaults)


# ─── Construção e invariantes ─────────────────────────────────────────


def REDACTED():
    e = _explanation()
    assert e.explanation_id == "exp-1"
    assert e.confidence == 0.85
    assert e.n_events_analyzed == 2


def test_explanation_immutable():
    e = _explanation()
    with pytest.raises(Exception):
        e.confidence = 0.5  # type: ignore[misc]


def REDACTED():
    with pytest.raises(ValueError, match="explanation_id is required"):
        _explanation(explanation_id="")


def REDACTED():
    with pytest.raises(ValueError, match="analysis_id is required"):
        _explanation(analysis_id="")


def test_explanation_requires_question():
    with pytest.raises(ValueError, match="question is required"):
        _explanation(question="")


def test_explanation_requires_answer():
    with pytest.raises(ValueError, match="answer is required"):
        _explanation(answer="")


def test_explanation_requires_method():
    with pytest.raises(ValueError, match="method is required"):
        _explanation(method="")


def REDACTED():
    with pytest.raises(ValueError, match="confidence must be in"):
        _explanation(confidence=-0.1)


def REDACTED():
    with pytest.raises(ValueError, match="confidence must be in"):
        _explanation(confidence=1.5)


def REDACTED():
    e0 = _explanation(confidence=0.0)
    e1 = _explanation(confidence=1.0)
    assert e0.confidence == 0.0
    assert e1.confidence == 1.0


def REDACTED():
    with pytest.raises(ValueError, match="variables must have at least 1"):
        _explanation(variables=[])


def REDACTED():
    with pytest.raises(ValueError, match="limitations must have at least 1"):
        _explanation(limitations=[])


def REDACTED():
    with pytest.raises(ValueError, match="created_at must be timezone-aware"):
        _explanation(created_at=datetime.now())


# ─── contributing_event_ids edge cases ────────────────────────────────


def REDACTED():
    """Permite contributing_event_ids=[] se limitations explica insufficient data."""
    e = _explanation(
        contributing_event_ids=[],
        limitations=[
            "insufficient_data: 0 events in window — análise não pôde ser executada",
        ],
    )
    assert e.n_events_analyzed == 0


def REDACTED():
    """Se contributing_event_ids vazio + sem limitation explicando → erro."""
    with pytest.raises(ValueError, match="contributing_event_ids empty"):
        _explanation(
            contributing_event_ids=[],
            limitations=["Correlação não implica causalidade"],
        )


# ─── to_dict ──────────────────────────────────────────────────────────


def test_explanation_to_dict_basic():
    e = _explanation()
    d = e.to_dict()
    assert d["explanation_id"] == "exp-1"
    assert d["analysis_type"] == "trend"
    assert d["confidence"] == 0.85
    assert d["method"] == "linear_regression"
    assert d["n_events_analyzed"] == 2
    assert d["data_window"]["start"]
    assert d["data_window"]["end"]
    assert isinstance(d["variables"], list)
    assert len(d["variables"]) == 1
    assert d["variables"][0]["name"] == "CARS2_total"


def REDACTED():
    e = _explanation()
    d = e.to_dict()
    assert len(d["assumptions"]) == 2
    assert "Linearidade" in d["assumptions"]
    assert len(d["limitations"]) == 2
    assert "causalidade" in d["limitations"][0]


# ─── AnalysisType ─────────────────────────────────────────────────────


def test_analysis_type_values():
    assert AnalysisType.CORRELATION.value == "correlation"
    assert AnalysisType.TREND.value == "trend"
    assert AnalysisType.HYPOTHESIS.value == "hypothesis"
    assert AnalysisType.EPISODE_SUGGESTION.value == "episode_suggestion"
    assert AnalysisType.COHORT_EVALUATION.value == "cohort_evaluation"
    assert AnalysisType.FORECAST.value == "forecast"
    assert AnalysisType.ANOMALY.value == "anomaly"


def test_analysis_type_count():
    # Sprint 4.2 adicionou CONTEXT_SUGGESTION ao conjunto de AnalysisTypes.
    # Total atual: 8 (CORRELATION, TREND, ANOMALY, HYPOTHESIS,
    # EPISODE_SUGGESTION, CONTEXT_SUGGESTION, COHORT_EVALUATION, FORECAST).
    assert len(list(AnalysisType)) == 8