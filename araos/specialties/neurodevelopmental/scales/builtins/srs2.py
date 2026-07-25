"""
SRS-2 — Social Responsiveness Scale, Second Edition (versão reduzida).

Rastreamento de sintomas relacionados ao espectro autista em 5
subescalas de comportamento social:
    1. social_awareness  (Consciência Social)
    2. social_cognition   (Cognição Social)
    3. social_communication (Comunicação Social)
    4. social_motivation  (Motivação Social)
    5. restricted_interests (Interesses Restritos / Comportamento Repetitivo)

Aplicação:
    - Idade: 2,5 a 18 anos.
    - Forma School-Age: 4-15 anos.
    - Forma Preschool: 2,5-4,5 anos (item-set diferente).
    - Forma Adult: 19+ anos.
    - Preenchimento por pais/responsáveis (~15-20 min).

Resposta: Likert 0-3
    0 = nunca
    1 = às vezes
    2 = frequentemente
    3 = sempre (atípico)

Implementação:
    - 25 itens (5 por sub-escala). Versão reduzida do SRS-2 de 65
      itens — o instrumento oficial exige compra e licenciamento.
    - T-score oficial NÃO é calculado (requer tabelas normativas
      específicas por idade/forma). Para T-score, integrar tabelas
      em sprint futura.
    - Bandas baseadas no escore bruto total:
        • 0-15  → dentro do esperado
        • 16-30 → sintomas leves
        • 31-50 → sintomas moderados
        • ≥51   → sintomas severos

Referência:
    Constantino JN, Gruber CP. Social Responsiveness Scale, Second
    Edition (SRS-2). Los Angeles, CA: Western Psychological Services;
    2012.

    Validação brasileira:
    Bosa CA, et al. Adaptação transcultural do Social Responsiveness
    Scale para uso no Brasil. (Forma de pesquisa, sem fins clínicos
    sem autorização do editor original).
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


# 5 sub-escalas × 5 itens cada.
# Tupla: (código, enunciado em PT-BR)

SRS_AWARENESS: List[Tuple[str, str]] = [
    ("sr1", "Parece alheio(a) ao ambiente ao redor"),
    ("sr2", "Tem dificuldade em fazer contato visual durante interações"),
    ("sr3", "Dificuldade em entender tom de voz e expressões faciais"),
    ("sr4", "Não percebe quando outros estão irritados ou chateados"),
    ("sr5", "Dificuldade em prestar atenção a pessoas"),
]

SRS_COGNITION: List[Tuple[str, str]] = [
    ("sr6", "Comporta-se de maneira inadequada em situações sociais"),
    ("sr7", "Interpreta literalmente expressões idiomáticas"),
    ("sr8", "Não compreende sarcasmo ou ironia"),
    ("sr9", "Dificuldade em entender a perspectiva de outras pessoas"),
    ("sr10", "Faz comentários inadequados sem perceber"),
]

SRS_COMMUNICATION: List[Tuple[str, str]] = [
    ("sr11", "Tem dificuldade em iniciar conversas"),
    ("sr12", "Não se expressa com entonação adequada"),
    ("sr13", "Fala de forma monótona, sem variação"),
    ("sr14", "Tem dificuldade em manter conversação"),
    ("sr15", "Respostas incomuns ou fora de contexto a perguntas"),
]

SRS_MOTIVATION: List[Tuple[str, str]] = [
    ("sr16", "Prefere atividades solitárias"),
    ("sr17", "Evita interação social"),
    ("sr18", "Não demonstra interesse em fazer amigos"),
    ("sr19", "Baixa motivação para interação social"),
    ("sr20", "Dificuldade em compartilhar alegrias com outros"),
]

SRS_RESTRICTED: List[Tuple[str, str]] = [
    ("sr21", "Fala repetidamente sobre os mesmos tópicos"),
    ("sr22", "Interesse intenso e restrito em certos temas"),
    ("sr23", "Apresenta movimentos repetitivos (balançar, bater palmas)"),
    ("sr24", "Insiste em rotinas rígidas"),
    ("sr25", "Reage de forma excessiva a mudanças de rotina"),
]


# ─── Funções puras ─────────────────────────────────────────────────


def _score_srs2(raw: RawResponses) -> ComputedScores:
    """Soma por sub-escala (5 itens × 0-3) + total (25 × 0-3 = 0-75)."""
    awareness = _sum_domain(raw, SRS_AWARENESS)
    cognition = _sum_domain(raw, SRS_COGNITION)
    communication = _sum_domain(raw, SRS_COMMUNICATION)
    motivation = _sum_domain(raw, SRS_MOTIVATION)
    restricted = _sum_domain(raw, SRS_RESTRICTED)
    total = (
        awareness + cognition + communication + motivation + restricted
    )
    return {
        "social_awareness": float(awareness),
        "social_cognition": float(cognition),
        "social_communication": float(communication),
        "social_motivation": float(motivation),
        "restricted_interests": float(restricted),
        "total": float(total),
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


def _interpret_srs2(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação por escore bruto total."""
    total = int(scores["total"])
    awareness = int(scores["social_awareness"])
    cognition = int(scores["social_cognition"])
    communication = int(scores["social_communication"])
    motivation = int(scores["social_motivation"])
    restricted = int(scores["restricted_interests"])

    if total <= 15:
        band = "dentro_esperado"
        label_pt = "Dentro do esperado"
        color = "#14a085"
        rec = (
            "Sintomas sociais abaixo do limiar clínico. Manter "
            "vigilância rotineira."
        )
    elif total <= 30:
        band = "leve"
        label_pt = "Sintomas leves"
        color = "#f5a623"
        rec = (
            "Presença de sintomas leves em comportamento social. "
            "Reavaliar em 6 meses e considerar orientação parental."
        )
    elif total <= 50:
        band = "moderado"
        label_pt = "Sintomas moderados"
        color = "#e07b00"
        rec = (
            "Sintomas moderados compatíveis com TEA ou traços do "
            "espectro. Encaminhar para avaliação diagnóstica formal."
        )
    else:
        band = "severo"
        label_pt = "Sintomas severos"
        color = "#d64545"
        rec = (
            "Sintomas severos. Encaminhar com prioridade para avaliação "
            "multidisciplinar (neuropediatra/psiquiatra/psicólogo) e "
            "iniciar intervenção intensiva."
        )

    # Sinaliza sub-escala com escore máximo
    high_subscales = []
    if awareness >= 12:
        high_subscales.append("Consciência Social")
    if cognition >= 12:
        high_subscales.append("Cognição Social")
    if communication >= 12:
        high_subscales.append("Comunicação Social")
    if motivation >= 12:
        high_subscales.append("Motivação Social")
    if restricted >= 12:
        high_subscales.append("Interesses Restritos")

    if high_subscales:
        rec = (
            rec
            + " ATENÇÃO: domínio(s) com escore muito elevado: "
            + ", ".join(high_subscales)
            + "."
        )

    return {
        "total": ScaleInterpretation(
            band=band,
            label_pt=label_pt,
            label_en=f"Autism social trait {band}",
            color=color,
            recommendation=rec,
            references=[
                "Constantino & Gruber, 2012 (SRS-2 manual)",
            ],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _srs2_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}

    def _add(items: List[Tuple[str, str]], section_label: str) -> None:
        for code, label in items:
            properties[code] = {
                "type": "integer",
                "minimum": 0,
                "maximum": 3,
                "description": (
                    f"[{section_label}] {label} "
                    "(0=nunca, 1=às vezes, 2=frequentemente, 3=sempre)"
                ),
                "title": f"Item {code[2:]}",
            }

    _add(SRS_AWARENESS, "Consciência Social")
    _add(SRS_COGNITION, "Cognição Social")
    _add(SRS_COMMUNICATION, "Comunicação Social")
    _add(SRS_MOTIVATION, "Motivação Social")
    _add(SRS_RESTRICTED, "Interesses Restritos")

    required = [c for c, _ in (
        SRS_AWARENESS + SRS_COGNITION + SRS_COMMUNICATION
        + SRS_MOTIVATION + SRS_RESTRICTED
    )]
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
        "title": "SRS-2 (versão reduzida)",
        "description": (
            "Social Responsiveness Scale — versão reduzida de 25 itens em "
            "5 sub-escalas. T-score oficial NÃO calculado nesta versão."
        ),
    }


# ─── Spec final ────────────────────────────────────────────────────


SRS2_SPEC = ScaleSpec(
    code="SRS2",
    name="Social Responsiveness Scale, Second Edition (versão reduzida)",
    version="1.0",
    author="Constantino & Gruber (2012)",
    scientific_reference=(
        "Constantino JN, Gruber CP. Social Responsiveness Scale, "
        "Second Edition (SRS-2). Los Angeles, CA: Western Psychological "
        "Services; 2012."
    ),
    target_age_months=(30, 18 * 12),  # 2,5-18 anos
    administration_time_min=15,
    json_schema=_srs2_json_schema(),
    subscales=[
        ScaleSubscale(
            code="social_awareness",
            label="Consciência Social",
            min=0,
            max=15,
            description="5 itens (0-3 cada) sobre percepção social.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="social_cognition",
            label="Cognição Social",
            min=0,
            max=15,
            description="5 itens (0-3 cada) sobre interpretação social.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="social_communication",
            label="Comunicação Social",
            min=0,
            max=15,
            description="5 itens (0-3 cada) sobre expressão social.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="social_motivation",
            label="Motivação Social",
            min=0,
            max=15,
            description="5 itens (0-3 cada) sobre interesse em interação.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="restricted_interests",
            label="Interesses Restritos",
            min=0,
            max=15,
            description="5 itens (0-3 cada) sobre comportamento repetitivo.",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="total",
            label="Escore Total (bruto)",
            min=0,
            max=75,
            description="Soma das 5 sub-escalas. NÃO é T-score oficial.",
            higher_is_worse=True,
        ),
    ],
    score_function=_score_srs2,
    interpretation_function=_interpret_srs2,
    description=(
        "Rastreamento de traços de TEA em comportamento social. "
        "Versão reduzida de 25 itens. ATENÇÃO: T-score oficial NÃO é "
        "produzido nesta versão."
    ),
    is_public=True,
    requires_training=False,
    languages=("pt-BR", "en-US"),
)
