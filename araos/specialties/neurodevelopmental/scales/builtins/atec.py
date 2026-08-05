"""
ATEC — Autism Treatment Effectiveness Checklist.

Instrumento longitudinal preenchido por pais/responsáveis para monitorar
evolução clínica de crianças com TEA sob intervenção. Indicado para
idades entre 2 e 12 anos.

Estrutura: 4 sub-escalas:
    1. speech_language       (Fala/Linguagem)
    2. sociability           (Sociabilidade)
    3. sensory_cognitive     (Consciência Sensorial/Cognitiva)
    4. health_behavior       (Saúde, Comportamento Físico)

Cada item usa escala ordinal própria:
    speech/sociability: 0 (típico) → 2 (severo)
    sensory_cognitive:  0 (típico) → 2 (severo)
    health_behavior:    0 (típico) → 3 (severo)

Total somado: ~0-108 (depende das faixas).

Bands totais (orientação clínica):
    0-20  → leve
    21-50 → moderado
    51-80 → severo
    ≥81   → muito severo

Referência:
    Rimland B, Edelson SM. Autism Treatment Effectiveness Checklist
    (ATEC). Autism Research Institute; 1999.

    Tradução e validação parcial: várias iniciativas acadêmicas no
    Brasil (forma não-oficial). Para estudos publicados em PT-BR,
    consultar Núcleo de Informática na Educação Especial (NIEE/UFSCar).
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


# Itens declarados por sub-escala.
# Tupla: (código, enunciado, max_value).
# "max_value" é o maior valor aceito (define enum do JSON Schema).

ATEC_SPEECH_LANGUAGE: List[Tuple[str, str]] = [
    ("at1", "Seu filho sabe o nome dele(a)?"),
    ("at2", "Seu filho diz 'sim' ou 'não' para perguntas simples?"),
    ("at3", "Seu filho segue comandos simples (ex: 'pega o sapato')?"),
    ("at4", "Seu filho consegue falar uma palavra de cada vez?"),
    ("at5", "Seu filho fala frases de duas palavras?"),
    ("at6", "Seu filho fala frases de três ou mais palavras?"),
    ("at7", "Seu filho faz perguntas espontaneamente?"),
]

ATEC_SOCIABILITY: List[Tuple[str, str]] = [
    ("at8", "Seu filho parece solitário(a) e distante?"),
    ("at9", "Seu filho não responde quando alguém chama pelo nome dele(a)?"),
    ("at10", "Seu filho tem dificuldade em manter contato visual?"),
    ("at11", "Seu filho prefere brincar sozinho(a)?"),
    ("at12", "Seu filho não tenta se comunicar com outras crianças?"),
    ("at13", "Seu filho mostra interesse em interagir com adultos familiares?"),
    ("at14", "Seu filho é sensível a sons ou ruídos altos?"),
    ("at15", "Seu filho reage positivamente quando outras crianças se aproximam?"),
    ("at16", "Seu filho gosta de festas e reuniões sociais?"),
    ("at17", "Seu filho reconhece emoções básicas (alegria, tristeza) nos outros?"),
]

ATEC_SENSORY_COGNITIVE: List[Tuple[str, str]] = [
    ("at18", "Seu filho demonstra interesse por texturas ou superfícies incomuns?"),
    ("at19", "Seu filho tem movimentos repetitivos (ex: balançar as mãos)?"),
    ("at20", "Seu filho tem reações incomuns a cheiros ou sabores?"),
    ("at21", "Seu filho é atraído por luzes brilhantes ou objetos que giram?"),
    ("at22", "Seu filho demonstra interesse por sons específicos repetidos?"),
    ("at23", "Seu filho apresenta hipersensibilidade tátil (rejeição a roupas)?"),
    ("at24", "Seu filho apresenta comportamento de auto-lesão?"),
    ("at25", "Seu filho demonstra ecolalia (repete palavras sem propósito)?"),
    ("at26", "Seu filho mostra fixação em tópicos ou objetos específicos?"),
]

ATEC_HEALTH_BEHAVIOR: List[Tuple[str, str]] = [
    ("at27", "Seu filho dorme bem?"),
    ("at28", "Seu filho se alimenta bem?"),
    ("at29", "Seu filho tem crises de birra?"),
    ("at30", "Seu filho é agressivo fisicamente?"),
    ("at31", "Seu filho se machuca intencionalmente?"),
    ("at32", "Seu filho toma alguma medicação?"),
    ("at33", "Seu filho tem alergias alimentares?"),
    ("at34", "Seu filho tem problemas gastrointestinais?"),
    ("at35", "Seu filho apresenta convulsões?"),
    ("at36", "Seu filho toma medicação para dormir?"),
    ("at37", "Seu filho apresenta comportamentos obsessivos?"),
    ("at38", "Seu filho apresenta enurese (xixi na cama)?"),
    ("at39", "Seu filho apresenta encoprese (coco na roupa)?"),
]


# ─── Funções puras ─────────────────────────────────────────────────


def _score_atec(raw: RawResponses) -> ComputedScores:
    """Soma por sub-escala + total. Valida range de cada item."""
    speech = 0
    for code, _ in ATEC_SPEECH_LANGUAGE:
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if not isinstance(v, int) or not 0 <= v <= 2:
            raise ValueError(
                f"{code} deve ser inteiro 0-2, recebido {v!r}"
            )
        speech += v

    sociability = 0
    for code, _ in ATEC_SOCIABILITY:
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if not isinstance(v, int) or not 0 <= v <= 2:
            raise ValueError(
                f"{code} deve ser inteiro 0-2, recebido {v!r}"
            )
        sociability += v

    sensory = 0
    for code, _ in ATEC_SENSORY_COGNITIVE:
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if not isinstance(v, int) or not 0 <= v <= 2:
            raise ValueError(
                f"{code} deve ser inteiro 0-2, recebido {v!r}"
            )
        sensory += v

    health = 0
    for code, _ in ATEC_HEALTH_BEHAVIOR:
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if not isinstance(v, int) or not 0 <= v <= 3:
            raise ValueError(
                f"{code} deve ser inteiro 0-3, recebido {v!r}"
            )
        health += v

    total = speech + sociability + sensory + health
    return {
        "speech_language": float(speech),
        "sociability": float(sociability),
        "sensory_cognitive": float(sensory),
        "health_behavior": float(health),
        "total": float(total),
    }


def _interpret_atec(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação por total + subescalas individuais."""
    total = int(scores["total"])
    speech = int(scores["speech_language"])
    soc = int(scores["sociability"])
    sens = int(scores["sensory_cognitive"])
    health = int(scores["health_behavior"])

    if total <= 20:
        band = "leve"
        label_pt = "TEA leve"
        color = "#14a085"
        rec = "Pontuação baixa. Manter vigilância clínica e intervenções leves."
    elif total <= 50:
        band = "moderado"
        label_pt = "TEA moderado"
        color = "#f5a623"
        rec = (
            "Pontuação moderada. Indicar intervenção estruturada "
            "(ABA, fono, TO) e acompanhamento multiprofissional regular."
        )
    elif total <= 80:
        band = "severo"
        label_pt = "TEA severo"
        color = "#e07b00"
        rec = (
            "Pontuação elevada. Intervenção intensiva necessária; "
            "considerar apoio escolar especializado e suporte familiar."
        )
    else:
        band = "muito_severo"
        label_pt = "TEA muito severo"
        color = "#d64545"
        rec = (
            "Pontuação muito elevada. Intervenção imediata e intensiva; "
            "avaliação psiquiátrica e de saúde mental complementar."
        )

    # Acrescenta sinalização quando sub-escala saúde está desproporcionalmente alta
    if health >= 20:
        rec += " ATENÇÃO: sub-escala Saúde/Comportamento muito elevada — investigar efeitos adversos de medicação, sono ou gastrointestinais."

    return {
        "total": ScaleInterpretation(
            band=band,
            label_pt=label_pt,
            label_en=f"Autism severity {band}",
            color=color,
            recommendation=rec,
            references=[
                "Rimland & Edelson, 1999 (ATEC original)",
                "Autism Research Institute (publicações técnicas)",
            ],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _atec_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}

    def _add(items: List[Tuple[str, str]], max_val: int, section_label: str) -> None:
        for code, label in items:
            properties[code] = {
                "type": "integer",
                "minimum": 0,
                "maximum": max_val,
                "description": f"[{section_label}] {label} (0=típico, {max_val}=severo)",
                "title": f"Item {code[2:]}",
            }

    _add(ATEC_SPEECH_LANGUAGE, 2, "Fala/Linguagem")
    _add(ATEC_SOCIABILITY, 2, "Sociabilidade")
    _add(ATEC_SENSORY_COGNITIVE, 2, "Sensorial/Cognitivo")
    _add(ATEC_HEALTH_BEHAVIOR, 3, "Saúde/Comportamento")

    required = [c for c, _ in (
        ATEC_SPEECH_LANGUAGE + ATEC_SOCIABILITY
        + ATEC_SENSORY_COGNITIVE + ATEC_HEALTH_BEHAVIOR
    )]
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
        "title": "ATEC",
        "description": (
            "Autism Treatment Effectiveness Checklist — versão reduzida PT-BR "
            "(39 itens distribuídos em 4 sub-escalas)."
        ),
    }


# ─── Spec final ────────────────────────────────────────────────────


ATEC_SPEC = ScaleSpec(
    code="ATEC",
    name="Autism Treatment Effectiveness Checklist",
    version="1.0",
    author="Rimland & Edelson (1999) — Autism Research Institute",
    scientific_reference=(
        "Rimland B, Edelson SM. Autism Treatment Effectiveness Checklist "
        "(ATEC). Autism Research Institute, San Diego, CA; 1999."
    ),
    target_age_months=(24, 144),  # 2-12 anos
    administration_time_min=20,
    json_schema=_atec_json_schema(),
    subscales=[
        ScaleSubscale(
            code="speech_language",
            label="Fala / Linguagem",
            min=0,
            max=2 * len(ATEC_SPEECH_LANGUAGE),
            description="7 itens (0-2 cada) sobre linguagem expressiva e receptiva.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="sociability",
            label="Sociabilidade",
            min=0,
            max=2 * len(ATEC_SOCIABILITY),
            description="10 itens (0-2 cada) sobre interação social e reciprocidade.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="sensory_cognitive",
            label="Sensorial / Cognitivo",
            min=0,
            max=2 * len(ATEC_SENSORY_COGNITIVE),
            description="9 itens (0-2 cada) sobre processamento sensorial e comportamentos repetitivos.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="health_behavior",
            label="Saúde / Comportamento",
            min=0,
            max=3 * len(ATEC_HEALTH_BEHAVIOR),
            description="13 itens (0-3 cada) sobre saúde física, sono, comportamento e medicação.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="total",
            label="Escore Total",
            min=0,
            max=(
                2 * len(ATEC_SPEECH_LANGUAGE)
                + 2 * len(ATEC_SOCIABILITY)
                + 2 * len(ATEC_SENSORY_COGNITIVE)
                + 3 * len(ATEC_HEALTH_BEHAVIOR)
            ),
            description="Soma das 4 sub-escalas.",
            higher_is_worse=True,
        ),
    ],
    score_function=_score_atec,
    interpretation_function=_interpret_atec,
    description=(
        "Checklist longitudinal preenchido por pais/responsáveis para monitorar "
        "evolução clínica de crianças com TEA sob intervenção. Indicada para "
        "idades entre 2 e 12 anos."
    ),
    is_public=True,
    requires_training=False,
    languages=("pt-BR", "en-US"),
)
