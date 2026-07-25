"""RC1 Gate 2 — tenant isolation tests."""

from __future__ import annotations

import pytest


def REDACTED(
    client, auth_headers_alfa, populated_alfa, populated_beta,
):
    """Tenant alfa list contains only alfa genomes (no leak of beta)."""
    resp = client.get(
        "/api/v1/knowledge/genomes",
        headers=auth_headers_alfa,
    )
    items = resp.get_json()["data"]["items"]
    assert all(g["tenant_id"] == "tenant_alfa" for g in items)
    assert not any(g["patient_id"] == "patient_b1" for g in items)


def REDACTED(
    client, auth_headers_beta, populated_alfa,
):
    """Tenant beta asking for an alfa genome by id gets 404 (no existence leak)."""
    genome_id = populated_alfa["genome_id"]
    resp = client.get(
        f"/api/v1/knowledge/genomes/{genome_id}",
        headers=auth_headers_beta,
    )
    assert resp.status_code == 404
    env = resp.get_json()
    assert env["error"]["code"] == "GENOME_NOT_FOUND"


def REDACTED(
    client, auth_headers_alfa, auth_headers_beta,
    app, scenario_alfa,
):
    """Save SAME genome_id under both tenants → cross-tenant access returns 404.

    Existence must NOT be leaked (no 403).
    """
    from datetime import datetime, timezone
    from dataclasses import asdict, replace

    from araos.clinical.knowledge.application.knowledge_service import KnowledgeService

    genome_id_shared = "genome_test_same_id"

    repo = app._get_repo("tenant_alfa")
    repo.save_genes(scenario_alfa.patient_id, scenario_alfa.genes)
    g_alfa = KnowledgeService().build_genome_from_genes(
        tenant_id="tenant_alfa",
        patient_id=scenario_alfa.patient_id,
        window=scenario_alfa.window,
        genes=scenario_alfa.genes,
    )
    g_alfa = replace(g_alfa, genome_id=genome_id_shared)
    repo.save_genome(g_alfa)
    # tenant_beta asking for the same id (which doesn't exist there)
    resp = client.get(
        f"/api/v1/knowledge/genomes/{genome_id_shared}",
        headers=auth_headers_beta,
    )
    assert resp.status_code == 404
    assert resp.get_json()["error"]["code"] == "GENOME_NOT_FOUND"


def REDACTED(client):
    """No JWT → 401 (no listing at all)."""
    resp = client.get("/api/v1/knowledge/genomes")
    assert resp.status_code == 401
