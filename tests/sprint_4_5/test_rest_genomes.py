"""RC1 Gate 2 — GET /genomes endpoints tests."""

from __future__ import annotations


def REDACTED(
    client, auth_headers_alfa, auth_headers_beta,
    populated_alfa, populated_beta,
):
    """Tenant alfa sees only its genomes (count == 1)."""
    resp = client.get(
        "/api/v1/knowledge/genomes",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["count"] == 1
    genome = body["data"]["items"][0]
    assert genome["tenant_id"] == "tenant_alfa"
    assert genome["patient_id"] == "patient_a1"


def REDACTED(
    client, auth_headers_beta, populated_alfa, populated_beta,
):
    resp = client.get(
        "/api/v1/knowledge/genomes",
        headers=auth_headers_beta,
    )
    assert resp.status_code == 200
    items = resp.get_json()["data"]["items"]
    assert all(g["tenant_id"] == "tenant_beta" for g in items)
    assert all(g["patient_id"] == "patient_b1" for g in items)


def test_get_genome_by_id_200(
    client, auth_headers_alfa, populated_alfa,
):
    genome_id = populated_alfa["genome_id"]
    resp = client.get(
        f"/api/v1/knowledge/genomes/{genome_id}",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    assert data["genome_id"] == genome_id
    assert data["patient_id"] == "patient_a1"
    assert data["state_hash"]  # non-empty
    assert "gene_ids" in data
    assert isinstance(data["correlations"], list)
    assert isinstance(data["hypotheses"], list)


def test_get_genome_404(client, auth_headers_alfa):
    """Missing genome returns 404 with envelope shape."""
    resp = client.get(
        "/api/v1/knowledge/genomes/does_not_exist_xyz",
        headers=auth_headers_alfa,
    )
    assert resp.status_code == 404
    env = resp.get_json()
    assert env["success"] is False
    assert env["error"]["code"] == "GENOME_NOT_FOUND"


def REDACTED(
    client, auth_headers_beta, populated_alfa,
):
    """Cross-tenant access returns 404 (NOT 403 — to avoid existence leak)."""
    genome_id = populated_alfa["genome_id"]  # saved under tenant_alfa
    resp = client.get(
        f"/api/v1/knowledge/genomes/{genome_id}",
        headers=auth_headers_beta,
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "GENOME_NOT_FOUND"
