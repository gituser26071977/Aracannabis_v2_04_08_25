"""Carregamento e registro do instrumento de triagem psiquiátrica."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple

from araos.specialties.neurodevelopmental.scales import (
    ScaleAlreadyRegisteredError,
    ScaleInterpretation,
    ScaleRegistry,
    ScaleSpec,
    ScaleSubscale,
)

from .items import (
    DomainDef,
    InstrumentConfig,
    PenaltyRule,
    PsychItem,
    SynergyRule,
)
from .scoring import Evaluation, evaluate

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config" / "psych_triage"


def _band_index(value: float) -> ScaleInterpretation:
    if value < 34:
        return ScaleInterpretation(
            band="baixa",
            label_pt="Compatibilidade baixa",
            label_en="Low",
            color="#2e7d32",
            recommendation="Poucos elementos compatíveis neste domínio.",
        )
    if value < 67:
        return ScaleInterpretation(
            band="moderada",
            label_pt="Compatibilidade moderada",
            label_en="Moderate",
            color="#f9a825",
            recommendation="Alguns elementos compatíveis; necessita avaliação complementar.",
        )
    return ScaleInterpretation(
        band="alta",
        label_pt="Compatibilidade elevada",
        label_en="High",
        color="#c62828",
        recommendation="Compatibilidade elevada; domínio que merece avaliação especializada.",
    )


@lru_cache(maxsize=None)
def load_config(version: str) -> Dict[str, Any]:
    path = _CONFIG_DIR / f"{version}.json"
    if not path.exists():
        raise FileNotFoundError(f"Configuração do instrumento não encontrada: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_config(data: Dict[str, Any]) -> InstrumentConfig:
    domains = tuple(DomainDef(code=d["code"], label=d["label"]) for d in data["domains"])
    items = tuple(
        PsychItem(
            id=item["id"],
            label=item["label"],
            domains=tuple(item["domains"]),
            weight=float(item["weight"]),
            specificity=item["specificity"],
            temporal_mode=item.get("temporal_mode", "state"),
            requires_context=tuple(item.get("requires_context", ())),
            subdomains=tuple(item.get("subdomains", ())),
        )
        for item in data["items"]
    )
    synergy = tuple(
        SynergyRule(
            id=rule["id"],
            domains=tuple(rule["domains"]),
            required_items=tuple(rule["required_items"]),
            min_present=int(rule["min_present"]),
            bonus=float(rule["bonus"]),
        )
        for rule in data.get("synergy_rules", [])
    )
    penalties = tuple(
        PenaltyRule(
            id=rule["id"],
            domain=rule["domain"],
            item=rule.get("item"),
            unless_context=rule.get("unless_context"),
            when_context=rule.get("when_context"),
            penalty=float(rule.get("penalty", 0.0)),
        )
        for rule in data.get("penalty_rules", [])
    )
    return InstrumentConfig(
        code=data["code"],
        name=data["name"],
        version=data["version"],
        criteria_version=data["criteria_version"],
        disclaimer=data["disclaimer"],
        updated_at=data.get("updated_at", ""),
        domains=domains,
        items=items,
        specificity_factors={k: float(v) for k, v in data["specificity_factors"].items()},
        temporal_bands={b["code"]: float(b["modifier"]) for b in data["temporal_bands"]},
        change_bands={b["code"]: float(b["modifier"]) for b in data["change_bands"]},
        synergy_rules=synergy,
        penalty_rules=penalties,
        mania_rules=data.get("mania_rules", {}),
        substance_weights={k: float(v) for k, v in data.get("substance_weights", {}).items()},
        suicide=data.get("suicide", {}),
        index_calibration=float(data.get("index_calibration", 0.6)),
        intensity_labels={str(k): v for k, v in data.get("intensity_labels", {}).items()},
    )


def _schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": True,
        "properties": {
            "items": {"type": "object"},
            "baseline": {"type": "object"},
            "episodes": {"type": "array"},
            "development": {"type": "object"},
            "psychosis": {"type": "object"},
            "substances": {"type": "array"},
            "suicide": {"type": "object"},
        },
    }


def build_interpretation(evaluation: Evaluation, cfg: InstrumentConfig) -> Dict[str, ScaleInterpretation]:
    interpretation: Dict[str, ScaleInterpretation] = {}
    for code in cfg.domain_codes:
        interpretation[code] = _band_index(evaluation.indices.get(code, 0.0))

    risk = evaluation.risk
    interpretation["risco_suicida"] = ScaleInterpretation(
        band=risk["level"],
        label_pt=risk["label"],
        label_en=risk["level"].upper(),
        color=risk.get("color", ""),
        recommendation=risk.get("recommendation", ""),
        references=[cfg.disclaimer],
    )

    mood = evaluation.patterns.get("mood", {})
    pattern = mood.get("pattern")
    if pattern:
        interpretation["padrao_humor"] = ScaleInterpretation(
            band=pattern,
            label_pt={
                "hipomania": "Padrão compatível com hipomania",
                "mania": "Padrão compatível com mania",
                "mania_with_psychosis": "Padrão compatível com mania com sintomas psicóticos",
                "indeterminado": "Padrão de humor indeterminado",
            }.get(pattern, pattern),
            color="#c62828" if mood.get("critical") else "",
            recommendation=(
                "Presença de sintomas psicóticos – investigar episódio maníaco com sintomas "
                "psicóticos ou outra condição psicótica/afetiva."
                if mood.get("critical")
                else ""
            ),
        )
    return interpretation


def build_spec(version: str = "1.0.0") -> Tuple[ScaleSpec, InstrumentConfig]:
    cfg = parse_config(load_config(version))
    subscales = [
        ScaleSubscale(code=code, label=cfg.domain_label(code), min=0, max=100)
        for code in cfg.domain_codes
    ]
    subscales.append(
        ScaleSubscale(code="risco_suicida", label="Risco suicida", min=0, max=100, higher_is_worse=True)
    )

    def _score(raw: Dict[str, Any]) -> Dict[str, float]:
        evaluation = evaluate(raw, cfg)
        scores = dict(evaluation.indices)
        scores["risco_suicida"] = float(evaluation.risk["score"])
        return scores

    def _interpret(scores: Dict[str, float], raw: Dict[str, Any]) -> Dict[str, ScaleInterpretation]:
        return build_interpretation(evaluate(raw, cfg), cfg)

    spec = ScaleSpec(
        code=cfg.code,
        name=cfg.name,
        version=cfg.version,
        author="AraOS Psychiatry",
        scientific_reference=(
            "Estrutura de critérios baseada em DSM-5-TR e CID-11 (WHO). "
            "Instrumento de triagem e apoio à decisão clínica; não validado como teste diagnóstico."
        ),
        target_age_months=(144, None),
        administration_time_min=20,
        json_schema=_schema(),
        subscales=subscales,
        score_function=_score,
        interpretation_function=_interpret,
        description=cfg.disclaimer,
        is_public=False,
        requires_training=True,
    )
    return spec, cfg


def available_versions() -> Tuple[str, ...]:
    versions = [
        path.stem
        for path in _CONFIG_DIR.glob("*.json")
        if path.stem and path.stem[0].isdigit()
    ]
    return tuple(sorted(versions))


def register_instrument(version: str | None = None) -> None:
    versions = (version,) if version else available_versions()
    for current in versions:
        if ScaleRegistry.has("PSYCH_TRIAGE", current):
            continue
        try:
            spec, _ = build_spec(current)
            ScaleRegistry.register(spec)
        except (ScaleAlreadyRegisteredError, FileNotFoundError):
            continue
