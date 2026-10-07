"""Motor de pontuação multidimensional (funções puras)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .items import InstrumentConfig, PenaltyRule, PsychItem, SynergyRule
from .safety import assess_suicide


@dataclass
class Evaluation:
    indices: Dict[str, float]
    contexts: Dict[str, bool]
    risk: Dict[str, Any]
    patterns: Dict[str, Any]
    contributions: Dict[str, Dict[str, List[Dict[str, Any]]]] = field(default_factory=dict)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def _responses(raw: Dict[str, Any]) -> Dict[str, Any]:
    items = raw.get("items")
    return items if isinstance(items, dict) else {}


def _intensity(resp: Any) -> float:
    if not isinstance(resp, dict):
        return 0.0
    return _clamp(_num(resp.get("intensity")), 0.0, 4.0)


def derive_contexts(raw: Dict[str, Any]) -> Dict[str, bool]:
    episodes = raw.get("episodes") if isinstance(raw.get("episodes"), list) else []
    dev = raw.get("development") if isinstance(raw.get("development"), dict) else {}
    psy = raw.get("psychosis") if isinstance(raw.get("psychosis"), dict) else {}
    relation = str(psy.get("temporal_relation") or "").lower()

    ctx = {
        "episodio_delimitado": any(_num(e.get("duration_days")) >= 2 for e in episodes if isinstance(e, dict)),
        "inicio_infancia": bool(dev.get("childhood_onset")),
        "psicose_alteracao_realidade": str(psy.get("reality_impairment") or "").lower() in ("parcial", "ausente"),
        "reducao_necessidade_sono": any(
            str(e.get("sleep_change") or "").upper() == "B" for e in episodes if isinstance(e, dict)
        ),
        "observable_by_others": any(bool(e.get("observed_by_others")) for e in episodes if isinstance(e, dict)),
        "somente_depressao": relation == "somente_depressao",
    }
    return ctx


def _specificity_factor(item: PsychItem, cfg: InstrumentConfig) -> float:
    return cfg.specificity_factors.get(item.specificity, 0.7)


def _gate(item: PsychItem, contexts: Dict[str, bool]) -> float:
    for required in item.requires_context:
        if not contexts.get(required):
            return 0.3
    return 1.0


def _temporal_modifiers(item: PsychItem, resp: Dict[str, Any], cfg: InstrumentConfig) -> Tuple[float, float]:
    temporal = str(resp.get("temporal") or "")
    change = str(resp.get("change") or "")
    tmod = cfg.temporal_bands.get(temporal, 1.0)
    cmod = cfg.change_bands.get(change, 1.0)

    if item.temporal_mode == "state":
        return tmod, cmod
    if item.temporal_mode == "episodic":
        if temporal not in ("episodico", "ultimos_30_dias", "ultimos_7_dias", "hoje", ""):
            tmod *= 0.4
        if change == "nao":
            tmod *= 0.3
        return tmod, cmod
    if change in ("moderadamente", "claramente", "drasticamente"):
        tmod = 0.4
    return tmod, 1.0


def _item_contribution(
    item: PsychItem, resp: Dict[str, Any], cfg: InstrumentConfig, contexts: Dict[str, bool]
) -> float:
    intensity = _intensity(resp) / 4.0
    if intensity <= 0:
        return 0.0
    tmod, cmod = _temporal_modifiers(item, resp, cfg)
    return intensity * item.weight * _specificity_factor(item, cfg) * tmod * cmod * _gate(item, contexts)


def _is_present(responses: Dict[str, Any], item_id: str) -> bool:
    return _intensity(responses.get(item_id)) > 0


def _apply_synergies(
    totals: Dict[str, float],
    responses: Dict[str, Any],
    rules: Tuple[SynergyRule, ...],
    cfg: InstrumentConfig,
    contexts: Dict[str, bool],
) -> None:
    for rule in rules:
        present = 0
        for item_id in rule.required_items:
            item = cfg.item_by_id(item_id)
            if item is not None and _is_present(responses, item_id) and _gate(item, contexts) >= 1.0:
                present += 1
        if present >= rule.min_present:
            for domain in rule.domains:
                totals[domain] = totals.get(domain, 0.0) + rule.bonus


def _apply_penalties(
    totals: Dict[str, float],
    responses: Dict[str, Any],
    contexts: Dict[str, bool],
    rules: Tuple[PenaltyRule, ...],
) -> None:
    for rule in rules:
        applies = False
        if rule.item and _is_present(responses, rule.item):
            if rule.unless_context and not contexts.get(rule.unless_context):
                applies = True
        if rule.when_context and contexts.get(rule.when_context):
            applies = True
        if applies:
            totals[rule.domain] = totals.get(rule.domain, 0.0) - rule.penalty


def _classify_mood(raw: Dict[str, Any], cfg: InstrumentConfig, contexts: Dict[str, bool]) -> Dict[str, Any]:
    episodes = raw.get("episodes") if isinstance(raw.get("episodes"), list) else []
    episodes = [e for e in episodes if isinstance(e, dict)]
    rules = cfg.mania_rules
    impairment_weights = rules.get("impairment_weights", {})

    hospitalization = any(bool(e.get("hospitalization")) for e in episodes)
    psychosis = any(bool(e.get("psychosis")) for e in episodes)
    dangerous = any(bool(e.get("dangerous_behavior")) for e in episodes)
    worst_impairment = max(
        (impairment_weights.get(str(e.get("functional_impairment") or "").lower(), 0.0) for e in episodes),
        default=0.0,
    )

    pattern = "indeterminado"
    critical = False
    if psychosis:
        pattern = "mania_with_psychosis"
        critical = True
    elif hospitalization or dangerous or worst_impairment >= 0.6:
        pattern = "mania"
    elif (
        contexts.get("episodio_delimitado")
        and contexts.get("observable_by_others")
        and contexts.get("reducao_necessidade_sono")
        and not hospitalization
        and not psychosis
    ):
        pattern = "hipomania"

    return {
        "pattern": pattern,
        "critical": critical,
        "hospitalization": hospitalization,
        "psychosis_in_episode": psychosis,
        "dangerous_behavior": dangerous,
        "worst_functional_impairment": worst_impairment,
    }


def _substance_index(raw: Dict[str, Any], cfg: InstrumentConfig) -> Tuple[float, Dict[str, Any]]:
    substances = raw.get("substances") if isinstance(raw.get("substances"), list) else []
    total = 0.0
    temporal_alert = False
    names: List[str] = []
    for sub in substances:
        if not isinstance(sub, dict):
            continue
        name = str(sub.get("name") or "outras").lower()
        weight = cfg.substance_weights.get(name, cfg.substance_weights.get("outras", 2))
        relation = str(sub.get("temporal_relation") or "").lower()
        worsened = bool(sub.get("worsened"))
        if relation in ("temporal", "piora_apos_uso", "piora") or worsened:
            total += weight
            temporal_alert = True
        else:
            total += weight * 0.5
        names.append(name)
    max_weight = max(1.0, sum(cfg.substance_weights.values()) * 0.4)
    index = _clamp(100.0 * total / max_weight)
    alert = None
    if temporal_alert and substances:
        alert = (
            "Sintomas potencialmente induzidos ou agravados por substância/medicamento "
            "– avaliar causalidade temporal."
        )
    return index, {"alert": alert, "names": names, "temporal_alert": temporal_alert}


def evaluate(raw: Dict[str, Any], cfg: InstrumentConfig) -> Evaluation:
    responses = _responses(raw)
    contexts = derive_contexts(raw)

    totals: Dict[str, float] = {code: 0.0 for code in cfg.domain_codes}
    maxes: Dict[str, float] = {code: 0.0 for code in cfg.domain_codes}

    for item in cfg.items:
        for domain in item.domains:
            maxes[domain] = maxes.get(domain, 0.0) + item.weight
        contribution = _item_contribution(item, responses.get(item.id), cfg, contexts)
        for domain in item.domains:
            totals[domain] = totals.get(domain, 0.0) + contribution

    _apply_synergies(totals, responses, cfg.synergy_rules, cfg, contexts)
    _apply_penalties(totals, responses, contexts, cfg.penalty_rules)

    calibration = cfg.index_calibration if cfg.index_calibration > 0 else 1.0
    indices = {
        code: round(
            _clamp(100.0 * totals[code] / (maxes[code] * calibration)) if maxes.get(code) else 0.0, 1
        )
        for code in cfg.domain_codes
    }

    mood = _classify_mood(raw, cfg, contexts)
    gain_mania = float(cfg.mania_rules.get("mania_index_gain", 25))
    gain_hypo = float(cfg.mania_rules.get("hypomania_index_gain", 15))
    if mood["pattern"] == "mania_with_psychosis":
        indices["mania_hipomania"] = _clamp(indices["mania_hipomania"] + gain_mania)
        indices["bipolaridade"] = _clamp(indices["bipolaridade"] + gain_mania)
    elif mood["pattern"] == "mania":
        indices["mania_hipomania"] = _clamp(indices["mania_hipomania"] + gain_mania)
    elif mood["pattern"] == "hipomania":
        indices["mania_hipomania"] = _clamp(indices["mania_hipomania"] + gain_hypo)

    subst_index, subst_meta = _substance_index(raw, cfg)
    indices["substancias"] = round(subst_index, 1)

    risk = assess_suicide(raw, cfg)

    patterns = {
        "mood": mood,
        "psychosis_temporal_relation": (raw.get("psychosis") or {}).get("temporal_relation"),
        "substances": subst_meta,
        "emergency": risk["emergency"],
        "substance_alert": subst_meta["alert"],
    }

    return Evaluation(indices=indices, contexts=contexts, risk=risk, patterns=patterns)
