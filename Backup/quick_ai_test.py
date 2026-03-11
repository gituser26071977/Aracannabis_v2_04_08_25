#!/usr/bin/env python3
"""Script de teste rápido para agentes de IA"""

from dotenv import load_dotenv
load_dotenv()

def quick_test():
    """Teste rápido de conectividade"""
    print("🔍 TESTE RÁPIDO DE IA")
    
    try:
        from services.ai_agents_optimized import process_evolution_input_optimized
        
        test_text = "Paciente melhorou com CBD"
        print(f"Testando: {test_text}")
        
        result = process_evolution_input_optimized(
            evolution_text_input=test_text,
            timeout=30  # Timeout curto para teste
        )
        
        print("✅ Teste concluído com sucesso!")
        print(f"Resultado: {result}")
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")

if __name__ == "__main__":
    quick_test()
