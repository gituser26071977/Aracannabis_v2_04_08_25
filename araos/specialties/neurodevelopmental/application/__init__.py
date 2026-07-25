"""
AraOS Neurodevelopmental — Application Layer.

Camada de orquestração entre API/routes e domain layer.

Padrão (DDD Application Service):
    1. Recebe command do caller (API, batch, admin).
    2. Constrói/atualiza entidade de domínio (estado em memória).
    3. Constrói Domain Event (frozen dataclass).
    4. Publica via `ClinicalEventPublisher.publish()`.
    5. Retorna `event_id` (síncrono) para caller.

Invariantes:
    - Application services NUNCA escrevem em tabelas/projeções diretamente.
      Toda mudança é via Event Store.
    - Application services NÃO conhecem detalhes HTTP (request/response).
      Adaptadores ficam nas routes/.

Serviços públicos:
    ClinicalIdentityService — criação, arquivamento
    DiagnosisService       — hypothesize, investigate, confirm, revise, remission, discard + classifications
    PhenotypeService       — observe, resolve
    AssessmentService      — apply, update
    InterventionService    — start, adjust, pause, resume, stop
    OutcomeService         — improvement, worsening, partial, remission, adverse, no_change
"""

from .assessment_service import AssessmentService
from .clinical_identity_service import ClinicalIdentityService
from .diagnosis_service import DiagnosisService
from .intervention_service import InterventionService
from .outcome_service import OutcomeService
from .phenotype_service import PhenotypeService

__all__ = [
    "ClinicalIdentityService",
    "DiagnosisService",
    "PhenotypeService",
    "AssessmentService",
    "InterventionService",
    "OutcomeService",
]