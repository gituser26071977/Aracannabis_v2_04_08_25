"""
AraOS Neurodevelopmental — Domain Events (25).

Frozen dataclasses representando o que aconteceu no domínio.
Cada Domain Event é a unidade publicável no Clinical Event Store.

Regras:
    - TODOS os eventos são frozen (imutáveis).
    - Convenção de nomenclatura: passado simples (Hypothesised, não Hypothesis).
    - Cada evento possui `event_type` (string do catálogo) + `aggregate_type`
      ('diagnosis'/'phenotype'/etc.) + `aggregate_id` (ID da entidade).
    - payload é Dict[str, Any] compatível com JSON Schema do catálogo.

Mapeamento Domain Event → Event Store:
    DomainEvent.event_type
        ↓ (publisher)
    ClinicalEventStore.append(event_type, payload, aggregate_type, aggregate_id)
        ↓ (replay)
    Registry Projection reconstruído

ADR-0002 §2.7: 25 event types novos. Cada Domain Event aqui é o payload
para o evento correspondente em CLINICAL_EVENT_CATALOG.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════
# Aggregate types — strings canônicas
# ═══════════════════════════════════════════════════════════════════════

AGGREGATE_CLINICAL_IDENTITY = "clinical_identity"
AGGREGATE_DIAGNOSIS = "diagnosis"
AGGREGATE_PHENOTYPE = "phenotype"
AGGREGATE_ASSESSMENT = "assessment"
AGGREGATE_INTERVENTION = "intervention"
AGGREGATE_OUTCOME = "outcome"


# ═══════════════════════════════════════════════════════════════════════
# Base — todos os Domain Events compartilham estes campos
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DomainEvent:
    """Base comum a todos os Domain Events."""

    aggregate_type: str
    aggregate_id: str
    actor_id: str  # profissional que originou o evento
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # event_type deve ser definido pela subclasse (string do catálogo)
    event_type: str = ""

    def to_payload(self) -> Dict[str, Any]:
        """
        Serializa para dict compatível com JSON Schema do catálogo.

        Subclasses sobrepõem para incluir seus campos específicos.
        """
        return {
            "actor_id": self.actor_id,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
        }


# ═══════════════════════════════════════════════════════════════════════
# ClinicalIdentity (2)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ClinicalIdentityCreated(DomainEvent):
    event_type: str = "CLINICAL_IDENTITY_CREATED"

    patient_id: str = ""
    initial_notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["patient_id"] = self.patient_id
        if self.initial_notes is not None:
            p["initial_notes"] = self.initial_notes
        return p


@dataclass(frozen=True)
class ClinicalIdentityArchived(DomainEvent):
    event_type: str = "CLINICAL_IDENTITY_ARCHIVED"

    reason: str = ""
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["reason"] = self.reason
        if self.notes is not None:
            p["notes"] = self.notes
        return p


# ═══════════════════════════════════════════════════════════════════════
# Diagnosis (8) — 6 transições + 2 classificação
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DiagnosisHypothesised(DomainEvent):
    event_type: str = "DIAGNOSIS_HYPOTHESIZED"

    condition_code: str = ""
    hypothesised_by: str = ""
    reason: Optional[str] = None
    onset_date: Optional[str] = None
    classification: Optional[Dict[str, Any]] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["condition_code"] = self.condition_code
        p["hypothesised_by"] = self.hypothesised_by
        if self.reason is not None:
            p["reason"] = self.reason
        if self.onset_date is not None:
            p["onset_date"] = self.onset_date
        if self.classification is not None:
            p["classification"] = self.classification
        return p


@dataclass(frozen=True)
class DiagnosisInvestigating(DomainEvent):
    event_type: str = "DIAGNOSIS_INVESTIGATING"

    investigation_plan: str = ""
    expected_evidence: Optional[List[str]] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["investigation_plan"] = self.investigation_plan
        if self.expected_evidence is not None:
            p["expected_evidence"] = self.expected_evidence
        return p


@dataclass(frozen=True)
class DiagnosisConfirmed(DomainEvent):
    event_type: str = "DIAGNOSIS_CONFIRMED"

    confirmed_by: str = ""
    confirmation_evidence: Dict[str, Any] = field(default_factory=dict)
    severity: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["confirmed_by"] = self.confirmed_by
        p["confirmation_evidence"] = dict(self.confirmation_evidence)
        if self.severity is not None:
            p["severity"] = self.severity
        return p


@dataclass(frozen=True)
class DiagnosisRevised(DomainEvent):
    event_type: str = "DIAGNOSIS_REVISED"

    new_condition_code: str = ""
    previous_condition_code: Optional[str] = None
    revised_by: str = ""
    reason: str = ""
    new_classification: Optional[Dict[str, Any]] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["new_condition_code"] = self.new_condition_code
        if self.previous_condition_code is not None:
            p["previous_condition_code"] = self.previous_condition_code
        p["revised_by"] = self.revised_by
        p["reason"] = self.reason
        if self.new_classification is not None:
            p["new_classification"] = self.new_classification
        return p


@dataclass(frozen=True)
class DiagnosisInRemission(DomainEvent):
    event_type: str = "DIAGNOSIS_IN_REMISSION"

    remission_type: str = ""  # 'partial' | 'complete'
    marked_by: str = ""
    evidence: Optional[Dict[str, Any]] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["remission_type"] = self.remission_type
        p["marked_by"] = self.marked_by
        if self.evidence is not None:
            p["evidence"] = self.evidence
        return p


@dataclass(frozen=True)
class DiagnosisDiscarded(DomainEvent):
    event_type: str = "DIAGNOSIS_DISCARDED"

    discarded_by: str = ""
    reason: str = ""
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["discarded_by"] = self.discarded_by
        p["reason"] = self.reason
        if self.notes is not None:
            p["notes"] = self.notes
        return p


@dataclass(frozen=True)
class DiagnosisClassificationAdded(DomainEvent):
    event_type: str = "DIAGNOSIS_CLASSIFICATION_ADDED"

    classification_type: str = ""
    code: str = ""
    added_by: str = ""
    is_primary: bool = False

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["classification_type"] = self.classification_type
        p["code"] = self.code
        p["added_by"] = self.added_by
        p["is_primary"] = self.is_primary
        return p


@dataclass(frozen=True)
class DiagnosisClassificationRemoved(DomainEvent):
    event_type: str = "DIAGNOSIS_CLASSIFICATION_REMOVED"

    classification_type: str = ""
    code: str = ""
    removed_by: str = ""
    reason: str = ""

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["classification_type"] = self.classification_type
        p["code"] = self.code
        p["removed_by"] = self.removed_by
        p["reason"] = self.reason
        return p


# ═══════════════════════════════════════════════════════════════════════
# Phenotype (2)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class PhenotypeObserved(DomainEvent):
    event_type: str = "PHENOTYPE_OBSERVED"

    phenotype_code: str = ""
    observed_by: str = ""
    severity: str = ""
    onset_date: Optional[str] = None
    linked_diagnosis_ids: Optional[List[str]] = None
    context: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["phenotype_code"] = self.phenotype_code
        p["observed_by"] = self.observed_by
        p["severity"] = self.severity
        if self.onset_date is not None:
            p["onset_date"] = self.onset_date
        if self.linked_diagnosis_ids is not None:
            p["linked_diagnosis_ids"] = self.linked_diagnosis_ids
        if self.context is not None:
            p["context"] = self.context
        return p


@dataclass(frozen=True)
class PhenotypeResolved(DomainEvent):
    event_type: str = "PHENOTYPE_RESOLVED"

    resolved_by: str = ""
    resolution_date: Optional[str] = None
    reason: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["resolved_by"] = self.resolved_by
        if self.resolution_date is not None:
            p["resolution_date"] = self.resolution_date
        if self.reason is not None:
            p["reason"] = self.reason
        return p


# ═══════════════════════════════════════════════════════════════════════
# Assessment (2)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AssessmentApplied(DomainEvent):
    event_type: str = "ASSESSMENT_APPLIED"

    scale_code: str = ""
    scale_version: str = ""
    applied_by: str = ""
    raw_responses: Dict[str, Any] = field(default_factory=dict)
    computed_scores: Dict[str, Any] = field(default_factory=dict)
    interpretation: Optional[Dict[str, Any]] = None
    linked_diagnosis_ids: Optional[List[str]] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["scale_code"] = self.scale_code
        p["scale_version"] = self.scale_version
        p["applied_by"] = self.applied_by
        p["raw_responses"] = dict(self.raw_responses)
        p["computed_scores"] = dict(self.computed_scores)
        if self.interpretation is not None:
            p["interpretation"] = self.interpretation
        if self.linked_diagnosis_ids is not None:
            p["linked_diagnosis_ids"] = self.linked_diagnosis_ids
        return p


@dataclass(frozen=True)
class AssessmentUpdated(DomainEvent):
    event_type: str = "ASSESSMENT_UPDATED"

    updated_by: str = ""
    raw_responses: Dict[str, Any] = field(default_factory=dict)
    computed_scores: Dict[str, Any] = field(default_factory=dict)
    interpretation: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["updated_by"] = self.updated_by
        p["raw_responses"] = dict(self.raw_responses)
        p["computed_scores"] = dict(self.computed_scores)
        if self.interpretation is not None:
            p["interpretation"] = self.interpretation
        if self.reason is not None:
            p["reason"] = self.reason
        return p


# ═══════════════════════════════════════════════════════════════════════
# Intervention (5)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class InterventionStarted(DomainEvent):
    event_type: str = "INTERVENTION_STARTED"

    intervention_type: str = ""
    subtype: str = ""
    started_by: str = ""
    start_date: str = ""
    dose: Optional[Dict[str, Any]] = None
    indication_condition_code: Optional[str] = None
    linked_diagnosis_ids: Optional[List[str]] = None
    prescriber_id: Optional[str] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["intervention_type"] = self.intervention_type
        p["subtype"] = self.subtype
        p["started_by"] = self.started_by
        p["start_date"] = self.start_date
        if self.dose is not None:
            p["dose"] = self.dose
        if self.indication_condition_code is not None:
            p["indication_condition_code"] = self.indication_condition_code
        if self.linked_diagnosis_ids is not None:
            p["linked_diagnosis_ids"] = self.linked_diagnosis_ids
        if self.prescriber_id is not None:
            p["prescriber_id"] = self.prescriber_id
        if self.notes is not None:
            p["notes"] = self.notes
        return p


@dataclass(frozen=True)
class InterventionAdjusted(DomainEvent):
    event_type: str = "INTERVENTION_ADJUSTED"

    adjusted_by: str = ""
    previous_dose: Optional[Dict[str, Any]] = None
    new_dose: Dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["adjusted_by"] = self.adjusted_by
        if self.previous_dose is not None:
            p["previous_dose"] = self.previous_dose
        p["new_dose"] = dict(self.new_dose)
        p["reason"] = self.reason
        return p


@dataclass(frozen=True)
class InterventionPaused(DomainEvent):
    event_type: str = "INTERVENTION_PAUSED"

    paused_by: str = ""
    reason: str = ""
    expected_resume_date: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["paused_by"] = self.paused_by
        p["reason"] = self.reason
        if self.expected_resume_date is not None:
            p["expected_resume_date"] = self.expected_resume_date
        return p


@dataclass(frozen=True)
class InterventionResumed(DomainEvent):
    event_type: str = "INTERVENTION_RESUMED"

    resumed_by: str = ""
    resume_date: str = ""
    new_dose: Optional[Dict[str, Any]] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["resumed_by"] = self.resumed_by
        p["resume_date"] = self.resume_date
        if self.new_dose is not None:
            p["new_dose"] = self.new_dose
        return p


@dataclass(frozen=True)
class InterventionStopped(DomainEvent):
    event_type: str = "INTERVENTION_STOPPED"

    stopped_by: str = ""
    end_date: str = ""
    reason: str = ""
    outcome_summary: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["stopped_by"] = self.stopped_by
        p["end_date"] = self.end_date
        p["reason"] = self.reason
        if self.outcome_summary is not None:
            p["outcome_summary"] = self.outcome_summary
        return p


# ═══════════════════════════════════════════════════════════════════════
# Outcome (6)
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class OutcomeImprovement(DomainEvent):
    event_type: str = "OUTCOME_IMPROVEMENT"

    observed_by: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    intervention_id: Optional[str] = None
    magnitude: Optional[str] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["observed_by"] = self.observed_by
        p["evidence"] = dict(self.evidence)
        if self.intervention_id is not None:
            p["intervention_id"] = self.intervention_id
        if self.magnitude is not None:
            p["magnitude"] = self.magnitude
        if self.notes is not None:
            p["notes"] = self.notes
        return p


@dataclass(frozen=True)
class OutcomeWorsening(DomainEvent):
    event_type: str = "OUTCOME_WORSENING"

    observed_by: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    intervention_id: Optional[str] = None
    magnitude: Optional[str] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["observed_by"] = self.observed_by
        p["evidence"] = dict(self.evidence)
        if self.intervention_id is not None:
            p["intervention_id"] = self.intervention_id
        if self.magnitude is not None:
            p["magnitude"] = self.magnitude
        if self.notes is not None:
            p["notes"] = self.notes
        return p


@dataclass(frozen=True)
class OutcomePartialResponse(DomainEvent):
    event_type: str = "OUTCOME_PARTIAL_RESPONSE"

    observed_by: str = ""
    intervention_id: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    responding_domains: Optional[List[str]] = None
    non_responding_domains: Optional[List[str]] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["observed_by"] = self.observed_by
        p["intervention_id"] = self.intervention_id
        p["evidence"] = dict(self.evidence)
        if self.responding_domains is not None:
            p["responding_domains"] = self.responding_domains
        if self.non_responding_domains is not None:
            p["non_responding_domains"] = self.non_responding_domains
        if self.notes is not None:
            p["notes"] = self.notes
        return p


@dataclass(frozen=True)
class OutcomeRemission(DomainEvent):
    event_type: str = "OUTCOME_REMISSION"

    observed_by: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    duration_months: Optional[int] = None
    intervention_id: Optional[str] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["observed_by"] = self.observed_by
        p["evidence"] = dict(self.evidence)
        if self.duration_months is not None:
            p["duration_months"] = self.duration_months
        if self.intervention_id is not None:
            p["intervention_id"] = self.intervention_id
        if self.notes is not None:
            p["notes"] = self.notes
        return p


@dataclass(frozen=True)
class OutcomeAdverseEvent(DomainEvent):
    event_type: str = "OUTCOME_ADVERSE_EVENT"

    observed_by: str = ""
    severity: str = ""
    description: str = ""
    intervention_id: Optional[str] = None
    causality: Optional[str] = None
    action_taken: Optional[str] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["observed_by"] = self.observed_by
        p["severity"] = self.severity
        p["description"] = self.description
        if self.intervention_id is not None:
            p["intervention_id"] = self.intervention_id
        if self.causality is not None:
            p["causality"] = self.causality
        if self.action_taken is not None:
            p["action_taken"] = self.action_taken
        if self.notes is not None:
            p["notes"] = self.notes
        return p


@dataclass(frozen=True)
class OutcomeNoChange(DomainEvent):
    event_type: str = "OUTCOME_NO_CHANGE"

    observed_by: str = ""
    intervention_id: Optional[str] = None
    duration_observed_months: Optional[int] = None
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        p = super().to_payload()
        p["observed_by"] = self.observed_by
        if self.intervention_id is not None:
            p["intervention_id"] = self.intervention_id
        if self.duration_observed_months is not None:
            p["duration_observed_months"] = self.duration_observed_months
        if self.notes is not None:
            p["notes"] = self.notes
        return p