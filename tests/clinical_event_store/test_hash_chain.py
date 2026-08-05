"""
Testes do Hash Chain do Clinical Event Engine.

Cobertura:
    - canonical_form
    - compute_event_hash (com/sem previous_hash)
    - verify_chain
    - find_break
    - GENESIS_HASH
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from araos.clinical.event_store.hash_chain import (
    GENESIS_HASH,
    canonical_form,
    compute_event_hash,
    find_break,
    verify_chain,
)


# ═══════════════════════════════════════════════════════════════════════
# canonical_form
# ═══════════════════════════════════════════════════════════════════════


class TestCanonicalForm:
    def test_returns_string(self):
        result = canonical_form({"a": 1})
        assert isinstance(result, str)

    def test_keys_are_sorted(self):
        canonical = canonical_form({"b": 1, "a": 2})
        parsed = json.loads(canonical)
        assert list(parsed.keys()) == ["a", "b"]

    def test_no_whitespace(self):
        result = canonical_form({"a": 1, "b": 2})
        assert " " not in result
        assert "{" in result
        assert "}" in result

    def test_deterministic_for_same_input(self):
        d = {"x": 1, "y": [1, 2, 3], "z": {"a": "b"}}
        assert canonical_form(d) == canonical_form(d)

    def REDACTED(self):
        dt = datetime(2026, 7, 15, 10, 30, tzinfo=timezone.utc)
        # Não pode lançar — usa default=str
        result = canonical_form({"event_datetime": dt})
        assert "2026" in result

    def test_handles_unicode(self):
        result = canonical_form({"paciente": "João", "médico": "Maria"})
        assert "João" in result or "Jo\\u00e3o" in result


# ═══════════════════════════════════════════════════════════════════════
# compute_event_hash
# ═══════════════════════════════════════════════════════════════════════


class TestComputeEventHash:
    def test_genesis_when_no_previous(self):
        h = compute_event_hash(None, {"a": 1})
        # Deve ser SHA-256(GENESIS + canonical({"a":1}))
        assert h != GENESIS_HASH
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        h1 = compute_event_hash(None, {"a": 1})
        h2 = compute_event_hash(None, {"a": 1})
        assert h1 == h2

    def REDACTED(self):
        e = {"a": 1}
        h1 = compute_event_hash(None, e)
        h2 = compute_event_hash("0" * 64, e)
        h3 = compute_event_hash("a" * 64, e)
        # h1 e h2 devem ser iguais (None = GENESIS = zeros)
        assert h1 == h2
        # h3 deve ser diferente
        assert h2 != h3

    def REDACTED(self):
        h1 = compute_event_hash(None, {"a": 1})
        h2 = compute_event_hash(None, {"a": 2})
        assert h1 != h2

    def REDACTED(self):
        h1 = compute_event_hash(None, {"a": 1, "b": 2})
        h2 = compute_event_hash(None, {"b": 2, "a": 1})
        assert h1 == h2


# ═══════════════════════════════════════════════════════════════════════
# verify_chain
# ═══════════════════════════════════════════════════════════════════════


class TestVerifyChain:
    def _make_event(self, payload: dict, prev_hash: str | None) -> dict:
        prev = prev_hash if prev_hash is not None else GENESIS_HASH
        event_for_hash = {**payload, "previous_hash": prev}
        h = compute_event_hash(prev, event_for_hash)
        return {**payload, "previous_hash": prev, "event_hash": h}

    def test_empty_chain_is_valid(self):
        assert verify_chain([]) is True

    def test_single_event_valid(self):
        e = self._make_event({"id": "1", "x": 1}, None)
        assert verify_chain([e]) is True

    def test_three_events_chained(self):
        e1 = self._make_event({"id": "1", "x": 1}, None)
        e2 = self._make_event({"id": "2", "x": 2}, e1["event_hash"])
        e3 = self._make_event({"id": "3", "x": 3}, e2["event_hash"])
        assert verify_chain([e1, e2, e3]) is True

    def test_tampered_event_detected(self):
        e1 = self._make_event({"id": "1", "x": 1}, None)
        e2 = self._make_event({"id": "2", "x": 2}, e1["event_hash"])
        # Tamper: alterar payload de e2 SEM recomputar hash
        e2["x"] = 999
        assert verify_chain([e1, e2]) is False

    def test_broken_link_detected(self):
        e1 = self._make_event({"id": "1", "x": 1}, None)
        e2 = self._make_event({"id": "2", "x": 2}, e1["event_hash"])
        e3 = self._make_event({"id": "3", "x": 3}, e1["event_hash"])  # link errado
        assert verify_chain([e1, e2, e3]) is False

    def test_missing_event_hash(self):
        e1 = self._make_event({"id": "1", "x": 1}, None)
        e1_no_hash = {**e1}
        del e1_no_hash["event_hash"]
        assert verify_chain([e1_no_hash]) is False

    def test_none_event_hash(self):
        e = self._make_event({"id": "1", "x": 1}, None)
        e["event_hash"] = None
        assert verify_chain([e]) is False


# ═══════════════════════════════════════════════════════════════════════
# find_break
# ═══════════════════════════════════════════════════════════════════════


class TestFindBreak:
    def _make_event(self, payload: dict, prev_hash: str | None) -> dict:
        prev = prev_hash if prev_hash is not None else GENESIS_HASH
        return {
            **payload,
            "previous_hash": prev,
            "event_hash": compute_event_hash(prev, {**payload, "previous_hash": prev}),
        }

    def test_intact_chain_returns_none(self):
        e1 = self._make_event({"id": "1"}, None)
        e2 = self._make_event({"id": "2"}, e1["event_hash"])
        e3 = self._make_event({"id": "3"}, e2["event_hash"])
        assert find_break([e1, e2, e3]) is None

    def test_finds_first_break(self):
        e1 = self._make_event({"id": "1"}, None)
        e2 = self._make_event({"id": "2"}, e1["event_hash"])
        e3 = self._make_event({"id": "3"}, e2["event_hash"])
        e3["id"] = "tampered"
        assert find_break([e1, e2, e3]) == 2

    def test_finds_break_in_middle(self):
        e1 = self._make_event({"id": "1"}, None)
        e2 = self._make_event({"id": "2"}, e1["event_hash"])
        e2["id"] = "tampered"
        assert find_break([e1, e2]) == 1


# ═══════════════════════════════════════════════════════════════════════
# GENESIS_HASH
# ═══════════════════════════════════════════════════════════════════════


class TestGenesisHash:
    def test_is_64_zeros(self):
        assert GENESIS_HASH == "0" * 64
