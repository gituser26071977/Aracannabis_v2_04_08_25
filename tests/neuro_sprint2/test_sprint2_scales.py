"""
Sprint 2 — Testes das 6 escalas adicionadas.

Cobre:
    - M-CHAT-R/F (rastreamento TEA 16-30 meses)
    - CARS2 (avaliação clínica ≥2 anos)
    - ATEC (longitudinal 2-12 anos)
    - Vineland-3 (adaptativo 0-90 anos)
    - SNAP-IV (TDAH/TOD 6-17 anos)
    - SRS-2 (rastreamento social ≥2,5 anos)

Para cada escala: spec metadata, scoring (borda/limites), interpretação
por banda, validação JSON Schema, applicability por idade.
"""

from __future__ import annotations

import pytest

from araos.specialties.neurodevelopmental.scales.builtins import (
    ATEC_SPEC,
    CARS2_SPEC,
    MCHAT_SPEC,
    SNAP_SPEC,
    SRS2_SPEC,
    VINELAND_SPEC,
    _register_all,
)
from araos.specialties.neurodevelopmental.scales.registry import ScaleRegistry
from araos.specialties.neurodevelopmental.scales.runner import (
    ScaleRunner,
    ScaleValidationError,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    ScaleRegistry.clear()
    _register_all()
    yield
    ScaleRegistry.clear()


# ─── Auto-registro ─────────────────────────────────────────────────


def test_all_6_new_scales_registered():
    codes = set(ScaleRegistry.codes())
    expected = {"MCHAT", "CARS2", "ATEC", "VINELAND", "SNAP", "SRS2"}
    assert expected.issubset(codes), (
        f"Faltam escalas: {expected - codes}. Presentes: {codes}"
    )


def REDACTED():
    """24 meses → escalas TEA devem estar presentes; TDAH não."""
    for age in [18, 24, 30, 36, 60, 120, 192, 240]:
        codes = {s.code for s in ScaleRegistry.list_by_age(age)}
        # TEA scales: MCHAT, CARS2, ATEC, VINELAND, SRS2
        # TDAH scales: SNAP
        if 18 <= age <= 30:
            assert "MCHAT" in codes
        if 24 <= age <= 72:
            assert "CARS2" in codes
        if 72 <= age <= 17 * 12:
            assert "SNAP" in codes
        if 30 <= age <= 18 * 12:
            assert "SRS2" in codes
        if 24 <= age <= 144:
            assert "ATEC" in codes


# ═══════════════════════════════════════════════════════════════════
# M-CHAT-R/F
# ═══════════════════════════════════════════════════════════════════


def _mchat_all_zero():
    return {f"q{i}": 0 for i in range(1, 21)}


def _mchat_all_one():
    return {f"q{i}": 1 for i in range(1, 21)}


def test_mchat_spec_metadata():
    assert MCHAT_SPEC.code == "MCHAT"
    assert MCHAT_SPEC.target_age_months == (16, 30)
    assert MCHAT_SPEC.json_schema["required"] == [
        f"q{i}" for i in range(1, 21)
    ]


def test_mchat_all_zero_low_risk():
    runner = ScaleRunner(MCHAT_SPEC)
    result = runner.run(_mchat_all_zero())
    assert result.scores["total"] == 0.0
    assert result.scores["critical_positives"] == 0.0
    interp = result.interpretation["total"]
    assert interp.band == "baixo_risco"


def test_mchat_total_3_medium_risk():
    """3 itens positivos (não-críticos) → risco médio."""
    runner = ScaleRunner(MCHAT_SPEC)
    responses = _mchat_all_zero()
    # itens não-críticos: 1, 3, 4, 6, 8, 10, 11, 12, 16, 17, 18, 19, 20
    for code in ("q1", "q3", "q4"):
        responses[code] = 1
    result = runner.run(responses)
    assert result.scores["total"] == 3.0
    assert result.scores["critical_positives"] == 0.0
    assert result.interpretation["total"].band == "medio_risco"


def REDACTED():
    runner = ScaleRunner(MCHAT_SPEC)
    responses = _mchat_all_zero()
    for code in (f"q{i}" for i in range(1, 9)):  # q1-q8
        responses[code] = 1
    result = runner.run(responses)
    assert result.scores["total"] == 8.0
    assert result.interpretation["total"].band == "alto_risco"


def REDACTED():
    """M-CHAT-R/F rule: ≥2 itens críticos positivos → alto risco."""
    runner = ScaleRunner(MCHAT_SPEC)
    responses = _mchat_all_zero()
    responses["q2"] = 1  # critical
    responses["q5"] = 1  # critical
    result = runner.run(responses)
    assert result.scores["total"] == 2.0
    assert result.scores["critical_positives"] == 2.0
    assert result.interpretation["total"].band == "alto_risco"


def REDACTED():
    """1 crítico positivo + total baixo → baixo risco com nota."""
    runner = ScaleRunner(MCHAT_SPEC)
    responses = _mchat_all_zero()
    responses["q2"] = 1
    result = runner.run(responses)
    assert result.scores["total"] == 1.0
    assert result.scores["critical_positives"] == 1.0
    interp = result.interpretation["total"]
    assert interp.band == "baixo_risco"
    assert "ATENÇÃO" in interp.recommendation


def test_mchat_rejects_invalid_value():
    runner = ScaleRunner(MCHAT_SPEC)
    bad = _mchat_all_zero()
    bad["q1"] = 2  # só 0/1 aceitos
    with pytest.raises(ScaleValidationError):
        runner.run(bad)


def REDACTED():
    """Chamando _score_mchat diretamente, sem schema, valida range e ausência."""
    from araos.specialties.neurodevelopmental.scales.builtins.mchat import (
        _score_mchat,
    )

    good = _mchat_all_zero()
    good["q2"] = 1
    scores = _score_mchat(good)
    assert scores["total"] == 1.0
    assert scores["critical_positives"] == 1.0

    # value inválido
    with pytest.raises(ValueError, match="0 .* ou 1"):
        _score_mchat({**good, "q1": 2})  # type: ignore[dict-item]
    # ausente
    bad = {f"q{i}": 0 for i in range(1, 21)}
    del bad["q5"]
    with pytest.raises(ValueError, match="q5 ausente"):
        _score_mchat(bad)


def REDACTED():
    """Total=8 sem ≥2 críticos → cai em 'alto_risco' pelo total."""
    runner = ScaleRunner(MCHAT_SPEC)
    responses = _mchat_all_zero()
    # 8 itens não-críticos em 1 (q1, q3, q4, q6, q8, q10, q11, q12)
    for code in ("q1", "q3", "q4", "q6", "q8", "q10", "q11", "q12"):
        responses[code] = 1
    result = runner.run(responses)
    assert result.scores["total"] == 8.0
    assert result.scores["critical_positives"] == 0.0
    assert result.interpretation["total"].band == "alto_risco"


def test_mchat_missing_question_raises():
    runner = ScaleRunner(MCHAT_SPEC)
    incomplete = {f"q{i}": 0 for i in range(1, 20)}  # falta q20
    with pytest.raises(ScaleValidationError, match="q20"):
        runner.run(incomplete)


def REDACTED():
    assert MCHAT_SPEC.is_applicable_for_age(40) is False
    assert MCHAT_SPEC.is_applicable_for_age(16) is True
    assert MCHAT_SPEC.is_applicable_for_age(30) is True


# ═══════════════════════════════════════════════════════════════════
# CARS2
# ═══════════════════════════════════════════════════════════════════


def _cars2_all(min_value: int = 1, max_value: int = 1) -> dict:
    """Helper: todos os 15 itens no mesmo valor (1-4)."""
    return {f"q{i}": min_value for i in range(1, 16)}


def test_cars2_spec_metadata():
    assert CARS2_SPEC.code == "CARS2"
    assert CARS2_SPEC.target_age_months == (24, 72)
    assert CARS2_SPEC.requires_training is True
    assert len(CARS2_SPEC.json_schema["required"]) == 15


def test_cars2_all_1_not_autistic():
    runner = ScaleRunner(CARS2_SPEC)
    result = runner.run(_cars2_all(1))
    assert result.scores["total"] == 15.0
    assert result.interpretation["total"].band == "nao_autista"


def REDACTED():
    """Cada item=2 → total=30 → entra em leve-moderado (limite)."""
    runner = ScaleRunner(CARS2_SPEC)
    result = runner.run(_cars2_all(2))
    assert result.scores["total"] == 30.0
    assert result.interpretation["total"].band == "autismo_leve_moderado"


def test_cars2_all_3_severo():
    """Cada item=3 → total=45 → severo."""
    runner = ScaleRunner(CARS2_SPEC)
    result = runner.run(_cars2_all(3))
    assert result.scores["total"] == 45.0
    assert result.interpretation["total"].band == "autismo_severo"


def test_cars2_all_4_max():
    runner = ScaleRunner(CARS2_SPEC)
    result = runner.run(_cars2_all(4))
    assert result.scores["total"] == 60.0
    assert result.interpretation["total"].band == "autismo_severo"


def test_cars2_rejects_zero():
    runner = ScaleRunner(CARS2_SPEC)
    bad = _cars2_all(1)
    bad["q1"] = 0
    with pytest.raises(ScaleValidationError, match="minimum"):
        runner.run(bad)


def test_cars2_rejects_value_above_4():
    runner = ScaleRunner(CARS2_SPEC)
    bad = _cars2_all(1)
    bad["q1"] = 5
    with pytest.raises(ScaleValidationError, match="maximum"):
        runner.run(bad)


def REDACTED():
    assert CARS2_SPEC.is_applicable_for_age(20) is False
    assert CARS2_SPEC.is_applicable_for_age(24) is True
    assert CARS2_SPEC.is_applicable_for_age(72) is True
    assert CARS2_SPEC.is_applicable_for_age(80) is False


# ═══════════════════════════════════════════════════════════════════
# ATEC
# ═══════════════════════════════════════════════════════════════════


def _atec_all_zero():
    return {f"at{i}": 0 for i in range(1, 40)}


def test_atec_spec_metadata():
    assert ATEC_SPEC.code == "ATEC"
    assert ATEC_SPEC.target_age_months == (24, 144)
    # 4 sub-escalas + total
    assert len(ATEC_SPEC.subscales) == 5


def test_atec_all_zero_minimal():
    runner = ScaleRunner(ATEC_SPEC)
    result = runner.run(_atec_all_zero())
    assert result.scores["total"] == 0.0
    assert result.scores["speech_language"] == 0.0
    assert result.scores["sociability"] == 0.0
    assert result.scores["sensory_cognitive"] == 0.0
    assert result.scores["health_behavior"] == 0.0
    assert result.interpretation["total"].band == "leve"


def test_atec_total_in_leve_band():
    """Total=20 → leve."""
    runner = ScaleRunner(ATEC_SPEC)
    responses = _atec_all_zero()
    # 10 itens em 1
    for code in ("at1", "at2", "at3", "at4", "at5",
                 "at8", "at9", "at10", "at11", "at12"):
        responses[code] = 1
    result = runner.run(responses)
    assert result.scores["total"] == 10.0
    assert result.interpretation["total"].band == "leve"


def test_atec_total_in_moderado_band():
    """Total=40 → moderado."""
    runner = ScaleRunner(ATEC_SPEC)
    responses = _atec_all_zero()
    for code in (f"at{i}" for i in range(1, 21)):  # 20 itens em 2
        responses[code] = 2
    result = runner.run(responses)
    # 20 itens × 2 = 40
    assert result.scores["total"] == 40.0
    assert result.interpretation["total"].band == "moderado"


def test_atec_total_in_severo_band():
    """Total ~ 65 → severo."""
    runner = ScaleRunner(ATEC_SPEC)
    responses = _atec_all_zero()
    for code in (f"at{i}" for i in range(1, 27)):  # 26 itens max=2
        responses[code] = 2
    for code in (f"at{i}" for i in range(27, 32)):  # 5 itens de saúde em 3
        responses[code] = 3
    # 26*2 + 5*3 = 52+15 = 67
    result = runner.run(responses)
    assert result.scores["total"] == 67.0
    assert result.interpretation["total"].band == "severo"


def test_atec_total_muito_severo():
    """Total=100+ → muito severo."""
    runner = ScaleRunner(ATEC_SPEC)
    responses = _atec_all_zero()
    # 3 sub-escalas de max=2 ficam em 2 (26 itens × 2 = 52)
    for code in (f"at{i}" for i in range(1, 27)):
        responses[code] = 2
    # Saúde (max=3) toda em 3 (13 × 3 = 39)
    for code in (f"at{i}" for i in range(27, 40)):
        responses[code] = 3
    # 52 + 39 = 91
    result = runner.run(responses)
    assert result.scores["total"] == 91.0
    assert result.interpretation["total"].band == "muito_severo"


def REDACTED():
    """Sub-escala Saúde ≥ 20 deve disparar nota de atenção."""
    runner = ScaleRunner(ATEC_SPEC)
    responses = _atec_all_zero()
    for code in (f"at{i}" for i in range(27, 40)):  # 13 itens saúde × 3 = 39
        responses[code] = 3
    result = runner.run(responses)
    assert result.scores["health_behavior"] == 39.0
    assert "ATENÇÃO" in result.interpretation["total"].recommendation


def test_atec_rejects_value_above_max():
    runner = ScaleRunner(ATEC_SPEC)
    bad = _atec_all_zero()
    bad["at1"] = 3  # speech max é 2
    with pytest.raises(ScaleValidationError, match="maximum"):
        runner.run(bad)


def REDACTED():
    """Valida que cada sub-domínio rejeita valor fora do range próprio."""
    runner = ScaleRunner(ATEC_SPEC)
    # speech (at1-at7) max=2
    bad = _atec_all_zero(); bad["at3"] = 3
    with pytest.raises(ScaleValidationError, match="at3"):
        runner.run(bad)
    # sociability (at8-at17) max=2
    bad = _atec_all_zero(); bad["at10"] = 3
    with pytest.raises(ScaleValidationError, match="at10"):
        runner.run(bad)
    # sensory (at18-at26) max=2
    bad = _atec_all_zero(); bad["at20"] = 3
    with pytest.raises(ScaleValidationError, match="at20"):
        runner.run(bad)
    # health (at27-at39) max=3
    bad = _atec_all_zero(); bad["at30"] = 4
    with pytest.raises(ScaleValidationError, match="at30"):
        runner.run(bad)


def REDACTED():
    """Valida que cada sub-domínio rejeita item ausente."""
    runner = ScaleRunner(ATEC_SPEC)
    # speech
    bad = _atec_all_zero(); del bad["at3"]
    with pytest.raises(ScaleValidationError, match="at3"):
        runner.run(bad)
    # sociability
    bad = _atec_all_zero(); del bad["at10"]
    with pytest.raises(ScaleValidationError, match="at10"):
        runner.run(bad)
    # sensory
    bad = _atec_all_zero(); del bad["at20"]
    with pytest.raises(ScaleValidationError, match="at20"):
        runner.run(bad)
    # health
    bad = _atec_all_zero(); del bad["at30"]
    with pytest.raises(ScaleValidationError, match="at30"):
        runner.run(bad)


def REDACTED():
    """Chamando _score_atec diretamente, sem schema, valida domínio."""
    from araos.specialties.neurodevelopmental.scales.builtins.atec import (
        _score_atec,
    )

    good = {f"at{i}": 1 for i in range(1, 40)}
    scores = _score_atec(good)
    assert scores["total"] == 39.0

    # Fora do range numérico (mesmo se schema aceitasse)
    with pytest.raises(ValueError, match="inteiro 0-2"):
        _score_atec({**good, "at1": "x"})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="Questão at5 ausente"):
        bad = {f"at{i}": 1 for i in range(1, 40)}
        del bad["at5"]
        _score_atec(bad)

    # ─── Cobertura por sub-escala (sociability, sensory, health) ───
    # sociability max=2 → valor >2 levanta
    with pytest.raises(ValueError, match="at12 deve ser inteiro 0-2"):
        bad = {f"at{i}": 1 for i in range(1, 40)}
        bad["at12"] = 5
        _score_atec(bad)
    # sociability: missing
    with pytest.raises(ValueError, match="Questão at15 ausente"):
        bad = {f"at{i}": 1 for i in range(1, 40)}
        del bad["at15"]
        _score_atec(bad)
    # sensory max=2
    with pytest.raises(ValueError, match="at22 deve ser inteiro 0-2"):
        bad = {f"at{i}": 1 for i in range(1, 40)}
        bad["at22"] = 4
        _score_atec(bad)
    # sensory: missing
    with pytest.raises(ValueError, match="Questão at25 ausente"):
        bad = {f"at{i}": 1 for i in range(1, 40)}
        del bad["at25"]
        _score_atec(bad)
    # health max=3
    with pytest.raises(ValueError, match="at32 deve ser inteiro 0-3"):
        bad = {f"at{i}": 1 for i in range(1, 40)}
        bad["at32"] = 5
        _score_atec(bad)
    # health: missing
    with pytest.raises(ValueError, match="Questão at35 ausente"):
        bad = {f"at{i}": 1 for i in range(1, 40)}
        del bad["at35"]
        _score_atec(bad)


def REDACTED():
    assert ATEC_SPEC.is_applicable_for_age(20) is False
    assert ATEC_SPEC.is_applicable_for_age(24) is True
    assert ATEC_SPEC.is_applicable_for_age(144) is True
    assert ATEC_SPEC.is_applicable_for_age(200) is False


# ═══════════════════════════════════════════════════════════════════
# VINELAND-3 (versão reduzida)
# ═══════════════════════════════════════════════════════════════════


def _vineland_all_two():
    """Todos os 20 itens (incluindo motor) com resposta 2."""
    return {f"vn{i}": 2 for i in range(1, 21)}


def _vineland_three_domains_two():
    """Sem domínio motor (aplicado a >6 anos)."""
    items = [f"vn{i}" for i in range(1, 16)]  # vn1-vn15 (3 domínios × 5)
    return {c: 2 for c in items}


def test_vineland_spec_metadata():
    assert VINELAND_SPEC.code == "VINELAND"
    assert VINELAND_SPEC.target_age_months[0] == 0
    assert VINELAND_SPEC.requires_training is True
    # Required = sem motor (opcional). 15 itens.
    assert len(VINELAND_SPEC.json_schema["required"]) == 15


def test_vineland_with_motor_max():
    """20 itens × 2 = 40 → acima do esperado."""
    runner = ScaleRunner(VINELAND_SPEC)
    result = runner.run(_vineland_all_two())
    assert result.scores["total"] == 40.0
    assert result.scores["communication"] == 10.0
    assert result.scores["daily_living"] == 10.0
    assert result.scores["socialization"] == 10.0
    assert result.scores["motor_skills"] == 10.0
    assert result.interpretation["total"].band == "acima_esperado"


def test_vineland_without_motor():
    """Sem motor → composite considera apenas 3 domínios (max 30)."""
    runner = ScaleRunner(VINELAND_SPEC)
    result = runner.run(_vineland_three_domains_two())
    assert result.scores["total"] == 30.0
    assert result.scores["motor_skills"] == 0.0
    assert result.interpretation["total"].band == "adequado"


def test_vineland_below_expected():
    """Total=10 → bem abaixo do esperado."""
    runner = ScaleRunner(VINELAND_SPEC)
    responses = {}
    # 5 itens em 2 = 10
    for i in range(1, 6):
        responses[f"vn{i}"] = 2
    for i in range(6, 21):
        responses[f"vn{i}"] = 0
    result = runner.run(responses)
    assert result.scores["total"] == 10.0
    assert result.interpretation["total"].band == "bem_abaixo_esperado"


def REDACTED():
    """Domínio com escore ≤ 1 deve disparar nota."""
    runner = ScaleRunner(VINELAND_SPEC)
    responses = _vineland_three_domains_two()
    # Zera a comunicação inteira
    for i in range(1, 6):
        responses[f"vn{i}"] = 0
    result = runner.run(responses)
    # Total = 20 (ainda dentro de "abaixo esperado")
    assert result.scores["communication"] == 0
    assert result.interpretation["total"].band == "abaixo_esperado"
    assert "ATENÇÃO" in result.interpretation["total"].recommendation
    assert "Comunicação" in result.interpretation["total"].recommendation


def REDACTED():
    runner = ScaleRunner(VINELAND_SPEC)
    bad = _vineland_three_domains_two()
    bad["vn1"] = 3
    with pytest.raises(ScaleValidationError, match="maximum"):
        runner.run(bad)


def REDACTED():
    runner = ScaleRunner(VINELAND_SPEC)
    incomplete = {f"vn{i}": 1 for i in range(6, 16)}  # falta vn1-vn5
    with pytest.raises(ScaleValidationError, match="vn1"):
        runner.run(incomplete)


# ═══════════════════════════════════════════════════════════════════
# SNAP-IV
# ═══════════════════════════════════════════════════════════════════


def _snap_all(value: int = 0) -> dict:
    return {f"sn{i}": value for i in range(1, 27)}


def test_snap_spec_metadata():
    assert SNAP_SPEC.code == "SNAP"
    assert SNAP_SPEC.target_age_months == (72, 17 * 12)
    assert len(SNAP_SPEC.json_schema["required"]) == 26


def REDACTED():
    runner = ScaleRunner(SNAP_SPEC)
    result = runner.run(_snap_all(0))
    assert result.scores["inattention_mean"] == 0.0
    assert result.scores["hyperactivity_mean"] == 0.0
    assert result.scores["odd_mean"] == 0.0
    assert result.scores["grand_mean"] == 0.0
    assert result.interpretation["grand_mean"].band == "negativo"


def test_snap_inattentive_positive():
    """Apenas desatenção ≥ 1.0 e < 1.5 (TOD e hip < 1.0) → tdah_desatento sugestivo."""
    runner = ScaleRunner(SNAP_SPEC)
    responses = _snap_all(0)
    for i in range(1, 10):  # 9 itens desatenção
        responses[f"sn{i}"] = 1
    result = runner.run(responses)
    # 9 * 1 / 9 = 1.0 → sugestivo (não severo)
    assert result.scores["inattention_mean"] == 1.0
    assert result.scores["hyperactivity_mean"] == 0.0
    assert result.interpretation["grand_mean"].band == "tdah_desatento_sugestivo"


def test_snap_combined_positive():
    """Desatenção + Hiperatividade ≥ 1.0 → combinado."""
    runner = ScaleRunner(SNAP_SPEC)
    responses = _snap_all(0)
    for i in range(1, 19):  # 18 itens inat+hip
        responses[f"sn{i}"] = 1
    result = runner.run(responses)
    assert result.scores["inattention_mean"] == 1.0
    assert result.scores["hyperactivity_mean"] == 1.0
    assert result.interpretation["grand_mean"].band == "tdah_combinado_sugestivo"


def test_snap_severity_escalation():
    """Qualquer sub-escala com mean ≥ 1.5 → gravidade clínica elevada."""
    runner = ScaleRunner(SNAP_SPEC)
    responses = _snap_all(0)
    # 9 itens inat × 2 = 18 / 9 = 2.0 → severo
    for i in range(1, 10):
        responses[f"sn{i}"] = 2
    result = runner.run(responses)
    assert result.scores["inattention_mean"] == 2.0
    assert result.interpretation["grand_mean"].band == "tdah_desatento_severo"


def test_snap_odd_comorbidity():
    """TOD ≥ 1.0 com TDAH qualquer → comorbidade opositivo-desafiadora."""
    runner = ScaleRunner(SNAP_SPEC)
    responses = _snap_all(0)
    for i in range(1, 10):  # inat
        responses[f"sn{i}"] = 1
    for i in range(19, 27):  # TOD
        responses[f"sn{i}"] = 1
    result = runner.run(responses)
    assert "comorbidade" in result.interpretation["grand_mean"].label_pt.lower()


def test_snap_rejects_out_of_range():
    runner = ScaleRunner(SNAP_SPEC)
    bad = _snap_all(0)
    bad["sn1"] = 4
    with pytest.raises(ScaleValidationError, match="maximum"):
        runner.run(bad)


def REDACTED():
    assert SNAP_SPEC.is_applicable_for_age(60) is False
    assert SNAP_SPEC.is_applicable_for_age(72) is True
    assert SNAP_SPEC.is_applicable_for_age(17 * 12) is True
    assert SNAP_SPEC.is_applicable_for_age(20 * 12) is False


# ═══════════════════════════════════════════════════════════════════
# SRS-2
# ═══════════════════════════════════════════════════════════════════


def _srs_all(value: int = 0) -> dict:
    return {f"sr{i}": value for i in range(1, 26)}


def test_srs2_spec_metadata():
    assert SRS2_SPEC.code == "SRS2"
    assert SRS2_SPEC.target_age_months == (30, 18 * 12)
    assert len(SRS2_SPEC.json_schema["required"]) == 25


def test_srs2_all_zero_within_expected():
    runner = ScaleRunner(SRS2_SPEC)
    result = runner.run(_srs_all(0))
    assert result.scores["total"] == 0.0
    assert result.interpretation["total"].band == "dentro_esperado"


def REDACTED():
    """Total=15 → ainda dentro do esperado (≤15)."""
    runner = ScaleRunner(SRS2_SPEC)
    responses = _srs_all(0)
    for i in range(1, 16):  # 15 itens em 1
        responses[f"sr{i}"] = 1
    result = runner.run(responses)
    assert result.scores["total"] == 15.0
    assert result.interpretation["total"].band == "dentro_esperado"


def test_srs2_leve_band():
    runner = ScaleRunner(SRS2_SPEC)
    responses = _srs_all(1)
    # 25 itens × 1 = 25
    result = runner.run(responses)
    assert result.scores["total"] == 25.0
    assert result.interpretation["total"].band == "leve"


def test_srs2_moderado_band():
    runner = ScaleRunner(SRS2_SPEC)
    responses = _srs_all(2)
    # 25 × 2 = 50
    result = runner.run(responses)
    assert result.scores["total"] == 50.0
    assert result.interpretation["total"].band == "moderado"


def test_srs2_severo_band():
    runner = ScaleRunner(SRS2_SPEC)
    responses = _srs_all(3)
    # 25 × 3 = 75
    result = runner.run(responses)
    assert result.scores["total"] == 75.0
    assert result.interpretation["total"].band == "severo"


def test_srs2_high_subscale_atencao():
    """Sub-escala com 12+ dispara ATENÇÃO."""
    runner = ScaleRunner(SRS2_SPEC)
    responses = _srs_all(0)
    # Consciência social (sr1-sr5) toda em 3
    for i in range(1, 6):
        responses[f"sr{i}"] = 3
    result = runner.run(responses)
    assert result.scores["social_awareness"] == 15.0
    assert "ATENÇÃO" in result.interpretation["total"].recommendation
    assert "Consciência Social" in result.interpretation["total"].recommendation


def test_srs2_rejects_value_4():
    runner = ScaleRunner(SRS2_SPEC)
    bad = _srs_all(0)
    bad["sr1"] = 4
    with pytest.raises(ScaleValidationError, match="maximum"):
        runner.run(bad)


def REDACTED():
    assert SRS2_SPEC.is_applicable_for_age(24) is False
    assert SRS2_SPEC.is_applicable_for_age(30) is True
    assert SRS2_SPEC.is_applicable_for_age(18 * 12) is True


# ═══════════════════════════════════════════════════════════════════
# Integração com Sprint 1 (regressão)
# ═══════════════════════════════════════════════════════════════════


def test_gad7_still_works():
    """Sanity check: Sprint 1 continua funcionando com Sprint 2 ativo."""
    from araos.specialties.neurodevelopmental.scales.builtins import GAD7_SPEC
    runner = ScaleRunner(GAD7_SPEC)
    result = runner.run({f"q{i}": 1 for i in range(1, 8)})
    assert result.scores["total"] == 7.0
    assert result.interpretation["total"].band == "leve"


def test_phq9_still_works():
    from araos.specialties.neurodevelopmental.scales.builtins import PHQ9_SPEC
    runner = ScaleRunner(PHQ9_SPEC)
    result = runner.run({f"q{i}": 0 for i in range(1, 10)})
    assert result.scores["total"] == 0.0
    assert result.interpretation["total"].band == "minimo"


def test_total_scales_count():
    """Sprint 1 (2) + Sprint 2 (6) = 8 escalas total."""
    assert len(ScaleRegistry.codes()) == 8
