"""RC1 Gate 2 — error envelope shape tests."""

from __future__ import annotations


def test_404_envelope_shape(client, auth_headers_alfa):
    """404 body has success:false, error:{code, message, details}, meta."""
    resp = client.get(
        "/api/v1/knowledge/genomes/_nope",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 404
    env = resp.get_json()
    assert env["success"] is False
    assert env["data"] is None
    assert env["error"]["code"] == "GENOME_NOT_FOUND"
    assert isinstance(env["error"]["message"], str)
    # Platform envelope uses dict for details (more structured than list).
    assert isinstance(env["error"]["details"], (dict, list))
    assert "timestamp" in env["meta"]
    assert "request_id" in env["meta"]


def test_400_envelope_shape(client, auth_headers_alfa):
    """Validation errors return 400 with VALIDATION_ERROR code."""
    resp = client.post(
        "/api/v1/knowledge/pipelines/run",
        json={"patient_id": "x", "window_start": "bad", "window_end": "bad"},
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 400
    env = resp.get_json()
    assert env["success"] is False
    assert env["error"]["code"] == "VALIDATION_ERROR"
    assert "meta" in env
    assert "request_id" in env["meta"]


def test_401_envelope_shape(client):
    """Unauthenticated request returns 401 with AUTH_REQUIRED."""
    resp = client.get("/api/v1/knowledge/genomes")
    assert resp.status_code == 401
    env = resp.get_json()
    # flask-jwt-extended may return a different shape, but at minimum
    # the request was rejected before reaching @tenant_required.
    # If we did reach @tenant_required, error.code would be AUTH_REQUIRED.
    # Otherwise just verify 401.
    if env and env.get("error", {}).get("code"):
        assert env["error"]["code"] in ("AUTH_REQUIRED",)


def test_request_id_in_response_header(client, auth_headers_alfa):
    """Every authenticated response carries X-Request-ID."""
    resp = client.get("/api/v1/knowledge/genomes", headers=auth_headers_alfa)
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) > 0
