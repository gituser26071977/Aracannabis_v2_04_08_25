"""
AraOS Specialty Framework — Specialty Timeline.

Timeline especializada integrada ao Clinical Timeline.

Week 10 — Specialty Framework Foundation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from araos.clinical.timeline.models import TimelineEntry


@dataclass
class SpecialtyTimelineEvent:
    """
    Evento de timeline especializado.

    Representa uma mudança ou observação específica de uma especialidade.
    Pode ser convertido para TimelineEntry do Clinical Timeline.

    Examples:
        - Cannabis dose change
        - Nutrology weight evolution
        - Psychiatry scale evolution
        - Cardiology BP evolution
    """
    event_id: str
    specialty_code: str
    event_type: str  # dose_change, scale_score, weight_update, bp_reading, etc.
    title: str
    description: str = ""
    value_before: Optional[Any] = None
    value_after: Optional[Any] = None
    unit: str = ""
    severity: str = ""  # info, warning, critical
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "specialty_code": self.specialty_code,
            "event_type": self.event_type,
            "title": self.title,
            "description": self.description,
            "value_before": self.value_before,
            "value_after": self.value_after,
            "unit": self.unit,
            "severity": self.severity,
            "metadata": self.metadata,
            "event_date": self.event_date.isoformat(),
        }

    def to_timeline_entry(
        self,
        patient_id: str,
        tenant_id: str,
    ) -> TimelineEntry:
        """
        Converte para TimelineEntry do Clinical Timeline.

        Permite que eventos especializados apareçam na timeline clínica geral.
        """
        return TimelineEntry(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_id=self.event_id,
            event_type=f"SPECIALTY_{self.event_type.upper()}",
            event_category="specialty",
            title=self.title,
            description=self.description,
            event_date=self.event_date,
            entity_data={
                "specialty_code": self.specialty_code,
                "value_before": self.value_before,
                "value_after": self.value_after,
                "unit": self.unit,
                "severity": self.severity,
            },
            metadata={
                "specialty_event": True,
                **self.metadata,
            },
        )


class SpecialtyTimeline:
    """
    Timeline especializada.

    Agrupa eventos de uma especialidade específica.
    Integra com o Clinical Timeline via conversão.

    Uso:
        timeline = SpecialtyTimeline("cannabis", patient_id="p_001")
        timeline.add_event(SpecialtyTimelineEvent(...))
        entries = timeline.to_timeline_entries(tenant_id="t_001")
    """

    def __init__(self, specialty_code: str, patient_id: str):
        self.specialty_code = specialty_code
        self.patient_id = patient_id
        self._events: List[SpecialtyTimelineEvent] = []

    def add_event(self, event: SpecialtyTimelineEvent) -> None:
        """Adiciona um evento à timeline."""
        self._events.append(event)

    def get_events(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SpecialtyTimelineEvent]:
        """Recupera eventos com filtros."""
        results = self._events.copy()

        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if start_date:
            results = [e for e in results if e.event_date >= start_date]

        if end_date:
            results = [e for e in results if e.event_date <= end_date]

        # Ordenar por data
        results.sort(key=lambda e: e.event_date)
        return results

    def get_latest_event(self, event_type: Optional[str] = None) -> Optional[SpecialtyTimelineEvent]:
        """Recupera o evento mais recente."""
        events = self.get_events(event_type=event_type)
        if not events:
            return None
        return max(events, key=lambda e: e.event_date)

    def to_timeline_entries(self, tenant_id: str) -> List[TimelineEntry]:
        """Converte todos os eventos para TimelineEntry."""
        return [
            e.to_timeline_entry(self.patient_id, tenant_id)
            for e in sorted(self._events, key=lambda e: e.event_date)
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "specialty_code": self.specialty_code,
            "patient_id": self.patient_id,
            "event_count": len(self._events),
            "events": [e.to_dict() for e in sorted(self._events, key=lambda e: e.event_date)],
        }
