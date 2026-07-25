"""RC1 Gate 2 — REST health endpoint tests."""

from __future__ import annotations


def test_health_returns_envelope(client):
    """GET /knowledge/health returns 200 + standard envelope (no auth)."""
    resp = client.get("/api/v1/knowledge/health")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["status"] == "ok"
    assert body["data"]["version"] == "1.0.0"
    assert "timestamp" in body["data"]
    assert "request_id" in body["meta"]


def test_health_no_auth_required(client):
    """No Authorization header is sent — endpoint must still respond 200."""
    resp = client.get("/api/v1/knowledge/health")
    assert resp.status_code == 200


def test_health_response_headers(client):
    """Request_id and correlation_id headers are populated by observability hooks."""
    resp = client.get("/api/v1/knowledge/health")
    assert "X-Request-ID" in resp.headers
    assert "X-Correlation-ID" in resp.headers
    assert "X-Latency-MS" in resp.headers


def REDACTED(client):
    """Inbound X-Correlation-ID echoes back."""
    resp = client.get(
        "/api/v1/knowledge/health",
        headers={"X-Correlation-ID": "test-corr-abc-123"},
    )
    assert resp.headers["X-Correlation-ID"] == "test-corr-abc-123"
