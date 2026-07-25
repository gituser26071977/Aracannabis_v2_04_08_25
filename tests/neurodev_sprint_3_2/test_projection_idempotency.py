"""
test_projection_idempotency.py — Aplicação repetida de eventos = idempotente.

INVARIANTE:

    apply(event) N vezes → mesmo estado final.

    N ∈ {1, 2, 5, 50, 100}

    Sem duplicação de linhas no Registry.
    Sem corrupção de contadores.
    Sem erros.

A idempotency é garantida via `processed_events` table: cada event_id é
marcado após aplicação; tentativas subsequentes são no-ops.

Testa também o caso degenerado: aplicar evento que NÃO está no store
diretamente no projection (cenários de replay / migração).
"""
from __future__ import annotations

import pytest

from tests.neurodev_sprint_3_2.builders import EventBuilder, RegistryBuilder
from tests.neurodev_sprint_3_2.test_projection_replay import Snapshot


# ─── Helpers ───────────────────────────────────────────────────────────────


def _make_event(event_type: str = "CLINICAL_IDENTITY_CREATED", **kwargs):
    """Atalho para construir um único evento."""
    return (
        EventBuilder()
        .with_type(event_type)
        .with_aggregate(
            kwargs.pop("aggregate_type", "clinical_identity"),
            kwargs.pop("aggregate_id", "identity-1"),
        )
        .with_payload(patient_id=kwargs.pop("patient_id", "p-1"), identity_id="identity-1")
        .with_tenant(kwargs.pop("tenant_id", "t-idem"))
        .with_actor(kwargs.pop("actor_id", "prof-1"))
        .build()
    )


# ─── Testes: idempotência em N aplicações ──────────────────────────────────


@pytest.mark.parametrize("n_applications", [1, 2, 5, 50, 100])
def REDACTED(projection, n_applications):
    """
    Aplicar o MESMO evento N vezes → mesmo estado final.

    Cobertura parametrizada: 1 (baseline), 2 (mínimo duplicação),
    5, 50, 100 (stress).
    """
    event = _make_event(event_type="CLINICAL_IDENTITY_CREATED")

    # Aplica N vezes
    results = [projection.apply(event) for _ in range(n_applications)]

    # Apenas a 1ª aplicação retorna True; demais retornam False (já processado)
    assert results[0] is True
    assert all(r is False for r in results[1:])

    # Estado: apenas 1 ClinicalIdentity
    snap = Snapshot.capture(projection, "t-idem")
    assert len(snap.identities) == 1
    assert snap.processed_count == 1  # Não cresce


def REDACTED(projection):
    """Stress: aplicar DIAGNOSIS_HYPOTHESIZED 50x."""
    fixture = (
        RegistryBuilder()
        .with_tenant("t-diag-idem")
        .with_identity()
        .build()
    )
    identity_event = fixture.events[0]
    projection.apply(identity_event)

    diag_event = (
        EventBuilder()
        .with_type("DIAGNOSIS_HYPOTHESIZED")
        .with_aggregate("diagnosis", "diag-idem")
        .with_payload(
            identity_id=fixture.identity_id,
            condition_code="TEA_F84.0",
            hypothesised_by="prof-1",
            reason="x",
        )
        .with_tenant(fixture.tenant_id)
        .build()
    )

    for _ in range(50):
        projection.apply(diag_event)

    snap = Snapshot.capture(projection, fixture.tenant_id)
    assert len(snap.diagnoses) == 1  # Apenas 1 linha
    assert snap.processed_count == 2  # identity + 1 diagnosis


# ─── Testes: idempotência com fixture rica ─────────────────────────────────


def REDACTED(projection, publisher):
    """Fixture rica (multi-entidade) — replay 100x mantém estado consistente."""
    fixture = (
        RegistryBuilder()
        .with_tenant("t-full")
        .with_patient("p-1")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_medication()
        .with_assessment()
        .with_outcome(type="improvement")
        .build()
    )

    # Publica no store (gera hash chain)
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

    # Aplica via query (como o replay faz)
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )

    # 100 iterações — cada uma aplica batch
    initial_snap = None
    for i in range(100):
        # Reset processed_events apenas na 1ª iteração para validar idempotency
        if i == 0:
            applied = projection.apply_batch(events)
            assert applied == len(fixture.events)
        else:
            applied = projection.apply_batch(events)
            assert applied == 0  # Todos já processados
        snap = Snapshot.capture(projection, fixture.tenant_id)
        if initial_snap is None:
            initial_snap = snap

    # Estado preservado ao longo de 100 iterações
    assert snap.processed_count == initial_snap.processed_count
    assert len(snap.identities) == 1
    assert len(snap.diagnoses) == 1
    assert len(snap.phenotypes) == 1
    assert len(snap.interventions) == 1
    assert len(snap.assessments) == 1
    assert len(snap.outcomes) == 1


# ─── Testes: idempotência após wipe+replay ─────────────────────────────────


def REDACTED(projection, publisher):
    """
    Cenário: Registry tem dados → wipe → replay_from(0) = mesmo estado.
    Validar que idempotency + replay coexistem.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-wipe-idem")
        .with_identity()
        .with_diagnosis(state="confirmed")
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

    # 5 ciclos wipe + replay
    for i in range(5):
        applied = projection.replay_all(fixture.tenant_id)
        snap = Snapshot.capture(projection, fixture.tenant_id)
        assert applied == len(fixture.events)
        assert len(snap.identities) == 1
        assert len(snap.diagnoses) == 1
        assert snap.processed_count == len(fixture.events)


# ─── Testes: contadores desnormalizados após idempotência ──────────────────


def REDACTED(projection, publisher):
    """
    Cenário crítico: counters desnormalizados na ClinicalIdentity
    (diagnosis_count, intervention_count, etc.) não devem crescer
    com aplicações repetidas.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-counter")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_medication()
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

    # Aplica 10x
    for _ in range(10):
        projection.apply_batch(events)

    snap = Snapshot.capture(projection, fixture.tenant_id)
    identity = snap.identities[0]
    assert identity["diagnosis_count"] == 1  # Não 10
    assert identity["phenotype_count"] == 1
    assert identity["intervention_count"] == 1
    assert identity["assessment_count"] == 0
    assert identity["outcome_count"] == 0


# ─── Testes: race condition simulada ───────────────────────────────────────


def REDACTED(projection):
    """
    Simula race condition: apply() chamado concorrentemente com mesmo evento.
    Como processed_events.check é single-thread (SQLite), o resultado
    deve ser consistente.
    """
    event = _make_event(event_type="CLINICAL_IDENTITY_CREATED")

    # Aplica 100x sequencialmente (simula race em SQLite que serializa writes)
    results = [projection.apply(event) for _ in range(100)]
    assert results[0] is True
    assert sum(1 for r in results if r) == 1  # Apenas 1 sucesso

    snap = Snapshot.capture(projection, "t-idem")
    assert len(snap.identities) == 1
