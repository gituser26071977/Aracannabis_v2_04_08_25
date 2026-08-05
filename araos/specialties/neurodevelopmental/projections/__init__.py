"""
AraOS Neurodevelopmental — Projection Layer (Registry rebuildable).

Camada de read model reconstruível a partir do Event Store.

Componentes:
    db_models.py    — 7 tabelas SQLAlchemy (read model físico)
    handlers.py     — Event → projection reducers (pure functions)
    registry.py     — REDACTED (replay_all, replay_from, apply)

Princípios:
    1. Registry é PROJECTION — descartável, reconstruível.
    2. Toda mutação ocorre via application service → Event Store → handler.
    3. Handlers são idempotentes (checa event_id em processed_events).
    4. Replay completo = wipe registry + replay desde genesis.
    5. Replay incremental = replay desde since_sequence (filtra já processados).

Garantias testáveis:
    - Wipe Registry → replay → bit-identical ao estado anterior.
    - Aplicar mesmo evento N vezes → mesmo estado (idempotência).
    - Eventos embaralhados → mesmo estado final (ordenação por sequence).
"""

from .db_models import (
    NeuroRegistryAssessmentModel,
    NeuroRegistryClinicalIdentityModel,
    NeuroRegistryDiagnosisModel,
    NeuroRegistryInterventionModel,
    NeuroRegistryOutcomeModel,
    NeuroRegistryPhenotypeModel,
    NeuroRegistryProcessedEventModel,
)
from .registry import REDACTED

__all__ = [
    "NeuroRegistryClinicalIdentityModel",
    "NeuroRegistryDiagnosisModel",
    "NeuroRegistryPhenotypeModel",
    "NeuroRegistryAssessmentModel",
    "NeuroRegistryInterventionModel",
    "NeuroRegistryOutcomeModel",
    "NeuroRegistryProcessedEventModel",
    "REDACTED",
]