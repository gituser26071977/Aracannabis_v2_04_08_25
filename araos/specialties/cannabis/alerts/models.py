"""
AraOS Cannabis Module — Alerts.

Alertas estruturados para o módulo Cannabis.

Week 11B — Cannabis Module V1
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from araos.followup.core.models import AlertSeverity, AlertStatus


class CannabisAlertType(str):
    """Tipos de alerta do módulo Cannabis."""
    ADVERSE_EFFECT_DETECTED = "adverse_effect_detected"
    NO_CLINICAL_RESPONSE = "no_clinical_response"
    ADHERENCE_PROBLEM = "adherence_problem"
    PATIENT_REQUESTED_REVIEW = "patient_requested_review"
    DOSE_TOLERANCE_ISSUE = "dose_tolerance_issue"
    WORSENING_SYMPTOMS = "worsening_symptoms"
    PRODUCT_EXPIRING = "product_expiring"


@dataclass
class CannabisAlert:
    """Alerta do módulo Cannabis."""
    alert_id: str
    patient_id: str
    tenant_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    description: str = ""
    status: AlertStatus = AlertStatus.OPEN
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    escalation_level: int = 0  # 0 = não escalado, 1 = equipe, 2 = médico, 3 = urgente
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "patient_id": self.patient_id,
            "tenant_id": self.tenant_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "triggered_at": self.triggered_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "escalation_level": self.escalation_level,
            "metadata": self.metadata,
        }

    def escalate(self, level: int = 1) -> None:
        """Escalona o alerta."""
        self.escalation_level = max(self.escalation_level, level)
        if self.escalation_level >= 2:
            self.status = AlertStatus.ESCALATED

    def resolve(self, user_id: str) -> None:
        """Resolve o alerta."""
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = user_id

    def is_open(self) -> bool:
        return self.status in (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)


class CannabisAlertManager:
    """Gerenciador de alertas do módulo Cannabis."""

    def __init__(self):
        self._alerts: List[CannabisAlert] = []

    def create_alert(
        self,
        alert_id: str,
        patient_id: str,
        tenant_id: str,
        alert_type: str,
        severity: AlertSeverity,
        title: str,
        description: str = "",
    ) -> CannabisAlert:
        alert = CannabisAlert(
            alert_id=alert_id,
            patient_id=patient_id,
            tenant_id=tenant_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
        )
        self._alerts.append(alert)
        return alert

    def get_alerts(
        self,
        patient_id: Optional[str] = None,
        alert_type: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
        open_only: bool = False,
    ) -> List[CannabisAlert]:
        results = self._alerts.copy()

        if patient_id:
            results = [a for a in results if a.patient_id == patient_id]

        if alert_type:
            results = [a for a in results if a.alert_type == alert_type]

        if severity:
            results = [a for a in results if a.severity == severity]

        if open_only:
            results = [a for a in results if a.is_open()]

        return results

    def get_open_critical_alerts(self, patient_id: Optional[str] = None) -> List[CannabisAlert]:
        """Recupera alertas críticos em aberto."""
        return self.get_alerts(
            patient_id=patient_id,
            severity=AlertSeverity.CRITICAL,
            open_only=True,
        )

    def summary(self) -> Dict[str, Any]:
        """Resumo de alertas."""
        total = len(self._alerts)
        open_alerts = len([a for a in self._alerts if a.is_open()])
        critical = len([a for a in self._alerts if a.severity == AlertSeverity.CRITICAL])
        escalated = len([a for a in self._alerts if a.escalation_level > 0])

        by_type: Dict[str, int] = {}
        for a in self._alerts:
            by_type[a.alert_type] = by_type.get(a.alert_type, 0) + 1

        return {
            "total_alerts": total,
            "open_alerts": open_alerts,
            "critical_alerts": critical,
            "escalated_alerts": escalated,
            "by_type": by_type,
        }
