"""
AraOS Cannabis Module — Medication Registry.

Registro de produtos e medicações de cannabis.

Week 11B — Cannabis Module V1
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class CannabinoidProfile:
    """Perfil de canabinoides de um produto."""
    cbd_mg: float = 0.0
    thc_mg: float = 0.0
    cbg_mg: float = 0.0
    cbn_mg: float = 0.0
    cbc_mg: float = 0.0
    thcv_mg: float = 0.0
    unit: str = "mg/ml"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cbd_mg": self.cbd_mg,
            "thc_mg": self.thc_mg,
            "cbg_mg": self.cbg_mg,
            "cbn_mg": self.cbn_mg,
            "cbc_mg": self.cbc_mg,
            "thcv_mg": self.thcv_mg,
            "unit": self.unit,
        }

    def total_cannabinoids_mg(self) -> float:
        return self.cbd_mg + self.thc_mg + self.cbg_mg + self.cbn_mg + self.cbc_mg + self.thcv_mg


@dataclass
class CannabisProduct:
    """
    Produto de cannabis medicinal.

    Attributes:
        product_id: ID único
        name: Nome comercial
        manufacturer: Fabricante
        formulation: Formulação (oil, capsule, sublingual, topical, inhaled)
        spectrum: full_spectrum, broad_spectrum, isolate
        cannabinoids: Perfil de canabinoides
        concentration: Concentração total
        volume_ml: Volume em ml
        route: Via de administração
        batch_number: Número do lote
        expiry_date: Data de validade
    """
    product_id: str
    name: str
    manufacturer: str = ""
    formulation: str = "oil"  # oil, capsule, sublingual, topical, inhaled, edible
    spectrum: str = "full_spectrum"  # full_spectrum, broad_spectrum, isolate
    cannabinoids: CannabinoidProfile = field(default_factory=CannabinoidProfile)
    concentration: str = ""  # ex: "500mg/30ml"
    volume_ml: float = 0.0
    route: str = "sublingual"  # sublingual, oral, topical, inhaled, rectal
    batch_number: str = ""
    expiry_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "formulation": self.formulation,
            "spectrum": self.spectrum,
            "cannabinoids": self.cannabinoids.to_dict(),
            "concentration": self.concentration,
            "volume_ml": self.volume_ml,
            "route": self.route,
            "batch_number": self.batch_number,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "metadata": self.metadata,
        }

    def is_full_spectrum(self) -> bool:
        return self.spectrum == "full_spectrum"

    def is_broad_spectrum(self) -> bool:
        return self.spectrum == "broad_spectrum"

    def is_isolate(self) -> bool:
        return self.spectrum == "isolate"


@dataclass
class CannabisMedication:
    """
    Medicação de cannabis prescrita a um paciente.

    Representa uma prescrição ativa ou histórica.
    """
    medication_id: str
    patient_id: str
    tenant_id: str
    product: CannabisProduct
    prescribed_dose_mg: float = 0.0
    frequency: str = ""  # 1x/dia, 2x/dia, etc.
    prescribed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    stopped_reason: str = ""  # adverse_effect, no_response, patient_choice, physician_decision
    status: str = "active"  # active, paused, discontinued
    instructions: str = ""
    prescribed_by: str = ""  # physician_id
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "medication_id": self.medication_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "product": self.product.to_dict(),
            "prescribed_dose_mg": self.prescribed_dose_mg,
            "frequency": self.frequency,
            "prescribed_at": self.prescribed_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "stopped_reason": self.stopped_reason,
            "status": self.status,
            "instructions": self.instructions,
            "prescribed_by": self.prescribed_by,
            "metadata": self.metadata,
        }

    def start(self) -> None:
        self.status = "active"
        self.started_at = datetime.now(timezone.utc)

    def stop(self, reason: str) -> None:
        self.status = "discontinued"
        self.stopped_at = datetime.now(timezone.utc)
        self.stopped_reason = reason

    def pause(self) -> None:
        self.status = "paused"

    def resume(self) -> None:
        self.status = "active"

    def is_active(self) -> bool:
        return self.status == "active"

    def get_thc_dose_mg(self) -> float:
        """Calcula dose de THC baseada na concentração."""
        if self.product.volume_ml > 0:
            ratio = self.prescribed_dose_mg / self.product.volume_ml
            return round(self.product.cannabinoids.thc_mg * ratio, 2)
        return 0.0

    def get_cbd_dose_mg(self) -> float:
        """Calcula dose de CBD baseada na concentração."""
        if self.product.volume_ml > 0:
            ratio = self.prescribed_dose_mg / self.product.volume_ml
            return round(self.product.cannabinoids.cbd_mg * ratio, 2)
        return 0.0
