"""
M-CHAT-R/F — Modified Checklist for Autism in Toddlers, Revised with Follow-Up.

Rastreamento de TEA em crianças de 16 a 30 meses. Autoaplicável pelos
pais/responsáveis (~5 min). Validada por Robins et al. (2009).

Itens (20, dicotômicos):
    - 7 itens CRÍTICOS (Q2, Q5, Q7, Q9, Q13, Q14, Q15): risco
      elevado se ≥2 positivos, independentemente do total.
    - Score total: 0-20 (cada "comportamento atípico" = 1 ponto).
      • 0-2  → baixo risco
      • 3-7  → médio risco (follow-up recomendado)
      • 8-20 → alto risco (encaminhar para avaliação diagnóstica)

Direção da codificação: 1 = comportamento atípico (risco);
0 = comportamento típico. Cada item é uma pergunta cuja resposta
de risco está descrita no enunciado.

Versão PT-BR adaptada de:
    Losapio MF, Pondé MP. Tradução para o português brasileiro do
    Modified Checklist for Autism in Toddlers (M-CHAT). Rev Psiquiatr
    Rio Gd Sul. 2010.

Referência científica original:
    Robins DL, Casagrande K, Barton M, Chen CM, Dumont-Mathieu T,
    Fein D. Validation of the Modified Checklist for Autism in
    Toddlers, Revised with Follow-Up (M-CHAT-R/F). Pediatrics.
    2014;133(1):37-45. doi:10.1542/peds.2013-1813

Versão M-CHAT-R original:
    Robins DL, Fein D, Barton ML, Green JA. The Modified Checklist
    for Autism in Toddlers: an initial study investigating the early
    detection of autism and pervasive developmental disorders.
    J Autism Dev Disord. 2001;31(2):131-144.
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


# Itens em PT-BR (adaptados de Losapio & Pondé, 2010).
# Cada tuple é (código, enunciado, indicador_de_risco_no_enunciado, é_crítico).
# Indicador_de_risco é textual para auditoria: "nao" se o risco for
# assinalar "NÃO apresenta o comportamento"; "sim" se o risco for "SIM
# apresenta o comportamento". Isso é usado para gerar a recomendação
# clínica caso o item seja positivo, mas NÃO afeta o scoring binário.
MCHAT_ITEMS_PT_BR: List[Tuple[str, str, str, bool]] = [
    ("q1", "Se você apontar para algum objeto, seu filho olha para ele?", "nao", False),
    ("q2", "Alguma vez você já se perguntou se seu filho pode ser surdo?", "sim", True),
    ("q3", "Seu filho já brincou de faz-de-conta (ex: fingir que um bloco é comida)?", "nao", False),
    ("q4", "Seu filho gosta de subir em coisas (ex: cadeiras, escadas)?", "nao", False),
    ("q5", "Seu filho já fez movimentos estranhos com os dedos perto dos olhos?", "sim", True),
    ("q6", "Seu filho já apontou com o dedo para pedir alguma coisa?", "nao", False),
    ("q7", "Seu filho já apontou com o dedo para mostrar algo interessante?", "nao", True),
    ("q8", "Seu filho tem interesse em outras crianças?", "nao", False),
    ("q9", "Seu filho já trouxe objetos para você mostrar algo?", "nao", True),
    ("q10", "Seu filho já respondeu quando você chamou pelo nome dele?", "nao", False),
    ("q11", "Quando você sorri para seu filho, ele sorri de volta?", "nao", False),
    ("q12", "Seu filho já se incomodou com barulhos do dia a dia (ex: aspirador, fogão)?", "sim", False),
    ("q13", "Seu filho já consegue andar?", "nao", True),
    ("q14", "Seu filho olha nos seus olhos quando você está falando, brincando ou vestindo-o?", "nao", True),
    ("q15", "Seu filho tenta imitar seus movimentos (ex: acenar, bater palma)?", "nao", True),
    ("q16", "Se você virar a cabeça para olhar algo, seu filho olha ao redor para ver o que você está olhando?", "nao", False),
    ("q17", "Seu filho já tentou fazer você olhar para ele?", "nao", False),
    ("q18", "Seu filho já entendeu quando você disse para ele fazer algo?", "nao", False),
    ("q19", "Se algo novo aparece, seu filho olha para o seu rosto para ver como você se sente?", "nao", False),
    ("q20", "Seu filho gosta de atividades de movimento (ex: ser balançado, pular)?", "nao", False),
]

CRITICAL_CODES: Tuple[str, ...] = ("q2", "q5", "q7", "q9", "q13", "q14", "q15")


# ─── Funções puras ─────────────────────────────────────────────────


def _score_mchat(raw: RawResponses) -> ComputedScores:
    """Soma simples: total + subscore de itens críticos positivos."""
    total = 0
    critical = 0
    for code, *_ in MCHAT_ITEMS_PT_BR:
        v = raw.get(code)
        if v is None:
            raise ValueError(f"Questão {code} ausente")
        if v not in (0, 1):
            raise ValueError(
                f"{code} deve ser 0 (típico) ou 1 (atípico/risco), recebido {v!r}"
            )
        total += v
        if code in CRITICAL_CODES and v == 1:
            critical += 1
    return {
        "total": float(total),
        "critical_positives": float(critical),
    }


def _interpret_mchat(
    scores: ComputedScores,
    raw: RawResponses,
) -> Dict[str, ScaleInterpretation]:
    """Interpretação conforme protocolo M-CHAT-R/F (Robins et al. 2014)."""
    total = int(scores["total"])
    critical = int(scores["critical_positives"])

    # Regra M-CHAT-R/F: ≥2 críticos positivos → risco elevado, mesmo se total<3
    if critical >= 2:
        band = "alto_risco"
        label_pt = "Risco elevado (≥2 itens críticos positivos)"
        color = "#d64545"
        rec = (
            "Encaminhar IMEDIATAMENTE para avaliação diagnóstica especializada. "
            f"Foram assinalados {critical} itens críticos (positivos) e {total} no total."
        )
    elif total <= 2:
        band = "baixo_risco"
        label_pt = "Baixo risco"
        color = "#14a085"
        rec = "Baixo risco para TEA. Manter vigilância de rotina."
    elif total <= 7:
        band = "medio_risco"
        label_pt = "Risco moderado"
        color = "#f5a623"
        rec = (
            "Aplicar entrevistas de follow-up estruturado (forma M-CHAT-R/F) "
            "para refinar o risco. Reavaliar em 30 dias."
        )
    else:
        band = "alto_risco"
        label_pt = "Risco elevado"
        color = "#d64545"
        rec = (
            "Encaminhar IMEDIATAMENTE para avaliação diagnóstica especializada "
            "(neurologista / psiquiatra infantil / equipe TEA)."
        )

    # Adiciona nota se houver ao menos um crítico positivo (sem chegar a 2)
    if critical == 1 and total <= 2:
        rec = (
            rec
            + " ATENÇÃO: 1 item crítico positivo — considerar re-aplicação em 30 dias."
        )

    return {
        "total": ScaleInterpretation(
            band=band,
            label_pt=label_pt,
            label_en=f"Autism risk {band.replace('_', ' ')}",
            color=color,
            recommendation=rec,
            references=[
                "Robins et al., 2014 (Pediatrics 133:37-45)",
                "Losapio & Pondé, 2010 (versão PT-BR)",
            ],
        )
    }


# ─── JSON Schema ───────────────────────────────────────────────────


def _mchat_json_schema() -> Dict:
    properties: Dict[str, Dict] = {}
    for code, label, risk_dir, is_critical in MCHAT_ITEMS_PT_BR:
        risk_text = (
            "Marque 1 (risco) se a resposta for SIM"
            if risk_dir == "sim"
            else "Marque 1 (risco) se a resposta for NÃO"
        )
        item_schema = {
            "type": "integer",
            "enum": [0, 1],
            "description": f"{label} {risk_text}",
            "title": f"Questão {code[1:]}",
        }
        if is_critical:
            item_schema["description"] += " ⚠️ Item crítico."
        properties[code] = item_schema
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": properties,
        "required": [code for code, *_ in MCHAT_ITEMS_PT_BR],
        "additionalProperties": False,
        "title": "M-CHAT-R/F",
        "description": "Rastreamento de TEA em toddlers (16-30 meses) — versão PT-BR",
    }


# ─── Spec final ────────────────────────────────────────────────────


MCHAT_SPEC = ScaleSpec(
    code="MCHAT",
    name="Modified Checklist for Autism in Toddlers, Revised (M-CHAT-R/F)",
    version="1.0",
    author="Robins, Casagrande, Barton, Chen, Dumont-Mathieu & Fein (2014)",
    scientific_reference=(
        "Robins DL, Casagrande K, Barton M, Chen CM, Dumont-Mathieu T, "
        "Fein D. Validation of the Modified Checklist for Autism in "
        "Toddlers, Revised with Follow-Up (M-CHAT-R/F). Pediatrics. "
        "2014;133(1):37-45. doi:10.1542/peds.2013-1813"
    ),
    target_age_months=(16, 30),  # 16-30 meses
    administration_time_min=5,
    json_schema=_mchat_json_schema(),
    subscales=[
        ScaleSubscale(
            code="total",
            label="Score Total",
            min=0,
            max=20,
            description="Soma de itens com comportamento atípico (0-20)",
            higher_is_worse=True,
        ),
        ScaleSubscale(
            code="critical_positives",
            label="Itens Críticos Positivos",
            min=0,
            max=len(CRITICAL_CODES),
            description=(
                "Subtotal dos 7 itens críticos (Q2, Q5, Q7, Q9, Q13, Q14, Q15) "
                f"positivos. ≥2 já indica risco elevado. Máx {len(CRITICAL_CODES)}."
            ),
            higher_is_worse=True,
        ),
    ],
    score_function=_score_mchat,
    interpretation_function=_interpret_mchat,
    description=(
        "Rastreamento populacional de TEA para crianças de 16-30 meses. "
        "Aplicação rápida (5 min) por pais/responsáveis. 20 itens dicotômicos; "
        "≥2 itens críticos positivos já indicam alto risco, independentemente "
        "do escore total."
    ),
    is_public=True,
    requires_training=False,
    languages=("pt-BR", "en-US"),
)
