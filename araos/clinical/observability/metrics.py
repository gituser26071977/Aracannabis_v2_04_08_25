"""
Metrics — instrumentação para Clinical Event Engine + Neuro Registry.

MÉTRICAS COBERTAS:

    Replay Duration       (timer)   — tempo de replay_all() / replay_from()
    Replay Count          (counter) — total de replays executados
    Projection Lag        (gauge)   — eventos publicados - processados
    Dead Events           (counter) — eventos sem handler
    Invalid Events        (counter) — eventos com payload inválido
    Aggregate Version     (gauge)   — version atual dos aggregates
    Published Events      (counter) — total de eventos publicados
    Processed Events      (counter) — total de eventos aplicados
    Pending Events        (gauge)   — published - processed (lag)

Thread-safety: usa threading.Lock para mutações atômicas.
Adapter-ready: dump_prometheus() expõe formato compatível Prometheus.
"""
from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class _Counter:
    name: str
    value: int = 0
    description: str = ""

    def inc(self, n: int = 1) -> None:
        self.value += n


@dataclass
class _Gauge:
    name: str
    value: float = 0.0
    description: str = ""

    def set(self, v: float) -> None:
        self.value = v

    def inc(self, n: float = 1.0) -> None:
        self.value += n

    def dec(self, n: float = 1.0) -> None:
        self.value -= n


@dataclass
class _Histogram:
    """Histograma simples (count, sum, min, max, mean)."""

    name: str
    samples: List[float] = field(default_factory=list)
    description: str = ""

    def observe(self, value: float) -> None:
        self.samples.append(value)

    @property
    def count(self) -> int:
        return len(self.samples)

    @property
    def sum(self) -> float:
        return sum(self.samples)

    @property
    def mean(self) -> float:
        if not self.samples:
            return 0.0
        return sum(self.samples) / len(self.samples)

    @property
    def min(self) -> float:
        return min(self.samples) if self.samples else 0.0

    @property
    def max(self) -> float:
        return max(self.samples) if self.samples else 0.0


class MetricsRecorder:
    """
    Recorder thread-safe para métricas do Clinical Event Engine.

    Singleton via get_metrics(). Para testes, use reset_metrics().
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, _Counter] = {}
        self._gauges: Dict[str, _Gauge] = {}
        self._histograms: Dict[str, _Histogram] = {}

    # ─── Counter API ──────────────────────────────────────────────

    def counter_inc(self, name: str, n: int = 1, description: str = "") -> None:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = _Counter(name=name, description=description)
            self._counters[name].inc(n)

    def counter_get(self, name: str) -> int:
        with self._lock:
            c = self._counters.get(name)
            return c.value if c else 0

    # ─── Gauge API ────────────────────────────────────────────────

    def gauge_set(self, name: str, value: float, description: str = "") -> None:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = _Gauge(name=name, description=description)
            self._gauges[name].set(value)

    def gauge_inc(self, name: str, n: float = 1.0) -> None:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = _Gauge(name=name)
            self._gauges[name].inc(n)

    def gauge_dec(self, name: str, n: float = 1.0) -> None:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = _Gauge(name=name)
            self._gauges[name].dec(n)

    def gauge_get(self, name: str) -> float:
        with self._lock:
            g = self._gauges.get(name)
            return g.value if g else 0.0

    # ─── Histogram (timer) API ────────────────────────────────────

    @contextmanager
    def timer(self, name: str, description: str = "") -> Iterator[None]:
        """Context manager que mede duração em segundos."""
        start = time.monotonic()
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = _Histogram(name=name, description=description)
        try:
            yield
        finally:
            duration = time.monotonic() - start
            with self._lock:
                self._histograms[name].observe(duration)

    def histogram_observe(self, name: str, value: float) -> None:
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = _Histogram(name=name)
            self._histograms[name].observe(value)

    # ─── Snapshot / Export ────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": {
                    name: c.value
                    for name, c in self._counters.items()
                },
                "gauges": {
                    name: g.value
                    for name, g in self._gauges.items()
                },
                "histograms": {
                    name: {
                        "count": h.count,
                        "sum": h.sum,
                        "mean": h.mean,
                        "min": h.min,
                        "max": h.max,
                    }
                    for name, h in self._histograms.items()
                },
            }

    def dump_prometheus(self) -> str:
        """Exporta em formato Prometheus exposition."""
        lines: List[str] = []
        with self._lock:
            for name, c in self._counters.items():
                lines.append(
                    f"# HELP {name} {c.description or name}\n"
                    f"# TYPE {name} counter\n"
                    f"{name} {c.value}\n"
                )
            for name, g in self._gauges.items():
                lines.append(
                    f"# HELP {name} {g.description or name}\n"
                    f"# TYPE {name} gauge\n"
                    f"{name} {g.value}\n"
                )
            for name, h in self._histograms.items():
                lines.append(
                    f"# HELP {name} {h.description or name}\n"
                    f"# TYPE {name} summary\n"
                    f"{name}_count {h.count}\n"
                    f"{name}_sum {h.sum}\n"
                )
        return "\n".join(lines)

    def reset(self) -> None:
        """Reset para testes."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()


# ─── Singleton ────────────────────────────────────────────────────────

_metrics: Optional[MetricsRecorder] = None
_metrics_lock = threading.Lock()


def get_metrics() -> MetricsRecorder:
    """Retorna singleton MetricsRecorder."""
    global _metrics
    with _metrics_lock:
        if _metrics is None:
            _metrics = MetricsRecorder()
        return _metrics


def reset_metrics() -> None:
    """Reseta singleton (uso em testes)."""
    global _metrics
    with _metrics_lock:
        _metrics = None


# ─── Métricas canônicas do Clinical Event Engine ────────────────────


# Counter names (constantes para evitar typos)
METRIC_REPLAY_COUNT = "clinical_replay_count"
METRIC_PUBLISHED_EVENTS = "clinical_published_events"
METRIC_PROCESSED_EVENTS = "clinical_processed_events"
METRIC_DEAD_EVENTS = "clinical_dead_events"
METRIC_INVALID_EVENTS = "clinical_invalid_events"

# Gauge names
METRIC_PROJECTION_LAG = "clinical_projection_lag"
METRIC_PENDING_EVENTS = "clinical_pending_events"
METRIC_AGGREGATE_VERSION = "clinical_aggregate_version"

# Histogram names
METRIC_REPLAY_DURATION = "clinical_replay_duration_seconds"
