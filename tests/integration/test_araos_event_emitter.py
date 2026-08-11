"""Testes do emitter SIAP → AraOS (F2, wrap não-rewrite).

Cobre:
    - build_event: contrato canônico
    - emit desabilitado → não publica, retorna False
    - emit habilidado → publica com HMAC, retorna True
    - emit com falha de rede → nunca lança, retorna False
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading

import pytest
import requests

from services.araos_event_emitter import AraOSEventEmitter, build_event


def _sign(raw: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


class FakeResponse:
    def __init__(self, status: int = 200) -> None:
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class RecordingSession:
    """Sessão fake que captura o POST e valida assinatura."""

    def __init__(self, *, status: int = 200) -> None:
        self.status = status
        self.posted: list[tuple[str, dict, bytes]] = []
        self._lock = threading.Lock()

    def post(self, url: str, headers: dict, data: bytes, timeout: float) -> FakeResponse:
        with self._lock:
            self.posted.append((url, headers, data))
        return FakeResponse(self.status)


class TestBuildEvent:
    def test_contract_shape(self):
        ev = build_event(
            event_type="EVOLUTION_RECORDED",
            patient_id=42,
            tenant_id="vittalis",
            payload={"evolucao_id": 7, "nota_evolucao": "Evoluiu bem"},
            source_id=7,
        )
        assert ev["type"] == "EVOLUTION_RECORDED"
        assert ev["patient_id"] == "42"
        assert ev["tenant_id"] == "vittalis"
        assert ev["source"] == "siap"
        assert ev["source_id"] == 7
        assert "occurred_at" in ev
        assert "evidence" in ev and ev["evidence"] == []
        assert "gene_expressions" in ev and ev["gene_expressions"] == []
        assert ev["metadata"] == {}

    def test_metadata_and_payload_merged(self):
        ev = build_event(
            event_type="X",
            patient_id=1,
            tenant_id="t",
            payload={"campo": "valor"},
            metadata={"professional_id": "9"},
        )
        assert ev["campo"] == "valor"
        assert ev["metadata"] == {"professional_id": "9"}


class TestEmit:
    def test_disabled_returns_false(self):
        emitter = AraOSEventEmitter(enabled=False, webhook_url="http://x")
        assert emitter.emit(event_type="X", patient_id=1, tenant_id="t", payload={}) is False

    def test_enabled_publishes_signed(self):
        secret = "segredo-teste"
        session = RecordingSession()
        emitter = AraOSEventEmitter(
            enabled=True,
            webhook_url="https://araos.local/api/v1/clinical/events",
            secret=secret,
            session=session,
        )
        ok = emitter.emit(
            event_type="ANAMNESIS_RECORDED",
            patient_id=9,
            tenant_id="vittalis",
            payload={"anamnesis_id": 3},
            source_id=3,
        )
        assert ok is True
        assert len(session.posted) == 1
        url, headers, content = session.posted[0]
        assert url == "https://araos.local/api/v1/clinical/events"
        assert headers["X-AraOS-Signature"] == _sign(content, secret)
        body = json.loads(content)
        assert body["type"] == "ANAMNESIS_RECORDED"
        assert body["patient_id"] == "9"

    def test_network_failure_never_raises(self):
        session = RecordingSession(status=500)
        emitter = AraOSEventEmitter(
            enabled=True,
            webhook_url="https://araos.local/events",
            secret="s",
            session=session,
        )
        # Não lança mesmo com erro 500
        assert emitter.emit(event_type="X", patient_id=1, tenant_id="t", payload={}) is False
        # Não lança mesmo com exceção de transporte
        import requests as rq

        class BrokenSession:
            def post(self, *args, **kwargs):
                raise rq.ConnectionError("boom")

        emitter2 = AraOSEventEmitter(
            enabled=True, webhook_url="https://araos.local/events", secret="s", session=BrokenSession()
        )
        assert emitter2.emit(event_type="X", patient_id=1, tenant_id="t", payload={}) is False


class TestWrapEventTypes:
    """F2 — wrap nos fluxos de exame/dosagem/prescrição: tipos canônicos."""

    @pytest.mark.parametrize(
        "event_type,payload",
        [
            (
                "EXAM_RECORDED",
                {"exame_id": 1, "paciente_id": 7, "tipo_exame": "texto", "titulo": "Hemograma"},
            ),
            (
                "DOSAGE_RECORDED",
                {"dosagem_id": 2, "paciente_id": 7, "dosage_text": "0.5ml", "drops": 15},
            ),
            (
                "PRESCRIPTION_ISSUED",
                {"prescricao_id": 3, "paciente_id": 7, "n_medicamentos": 2},
            ),
        ],
    )
    def test_wrap_emits_canonical_type(self, event_type, payload):
        session = RecordingSession()
        emitter = AraOSEventEmitter(
            enabled=True,
            webhook_url="https://araos.local/api/v1/clinical/events",
            secret="s",
            session=session,
        )
        ok = emitter.emit(
            event_type=event_type,
            patient_id=payload.get("paciente_id", 7),
            tenant_id="t-vittalis",
            payload=payload,
            source_id=payload.get(f"{event_type.lower().split('_')[0]}_id"),
        )
        assert ok is True
        body = json.loads(session.posted[-1][2])
        assert body["type"] == event_type
        assert body["tenant_id"] == "t-vittalis"
        assert body["source"] == "siap"
        # payload canônico preservado
        for k, v in payload.items():
            assert body.get(k) == v
