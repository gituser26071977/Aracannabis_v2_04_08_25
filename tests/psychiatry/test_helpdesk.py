"""Testes do helpdesk de entrada do WhatsApp."""

from __future__ import annotations

from types import SimpleNamespace

from services.psych_triage_helpdesk import (
    handle_inbound,
    parse_inbound,
)


def test_parse_evolution():
    payload = {
        "instance": "siap",
        "data": {
            "key": {"remoteJid": "5579999999999@s.whatsapp.net", "fromMe": False},
            "message": {"conversation": "oi"},
        },
    }
    parsed = parse_inbound(payload, provider="evolution")
    assert parsed["phone"] == "5579999999999"
    assert parsed["text"] == "oi"
    assert parsed["channel"] == "evolution"


def test_parse_meta():
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "123"},
                            "messages": [{"from": "5579888888888", "type": "text", "text": {"body": "quero o teste"}}],
                        }
                    }
                ]
            }
        ]
    }
    parsed = parse_inbound(payload, provider="meta")
    assert parsed["phone"] == "5579888888888"
    assert parsed["text"] == "quero o teste"
    assert parsed["channel"] == "meta"


def test_handle_inbound_known_patient():
    sent = []

    def sender(phone, text):
        sent.append((phone, text))
        return True

    def finder(phone, tenant_id):
        return SimpleNamespace(id=42)

    payload = {
        "data": {
            "key": {"remoteJid": "5579999999999@s.whatsapp.net", "fromMe": False},
            "message": {"conversation": "oi"},
        }
    }
    result = handle_inbound(payload, "tenant-1", sender=sender, finder=finder)
    assert result["ok"] is True
    assert result["patient_id"] == 42
    assert "token=" in result["link"]
    assert sent and "token=" in sent[0][1]


def test_handle_inbound_unknown_patient_replies_generic():
    sent = []

    def sender(phone, text):
        sent.append(text)
        return True

    def finder(phone, tenant_id):
        return None

    payload = {
        "data": {
            "key": {"remoteJid": "5579999999999@s.whatsapp.net", "fromMe": False},
            "message": {"conversation": "oi"},
        }
    }
    result = handle_inbound(payload, "tenant-1", sender=sender, finder=finder)
    assert result["ok"] is False
    assert result["reason"] == "not_found"
    assert sent and "não localizamos" in sent[0].lower()


def test_handle_inbound_ignores_from_me():
    payload = {
        "data": {
            "key": {"remoteJid": "5579999999999@s.whatsapp.net", "fromMe": True},
            "message": {"conversation": "oi"},
        }
    }
    result = handle_inbound(payload, "tenant-1")
    assert result["ok"] is False
    assert result["reason"] == "ignored"


def test_webhook_route(client, monkeypatch):
    import services.psych_triage_helpdesk as helpdesk

    monkeypatch.setattr(helpdesk, "handle_inbound", lambda payload, tenant_id, provider=None: {"ok": True})
    resp = client.post(
        "/api/public/psych-triage/webhook?tenant_id=t1",
        json={"data": {"key": {"remoteJid": "5579999999999@s.whatsapp.net"}}},
    )
    assert resp.status_code == 200
    assert resp.get_json()["handled"] is True
