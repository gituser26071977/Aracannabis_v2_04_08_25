"""Testes do replay histórico do SIAP → AraOS (F2 retrofit).

Valida que anamneses/evoluções históricas são convertidas em Clinical
Events canônicos com gene_expressions derivadas e occurred_at retroativo.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from services.historical_replay import HistoricalReplayService


class FakeEmitter:
    """Captura os emits, retornando sucesso (True)."""

    def __init__(self, *, ok: bool = True) -> None:
        self.ok = ok
        self.events: list[dict] = []

    def emit(self, **kwargs) -> bool:
        self.events.append(kwargs)
        return self.ok


def _anamnese(id_, paciente_id, condicao, data):
    rec = MagicMock()
    rec.id = id_
    rec.paciente_id = paciente_id
    rec.condicao_principal = condicao
    rec.sintomas_atuais = None
    rec.medicamentos_uso = None
    rec.fonte = "manual"
    rec.data_anamnese = data
    return rec


def _evolucao(id_, paciente_id, nota, data):
    rec = MagicMock()
    rec.id = id_
    rec.paciente_id = paciente_id
    rec.nota_evolucao = nota
    rec.data_evolucao = data
    return rec


def _make_session(anamneses, evolutions, pacientes=None):
    """Sessão fake com query/order_by/all e get de paciente."""
    session = MagicMock()

    class _QueryResult:
        def __init__(self, rows):
            self._rows = rows

        def order_by(self, *a, **k):
            return self

        def all(self):
            return self._rows

    session.query.side_effect = lambda model: (
        _QueryResult(anamneses) if model.__name__ == "Anamnese" else _QueryResult(evolutions)
    )
    pacientes = pacientes or {}
    session.get.side_effect = lambda model, pk: pacientes.get(pk)
    return session


def _paciente(id_, associacao_id):
    p = MagicMock()
    p.id = id_
    p.associacao_id = associacao_id
    return p


class TestHistoricalReplay:
    def test_emits_anamnesis_with_genes(self):
        from datetime import datetime

        ana = _anamnese(42, 7, "Paciente com insônia crônica", datetime(2026, 1, 15))
        session = _make_session([ana], [], {7: _paciente(7, 5)})
        emitter = FakeEmitter()
        replay = HistoricalReplayService(session, emitter=emitter)

        result = replay.run()

        assert result.total == 1
        assert result.emitted == 1
        ev = emitter.events[0]
        assert ev["event_type"] == "ANAMNESIS_RECORDED"
        assert ev["patient_id"] == 7
        assert ev["tenant_id"] == "5"
        assert ev["source_id"] == 42
        assert ev["metadata"]["replay"] is True
        genes = ev["payload"]["gene_expressions"]
        assert any(g["gene"] == "sono" for g in genes)

    def test_emits_evolucao_with_genes(self):
        from datetime import datetime

        evo = _evolucao(7, 7, "Paciente com boa evolução, dorme bem", datetime(2026, 2, 1))
        session = _make_session([], [evo], {7: _paciente(7, 5)})
        emitter = FakeEmitter()
        replay = HistoricalReplayService(session, emitter=emitter)

        result = replay.run()

        assert result.emitted == 1
        ev = emitter.events[0]
        assert ev["event_type"] == "EVOLUTION_RECORDED"
        genes = ev["payload"]["gene_expressions"]
        assert any(g["gene"] == "sono" for g in genes)

    def test_no_genes_no_payload_skip(self):
        from datetime import datetime

        evo = _evolucao(8, 7, "Evolução sem marcadores", datetime(2026, 3, 1))
        session = _make_session([], [evo], {7: _paciente(7, 5)})
        emitter = FakeEmitter()
        replay = HistoricalReplayService(session, emitter=emitter)

        result = replay.run()

        assert result.emitted == 1  # emite mesmo sem genes (payload ainda tem nota)

    def test_emitter_failure_counts_failed(self):
        from datetime import datetime

        ana = _anamnese(42, 7, "insônia", datetime(2026, 1, 15))
        session = _make_session([ana], [], {7: _paciente(7, 5)})
        emitter = FakeEmitter(ok=False)
        replay = HistoricalReplayService(session, emitter=emitter)

        result = replay.run()

        assert result.emitted == 0
        assert result.failed == 1

    def test_limit(self):
        from datetime import datetime

        anas = [_anamnese(1, 7, "insônia", datetime(2026, 1, 1)),
                _anamnese(2, 7, "dor", datetime(2026, 1, 2))]
        session = _make_session(anas, [], {7: _paciente(7, 5)})
        emitter = FakeEmitter()
        replay = HistoricalReplayService(session, emitter=emitter)

        result = replay.run(limit=1)

        assert result.total == 1
        assert len(emitter.events) == 1
