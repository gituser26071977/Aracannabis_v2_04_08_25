"""Algoritmo independente de risco suicida."""

from __future__ import annotations

from typing import Any, Dict, List

from .items import InstrumentConfig


def _flag(raw: Dict[str, Any], key: str) -> bool:
    suicide = raw.get("suicide")
    if not isinstance(suicide, dict):
        return False
    return bool(suicide.get(key))


def assess_suicide(raw: Dict[str, Any], cfg: InstrumentConfig) -> Dict[str, Any]:
    cfg_suicide = cfg.suicide
    items = cfg_suicide.get("items", [])
    thresholds = cfg_suicide.get("thresholds", {})
    bands = cfg_suicide.get("bands", {})

    score = 0.0
    positive: List[str] = []
    high_risk_positive: List[str] = []
    for item in items:
        item_id = item["id"]
        if _flag(raw, item_id):
            score += float(item.get("severity", 0))
            positive.append(item_id)
            if item.get("high_risk"):
                high_risk_positive.append(item_id)

    intermediario_threshold = float(thresholds.get("intermediario", thresholds.get("alto", 13) / 2.0))
    alto_threshold = float(thresholds.get("alto", 13))
    iminente_threshold = float(thresholds.get("iminente", 22))

    capacity_for_safety = _flag(raw, cfg_suicide.get("protective_item", "capacidade_seguranca"))
    markers = [m for m in cfg_suicide.get("emergency_markers", []) if _flag(raw, m)]
    min_markers = int(cfg_suicide.get("emergency_min_markers", 3))
    emergency = len(markers) >= min_markers and not capacity_for_safety

    if score >= iminente_threshold or emergency:
        level = "iminente"
    elif score >= alto_threshold:
        level = "alto"
    elif score >= intermediario_threshold:
        level = "intermediario"
    else:
        level = "baixo"

    band = bands.get(level, {})
    return {
        "level": level,
        "label": band.get("label", level.upper()),
        "color": band.get("color", ""),
        "recommendation": band.get("recommendation", ""),
        "score": round(score, 1),
        "positive_items": positive,
        "high_risk_items": high_risk_positive,
        "emergency": emergency or level == "iminente",
        "capacity_for_safety": capacity_for_safety,
        "emergency_markers": markers,
    }
