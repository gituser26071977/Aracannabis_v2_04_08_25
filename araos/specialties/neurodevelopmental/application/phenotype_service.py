"""
AraOS Neurodevelopmental — Phenotype Application Service.

Observação e resolução de fenótipos/manifestações funcionais.

ADR-0002 §2.2.3: 'Phenotype pode existir antes do diagnóstico.'
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from araos.clinical.event_store import ClinicalEventPublisher

from ..domain.events import PhenotypeObserved, PhenotypeResolved
from ..domain.ids import PhenotypeId, new_id
from ..domain.phenotype import Phenotype, PhenotypeSeverity


@dataclass
class PhenotypeCommandResult:
    event_id: str
    phenotype_id: str
    event_type: str
    occurred_at: datetime


class PhenotypeService:
    """Application service para Phenotype."""

    def __init__(self, publisher: ClinicalEventPublisher) -> None:
        self._publisher = publisher

    def observe(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        phenotype_code: str,
        severity: PhenotypeSeverity,
        observed_by: str,
        onset_date: Optional[str] = None,
        linked_diagnosis_ids: Optional[List[str]] = None,
        context: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> PhenotypeCommandResult:
        """
        Cria nova Phenotype em estado ativo.
        """
        when = event_datetime or datetime.now(timezone.utc)
        new_phenotype_id = PhenotypeId(new_id())

        event = PhenotypeObserved(
            aggregate_type="phenotype",
            aggregate_id=str(new_phenotype_id),
            actor_id=observed_by,
            occurred_at=when,
            phenotype_code=phenotype_code,
            observed_by=observed_by,
            severity=severity.value,
            onset_date=onset_date,
            linked_diagnosis_ids=linked_diagnosis_ids,
            context=context,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="phenotype",
            aggregate_id=str(new_phenotype_id),
            created_by=observed_by,
        )

        return PhenotypeCommandResult(
            event_id=event_id,
            phenotype_id=str(new_phenotype_id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def resolve(
        self,
        tenant_id: str,
        patient_id: str,
        identity_id: str,
        phenotype_id: str,
        resolved_by: str,
        reason: Optional[str] = None,
        resolution_date: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> PhenotypeCommandResult:
        """
        Marca Phenotype como resolvido. Histórico preservado.
        """
        when = event_datetime or datetime.now(timezone.utc)

        event = PhenotypeResolved(
            aggregate_type="phenotype",
            aggregate_id=phenotype_id,
            actor_id=resolved_by,
            occurred_at=when,
            resolved_by=resolved_by,
            resolution_date=resolution_date,
            reason=reason,
        )
        payload = event.to_payload()
        payload["identity_id"] = identity_id

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="phenotype",
            aggregate_id=phenotype_id,
            created_by=resolved_by,
        )

        return PhenotypeCommandResult(
            event_id=event_id,
            phenotype_id=phenotype_id,
            event_type=event.event_type,
            occurred_at=when,
        )