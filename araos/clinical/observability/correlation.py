"""
Correlation IDs — propagação thread-local + context manager.

Um correlation_id é propagado por TODA a cadeia de processamento:

    HTTP request → Application service → Publisher → Event Store → Projection → Logs

Uso típico:

    # Em Flask before_request:
    set_correlation_id(request.headers.get("X-Correlation-ID") or new_correlation_id())

    # Em Application service:
    with CorrelationContext(correlation_id):
        publisher.publish(...)

    # Em qualquer ponto:
    logger.info("processing", extra={"correlation_id": current_correlation_id()})
"""
from __future__ import annotations

import contextlib
import threading
import uuid
from typing import Iterator, Optional

# Thread-local storage — cada thread (ou async task) tem sua própria correlation_id.
_local = threading.local()


def new_correlation_id() -> str:
    """Gera novo correlation_id (UUID4)."""
    return str(uuid.uuid4())


def current_correlation_id() -> Optional[str]:
    """Retorna correlation_id da thread atual (None se não setado)."""
    return getattr(_local, "correlation_id", None)


def set_correlation_id(correlation_id: str) -> None:
    """Define correlation_id da thread atual."""
    _local.correlation_id = correlation_id


def clear_correlation_id() -> None:
    """Limpa correlation_id da thread atual."""
    _local.correlation_id = None


class CorrelationContext:
    """
    Context manager para escopo de correlation_id.

    Uso:
        with CorrelationContext(new_correlation_id()):
            ...  # correlation_id disponível em qualquer ponto
    """

    def __init__(self, correlation_id: Optional[str] = None) -> None:
        self._correlation_id = correlation_id or new_correlation_id()
        self._previous: Optional[str] = None

    @property
    def correlation_id(self) -> str:
        return self._correlation_id

    def __enter__(self) -> str:
        self._previous = current_correlation_id()
        set_correlation_id(self._correlation_id)
        return self._correlation_id

    def __exit__(self, *exc) -> None:
        if self._previous is not None:
            set_correlation_id(self._previous)
        else:
            clear_correlation_id()


@contextlib.contextmanager
def correlation_scope(correlation_id: Optional[str] = None) -> Iterator[str]:
    """Atalho: with correlation_scope(): ..."""
    cid = correlation_id or new_correlation_id()
    with CorrelationContext(cid) as c:
        yield c
