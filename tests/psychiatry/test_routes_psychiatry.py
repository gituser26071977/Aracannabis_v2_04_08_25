"""Testes de rota do módulo de triagem psiquiátrica."""

from __future__ import annotations

DEPRESSION = {
    "items": {
        "dep_humor": {"intensity": 4, "temporal": "ultimos_30_dias", "change": "claramente"},
        "dep_anedonia": {"intensity": 4, "temporal": "ultimos_30_dias", "change": "claramente"},
        "dep_desesperanca": {"intensity": 3, "temporal": "ultimos_30_dias", "change": "moderadamente"},
    }
}

EMERGENCY = {
    "items": {},
    "suicide": {
        "ideacao_suicida": True,
        "plano": True,
        "acesso_meio": True,
        "intencao": True,
        "preparacao": True,
        "agitacao": True,
        "capacidade_seguranca": False,
    },
}


def test_meta(client, auth_header):
    resp = client.get("/api/psychiatry/triage/meta", headers=auth_header)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["code"] == "PSYCH_TRIAGE"
    assert "não substitui" in body["disclaimer"]


def test_catalog_and_instrument(client, auth_header):
    assert client.get("/api/psychiatry/triage/catalog", headers=auth_header).status_code == 200
    resp = client.get("/api/psychiatry/triage/instrument", headers=auth_header)
    assert resp.status_code == 200
    assert len(resp.get_json()["items"]) > 50


def test_apply_persist_and_explain(client, auth_header):
    resp = client.post(
        "/api/psychiatry/triage/apply",
        headers=auth_header,
        json={"patient_id": "p1", "raw_responses": DEPRESSION},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["domain_scores"]["depressao"] >= 34
    assert "não substitui" in body["disclaimer"]
    assert "tem transtorno" not in body["narrative"].lower()
    response_id = body["id"]

    got = client.get(f"/api/psychiatry/triage/responses/{response_id}", headers=auth_header)
    assert got.status_code == 200

    explained = client.get(
        f"/api/psychiatry/triage/responses/{response_id}/explain", headers=auth_header
    )
    assert explained.status_code == 200
    assert "increased" in explained.get_json()["explainability"]["depressao"]

    listed = client.get(
        "/api/psychiatry/triage/responses?patient_id=p1", headers=auth_header
    )
    assert listed.status_code == 200
    assert listed.get_json()["total"] == 1

    longitudinal = client.get(
        "/api/psychiatry/triage/longitudinal?patient_id=p1", headers=auth_header
    )
    assert longitudinal.status_code == 200
    assert longitudinal.get_json()["total"] == 1


def test_apply_emergency_flag(client, auth_header):
    resp = client.post(
        "/api/psychiatry/triage/apply",
        headers=auth_header,
        json={"patient_id": "p2", "raw_responses": EMERGENCY},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["risk"]["emergency"] is True
    assert body["risk"]["level"] == "iminente"


def test_apply_requires_tenant(client):
    from flask_jwt_extended import create_access_token

    token = create_access_token(identity={"user_id": "actor"})
    resp = client.post(
        "/api/psychiatry/triage/apply",
        headers={"Authorization": f"Bearer {token}"},
        json={"patient_id": "p1", "raw_responses": DEPRESSION},
    )
    assert resp.status_code == 400


def test_invite_generates_link(client, auth_header):
    resp = client.post(
        "/api/psychiatry/triage/invite",
        headers=auth_header,
        json={"patient_id": "p1", "channel": "link"},
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert "token=" in body["link"]
    assert body["sent"] is False

    from services.psych_triage_invite import verify_invite_token

    data = verify_invite_token(body["token"])
    assert data["tenant_id"] == "tenant-1"
    assert data["patient_id"] == "p1"
