"""
AraOS Clinical Event Engine — Catalog.

Catálogo versionado de `event_type` do Clinical Event Engine (ADR-0001).

Complementa o catálogo global `araos.platform.events.catalog._EVENT_CATALOG`
com eventos específicos do motor clínico cross-specialty.

Cada entrada carrega:
    - event_type: identificador único
    - domain: 'clinical' (cross-specialty)
    - producer: source_module que tipicamente produz
    - description: human-readable
    - version: schema version do payload
    - json_schema: JSON Schema Draft 7 do payload (opcional)
    - status: 'active' | 'deprecated'
    - consumers: lista de consumer groups esperados
    - sensitive: True se contém dados sensíveis (LGPD)

Adicionar novo evento = 1 entrada abaixo. Zero migração Alembic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventStatus(str, Enum):
    """Status do tipo de evento no catálogo."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class EventProducer(str, Enum):
    """Produtor típico do evento (source_module)."""
    CORE = "core"
    NEURODEVELOPMENTAL = "neurodevelopmental"
    CANNABIS = "cannabis"
    PHYSIOTHERAPY = "physiotherapy"
    SPEECH_THERAPY = "speech_therapy"
    OCCUPATIONAL_THERAPY = "occupational_therapy"
    PSYCHOLOGY = "psychology"
    PSYCHIATRY = "psychiatry"
    INTERNAL_MEDICINE = "internal_medicine"
    ICU = "icu"
    PAIN = "pain"
    SLEEP = "sleep"
    REHABILITATION = "rehabilitation"

    # ─── Sprint 4 — Clinical Intelligence Platform ──────────────────
    INTELLIGENCE = "intelligence"


@dataclass(frozen=True)
class ClinicalEventDefinition:
    """Definição canônica de um event_type no Clinical Event Engine."""
    event_type: str
    domain: str
    producer: str
    description: str
    version: str = "1.0"
    json_schema: Dict[str, Any] = field(default_factory=dict)
    status: EventStatus = EventStatus.ACTIVE
    consumers: List[str] = field(default_factory=list)
    sensitive: bool = True


# ═══════════════════════════════════════════════════════════════════════
# CATÁLOGO OFICIAL — CLINICAL EVENT ENGINE (ADR-0001)
# ═══════════════════════════════════════════════════════════════════════

CLINICAL_EVENT_CATALOG: Dict[str, ClinicalEventDefinition] = {

    # ─── PACIENTE ────────────────────────────────────────────────────
    "PATIENT_CREATED": ClinicalEventDefinition(
        event_type="PATIENT_CREATED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Paciente cadastrado",
        consumers=["audit", "knowledge", "concierge"],
    ),
    "PATIENT_UPDATED": ClinicalEventDefinition(
        event_type="PATIENT_UPDATED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Dados do paciente atualizados",
        consumers=["audit", "knowledge"],
    ),

    # ─── DIAGNÓSTICO ─────────────────────────────────────────────────
    "DIAGNOSIS_ADDED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_ADDED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Diagnóstico adicionado (multi-CID-10/CID-11/DSM-5-TR)",
        consumers=["audit", "timeline", "knowledge", "observatory_etl"],
    ),
    "DIAGNOSIS_REMOVED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_REMOVED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Diagnóstico removido (correção ou descarte)",
        consumers=["audit", "timeline"],
    ),
    "DIAGNOSIS_UPDATED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_UPDATED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Diagnóstico atualizado (correção de metadata)",
        consumers=["audit", "timeline"],
    ),
    "DIAGNOSIS_STATUS_CHANGED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_STATUS_CHANGED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description=(
            "Status do diagnóstico alterado: hipótese, confirmado, "
            "descartado, histórico"
        ),
        consumers=["audit", "timeline"],
    ),

    # ─── ESCALAS ─────────────────────────────────────────────────────
    "SCALE_APPLIED": ClinicalEventDefinition(
        event_type="SCALE_APPLIED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Escala neuropsicológica aplicada",
        consumers=["audit", "timeline", "knowledge", "observatory_etl"],
    ),
    "SCALE_UPDATED": ClinicalEventDefinition(
        event_type="SCALE_UPDATED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Resposta de escala atualizada/corrigida",
        consumers=["audit", "timeline"],
    ),

    # ─── MEDICAÇÕES ──────────────────────────────────────────────────
    "MEDICATION_STARTED": ClinicalEventDefinition(
        event_type="MEDICATION_STARTED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Medicação iniciada",
        consumers=["audit", "timeline", "dashboard_cache"],
    ),
    "MEDICATION_ADJUSTED": ClinicalEventDefinition(
        event_type="MEDICATION_ADJUSTED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Medicação ajustada (dose, concentração, frequência)",
        consumers=["audit", "timeline"],
    ),
    "MEDICATION_STOPPED": ClinicalEventDefinition(
        event_type="MEDICATION_STOPPED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Medicação suspensa",
        consumers=["audit", "timeline"],
    ),

    # ─── CANNABIS MEDICINAL ──────────────────────────────────────────
    "CANNABIS_ADJUSTED": ClinicalEventDefinition(
        event_type="CANNABIS_ADJUSTED",
        domain="clinical",
        producer=EventProducer.CANNABIS.value,
        description="Regime de cannabis medicinal ajustado",
        consumers=["audit", "timeline"],
    ),

    # ─── TERAPIAS ────────────────────────────────────────────────────
    "THERAPY_STARTED": ClinicalEventDefinition(
        event_type="THERAPY_STARTED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description=(
            "Terapia iniciada: ABA, TO, Fono, Psicologia, "
            "Musicoterapia, Equoterapia, etc."
        ),
        consumers=["audit", "timeline"],
    ),
    "THERAPY_FINISHED": ClinicalEventDefinition(
        event_type="THERAPY_FINISHED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Terapia finalizada",
        consumers=["audit", "timeline"],
    ),

    # ─── CONTEXTO DE VIDA ────────────────────────────────────────────
    "SCHOOL_CHANGED": ClinicalEventDefinition(
        event_type="SCHOOL_CHANGED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Mudança escolar registrada",
        consumers=["audit", "timeline"],
    ),
    "SLEEP_CHANGED": ClinicalEventDefinition(
        event_type="SLEEP_CHANGED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Mudança de padrão de sono (latência, eficiência, despertares)",
        consumers=["audit", "timeline", "phenotypes"],
    ),
    "WEIGHT_CHANGED": ClinicalEventDefinition(
        event_type="WEIGHT_CHANGED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Mudança de peso (kg)",
        consumers=["audit", "timeline", "phenotypes"],
    ),
    "HEIGHT_CHANGED": ClinicalEventDefinition(
        event_type="HEIGHT_CHANGED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Mudança de altura (cm)",
        consumers=["audit", "timeline", "phenotypes"],
    ),

    # ─── EVENTOS CRÍTICOS ────────────────────────────────────────────
    "CRISIS_RECORDED": ClinicalEventDefinition(
        event_type="CRISIS_RECORDED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Crise comportamental registrada",
        consumers=["audit", "timeline", "observatory_etl"],
    ),
    "HOSPITALIZATION": ClinicalEventDefinition(
        event_type="HOSPITALIZATION",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Internação registrada",
        consumers=["audit", "timeline", "observatory_etl"],
    ),
    "SURGERY": ClinicalEventDefinition(
        event_type="SURGERY",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Cirurgia registrada",
        consumers=["audit", "timeline"],
    ),

    # ─── EXAMES ──────────────────────────────────────────────────────
    "LABORATORY_RESULT": ClinicalEventDefinition(
        event_type="LABORATORY_RESULT",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Resultado laboratorial",
        consumers=["audit", "timeline"],
    ),
    "IMAGING_RESULT": ClinicalEventDefinition(
        event_type="IMAGING_RESULT",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Resultado de imagem (ressonância, tomografia, etc.)",
        consumers=["audit", "timeline"],
    ),

    # ─── ATENDIMENTO ─────────────────────────────────────────────────
    "CONSULTATION_PERFORMED": ClinicalEventDefinition(
        event_type="CONSULTATION_PERFORMED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Consulta realizada",
        consumers=["audit", "timeline", "knowledge"],
    ),
    "FAMILY_MEETING": ClinicalEventDefinition(
        event_type="FAMILY_MEETING",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Reunião familiar realizada",
        consumers=["audit", "timeline"],
    ),
    "CARE_PLAN_UPDATED": ClinicalEventDefinition(
        event_type="CARE_PLAN_UPDATED",
        domain="clinical",
        producer=EventProducer.CORE.value,
        description="Plano de cuidado atualizado",
        consumers=["audit", "timeline"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # SPRINT 3.2 — CLINICAL IDENTITY & NEURODEVELOPMENTAL REGISTRY
    # (ADR-0002)
    # Domain Events para DDD — ClinicalIdentity + 6 entidades
    # ═══════════════════════════════════════════════════════════════════

    # ─── Clinical Identity ────────────────────────────────────────────
    "CLINICAL_IDENTITY_CREATED": ClinicalEventDefinition(
        event_type="CLINICAL_IDENTITY_CREATED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Identidade clínica longitudinal criada para o paciente. "
            "Aggregate root permanente — sobrevive a todas as mudanças clínicas."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["patient_id"],
            "properties": {
                "patient_id": {"type": "string", "minLength": 1},
                "initial_notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection"],
    ),
    "CLINICAL_IDENTITY_ARCHIVED": ClinicalEventDefinition(
        event_type="CLINICAL_IDENTITY_ARCHIVED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Identidade clínica arquivada. Não deleta — histórico permanece. "
            "Significa 'paciente não está mais em acompanhamento'."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["reason"],
            "properties": {
                "reason": {
                    "type": "string",
                    "enum": [
                        "patient_transferred",
                        "patient_deceased",
                        "patient_discharged",
                        "administrative",
                        "other",
                    ],
                },
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection"],
    ),

    # ─── Diagnosis — 6 estados evolutivos ─────────────────────────────
    "DIAGNOSIS_HYPOTHESIZED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_HYPOTHESIZED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Hipótese diagnóstica formulada. Estado inicial do Diagnosis. "
            "Requer pelo menos um condition_code."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["condition_code", "hypothesised_by"],
            "properties": {
                "condition_code": {"type": "string", "minLength": 1},
                "hypothesised_by": {"type": "string", "minLength": 1},
                "reason": {"type": "string"},
                "onset_date": {"type": "string", "format": "date"},
                "classification": {
                    "type": "object",
                    "properties": {
                        "cid10": {"type": "string", "pattern": "^[A-Z]\\d{2}(\\.\\d)?$"},
                        "cid11": {"type": "string"},
                        "dsm5_tr": {"type": "string"},
                        "internal": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "DIAGNOSIS_INVESTIGATING": ClinicalEventDefinition(
        event_type="DIAGNOSIS_INVESTIGATING",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Diagnóstico em investigação ativa. Transição de HYPOTHESIS "
            "para coleta de evidência."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["investigation_plan"],
            "properties": {
                "investigation_plan": {"type": "string", "minLength": 1},
                "expected_evidence": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "DIAGNOSIS_CONFIRMED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_CONFIRMED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Diagnóstico confirmado com evidência. Invariante: "
            "confirmation_evidence não pode ser vazio."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["confirmed_by", "confirmation_evidence"],
            "properties": {
                "confirmed_by": {"type": "string", "minLength": 1},
                "confirmation_evidence": {
                    "type": "object",
                    "minProperties": 1,
                    "properties": {
                        "assessment_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "exam_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "clinical_criteria_met": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "notes": {"type": "string"},
                    },
                },
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe", "profound"],
                },
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline", "observatory_etl"],
    ),
    "DIAGNOSIS_REVISED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_REVISED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Diagnóstico revisado. Mudança de condição ou severidade. "
            "Não deleta o anterior — gera novo evento."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["new_condition_code", "revised_by", "reason"],
            "properties": {
                "new_condition_code": {"type": "string", "minLength": 1},
                "previous_condition_code": {"type": "string"},
                "revised_by": {"type": "string", "minLength": 1},
                "reason": {"type": "string", "minLength": 1},
                "new_classification": {
                    "type": "object",
                    "properties": {
                        "cid10": {"type": "string"},
                        "cid11": {"type": "string"},
                        "dsm5_tr": {"type": "string"},
                    },
                },
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "DIAGNOSIS_IN_REMISSION": ClinicalEventDefinition(
        event_type="DIAGNOSIS_IN_REMISSION",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Diagnóstico em remissão (parcial ou total). Não deleta — "
            "pode haver recidiva futura."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["remission_type", "marked_by"],
            "properties": {
                "remission_type": {
                    "type": "string",
                    "enum": ["partial", "complete"],
                },
                "marked_by": {"type": "string", "minLength": 1},
                "evidence": {
                    "type": "object",
                    "properties": {
                        "assessment_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "duration_months": {"type": "integer", "minimum": 0},
                    },
                },
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "DIAGNOSIS_DISCARDED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_DISCARDED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Diagnóstico descartado (hipótese rejeitada, erro diagnóstico). "
            "Histórico permanece — apenas estado final muda."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["discarded_by", "reason"],
            "properties": {
                "discarded_by": {"type": "string", "minLength": 1},
                "reason": {
                    "type": "string",
                    "enum": [
                        "no_evidence",
                        "alternative_diagnosis",
                        "diagnostic_error",
                        "patient_recovery",
                        "other",
                    ],
                },
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "DIAGNOSIS_CLASSIFICATION_ADDED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_CLASSIFICATION_ADDED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Classificação adicional (CID/DSM/SNOMED) adicionada ao "
            "diagnóstico. Multi-classificação simultânea permitida."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["classification_type", "code", "added_by"],
            "properties": {
                "classification_type": {
                    "type": "string",
                    "enum": ["cid10", "cid11", "dsm5_tr", "snomed", "internal"],
                },
                "code": {"type": "string", "minLength": 1},
                "added_by": {"type": "string", "minLength": 1},
                "is_primary": {"type": "boolean"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection"],
    ),
    "DIAGNOSIS_CLASSIFICATION_REMOVED": ClinicalEventDefinition(
        event_type="DIAGNOSIS_CLASSIFICATION_REMOVED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Classificação removida do diagnóstico. Histórico preservado."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["classification_type", "code", "removed_by", "reason"],
            "properties": {
                "classification_type": {
                    "type": "string",
                    "enum": ["cid10", "cid11", "dsm5_tr", "snomed", "internal"],
                },
                "code": {"type": "string", "minLength": 1},
                "removed_by": {"type": "string", "minLength": 1},
                "reason": {"type": "string", "minLength": 1},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection"],
    ),

    # ─── Phenotype — manifestações observáveis ────────────────────────
    "PHENOTYPE_OBSERVED": ClinicalEventDefinition(
        event_type="PHENOTYPE_OBSERVED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Fenótipo/manifestação funcional observada. Independente de "
            "diagnóstico — pode existir antes, durante ou após."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["phenotype_code", "observed_by", "severity"],
            "properties": {
                "phenotype_code": {"type": "string", "minLength": 1},
                "observed_by": {"type": "string", "minLength": 1},
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe", "profound"],
                },
                "onset_date": {"type": "string", "format": "date"},
                "linked_diagnosis_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "context": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "PHENOTYPE_RESOLVED": ClinicalEventDefinition(
        event_type="PHENOTYPE_RESOLVED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Fenótipo resolvido. Não deleta — histórico preservado "
            "para análise longitudinal."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["resolved_by"],
            "properties": {
                "resolved_by": {"type": "string", "minLength": 1},
                "resolution_date": {"type": "string", "format": "date"},
                "reason": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),

    # ─── Assessment — aplicações de escala ────────────────────────────
    "ASSESSMENT_APPLIED": ClinicalEventDefinition(
        event_type="ASSESSMENT_APPLIED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Escala neuropsicológica aplicada. Produz evidência — "
            "não mutua estado clínico diretamente."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": [
                "scale_code",
                "scale_version",
                "applied_by",
                "raw_responses",
                "computed_scores",
            ],
            "properties": {
                "scale_code": {"type": "string", "minLength": 1},
                "scale_version": {"type": "string", "minLength": 1},
                "applied_by": {"type": "string", "minLength": 1},
                "applied_at": {"type": "string", "format": "date-time"},
                "raw_responses": {"type": "object"},
                "computed_scores": {"type": "object"},
                "interpretation": {"type": "string"},
                "linked_diagnosis_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline", "observatory_etl"],
    ),
    "ASSESSMENT_UPDATED": ClinicalEventDefinition(
        event_type="ASSESSMENT_UPDATED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Assessment atualizado/corrigido. Mantém audit chain "
            "completo do cálculo de score."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["updated_by", "raw_responses", "computed_scores"],
            "properties": {
                "updated_by": {"type": "string", "minLength": 1},
                "raw_responses": {"type": "object"},
                "computed_scores": {"type": "object"},
                "interpretation": {"type": "string"},
                "reason": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),

    # ─── Intervention — modelo unificado ──────────────────────────────
    "INTERVENTION_STARTED": ClinicalEventDefinition(
        event_type="INTERVENTION_STARTED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Intervenção clínica iniciada. Modelo único compartilhado "
            "para medication, cannabis, ABA, TO, fono, psicoterapia, etc."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": [
                "intervention_type",
                "subtype",
                "started_by",
                "start_date",
            ],
            "properties": {
                "intervention_type": {
                    "type": "string",
                    "enum": [
                        "medication",
                        "cannabis",
                        "psychotherapy",
                        "occupational_therapy",
                        "speech_therapy",
                        "aba",
                        "neuromodulation",
                        "nutrition",
                        "exercise",
                        "school_support",
                        "parent_training",
                        "other",
                    ],
                },
                "subtype": {"type": "string", "minLength": 1},
                "started_by": {"type": "string", "minLength": 1},
                "start_date": {"type": "string", "format": "date"},
                "dose": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number"},
                        "unit": {"type": "string"},
                        "frequency": {"type": "string"},
                    },
                },
                "indication_condition_code": {"type": "string"},
                "linked_diagnosis_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "prescriber_id": {"type": "string"},
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "INTERVENTION_ADJUSTED": ClinicalEventDefinition(
        event_type="INTERVENTION_ADJUSTED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Intervenção ajustada (dose, frequência, modalidade). "
            "Não reinicia — apenas modifica estado atual."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["adjusted_by", "new_dose"],
            "properties": {
                "adjusted_by": {"type": "string", "minLength": 1},
                "previous_dose": {"type": "object"},
                "new_dose": {"type": "object"},
                "reason": {"type": "string", "minLength": 1},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "INTERVENTION_PAUSED": ClinicalEventDefinition(
        event_type="INTERVENTION_PAUSED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Intervenção pausada temporariamente.",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["paused_by", "reason"],
            "properties": {
                "paused_by": {"type": "string", "minLength": 1},
                "reason": {"type": "string", "minLength": 1},
                "expected_resume_date": {"type": "string", "format": "date"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "INTERVENTION_RESUMED": ClinicalEventDefinition(
        event_type="INTERVENTION_RESUMED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Intervenção retomada após pausa.",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["resumed_by", "resume_date"],
            "properties": {
                "resumed_by": {"type": "string", "minLength": 1},
                "resume_date": {"type": "string", "format": "date"},
                "new_dose": {"type": "object"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "INTERVENTION_STOPPED": ClinicalEventDefinition(
        event_type="INTERVENTION_STOPPED",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Intervenção finalizada. Estado terminal — intervenção "
            "histórica preservada, não pode ser retomada."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["stopped_by", "end_date", "reason"],
            "properties": {
                "stopped_by": {"type": "string", "minLength": 1},
                "end_date": {"type": "string", "format": "date"},
                "reason": {
                    "type": "string",
                    "enum": [
                        "planned_completion",
                        "adverse_event",
                        "ineffectiveness",
                        "patient_choice",
                        "access_barrier",
                        "other",
                    ],
                },
                "outcome_summary": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),

    # ─── Outcome — resultados clínicos ────────────────────────────────
    "OUTCOME_IMPROVEMENT": ClinicalEventDefinition(
        event_type="OUTCOME_IMPROVEMENT",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Melhora clínica observada.",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["observed_by", "evidence"],
            "properties": {
                "observed_by": {"type": "string", "minLength": 1},
                "observed_at": {"type": "string", "format": "date-time"},
                "evidence": {
                    "type": "object",
                    "properties": {
                        "assessment_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "phenotype_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                },
                "intervention_id": {"type": "string"},
                "magnitude": {
                    "type": "string",
                    "enum": ["small", "moderate", "large"],
                },
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "OUTCOME_WORSENING": ClinicalEventDefinition(
        event_type="OUTCOME_WORSENING",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Piora clínica observada.",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["observed_by", "evidence"],
            "properties": {
                "observed_by": {"type": "string", "minLength": 1},
                "observed_at": {"type": "string", "format": "date-time"},
                "evidence": {"type": "object"},
                "intervention_id": {"type": "string"},
                "magnitude": {
                    "type": "string",
                    "enum": ["small", "moderate", "large"],
                },
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "OUTCOME_PARTIAL_RESPONSE": ClinicalEventDefinition(
        event_type="OUTCOME_PARTIAL_RESPONSE",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Resposta parcial a tratamento.",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["observed_by", "intervention_id"],
            "properties": {
                "observed_by": {"type": "string", "minLength": 1},
                "observed_at": {"type": "string", "format": "date-time"},
                "intervention_id": {"type": "string", "minLength": 1},
                "evidence": {"type": "object"},
                "responding_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "non_responding_domains": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "OUTCOME_REMISSION": ClinicalEventDefinition(
        event_type="OUTCOME_REMISSION",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Remissão observada.",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["observed_by", "evidence"],
            "properties": {
                "observed_by": {"type": "string", "minLength": 1},
                "observed_at": {"type": "string", "format": "date-time"},
                "evidence": {"type": "object"},
                "duration_months": {"type": "integer", "minimum": 0},
                "intervention_id": {"type": "string"},
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "OUTCOME_ADVERSE_EVENT": ClinicalEventDefinition(
        event_type="OUTCOME_ADVERSE_EVENT",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description=(
            "Evento adverso. CRÍTICO — sempre registrado. "
            "Vinculado a intervention quando aplicável."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["observed_by", "severity", "description"],
            "properties": {
                "observed_by": {"type": "string", "minLength": 1},
                "observed_at": {"type": "string", "format": "date-time"},
                "severity": {
                    "type": "string",
                    "enum": ["mild", "moderate", "severe", "life_threatening", "fatal"],
                },
                "description": {"type": "string", "minLength": 1},
                "intervention_id": {"type": "string"},
                "causality": {
                    "type": "string",
                    "enum": [
                        "definite",
                        "probable",
                        "possible",
                        "unlikely",
                        "unrelated",
                    ],
                },
                "action_taken": {"type": "string"},
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),
    "OUTCOME_NO_CHANGE": ClinicalEventDefinition(
        event_type="OUTCOME_NO_CHANGE",
        domain="clinical",
        producer=EventProducer.NEURODEVELOPMENTAL.value,
        description="Sem mudança clínica observada.",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["observed_by"],
            "properties": {
                "observed_by": {"type": "string", "minLength": 1},
                "observed_at": {"type": "string", "format": "date-time"},
                "intervention_id": {"type": "string"},
                "duration_observed_months": {"type": "integer", "minimum": 0},
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "registry_projection", "timeline"],
    ),

    # ═══════════════════════════════════════════════════════════════════
    # SPRINT 4 — CLINICAL INTELLIGENCE PLATFORM (ADR-0003)
    # Explicabilidade, Inteligência Clínica, Pesquisa
    # ═══════════════════════════════════════════════════════════════════

    # ─── Explainability (Sprint 4.1) ─────────────────────────────────
    "EXPLANATION_REGISTERED": ClinicalEventDefinition(
        event_type="EXPLANATION_REGISTERED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "Explicabilidade registrada para uma análise de inteligência "
            "clínica. Toda análise DEVE emitir uma Explanation — sem ela, "
            "a análise é considerada caixa-preta e deve ser rejeitada."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": [
                "analysis_id",
                "analysis_type",
                "method",
                "confidence",
            ],
            "properties": {
                "analysis_id": {"type": "string", "minLength": 1},
                "analysis_type": {
                    "type": "string",
                    "enum": [
                        "correlation",
                        "trend",
                        "anomaly",
                        "hypothesis",
                        "episode_suggestion",
                        "cohort_evaluation",
                    ],
                },
                "question": {"type": "string"},
                "answer": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "method": {"type": "string", "minLength": 1},
                "data_window_start": {"type": "string", "format": "date-time"},
                "data_window_end": {"type": "string", "format": "date-time"},
                "n_events_analyzed": {"type": "integer", "minimum": 0},
                "variables": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "contributing_event_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "limitations": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "additionalProperties": True,
        },
        consumers=["audit", "explainability_registry", "intelligence_dashboard"],
    ),
    "EXPLANATION_INVALID": ClinicalEventDefinition(
        event_type="EXPLANATION_INVALID",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "Análise de inteligência rejeitada por ausência de Explanation "
            "ou violação de invariantes de explicabilidade. "
            "Indica potencial caixa-preta — incrementa métrica "
            "intelligence_unexplained_total."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["analysis_id", "reason"],
            "properties": {
                "analysis_id": {"type": "string", "minLength": 1},
                "reason": {
                    "type": "string",
                    "enum": [
                        "missing_explanation",
                        "low_confidence",
                        "invalid_window",
                        "no_contributing_events",
                        "black_box_detected",
                    ],
                },
                "notes": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "intelligence_dlq"],
    ),

    # ─── Sprint 4.2 — Clinical Context Engine (ADR-0003) ─────────────
    "CLINICAL_CONTEXT_SUGGESTED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_SUGGESTED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "Rule engine ou AI sugeriu abertura de um ClinicalContext. "
            "Não é abertura automática — exige confirmação humana."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "context_type", "rule_id", "confidence"],
            "properties": {
                "context_id": {"type": "string", "minLength": 1},
                "context_type": {"type": "string", "minLength": 1},
                "rule_id": {"type": "string", "minLength": 1},
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "contributing_event_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "explanation_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "patient_id": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "explainability_registry"],
    ),
    "CLINICAL_CONTEXT_CREATED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_CREATED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "ClinicalContext criado manualmente (planned) ou confirmado "
            "a partir de uma sugestão."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "context_type", "patient_id", "origin"],
            "properties": {
                "context_id": {"type": "string", "minLength": 1},
                "context_type": {"type": "string"},
                "status": {"type": "string"},
                "origin": {"type": "string"},
                "confidence_score": {"type": "number"},
                "patient_id": {"type": "string"},
                "tenant_id": {"type": "string"},
                "title": {"type": "string"},
                "reason": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "active_context_projection"],
    ),
    "CLINICAL_CONTEXT_ACTIVATED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_ACTIVATED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "ClinicalContext movido para Active (Planned→Active ou "
            "Suggested→Active após confirmação humana)."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "actor_id"],
            "properties": {
                "context_id": {"type": "string"},
                "actor_id": {"type": "string"},
                "from_status": {"type": "string"},
                "activated_at": {"type": "string", "format": "date-time"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "active_context_projection"],
    ),
    "CLINICAL_CONTEXT_UPDATED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_UPDATED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description="Metadados de ClinicalContext atualizados (in-place).",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "actor_id"],
            "properties": {
                "context_id": {"type": "string"},
                "actor_id": {"type": "string"},
                "changed_fields": {"type": "array", "items": {"type": "string"}},
                "old_values": {"type": "object"},
                "new_values": {"type": "object"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection"],
    ),
    "CLINICAL_CONTEXT_CLOSED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_CLOSED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "ClinicalContext fechado (Active→Completed/Cancelled/Archived). "
            "end_date registrado."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "actor_id", "new_status"],
            "properties": {
                "context_id": {"type": "string"},
                "actor_id": {"type": "string"},
                "from_status": {"type": "string"},
                "new_status": {"type": "string", "enum": ["Completed", "Cancelled", "Archived"]},
                "end_date": {"type": "string", "format": "date-time"},
                "summary": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "active_context_projection"],
    ),
    "CLINICAL_CONTEXT_REOPENED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_REOPENED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "ClinicalContext reaberto (Completed→Active). "
            "Incrementa aggregate_version."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "actor_id"],
            "properties": {
                "context_id": {"type": "string"},
                "actor_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "active_context_projection"],
    ),
    "CLINICAL_CONTEXT_LINKED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_LINKED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "Relacionamento criado entre dois ClinicalContexts "
            "(grafo de contexto)."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["relationship_id", "source_context_id", "target_context_id", "relationship_type"],
            "properties": {
                "relationship_id": {"type": "string"},
                "source_context_id": {"type": "string"},
                "target_context_id": {"type": "string"},
                "relationship_type": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "relationship_projection"],
    ),
    "CLINICAL_CONTEXT_UNLINKED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_UNLINKED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description="Relacionamento entre ClinicalContexts removido (soft delete).",
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["relationship_id", "actor_id"],
            "properties": {
                "relationship_id": {"type": "string"},
                "actor_id": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "relationship_projection"],
    ),
    "CLINICAL_CONTEXT_REJECTED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_REJECTED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "Sugestão de ClinicalContext rejeitada por humano. "
            "Contexto entra em estado terminal Rejected."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "actor_id", "reason"],
            "properties": {
                "context_id": {"type": "string"},
                "actor_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection", "intelligence_dlq"],
    ),
    "CLINICAL_CONTEXT_TYPE_CONFIRMED": ClinicalEventDefinition(
        event_type="CLINICAL_CONTEXT_TYPE_CONFIRMED",
        domain="clinical",
        producer=EventProducer.INTELLIGENCE.value,
        description=(
            "Tipo de ClinicalContext sugerido confirmado ou corrigido pelo "
            "curador antes da ativação."
        ),
        version="1.0",
        json_schema={
            "type": "object",
            "required": ["context_id", "actor_id", "confirmed_type"],
            "properties": {
                "context_id": {"type": "string"},
                "actor_id": {"type": "string"},
                "confirmed_type": {"type": "string"},
                "suggested_type": {"type": "string"},
            },
            "additionalProperties": True,
        },
        consumers=["audit", "context_projection"],
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# API PÚBLICA DO CATÁLOGO
# ═══════════════════════════════════════════════════════════════════════


def get_event_definition(event_type: str) -> Optional[ClinicalEventDefinition]:
    """Busca definição de um event_type no catálogo."""
    return CLINICAL_EVENT_CATALOG.get(event_type)


def is_known_event_type(event_type: str) -> bool:
    """Verifica se um event_type está registrado."""
    return event_type in CLINICAL_EVENT_CATALOG


def list_event_types(
    status: Optional[EventStatus] = None,
    producer: Optional[str] = None,
    active_only: bool = True,
) -> List[ClinicalEventDefinition]:
    """
    Lista event_types do catálogo com filtros opcionais.

    Args:
        status: filtra por status (active/deprecated)
        producer: filtra por source_module
        active_only: se True, exclui deprecated
    """
    results = list(CLINICAL_EVENT_CATALOG.values())
    if active_only:
        results = [d for d in results if d.status == EventStatus.ACTIVE]
    if status is not None:
        results = [d for d in results if d.status == status]
    if producer is not None:
        results = [d for d in results if d.producer == producer]
    return results


def count_event_types() -> int:
    """Conta total de event_types registrados."""
    return len(CLINICAL_EVENT_CATALOG)
