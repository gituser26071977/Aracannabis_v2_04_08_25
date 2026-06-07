"""
AraOS Clinical Intelligence Foundation.

Módulo de representação estruturada do conhecimento clínico.
NÃO contém IA — apenas modelos, projeções e contratos.

O objetivo é criar a fundação para:
    - Clinical Intelligence futura
    - Voice Copilot
    - Concierge IA
    - Patient Digital Twin
    - Knowledge Graph
"""

from .entities.models import (
    Diagnosis,
    Medication,
    Allergy,
    Procedure,
    RiskFactor,
    ClinicalEntityBase,
)
from .profile.models import ClinicalProfile
from .timeline.models import ClinicalTimeline, TimelineEntry
from .graph.models import ClinicalGraph, ClinicalNode, ClinicalRelationship
from .summary.engine import ClinicalSummaryEngine
from .twin.models import PatientDigitalTwin
from .projections.engine import ClinicalProjectionEngine

__all__ = [
    "ClinicalEntityBase",
    "Diagnosis",
    "Medication",
    "Allergy",
    "Procedure",
    "RiskFactor",
    "ClinicalProfile",
    "ClinicalTimeline",
    "TimelineEntry",
    "ClinicalGraph",
    "ClinicalNode",
    "ClinicalRelationship",
    "ClinicalSummaryEngine",
    "PatientDigitalTwin",
    "ClinicalProjectionEngine",
]
