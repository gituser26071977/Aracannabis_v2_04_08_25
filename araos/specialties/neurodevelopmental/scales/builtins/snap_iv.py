"""
SNAP-IV — Swanson, Nolan, and Pelham-IV Rating Scale.

Instrumento de rastreamento de TDAH (ADHD) baseado em critérios
DSM-IV para sintomas de:
    - Desatenção (9 itens)
    - Hiperatividade/Impulsividade (9 itens)
    - Transtorno Opositivo-Desafiador (TOD/ODD, 8 itens)

Aplicação:
    - Idade: 6 a 17 anos.
    - Preenchimento por pais, professores ou auto-relato (adolescentes).
    - Tempo: ~5-10 minutos.

Resposta: Likert 0-3
    0 = nada
    1 = um pouco
    2 = bastante
    3 = demais

Scoring:
    - Score por subescala = média dos itens (0-3).
    - Score total = média geral das 3 subescalas (0-3).
    - Pontos de corte (≥1.0 em qualquer subescala):
        • Inatenção ≥ 1.0 → sugestivo de TDAH tipo desatento
        • Hiperatividade ≥ 1.0 → sugestivo de TDAH tipo hiperativo-impulsivo
        • Inatenção ≥ 1.0 E Hiperatividade ≥ 1.0 → sugestivo de TDAH combinado
        • TOD ≥ 1.0 → sugestivo de comorbidade opositivo-desafiadora
    - Pontuação ≥ 1.5 em qualquer subescala indica gravidade clínica elevada.

Referência:
    Swanson JM. School-based assessments and interventions for ADD
    students. Irvine, CA: KC Publishing; 1992.

    Tradução e validação brasileira:
    Mattos P, Serra-Pinheiro MA, Rohde LA, Pinto D. Apresentação de
    uma versão em português para uso no Brasil do instrumento MTA-SNAP-IV
    de avaliação de sintomas de transtorno de déficit de atenção/
    hiperatividade e sintomas de transtorno desafiador de oposição.
    Rev Psiquiatr Rio Gd Sul. 2006;28(3):290-297.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..base import (
    ComputedScores,
    RawResponses,
    ScaleInterpretation,
    ScaleSpec,
    ScaleSubscale,
)


# Itens por sub-escala.
# Tupla: (código, enunciado em PT-BR)
SNAP_INATTENTION: List[Tuple[str, str]] = [
    ("sn1", "Não consegue dar atenção a detalhes ou comete erros por descuido"),
    ("sn2", "Tem dificuldade em manter atenção em tarefas ou brincadeiras"),
    ("sn3", "Parece não escutar quando falam diretamente com ele(a)"),
    ("sn4", "Não segue instruções até o fim e não completa tarefas"),
    ("sn5", "Tem dificuldade em organizar tarefas e atividades"),
    ("sn6", "Evita ou reluta em se envolver em tarefas que exigem esforço mental"),
    ("sn7", "Perde coisas necessárias para tarefas ou atividades"),
    ("sn8", "Distrai-se facilmente com estímulos externos"),
    ("sn9", "É esquecido(a) em atividades diárias"),
]

SNAP_HYPERACTIVITY: List[Tuple[str, str]] = [
    ("sn10", "Agita as mãos ou os pés ou se mexe na cadeira"),
    ("sn11", "Levanta da cadeira em situações em que deveria ficar sentado"),
    ("sn12", "Corre ou sobe demais em situações inapropriadas"),
    ("sn13", "Tem dificuldade em brincar ou se envolver em atividades de lazer calmamente"),
    ("sn14", '"Não para" ou age como se "movido a motor"'),
    ("sn15", "Fala demais"),
    ("sn16", "Responde perguntas antes de serem completadas"),
    ("sn17", "Tem dificuldade em esperar sua vez"),
    ("sn18", "Interrompe ou se intromete em conversas ou atividades de outros"),
]

SNAP_ODD: List[Tuple[str, str]] = [
    ("sn19", "Perde a paciência"),
    ("sn20", "Discute com adultos"),
    ("sn21", "Desafia ou recusa ativamente obedecer regras ou pedidos de adultos"),
    ("sn22", "Faz coisas que incomodam outras pessoas deliberadamente"),
    ("sn23", "Culpa outros por seus erros ou mau comportamento"),
    ("sn24", "É facilmente incomodado(a) por outros"),
    ("sn25", "É zangado(a) e ressentido(a)"),
    ("sn26", "É rancoroso(a) ou vingativo(a)"),
]


# ─── Funções puras ─────────────────────────────────────────────────


def _score_snap(raw: RawResponses) -> ComputedScores:
    """Soma por sub-escala + média por sub-escala + média geral."""
    inatt_total = _sum_domain(raw, SNAP_INATTENTION)
    hyp_total = _sum_domain(raw, SNAP_HYPERACTIVITY)
    odd_total = _sum_domain(raw, SNAP_ODD)

    n_inatt = len(SNAP_INATTENTION)
    n_hyp = len(SNAP_HYPERACTIVITY)
    n_odd = len(SNAP_ODD)

    inatt_mean = inatt_total / n_inatt
    hyp_mean = hyp_total / n_hyp
    odd_mean = odd_total / n_odd
    grand_mean = (inatt_mean + hyp_mean + odd_mean) / 3

    return {
        "inattention_total": float(inatt_total),
        "hyperactivity_total": float(hyp_total),
        "odd_total": float(odd_total),
        "inattention_mean": inatt_mean,
        "hyperactivity_mean": hyp_mean,
        "odd_mean": odd_mean,
        "grand_mean": grand_mean,
    }


def _sum_domain(raw: RawResponses, items: List[Tuple[str, str]]) -> float:
    total = 0
    for code, _ in items:
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if not isinstance(v, int) or not 0 <= v <= 3:
            raise ValueError(
                f"{code} deve ser inteiro 0-3, recebido {v!r}"
            )
        total += v
    return total


def _interpret_snap(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação conforme pontos de corte SNAP-IV."""
    inatt_mean = scores["inattention_mean"]
    hyp_mean = scores["hyperactivity_mean"]
    odd_mean = scores["odd_mean"]

    # Subscales ≥ 1.0 são sugestivas de TDAH/TOD
    inatt_pos = inatt_mean >= 1.0
    hyp_pos = hyp_mean >= 1.0
    odd_pos = odd_mean >= 1.0

    if inatt_pos and hyp_pos:
        sub_type = "combinado"
    elif inatt_pos:
        sub_type = "desatento"
    elif hyp_pos:
        sub_type = "hiperativo_impulsivo"
    else:
        sub_type = "nenhum"

    if odd_pos and (inatt_pos or hyp_pos):
        comorbidity = " com comorbidade opositivo-desafiadora"
    elif odd_pos:
        comorbidity = " com traços opositivo-desafiadores isolados"
    else:
        comorbidity = ""

    # Gravidade baseada em qualquer sub-escala ≥ 1.5
    severe = (
        inatt_mean >= 1.5 or hyp_mean >= 1.5 or odd_mean >= 1.5
    )

    if sub_type == "nenhum":
        band = "negativo"
        label_pt = "Rastreamento negativo"
        color = "#14a085"
        rec = (
            "Sintomas abaixo dos pontos de corte clínicos. Não há "
            "indícios de TDAH ou TOD neste rastreamento."
        )
    elif severe:
        band = f"tdah_{sub_type}_severo"
        label_pt = f"TDAH {sub_type} com gravidade clínica elevada{comorbidity}"
        color = "#d64545"
        rec = (
            f"Pontuação elevada nas subescalas — sugestivo de TDAH tipo "
            f"{sub_type} com gravidade clínica{comorbidity}. Encaminhar "
            f"para avaliação diagnóstica formal por especialista "
            f"(neuropediatra, psiquiatra infantil, psicologia)."
        )
    else:
        band = f"tdah_{sub_type}_sugestivo"
        label_pt = f"Sugestivo de TDAH {sub_type}{comorbidity}"
        color = "#f5a623"
        rec = (
            f"Pontuação acima do ponto de corte clínico em subescalas — "
            f"sugestivo de TDAH tipo {sub_type}{comorbidity}. Reavaliar "
            f"com outro informante (professor) e considerar monitoramento."
        )

    return {
        "grand_mean": ScaleInterpretation(
            band=band,
            label_pt=label_pt,
            label_en=f"ADHD screening {sub_type}",
            color=color,
            recommendation=rec,
            references=[
                "Swanson, 1992 (SNAP-IV original)",
                "Mattos et al., 2006 (versão PT-BR)",
            ],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _snap_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}

    def _add(items: List[Tuple[str, str]], section_label: str) -> None:
        for code, label in items:
            properties[code] = {
                "type": "integer",
                "minimum": 0,
                "maximum": 3,
                "description": (
                    f"[{section_label}] {label} "
                    "(0=nada, 1=um pouco, 2=bastante, 3=demais)"
                ),
                "title": f"Item {code[2:]}",
            }

    _add(SNAP_INATTENTION, "Desatenção")
    _add(SNAP_HYPERACTIVITY, "Hiperatividade/Impulsividade")
    _add(SNAP_ODD, "TOD")

    required = [c for c, _ in (
        SNAP_INATTENTION + SNAP_HYPERACTIVITY + SNAP_ODD
    )]
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
        "title": "SNAP-IV",
        "description": (
            "Rastreamento de TDAH e TOD. 26 itens Likert 0-3 em 3 subescalas. "
            "Preenchimento por pais, professores ou auto-relato."
        ),
    }


# ─── Spec final ────────────────────────────────────────────────────


SNAP_SPEC = ScaleSpec(
    code="SNAP",
    name="SNAP-IV Rating Scale (Swanson, Nolan, and Pelham-IV)",
    version="1.0",
    author="Swanson (1992)",
    scientific_reference=(
        "Mattos P, Serra-Pinheiro MA, Rohde LA, Pinto D. Apresentação "
        "de uma versão em português para uso no Brasil do instrumento "
        "MTA-SNAP-IV de avaliação de sintomas de TDAH e TOD. "
        "Rev Psiquiatr Rio Gd Sul. 2006;28(3):290-297."
    ),
    target_age_months=(72, 17 * 12),  # 6-17 anos
    administration_time_min=10,
    json_schema=_snap_json_schema(),
    subscales=[
        ScaleSubscale(
            code="inattention_mean",
            label="Desatenção (média)",
            min=0,
            max=3,
            description="Média dos 9 itens de desatenção. ≥1.0 = sugestivo.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="hyperactivity_mean",
            label="Hiperatividade/Impulsividade (média)",
            min=0,
            max=3,
            description="Média dos 9 itens. ≥1.0 = sugestivo.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="odd_mean",
            label="TOD (média)",
            min=0,
            max=3,
            description="Média dos 8 itens. ≥1.0 = sugestivo.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="grand_mean",
            label="Média geral",
            min=0,
            max=3,
            description="Média das 3 subescalas.",
            higher_is_worse=True,
        ),
    ],
    score_function=_score_snap,
    interpretation_function=_interpret_snap,
    description=(
        "Rastreamento de TDAH e Transtorno Opositivo-Desafiador. "
        "26 itens Likert 0-3 distribuídos em 3 subescalas (Desatenção, "
        "Hiperatividade/Impulsividade, TOD). Aplicação 5-10 min."
    ),
    is_public=True,
    requires_training=False,
    languages=("pt-BR", "en-US"),
)
