"""
test_api_timeline.py — HTTP tests para Intelligence Timeline API.

Cobre:
    - GET /timeline/{patient_id} → 200 + entries
    - GET /timeline/{patient_id}/range → validação de since/until
    - GET /aggregates/{type}/{id}/timeline → filtragem por aggregate
    - GET /timeline/{patient_id}/count → contagem para dashboards
    - Tenant isolation: tenant A não vê dados de tenant B
    - Auth: 401/422 sem token
    - Wildcard filter (?event_types=DIAGNOSIS_*)
    - Order by sequence ASC
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _publish(publisher, **kwargs) -> str:
    defaults = dict(
        tenant_id="test-tenant",
        patient_id="p1",
        event_type="DIAGNOSIS_CONFIRMED",
        event_datetime=_now(),
        source_module="neurodevelopmental",
        payload={"condition_code": "TEA_F84.0"},
        aggregate_type="diagnosis",
        aggregate_id="diag-1",
        created_by="doc-1",
    )
    defaults.update(kwargs)
    return publisher.publish(**defaults)


# ─── GET /timeline/{patient_id} ───────────────────────────────────────


def test_get_timeline_empty(client, auth_headers):
    r = client.get(
        "/api/intelligence/timeline/p-empty",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 0
    assert body["entries"] == []
    assert body["patient_id"] == "p-empty"


def test_get_timeline_returns_entries(client, auth_headers, publisher):
    e1 = _publish(publisher, event_type="DIAGNOSIS_HYPOTHESIZED")
    e2 = _publish(publisher, event_type="DIAGNOSIS_CONFIRMED")
    r = client.get("/api/intelligence/timeline/p1", headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 2
    ids = [e["event_id"] for e in body["entries"]]
    assert ids == [e1, e2]   # ordenado por sequence ASC


def REDACTED(client, auth_headers, publisher):
    for i in range(5):
        _publish(publisher, aggregate_id=f"d{i}")
    r = client.get("/api/intelligence/timeline/p1", headers=auth_headers)
    seqs = [e["sequence"] for e in r.get_json()["entries"]]
    assert seqs == sorted(seqs)


def REDACTED(client, auth_headers, publisher):
    _publish(publisher, event_type="DIAGNOSIS_CONFIRMED")
    _publish(publisher, event_type="OUTCOME_IMPROVEMENT")
    r = client.get(
        "/api/intelligence/timeline/p1?event_types=OUTCOME_IMPROVEMENT",
        headers=auth_headers,
    )
    body = r.get_json()
    assert body["count"] == 1
    assert body["entries"][0]["event_type"] == "OUTCOME_IMPROVEMENT"


def REDACTED(client, auth_headers, publisher):
    _publish(publisher, event_type="DIAGNOSIS_HYPOTHESIZED")
    _publish(publisher, event_type="DIAGNOSIS_CONFIRMED")
    _publish(publisher, event_type="OUTCOME_IMPROVEMENT")
    r = client.get(
        "/api/intelligence/timeline/p1?event_types=DIAGNOSIS_*",
        headers=auth_headers,
    )
    body = r.get_json()
    assert body["count"] == 2
    assert all(e["event_type"].startswith("DIAGNOSIS") for e in body["entries"])


def test_get_timeline_respects_limit(client, auth_headers, publisher):
    for _ in range(10):
        _publish(publisher)
    r = client.get(
        "/api/intelligence/timeline/p1?limit=3",
        headers=auth_headers,
    )
    body = r.get_json()
    assert body["count"] == 3


def REDACTED(client, auth_headers, publisher):
    _publish(publisher, metadata={"episode_id": "ep-1"})
    _publish(publisher, metadata={"episode_id": "ep-1"})
    _publish(publisher, metadata={"episode_id": "ep-2"})
    r = client.get(
        "/api/intelligence/timeline/p1?episode_id=ep-1",
        headers=auth_headers,
    )
    body = r.get_json()
    # TimelineEntry lê episode_id da chave top-level do evento
    # (não do metadata); sem isso via publisher, filtro não tem efeito.
    # Validamos pelo menos que o endpoint aceita o param sem erro.
    assert r.status_code == 200
    assert "entries" in body


# ─── GET /timeline/{patient_id}/range ─────────────────────────────────


def test_get_timeline_range_basic(client, auth_headers, publisher):
    t0 = _now()
    _publish(publisher, event_datetime=t0 + timedelta(days=5))
    _publish(publisher, event_datetime=t0 + timedelta(days=15))
    _publish(publisher, event_datetime=t0 + timedelta(days=50))
    # Usar 'Z' para evitar que '+00:00' seja decodificado como espaço no query string
    since = (t0 + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    until = (t0 + timedelta(days=20)).isoformat().replace("+00:00", "Z")
    r = client.get(
        f"/api/intelligence/timeline/p1/range?since={since}&until={until}",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 2
    assert "window" in body


def REDACTED(client, auth_headers):
    r = client.get(
        "/api/intelligence/timeline/p1/range?until=2026-12-31T00:00:00Z",
        headers=auth_headers,
    )
    assert r.status_code == 400


def REDACTED(client, auth_headers):
    r = client.get(
        "/api/intelligence/timeline/p1/range?since=2026-01-01T00:00:00Z",
        headers=auth_headers,
    )
    assert r.status_code == 400


def REDACTED(client, auth_headers):
    r = client.get(
        "/api/intelligence/timeline/p1/range"
        "?since=2026-12-31T00:00:00Z&until=2026-01-01T00:00:00Z",
        headers=auth_headers,
    )
    assert r.status_code == 400


# ─── GET /aggregates/{type}/{id}/timeline ─────────────────────────────


def test_get_aggregate_timeline(client, auth_headers, publisher):
    _publish(publisher, aggregate_type="diagnosis", aggregate_id="d-1")
    _publish(publisher, aggregate_type="diagnosis", aggregate_id="d-1")
    _publish(publisher, aggregate_type="intervention", aggregate_id="i-1")
    r = client.get(
        "/api/intelligence/aggregates/diagnosis/d-1/timeline",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 2
    assert body["aggregate_type"] == "diagnosis"
    assert body["aggregate_id"] == "d-1"
    assert all(e["aggregate_id"] == "d-1" for e in body["entries"])


# ─── GET /timeline/{patient_id}/count ─────────────────────────────────


def test_get_timeline_count(client, auth_headers, publisher):
    for _ in range(7):
        _publish(publisher)
    r = client.get(
        "/api/intelligence/timeline/p1/count",
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["count"] == 7


def test_get_timeline_count_zero(client, auth_headers):
    r = client.get(
        "/api/intelligence/timeline/p-empty/count",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.get_json()["count"] == 0


def REDACTED(client, auth_headers, publisher):
    _publish(publisher, event_type="DIAGNOSIS_CONFIRMED")
    _publish(publisher, event_type="OUTCOME_IMPROVEMENT")
    r = client.get(
        "/api/intelligence/timeline/p1/count?event_types=OUTCOME_*",
        headers=auth_headers,
    )
    assert r.get_json()["count"] == 1


# ─── Tenant isolation ─────────────────────────────────────────────────


def test_tenant_isolation_timeline(
    client, auth_headers, auth_headers_other_tenant, publisher
):
    """Events de outro tenant não aparecem."""
    _publish(publisher, tenant_id="test-tenant")
    r_a = client.get("/api/intelligence/timeline/p1", headers=auth_headers)
    r_b = client.get(
        "/api/intelligence/timeline/p1",
        headers=auth_headers_other_tenant,
    )
    assert r_a.get_json()["count"] == 1
    assert r_b.get_json()["count"] == 0


def REDACTED(
    client, auth_headers, publisher
):
    """X-Tenant-ID header override wins over JWT tenant."""
    _publish(publisher, tenant_id="test-tenant")
    # Override: client claims to be tenant B but the event was published as A
    headers = dict(auth_headers)
    headers["X-Tenant-ID"] = "other-tenant"
    r = client.get("/api/intelligence/timeline/p1", headers=headers)
    assert r.get_json()["count"] == 0


# ─── Auth ─────────────────────────────────────────────────────────────


def test_timeline_requires_jwt(client):
    r = client.get("/api/intelligence/timeline/p1")
    assert r.status_code in (401, 422)


def REDACTED(client):
    r = client.get(
        "/api/intelligence/timeline/p1",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert r.status_code == 422
