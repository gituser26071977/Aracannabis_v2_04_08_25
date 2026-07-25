"""
AraOS Clinical Event Engine — Publisher.

Ponto único de publicação de eventos.

Fluxo:
    1. Valida `event_type` contra o catálogo
    2. Valida `payload` contra JSON Schema (se registrado)
    3. Escreve no Event Store (PostgreSQL)
    4. Publica no Event Bus (Redis Streams) para fan-out real-time
    5. Retorna `event_id`

Falha no Bus NÃO impede o write no Store (graceful degradation).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .catalog import get_event_definition, is_known_event_type
from .store import ClinicalEventStore
from .validators import validate_event_payload


logger = logging.getLogger(__name__)


class UnknownEventTypeError(ValueError):
    """Erro quando event_type não está no catálogo."""
    pass


class EventValidationError(ValueError):
    """Erro quando payload não passa no JSON Schema."""
    pass


class ClinicalEventPublisher:
    """
    Publicador de eventos clínicos cross-specialty.

    Args:
        store: implementação de ClinicalEventStore (in-memory ou SQLAlchemy)
        bus: AraOSEventBus (opcional — fan-out real-time)
        validate_payload: se True, valida contra JSON Schema do catálogo
    """

    def __init__(
        self,
        store: ClinicalEventStore,
        bus: Optional[Any] = None,
        validate_payload: bool = True,
    ) -> None:
        self.store = store
        self.bus = bus
        self.validate_payload = validate_payload

    def publish(
        self,
        tenant_id: str,
        patient_id: str,
        event_type: str,
        payload: Dict[str, Any],
        event_datetime: Optional[datetime] = None,
        source_module: str = "core",
        metadata: Optional[Dict[str, Any]] = None,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        event_version: Optional[str] = None,
        created_by: Optional[str] = None,
        created_by_user: Optional[str] = None,
    ) -> str:
        """
        Publica um evento clínico.

        Returns:
            event_id (UUID4) do evento persistido.
        """
        # 1. Valida event_type no catálogo
        if not is_known_event_type(event_type):
            raise UnknownEventTypeError(
                f"Event type '{event_type}' not found in catalog. "
                "Register it in araos/clinical/event_store/catalog.py first."
            )
        definition = get_event_definition(event_type)
        assert definition is not None  # narrow para type checker

        # 2. Valida payload (se schema registrado + flag ligado)
        if self.validate_payload and definition.json_schema:
            try:
                validate_event_payload(payload, definition)
            except Exception as e:
                raise EventValidationError(
                    f"Payload validation failed for '{event_type}': {e}"
                ) from e

        # 3. Defaults
        if event_datetime is None:
            event_datetime = datetime.now(timezone.utc)
        if event_version is None:
            event_version = definition.version

        # 4. Escreve no Store
        event_id = self.store.append(
            tenant_id=tenant_id,
            patient_id=patient_id,
            event_type=event_type,
            event_datetime=event_datetime,
            source_module=source_module,
            payload=payload,
            event_version=event_version,
            metadata=metadata,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            created_by=created_by,
            created_by_user=created_by_user,
        )

        # 5. Fan-out no Bus (graceful degradation)
        if self.bus is not None:
            self._publish_to_bus(
                event_id=event_id,
                event_type=event_type,
                event_version=event_version,
                tenant_id=tenant_id,
                patient_id=patient_id,
                payload=payload,
                metadata=metadata,
            )

        return event_id

    def _publish_to_bus(
        self,
        event_id: str,
        event_type: str,
        event_version: str,
        tenant_id: str,
        patient_id: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]],
    ) -> None:
        """
        Tenta publicar no Event Bus. Falha NÃO quebra a operação.
        """
        try:
            from araos.platform.event_bus.envelope import (
                EventEnvelopeV2,
                EventCategory,
            )
            envelope = EventEnvelopeV2(
                event_type=event_type,
                tenant_id=tenant_id,
                payload={
                    "event_id": event_id,
                    "patient_id": patient_id,
                    **payload,
                },
                event_id=event_id,
                event_version=event_version,
                event_category=EventCategory.CLINICAL,
                metadata=metadata or {},
            )
            # Tenta tanto .publish() quanto .publish_sync()
            if hasattr(self.bus, "publish_sync"):
                self.bus.publish_sync(envelope)
            elif hasattr(self.bus, "publish"):
                result = self.bus.publish(envelope)
                # Se for coroutine, não awaita (publisher é síncrono).
                # O Event Bus em si tem seu próprio loop/event loop.
                _ = result
        except Exception as e:  # pragma: no cover — defensive
            logger.warning(
                "Failed to publish to Event Bus (continuing): %s",
                e,
            )
