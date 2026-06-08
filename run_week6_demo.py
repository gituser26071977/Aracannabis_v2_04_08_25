#!/usr/bin/env python3
"""
AraOS Week 6 — Demonstração dos Fluxos MVP

Executa os 3 fluxos end-to-end de integração:
    1. Concierge → Digital Twin → Voice
    2. Smart Flow → Check-in → Event Bus → Consulta
    3. WhatsApp → Intake → Documentos → Consulta

Uso:
    python3 run_week6_demo.py
"""

import asyncio
import sys

sys.path.insert(0, ".")

from araos.demo.demo_base import DemoEnvironment
from araos.demo.concierge_intake_flow import run_concierge_intake_flow
from araos.demo.smart_flow_checkin import run_smart_flow_checkin
from araos.demo.whatsapp_document_flow import run_whatsapp_document_flow


async def main():
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "ARAOS WEEK 6 — MVP INTEGRATION SPRINT" + " " * 16 + "║")
    print("║" + " " * 68 + "║")
    print("║  Fluxos end-to-end sem LLMs — validação da arquitetura de plataforma  ║")
    print("╚" + "═" * 68 + "╝")
    
    results = []
    
    # ─── Fluxo 1 ─────────────────────────────────────────────────────
    env1 = DemoEnvironment().setup()
    try:
        result1 = await run_concierge_intake_flow(env1)
        results.append(result1)
    finally:
        env1.teardown()
    
    # ─── Fluxo 2 ─────────────────────────────────────────────────────
    env2 = DemoEnvironment().setup()
    try:
        result2 = await run_smart_flow_checkin(env2)
        results.append(result2)
    finally:
        env2.teardown()
    
    # ─── Fluxo 3 ─────────────────────────────────────────────────────
    env3 = DemoEnvironment().setup()
    try:
        result3 = await run_whatsapp_document_flow(env3)
        results.append(result3)
    finally:
        env3.teardown()
    
    # ─── Resumo ──────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("  RESUMO DOS FLUXOS")
    print("=" * 70)
    
    total_events = sum(r["events_count"] for r in results)
    
    for r in results:
        print(f"\n  {r['flow'].upper()}")
        print(f"    Paciente: {r['patient_id']}")
        print(f"    Eventos: {r['events_count']}")
        print(f"    Cadeia de correlação: {r['correlation_chain_length']} eventos")
    
    print(f"\n  TOTAL: {total_events} eventos processados")
    print(f"  STATUS: ✅ Todos os fluxos concluídos com sucesso")
    print()
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
