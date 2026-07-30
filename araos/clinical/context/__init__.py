"""
Clinical Context Engine — Bounded Context (Sprint 4.2 / ADR-0003).

Camada de contexto clínico do AraOS — representa QUALQUER contexto
relevante para a evolução longitudinal do paciente.

Sub-tipos (via ContextType):
    - ClinicalEpisode
    - MedicationContext
    - SchoolContext
    - FamilyContext
    - EnvironmentalContext
    - DevelopmentalMilestone
    - BehavioralPhase
    - SleepPattern
    - EducationalTransition
    - SocialContext

Sub-módulos:
    domain         — Aggregate Root + enums + state machine + rule ABC
    application    — service + rule engine + query + suggester
    projections    — Context + ActiveContext + Relationship
    (api + sql)    — entregues em arquivos paralelos
"""

from araos.clinical.context import (
    application,
    domain,
    projections,
)


__all__ = [
    "domain",
    "application",
    "projections",
]
