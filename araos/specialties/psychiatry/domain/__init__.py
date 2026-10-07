"""Domínio da triagem psiquiátrica (puro, sem I/O de framework)."""

from .explain import explain
from .instrument import build_spec, load_config, parse_config, register_instrument
from .items import DomainDef, InstrumentConfig, PsychItem
from .safety import assess_suicide
from .scoring import Evaluation, derive_contexts, evaluate

__all__ = [
    "DomainDef",
    "InstrumentConfig",
    "PsychItem",
    "Evaluation",
    "evaluate",
    "derive_contexts",
    "assess_suicide",
    "explain",
    "build_spec",
    "parse_config",
    "load_config",
    "register_instrument",
]
