"""
AraOS Clinical Event Engine — Hash Chain.

Append-only audit chain usando SHA-256.

Cada evento tem:
    event_hash = SHA256(previous_hash + canonical_json(event_sem_hash))

Garantias:
    - Qualquer alteração em evento passado quebra a chain
    - Detecção determinística de tampering
    - Performance O(1) para append, O(N) para verify
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional


# Hash da "ausência de evento anterior" — primeiro evento da chain
GENESIS_HASH: str = "0" * 64


def canonical_form(event_dict: Dict[str, Any]) -> str:
    """
    Serializa dict para JSON canônico (chaves ordenadas, sem whitespace).
    Garante que o hash é determinístico independente da ordem das chaves.
    """
    return json.dumps(
        event_dict,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
        ensure_ascii=False,
    )


def compute_event_hash(
    previous_hash: Optional[str],
    event_dict: Dict[str, Any],
) -> str:
    """
    Calcula SHA-256 de um evento incluindo o link com o anterior.

    Args:
        previous_hash: hash do evento anterior (None → GENESIS_HASH).
        event_dict: dict do evento SEM o campo `event_hash` (para auto-referência
                    não contaminar o cálculo).

    Returns:
        Hash hex (64 chars) do evento.
    """
    prev = previous_hash if previous_hash is not None else GENESIS_HASH
    payload = prev + canonical_form(event_dict)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_chain(events: List[Dict[str, Any]]) -> bool:
    """
    Verifica integridade de uma chain ordenada de eventos.

    Args:
        events: lista de dicts na ordem cronológica, cada um com `event_hash`.

    Returns:
        True se todos os links estão intactos.
    """
    prev_hash: Optional[str] = None
    for event in events:
        if "event_hash" not in event or event["event_hash"] is None:
            return False
        # Reconstrói dict sem event_hash para cálculo
        event_for_hash = {k: v for k, v in event.items() if k != "event_hash"}
        expected = compute_event_hash(prev_hash, event_for_hash)
        if expected != event["event_hash"]:
            return False
        prev_hash = event["event_hash"]
    return True


def find_break(events: List[Dict[str, Any]]) -> Optional[int]:
    """
    Encontra o índice do primeiro evento com hash inválido.

    Útil para debug de corrupção de chain. Retorna None se chain íntegra.
    """
    prev_hash: Optional[str] = None
    for idx, event in enumerate(events):
        if "event_hash" not in event or event["event_hash"] is None:
            return idx
        event_for_hash = {k: v for k, v in event.items() if k != "event_hash"}
        expected = compute_event_hash(prev_hash, event_for_hash)
        if expected != event["event_hash"]:
            return idx
        prev_hash = event["event_hash"]
    return None
