"""
test_api_explainability.py — HTTP tests para Explainability API.

Cobre:
    - GET /explanations/{id} → 200 / 404
    - GET /explanations?analysis_id=... → lista por análise
    - GET /explanations?event_id=... → lista por evento
    - GET /explanations?analysis_type=... → lista por tipo
    - GET /explanations (sem filtro) → retorna count + hint
    - GET /explanations/{id}/verify → 200 valid / 422 invalid
    - Tenant isolation
    - Auth
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.explainability import AnalysisType, Explanation
from araos.clinical.explainability.registry import new_explanation_id
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
    )


def _explanation(
    tenant_id="test-tenant",
    analysis_id="ana-1",
    contributing=None,
    analysis_type=AnalysisType.TREND,
    limitations=None,
) -> Explanation:
    return Explanation(
        explanation_id=new_explanation_id(),
        analysis_id=analysis_id,
        analysis_type=analysis_type,
        question="Q?",
        answer="A.",
        confidence=0.85,
        method="linear_regression",
        data_window=_window(),
        variables=[_var()],
        contributing_event_ids=contributing or ["ev-1", "ev-2"],
        assumptions=["ass"],
        limitations=limitations or [
            "Correlação não implica causalidade",
        ],
        created_at=_now(),
        tenant_id=tenant_id,
    )


# ─── GET /explanations/{id} ───────────────────────────────────────────


def REDACTED(
    client, auth_headers, explanation_registry
):
    e = _explanation()
    explanation_registry.register(e)
    r = client.get(
        f"/api/intelligence/explanations/{e.explanation_id}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["explanation_id"] == e.explanation_id
    assert body["confidence"] == 0.85


def REDACTED(client, auth_headers):
    r = client.get(
        "/api/intelligence/explanations/nonexistent",
        headers=auth_headers,
    )
    assert r.status_code == 404


def REDACTED(
    client, auth_headers, explanation_registry
):
    """Mesmo explanation_id não pode ser lido por outro tenant."""
    e = _explanation(tenant_id="other-tenant")
    explanation_registry.register(e)
    r = client.get(
        f"/api/intelligence/explanations/{e.explanation_id}",
        headers=auth_headers,
    )
    assert r.status_code == 404


def test_get_explanation_requires_jwt(client):
    r = client.get("/api/intelligence/explanations/exp-1")
    assert r.status_code in (401, 422)


# ─── GET /explanations (listagem) ─────────────────────────────────────


def REDACTED(
    client, auth_headers, explanation_registry
):
    for _ in range(3):
        explanation_registry.register(_explanation())
    r = client.get(
        "/api/intelligence/explanations",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 3
    assert "hint" in body
    assert "explanations" not in body   # sem details sem filtro


def REDACTED(
    client, auth_headers, explanation_registry
):
    explanation_registry.register(_explanation(analysis_id="ana-1"))
    explanation_registry.register(_explanation(analysis_id="ana-1"))
    explanation_registry.register(_explanation(analysis_id="ana-2"))
    r = client.get(
        "/api/intelligence/explanations?analysis_id=ana-1",
        headers=auth_headers,
    )
    body = r.get_json()
    assert body["count"] == 2
    assert all(e["analysis_id"] == "ana-1" for e in body["explanations"])


def test_list_explanations_by_event_id(
    client, auth_headers, explanation_registry
):
    e1 = _explanation(contributing=["ev-A", "ev-B"])
    e2 = _explanation(contributing=["ev-B"])
    e3 = _explanation(contributing=["ev-C"])
    explanation_registry.register(e1)
    explanation_registry.register(e2)
    explanation_registry.register(e3)
    r = client.get(
        "/api/intelligence/explanations?event_id=ev-B",
        headers=auth_headers,
    )
    body = r.get_json()
    assert body["count"] == 2


def REDACTED(
    client, auth_headers, explanation_registry
):
    explanation_registry.register(_explanation(analysis_type=AnalysisType.TREND))
    explanation_registry.register(
        _explanation(analysis_type=AnalysisType.CORRELATION),
    )
    explanation_registry.register(_explanation(analysis_type=AnalysisType.TREND))
    r = client.get(
        "/api/intelligence/explanations?analysis_type=trend",
        headers=auth_headers,
    )
    body = r.get_json()
    assert body["count"] == 2
    assert all(e["analysis_type"] == "trend" for e in body["explanations"])


def REDACTED(
    client, auth_headers, explanation_registry
):
    r = client.get(
        "/api/intelligence/explanations?analysis_type=bogus",
        headers=auth_headers,
    )
    assert r.status_code == 400
    body = r.get_json()
    assert "valid_types" in body


def REDACTED(
    client, auth_headers, explanation_registry
):
    for _ in range(10):
        explanation_registry.register(
            _explanation(analysis_id="ana-bulk"),
        )
    r = client.get(
        "/api/intelligence/explanations?analysis_id=ana-bulk&limit=3",
        headers=auth_headers,
    )
    body = r.get_json()
    # `count` = total matching (sem limit); `explanations` = lista truncada
    assert body["count"] == 10
    assert len(body["explanations"]) == 3


def REDACTED(
    client, auth_headers, explanation_registry
):
    """Listagem é scoped por tenant (header JWT)."""
    explanation_registry.register(_explanation(tenant_id="test-tenant"))
    explanation_registry.register(_explanation(tenant_id="other-tenant"))
    r = client.get(
        "/api/intelligence/explanations?analysis_id=ana-1",
        headers=auth_headers,
    )
    body = r.get_json()
    assert body["count"] == 1
    assert body["explanations"][0]["tenant_id"] == "test-tenant"


# ─── GET /explanations/{id}/verify ────────────────────────────────────


def test_verify_explanation_valid(
    client, auth_headers, explanation_registry
):
    e = _explanation()
    explanation_registry.register(e)
    r = client.get(
        f"/api/intelligence/explanations/{e.explanation_id}/verify",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["valid"] is True
    assert body["violations"] == []


def REDACTED(client, auth_headers):
    r = client.get(
        "/api/intelligence/explanations/missing/verify",
        headers=auth_headers,
    )
    assert r.status_code == 404


def REDACTED(client):
    r = client.get("/api/intelligence/explanations/exp-1/verify")
    assert r.status_code in (401, 422)


# ─── Cross-cutting: registry empty ────────────────────────────────────


def test_list_with_empty_registry(client, auth_headers):
    r = client.get(
        "/api/intelligence/explanations",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.get_json()["count"] == 0
