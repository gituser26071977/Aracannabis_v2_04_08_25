"""
GAD-7 — Generalized Anxiety Disorder 7-item Scale.

Autoaplicável. Mede gravidade de sintomas de ansiedade generalizada
nas últimas 2 semanas. Validada para ≥14 anos (168 meses).

Referência:
    Spitzer RL, Kroenke K, Williams JBW, Löwe B. A brief measure for
    assessing generalized anxiety disorder: the GAD-7. Arch Intern Med.
    2006;166(10):1092-1097. doi:10.1001/archinte.166.10.1092

Pontuação: soma simples (0-3 por item, 7 itens) → 0-21.
    0-4  : mínimo
    5-9  : leve
    10-14: moderado
    15-21: severo

Recomendação clínica (Spitzer et al., 2006):
    ≥10 → investigação adicional
    ≥15 → tratamento ativo fortemente recomendado
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
from ..runner import ScaleRunner


# Itens (Likert 0-3) — versão PT-BR (adaptada de Pfizer/GAD-7)
GAD7_ITEMS_PT_BR: List[str] = [
    "Sentir-se nervoso(a), ansioso(a) ou muito tenso(a)",
    "Não ser capaz de parar ou controlar as preocupações",
    "Preocupar-se demais com diversas coisas",
    "Dificuldade para relaxar",
    "Ficar tão agitado(a) que é difícil permanecer sentado(a)",
    "Ficar facilmente aborrecido(a) ou irritado(a)",
    "Sentir medo como se algo terrível fosse acontecer",
]

# ─── Funções puras de scoring/interpretation ────────────────────────


def _score_gad7(raw: RawResponses) -> ComputedScores:
    """Soma simples dos 7 itens. Cada item é inteiro 0-3."""
    total = 0
    for i in range(1, 8):
        value = raw.get(f"q{i}")
        if value is None:
            raise ValueError(f"Questão q{i} ausente")
        if not isinstance(value, int) or not 0 <= value <= 3:
            raise ValueError(f"q{i} deve ser inteiro 0-3, recebido {value!r}")
        total += value
    return {"total": float(total)}


def _interpret_gad7(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação baseada no escore total (Spitzer et al., 2006)."""
    total = scores["total"]

    if total <= 4:
        return {
            "total": ScaleInterpretation(
                band="minimo",
                label_pt="Ansiedade mínima",
                label_en="Minimal anxiety",
                color="#14a085",
                recommendation="Sem indicação de tratamento adicional.",
                references=["Spitzer et al., 2006"],
            )
        }
    if total <= 9:
        return {
            "total": ScaleInterpretation(
                band="leve",
                label_pt="Ansiedade leve",
                label_en="Mild anxiety",
                color="#0d7377",
                recommendation="Monitoramento clínico. Reavaliar em 2-4 semanas.",
                references=["Spitzer et al., 2006"],
            )
        }
    if total <= 14:
        return {
            "total": ScaleInterpretation(
                band="moderado",
                label_pt="Ansiedade moderada",
                label_en="Moderate anxiety",
                color="#f5a623",
                recommendation=(
                    "Investigação clínica adicional recomendada. "
                    "Considerar intervenção psicoterápica."
                ),
                references=["Spitzer et al., 2006"],
            )
        }
    return {
        "total": ScaleInterpretation(
            band="severo",
            label_pt="Ansiedade severa",
            label_en="Severe anxiety",
            color="#d64545",
            recommendation=(
                "Tratamento ativo fortemente recomendado. "
                "Considerar farmacoterapia e/ou psicoterapia intensiva."
            ),
            references=["Spitzer et al., 2006"],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _gad7_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}
    for i, label in enumerate(GAD7_ITEMS_PT_BR, start=1):
        properties[f"q{i}"] = {
            "type": "integer",
            "minimum": 0,
            "maximum": 3,
            "description": f"{label} (0=nenhuma, 1=vários dias, 2=mais da metade dos dias, 3=quase todos os dias)",
            "title": f"Questão {i}",
        }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": [f"q{i}" for i in range(1, 8)],
        "additionalProperties": False,
        "title": "GAD-7",
        "description": "Respostas GAD-7 — Generalized Anxiety Disorder 7-item",
    }


# ─── Spec final ────────────────────────────────────────────────────


GAD7_SPEC = ScaleSpec(
    code="GAD7",
    name="Generalized Anxiety Disorder 7-item",
    version="1.0",
    author="Spitzer, Kroenke, Williams & Löwe (2006)",
    scientific_reference=(
        "Spitzer RL, Kroenke K, Williams JBW, Löwe B. "
        "A brief measure for assessing generalized anxiety disorder: the GAD-7. "
        "Archives of Internal Medicine, 166(10):1092-1097, 2006. "
        "doi:10.1001/archinte.166.10.1092"
    ),
    target_age_months=(168, None),  # ≥14 anos
    administration_time_min=3,
    json_schema=_gad7_json_schema(),
    subscales=[
        ScaleSubscale(
            code="total",
            label="Escore Total",
            min=0,
            max=21,
            description="Soma dos 7 itens (0-3 cada)",
            higher_is_worse=True,
        )
    ],
    score_function=_score_gad7,
    interpretation_function=_interpret_gad7,
    description=(
        "Escala de 7 itens para rastreamento de ansiedade generalizada. "
        "Autoaplicável, ~3 minutos. Indicada para adolescentes (≥14 anos) "
        "e adultos em contexto clínico e de pesquisa."
    ),
    is_public=True,
    requires_training=False,
    languages=("pt-BR", "en-US"),
)