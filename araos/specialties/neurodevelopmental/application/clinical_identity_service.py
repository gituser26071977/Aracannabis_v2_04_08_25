"""
AraOS Neurodevelopmental — ClinicalIdentity Application Service.

Cria e arquiva identidades clínicas longitudinais.

Padrão:
    caller → service.create(tenant_id, patient_id, actor_id)
        → publisher.publish(CLINICAL_IDENTITY_CREATED, ...)
        → retorna event_id
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from araos.clinical.event_store import ClinicalEventPublisher

from ..domain.clinical_identity import ClinicalIdentity
from ..domain.events import ClinicalIdentityArchived, ClinicalIdentityCreated


@dataclass
class ClinicalIdentityCommandResult:
    """Resultado de uma operação sobre ClinicalIdentity."""

    event_id: str
    identity_id: str
    event_type: str
    occurred_at: datetime


class ClinicalIdentityService:
    """Application service para ClinicalIdentity."""

    def __init__(self, publisher: ClinicalEventPublisher) -> None:
        self._publisher = publisher

    def create(
        self,
        tenant_id: str,
        patient_id: str,
        actor_id: str,
        initial_notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> ClinicalIdentityCommandResult:
        """
        Cria nova ClinicalIdentity em estado ACTIVE.

        Args:
            tenant_id: tenant do AraOS.
            patient_id: ID administrativo do paciente.
            actor_id: profissional que está criando.
            initial_notes: observações iniciais opcionais.
            event_datetime: timestamp clínico (default: now UTC).

        Returns:
            ClinicalIdentityCommandResult com event_id e identity_id.
        """
        when = event_datetime or datetime.now(timezone.utc)

        # 1. Constrói agregado em memória (provisional)
        identity = ClinicalIdentity.create(
            patient_id=patient_id,
            source_event_id="<pending>",  # será preenchido após publish
            initial_notes=initial_notes,
            when=when,
        )

        # 2. Constrói Domain Event
        event = ClinicalIdentityCreated(
            aggregate_type="clinical_identity",
            aggregate_id=str(identity.id),
            actor_id=actor_id,
            occurred_at=when,
            patient_id=patient_id,
            initial_notes=initial_notes,
        )
        payload = event.to_payload()

        # 3. Publica no Event Store
        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="clinical_identity",
            aggregate_id=str(identity.id),
            created_by=actor_id,
        )

        return ClinicalIdentityCommandResult(
            event_id=event_id,
            identity_id=str(identity.id),
            event_type=event.event_type,
            occurred_at=when,
        )

    def archive(
        self,
        tenant_id: str,
        identity_id: str,
        patient_id: str,
        actor_id: str,
        reason: str,
        notes: Optional[str] = None,
        event_datetime: Optional[datetime] = None,
    ) -> ClinicalIdentityCommandResult:
        """
        Arquiva ClinicalIdentity existente.

        Args:
            tenant_id: tenant do AraOS.
            identity_id: ClinicalIdentityId.
            patient_id: patient_id (para indexação).
            actor_id: profissional responsável.
            reason: 'patient_transferred'/'patient_deceased'/etc.
            notes: observação adicional.
            event_datetime: timestamp clínico (default: now UTC).
        """
        when = event_datetime or datetime.now(timezone.utc)

        event = ClinicalIdentityArchived(
            aggregate_type="clinical_identity",
            aggregate_id=identity_id,
            actor_id=actor_id,
            occurred_at=when,
            reason=reason,
            notes=notes,
        )
        payload = event.to_payload()

        event_id = self._publisher.publish(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event.event_type,
            payload=payload,
            event_datetime=when,
            source_module="neurodevelopmental",
            aggregate_type="clinical_identity",
            aggregate_id=identity_id,
            created_by=actor_id,
        )

        return ClinicalIdentityCommandResult(
            event_id=event_id,
            identity_id=identity_id,
            event_type=event.event_type,
            occurred_at=when,
        )