"""Contratos de domínio do módulo de triagem psiquiátrica."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class PsychItem:
    id: str
    label: str
    domains: Tuple[str, ...]
    weight: float
    specificity: str
    temporal_mode: str
    requires_context: Tuple[str, ...] = ()
    subdomains: Tuple[str, ...] = ()


@dataclass(frozen=True)
class DomainDef:
    code: str
    label: str


@dataclass(frozen=True)
class SynergyRule:
    id: str
    domains: Tuple[str, ...]
    required_items: Tuple[str, ...]
    min_present: int
    bonus: float


@dataclass(frozen=True)
class PenaltyRule:
    id: str
    domain: str
    item: str | None = None
    unless_context: str | None = None
    when_context: str | None = None
    penalty: float = 0.0


@dataclass(frozen=True)
class SuicideItem:
    id: str
    label: str
    severity: float
    high_risk: bool


@dataclass(frozen=True)
class InstrumentConfig:
    code: str
    name: str
    version: str
    criteria_version: str
    disclaimer: str
    updated_at: str
    domains: Tuple[DomainDef, ...]
    items: Tuple[PsychItem, ...]
    specificity_factors: Dict[str, float]
    temporal_bands: Dict[str, float]
    change_bands: Dict[str, float]
    synergy_rules: Tuple[SynergyRule, ...]
    penalty_rules: Tuple[PenaltyRule, ...]
    mania_rules: Dict[str, Any]
    substance_weights: Dict[str, float]
    suicide: Dict[str, Any]
    index_calibration: float = 0.6
    intensity_labels: Dict[str, str] = field(default_factory=dict)

    @property
    def domain_codes(self) -> Tuple[str, ...]:
        return tuple(d.code for d in self.domains)

    def item_by_id(self, item_id: str) -> PsychItem | None:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def domain_label(self, code: str) -> str:
        for d in self.domains:
            if d.code == code:
                return d.label
        return code
