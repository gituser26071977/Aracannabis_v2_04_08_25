"""
test_explanation_registry.py — InMemory + SQLAlchemy registry tests.

Cobre:
    - InMemoryExplanationRegistry:
        - register() retorna explanation_id e dedupe por id.
        - get() retorna None se não encontrada.
        - list_for_analysis / list_for_event / list_for_type.
        - count() correto.
        - thread-safety (smoke test).
        - clear() (helper de teste).
    - SqlAlchemyExplanationRegistry:
        - round-trip via SQL (register → get).
        - list_for_analysis respeita tenant isolation.
        - list_for_event faz JSON containment.
        - count por tenant.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.explainability import (
    AnalysisType,
    Explanation,
    InMemoryExplanationRegistry,
)
from araos.clinical.explainability.registry import (
    ExplanationRegistry,
    new_explanation_id,
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
        name="x",
        source=VariableSource.EVENT_PAYLOAD,
        source_event_type="ASSESSMENT_APPLIED",
        value_extractor="score",
    )


def _explanation(analysis_id="ana-1", tenant_id="t1",
                 contributing=None, analysis_type=None,
                 limitations=None) -> Explanation:
    return Explanation(
        explanation_id=new_explanation_id(),
        analysis_id=analysis_id,
        analysis_type=analysis_type or AnalysisType.TREND,
        question="Q?",
        answer="A.",
        confidence=0.8,
        method="linear_regression",
        data_window=_window(),
        variables=[_var()],
        contributing_event_ids=contributing or ["ev-1", "ev-2"],
        assumptions=["ass1"],
        limitations=limitations or ["Correlação não implica causalidade"],
        created_at=_now(),
        tenant_id=tenant_id,
    )


# ─── InMemoryExplanationRegistry ──────────────────────────────────────


def test_inmemory_register_returns_id(explanation_registry):
    e = _explanation()
    rid = explanation_registry.register(e)
    assert rid == e.explanation_id
    assert isinstance(rid, str)
    assert rid.startswith("exp_")


def REDACTED(explanation_registry):
    e = _explanation()
    explanation_registry.register(e)
    fetched = explanation_registry.get(e.explanation_id)
    assert fetched is not None
    assert fetched.explanation_id == e.explanation_id
    assert fetched.confidence == e.confidence


def REDACTED(explanation_registry):
    assert explanation_registry.get("nonexistent") is None


def REDACTED(explanation_registry):
    with pytest.raises(TypeError):
        explanation_registry.register({"not": "an explanation"})


def test_inmemory_list_for_analysis(explanation_registry):
    a1 = _explanation(analysis_id="ana-1")
    a2 = _explanation(analysis_id="ana-1")
    b = _explanation(analysis_id="ana-2")
    explanation_registry.register(a1)
    explanation_registry.register(a2)
    explanation_registry.register(b)

    results = explanation_registry.list_for_analysis("t1", "ana-1")
    assert len(results) == 2
    ids = {r.explanation_id for r in results}
    assert a1.explanation_id in ids
    assert a2.explanation_id in ids


def test_inmemory_list_for_event(explanation_registry):
    e1 = _explanation(contributing=["ev-A", "ev-B"])
    e2 = _explanation(contributing=["ev-B", "ev-C"])
    e3 = _explanation(contributing=["ev-D"])
    explanation_registry.register(e1)
    explanation_registry.register(e2)
    explanation_registry.register(e3)

    a_results = explanation_registry.list_for_event("t1", "ev-A")
    assert len(a_results) == 1
    b_results = explanation_registry.list_for_event("t1", "ev-B")
    assert len(b_results) == 2
    d_results = explanation_registry.list_for_event("t1", "ev-D")
    assert len(d_results) == 1


def test_inmemory_list_for_type(explanation_registry):
    e1 = _explanation(analysis_type=AnalysisType.TREND)
    e2 = _explanation(analysis_type=AnalysisType.CORRELATION)
    e3 = _explanation(analysis_type=AnalysisType.TREND)
    explanation_registry.register(e1)
    explanation_registry.register(e2)
    explanation_registry.register(e3)

    trends = explanation_registry.list_for_type("t1", AnalysisType.TREND)
    assert len(trends) == 2
    corrs = explanation_registry.list_for_type("t1", AnalysisType.CORRELATION)
    assert len(corrs) == 1


def test_inmemory_list_for_type_limit(explanation_registry):
    for _ in range(5):
        explanation_registry.register(_explanation(analysis_type=AnalysisType.TREND))
    results = explanation_registry.list_for_type("t1", AnalysisType.TREND, limit=2)
    assert len(results) == 2


def test_inmemory_count(explanation_registry):
    assert explanation_registry.count("t1") == 0
    explanation_registry.register(_explanation())
    explanation_registry.register(_explanation())
    assert explanation_registry.count("t1") == 2


def test_inmemory_clear(explanation_registry):
    explanation_registry.register(_explanation())
    explanation_registry.clear()
    assert explanation_registry.count("t1") == 0


def REDACTED():
    assert issubclass(InMemoryExplanationRegistry, ExplanationRegistry)


def test_inmemory_thread_safe_smoke():
    """Smoke test: múltiplas threads registrando não quebram."""
    import threading

    reg = InMemoryExplanationRegistry()
    errors: list = []

    def worker(i: int) -> None:
        try:
            for _ in range(10):
                reg.register(_explanation(analysis_id=f"a-{i}"))
        except Exception as e:    # pragma: no cover
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    # 5 threads * 10 explanações = 50
    assert reg.count("t1") == 50


# ─── SqlAlchemyExplanationRegistry ────────────────────────────────────


def test_sql_register_and_get(sql_explanation_registry, session_factory):
    e = _explanation(tenant_id="tenant-sql")
    rid = sql_explanation_registry.register(e)
    assert rid == e.explanation_id
    fetched = sql_explanation_registry.get(rid)
    assert fetched is not None
    assert fetched.tenant_id == "tenant-sql"
    assert fetched.confidence == e.confidence
    assert fetched.analysis_id == e.analysis_id


def test_sql_get_missing(sql_explanation_registry):
    assert sql_explanation_registry.get("missing-id") is None


def test_sql_list_for_analysis(sql_explanation_registry):
    a1 = _explanation(analysis_id="sql-ana-1", tenant_id="t-sql")
    a2 = _explanation(analysis_id="sql-ana-1", tenant_id="t-sql")
    b = _explanation(analysis_id="sql-ana-2", tenant_id="t-sql")
    sql_explanation_registry.register(a1)
    sql_explanation_registry.register(a2)
    sql_explanation_registry.register(b)
    results = sql_explanation_registry.list_for_analysis("t-sql", "sql-ana-1")
    assert len(results) == 2


def test_sql_tenant_isolation(sql_explanation_registry):
    """Explicações de outro tenant NÃO aparecem em list_for_analysis."""
    e1 = _explanation(analysis_id="iso-1", tenant_id="tenant-A")
    e2 = _explanation(analysis_id="iso-1", tenant_id="tenant-B")
    sql_explanation_registry.register(e1)
    sql_explanation_registry.register(e2)
    results_a = sql_explanation_registry.list_for_analysis("tenant-A", "iso-1")
    results_b = sql_explanation_registry.list_for_analysis("tenant-B", "iso-1")
    assert len(results_a) == 1
    assert len(results_b) == 1
    assert results_a[0].tenant_id == "tenant-A"
    assert results_b[0].tenant_id == "tenant-B"


def test_sql_list_for_event(sql_explanation_registry):
    e1 = _explanation(contributing=["sql-ev-1"], tenant_id="t-sql")
    e2 = _explanation(contributing=["sql-ev-2"], tenant_id="t-sql")
    sql_explanation_registry.register(e1)
    sql_explanation_registry.register(e2)
    found = sql_explanation_registry.list_for_event("t-sql", "sql-ev-1")
    assert len(found) == 1
    assert found[0].explanation_id == e1.explanation_id


def test_sql_list_for_type(sql_explanation_registry):
    e1 = _explanation(analysis_type=AnalysisType.TREND, tenant_id="t-sql")
    e2 = _explanation(analysis_type=AnalysisType.CORRELATION, tenant_id="t-sql")
    sql_explanation_registry.register(e1)
    sql_explanation_registry.register(e2)
    trends = sql_explanation_registry.list_for_type("t-sql", AnalysisType.TREND)
    assert len(trends) == 1
    corrs = sql_explanation_registry.list_for_type("t-sql", AnalysisType.CORRELATION)
    assert len(corrs) == 1


def test_sql_count(sql_explanation_registry):
    assert sql_explanation_registry.count("t-sql") == 0
    sql_explanation_registry.register(_explanation(tenant_id="t-sql"))
    sql_explanation_registry.register(_explanation(tenant_id="t-sql"))
    sql_explanation_registry.register(_explanation(tenant_id="other"))
    assert sql_explanation_registry.count("t-sql") == 2
    assert sql_explanation_registry.count("other") == 1