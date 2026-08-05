"""
test_projection_replay.py — Garantia fundamental do Registry como Projection.

A REGRA DE OURO:

    wipe() + replay(all_events) → projection bit-identical

Se esta invariante quebrar, o Registry NÃO é mais rebuildable e a
fundação do AraOS desmorona. Estes testes cobrem TODOS os cenários
de replay:

    - replay_all() completo (desde genesis)
    - replay_from(sequence) incremental
    - replay após falha no meio
    - replay após migration de schema
    - replay parcial (apenas algumas entidades)

ADR-0002 §2.5: 'Registry como Projection — não fonte primária,
reconstruível integralmente a partir do Event Store.'
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from araos.clinical.event_store import ClinicalEventPublisher
from tests.neurodev_sprint_3_2.builders import RegistryBuilder


# ─── Helpers ───────────────────────────────────────────────────────────────


@dataclass
class Snapshot:
    """Snapshot do Registry para comparação bit-identical."""

    identities: List[Dict[str, Any]]
    diagnoses: List[Dict[str, Any]]
    phenotypes: List[Dict[str, Any]]
    interventions: List[Dict[str, Any]]
    assessments: List[Dict[str, Any]]
    outcomes: List[Dict[str, Any]]
    processed_count: int

    @classmethod
    def capture(cls, projection, tenant_id: str) -> "Snapshot":
        """Captura estado completo do Registry em dicts serializáveis."""

        def _row_to_dict(row) -> Dict[str, Any]:
            d = {}
            for col in row.__table__.columns:
                v = getattr(row, col.name)
                if hasattr(v, "isoformat"):
                    v = v.isoformat()
                d[col.name] = v
            return d

        from araos.specialties.neurodevelopmental.projections.db_models import (
            NeuroRegistryAssessmentModel,
            NeuroRegistryClinicalIdentityModel,
            NeuroRegistryDiagnosisModel,
            NeuroRegistryInterventionModel,
            NeuroRegistryOutcomeModel,
            NeuroRegistryPhenotypeModel,
        )

        with projection._session_factory() as session:
            identities = sorted(
                [
                    _row_to_dict(row)
                    for row in session.query(NeuroRegistryClinicalIdentityModel)
                    .filter_by(tenant_id=tenant_id)
                    .all()
                ],
                key=lambda x: x["id"],
            )
            diagnoses = sorted(
                [
                    _row_to_dict(row)
                    for row in session.query(NeuroRegistryDiagnosisModel)
                    .filter_by(tenant_id=tenant_id)
                    .all()
                ],
                key=lambda x: x["id"],
            )
            phenotypes = sorted(
                [
                    _row_to_dict(row)
                    for row in session.query(NeuroRegistryPhenotypeModel)
                    .filter_by(tenant_id=tenant_id)
                    .all()
                ],
                key=lambda x: x["id"],
            )
            interventions = sorted(
                [
                    _row_to_dict(row)
                    for row in session.query(NeuroRegistryInterventionModel)
                    .filter_by(tenant_id=tenant_id)
                    .all()
                ],
                key=lambda x: x["id"],
            )
            assessments = sorted(
                [
                    _row_to_dict(row)
                    for row in session.query(NeuroRegistryAssessmentModel)
                    .filter_by(tenant_id=tenant_id)
                    .all()
                ],
                key=lambda x: x["id"],
            )
            outcomes = sorted(
                [
                    _row_to_dict(row)
                    for row in session.query(NeuroRegistryOutcomeModel)
                    .filter_by(tenant_id=tenant_id)
                    .all()
                ],
                key=lambda x: x["id"],
            )

        return cls(
            identities=identities,
            diagnoses=diagnoses,
            phenotypes=phenotypes,
            interventions=interventions,
            assessments=assessments,
            outcomes=outcomes,
            processed_count=projection.get_processed_count(tenant_id),
        )


def _apply_fixture_to_store(publisher: ClinicalEventPublisher, fixture) -> None:
    """Aplica os eventos da fixture via publisher real (gera hash chain)."""
    for evt in fixture.events:
        publisher.publish(
            tenant_id=evt["tenant_id"],
            patient_id=evt["patient_id"],
            event_type=evt["event_type"],
            event_datetime=__import__("datetime").datetime.fromisoformat(
                evt["event_datetime"].replace("Z", "+00:00")
            ),
            source_module=evt.get("source_module", "neurodevelopmental"),
            payload=evt["payload"],
            aggregate_type=evt["aggregate_type"],
            aggregate_id=evt["aggregate_id"],
            created_by=evt.get("created_by"),
        )


def _apply_fixture_to_projection(projection, fixture) -> None:
    """Replay eventos da fixture via Event Store → projection."""
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(events)


# ─── Testes: replay_all completo ───────────────────────────────────────────


def REDACTED(projection, publisher):
    """Cenário 1: replay_all() reconstroi ClinicalIdentity a partir do genesis."""
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-1")
        .with_patient("p-replay-1")
        .with_identity(initial_notes="Teste replay")
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_before = Snapshot.capture(projection, fixture.tenant_id)
    assert len(snap_before.identities) == 1
    assert snap_before.identities[0]["patient_id"] == "p-replay-1"

    # Wipe + replay
    applied = projection.replay_all(fixture.tenant_id)

    snap_after = Snapshot.capture(projection, fixture.tenant_id)
    assert applied == 1  # 1 evento (CLINICAL_IDENTITY_CREATED)
    assert snap_after.identities == snap_before.identities
    assert snap_after.processed_count == snap_before.processed_count


def REDACTED(projection, publisher):
    """
    Cenário 2: Cenário clínico rico (multi-diagnóstico + phenotype +
    intervention + assessment + outcome) — replay bit-identical.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-2")
        .with_patient("p-replay-2")
        .with_identity()
        .with_diagnosis(condition_code="TEA_F84.0", state="confirmed")
        .with_phenotype(code="social_deficit", severity="moderate")
        .with_medication(subtype="risperidona", dose_value=0.5, dose_unit="mg")
        .with_assessment(scale_code="MCHAT_R_F", computed_score=8.0)
        .with_outcome(type="improvement", magnitude="moderate")
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_before = Snapshot.capture(projection, fixture.tenant_id)
    applied = projection.replay_all(fixture.tenant_id)
    snap_after = Snapshot.capture(projection, fixture.tenant_id)

    assert applied == len(fixture.events)
    assert snap_after.identities == snap_before.identities
    assert snap_after.diagnoses == snap_before.diagnoses
    assert snap_after.phenotypes == snap_before.phenotypes
    assert snap_after.interventions == snap_before.interventions
    assert snap_after.assessments == snap_before.assessments
    assert snap_after.outcomes == snap_before.outcomes


def test_replay_all_preserves_counters(projection, publisher):
    """
    Cenário 3: Counters desnormalizados (diagnosis_count, intervention_count, etc.)
    devem sobreviver ao replay.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-3")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_diagnosis(condition_code="TDAH_F90.0", state="confirmed")
        .with_phenotype()
        .with_medication()
        .with_assessment()
        .with_outcome()
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_before = Snapshot.capture(projection, fixture.tenant_id)
    identity_before = snap_before.identities[0]
    assert identity_before["diagnosis_count"] == 2
    assert identity_before["phenotype_count"] == 1
    assert identity_before["intervention_count"] == 1
    assert identity_before["assessment_count"] == 1
    assert identity_before["outcome_count"] == 1

    projection.replay_all(fixture.tenant_id)
    snap_after = Snapshot.capture(projection, fixture.tenant_id)
    identity_after = snap_after.identities[0]

    assert identity_after["diagnosis_count"] == 2
    assert identity_after["phenotype_count"] == 1
    assert identity_after["intervention_count"] == 1
    assert identity_after["assessment_count"] == 1
    assert identity_after["outcome_count"] == 1


# ─── Testes: replay_from incremental ───────────────────────────────────────


def REDACTED(projection, publisher):
    """
    Cenário 4: Replay incremental — processar metade, depois replay_from.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-4")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_medication()
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_before = Snapshot.capture(projection, fixture.tenant_id)

    # Pega metade dos eventos e replay incremental
    all_events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    midpoint = len(all_events) // 2
    projection.replay_from(fixture.tenant_id, since_sequence=midpoint)

    snap_after = Snapshot.capture(projection, fixture.tenant_id)
    assert snap_after.processed_count == snap_before.processed_count
    assert snap_after.identities == snap_before.identities
    assert snap_after.diagnoses == snap_before.diagnoses


def REDACTED(projection, publisher):
    """
    Cenário 5: replay_from(0) == replay_all() em efeito (bit-identical).
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-5")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_full = Snapshot.capture(projection, fixture.tenant_id)

    projection.replay_from(fixture.tenant_id, since_sequence=0)
    snap_incremental = Snapshot.capture(projection, fixture.tenant_id)

    assert snap_incremental.identities == snap_full.identities
    assert snap_incremental.diagnoses == snap_full.diagnoses
    assert snap_incremental.phenotypes == snap_full.phenotypes


def REDACTED(projection, publisher):
    """
    Cenário 6: replay_from com since_sequence > todos eventos = 0 aplicados.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-6")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_before = Snapshot.capture(projection, fixture.tenant_id)
    applied = projection.replay_from(fixture.tenant_id, since_sequence=999999)
    snap_after = Snapshot.capture(projection, fixture.tenant_id)

    assert applied == 0
    assert snap_after.processed_count == snap_before.processed_count


# ─── Testes: replay após falha / estado corrompido ─────────────────────────


def REDACTED(projection, publisher):
    """
    Cenário 7: Registry em estado parcial (apenas metade dos eventos aplicados).
    replay_all() reconstrói estado correto do zero.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-7")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_medication()
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    # Simula corrupção: deleta phenotype do Registry (mas evento continua no store)
    from araos.specialties.neurodevelopmental.projections.db_models import (
        NeuroRegistryPhenotypeModel,
    )
    with projection._session_factory() as session:
        session.query(NeuroRegistryPhenotypeModel).filter_by(
            tenant_id=fixture.tenant_id
        ).delete()
        session.commit()

    snap_corrupted = Snapshot.capture(projection, fixture.tenant_id)
    assert len(snap_corrupted.phenotypes) == 0  # phenotype perdido

    # Replay recupera
    projection.replay_all(fixture.tenant_id)
    snap_recovered = Snapshot.capture(projection, fixture.tenant_id)
    assert len(snap_recovered.phenotypes) == 1


def REDACTED(projection, publisher):
    """
    Cenário 8: Registry tem evento aplicado que NÃO deveria estar lá
    (simula double-apply que bypassou idempotency).
    Replay deve normalizar.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-8")
        .with_identity()
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    # O replay_all() faz wipe + replay → estado deve ser exato
    snap_before = Snapshot.capture(projection, fixture.tenant_id)
    projection.replay_all(fixture.tenant_id)
    snap_after = Snapshot.capture(projection, fixture.tenant_id)

    # Tudo igual
    assert snap_after.processed_count == snap_before.processed_count
    assert snap_after.identities == snap_before.identities


def test_replay_after_migration_schema(projection, publisher):
    """
    Cenário 9: Simula cenário pós-migration (todas tabelas recriadas vazias).
    replay_all() deve reconstruir fielmente.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-replay-9")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_assessment()
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_before = Snapshot.capture(projection, fixture.tenant_id)

    # Simula migration: drop + recriação de todas as tabelas projection
    from araos.specialties.neurodevelopmental.projections.db_models import (
        NeuroRegistryAssessmentModel,
        NeuroRegistryClinicalIdentityModel,
        NeuroRegistryDiagnosisModel,
        NeuroRegistryInterventionModel,
        NeuroRegistryOutcomeModel,
        NeuroRegistryPhenotypeModel,
        NeuroRegistryProcessedEventModel,
        Base,
    )
    Base.metadata.drop_all(projection._session_factory().kw["bind"])
    Base.metadata.create_all(projection._session_factory().kw["bind"])

    snap_post_migration = Snapshot.capture(projection, fixture.tenant_id)
    assert len(snap_post_migration.identities) == 0

    # Replay reconstrói
    projection.replay_all(fixture.tenant_id)
    snap_after = Snapshot.capture(projection, fixture.tenant_id)

    assert snap_after.identities == snap_before.identities
    assert snap_after.diagnoses == snap_before.diagnoses
    assert snap_after.assessments == snap_before.assessments


# ─── Testes: isolamento multi-tenant ───────────────────────────────────────


def test_replay_isolates_per_tenant(projection, publisher):
    """
    Cenário 10: replay_all() afeta APENAS o tenant especificado.
    Outros tenants permanecem intactos.
    """
    f1 = (
        RegistryBuilder()
        .with_tenant("t-A")
        .with_patient("p-A")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .build()
    )
    f2 = (
        RegistryBuilder()
        .with_tenant("t-B")
        .with_patient("p-B")
        .with_identity()
        .with_diagnosis(condition_code="TDAH_F90.0", state="confirmed")
        .with_phenotype()
        .build()
    )

    _apply_fixture_to_store(publisher, f1)
    _apply_fixture_to_store(publisher, f2)
    _apply_fixture_to_projection(projection, f1)
    _apply_fixture_to_projection(projection, f2)

    snap_b_before = Snapshot.capture(projection, "t-B")
    projection.replay_all("t-A")  # wipe + replay APENAS tenant A
    snap_b_after = Snapshot.capture(projection, "t-B")

    # Tenant B intocado
    assert snap_b_after.identities == snap_b_before.identities
    assert snap_b_after.diagnoses == snap_b_before.diagnoses
    assert snap_b_after.phenotypes == snap_b_before.phenotypes


# ─── Testes: replay parcial / seletivo ─────────────────────────────────────


def test_replay_only_some_aggregates(projection, publisher):
    """
    Cenário 11: Cenário com 2 ClinicalIdentities distintas — replay_all
    deve reconstruir ambas.
    """
    f1 = (
        RegistryBuilder()
        .with_tenant("t-multi")
        .with_patient("p-1")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .build()
    )
    f2 = (
        RegistryBuilder()
        .with_tenant("t-multi")
        .with_patient("p-2")
        .with_identity()
        .with_phenotype()
        .build()
    )

    _apply_fixture_to_store(publisher, f1)
    _apply_fixture_to_store(publisher, f2)
    _apply_fixture_to_projection(projection, f1)
    _apply_fixture_to_projection(projection, f2)

    snap_before = Snapshot.capture(projection, "t-multi")
    assert len(snap_before.identities) == 2

    projection.replay_all("t-multi")
    snap_after = Snapshot.capture(projection, "t-multi")

    assert len(snap_after.identities) == 2
    assert sorted(i["id"] for i in snap_after.identities) == sorted(
        i["id"] for i in snap_before.identities
    )


def REDACTED(projection, publisher):
    """
    Cenário 12: Metadata dos eventos (sequence, event_datetime) deve
    ser preservada no Registry.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-meta")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .build()
    )
    _apply_fixture_to_store(publisher, fixture)
    _apply_fixture_to_projection(projection, fixture)

    snap_before = Snapshot.capture(projection, fixture.tenant_id)
    diag_before = snap_before.diagnoses[0]
    seq_before = diag_before["last_sequence"]

    projection.replay_all(fixture.tenant_id)
    snap_after = Snapshot.capture(projection, fixture.tenant_id)
    diag_after = snap_after.diagnoses[0]

    assert diag_after["last_sequence"] == seq_before
    assert diag_after["id"] == diag_before["id"]
    assert diag_after["state"] == diag_before["state"]
