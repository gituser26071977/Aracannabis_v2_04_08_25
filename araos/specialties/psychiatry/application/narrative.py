"""Síntese narrativa com guardrails (sem linguagem diagnóstica)."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

from ..domain.items import InstrumentConfig
from ..domain.scoring import Evaluation

logger = logging.getLogger(__name__)

_FORBIDDEN_PATTERNS = [
    r"\bdiagn[óo]stico\s*:",
    r"\bo paciente tem\b",
    r"\btem transtorno\b",
    r"\bdx\b",
    r"\bprescrev\w*",
    r"\bantidepressiv\w*",
    r"\bantipsic[óo]tic\w*",
    r"\bestabilizador\w* de humor\b",
    r"\bbenzo\w*",
    r"\bthc\b",
    r"\bcbd\b",
]


def _high_domains(evaluation: Evaluation, cfg: InstrumentConfig) -> List[str]:
    return [cfg.domain_label(c) for c in cfg.domain_codes if evaluation.indices.get(c, 0) >= 67]


def _moderate_domains(evaluation: Evaluation, cfg: InstrumentConfig) -> List[str]:
    return [cfg.domain_label(c) for c in cfg.domain_codes if 34 <= evaluation.indices.get(c, 0) < 67]


def build_narrative(evaluation: Evaluation, cfg: InstrumentConfig) -> str:
    high = _high_domains(evaluation, cfg)
    moderate = _moderate_domains(evaluation, cfg)
    sentences: List[str] = []

    if high:
        sentences.append(
            "O padrão atual apresenta maior compatibilidade clínica com " + ", ".join(high) + "."
        )
    elif moderate:
        sentences.append(
            "O padrão atual apresenta elementos compatíveis com " + ", ".join(moderate) + "."
        )
    else:
        sentences.append("Não foram identificados índices de compatibilidade clinicamente relevantes neste momento.")

    bipolar = evaluation.indices.get("bipolaridade", 0)
    mood = evaluation.patterns.get("mood", {})
    pattern = mood.get("pattern")
    if pattern == "mania_with_psychosis":
        sentences.append(
            "Foram identificados sintomas psicóticos durante episódio de elevação do humor/energia, "
            "o que é compatível com episódio maníaco com sintomas psicóticos, hipótese a investigar."
        )
    elif pattern == "mania":
        sentences.append(
            "Foram identificados elementos compatíveis com episódio maníaco, incluindo prejuízo funcional "
            "e/ou comportamento de risco; necessita avaliação complementar."
        )
    elif pattern == "hipomania":
        sentences.append(
            "Foram identificados elementos compatíveis com episódio hipomaníaco, com mudança observável "
            "e redução da necessidade de sono, sem prejuízo grave."
        )
    elif 34 <= bipolar < 67:
        sentences.append(
            "Foram identificados alguns elementos compatíveis com espectro bipolar, porém os dados "
            "disponíveis são insuficientes para caracterização de episódio hipomaníaco/maníaco."
        )

    if evaluation.indices.get("psicose", 0) < 34:
        sentences.append(
            "Não foram identificados elementos suficientes para caracterizar psicose neste momento."
        )
    else:
        sentences.append(
            "Há sinais compatíveis com sintomas psicóticos; necessita avaliação complementar e "
            "investigação da relação temporal com episódios de humor."
        )

    if evaluation.indices.get("tea", 0) >= 34:
        sentences.append(
            "Há características do neurodesenvolvimento que justificam investigação de TEA, "
            "especialmente por sua possível presença desde a infância."
        )

    if evaluation.patterns.get("substance_alert"):
        sentences.append(
            "Há uso de substância/medicamento com relação temporal com os sintomas – avaliar causalidade."
        )

    if evaluation.risk.get("emergency"):
        sentences.append(evaluation.risk.get("recommendation", ""))

    text = " ".join(s.strip() for s in sentences if s).strip()
    return sanitize(text)


def sanitize(text: str) -> str:
    cleaned = text
    for pattern in _FORBIDDEN_PATTERNS:
        cleaned = re.sub(pattern, "[termo removido]", cleaned, flags=re.IGNORECASE)
    return cleaned


def polish_with_llm(text: str, checklist: Optional[str] = None) -> str:
    try:
        from services.ai_agents import ai_manager

        system = (
            "Você é um assistente clínico. Reescreva a síntese abaixo em linguagem acolhedora e "
            "profissional, sem emitir diagnóstico, sem sugerir medicações e sem usar termos proibidos. "
            "O texto deve permanecer fiel aos índices fornecidos."
        )
        prompt = text if not checklist else f"{text}\n\n{checklist}"
        result = ai_manager.chat_completion(prompt=prompt, system=system)
        if result:
            return sanitize(result)
    except Exception as exc:  # noqa: BLE001
        logger.warning("psych_triage_narrative_llm_failed: %s", exc)
    return text


def build_checklist(evaluation: Evaluation, cfg: InstrumentConfig) -> str:
    lines = ["Índices de compatibilidade clínica:"]
    for code in cfg.domain_codes:
        lines.append(f"- {cfg.domain_label(code)}: {evaluation.indices.get(code, 0)}/100")
    risk: Dict[str, Any] = evaluation.risk
    lines.append(f"- Risco suicida: {risk.get('label')}")
    return "\n".join(lines)
