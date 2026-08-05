"""
Test Builders para Sprint 3.2 — Neurodevelopmental Registry.

API fluente para reduzir boilerplate em testes:

    builder = (RegistryBuilder()
               .with_identity(patient_id="patient-1")
               .with_diagnosis(condition_code="TEA_F84.0", state="confirmed")
               .with_phenotype(code="social_deficit", severity="moderate")
               .with_medication(subtype="risperidona", dose=Dose(...))
               .with_intervention(subtype="aba", state="started")
               .with_assessment(scale_code="MCHAT_R_F")
               .with_outcome(type="improvement")
               .build())

Cada builder retorna uma estrutura pronta para:
    - Inserir em InMemoryClinicalEventStore (cenários integration)
    - Aplicar via REDACTED (cenários projection)
    - Validar invariantes via domain assertions
"""
from .registry_builder import RegistryBuilder, RegistryFixture
from .event_builder import EventBuilder, build_clinical_event

__all__ = [
    "RegistryBuilder",
    "RegistryFixture",
    "EventBuilder",
    "build_clinical_event",
]
