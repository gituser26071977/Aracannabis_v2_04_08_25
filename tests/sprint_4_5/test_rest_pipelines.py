"""RC1 Gate 2 — POST /pipelines/run tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def seeded_genes_alfa(app, scenario_alfa):
    """Persist scenario_alfa's genes into the shared InMemory repo
    that the request handler uses."""
    repo = app._get_repo("tenant_alfa")
    repo.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
    return {"patient_id": scenario_alfa.patient_id, "tenant_id": "tenant_alfa"}


def test_run_pipeline_happy_path(client, auth_headers_alfa, scenario_alfa, seeded_genes_alfa):
    """POST /pipelines/run computes & persists genome + returns full data."""
    body = {
        "patient_id": scenario_alfa.patient_id,
        "window_start": "2026-01-01T00:00:00+00:00",
        "window_end": "2026-06-01T00:00:00+00:00",
        "window_label": "6_months",
        "methods": [],
        "include_graph": True,
    }
    resp = client.post(
        "/api/v1/knowledge/pipelines/run",
        json=body,
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    envelope = resp.get_json()
    assert envelope["success"] is True
    assert "genome" in envelope["data"]
    assert envelope["data"]["genome"]["patient_id"] == scenario_alfa.patient_id
    assert envelope["data"]["genome"]["tenant_id"] == "tenant_alfa"
    assert envelope["data"]["genome"]["gene_count"] >= 1
    assert "started_at" in envelope["data"]
    assert "completed_at" in envelope["data"]
    assert "duration_seconds" in envelope["data"]


def REDACTED(client, auth_headers_alfa, scenario_alfa, seeded_genes_alfa):
    """Standard envelope keys are all present."""
    body = {
        "patient_id": scenario_alfa.patient_id,
        "window_start": "2026-01-01T00:00:00+00:00",
        "window_end": "2026-06-01T00:00:00+00:00",
    }
    resp = client.post(
        "/api/v1/knowledge/pipelines/run",
        json=body,
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 201, resp.get_data(as_text=True)
    env = resp.get_json()
    assert set(env.keys()) >= {"success", "data", "error", "meta"}
    assert set(env["meta"].keys()) >= {"timestamp", "request_id", "latency_ms"}
    assert env["error"] is None


def REDACTED(client, auth_headers_alfa):
    """window_end <= window_start triggers VALIDATION_ERROR."""
    body = {
        "patient_id": "patient_a1",
        "window_start": "2026-06-01T00:00:00+00:00",
        "window_end": "2026-01-01T00:00:00+00:00",
    }
    resp = client.post(
        "/api/v1/knowledge/pipelines/run",
        json=body,
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 400
    env = resp.get_json()
    assert env["success"] is False
    assert env["error"]["code"] == "VALIDATION_ERROR"
    assert "window_end" in env["error"]["message"]


def REDACTED(client):
    """No Authorization header → 401 AUTH_REQUIRED."""
    body = {
        "patient_id": "patient_a1",
        "window_start": "2026-01-01T00:00:00+00:00",
        "window_end": "2026-06-01T00:00:00+00:00",
    }
    resp = client.post("/api/v1/knowledge/pipelines/run", json=body)
    assert resp.status_code == 401


def REDACTED(client, auth_headers_alfa):
    """patient_id is required."""
    body = {
        "window_start": "2026-01-01T00:00:00+00:00",
        "window_end": "2026-06-01T00:00:00+00:00",
    }
    resp = client.post(
        "/api/v1/knowledge/pipelines/run",
        json=body,
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 400
    env = resp.get_json()
    assert env["error"]["code"] == "VALIDATION_ERROR"
    assert "patient_id" in env["error"]["message"]


def REDACTED(client, auth_headers_alfa):
    """Patient with no genes in this tenant returns 400 INVALID_REQUEST (not 404 — we
    are 'no input data', not 'no resource')."""
    body = {
        "patient_id": "patient_does_not_exist",
        "window_start": "2026-01-01T00:00:00+00:00",
        "window_end": "2026-06-01T00:00:00+00:00",
    }
    resp = client.post(
        "/api/v1/knowledge/pipelines/run",
        json=body,
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"]["code"] == "INVALID_REQUEST"
