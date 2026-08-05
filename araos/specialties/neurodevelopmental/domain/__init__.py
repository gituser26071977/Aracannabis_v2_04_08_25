"""
AraOS Neurodevelopmental — Domain Layer (DDD).

Pure Python, zero SQLAlchemy/Flask/FastAPI. Este pacote define o domínio
clínico do Módulo NEURODESENVOLVIMENTO segundo princípios DDD:

    - Bounded Context: Neurodevelopmental Registry (ADR-0002)
    - Aggregate Roots: ClinicalIdentity, Intervention
    - Entities: Diagnosis, Phenotype, Assessment, Outcome
    - Value Objects: CID10Code, CID11Code, DSM5Code, ConditionCode, ClassificationEntry, DiagnosisClassification
    - Domain Events: frozen dataclasses (pub/sub do Clinical Event Engine)
    - Domain Services: DiagnosisTransitionService

Invariantes do domínio:
    1. Toda mudança clínica ocorre via Domain Event publicado no Event Store.
    2. Multi-classificação simultânea permitida (CID-10 + CID-11 + DSM-5-TR + SNOMED + interna).
    3. Diagnosis segue state machine de 6 estados com matriz de transições.
    4. Phenotype pode existir antes/depois do diagnóstico — independente.
    5. Assessment nunca mutua estado do paciente — apenas produz evidência.
    6. source_event_ids sempre presente (lista) — rastreabilidade completa.

Public API (re-exportada):
    IDs:           ClinicalIdentityId, DiagnosisId, PhenotypeId, AssessmentId,
                   InterventionId, OutcomeId, PatientId
    Aggregates:    ClinicalIdentity, Intervention
    Entities:      Diagnosis, Phenotype, Assessment, Outcome
    Value Objects: CID10Code, CID11Code, DSM5Code, ConditionCode,
                   ClassificationEntry, DiagnosisClassification, AssessmentScore
    States:        DiagnosisState, InterventionState
    Enums:         InterventionType, ClassificationType, PhenotypeSeverity,
                   OutcomeSeverity, OutcomeMagnitude, OutcomeType, OutcomeCausality,
                   AssessmentStatus, ClinicalIdentityStatus
    Events:        25 DomainEvent frozen dataclasses
    Services:      DiagnosisTransitionService, DomainError, exceptions
"""

from .assessment import Assessment, AssessmentScore, AssessmentStatus
from .classification import ClassificationEntry, ClassificationType, DiagnosisClassification
from .clinical_identity import ClinicalIdentity, ClinicalIdentityStatus
from .condition import (
    CID10Code,
    CID11Code,
    ConditionCode,
    DSM5Code,
    InvalidConditionCodeError,
)
from .diagnosis import (
    Diagnosis,
    DiagnosisState,
    InvalidDiagnosisTransitionError,
)
from .events import (
    AssessmentApplied,
    AssessmentUpdated,
    DomainEvent,
    ClinicalIdentityArchived,
    ClinicalIdentityCreated,
    DiagnosisClassificationAdded,
    DiagnosisClassificationRemoved,
    DiagnosisConfirmed,
    DiagnosisDiscarded,
    DiagnosisHypothesised,
    DiagnosisInRemission,
    DiagnosisInvestigating,
    DiagnosisRevised,
    InterventionAdjusted,
    InterventionPaused,
    InterventionResumed,
    InterventionStarted,
    InterventionStopped,
    OutcomeAdverseEvent,
    OutcomeImprovement,
    OutcomeNoChange,
    OutcomePartialResponse,
    OutcomeRemission,
    OutcomeWorsening,
    PhenotypeObserved,
    PhenotypeResolved,
)
from .ids import (
    AssessmentId,
    ClinicalIdentityId,
    DiagnosisId,
    InterventionId,
    OutcomeId,
    PatientId,
    PhenotypeId,
    new_id,
)
from .intervention import Dose, Intervention, InterventionState, InterventionType
from .outcome import (
    Outcome,
    OutcomeCausality,
    OutcomeMagnitude,
    OutcomeSeverity,
    OutcomeType,
)
from .phenotype import (
    Phenotype,
    PhenotypeSeverity,
)
from .services import DiagnosisTransitionService

__version__ = "1.0.0"

__all__ = [
    # IDs
    "ClinicalIdentityId",
    "DiagnosisId",
    "PhenotypeId",
    "AssessmentId",
    "InterventionId",
    "OutcomeId",
    "PatientId",
    "new_id",
    # Aggregate Roots
    "ClinicalIdentity",
    "Intervention",
    # Entities
    "Diagnosis",
    "Phenotype",
    "Assessment",
    "Outcome",
    # Value Objects
    "CID10Code",
    "CID11Code",
    "DSM5Code",
    "ConditionCode",
    "InvalidConditionCodeError",
    "DiagnosisClassification",
    "ClassificationType",
    "ClassificationEntry",
    "AssessmentScore",
    # States & Enums
    "DiagnosisState",
    "InterventionState",
    "InterventionType",
    "PhenotypeSeverity",
    "OutcomeSeverity",
    "OutcomeMagnitude",
    "OutcomeType",
    "OutcomeCausality",
    "AssessmentStatus",
    "ClinicalIdentityStatus",
    "Dose",
    # Domain Events (25)
    "DomainEvent",
    "ClinicalIdentityCreated",
    "ClinicalIdentityArchived",
    "DiagnosisHypothesised",
    "DiagnosisInvestigating",
    "DiagnosisConfirmed",
    "DiagnosisRevised",
    "DiagnosisInRemission",
    "DiagnosisDiscarded",
    "DiagnosisClassificationAdded",
    "DiagnosisClassificationRemoved",
    "PhenotypeObserved",
    "PhenotypeResolved",
    "AssessmentApplied",
    "AssessmentUpdated",
    "InterventionStarted",
    "InterventionAdjusted",
    "InterventionPaused",
    "InterventionResumed",
    "InterventionStopped",
    "OutcomeImprovement",
    "OutcomeWorsening",
    "OutcomePartialResponse",
    "OutcomeRemission",
    "OutcomeAdverseEvent",
    "OutcomeNoChange",
    # Services
    "DiagnosisTransitionService",
    "InvalidDiagnosisTransitionError",
]