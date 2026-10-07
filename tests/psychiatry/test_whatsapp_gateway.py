"""Testes do gateway de WhatsApp (providers meta e evolution)."""

from __future__ import annotations

from services.whatsapp_gateway import WhatsAppGateway, normalize_phone


class _Response:
    def __init__(self, status_code: int, text: str = "{}") -> None:
        self.status_code = status_code
        self.text = text


class _FakeSession:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return _Response(self.status_code)


def test_normalize_phone():
    assert normalize_phone("(79) 99999-9999") == "5579999999999"
    assert normalize_phone("+55 79 99999-9999") == "5579999999999"
    assert normalize_phone("") == ""


def test_meta_send_text():
    session = _FakeSession()
    gw = WhatsAppGateway(
        provider="meta", session=session, phone_number_id="123", access_token="tok"
    )
    assert gw.is_configured() is True
    assert gw.resolved_provider == "meta"
    assert gw.send_text("79999999999", "Olá") is True
    call = session.calls[0]
    assert "graph.facebook.com" in call["url"]
    assert call["headers"]["Authorization"] == "Bearer tok"
    assert call["json"]["type"] == "text"
    assert call["json"]["to"] == "5579999999999"


def test_meta_send_template():
    session = _FakeSession()
    gw = WhatsAppGateway(
        provider="meta", session=session, phone_number_id="1", access_token="t",
        template_name="triagem", template_lang="pt_BR",
    )
    assert gw.send_template("7999999999", body_variables=["https://x/y"], url_button_suffix="tok") is True
    payload = session.calls[0]["json"]
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "triagem"
    assert payload["template"]["components"]


def test_evolution_send_text():
    session = _FakeSession(status_code=201)
    gw = WhatsAppGateway(
        provider="evolution", session=session, evolution_url="http://evo:8080",
        evolution_instance="siap", evolution_key="key",
    )
    assert gw.resolved_provider == "evolution"
    assert gw.send_text("7999999999", "Oi") is True
    assert "message/sendText/siap" in session.calls[0]["url"]
    assert session.calls[0]["headers"]["apikey"] == "key"


def test_not_configured_returns_false():
    gw = WhatsAppGateway(provider="auto", phone_number_id=None, access_token=None,
                         evolution_url="", evolution_key=None)
    assert gw.is_configured() is False
    assert gw.send_text("7999999999", "Oi") is False


def test_failure_status_returns_false():
    session = _FakeSession(status_code=401)
    gw = WhatsAppGateway(provider="meta", session=session, phone_number_id="1", access_token="bad")
    assert gw.send_text("7999999999", "Oi") is False
