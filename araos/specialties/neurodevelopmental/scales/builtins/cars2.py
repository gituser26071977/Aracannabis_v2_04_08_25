"""
CARS2 — Childhood Autism Rating Scale, Second Edition (Standard Form).

Avaliação de sintomas autísticos por profissional treinado (15-20 min).
Indicada para crianças de 2 a 6 anos (forma padrão CARS-2-ST). Versão
High-Functioning (CARS-2-HF) para ≥6 anos com Quociente Intelectual
≥80 — implementação separada fora do escopo deste módulo.

15 itens avaliados em escala Likert de 1 a 4:
    1 = comportamento dentro da faixa típica da idade
    2 = comportamento levemente atípico
    3 = comportamento moderadamente atípico
    4 = comportamento severamente atípico

Pontuação total: 15-60.
    15-29.5 → Não autista
    30-36.5 → Autismo leve a moderado
    37-60   → Autismo severo

Como o scoring oficial usa incrementos de 0.5, nossa implementação
opera com inteiros 1-4 e aplica pontos de corte arredondados.
Para versões em produção com T-scores padronizados, ver
Schopler E, Van Bourgondien ME, Wellman GJ, Love SR (2010).

Referência:
    Schopler E, Van Bourgondien ME, Wellman GJ, Love SR. CARS-2:
    Childhood Autism Rating Scale, Second Edition. Los Angeles, CA:
    Western Psychological Services; 2010.

Tradução brasileira:
    Pereira AM, Wagner GP. Escala de Avaliação do Autismo na Infância
    (CARS-BR). São Paulo: Casa do Psicólogo; 2008. (CARS original
    adaptado — versão vigente no Brasil).
"""

from __future__ import annotations

from typing import Dict

from ..base import (
    ComputedScores,
    RawResponses,
    ScaleInterpretation,
    ScaleSpec,
    ScaleSubscale,
)


# 15 itens da CARS-2-ST (texto descritivo breve para auditoria).
CARS2_ITEMS_PT_BR: Dict[str, str] = {
    "q1": "Relação com pessoas (proximidade, responsividade social)",
    "q2": "Imitação (capacidade de imitar gestos, sons, ações)",
    "q3": "Resposta emocional (reação afetiva apropriada ao contexto)",
    "q4": "Uso do corpo (coordenação motora, postura, movimentos estereotipados)",
    "q5": "Uso de objetos (interesse funcional e apropriado com brinquedos)",
    "q6": "Adaptação a mudanças (flexibilidade diante de novas situações)",
    "q7": "Resposta visual (uso do olhar para interagir)",
    "q8": "Resposta auditiva (atenção e reação a sons)",
    "q9": "Resposta ao gosto, cheiro e tato (uso sensorial exploratório)",
    "q10": "Medo ou nervosismo (reação a estímulos ameaçadores)",
    "q11": "Comunicação verbal (linguagem expressiva e receptiva)",
    "q12": "Comunicação não verbal (gestos, expressão facial)",
    "q13": "Nível de atividade (letargia ou hiperatividade excessiva)",
    "q14": "Nível intelectual (funções cognitivas observadas)",
    "q15": "Impressão geral (julgamento clínico global)",
}

# Pontos de corte oficiais (CARS-2 manual).
CUTOFF_NAO_AUTISTA_MAX = 30  # 15-29.5
CUTOFF_AUTISMO_LEVE_MAX = 37  # 30-36.5


# ─── Funções puras ─────────────────────────────────────────────────


def _score_cars2(raw: RawResponses) -> ComputedScores:
    """Soma simples dos 15 itens (1-4 cada) → total 15-60."""
    total = 0
    for code, _ in CARS2_ITEMS_PT_BR.items():
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if not isinstance(v, int) or not 1 <= v <= 4:
            raise ValueError(
                f"{code} deve ser inteiro 1-4, recebido {v!r}"
            )
        total += v
    return {"total": float(total)}


def _interpret_cars2(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação conforme CARS-2 manual."""
    total = int(scores["total"])

    if total < CUTOFF_NAO_AUTISTA_MAX:
        band = "nao_autista"
        label_pt = "Não autista"
        color = "#14a085"
        rec = (
            "Pontuação dentro da faixa de não-autismo. Considerar outras "
            "hipóteses diagnósticas se houver preocupação clínica."
        )
    elif total < CUTOFF_AUTISMO_LEVE_MAX:
        band = "autismo_leve_moderado"
        label_pt = "Autismo leve a moderado"
        color = "#f5a623"
        rec = (
            "Pontuação compatível com autismo leve a moderado. Encaminhar "
            "para equipe multidisciplinar (neurologia, psicologia, "
            "fonoaudiologia, terapia ocupacional) e iniciar intervenção."
        )
    else:
        band = "autismo_severo"
        label_pt = "Autismo severo"
        color = "#d64545"
        rec = (
            "Pontuação compatível com autismo severo. Intervenção intensiva "
            "IMEDIATA (ABA, comunicação alternativa, equipe especializada). "
            "Encaminhar para serviços de saúde de alta complexidade."
        )

    return {
        "total": ScaleInterpretation(
            band=band,
            label_pt=label_pt,
            label_en=f"Autism severity {band.replace('_', ' ')}",
            color=color,
            recommendation=rec,
            references=[
                "Schopler et al., 2010 (CARS-2 manual)",
                "Pereira & Wagner, 2008 (CARS-BR)",
            ],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _cars2_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}
    for code, label in CARS2_ITEMS_PT_BR.items():
        properties[code] = {
            "type": "integer",
            "minimum": 1,
            "maximum": 4,
            "description": (
                f"{label}. 1=típico, 2=levemente atípico, "
                f"3=moderadamente atípico, 4=severamente atípico."
            ),
            "title": f"Item {code[1:]}",
        }
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": list(CARS2_ITEMS_PT_BR.keys()),
        "additionalProperties": False,
        "title": "CARS-2 (Standard Form)",
        "description": (
            "Avaliação clínica de sintomas autísticos por profissional treinado. "
            "Aplicada a crianças de 2-6 anos."
        ),
    }


# ─── Spec final ────────────────────────────────────────────────────


CARS2_SPEC = ScaleSpec(
    code="CARS2",
    name="Childhood Autism Rating Scale, Second Edition (Standard Form)",
    version="1.0",
    author="Schopler, Van Bourgondien, Wellman & Love (2010)",
    scientific_reference=(
        "Schopler E, Van Bourgondien ME, Wellman GJ, Love SR. CARS-2: "
        "Childhood Autism Rating Scale, Second Edition. Los Angeles: "
        "Western Psychological Services; 2010."
    ),
    target_age_months=(24, 72),  # 2-6 anos (forma padrão)
    administration_time_min=20,
    json_schema=_cars2_json_schema(),
    subscales=[
        ScaleSubscale(
            code="total",
            label="Escore Total CARS-2-ST",
            min=15,
            max=60,
            description="Soma dos 15 itens Likert 1-4. Faixas: 15-29 não-TEA, 30-36 TEA leve-moderado, 37-60 TEA severo.",
            higher_is_worse=True,
        ),
    ],
    score_function=_score_cars2,
    interpretation_function=_interpret_cars2,
    description=(
        "Avaliação clínica estruturada de sintomas autísticos por profissional "
        "treinado. Indicada para crianças de 2-6 anos (Standard Form). "
        "A versão High-Functioning (≥6 anos) é uma escala separada."
    ),
    is_public=True,
    requires_training=True,  # exige profissional treinado
    languages=("pt-BR", "en-US"),
)
