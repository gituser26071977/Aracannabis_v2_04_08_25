"""Explicabilidade por domínio (fatores que aumentam/reduzem o índice)."""

from __future__ import annotations

from typing import Any, Dict, List

from .items import InstrumentConfig, PsychItem
from .scoring import _gate, _item_contribution, _is_present, derive_contexts


def _context_reason(item: PsychItem) -> str:
    reasons = {
        "episodio_delimitado": "sem episódio claramente delimitado",
        "inicio_infancia": "características não presentes desde a infância/adolescência",
        "psicose_alteracao_realidade": "sem evidência de alteração do teste de realidade",
        "reducao_necessidade_sono": "sono não reduzido por ausência de necessidade",
    }
    return ", ".join(reasons.get(ctx, ctx) for ctx in item.requires_context)


def explain(raw: Dict[str, Any], cfg: InstrumentConfig) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:  # noqa: C901
    responses = raw.get("items") if isinstance(raw.get("items"), dict) else {}
    contexts = derive_contexts(raw)
    domains = cfg.domain_codes
    report: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
        code: {"increased": [], "decreased": []} for code in domains
    }

    for item in cfg.items:
        resp = responses.get(item.id)
        contribution = _item_contribution(item, resp, cfg, contexts)
        if contribution > 0:
            for domain in item.domains:
                report[domain]["increased"].append(
                    {"item": item.id, "label": item.label, "contribution": round(contribution, 2)}
                )
        elif item.requires_context and _is_present(responses, item.id):
            for domain in item.domains:
                report[domain]["decreased"].append(
                    {"item": item.id, "label": item.label, "reason": _context_reason(item)}
                )

    for rule in cfg.synergy_rules:
        present = 0
        for item_id in rule.required_items:
            item = cfg.item_by_id(item_id)
            if item is not None and _is_present(responses, item_id) and _gate(item, contexts) >= 1.0:
                present += 1
        if present >= rule.min_present:
            for domain in rule.domains:
                report[domain]["increased"].append(
                    {"item": rule.id, "label": f"Agrupamento clínico ({rule.id})", "contribution": rule.bonus}
                )

    for rule in cfg.penalty_rules:
        applies = False
        reason = ""
        if rule.item and _is_present(responses, rule.item):
            if rule.unless_context and not contexts.get(rule.unless_context):
                applies = True
                reason = _context_reason(cfg.item_by_id(rule.item)) if cfg.item_by_id(rule.item) else ""
        if rule.when_context and contexts.get(rule.when_context):
            applies = True
            reason = "sintomas explicados por outra condição"
        if applies:
            report[rule.domain]["decreased"].append(
                {
                    "item": rule.item or rule.id,
                    "label": "Penalidade clínica",
                    "reason": reason or "sintomas inespecíficos isolados",
                }
            )

    for domain in domains:
        report[domain]["increased"].sort(key=lambda e: e.get("contribution", 0), reverse=True)
    return report
