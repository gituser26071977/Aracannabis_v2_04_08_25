"""
Vineland-3 — Vineland Adaptive Behavior Scales, Third Edition.

Avaliação padronizada de comportamento adaptativo em 4 domínios
(Communication, Daily Living, Socialization, Motor Skills) por
entrevista estruturada com pais/responsáveis (Comprehensive Interview
Form) ou questionário (Parent/Guardian Form).

Aplicação:
    - Forma completa (entrevista): 60-90 min por profissional treinado.
    - Forma questionário: 20-30 min, autoaplicável por pais.

Idades:
    - Forma entrevista: 0-90 anos.
    - Forma questionário: 3-21 anos.
    - Motor Skills aplicável apenas até 6 anos (<72 meses); após,
      o domínio Motor não compõe o Adaptive Behavior Composite.

Scoring original:
    - Escala-V (V-scale): M=15, DP=3.
    - Escala padrão (Standard): M=100, DP=15.
    - Requer tabelas normativas baseadas em idade cronológica.

Nossa implementação:
    - Coleta por escore bruto em cada domínio (mínimo, versão reduzida
      de 5 itens por domínio — 20 itens totais, escala Likert 0-2).
    - Cálculo do Adaptive Behavior Composite (soma dos 4 domínios).
    - Interpretação por banda relativa ao total bruto:
        • 0-10  → bem abaixo do esperado
        • 11-20 → abaixo do esperado
        • 21-30 → adequado
        • 31-40 → acima do esperado
    - T-scores oficiais NÃO são produzidos (requerem tabelas normativas
      específicas por idade). Para produção clínica, integrar tabelas
      normativas em Sprint futura.

IMPORTANTE (anti-engano):
    Esta versão NÃO substitui o cálculo oficial com tabelas normativas
    do instrumento original. É uma alternativa reduzida para screening
    e monitoramento longitudinal. Resultados oficiais exigem aplicação
    do protocolo original por profissional habilitado.

Referência:
    Sparrow SS, Cicchetti DV, Saulnier CA. Vineland Adaptive Behavior
    Scales, Third Edition (Vineland-3). San Antonio, TX: Pearson; 2016.
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


# 4 domínios × 5 itens cada (versão reduzida).
# Resposta 0 (nunca/incapaz), 1 (às vezes), 2 (frequentemente/sempre).

VINELAND_COMMUNICATION: List[Tuple[str, str]] = [
    ("vn1", "Responde quando alguém fala com ele(a)"),
    ("vn2", "Segue instruções simples do cotidiano"),
    ("vn3", "Aponta para coisas que quer ou quer mostrar"),
    ("vn4", "Diz palavras/frases para se comunicar"),
    ("vn5", "Compreende histórias simples contadas"),
]

VINELAND_DAILY_LIVING: List[Tuple[str, str]] = [
    ("vn6", "Come sozinho(a) com talheres"),
    ("vn7", "Veste-se sozinho(a) com supervisão mínima"),
    ("vn8", "Escova os dentes com supervisão"),
    ("vn9", "Toma banho com supervisão"),
    ("vn10", "Pede para ir ao banheiro ou usa banheiro independentemente"),
]

VINELAND_SOCIALIZATION: List[Tuple[str, str]] = [
    ("vn11", "Sorri para outras pessoas"),
    ("vn12", "Brinca com outras crianças"),
    ("vn13", "Compartilha brinquedos voluntariamente"),
    ("vn14", "Cumprimenta pessoas conhecidas"),
    ("vn15", "Demonstra empatia em situações emocionais"),
]

VINELAND_MOTOR: List[Tuple[str, str]] = [
    ("vn16", "Senta-se sem apoio"),
    ("vn17", "Anda sem apoio"),
    ("vn18", "Corre"),
    ("vn19", "Pula com os dois pés"),
    ("vn20", "Pega objetos pequenos com pinça"),
]


# ─── Funções puras ─────────────────────────────────────────────────


def _score_vineland(raw: RawResponses) -> ComputedScores:
    """Soma por domínio (0-10 cada) + Adaptive Behavior Composite (0-40).

    IMPORTANTE: o domínio Motor é aplicável apenas até 6 anos (72 meses);
    quando aplicado a crianças maiores, deve ser ignorado (composite
    considera apenas os 3 outros domínios, range 0-30).

    O domínio é detectado a partir da presença dos itens (vn16-vn20).
    """
    comm = _sum_domain(raw, VINELAND_COMMUNICATION, "vn")
    daily = _sum_domain(raw, VINELAND_DAILY_LIVING, "vn")
    social = _sum_domain(raw, VINELAND_SOCIALIZATION, "vn")
    motor_items = {code for code, _ in VINELAND_MOTOR}
    has_motor = any(c in raw for c in motor_items)

    motor = 0.0
    if has_motor:
        motor = _sum_domain(raw, VINELAND_MOTOR, "vn")

    total = comm + daily + social + motor
    return {
        "communication": float(comm),
        "daily_living": float(daily),
        "socialization": float(social),
        "motor_skills": float(motor),
        "total": float(total),
    }


def _sum_domain(
    raw: RawResponses, items: List[Tuple[str, str]], _: str
) -> float:
    total = 0
    for code, _label in items:
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if not isinstance(v, int) or not 0 <= v <= 2:
            raise ValueError(
                f"{code} deve ser inteiro 0-2, recebido {v!r}"
            )
        total += v
    return total


def _interpret_vineland(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação por Adaptive Behavior Composite (soma dos domínios).

    ATENÇÃO: bandas baseadas em escores brutos. T-scores oficiais
    requerem tabelas normativas por idade (não implementadas nesta
    versão plugin).
    """
    total = int(scores["total"])
    comm = int(scores["communication"])
    daily = int(scores["daily_living"])
    social = int(scores["socialization"])
    motor = int(scores["motor_skills"])

    if total <= 10:
        band = "bem_abaixo_esperado"
        label_pt = "Bem abaixo do esperado"
        color = "#d64545"
        rec = (
            "Escore bruto bem abaixo do esperado. Encaminhar para avaliação "
            "diagnóstica formal por equipe multidisciplinar (T-scores oficiais "
            "requerem aplicação do protocolo Vineland-3 padrão)."
        )
    elif total <= 20:
        band = "abaixo_esperado"
        label_pt = "Abaixo do esperado"
        color = "#e07b00"
        rec = (
            "Escore bruto abaixo do esperado. Considerar suporte adaptativo "
            "e reavaliação em 6 meses com escores normativos."
        )
    elif total <= 30:
        band = "adequado"
        label_pt = "Adequado"
        color = "#14a085"
        rec = (
            "Escore bruto dentro da faixa esperada para idade. Manter "
            "monitoramento longitudinal."
        )
    else:
        band = "acima_esperado"
        label_pt = "Acima do esperado"
        color = "#0d7377"
        rec = "Escore bruto acima do esperado. Comportamento adaptativo sólido."

    # Sinaliza domínios individuais muito baixos
    domains_low = []
    if comm <= 1:
        domains_low.append("Comunicação")
    if daily <= 1:
        domains_low.append("Habilidades Cotidianas")
    if social <= 1:
        domains_low.append("Socialização")
    if motor <= 1 and motor > 0:
        domains_low.append("Motor")

    if domains_low:
        rec = (
            rec
            + " ATENÇÃO: domínio(s) com escore crítico: "
            + ", ".join(domains_low)
            + "."
        )

    return {
        "total": ScaleInterpretation(
            band=band,
            label_pt=label_pt,
            label_en=f"Adaptive behavior {band.replace('_', ' ')}",
            color=color,
            recommendation=rec,
            references=[
                "Sparrow, Cicchetti & Saulnier, 2016 (Vineland-3 manual)",
            ],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _vineland_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}

    def _add(items: List[Tuple[str, str]], section_label: str) -> None:
        for code, label in items:
            properties[code] = {
                "type": "integer",
                "minimum": 0,
                "maximum": 2,
                "description": (
                    f"[{section_label}] {label} "
                    "(0=nunca/incapaz, 1=às vezes, 2=frequentemente/sempre)"
                ),
                "title": f"Item {code[2:]}",
            }

    _add(VINELAND_COMMUNICATION, "Comunicação")
    _add(VINELAND_DAILY_LIVING, "Habilidades Cotidianas")
    _add(VINELAND_SOCIALIZATION, "Socialização")
    _add(VINELAND_MOTOR, "Motor")

    required_communication = [c for c, _ in VINELAND_COMMUNICATION]
    required_daily = [c for c, _ in VINELAND_DAILY_LIVING]
    required_social = [c for c, _ in VINELAND_SOCIALIZATION]
    # Motor é opcional (apenas até 6 anos)
    required = required_communication + required_daily + required_social

    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
        "title": "Vineland-3 (versão reduzida)",
        "description": (
            "Comportamento adaptativo em 4 domínios. ATENÇÃO: T-scores "
            "oficiais NÃO calculados nesta versão — escores brutos apenas."
        ),
    }


# ─── Spec final ────────────────────────────────────────────────────


VINELAND_SPEC = ScaleSpec(
    code="VINELAND",
    name="Vineland Adaptive Behavior Scales, Third Edition (versão reduzida)",
    version="1.0",
    author="Sparrow, Cicchetti & Saulnier (2016)",
    scientific_reference=(
        "Sparrow SS, Cicchetti DV, Saulnier CA. Vineland Adaptive "
        "Behavior Scales, Third Edition (Vineland-3). San Antonio, TX: "
        "Pearson; 2016."
    ),
    target_age_months=(0, 12 * 90),  # 0-90 anos (forma entrevista completa)
    administration_time_min=25,  # forma questionário
    json_schema=_vineland_json_schema(),
    subscales=[
        ScaleSubscale(
            code="communication",
            label="Comunicação",
            min=0,
            max=10,
            description="5 itens (0-2 cada) sobre linguagem receptiva/expressiva.",
            higher_is_worse=False,  # aqui, MAIOR = MELHOR
        ),
        ScaleSubscale(
            code="daily_living",
            label="Habilidades Cotidianas",
            min=0,
            max=10,
            description="5 itens (0-2 cada) sobre autonomia pessoal.",
            higher_is_worse=False,
        ),
        ScaleSubscale(
            code="socialization",
            label="Socialização",
            min=0,
            max=10,
            description="5 itens (0-2 cada) sobre interação social.",
            higher_is_worse=False,
        ),
        ScaleSubscale(
            code="motor_skills",
            label="Habilidades Motoras",
            min=0,
            max=10,
            description="5 itens (0-2 cada). Aplicável até 6 anos (<72 meses).",
            higher_is_worse=False,
        ),
        ScaleSubscale(
            code="total",
            label="Adaptive Behavior Composite (bruto)",
            min=0,
            max=40,
            description="Soma dos domínios. NÃO é T-score oficial.",
            higher_is_worse=False,
        ),
    ],
    score_function=_score_vineland,
    interpretation_function=_interpret_vineland,
    description=(
        "Avaliação do comportamento adaptativo em 4 domínios. IMPORTANTE: "
        "esta versão reduzida opera com escores brutos e NÃO produz "
        "T-scores oficiais. Para uso clínico definitivo, aplicar protocolo "
        "original com tabelas normativas por idade."
    ),
    is_public=True,
    requires_training=True,  # exige profissional habilitado
    languages=("pt-BR", "en-US"),
)
