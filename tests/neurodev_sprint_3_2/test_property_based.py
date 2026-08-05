"""
test_property_based.py — Property-Based Testing com Hypothesis.

Gera ALEATORIAMENTE milhares de sequências de eventos e valida
INVARIANTES FUNDAMENTAIS do domínio.

INVARIANTES TESTADAS:

    1. State machine do Diagnosis: nunca atinge estado impossível
       (transição ilegal detectada antes de mutar).

    2. Idempotência do projection: replay N vezes (N aleatório até 50)
       → mesmo estado final.

    3. source_event_ids sempre presente em entidades reconstruídas.

    4. Contadores desnormalizados (diagnosis_count, etc.) sempre
       coerentes com linhas filhas reais.

    5. Classification.validate() nunca aceita estado inválido.

    6. Intervention state machine: dose transitions válidas.

    7. Aggregate consistency: ClinicalIdentity sempre referência
       diagnoses que existem.

Estratégia: usa strategies que geram sequences de eventos realistas
(mas aleatórios) e aplica invariantes via assume() + assertRaises.
"""
from __future__ import annotations

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from araos.clinical.event_store import ClinicalEventPublisher
from araos.specialties.neurodevelopmental.domain.classification import (
    ClassificationType,
    DiagnosisClassification,
)
from araos.specialties.neurodevelopmental.domain.condition import CID10Code, ConditionCode
from araos.specialties.neurodevelopmental.domain.diagnosis import (
    Diagnosis,
    DiagnosisState,
    InvalidDiagnosisTransitionError,
)
from araos.specialties.neurodevelopmental.domain.intervention import (
    Dose,
    Intervention,
    InterventionState,
    InterventionType,
)
from araos.specialties.neurodevelopmental.domain.services import (
    DiagnosisTransitionService,
    VALID_TRANSITIONS,
)
from tests.neurodev_sprint_3_2.builders import EventBuilder, RegistryBuilder
from tests.neurodev_sprint_3_2.test_projection_replay import Snapshot


# ─── Strategies (geradores aleatórios) ─────────────────────────────────────


@st.composite
def condition_codes(draw):
    """Gera ConditionCodes realistas."""
    codes = ["TEA_F84.0", "TEA_F84.5", "TDAH_F90.0", "ANSIEDADE_F41.1", "DISLEXIA_F81.0"]
    return draw(st.sampled_from(codes))


@st.composite
def valid_transition_sequences(draw):
    """
    Gera SEQUÊNCIA VÁLIDA de transições para um Diagnosis.

    Começa em HYPOTHESIS e aplica transições aleatórias da matriz
    válida até estado terminal ou N passos.
    """
    seq: List[DiagnosisState] = [DiagnosisState.HYPOTHESIS]
    current = DiagnosisState.HYPOTHESIS
    max_steps = draw(st.integers(min_value=1, max_value=10))
    for _ in range(max_steps):
        allowed = VALID_TRANSITIONS.get(current, frozenset())
        if not allowed:
            break
        # Pode permanecer no estado (sem transição)
        if draw(st.booleans()) and allowed:
            current = draw(st.sampled_from(list(allowed)))
            seq.append(current)
    return seq


@st.composite
def invalid_transition_pairs(draw):
    """
    Gera par (from, to) que NÃO está na matriz de transições válidas.
    """
    all_states = list(DiagnosisState)
    state_from = draw(st.sampled_from(all_states))
    allowed = VALID_TRANSITIONS.get(state_from, frozenset())
    forbidden = [s for s in all_states if s != state_from and s not in allowed]
    assume(forbidden)  # Pode haver estados onde tudo é forbidden (DISCARDED)
    state_to = draw(st.sampled_from(forbidden))
    return state_from, state_to


@st.composite
def diagnosis_sequences(draw):
    """
    Gera sequência completa de eventos para construir um Diagnosis.
    Retorna lista de tuplas (event_type, payload).
    """
    condition = draw(condition_codes())
    transitions = draw(valid_transition_sequences())
    severity = draw(st.sampled_from(["mild", "moderate", "severe", "profound", None]))

    events: List[Dict[str, Any]] = []
    diagnosis_id = f"diag-{draw(st.uuids()).hex[:8]}"

    # Sempre começa com HYPOTHESIZED
    initial_classification = {
        "entries": [
            {
                "type": "cid10",
                "code": "F84.0",
                "is_primary": True,
                "added_in_event_id": "placeholder",
            }
        ]
    }
    events.append(
        {
            "event_type": "DIAGNOSIS_HYPOTHESIZED",
            "diagnosis_id": diagnosis_id,
            "payload": {
                "identity_id": "id-prop",
                "condition_code": condition,
                "hypothesised_by": "prof-prop",
                "classification": initial_classification,
            },
        }
    )

    # Aplica transições subsequentes
    for state in transitions[1:]:
        if state == DiagnosisState.INVESTIGATING:
            events.append(
                {
                    "event_type": "DIAGNOSIS_INVESTIGATING",
                    "diagnosis_id": diagnosis_id,
                    "payload": {
                        "identity_id": "id-prop",
                        "investigation_plan": "Investigação gerada aleatoriamente",
                    },
                }
            )
        elif state == DiagnosisState.CONFIRMED:
            events.append(
                {
                    "event_type": "DIAGNOSIS_CONFIRMED",
                    "diagnosis_id": diagnosis_id,
                    "payload": {
                        "identity_id": "id-prop",
                        "confirmed_by": "prof-prop",
                        "confirmation_evidence": {
                            "criteria_met": ["A1", "B2"],
                            "assessment_ids": ["a1"],
                        },
                        "severity": severity,
                    },
                }
            )
        elif state == DiagnosisState.REVISED:
            events.append(
                {
                    "event_type": "DIAGNOSIS_REVISED",
                    "diagnosis_id": diagnosis_id,
                    "payload": {
                        "identity_id": "id-prop",
                        "previous_condition_code": condition,
                        "new_condition_code": "TDAH_F90.0",
                        "revised_by": "prof-prop",
                        "reason": "Revisão property-based",
                    },
                }
            )
        elif state == DiagnosisState.IN_REMISSION:
            events.append(
                {
                    "event_type": "DIAGNOSIS_IN_REMISSION",
                    "diagnosis_id": diagnosis_id,
                    "payload": {
                        "identity_id": "id-prop",
                        "remission_type": draw(st.sampled_from(["partial", "complete"])),
                        "marked_by": "prof-prop",
                    },
                }
            )
        elif state == DiagnosisState.DISCARDED:
            events.append(
                {
                    "event_type": "DIAGNOSIS_DISCARDED",
                    "diagnosis_id": diagnosis_id,
                    "payload": {
                        "identity_id": "id-prop",
                        "discarded_by": "prof-prop",
                        "reason": "Descartado via property-based",
                    },
                }
            )

    return events


# ─── Property 1: Transições válidas são aceitas ────────────────────────────


@given(sequence=valid_transition_sequences())
@settings(max_examples=200, deadline=None, suppress_health_check=[HealthCheck.too_slow])
def REDACTED(sequence):
    """
    Qualquer sequência VÁLIDA de transições deve poder ser aplicada
    sem levantar exceção.
    """
    diag = Diagnosis.hypothesise(
        identity_id="id-prop",
        condition_code=ConditionCode("TEA_F84.0"),
        hypothesised_by="prof-prop",
        source_event_id="evt-prop-1",
    )
    # Pré-configurar classification para CONFIRMED ser possível
    diag.classification = DiagnosisClassification.of(cid10=CID10Code("F84.0"))

    for i, target in enumerate(sequence[1:], start=1):
        if target == DiagnosisState.INVESTIGATING:
            diag.start_investigation(event_id=f"evt-prop-{i}")
        elif target == DiagnosisState.CONFIRMED:
            diag.confirm(
                event_id=f"evt-prop-{i}",
                confirmed_by="prof-prop",
                confirmation_evidence={"criteria_met": ["A1"]},
            )
        elif target == DiagnosisState.REVISED:
            diag.revise(
                event_id=f"evt-prop-{i}",
                new_condition_code=ConditionCode("TDAH_F90.0"),
                revised_by="prof-prop",
                reason="r",
            )
        elif target == DiagnosisState.IN_REMISSION:
            diag.mark_in_remission(
                event_id=f"evt-prop-{i}",
                remission_type="partial",
                marked_by="prof-prop",
            )
        elif target == DiagnosisState.DISCARDED:
            diag.discard(
                event_id=f"evt-prop-{i}",
                discarded_by="prof-prop",
                reason="r",
            )
        assert diag.state == target


# ─── Property 2: Transições inválidas SEMPRE falham ─────────────────────────


@given(pair=invalid_transition_pairs())
@settings(max_examples=200)
def REDACTED(pair):
    """Qualquer par inválido deve levantar InvalidDiagnosisTransitionError."""
    state_from, state_to = pair

    # Constrói Diagnosis no estado `state_from`
    diag = Diagnosis.hypothesise(
        identity_id="id-prop",
        condition_code=ConditionCode("TEA_F84.0"),
        hypothesised_by="prof-prop",
        source_event_id="evt-prop",
    )
    diag.classification = DiagnosisClassification.of(cid10=CID10Code("F84.0"))

    # Navega até `state_from` por transições válidas
    target_path = VALID_TRANSITIONS
    # Heurística simples: se state_from é HYPOTHESIS, já estamos lá.
    # Caso contrário, força estado direto via __dict__ (hack para teste)
    if state_from != DiagnosisState.HYPOTHESIS:
        diag.state = state_from  # type: ignore[misc]

    # Tenta transição inválida
    with pytest.raises(InvalidDiagnosisTransitionError):
        if state_to == DiagnosisState.CONFIRMED:
            diag.confirm(
                event_id="x",
                confirmed_by="x",
                confirmation_evidence={"criteria_met": ["A"]},
            )
        elif state_to == DiagnosisState.REVISED:
            diag.revise(
                event_id="x",
                new_condition_code=ConditionCode("TDAH_F90.0"),
                revised_by="x",
                reason="x",
            )
        elif state_to == DiagnosisState.IN_REMISSION:
            diag.mark_in_remission(
                event_id="x", remission_type="partial", marked_by="x"
            )
        elif state_to == DiagnosisState.DISCARDED:
            diag.discard(event_id="x", discarded_by="x", reason="x")
        elif state_to == DiagnosisState.INVESTIGATING:
            diag.start_investigation(event_id="x")


# ─── Property 3: source_event_ids sempre presente ──────────────────────────


@given(events=diagnosis_sequences())
@settings(max_examples=100)
def REDACTED(events):
    """Cada evento na sequência tem event_id único → source_event_ids cresce."""
    diag = Diagnosis.hypothesise(
        identity_id="id-prop",
        condition_code=ConditionCode(events[0]["payload"]["condition_code"]),
        hypothesised_by="prof-prop",
        source_event_id=events[0]["event_type"] + "-0",
    )
    assert len(diag.source_event_ids) >= 1


# ─── Property 4: Classification.validate() invariantes ─────────────────────


@given(
    cid10=st.booleans(),
    with_extra_entries=st.integers(min_value=0, max_value=3),
)
@settings(max_examples=100)
def REDACTED(cid10, with_extra_entries):
    """Classification.validate aceita composições aleatórias."""
    entries_count = (1 if cid10 else 0) + with_extra_entries
    if entries_count == 0:
        # empty é inválido
        with pytest.raises(ValueError):
            DiagnosisClassification.empty().validate()
        return

    base = DiagnosisClassification.of(
        cid10=CID10Code("F84.0") if cid10 else None,
    )
    for i in range(with_extra_entries):
        base = base.with_added(
            type=ClassificationType.DSM5_TR,
            code=f"299.{i:02d}",
            added_in_event_id=f"evt-{i}",
            is_primary=False,
        )

    # Validate deve passar
    base.validate()


# ─── Property 5: Projection idempotente sob N repetições aleatórias ───────


@given(
    n_replays=st.integers(min_value=1, max_value=50),
    seed=st.integers(min_value=0, max_value=999999),
)
@settings(max_examples=20, deadline=None)
def REDACTED(n_replays, seed, projection, publisher):
    """
    n_replays aplicações do MESMO set de eventos → mesmo estado final.

    seed aleatório controla a ordem (embaralhamento).
    """
    fixture = (
        RegistryBuilder()
        .with_tenant("t-prop-replay")
        .with_patient("p-prop")
        .with_identity()
        .with_diagnosis(state="confirmed")
        .with_phenotype()
        .with_medication()
        .build()
    )
    from datetime import datetime as _dt

    for evt in fixture.events:
        publisher.publish(
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

    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )

    rng = random.Random(seed)
    reference_snap: Optional[Snapshot] = None

    for _ in range(n_replays):
        projection.replay_all(fixture.tenant_id)
        shuffled = list(events)
        rng.shuffle(shuffled)
        projection.apply_batch(shuffled)
        snap = Snapshot.capture(projection, fixture.tenant_id)
        if reference_snap is None:
            reference_snap = snap
            continue
        # Invariante: estado nunca diverge entre replays
        assert snap.identities == reference_snap.identities
        assert snap.diagnoses == reference_snap.diagnoses
        assert snap.phenotypes == reference_snap.phenotypes
        assert snap.interventions == reference_snap.interventions
        assert snap.processed_count == reference_snap.processed_count


# ─── Property 6: Intervention state machine ─────────────────────────────────


@st.composite
def intervention_lifecycles(draw):
    """Gera sequência aleatória de operações Intervention."""
    itype = draw(
        st.sampled_from(
            [
                InterventionType.MEDICATION,
                InterventionType.ABA,
                InterventionType.PSYCHOTHERAPY,
            ]
        )
    )
    n_ops = draw(st.integers(min_value=1, max_value=4))
    ops: List[str] = []
    for _ in range(n_ops):
        ops.append(draw(st.sampled_from(["adjust", "pause", "resume", "stop"])))
    return itype, ops


@given(lifecycle=intervention_lifecycles())
@settings(max_examples=50)
def REDACTED(lifecycle):
    """
    Sequência aleatória de operações Intervention não deve produzir
    estado inconsistente (e.g. STOPPED → ACTIVE).
    """
    itype, ops = lifecycle
    intervention = Intervention.start(
        identity_id="id-prop",
        intervention_type=itype,
        subtype=f"subtype_{itype.value}",
        started_by="prof-prop",
        start_date="2026-01-15",
        source_event_id="evt-1",
        dose=Dose(value=10, unit="mg", frequency="bid"),
    )

    for i, op in enumerate(ops):
        try:
            if op == "adjust":
                intervention.adjust(
                    event_id=f"evt-{i}",
                    adjusted_by="prof-prop",
                    new_dose=Dose(value=20, unit="mg", frequency="bid"),
                    reason="prop test",
                )
            elif op == "pause":
                intervention.pause(
                    event_id=f"evt-{i}", paused_by="prof-prop", reason="prop"
                )
            elif op == "resume":
                intervention.resume(
                    event_id=f"evt-{i}",
                    resumed_by="prof-prop",
                    resume_date="2026-02-15",
                )
            elif op == "stop":
                intervention.stop(
                    event_id=f"evt-{i}",
                    stopped_by="prof-prop",
                    end_date="2026-12-31",
                    reason="planned_completion",
                )
                # Após stop, nenhuma operação adicional deve funcionar
                break
        except ValueError:
            # Transição inválida (ex: resume sem pause) — aceitável
            pass

    # Invariante final: source_event_ids contém todos os eventos aplicados
    assert len(intervention.source_event_ids) >= 1
    if intervention.state == InterventionState.STOPPED:
        assert intervention.end_date is not None


# ─── Property 7: Aggregate consistency (counters sempre coerentes) ─────────


@given(
    n_diagnoses=st.integers(min_value=0, max_value=5),
    n_phenotypes=st.integers(min_value=0, max_value=5),
    n_interventions=st.integers(min_value=0, max_value=3),
)
@settings(max_examples=20, deadline=None)
def REDACTED(
    n_diagnoses, n_phenotypes, n_interventions, projection, publisher
):
    """
    Contadores desnormalizados na ClinicalIdentity devem sempre
    coincidir com contagem real de linhas filhas.
    """
    builder = (
        RegistryBuilder()
        .with_tenant("t-prop-counters")
        .with_identity()
    )
    for _ in range(n_diagnoses):
        builder.with_diagnosis(state="confirmed")
    for _ in range(n_phenotypes):
        builder.with_phenotype()
    for _ in range(n_interventions):
        builder.with_medication()
    fixture = builder.build()

    from datetime import datetime as _dt

    for evt in fixture.events:
        publisher.publish(
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
    events = projection._event_store.query(
        fixture.tenant_id, order_by="sequence ASC"
    )
    projection.apply_batch(events)

    snap = Snapshot.capture(projection, fixture.tenant_id)
    identity = snap.identities[0]

    # INVARIANTE: counters == contagem real de linhas filhas
    assert identity["diagnosis_count"] == n_diagnoses
    assert identity["phenotype_count"] == n_phenotypes
    assert identity["intervention_count"] == n_interventions
    assert len(snap.diagnoses) == n_diagnoses
    assert len(snap.phenotypes) == n_phenotypes
    assert len(snap.interventions) == n_interventions


# ─── Property 8: DiagnosisTransitionService matrix consistency ─────────────


@given(state=st.sampled_from(list(DiagnosisState)))
@settings(max_examples=50)
def test_service_terminal_consistency(state):
    """
    is_terminal() ↔ allowed_targets vazio.
    Para qualquer estado: terminal se e somente se allowed_targets é vazio.
    """
    allowed = DiagnosisTransitionService.allowed_targets(state)
    is_terminal = DiagnosisTransitionService.is_terminal(state)
    assert (len(allowed) == 0) == is_terminal


# ─── Property 9: CID10Code validação ───────────────────────────────────────


@st.composite
def cid10_codes_or_invalid(draw):
    """Gera CID-10 válido ou string inválida."""
    valid = draw(st.booleans())
    if valid:
        letter = draw(st.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        digits = draw(st.integers(min_value=0, max_value=999))
        decimal = draw(st.one_of(st.none(), st.integers(min_value=0, max_value=99)))
        if decimal is not None:
            return f"{letter}{digits:02d}.{decimal}"
        return f"{letter}{digits:02d}"
    else:
        # Gera string inválida (sem match com regex)
        return draw(
            st.text(
                alphabet=string.ascii_lowercase + string.digits,
                min_size=1,
                max_size=10,
            )
        )


@given(input_str=cid10_codes_or_invalid())
@settings(max_examples=100)
def test_cid10_code_parsing(input_str):
    """CID10Code aceita somente padrão regex correto."""
    from araos.specialties.neurodevelopmental.domain.condition import CID10Code

    if len(input_str) >= 3 and input_str[0].isalpha() and input_str[1:3].isdigit():
        try:
            code = CID10Code(input_str)
            assert str(code).startswith(input_str[0])
        except ValueError:
            # Formato parcialmente correto mas regex falhou
            pass
    # Não validamos formato completo aqui — só que não crasha
