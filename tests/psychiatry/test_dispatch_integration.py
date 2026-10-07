"""Testes de integração do dispatch de convites (rotas)."""

from __future__ import annotations

import services.telegram_service as telegram_module
import services.whatsapp_gateway as gateway_module
from routes.psychiatry import _dispatch


class _FakeEmail:
    last = None

    def send_email(self, to_email, subject, html_body, text_body=None):
        _FakeEmail.last = {"to": to_email, "subject": subject, "html": html_body}
        return True


class _FakeGateway:
    def __init__(self, provider="evolution", template_name=None):
        self.resolved_provider = provider
        self.template_name = template_name
        self.text_calls = []
        self.template_calls = []

    def send_text(self, to, text):
        self.text_calls.append((to, text))
        return True

    def send_template(self, to, **kwargs):
        self.template_calls.append((to, kwargs))
        return True


class _FakeTelegram:
    def __init__(self):
        self.calls = []

    def send_message(self, chat_id, text, parse_mode="HTML"):
        self.calls.append((chat_id, text))
        return True


def test_dispatch_email(monkeypatch):
    monkeypatch.setattr("services.email_service.EmailService", _FakeEmail)
    ok, detail = _dispatch("email", "p@x.com", "https://link?token=1", "1")
    assert ok is True
    assert detail == "email"
    assert _FakeEmail.last["to"] == "p@x.com"
    assert "token=1" in _FakeEmail.last["html"]


def test_dispatch_whatsapp_text(monkeypatch):
    fake = _FakeGateway(provider="evolution")
    monkeypatch.setattr(gateway_module, "default_gateway", lambda: fake)
    ok, detail = _dispatch("whatsapp", "5579999999999", "https://link?token=2", "2")
    assert ok is True
    assert detail == "whatsapp"
    assert fake.text_calls and "token=2" in fake.text_calls[0][1]
    assert fake.template_calls == []


def test_dispatch_whatsapp_template_meta(monkeypatch):
    fake = _FakeGateway(provider="meta", template_name="triagem")
    monkeypatch.setattr(gateway_module, "default_gateway", lambda: fake)
    ok, _ = _dispatch("whatsapp", "5579999999999", "https://link?token=3", "3")
    assert ok is True
    assert fake.template_calls and fake.template_calls[0][1]["body_variables"] == ["https://link?token=3"]
    assert fake.text_calls == []


def test_dispatch_telegram(monkeypatch):
    fake = _FakeTelegram()
    monkeypatch.setattr(telegram_module, "telegram_service", fake)
    ok, detail = _dispatch("telegram", "12345", "https://link?token=4", "4")
    assert ok is True
    assert detail == "telegram"
    assert fake.calls and "token=4" in fake.calls[0][1]
