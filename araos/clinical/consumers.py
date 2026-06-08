"""
AraOS Clinical — Event Consumers.

Week 7A Hardening:
    - Consumers de produção para eventos clínicos
    - Desacoplamento: publishers não chamam Projection Engine diretamente
    - Registro via Event Bus subscribe()
"""

from typing import List

from araos.platform.event_bus.envelope import EventEnvelopeV2
from .projections.engine import ClinicalProjectionEngine


class ClinicalProjectionConsumer:
    """
    Consumer que processa eventos clínicos via Projection Engine.
    
    Uso:
        consumer = ClinicalProjectionConsumer(engine)
        await event_bus.subscribe(
            event_types=["DIAGNOSIS_ADDED", "MEDICATION_PRESCRIBED", ...],
            group="clinical_projection",
            handler=consumer.handle,
        )
    """
    
    CLINICAL_EVENT_TYPES = [
        "DIAGNOSIS_ADDED",
        "DIAGNOSIS_UPDATED",
        "MEDICATION_PRESCRIBED",
        "MEDICATION_STOPPED",
        "ALLERGY_REGISTERED",
        "ALLERGY_REMOVED",
        "EXAM_RESULTED",
        "CLINICAL_NOTE_CREATED",
        "PROCEDURE_APPLIED",
    ]
    
    def __init__(self, engine: ClinicalProjectionEngine):
        self.engine = engine
    
    async def handle(self, event: EventEnvelopeV2) -> None:
        """Handler para Event Bus."""
        result = await self.engine.process(event)
        # Em produção, métricas e logs aqui
        return result


def register_clinical_consumers(event_bus, engine: ClinicalProjectionEngine) -> None:
    """
    Registra todos os consumers clínicos no Event Bus.
    
    Args:
        event_bus: Instância de EventBus (AraOSEventBus ou InMemoryEventBus)
        engine: ClinicalProjectionEngine configurado
    """
    consumer = ClinicalProjectionConsumer(engine)
    event_bus.subscribe(
        event_types=consumer.CLINICAL_EVENT_TYPES,
        group="clinical_projection",
        handler=consumer.handle,
    )
