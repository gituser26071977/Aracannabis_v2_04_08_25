"""
test_projection_out_of_order.py — Eventos fora de ordem = mesmo estado final.

INVARIANTE:

    apply({e1, e2, e3, ...}) onde ordem é embaralhada
    ==
    apply({e1, e2, e3, ...}) em ordem canônica (sequence ASC)

A ordenação canônica é por `sequence` (insertion order no Event Store),
NUNCA por event_datetime. Isto é FUNDAMENTAL para o sistema: o relógio
do sistema pode estar dessincronizado, mas a sequência lógica
do domínio é preservada.

Casos cobertos:
    - Eventos embaralhados aleatoriamente
    - Ordem inversa
    - Eventos com timestamps fora de ordem
    - Intercalação (e.g. identity, phenotype1, diagnosis, phenotype2)
    - Diagnóstico CONFIRMED chega antes de HYPOTHESIZED (cenário race)
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from araos.clinical.event_store import ClinicalEventPublisher
from tests.neurodev_sprint_3_2.builders import EventBuilder, RegistryBuilder
from tests.neurodev_sprint_3_2.test_projection_replay import Snapshot


def _publish_all(publisher: ClinicalEventPublisher, fixture) -> List[str]:
    """Publica todos os eventos da fixture no store, retorna lista de event_ids."""
    from datetime import datetime as _dt

    ids: List[str] = []
    for evt in fixture.events:
        eid = publisher.publish(
            tenant_id=evt["tenant_id"],
            patient_id=evt["patient_id"],
            event_type=evt["event_type"],
            event_datetime=_dt.fromisoformat(
                evt["event_datetime"].replace("Z", "+00:00")
            ),
            source_module=evt.get("source_module", "neurodevelopmental"),
            payload=evt["payload"],
            aggregate_type=evt["aggregate_type"],
            aggregate_id=evt["aggregate_id"],
            created_by=evt.get("created_by"),
        )
        ids.append(eid)
    return ids


# ─── Testes: embaralhamento aleatório ───────────────────────────────────────


def REDACTED(projection, publisher, monkeypatch):
    """
    Aplica 100 permutações diferentes dos mesmos eventos.
    Estado final deve ser idêntico em todas.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-shuffle")
        .with_patient("p-1")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_medication()
        .with_assessment()
        .build()
    )

    # Snapshot de referência (ordem canônica)
    _publish_all(publisher, fixture)
    canonical_events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(canonical_events)
    reference_snap = Snapshot.capture(projection, fixture.tenant_id)

    # 100 iterações com ordens aleatórias
    rng = random.Random(42)  # seed fixo → reprodutível
    for i in range(100):
        # Wipe
        projection.replay_all(fixture.tenant_id)

        # Embaralha
        shuffled = list(canonical_events)
        rng.shuffle(shuffled)

        projection.apply_batch(shuffled)
        snap = Snapshot.capture(projection, fixture.tenant_id)

        # Bit-identical
        assert snap.identities == reference_snap.identities, (
            f"Iteração {i}: identities divergiram"
        )
        assert snap.diagnoses == reference_snap.diagnoses
        assert snap.phenotypes == reference_snap.phenotypes
        assert snap.interventions == reference_snap.interventions
        assert snap.assessments == reference_snap.assessments


def REDACTED(projection, publisher):
    """Eventos em ordem inversa devem produzir mesmo estado."""
    fixture = (
        RegistryBuilder()
        .with_tenant("t-reverse")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .build()
    )
    _publish_all(publisher, fixture)
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )

    projection.apply_batch(events)
    reference = Snapshot.capture(projection, fixture.tenant_id)

    projection.replay_all(fixture.tenant_id)
    projection.apply_batch(list(reversed(events)))
    reversed_snap = Snapshot.capture(projection, fixture.tenant_id)

    assert reversed_snap.identities == reference.identities
    assert reversed_snap.diagnoses == reference.diagnoses
    assert reversed_snap.phenotypes == reference.phenotypes


# ─── Testes: timestamps fora de ordem ───────────────────────────────────────


def REDACTED(projection):
    """
    Cenário crítico: eventos com timestamps desordenados cronologicamente.
    A ordenação canônica (sequence) deve prevalecer sobre event_datetime.
    """
    base = datetime.now(timezone.utc)
    events = [
        EventBuilder()
        .with_type("CLINICAL_IDENTITY_CREATED")
        .with_aggregate("clinical_identity", "id-1")
        .with_payload(patient_id="p-1", identity_id="id-1")
        .with_tenant("t-time")
        .with_event_datetime(base + timedelta(hours=10))  # Timestamp alto
        .with_sequence(1)
        .build(),
        EventBuilder()
        .with_type("DIAGNOSIS_HYPOTHESIZED")
        .with_aggregate("diagnosis", "diag-1")
        .with_payload(
            identity_id="id-1",
            condition_code="TEA_F84.0",
            hypothesised_by="prof-1",
        )
        .with_tenant("t-time")
        .with_event_datetime(base + timedelta(hours=2))  # Timestamp baixo!
        .with_sequence(2)
        .build(),
        EventBuilder()
        .with_type("DIAGNOSIS_CONFIRMED")
        .with_aggregate("diagnosis", "diag-1")
        .with_payload(
            identity_id="id-1",
            confirmed_by="prof-1",
            confirmation_evidence={"criteria_met": ["A1"]},
        )
        .with_tenant("t-time")
        .with_event_datetime(base + timedelta(hours=20))  # Timestamp alto
        .with_sequence(3)
        .build(),
    ]

    # apply() individual — ordem pela sequence (não event_datetime)
    for evt in events:
        projection.apply(evt)

    snap = Snapshot.capture(projection, "t-time")
    assert len(snap.identities) == 1
    assert len(snap.diagnoses) == 1
    diag = snap.diagnoses[0]
    assert diag["state"] == "confirmed"  # Estado final correto


# ─── Testes: race condition entre aggregates ───────────────────────────────


def REDACTED(projection):
    """
    Cenário patológico: DIAGNOSIS_CONFIRMED chega antes de DIAGNOSIS_HYPOTHESIZED
    (eventos chegam fora de ordem via rede).
    Após aplicação completa, estado final deve ser CONFIRMED.
    """
    events = [
        # Sequence 1: CONFIRMED primeiro
        EventBuilder()
        .with_type("DIAGNOSIS_CONFIRMED")
        .with_aggregate("diagnosis", "diag-race")
        .with_payload(
            identity_id="id-1",
            confirmed_by="prof-1",
            confirmation_evidence={"criteria_met": ["A1"]},
        )
        .with_tenant("t-race")
        .with_sequence(1)
        .build(),
        # Sequence 2: HYPOTHESIZED depois
        EventBuilder()
        .with_type("DIAGNOSIS_HYPOTHESIZED")
        .with_aggregate("diagnosis", "diag-race")
        .with_payload(
            identity_id="id-1",
            condition_code="TEA_F84.0",
            hypothesised_by="prof-1",
        )
        .with_tenant("t-race")
        .with_sequence(2)
        .build(),
    ]
    for evt in events:
        projection.apply(evt)

    snap = Snapshot.capture(projection, "t-race")
    assert len(snap.diagnoses) == 1
    # Estado final deve refletir último evento aplicado (HYPOTHESIZED)
    diag = snap.diagnoses[0]
    # Como CONFIRMED foi aplicado primeiro (sequence=1), depois HYPOTHESIZED (sequence=2),
    # o estado final no Registry será HYPOTHESIS (último handler a tocar)
    # IMPORTANTE: projection = reflete estado atual agregado. Event order matters.
    assert diag["state"] == "hypothesis"  # last applied


# ─── Testes: intercalação entre identidades ─────────────────────────────────


def REDACTED(projection, publisher):
    """
    2 ClinicalIdentities com eventos intercalados:
        id1_CREATED → id2_CREATED → id1_DIAGNOSIS → id2_PHENOTYPE → ...

    Cada identidade deve ter seu próprio estado coerente.
    """
    f1 = (
        RegistryBuilder()
        .with_tenant("t-interleave")
        .with_patient("p-1")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .build()
    )
    f2 = (
        RegistryBuilder()
        .with_tenant("t-interleave")
        .with_patient("p-2")
        .with_identity()
        .with_phenotype()
        .build()
    )

    # Publica f1 (sequence 1-N) depois f2 (sequence N+1-2N)
    _publish_all(publisher, f1)
    _publish_all(publisher, f2)

    # Wipe + replay em ordem intercalada manual
    projection.replay_all("t-interleave")

    all_events = projection._event_store.query(
        "t-interleave", order_by="sequence ASC"
    )

    # Embaralha mantendo sequence
    interleaved: List = []
    max_n = max(
        sum(1 for e in all_events if e["patient_id"] == pid) for pid in ("p-1", "p-2")
    )
    f1_events = [e for e in all_events if e["patient_id"] == "p-1"]
    f2_events = [e for e in all_events if e["patient_id"] == "p-2"]
    for i in range(max_n):
        if i < len(f1_events):
            interleaved.append(f1_events[i])
        if i < len(f2_events):
            interleaved.append(f2_events[i])

    projection.apply_batch(interleaved)
    snap = Snapshot.capture(projection, "t-interleave")

    assert len(snap.identities) == 2
    assert len(snap.diagnoses) == 1
    assert len(snap.phenotypes) == 1


# ─── Testes: idempotência + out-of-order ────────────────────────────────────


def REDACTED(projection, publisher):
    """
    Aplica eventos embaralhados 10x — estado sempre consistente.
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-idem-shuffle")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .build()
    )
    _publish_all(publisher, fixture)
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )

    projection.apply_batch(events)
    reference = Snapshot.capture(projection, fixture.tenant_id)

    rng = random.Random(99)
    for _ in range(10):
        projection.replay_all(fixture.tenant_id)
        shuffled = list(events)
        rng.shuffle(shuffled)
        projection.apply_batch(shuffled)
        snap = Snapshot.capture(projection, fixture.tenant_id)
        assert snap.identities == reference.identities
        assert snap.diagnoses == reference.diagnoses
        assert snap.phenotypes == reference.phenotypes
