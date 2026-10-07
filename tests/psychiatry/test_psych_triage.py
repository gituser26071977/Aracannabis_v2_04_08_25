"""Testes dos cenários críticos da triagem psiquiátrica."""

from __future__ import annotations

from araos.specialties.psychiatry import (
    build_narrative,
    evaluate,
    explain,
    load_config,
    parse_config,
    sanitize,
)

CFG = parse_config(load_config("1.0.0"))


def item(intensity: int, temporal: str = "ultimos_30_dias", change: str = "claramente"):
    return {"intensity": intensity, "temporal": temporal, "change": change}


def episodic(intensity: int, change: str = "claramente"):
    return item(intensity, temporal="episodico", change=change)


def test_depressao_sem_bipolaridade():
    raw = {
        "items": {
            "dep_humor": item(4),
            "dep_anedonia": item(4),
            "dep_interesse": item(3),
            "dep_desesperanca": item(3),
            "dep_culpa": item(3),
            "dep_baixa_autoestima": item(3),
            "dep_psicomotor": item(2),
        }
    }
    ev = evaluate(raw, CFG)
    assert ev.indices["depressao"] >= 67
    assert ev.indices["bipolaridade"] < 34
    assert ev.patterns["mood"]["pattern"] == "indeterminado"


def test_bipolaridade_provavel():
    raw = {
        "items": {
            "bip_sono_reduzido": episodic(4),
            "bip_energia": episodic(4),
            "bip_grandiosidade": episodic(3),
            "bip_impulsividade": episodic(3),
            "bip_atividade": episodic(3),
        },
        "episodes": [
            {"duration_days": 4, "observed_by_others": True, "sleep_change": "B", "functional_impairment": "leve"}
        ],
    }
    ev = evaluate(raw, CFG)
    assert ev.indices["bipolaridade"] >= 67
    assert ev.patterns["mood"]["pattern"] == "hipomania"


def test_hipomania_vs_mania_por_prejuizo():
    base = {
        "bip_sono_reduzido": episodic(4),
        "bip_energia": episodic(4),
        "bip_grandiosidade": episodic(4),
        "bip_impulsividade": episodic(4),
    }
    hipo = {
        "items": base,
        "episodes": [
            {"duration_days": 4, "observed_by_others": True, "sleep_change": "B", "functional_impairment": "leve"}
        ],
    }
    mania = {
        "items": base,
        "episodes": [
            {"duration_days": 8, "observed_by_others": True, "sleep_change": "B", "functional_impairment": "grave"}
        ],
    }
    assert evaluate(hipo, CFG).patterns["mood"]["pattern"] == "hipomania"
    assert evaluate(mania, CFG).patterns["mood"]["pattern"] == "mania"


def test_mania_com_psicose_nao_e_hipomania():
    raw = {
        "items": {
            "bip_sono_reduzido": episodic(4),
            "bip_energia": episodic(4),
            "bip_grandiosidade": episodic(4),
            "psi_aluc_auditiva": item(4, temporal="hoje"),
            "psi_delirio_persecutorio": item(3, temporal="hoje"),
        },
        "psychosis": {"reality_impairment": "ausente", "temporal_relation": "somente_mania"},
        "episodes": [
            {"duration_days": 10, "observed_by_others": True, "sleep_change": "B", "psychosis": True}
        ],
    }
    ev = evaluate(raw, CFG)
    assert ev.patterns["mood"]["pattern"] == "mania_with_psychosis"
    assert ev.patterns["mood"]["critical"] is True
    assert ev.indices["mania_hipomania"] > 67


def test_psicose_fora_de_episodio_de_humor():
    raw = {
        "items": {
            "psi_delirio_persecutorio": item(4, temporal="hoje"),
            "psi_aluc_auditiva": item(4, temporal="hoje"),
            "psi_delirio_referencia": item(3, temporal="hoje"),
            "psi_desorganizacao": item(0),
            "psi_discurso": item(3, temporal="hoje"),
            "psi_insercao": item(3, temporal="hoje"),
        },
        "psychosis": {"reality_impairment": "ausente", "temporal_relation": "ambos"},
    }
    ev = evaluate(raw, CFG)
    assert ev.indices["psicose"] >= 67
    assert ev.indices["bipolaridade"] < 34
    assert ev.patterns["mood"]["pattern"] == "indeterminado"


def test_tea_com_inicio_infancia():
    raw = {
        "items": {k: item(4, temporal="passado_remoto", change="nao") for k in [
            "tea_reciprocidade", "tea_pistas_sociais", "tea_interacao",
            "tea_rotina", "tea_interesses", "tea_sensorial", "tea_mudancas",
            "tea_literal", "tea_amizades", "tea_codigos_sociais",
        ]},
        "development": {"childhood_onset": True},
    }
    ev = evaluate(raw, CFG)
    assert ev.indices["tea"] >= 67


def test_tea_sem_inicio_infancia_nao_classifica():
    raw = {
        "items": {k: item(4, temporal="ultimos_30_dias") for k in [
            "tea_reciprocidade", "tea_interesses", "tea_rotina", "tea_sensorial",
            "tea_pistas_sociais", "tea_interacao", "tea_amizades",
        ]},
        "development": {"childhood_onset": False},
    }
    assert evaluate(raw, CFG).indices["tea"] < 60


def test_tdah_cronico_nao_vira_mania():
    raw = {
        "items": {k: item(4, temporal="passado_remoto", change="nao") for k in [
            "tdah_desatencao", "tdah_impulsividade", "tdah_desorganizacao",
            "tdah_hiperatividade", "tdah_planejamento", "tdah_distracao",
        ]},
        "development": {"childhood_onset": True},
    }
    ev = evaluate(raw, CFG)
    assert ev.indices["tdah"] >= 67
    assert ev.indices["mania_hipomania"] < 34


def test_ansiedade():
    raw = {
        "items": {
            "anx_preocupacao": item(4),
            "anx_controle": item(4),
            "anx_autonomicos": item(3),
            "anx_panico": item(3),
            "anx_inquietacao": item(3),
            "anx_tensao": item(3),
        }
    }
    ev = evaluate(raw, CFG)
    assert ev.indices["ansiedade"] >= 67
    assert ev.indices["depressao"] < 34


def test_sintomas_induzidos_por_substancia():
    raw = {
        "items": {"dep_humor": item(3), "dep_anedonia": item(3)},
        "substances": [
            {"name": "cannabis", "temporal_relation": "piora_apos_uso", "worsened": True},
            {"name": "estimulantes", "temporal_relation": "temporal", "worsened": True},
        ],
    }
    ev = evaluate(raw, CFG)
    assert ev.indices["substancias"] > 0
    assert ev.patterns["substance_alert"] is not None


def test_risco_suicida_baixo():
    raw = {"suicide": {"pensamentos_morte": True}}
    assert evaluate(raw, CFG).risk["level"] == "baixo"


def test_risco_suicida_alto_sem_emergencia():
    raw = {
        "suicide": {
            "ideacao_suicida": True,
            "pensamento_metodo": True,
            "tentativa_previa": True,
            "autoagressao_recente": True,
            "capacidade_seguranca": True,
        }
    }
    risk = evaluate(raw, CFG).risk
    assert risk["level"] in ("alto", "iminente")


def test_risco_suicida_iminente_e_emergencia():
    raw = {
        "suicide": {
            "ideacao_suicida": True,
            "plano": True,
            "acesso_meio": True,
            "intencao": True,
            "preparacao": True,
            "agitacao": True,
            "capacidade_seguranca": False,
        }
    }
    risk = evaluate(raw, CFG).risk
    assert risk["level"] == "iminente"
    assert risk["emergency"] is True


def test_risco_nao_reduzido_por_dominios_baixos():
    raw = {
        "items": {},
        "suicide": {
            "intencao": True,
            "plano": True,
            "acesso_meio": True,
            "capacidade_seguranca": False,
        },
    }
    risk = evaluate(raw, CFG).risk
    assert risk["level"] in ("alto", "iminente")


def test_explicabilidade_lista_fatores():
    raw = {
        "items": {"bip_sono_reduzido": episodic(4), "bip_energia": episodic(4)},
        "episodes": [{"duration_days": 3, "sleep_change": "B", "observed_by_others": True}],
    }
    report = explain(raw, CFG)
    increased = [e["item"] for e in report["bipolaridade"]["increased"]]
    assert "bip_sono_reduzido" in increased


def test_narrativa_sem_linguagem_diagnostica():
    raw = {
        "items": {"dep_humor": item(4), "dep_anedonia": item(4), "dep_desesperanca": item(3)},
    }
    ev = evaluate(raw, CFG)
    text = build_narrative(ev, CFG)
    assert "tem transtorno" not in text.lower()
    assert "diagnóstico:" not in text.lower()
    assert sanitize("Diagnóstico: transtorno bipolar") == "[termo removido] transtorno bipolar"


def test_mania_exclui_hipomania_com_psicose():
    raw = {
        "items": {"bip_energia": episodic(4), "bip_sono_reduzido": episodic(4)},
        "episodes": [
            {"duration_days": 6, "observed_by_others": True, "sleep_change": "B", "psychosis": True}
        ],
    }
    assert evaluate(raw, CFG).patterns["mood"]["pattern"] != "hipomania"
