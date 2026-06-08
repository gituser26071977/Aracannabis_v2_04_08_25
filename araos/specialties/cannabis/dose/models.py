"""
AraOS Cannabis Module — Dose Timeline.

Timeline de doses e eventos de medicação.

Week 11B — Cannabis Module V1
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from araos.specialties.cannabis.medication.models import CannabisMedication


@dataclass
class CannabisDoseEntry:
    """
    Entrada de dose em um momento específico.

    Pode representar:
        - Dose inicial
        - Aumento de dose
        - Redução de dose
        - Mudança de produto
        - Interrupção
    """
    entry_id: str
    medication_id: str
    patient_id: str
    tenant_id: str
    dose_mg: float
    thc_mg: float = 0.0
    cbd_mg: float = 0.0
    entry_type: str = "dose_adjustment"  # initial, increase, decrease, product_change, pause, resume, discontinue
    reason: str = ""
    physician_id: str = ""
    entry_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "medication_id": self.medication_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "dose_mg": self.dose_mg,
            "thc_mg": self.thc_mg,
            "cbd_mg": self.cbd_mg,
            "entry_type": self.entry_type,
            "reason": self.reason,
            "physician_id": self.physician_id,
            "entry_date": self.entry_date.isoformat(),
            "metadata": self.metadata,
        }


class CannabisDoseTimeline:
    """
    Timeline de doses de cannabis.

    Registra todas as mudanças de dose ao longo do tempo.
    Alimenta Digital Twin e Clinical Timeline.
    """

    def __init__(self, patient_id: str, tenant_id: str):
        self.patient_id = patient_id
        self.tenant_id = tenant_id
        self._entries: List[CannabisDoseEntry] = []

    def add_entry(self, entry: CannabisDoseEntry) -> None:
        """Adiciona entrada à timeline."""
        self._entries.append(entry)

    def get_entries(
        self,
        entry_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[CannabisDoseEntry]:
        """Recupera entradas com filtros."""
        results = self._entries.copy()

        if entry_type:
            results = [e for e in results if e.entry_type == entry_type]

        if start_date:
            results = [e for e in results if e.entry_date >= start_date]

        if end_date:
            results = [e for e in results if e.entry_date <= end_date]

        return sorted(results, key=lambda e: e.entry_date)

    def get_current_dose(self) -> Optional[CannabisDoseEntry]:
        """Retorna a dose atual (última entrada ativa)."""
        active = [e for e in self._entries if e.entry_type != "discontinue"]
        if active:
            return max(active, key=lambda e: e.entry_date)
        return None

    def get_initial_dose(self) -> Optional[CannabisDoseEntry]:
        """Retorna a dose inicial."""
        initial = [e for e in self._entries if e.entry_type == "initial"]
        if initial:
            return min(initial, key=lambda e: e.entry_date)
        return None

    def get_dose_changes(self) -> List[CannabisDoseEntry]:
        """Retorna todas as mudanças de dose."""
        return [e for e in self._entries if e.entry_type in ("increase", "decrease", "product_change")]

    def get_max_dose(self) -> Optional[CannabisDoseEntry]:
        """Retorna a maior dose registrada."""
        if not self._entries:
            return None
        return max(self._entries, key=lambda e: e.dose_mg)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "entry_count": len(self._entries),
            "entries": [e.to_dict() for e in sorted(self._entries, key=lambda e: e.entry_date)],
            "current_dose": self.get_current_dose().to_dict() if self.get_current_dose() else None,
        }

    def calculate_titration_summary(self) -> Dict[str, Any]:
        """Resumo da titulação de dose."""
        initial = self.get_initial_dose()
        current = self.get_current_dose()

        if not initial or not current:
            return {"error": "Doses insuficientes para análise"}

        return {
            "initial_dose_mg": initial.dose_mg,
            "current_dose_mg": current.dose_mg,
            "initial_thc_mg": initial.thc_mg,
            "current_thc_mg": current.thc_mg,
            "initial_cbd_mg": initial.cbd_mg,
            "current_cbd_mg": current.cbd_mg,
            "dose_change_mg": round(current.dose_mg - initial.dose_mg, 2),
            "dose_change_percent": round(((current.dose_mg - initial.dose_mg) / initial.dose_mg) * 100, 1) if initial.dose_mg > 0 else 0.0,
            "total_adjustments": len(self.get_dose_changes()),
        }
