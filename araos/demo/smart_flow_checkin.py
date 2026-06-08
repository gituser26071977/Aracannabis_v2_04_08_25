"""
AraOS Demo — Fluxo 2: Smart Flow → Check-in → Event Bus → Consulta

Demonstra:
    1. Paciente chega na clínica
    2. Smart Flow detecta check-in
    3. Eventos propagam contexto
    4. Voice recebe automaticamente dados do paciente
    5. Consulta é iniciada com contexto completo
"""

import asyncio
from datetime import datetime, timezone

from araos.platform.event_bus.envelope import EventEnvelopeV2, EventCategory
from .demo_base import DemoEnvironment


def now_utc():
    return datetime.now(timezone.utc)


async def run_smart_flow_checkin(env: DemoEnvironment = None) -> dict:
    """
    Executa Fluxo 2: Smart Flow → Check-in → Event Bus → Consulta.
    """
    env = env or DemoEnvironment().setup()
    env.print_header("FLUXO 2: SMART FLOW → CHECK-IN → EVENT BUS → CONSULTA")
    
    # ─── Setup ───────────────────────────────────────────────────────
    env.print_section("1. Setup: Paciente agendado para consulta")
    env.create_patient_with_data()
    print(f"   ✓ Paciente: {env.patient_id}")
    print(f"   ✓ Clínica: {env.clinic_id}")
    print(f"   ✓ Médico: Dr. Anderson Silva")
    
    consultation_id = "demo_consultation_001"
    
    # ─── Passo 1: Smart Flow detecta chegada ────────────────────────
    env.print_section("2. Smart Flow detecta paciente na entrada")
    
    checkin_event = EventEnvelopeV2(
        event_type="CHECKIN_DETECTED",
        tenant_id=env.tenant_id,
        payload={
            "patient_id": env.patient_id,
            "clinic_id": env.clinic_id,
            "room_id": "room_01",
            "checkin_method": "face",
            "biometric_confidence": 0.97,
            "_aggregate_type": "checkin",
            "_aggregate_id": "checkin_001",
        },
        event_category=EventCategory.OPERATIONAL,
        actor_id="smart_flow_camera_01",
        actor_type="system",
        metadata={"source": "smart_flow"},
    )
    await env.event_bus.publish(checkin_event)
    print(f"   ✓ Evento CHECKIN_DETECTED emitido")
    print(f"   ✓ Método: reconhecimento facial (97% confiança)")
    
    # ─── Passo 2: Check-in concluído ─────────────────────────────────
    env.print_section("3. Check-in concluído com identificação")
    
    checkin_completed = EventEnvelopeV2(
        event_type="CHECKIN_COMPLETED",
        tenant_id=env.tenant_id,
        payload={
            "checkin_id": "checkin_001",
            "patient_id": env.patient_id,
            "consultation_id": consultation_id,
            "room_id": "room_01",
            "biometric_confidence": 0.97,
            "checkin_method": "face",
            "_aggregate_type": "checkin",
            "_aggregate_id": "checkin_001",
        },
        event_category=EventCategory.OPERATIONAL,
        actor_id="smart_flow",
        actor_type="system",
        metadata={"source": "smart_flow"},
    )
    checkin_completed.with_causation(checkin_event)
    await env.event_bus.publish(checkin_completed)
    print(f"   ✓ Evento CHECKIN_COMPLETED emitido")
    print(f"   ✓ Paciente identificado: {env.patient_id}")
    
    # ─── Passo 3: Contexto propagado para Voice ─────────────────────
    env.print_section("4. Contexto propagado automaticamente")
    
    # Voice carrega Digital Twin do paciente
    from araos.clinical.twin.models import PatientDigitalTwinBuilder
    
    builder = PatientDigitalTwinBuilder(env.db, env.patient_id, env.tenant_id)
    twin = await builder.build()
    
    print(f"   ✓ Voice recebe contexto do paciente automaticamente")
    print(f"   ✓ Diagnósticos: {len(twin.active_diagnoses)}")
    print(f"   ✓ Medicações: {len(twin.active_medications)}")
    print(f"   ✓ Alergias: {len(twin.allergies)}")
    
    # ─── Passo 4: Consulta iniciada com contexto ────────────────────
    env.print_section("5. Consulta iniciada com contexto completo")
    
    consultation_started = EventEnvelopeV2(
        event_type="CONSULTATION_STARTED",
        tenant_id=env.tenant_id,
        payload={
            "consultation_id": consultation_id,
            "patient_id": env.patient_id,
            "doctor_id": env.doctor_id,
            "clinic_id": env.clinic_id,
            "room_id": "room_01",
            "started_at": now_utc().isoformat(),
            "context_loaded": True,
            "_aggregate_type": "consultation",
            "_aggregate_id": consultation_id,
        },
        event_category=EventCategory.CLINICAL,
        actor_id=env.doctor_id,
        actor_type="professional",
        metadata={"source": "siap"},
    )
    consultation_started.with_causation(checkin_completed)
    await env.event_bus.publish(consultation_started)
    print(f"   ✓ Evento CONSULTATION_STARTED emitido")
    print(f"   ✓ Médico tem acesso completo ao Digital Twin")
    
    # ─── Passo 5: Voice oferece assistência ────────────────────────
    env.print_section("6. Voice Copilot oferece assistência")
    
    print(f"   🎤 'Ara, resumo do paciente para consulta {consultation_id}'")
    print(f"   🤖 Resposta estruturada:")
    print()
    print(f"      ── PACIENTE: {env.patient_id} ──")
    for d in twin.active_diagnoses:
        print(f"      🏥 {d.get('description')} (ICD-10: {d.get('icd10_code')})")
    for m in twin.active_medications:
        print(f"      💊 {m.get('name')} {m.get('dosage')} {m.get('frequency')}")
    for a in twin.allergies:
        print(f"      ⚠️  Alergia: {a.get('substance')} [{a.get('severity')}]")
    
    # ─── Passo 6: Evolução registrada ───────────────────────────────
    env.print_section("7. Evolução clínica registrada")
    
    evolution_event = EventEnvelopeV2(
        event_type="EVOLUTION_CREATED",
        tenant_id=env.tenant_id,
        payload={
            "consultation_id": consultation_id,
            "patient_id": env.patient_id,
            "doctor_id": env.doctor_id,
            "content": "Paciente relata cefaleia tensional. Mantém HAS controlada.",
            "_aggregate_type": "evolution",
            "_aggregate_id": "evo_001",
        },
        event_category=EventCategory.CLINICAL,
        actor_id=env.doctor_id,
        actor_type="professional",
        metadata={"source": "siap"},
    )
    evolution_event.with_causation(consultation_started)
    await env.event_bus.publish(evolution_event)
    print(f"   ✓ Evento EVOLUTION_CREATED emitido")
    
    # ─── Métricas ───────────────────────────────────────────────────
    env.print_section("8. Métricas do fluxo")
    
    events = env.event_bus.get_events()
    print(f"   ✓ Total de eventos: {len(events)}")
    
    chain = env.event_bus.get_correlation_chain(checkin_event.correlation_id)
    print(f"   ✓ Cadeia completa: {len(chain)} eventos")
    print(f"   ✓ Fluxo: CHECKIN_DETECTED → CHECKIN_COMPLETED → CONSULTATION_STARTED → EVOLUTION_CREATED")
    
    env.print_section("✅ FLUXO 2 CONCLUÍDO")
    
    return {
        "flow": "smart_flow_checkin",
        "patient_id": env.patient_id,
        "consultation_id": consultation_id,
        "events_count": len(events),
        "correlation_chain_length": len(chain),
        "checkin_method": "face",
        "biometric_confidence": 0.97,
    }
