"""
AraOS Neurodevelopmental — Builtin Scales (auto-registro).

Importar este módulo registra todas as escalas builtin no `ScaleRegistry`.

Adicionar nova escala:
    1. Criar arquivo `meuescala.py` neste diretório com `MEUESCALA_SPEC`.
    2. Adicionar `from .meuescala import MEUESCALA_SPEC` abaixo.
    3. Adicionar `MEUESCALA_SPEC` à lista `_BUILTIN_SPECS`.

Sem alteração do código central.
"""

from __future__ import annotations

from ..registry import ScaleRegistry
from .atec import ATEC_SPEC
from .cars2 import CARS2_SPEC
from .gad7 import GAD7_SPEC
from .mchat import MCHAT_SPEC
from .phq9 import PHQ9_SPEC
from .snap_iv import SNAP_SPEC
from .srs2 import SRS2_SPEC
from .vineland import VINELAND_SPEC


_BUILTIN_SPECS = [
    # Sprint 1 (Sprint inicial)
    GAD7_SPEC,
    PHQ9_SPEC,
    # Sprint 2 (TEA + TDAH)
    MCHAT_SPEC,
    CARS2_SPEC,
    ATEC_SPEC,
    VINELAND_SPEC,
    SNAP_SPEC,
    SRS2_SPEC,
]


def _register_all() -> None:
    """Registra todas as escalas builtin. Idempotente em runtime."""
    for spec in _BUILTIN_SPECS:
        try:
            ScaleRegistry.register(spec)
        except Exception:
            # Spec já registrado — esperado em testes ou reimports.
            pass


# Auto-registro no import
_register_all()


__all__ = [
    "GAD7_SPEC",
    "PHQ9_SPEC",
    "MCHAT_SPEC",
    "CARS2_SPEC",
    "ATEC_SPEC",
    "VINELAND_SPEC",
    "SNAP_SPEC",
    "SRS2_SPEC",
    "_register_all",
    "_BUILTIN_SPECS",
]
