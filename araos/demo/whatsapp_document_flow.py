"""
AraOS Demo — Fluxo 3: WhatsApp → Intake → Documentos → Consulta

Demonstra:
    1. Paciente envia documento via WhatsApp
    2. Documento é processado (OCR/IA)
    3. Timeline atualizada
    4. Digital Twin reflete novo documento
    5. Consulta agenda-se automaticamente
"""

import asyncio
from datetime import datetime, timezone

from araos.platform.event_bus.envelope import EventEnvelopeV2, EventCategory
from .demo_base import DemoEnvironment


def now_utc():
    return datetime.now(timezone.utc)


async def run_whatsapp_document_flow(env: DemoEnvironment = None) -> dict:
    """
    Executa Fluxo 3: WhatsApp → Intake → Documentos → Consulta.
    """
    env = env or DemoEnvironment().setup()
    env.print_header("FLUXO 3: WHATSAPP → INTAKE → DOCUMENTOS → CONSULTA")
    
    # ─── Setup ───────────────────────────────────────────────────────
    env.print_section("1. Setup: Paciente cadastrado")
    env.create_patient_with_data()
    print(f"   ✓ Paciente: {env.patient_id}")
    
    # ─── Passo 1: WhatsApp recebe documento ─────────────────────────
    env.print_section("2. Paciente envia receita médica via WhatsApp")
    
    document_event = EventEnvelopeV2(
        event_type="DOCUMENT_UPLOADED",
        tenant_id=env.tenant_id,
        payload={
            "patient_id": env.patient_id,
            "document_type": "receita",
            "file_name": "receita_2026_06_07.pdf",
            "file_size": 245760,
            "mime_type": "application/pdf",
            "uploaded_by": env.patient_id,
            "_aggregate_type": "document",
            "_aggregate_id": "doc_001",
        },
        event_category=EventCategory.OPERATIONAL,
        actor_id=env.patient_id,
        actor_type="patient",
        metadata={"source": "whatsapp", "channel": "patient"},
    )
    await env.event_bus.publish(document_event)
    print(f"   ✓ Evento DOCUMENT_UPLOADED emitido")
    print(f"   ✓ Arquivo: receita_2026_06_07.pdf (240KB)")
    
    # ─── Passo 2: OCR processa documento ────────────────────────────
    env.print_section("3. Sistema processa documento (OCR)")
    
    processed_event = EventEnvelopeV2(
        event_type="DOCUMENT_PROCESSED",
        tenant_id=env.tenant_id,
        payload={
            "document_id": "doc_001",
            "patient_id": env.patient_id,
            "processing_status": "success",
            "extracted_fields": {
                "tipo": "Receita Médica",
                "medico": "Dr. João Pereira",
                "crm": "CRM-SP 987654",
                "data": "2026-06-01",
                "medicamentos": [
                    {"nome": "Atenolol", "dosagem": "25mg", "frequencia": "1x ao dia"},
                ],
            },
            "confidence_score": 0.94,
            "_aggregate_type": "document",
            "_aggregate_id": "doc_001",
        },
        event_category=EventCategory.OPERATIONAL,
        actor_id="system",
        actor_type="system",
        metadata={"source": "intake"},
    )
    processed_event.with_causation(document_event)
    await env.event_bus.publish(processed_event)
    print(f"   ✓ Evento DOCUMENT_PROCESSED emitido")
    print(f"   ✓ OCR: Atenolol 25mg detectado (94% confiança)")
    
    # ─── Passo 3: Medicação adicionada ao perfil ───────────────────
    env.print_section("4. Medicação extraída adicionada ao perfil")
    
    med_event = EventEnvelopeV2(
        event_type="MEDICATION_PRESCRIBED",
        tenant_id=env.tenant_id,
        payload={
            "patient_id": env.patient_id,
            "name": "Atenolol",
            "generic_name": "Atenolol",
            "dosage": "25mg",
            "frequency": "1x ao dia",
            "route": "oral",
            "source": "document_extraction",
            "document_id": "doc_001",
            "_aggregate_type": "patient",
            "_aggregate_id": env.patient_id,
        },
        event_category=EventCategory.CLINICAL,
        actor_id="intake",
        actor_type="agent",
        metadata={"source": "intake"},
    )
    med_event.with_causation(processed_event)
    await env.event_bus.publish(med_event)
    print(f"   ✓ Evento MEDICATION_PRESCRIBED emitido")
    
    # Week 7A: Projeção é feita automaticamente pelo Consumer no Event Bus
    print(f"   ✓ Evento encaminhado para ClinicalProjectionConsumer")
    
    # ─── Passo 4: Timeline atualizada ───────────────────────────────
    env.print_section("5. Timeline clínica atualizada")
    
    from araos.clinical.timeline.models import TimelineEntry
    entries = env.db.query(TimelineEntry).filter(
        TimelineEntry.patient_id == env.patient_id,
    ).order_by(TimelineEntry.event_date.desc()).all()
    
    if entries:
        print(f"   ✓ Timeline: {len(entries)} entradas")
        for e in entries:
            print(f"   ✓ [{e.event_type}] {e.title}")
    else:
        print(f"   ✓ Timeline vazia (projeção não persistiu timeline)")
    
    # ─── Passo 5: Digital Twin atualizado ──────────────────────────
    env.print_section("6. Patient Digital Twin atualizado")
    
    from araos.clinical.twin.models import PatientDigitalTwinBuilder
    
    builder = PatientDigitalTwinBuilder(env.repository, cache=env.cache)
    twin = await builder.build(env.patient_id, env.tenant_id)
    
    print(f"   ✓ Twin reconstruído")
    print(f"   ✓ Diagnósticos: {len(twin.active_diagnoses)}")
    print(f"   ✓ Medicações: {len(twin.active_medications)}")
    
    med_names = [m.get("name") for m in twin.active_medications]
    print(f"   ✓ Medicações atuais: {', '.join(med_names)}")
    
    # ─── Passo 6: Consulta agendada ─────────────────────────────────
    env.print_section("7. Consulta agendada automaticamente")
    
    consultation_id = "demo_consultation_doc_001"
    
    schedule_event = EventEnvelopeV2(
        event_type="CONSULTATION_SCHEDULED",
        tenant_id=env.tenant_id,
        payload={
            "consultation_id": consultation_id,
            "patient_id": env.patient_id,
            "doctor_id": env.doctor_id,
            "clinic_id": env.clinic_id,
            "scheduled_at": "2026-06-10T14:00:00",
            "reason": "Ajuste de medicação (receita recebida)",
            "source": "intake_automation",
            "_aggregate_type": "consultation",
            "_aggregate_id": consultation_id,
        },
        event_category=EventCategory.OPERATIONAL,
        actor_id="concierge",
        actor_type="agent",
        metadata={"source": "concierge"},
    )
    schedule_event.with_causation(med_event)
    await env.event_bus.publish(schedule_event)
    print(f"   ✓ Evento CONSULTATION_SCHEDULED emitido")
    print(f"   ✓ Consulta agendada: 10/06/2026 às 14:00")
    print(f"   ✓ Motivo: Ajuste de medicação")
    
    # ─── Métricas ───────────────────────────────────────────────────
    env.print_section("8. Métricas do fluxo")
    
    events = env.event_bus.get_events()
    print(f"   ✓ Total de eventos: {len(events)}")
    
    chain = env.event_bus.get_correlation_chain(document_event.correlation_id)
    print(f"   ✓ Cadeia de correlação: {len(chain)} eventos")
    print(f"   ✓ Fluxo: DOCUMENT_UPLOADED → DOCUMENT_PROCESSED → MEDICATION_PRESCRIBED → CONSULTATION_SCHEDULED")
    
    env.print_section("✅ FLUXO 3 CONCLUÍDO")
    
    return {
        "flow": "whatsapp_document",
        "patient_id": env.patient_id,
        "events_count": len(events),
        "correlation_chain_length": len(chain),
        "medications_after": len(twin.active_medications),
        "consultation_scheduled": consultation_id,
        "ocr_confidence": 0.94,
    }
