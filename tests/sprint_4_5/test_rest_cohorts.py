"""RC1 Gate 2 — GET /cohorts endpoints tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def cohort_alfa(app):
    """Persist one cohort under tenant_alfa for read tests (shared repo)."""
    from datetime import datetime, timezone
    from araos.clinical.knowledge.domain.cohort import Cohort

    co = Cohort(
        cohort_id="cohort_a1_test",
        tenant_id="tenant_alfa",
        name="Sleepers > 5y",
        criteria=(),
        matched_patient_ids=("patient_a1",),
        built_at=datetime.now(timezone.utc),
        state_hash="",
    )
    repo = app._get_repo("tenant_alfa")
    repo.save_cohort(co)
    return {"cohort_id": co.cohort_id, "tenant_id": co.tenant_id}


def test_list_cohorts(client, auth_headers_alfa, cohort_alfa):
    resp = client.get(
        "/api/v1/knowledge/cohorts",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    items = body["data"]["items"]
    assert any(c["cohort_id"] == "cohort_a1_test" for c in items)
    assert all(c["tenant_id"] == "tenant_alfa" for c in items)


def test_get_cohort_200(client, auth_headers_alfa, cohort_alfa):
    resp = client.get(
        "/api/v1/knowledge/cohorts/cohort_a1_test",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["cohort_id"] == "cohort_a1_test"
    assert data["tenant_id"] == "tenant_alfa"
    assert data["name"] == "Sleepers > 5y"
    assert data["count"] == 1
    assert "matched_patient_ids" in data
    assert "criteria" in data


def test_get_cohort_404(client, auth_headers_alfa):
    resp = client.get(
        "/api/v1/knowledge/cohorts/cohort_does_not_exist",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "COHORT_NOT_FOUND"


def REDACTED(client, auth_headers_beta, cohort_alfa):
    """Cross-tenant cohort lookup returns 404."""
    resp = client.get(
        "/api/v1/knowledge/cohorts/cohort_a1_test",
        headers=auth_headers_beta,
    )
    assert resp.status_code == 404
