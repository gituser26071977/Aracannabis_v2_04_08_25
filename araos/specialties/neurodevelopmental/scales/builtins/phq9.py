"""
PHQ-9 — Patient Health Questionnaire-9.

Autoaplicável. Mede gravidade de sintomas depressivos nas últimas
2 semanas. Validada para ≥12 anos (144 meses) em adolescentes.

Referência:
    Kroenke K, Spitzer RL, Williams JBW. The PHQ-9: validity of a brief
    depression severity measure. J Gen Intern Med. 2001;16(9):606-613.
    doi:10.1046/j.1525-1497.2001.016009606.x

Pontuação: soma simples (0-3 por item, 9 itens) → 0-27.
    0-4  : mínimo
    5-9  : leve
    10-14: moderado
    15-19: moderadamente severo
    20-27: severo

Item 9 (pensamento de morte/autolesão) → triagem adicional obrigatória
quando score ≥1.
"""

from __future__ import annotations

from typing import Dict, List

from ..base import (
    ComputedScores,
    RawResponses,
    ScaleInterpretation,
    ScaleSpec,
    ScaleSubscale,
)


# Itens (Likert 0-3) — versão PT-BR (adaptada de Pfizer/PHQ-9)
PHQ9_ITEMS_PT_BR: List[str] = [
    "Pouco interesse ou prazer em fazer as coisas",
    "Sentir-se para baixo, deprimido(a) ou sem esperança",
    "Dificuldade para pegar no sono ou permanecer dormindo, ou dormir demais",
    "Sentir-se cansado(a) ou com pouca energia",
    "Falta de apetite ou comer demais",
    "Sentir-se mal consigo mesmo(a) — ou achar que é um fracasso ou ter decepcionado a si mesmo(a) ou à sua família",
    "Dificuldade para se concentrar nas coisas (ler jornal, assistir televisão)",
    "Movimentar-se ou falar tão lentamente que outras pessoas perceberam — ou o oposto, estar tão agitado(a) que você fica andando de um lado para o outro mais do que o costume",
    "Pensamentos de que seria melhor estar morto(a) ou de se ferir de alguma maneira",
]


# ─── Funções puras ──────────────────────────────────────────────────


def _score_phq9(raw: RawResponses) -> ComputedScores:
    """Soma simples dos 9 itens. Cada item é inteiro 0-3."""
    total = 0
    for i in range(1, 10):
        value = raw.get(f"q{i}")
        if value is None:
            raise ValueError(f"Questão q{i} ausente")
        if not isinstance(value, int) or not 0 <= value <= 3:
            raise ValueError(f"q{i} deve ser inteiro 0-3, recebido {value!r}")
        total += value
    return {
        "total": float(total),
        "item9_self_harm_risk": float(raw["q9"]),  # rastreio de risco
    }


def _interpret_phq9(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação baseada no escore total (Kroenke et al., 2001)."""
    total = scores["total"]
    item9 = raw.get("q9", 0)

    # Triagem adicional obrigatória se item 9 ≥ 1 (qualquer indicação de autolesão)
    safety_note = ""
    if item9 >= 1:
        safety_note = (
            " ATENÇÃO: item 9 (pensamentos de morte/autolesão) positivo "
            "— avaliação clínica adicional obrigatória e considerar protocolo de risco."
        )

    if total <= 4:
        band, label, color, rec = (
            "minimo",
            "Depressão mínima",
            "#14a085",
            "Sem indicação de tratamento." + safety_note,
        )
    elif total <= 9:
        band, label, color, rec = (
            "leve",
            "Depressão leve",
            "#0d7377",
            "Watchful waiting; reavaliar em 2-4 semanas." + safety_note,
        )
    elif total <= 14:
        band, label, color, rec = (
            "moderado",
            "Depressão moderada",
            "#f5a623",
            "Plano de tratamento: considerar psicoterapia e/ou farmacoterapia." + safety_note,
        )
    elif total <= 19:
        band, label, color, rec = (
            "moderadamente_severo",
            "Depressão moderadamente severa",
            "#e07b00",
            "Tratamento ativo com farmacoterapia e/ou psicoterapia." + safety_note,
        )
    else:
        band, label, color, rec = (
            "severo",
            "Depressão severa",
            "#d64545",
            "Tratamento intensivo imediato; considerar encaminhamento especializado." + safety_note,
        )

    return {
        "total": ScaleInterpretation(
            band=band,
            label_pt=label,
            label_en=band.replace("_", " ").capitalize(),
            color=color,
            recommendation=rec,
            references=["Kroenke, Spitzer & Williams, 2001"],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _phq9_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}
    for i, label in enumerate(PHQ9_ITEMS_PT_BR, start=1):
        item_schema = {
            "type": "integer",
            "minimum": 0,
            "maximum": 3,
            "description": (
                f"{label} (0=nenhuma, 1=vários dias, 2=mais da metade dos dias, 3=quase todos os dias)"
            ),
            "title": f"Questão {i}",
        }
        if i == 9:
            item_schema["description"] += " ⚠️ Item crítico: pensamentos de morte ou autolesão."
        properties[f"q{i}"] = item_schema
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": [f"q{i}" for i in range(1, 10)],
        "additionalProperties": False,
        "title": "PHQ-9",
        "description": "Respostas PHQ-9 — Patient Health Questionnaire-9",
    }


# ─── Spec final ────────────────────────────────────────────────────


PHQ9_SPEC = ScaleSpec(
    code="PHQ9",
    name="Patient Health Questionnaire-9",
    version="1.0",
    author="Kroenke, Spitzer & Williams (2001)",
    scientific_reference=(
        "Kroenke K, Spitzer RL, Williams JBW. The PHQ-9: validity of a brief "
        "depression severity measure. Journal of General Internal Medicine, "
        "16(9):606-613, 2001. doi:10.1046/j.1525-1497.2001.016009606.x"
    ),
    target_age_months=(144, None),  # ≥12 anos
    administration_time_min=3,
    json_schema=_phq9_json_schema(),
    subscales=[
        ScaleSubscale(
            code="total",
            label="Escore Total",
            min=0,
            max=27,
            description="Soma dos 9 itens (0-3 cada)",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="item9_self_harm_risk",
            label="Item 9 — Risco de Autolesão",
            min=0,
            max=3,
            description="Item 9 isolado: pensamentos de morte ou autolesão",
            higher_is_worse=True,
        ),
    ],
    score_function=_score_phq9,
    interpretation_function=_interpret_phq9,
    description=(
        "Escala de 9 itens para rastreamento de depressão. Autoaplicável, "
        "~3 minutos. Inclui item crítico 9 (risco de autolesão) que dispara "
        "avaliação adicional quando ≥1."
    ),
    is_public=True,
    requires_training=False,
    languages=("pt-BR", "en-US"),
)