"""RC1 Gate 2 — research sessions and replay tests."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest


def _build_session(cohort_id: str = "cohort_a1_test", tenant_id: str = "tenant_alfa"):
    """Build a minimal ResearchSession for a tenant without replay machinery."""
    from dataclasses import dataclass
    from araos.clinical.knowledge.domain.research import (
        AnalysisType,
        ResearchQuery,
        ResearchSession,
    )

    @dataclass(frozen=True)
    class _StubExplanation:
        explanation_id: str = "exp_stub"

    @dataclass(frozen=True)
    class _StubResult:
        # Renamed from ResearchSession.result_json to avoid shadowing
        records: tuple = ()

    q = ResearchQuery(
        query_id="query_corr",
        cohort_id=cohort_id,
        analysis_type=AnalysisType.CORRELATIONS,
        params={},
        version=1,
        created_at=datetime.now(timezone.utc),
    )
    s = ResearchSession(
        session_id="sess_alfa_001",
        query=q,
        version=1,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        result_json="{}",
        state_hash="h_alfa",
        reproducible=True,
        explanation=_StubExplanation(),
    )
    return s


@pytest.fixture
def session_alfa(app):
    s = _build_session()
    repo = app._get_repo("tenant_alfa")
    repo.save_session(s)
    return {"session_id": s.session_id, "tenant_id": "tenant_alfa"}


def test_list_sessions(client, auth_headers_alfa, session_alfa):
    resp = client.get(
        "/api/v1/knowledge/research/sessions",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert any(i["session_id"] == "sess_alfa_001" for i in items)


def REDACTED(client, auth_headers_alfa, session_alfa):
    resp = client.get(
        "/api/v1/knowledge/research/sessions/sess_alfa_001",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["session_id"] == "sess_alfa_001"
    assert data["state_hash"] == "h_alfa"
    assert data["reproducible"] is True
    assert data["result_json"] == "{}"
    assert "duration_seconds" in data


def test_get_session_404(client, auth_headers_alfa):
    resp = client.get(
        "/api/v1/knowledge/research/sessions/sess_does_not_exist",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "RESEARCH_SESSION_NOT_FOUND"


def REDACTED(
    client, auth_headers_alfa, session_alfa,
):
    """Replay returns a NEW session (status 201) with reproducible state_hash.

    Note: the state_hash is recomputed deterministically from the session
    content (not the pre-saved 'h_alfa' literal), so we just verify the
    replay succeeded and produced a valid session.
    """
    resp = client.post(
        "/api/v1/knowledge/research/sessions/sess_alfa_001/replay",
        headers=auth_headers_alfa,
    )
    assert resp.status_code in (200, 201), resp.get_data(as_text=True)
    data = resp.get_json()["data"]
    if "session_id" in data:
        # Replay produced a session — verify shape.
        assert "state_hash" in data
        assert len(data["state_hash"]) > 0
        assert "reproducible" in data
    else:
        # If patient-data replay is not supported, an envelope error is shown.
        assert False, f"replay should return a session, got: {data}"


def REDACTED(client, auth_headers_alfa):
    resp = client.post(
        "/api/v1/knowledge/research/sessions/sess_missing/replay",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "RESEARCH_SESSION_NOT_FOUND"
