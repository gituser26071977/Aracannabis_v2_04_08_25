"""
RegistryBuilder — fluent factory para ClinicalIdentity + entidades filhas.

Permite construir cenários clínicos completos em poucos linhas:

    fixture = (RegistryBuilder()
               .with_tenant("t1")
               .with_patient("p1")
               .with_identity()
               .with_diagnosis(condition_code="TEA_F84.0", state="confirmed")
               .with_phenotype(code="social_deficit", severity="moderate")
               .with_medication(subtype="risperidona", state="started",
                                dose_value=0.5, dose_unit="mg", dose_frequency="bid")
               .with_intervention(subtype="aba_therapy", state="started")
               .with_assessment(scale_code="MCHAT_R_F")
               .with_outcome(type="improvement")
               .build())

    # fixture.identity_id, fixture.diagnoses, fixture.events, fixture.identity_payload

Uso principal: testes que precisam de uma "fotografia clínica" rica,
sem repetir boilerplate de criação de cada entidade.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .event_builder import build_clinical_event


# ─── Helpers ───────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


# ─── Fixture ──────────────────────────────────────────────────────────────


@dataclass
class RegistryFixture:
    """Resultado imutável do build — pronto para aplicar em Event Store + Projection."""

    tenant_id: str
    patient_id: str
    identity_id: str
    events: List[Dict[str, Any]]
    diagnoses: List[Dict[str, Any]] = field(default_factory=list)
    phenotypes: List[Dict[str, Any]] = field(default_factory=list)
    interventions: List[Dict[str, Any]] = field(default_factory=list)
    assessments: List[Dict[str, Any]] = field(default_factory=list)
    outcomes: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def all_aggregate_ids(self) -> List[str]:
        ids = [self.identity_id]
        ids.extend(d["aggregate_id"] for d in self.diagnoses)
        ids.extend(p["aggregate_id"] for p in self.phenotypes)
        ids.extend(i["aggregate_id"] for i in self.interventions)
        ids.extend(a["aggregate_id"] for a in self.assessments)
        ids.extend(o["aggregate_id"] for o in self.outcomes)
        return ids

    def find_event_by_type(self, event_type: str) -> Optional[Dict[str, Any]]:
        for e in self.events:
            if e["event_type"] == event_type:
                return e
        return None


# ─── Builder ──────────────────────────────────────────────────────────────


class RegistryBuilder:
    """Fluent builder para cenários clínicos completos."""

    def __init__(self) -> None:
        self._tenant_id: str = "tenant-test"
        self._patient_id: str = f"patient-{uuid.uuid4().hex[:8]}"
        self._identity_id: str = f"identity-{uuid.uuid4().hex[:8]}"
        self._actor_id: str = "prof-test"
        self._events: List[Dict[str, Any]] = []
        self._diagnoses: List[Dict[str, Any]] = []
        self._phenotypes: List[Dict[str, Any]] = []
        self._interventions: List[Dict[str, Any]] = []
        self._assessments: List[Dict[str, Any]] = []
        self._outcomes: List[Dict[str, Any]] = []
        self._sequence: int = 0

    # ─── Setup ────────────────────────────────────────────────────────

    def with_tenant(self, tenant_id: str) -> "RegistryBuilder":
        self._tenant_id = tenant_id
        return self

    def with_patient(self, patient_id: str) -> "RegistryBuilder":
        self._patient_id = patient_id
        return self

    def with_actor(self, actor_id: str) -> "RegistryBuilder":
        self._actor_id = actor_id
        return self

    def with_identity_id(self, identity_id: str) -> "RegistryBuilder":
        self._identity_id = identity_id
        return self

    def with_sequence_start(self, start: int) -> "RegistryBuilder":
        self._sequence = start
        return self

    # ─── Identity ─────────────────────────────────────────────────────

    def with_identity(
        self,
        patient_id: Optional[str] = None,
        initial_notes: Optional[str] = None,
    ) -> "RegistryBuilder":
        """Cria ClinicalIdentity (sempre 1º evento)."""
        pid = patient_id or self._patient_id
        evt = self._emit(
            event_type="CLINICAL_IDENTITY_CREATED",
            aggregate_type="clinical_identity",
            aggregate_id=self._identity_id,
            payload={
                "patient_id": pid,
                "identity_id": self._identity_id,
                **({"initial_notes": initial_notes} if initial_notes else {}),
            },
        )
        return self

    # ─── Diagnosis ────────────────────────────────────────────────────

    def with_diagnosis(
        self,
        condition_code: str = "TEA_F84.0",
        state: str = "confirmed",
        severity: Optional[str] = "moderate",
        onset_date: Optional[str] = None,
        include_cid10: bool = True,
        include_dsm5: bool = True,
    ) -> "RegistryBuilder":
        """
        Cria diagnosis no estado especificado.

        state ∈ {"hypothesis", "investigating", "confirmed", "revised",
                 "in_remission", "discarded"}

        Gera os eventos intermediários necessários para chegar ao estado.
        Ex.: state="confirmed" → emite HYPOTHESIZED + CONFIRMED.
        """
        diag_id = f"diag-{uuid.uuid4().hex[:8]}"

        # 1. HYPOTHESIZED (com classification inicial se confirmado/revised)
        initial_classification: Optional[Dict[str, Any]] = None
        if state in ("confirmed", "revised", "in_remission") and include_cid10:
            initial_classification = {
                "entries": [
                    {
                        "type": "cid10",
                        "code": self._cid10_from_condition(condition_code),
                        "is_primary": True,
                        "added_in_event_id": "placeholder",
                    }
                ]
            }
            if include_dsm5:
                initial_classification["entries"].append(
                    {
                        "type": "dsm5_tr",
                        "code": self._dsm5_from_condition(condition_code),
                        "is_primary": False,
                        "added_in_event_id": "placeholder",
                    }
                )

        self._emit(
            event_type="DIAGNOSIS_HYPOTHESIZED",
            aggregate_type="diagnosis",
            aggregate_id=diag_id,
            payload={
                "identity_id": self._identity_id,
                "condition_code": condition_code,
                "hypothesised_by": self._actor_id,
                "reason": f"Builder: hipótese de {condition_code}",
                "onset_date": onset_date,
                **(
                    {"classification": initial_classification}
                    if initial_classification
                    else {}
                ),
            },
        )

        # 2. INVESTIGATING (se necessário)
        if state == "investigating":
            self._emit(
                event_type="DIAGNOSIS_INVESTIGATING",
                aggregate_type="diagnosis",
                aggregate_id=diag_id,
                payload={
                    "identity_id": self._identity_id,
                    "investigation_plan": "Coleta de evidência padrão",
                    "expected_evidence": ["ADI-R", "ADOS-2"],
                },
            )

        # 3. CONFIRMED (com evidence)
        if state in ("confirmed", "revised", "in_remission"):
            self._emit(
                event_type="DIAGNOSIS_CONFIRMED",
                aggregate_type="diagnosis",
                aggregate_id=diag_id,
                payload={
                    "identity_id": self._identity_id,
                    "confirmed_by": self._actor_id,
                    "confirmation_evidence": {
                        "assessment_ids": ["assess-builder-1"],
                        "criteria_met": ["A1", "A2", "B1", "B3"],
                        "clinical_notes": f"Builder: confirmação de {condition_code}",
                    },
                    "severity": severity,
                },
            )

        # 4. REVISED
        if state == "revised":
            new_code = "TDAH_F90.0"
            self._emit(
                event_type="DIAGNOSIS_REVISED",
                aggregate_type="diagnosis",
                aggregate_id=diag_id,
                payload={
                    "identity_id": self._identity_id,
                    "previous_condition_code": condition_code,
                    "new_condition_code": new_code,
                    "revised_by": self._actor_id,
                    "reason": "Builder: revisão para TDAH",
                },
            )

        # 5. IN_REMISSION
        if state == "in_remission":
            self._emit(
                event_type="DIAGNOSIS_IN_REMISSION",
                aggregate_type="diagnosis",
                aggregate_id=diag_id,
                payload={
                    "identity_id": self._identity_id,
                    "remission_type": "partial",
                    "marked_by": self._actor_id,
                    "evidence": {"assessment_ids": ["assess-builder-1"]},
                },
            )

        # 6. DISCARDED
        if state == "discarded":
            self._emit(
                event_type="DIAGNOSIS_DISCARDED",
                aggregate_type="diagnosis",
                aggregate_id=diag_id,
                payload={
                    "identity_id": self._identity_id,
                    "discarded_by": self._actor_id,
                    "reason": "Builder: hipótese descartada",
                },
            )

        self._diagnoses.append(
            {
                "aggregate_id": diag_id,
                "condition_code": condition_code,
                "state": state,
            }
        )
        return self

    # ─── Phenotype ────────────────────────────────────────────────────

    def with_phenotype(
        self,
        code: str = "social_deficit",
        severity: str = "moderate",
        resolved: bool = False,
    ) -> "RegistryBuilder":
        """Cria phenotype (opcionalmente resolve)."""
        phen_id = f"phen-{uuid.uuid4().hex[:8]}"
        self._emit(
            event_type="PHENOTYPE_OBSERVED",
            aggregate_type="phenotype",
            aggregate_id=phen_id,
            payload={
                "identity_id": self._identity_id,
                "phenotype_code": code,
                "observed_by": self._actor_id,
                "severity": severity,
                "context": "Builder: observação padrão",
            },
        )
        if resolved:
            self._emit(
                event_type="PHENOTYPE_RESOLVED",
                aggregate_type="phenotype",
                aggregate_id=phen_id,
                payload={
                    "identity_id": self._identity_id,
                    "resolved_by": self._actor_id,
                    "reason": "Builder: resolução",
                },
            )
        self._phenotypes.append(
            {"aggregate_id": phen_id, "phenotype_code": code, "is_resolved": resolved}
        )
        return self

    # ─── Intervention ─────────────────────────────────────────────────

    def with_medication(
        self,
        subtype: str = "risperidona",
        state: str = "started",
        dose_value: Optional[float] = 0.5,
        dose_unit: Optional[str] = "mg",
        dose_frequency: Optional[str] = "bid",
        indication: Optional[str] = "TEA_F84.0",
    ) -> "RegistryBuilder":
        """Atalho semântico: intervention tipo MEDICATION."""
        return self.with_intervention(
            intervention_type="MEDICATION",
            subtype=subtype,
            state=state,
            dose_value=dose_value,
            dose_unit=dose_unit,
            dose_frequency=dose_frequency,
            indication=indication,
        )

    def with_intervention(
        self,
        intervention_type: str = "MEDICATION",
        subtype: str = "risperidona",
        state: str = "started",
        dose_value: Optional[float] = None,
        dose_unit: Optional[str] = None,
        dose_frequency: Optional[str] = None,
        indication: Optional[str] = None,
    ) -> "RegistryBuilder":
        """
        Cria intervention. state ∈ {started, adjusted, paused, resumed, stopped}.

        intervention_type ∈ {MEDICATION, CANNABIS, ABA, TO, FONO, ...} — ver
        araos.specialties.neurodevelopmental.domain.intervention.InterventionType.
        """
        int_id = f"int-{uuid.uuid4().hex[:8]}"

        if state == "started":
            dose_payload = None
            if dose_value is not None:
                dose_payload = {
                    "value": dose_value,
                    "unit": dose_unit,
                    "frequency": dose_frequency,
                }
            self._emit(
                event_type="INTERVENTION_STARTED",
                aggregate_type="intervention",
                aggregate_id=int_id,
                payload={
                    "identity_id": self._identity_id,
                    "intervention_type": intervention_type,
                    "subtype": subtype,
                    "started_by": self._actor_id,
                    "start_date": _now_iso(),
                    **({"dose": dose_payload} if dose_payload else {}),
                    **(
                        {"indication_condition_code": indication}
                        if indication
                        else {}
                    ),
                },
            )
        elif state == "stopped":
            self._emit(
                event_type="INTERVENTION_STOPPED",
                aggregate_type="intervention",
                aggregate_id=int_id,
                payload={
                    "identity_id": self._identity_id,
                    "stopped_by": self._actor_id,
                    "end_date": _now_iso(),
                    "reason": "Builder: parada programada",
                },
            )

        self._interventions.append(
            {
                "aggregate_id": int_id,
                "intervention_type": intervention_type,
                "subtype": subtype,
                "state": state,
            }
        )
        return self

    # ─── Assessment ───────────────────────────────────────────────────

    def with_assessment(
        self,
        scale_code: str = "MCHAT_R_F",
        scale_version: str = "2024-01",
        computed_score: Optional[float] = 8.0,
    ) -> "RegistryBuilder":
        """Cria assessment."""
        assess_id = f"assess-{uuid.uuid4().hex[:8]}"
        self._emit(
            event_type="ASSESSMENT_APPLIED",
            aggregate_type="assessment",
            aggregate_id=assess_id,
            payload={
                "identity_id": self._identity_id,
                "scale_code": scale_code,
                "scale_version": scale_version,
                "applied_by": self._actor_id,
                "raw_responses": {"q1": 1, "q2": 0, "q3": 1},
                "computed_scores": (
                    {"total": computed_score} if computed_score is not None else {}
                ),
                "interpretation": {"risk_level": "elevated"},
            },
        )
        self._assessments.append(
            {
                "aggregate_id": assess_id,
                "scale_code": scale_code,
            }
        )
        return self

    # ─── Outcome ──────────────────────────────────────────────────────

    def with_outcome(
        self,
        type: str = "improvement",
        magnitude: Optional[str] = "moderate",
        intervention_id: Optional[str] = None,
    ) -> "RegistryBuilder":
        """
        Cria outcome. type ∈ {improvement, worsening, partial_response,
        remission, adverse_event, no_change}.
        """
        out_id = f"out-{uuid.uuid4().hex[:8]}"
        target_int = intervention_id
        if target_int is None and self._interventions:
            target_int = self._interventions[-1]["aggregate_id"]

        base_payload: Dict[str, Any] = {
            "identity_id": self._identity_id,
            "observed_by": self._actor_id,
            "intervention_id": target_int,
        }

        event_type_map = {
            "improvement": "OUTCOME_IMPROVEMENT",
            "worsening": "OUTCOME_WORSENING",
            "partial_response": "OUTCOME_PARTIAL_RESPONSE",
            "remission": "OUTCOME_REMISSION",
            "adverse_event": "OUTCOME_ADVERSE_EVENT",
            "no_change": "OUTCOME_NO_CHANGE",
        }
        et = event_type_map[type]

        if type == "adverse_event":
            base_payload.update(
                {
                    "severity": "mild",
                    "description": "Builder: evento adverso leve",
                    "causality": "possible",
                }
            )
        elif type in ("improvement", "worsening"):
            base_payload.update(
                {
                    "evidence": {"assessment_ids": ["assess-builder-1"]},
                    **({"magnitude": magnitude} if magnitude else {}),
                }
            )
        elif type == "partial_response":
            base_payload.update(
                {
                    "evidence": {"assessment_ids": ["assess-builder-1"]},
                    "responding_domains": ["social", "communication"],
                    "non_responding_domains": ["sensory"],
                }
            )
        elif type == "remission":
            base_payload.update(
                {
                    "evidence": {"assessment_ids": ["assess-builder-1"]},
                    "duration_months": 12,
                }
            )
        elif type == "no_change":
            base_payload["duration_observed_months"] = 6

        self._emit(
            event_type=et,
            aggregate_type="outcome",
            aggregate_id=out_id,
            payload=base_payload,
        )
        self._outcomes.append({"aggregate_id": out_id, "type": type})
        return self

    # ─── Build ────────────────────────────────────────────────────────

    def build(self) -> RegistryFixture:
        """Emite a fixture com identidade obrigatória."""
        if not any(e["event_type"] == "CLINICAL_IDENTITY_CREATED" for e in self._events):
            self.with_identity()
        return RegistryFixture(
            tenant_id=self._tenant_id,
            patient_id=self._patient_id,
            identity_id=self._identity_id,
            events=list(self._events),
            diagnoses=list(self._diagnoses),
            phenotypes=list(self._phenotypes),
            interventions=list(self._interventions),
            assessments=list(self._assessments),
            outcomes=list(self._outcomes),
        )

    # ─── Internals ────────────────────────────────────────────────────

    def _emit(
        self,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        evt = build_clinical_event(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            tenant_id=self._tenant_id,
            patient_id=self._patient_id,
            sequence=self._sequence,
            payload=payload,
            actor_id=self._actor_id,
        )
        self._sequence += 1
        self._events.append(evt)
        return evt

    @staticmethod
    def _cid10_from_condition(condition_code: str) -> str:
        """Extrai CID-10 a partir do ConditionCode (formato TEA_F84.0 → F84.0)."""
        if "_" in condition_code:
            _, code = condition_code.split("_", 1)
            return code
        return condition_code

    @staticmethod
    def _dsm5_from_condition(condition_code: str) -> str:
        """Mapeia ConditionCode para DSM-5-TR aproximado (placeholder)."""
        mapping = {
            "TEA_F84.0": "299.00",
            "TEA_F84.5": "299.00",
            "TDAH_F90.0": "314.01",
            "ANSIEDADE_F41.1": "309.21",
            "DISLEXIA_F81.0": "315.00",
        }
        return mapping.get(condition_code, "315.00")  # default: unspecified
