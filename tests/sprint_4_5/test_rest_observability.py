"""RC1 Gate 2 — observability header propagation tests."""

from __future__ import annotations


def REDACTED(client):
    """Every health response carries an X-Request-ID header."""
    resp = client.get("/api/v1/knowledge/health")
    assert "X-Request-ID" in resp.headers
    assert len(resp.headers["X-Request-ID"]) == 36  # UUID length
    return None


def REDACTED(client):
    """Inbound X-Correlation-ID echoes back unchanged."""
    sentinel = "corr-abc-12345-xyz"
    resp = client.get(
        "/api/v1/knowledge/health",
        headers={"X-Correlation-ID": sentinel},
    )
    assert resp.headers["X-Correlation-ID"] == sentinel


def REDACTED(client):
    """Without X-Correlation-ID, server-generated request_id is used."""
    resp = client.get("/api/v1/knowledge/health")
    assert resp.headers["X-Correlation-ID"] == resp.headers["X-Request-ID"]


def REDACTED(client):
    """X-Latency-MS is present and parseable as a float."""
    resp = client.get("/api/v1/knowledge/health")
    assert "X-Latency-MS" in resp.headers
    latency = float(resp.headers["X-Latency-MS"])
    assert latency >= 0.0
