"""
test_lifecycle_clinical_identity.py — Lifecycle completo do Aggregate Root.

Cobre:
    - create(): estado inicial ACTIVE.
    - attach_*(): cada tipo de entidade pode ser vinculada.
    - archive(): transição para ARCHIVED.
    - Re-archive(): levanta erro (idempotency no domain).
    - Invariantes: source_event_ids sempre presente.
    - Lifecycle via Registry (replay produz mesmo estado).
"""
from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.domain.clinical_identity import (
    ClinicalIdentity,
    ClinicalIdentityStatus,
)
from tests.neurodev_sprint_3_2.builders import RegistryBuilder
from tests.neurodev_sprint_3_2.test_projection_replay import Snapshot


# ─── Domain tests ──────────────────────────────────────────────────────────


def test_create_initial_state():
    identity = ClinicalIdentity.create(
        patient_id="p-1",
        source_event_id="evt-1",
        initial_notes="Primeira consulta",
    )
    assert identity.status == ClinicalIdentityStatus.ACTIVE
    assert identity.patient_id == "p-1"
    assert identity.initial_notes == "Primeira consulta"
    assert identity.diagnosis_ids == []
    assert identity.phenotype_ids == []
    assert identity.assessment_ids == []
    assert identity.intervention_ids == []
    assert identity.outcome_ids == []
    assert identity.archived_at is None
    assert identity.archive_reason is None
    assert identity.is_active()
    assert not identity.is_archived()


def REDACTED():
    with pytest.raises(ValueError, match="source_event_ids"):
        ClinicalIdentity(
            id="identity-1",
            patient_id="p-1",
            source_event_ids=[],
        )


def REDACTED():
    identity = ClinicalIdentity.create(patient_id="p-1", source_event_id="evt-1")
    identity.attach_diagnosis("diag-1", "evt-2")
    identity.attach_diagnosis("diag-1", "evt-3")  # duplicata — não adiciona
    assert identity.diagnosis_ids == ["diag-1"]


def test_attach_multiple_diagnoses():
    identity = ClinicalIdentity.create(patient_id="p-1", source_event_id="evt-1")
    identity.attach_diagnosis("diag-1", "evt-2")
    identity.attach_diagnosis("diag-2", "evt-3")
    identity.attach_diagnosis("diag-3", "evt-4")
    assert identity.diagnosis_ids == ["diag-1", "diag-2", "diag-3"]


def REDACTED():
    identity = ClinicalIdentity.create(patient_id="p-1", source_event_id="evt-1")
    identity.archive(event_id="evt-arch", reason="patient_transferred")
    assert identity.is_archived()
    assert not identity.is_active()
    assert identity.archive_reason == "patient_transferred"
    assert identity.archived_at is not None


def REDACTED():
    identity = ClinicalIdentity.create(patient_id="p-1", source_event_id="evt-1")
    identity.archive(event_id="evt-1", reason="x")
    with pytest.raises(ValueError, match="already archived"):
        identity.archive(event_id="evt-2", reason="y")


def test_to_dict_includes_all_fields():
    identity = ClinicalIdentity.create(
        patient_id="p-1",
        source_event_id="evt-1",
        initial_notes="notas",
    )
    identity.attach_diagnosis("d1", "evt-2")
    identity.attach_phenotype("p1", "evt-3")

    d = identity.to_dict()
    assert d["patient_id"] == "p-1"
    assert d["status"] == "active"
    assert d["diagnosis_count"] == 1
    assert d["phenotype_count"] == 1
    assert d["diagnosis_ids"] == ["d1"]
    assert d["phenotype_ids"] == ["p1"]


# ─── Projection lifecycle tests ────────────────────────────────────────────


def REDACTED(projection, publisher):
    """
    Cenário completo: identity → diagnosis → phenotype → intervention →
    outcome → archive. Registry deve refletir todas as mudanças.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-lifecycle")
        .with_patient("p-1")
        .with_identity(initial_notes="Início do acompanhamento")
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_medication()
        .with_assessment()
        .with_outcome(type="improvement")
        .build()
    )
    from datetime import datetime

    for evt in fixture.events:
        publisher.publish(
            tenant_id=evt["tenant_id"],
            patient_id=evt["patient_id"],
            event_type=evt["event_type"],
            event_datetime=datetime.fromisoformat(
                evt["event_datetime"].replace("Z", "+00:00")
            ),
            source_module=evt.get("source_module", "neurodevelopmental"),
            payload=evt["payload"],
            aggregate_type=evt["aggregate_type"],
            aggregate_id=evt["aggregate_id"],
            created_by=evt.get("created_by"),
        )
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(events)

    snap = Snapshot.capture(projection, fixture.tenant_id)
    identity = snap.identities[0]
    assert identity["status"] == "active"
    assert identity["diagnosis_count"] == 1
    assert identity["phenotype_count"] == 1
    assert identity["intervention_count"] == 1
    assert identity["assessment_count"] == 1
    assert identity["outcome_count"] == 1


def REDACTED(projection, publisher):
    """
    Arquivar ClinicalIdentity → status muda para 'archived' no Registry.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-archive")
        .with_identity()
        .build()
    )
    from datetime import datetime

    for evt in fixture.events:
        publisher.publish(
            tenant_id=evt["tenant_id"],
            patient_id=evt["patient_id"],
            event_type=evt["event_type"],
            event_datetime=datetime.fromisoformat(
                evt["event_datetime"].replace("Z", "+00:00")
            ),
            source_module=evt.get("source_module", "neurodevelopmental"),
            payload=evt["payload"],
            aggregate_type=evt["aggregate_type"],
            aggregate_id=evt["aggregate_id"],
            created_by=evt.get("created_by"),
        )

    # Adiciona evento CLINICAL_IDENTITY_ARCHIVED
    archive_evt_id = publisher.publish(
        tenant_id=fixture.tenant_id,
        patient_id=fixture.patient_id,
        event_type="CLINICAL_IDENTITY_ARCHIVED",
        event_datetime=datetime.now(tz=datetime.now().astimezone().tzinfo),
        source_module="neurodevelopmental",
        payload={
            "identity_id": fixture.identity_id,
            "reason": "patient_transferred",
            "notes": "Transferido para outro serviço",
        },
        aggregate_type="clinical_identity",
        aggregate_id=fixture.identity_id,
        created_by="prof-1",
    )

    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(events)

    identity = projection.get_clinical_identity(
        fixture.tenant_id, fixture.identity_id
    )
    assert identity.status == "archived"
    assert identity.archive_reason == "patient_transferred"
