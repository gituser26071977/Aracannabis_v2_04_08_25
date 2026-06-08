"""
AraOS Demo — Fluxo 1: Concierge → Digital Twin → Voice

Demonstra:
    1. Paciente envia mensagem via Concierge
    2. Concierge processa e gera eventos
    3. Clinical Profile é atualizado
    4. Digital Twin reflete mudanças
    5. Voice consegue responder "resumo do paciente"
"""

import asyncio
from datetime import datetime, timezone

from araos.platform.event_bus.envelope import EventEnvelopeV2, EventCategory
from araos.platform.identity.context import IdentityContext, ActorType
from araos.platform.shared.context import TenantContext
from araos.clinical.twin.models import PatientDigitalTwinBuilder
from araos.clinical.summary.engine import ClinicalSummaryEngine
from .demo_base import DemoEnvironment


def now_utc():
    return datetime.now(timezone.utc)


async def run_concierge_intake_flow(env: DemoEnvironment = None) -> dict:
    """
    Executa Fluxo 1: Concierge → Digital Twin → Voice.
    
    Returns:
        dict com resultados da demo
    """
    env = env or DemoEnvironment().setup()
    env.print_header("FLUXO 1: CONCIERGE → DIGITAL TWIN → VOICE")
    
    # ─── Setup inicial ───────────────────────────────────────────────
    env.print_section("1. Setup: Paciente com dados clínicos iniciais")
    patient_data = env.create_patient_with_data()
    print(f"   ✓ Paciente criado: {env.patient_id}")
    print(f"   ✓ Diagnóstico: Hipertensão Arterial (I10)")
    print(f"   ✓ Medicação: Losartana 50mg")
    print(f"   ✓ Alergia: Penicilina")
    
    # ─── Passo 1: Concierge recebe mensagem ──────────────────────────
    env.print_section("2. Concierge recebe mensagem do paciente")
    
    message_text = "Oi, estou com dor de cabeça forte e tontura"
    
    # Emitir evento de mensagem recebida
    message_event = EventEnvelopeV2(
        event_type="WHATSAPP_RECEIVED",
        tenant_id=env.tenant_id,
        payload={
            "patient_id": env.patient_id,
            "message": message_text,
            "channel": "whatsapp",
            "sender_phone": "5511999999999",
        },
        event_category=EventCategory.COMMUNICATION,
        actor_id=env.patient_id,
        actor_type="patient",
        metadata={"source": "concierge"},
    )
    await env.event_bus.publish(message_event)
    print(f"   ✓ Evento WHATSAPP_RECEIVED emitido")
    print(f"   ✓ Mensagem: \"{message_text}\"")
    
    # ─── Passo 2: Concierge identifica necessidade de coleta ────────
    env.print_section("3. Concierge identifica sintomas e registra")
    
    # Emitir evento de novo diagnóstico (intake)
    intake_event = EventEnvelopeV2(
        event_type="DIAGNOSIS_ADDED",
        tenant_id=env.tenant_id,
        payload={
            "patient_id": env.patient_id,
            "description": "Cefaleia tensional",
            "icd10_code": "G44.2",
            "is_primary": False,
            "is_chronic": False,
            "_aggregate_type": "patient",
            "_aggregate_id": env.patient_id,
        },
        event_category=EventCategory.CLINICAL,
        actor_id="concierge",
        actor_type="agent",
        metadata={"source": "concierge"},
    )
    intake_event.with_causation(message_event)
    await env.event_bus.publish(intake_event)
    print(f"   ✓ Evento DIAGNOSIS_ADDED emitido (Cefaleia tensional)")
    
    # ─── Passo 3: Projection Engine processa evento ─────────────────
    env.print_section("4. Clinical Projection Engine processa eventos")
    
    from araos.clinical.projections.engine import ClinicalProjectionEngine
    
    projection = ClinicalProjectionEngine(env.db)
    result = await projection.process(intake_event)
    
    print(f"   ✓ Projeção executada: {result}")
    
    # ─── Passo 4: Digital Twin reconstruído ─────────────────────────
    env.print_section("5. Patient Digital Twin reconstruído")
    
    builder = PatientDigitalTwinBuilder(env.db, env.patient_id, env.tenant_id)
    twin = await builder.build()
    
    print(f"   ✓ Twin construído para paciente {twin.patient_id}")
    print(f"   ✓ Diagnósticos ativos: {len(twin.active_diagnoses)}")
    print(f"   ✓ Medicações ativas: {len(twin.active_medications)}")
    print(f"   ✓ Alergias: {len(twin.allergies)}")
    print(f"   ✓ Fatores de risco: {len(twin.risk_factors)}")
    
    # ─── Passo 5: Clinical Summary gerado ────────────────────────────
    env.print_section("6. Clinical Summary Engine gera resumo")
    
    engine = ClinicalSummaryEngine()
    summary = engine.generate(twin.profile.to_dict() if twin.profile else {})
    
    print(f"   ✓ Resumo gerado (v{summary.version})")
    print(f"   ✓ Warnings: {summary.warnings}")
    print()
    print("   ── RESUMO CLÍNICO ──")
    for line in summary.text.split("\n"):
        print(f"   {line}")
    
    # ─── Passo 6: Voice responde com contexto ───────────────────────
    env.print_section("7. Voice Copilot acessa Digital Twin")
    
    # Simular query do Voice
    print(f"   🎤 'Ara, resumo do paciente'")
    print(f"   🤖 Resposta: Paciente tem {len(twin.active_diagnoses)} diagnósticos ativos,")
    print(f"      {len(twin.active_medications)} medicações,")
    print(f"      {len(twin.allergies)} alergias registradas.")
    print()
    print(f"   🎤 'Ara, o paciente tem alergias?'")
    if twin.has_severe_allergy():
        print(f"   ⚠️  ALERTA: Alergia grave detectada!")
    else:
        print(f"   🤖 Resposta: Paciente tem {len(twin.allergies)} alergia(s):")
        for a in twin.allergies:
            print(f"      - {a.get('substance')} ({a.get('severity')})")
    
    # ─── Métricas do fluxo ──────────────────────────────────────────
    env.print_section("8. Métricas do Event Bus")
    
    events = env.event_bus.get_events()
    print(f"   ✓ Total de eventos: {len(events)}")
    
    for et in set(e.event_type for e in events):
        count = len([e for e in events if e.event_type == et])
        print(f"   ✓ {et}: {count}")
    
    # Mostrar cadeia de correlação
    chain = env.event_bus.get_correlation_chain(message_event.correlation_id)
    print(f"   ✓ Cadeia de correlação: {len(chain)} eventos ligados")
    
    env.print_section("✅ FLUXO 1 CONCLUÍDO")
    
    return {
        "flow": "concierge_intake",
        "patient_id": env.patient_id,
        "events_count": len(events),
        "diagnoses_count": len(twin.active_diagnoses),
        "medications_count": len(twin.active_medications),
        "allergies_count": len(twin.allergies),
        "summary_text": summary.text,
        "correlation_chain_length": len(chain),
    }
