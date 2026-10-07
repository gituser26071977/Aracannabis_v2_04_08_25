"""Testes da rota pública conduzida pelo paciente."""

from __future__ import annotations

import pytest

from araos.specialties.psychiatry import load_config, parse_config
from services.psych_triage_agent import build_agent
from services.psych_triage_session import clear, get_state, set_state

AGENT = build_agent(parse_config(load_config("1.0.0")))


@pytest.fixture(autouse=True)
def _clean_sessions():
    clear()
    yield
    clear()


def _fill_answers(overrides=None):
    answers = {}
    while True:
        question = AGENT.next_question(answers)
        if question is None:
            break
        if question.kind == "yesno":
            value = "nao"
        elif question.kind == "intensity":
            value = 0
        else:
            value = question.choices[0]
        answers[question.id] = AGENT.normalize(question, str(value))
    if overrides:
        answers.update(overrides)
    return answers


def test_start_returns_greeting_and_question(client):
    resp = client.post("/api/public/psych-triage/start", json={"tenant_id": "t1"})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["session_id"]
    assert "triagem" in body["greeting"].lower()
    assert body["question"]["id"] == "gate_infancia"
    assert "não substitui" in body["disclaimer"]


def test_answer_accepts_and_hints(client):
    session_id = client.post("/api/public/psych-triage/start", json={"tenant_id": "t1"}).get_json()[
        "session_id"
    ]
    ok = client.post(
        f"/api/public/psych-triage/{session_id}/answer", json={"message": "não"}
    )
    assert ok.status_code == 200
    assert ok.get_json()["accepted"] is True

    bad = client.post(
        f"/api/public/psych-triage/{session_id}/answer", json={"message": "talvez quem sabe"}
    )
    assert bad.status_code == 200
    assert bad.get_json()["accepted"] is False
    assert "hint" in bad.get_json()


def test_finalize_persists_and_returns_risk(client):
    session_id = client.post(
        "/api/public/psych-triage/start", json={"tenant_id": "t1", "patient_id": "p1"}
    ).get_json()["session_id"]
    state = get_state(session_id)
    state["answers"] = _fill_answers()
    set_state(session_id, state)

    resp = client.post(
        f"/api/public/psych-triage/{session_id}/answer", json={"message": "ok"}
    )
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["done"] is True
    assert body["response_id"]
    assert "risk" in body
    assert "não substitui" in body["disclaimer"]


def test_finalize_flags_emergency(client):
    session_id = client.post(
        "/api/public/psych-triage/start", json={"tenant_id": "t1", "patient_id": "p2"}
    ).get_json()["session_id"]
    overrides = {
        "sui_ideacao_suicida": "sim",
        "sui_plano": "sim",
        "sui_acesso_meio": "sim",
        "sui_preparacao": "sim",
        "sui_agitacao": "sim",
        "sui_capacidade_seguranca": "nao",
    }
    state = get_state(session_id)
    state["answers"] = _fill_answers(overrides)
    set_state(session_id, state)

    body = client.post(f"/api/public/psych-triage/{session_id}/answer", json={"message": "ok"}).get_json()
    assert body["emergency"] is True
    assert "188" in body["closing"]


def test_start_with_valid_token(client):
    from services.psych_triage_invite import create_invite_token

    token = create_invite_token("tenant-9", patient_id="p9")
    resp = client.post("/api/public/psych-triage/start", json={"token": token})
    assert resp.status_code == 201
    assert resp.get_json()["question"]["id"] == "gate_infancia"


def test_start_with_invalid_token(client):
    resp = client.post("/api/public/psych-triage/start", json={"token": "garbage"})
    assert resp.status_code == 401
