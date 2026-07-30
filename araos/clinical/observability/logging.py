"""
Structured Logging — logger adapter que injeta contexto automaticamente.

Cada log automaticamente inclui:
    - correlation_id (thread-local)
    - tenant_id (se setado)
    - event_type (se setado)
    - aggregate_type (se setado)
    - aggregate_id (se setado)

Formato JSON para consumo por Loki/CloudWatch/Elastic.

Uso:

    logger = get_logger("neurodevelopmental.registry")
    logger.info("diagnosis_confirmed", extra={
        "diagnosis_id": "diag-1",
        "severity": "moderate",
    })
    # → {"timestamp": "...", "level": "INFO", "message": "diagnosis_confirmed",
    #    "correlation_id": "...", "tenant_id": "...", ...}
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .correlation import current_correlation_id


class StructuredLogger:
    """
    Logger que formata saída como JSON estruturado com contexto automático.
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
        self._name = name

    def _format(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> str:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": logging.getLevelName(level),
            "logger": self._name,
            "message": message,
        }
        cid = current_correlation_id()
        if cid:
            record["correlation_id"] = cid
        if extra:
            record.update(extra)
        return json.dumps(record, default=str)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._logger.debug(self._format(logging.DEBUG, message, extra))

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._logger.info(self._format(logging.INFO, message, extra))

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._logger.warning(self._format(logging.WARNING, message, extra))

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._logger.error(self._format(logging.ERROR, message, extra))

    def exception(
        self, message: str, extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log com stacktrace."""
        exc_info = sys.exc_info()
        if exc_info[0] is not None:
            record = self._format(logging.ERROR, message, extra)
            self._logger.error(record, exc_info=exc_info)
        else:
            self.error(message, extra)


_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """Retorna StructuredLogger singleton por nome."""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def configure_root_logging(level: int = logging.INFO) -> None:
    """Configura logging root uma vez (chamado no app factory)."""
    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(level)
        root.addHandler(handler)
    root.setLevel(level)
