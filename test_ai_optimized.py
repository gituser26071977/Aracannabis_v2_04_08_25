#!/usr/bin/env python3
"""
Script de teste para o sistema de IA otimizado do Aracannabis
"""

import os
import sys
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório atual ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_ai_providers():
    """Testa todos os provedores de IA disponíveis"""
    
    print("🤖 TESTE DO SISTEMA DE IA OTIMIZADO")
    print("=" * 50)
    
    try:
        from services.ai_agents_optimized import ai_manager, test_llm_connection_optimized
        
        print(f"✅ Módulo de IA carregado com sucesso")
        print(f"📊 Provedores disponíveis: {list(ai_manager.providers.keys())}")
        print(f"🎯 Provedor atual: {ai_manager.current_provider}")
        print()
        
        # Testar cada provedor disponível
        for provider_name in ai_manager.providers.keys():
            print(f"🔍 Testando provedor: {provider_name}")
            
            try:
                provider = ai_manager.providers[provider_name]
                result = provider.test_connection()
                
                if result["success"]:
                    print(f"  ✅ {provider_name}: {result['message']}")
                    print(f"  📝 Resposta: {result.get('response', 'N/A')}")
                else:
                    print(f"  ❌ {provider_name}: {result['error']}")
                    
            except Exception as e:
                print(f"  💥 {provider_name}: Erro - {str(e)}")
            
            print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Erro ao importar módulo de IA: {e}")
        return False
    except Exception as e:
        print(f"💥 Erro geral: {e}")
        return False

def test_evolution_processing():
    """Testa o processamento de evolução"""
    
    print("🧠 TESTE DE PROCESSAMENTO DE EVOLUÇÃO")
    print("=" * 50)
    
    try:
        from services.ai_agents_optimized import process_evolution_input_optimized
        
        test_text = """
        Paciente relata melhora significativa dos sintomas de ansiedade após 
        início do tratamento com óleo de CBD 25mg/ml. Está usando 3 gotas 
        2x ao dia. Diminuição da insônia e melhora do humor. 
        Sem efeitos colaterais relatados.
        """
        
        print("📝 Texto de teste:")
        print(test_text.strip())
        print()
        
        print("🔄 Processando com IA...")
        result = process_evolution_input_optimized(test_text.strip())
        
        print("📊 Resultado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Verificar se o resultado tem a estrutura esperada
        required_keys = ["narrative_evolution", "dosage_info", "symptoms", "observations", "confidence"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if not missing_keys:
            print("✅ Estrutura do resultado está correta")
        else:
            print(f"⚠️  Chaves faltando: {missing_keys}")
        
        if result.get("provider_used"):
            print(f"🤖 Provedor usado: {result['provider_used']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de evolução: {e}")
        return False

def test_import_processing():
    """Testa o processamento de importação"""
    
    print("\n📥 TESTE DE PROCESSAMENTO DE IMPORTAÇÃO")
    print("=" * 50)
    
    try:
        from services.ai_agents_optimized import process_import_data_optimized
        
        test_data = """
        Data: 2024-01-15
        Paciente: João Silva
        Dosagem: Óleo CBD 25mg/ml - 5 gotas manhã e noite
        Sintomas: Ansiedade (intensidade 3), Insônia (intensidade 4)
        Observações: Paciente relata melhora gradual
        """
        
        print("📝 Dados de teste:")
        print(test_data.strip())
        print()
        
        print("🔄 Processando importação...")
        result = process_import_data_optimized(test_data.strip(), patient_id=1)
        
        print("📊 Resultado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("provider_used"):
            print(f"🤖 Provedor usado: {result['provider_used']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de importação: {e}")
        return False

def test_chat_functionality():
    """Testa a funcionalidade de chat"""
    
    print("\n💬 TESTE DE CHAT COM DADOS")
    print("=" * 50)
    
    try:
        from services.ai_agents_optimized import chat_with_data_optimized
        
        # Contexto simulado
        context = {
            "paciente": {
                "nome": "João Silva",
                "condicao_medica": "Ansiedade e Insônia"
            },
            "evolucoes": [
                {
                    "data": "2024-01-15",
                    "descricao": "Melhora dos sintomas de ansiedade",
                    "observacoes": "Sem efeitos colaterais"
                }
            ],
            "dosagens": [
                {
                    "data": "2024-01-15",
                    "produto": "Óleo CBD 25mg/ml",
                    "gotas": 5,
                    "frequencia": 2,
                    "cbd": 25.0,
                    "thc": 0.0
                }
            ],
            "sintomas": [
                {
                    "data": "2024-01-15",
                    "sintoma": "Ansiedade",
                    "intensidade": 3
                }
            ]
        }
        
        question = "Como está a evolução do tratamento do paciente?"
        
        print(f"❓ Pergunta: {question}")
        print()
        
        print("🔄 Processando chat...")
        result = chat_with_data_optimized(question, context)
        
        print("📊 Resultado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get("provider_used"):
            print(f"🤖 Provedor usado: {result['provider_used']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de chat: {e}")
        return False

def check_environment():
    """Verifica as configurações do ambiente"""
    
    print("\n🔧 VERIFICAÇÃO DO AMBIENTE")
    print("=" * 50)
    
    # Verificar variáveis de ambiente importantes
    env_vars = [
        "DEFAULT_LLM_PROVIDER",
        "DEFAULT_LLM_MODEL", 
        "OPENAI_API_KEY",
        "GROQ_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mascarar chaves de API
            if "API_KEY" in var:
                masked_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Não configurado")
    
    print()
    
    # Verificar dependências
    dependencies = [
        "requests",
        "python-dotenv",
        "flask"
    ]
    
    print("📦 Verificando dependências:")
    for dep in dependencies:
        try:
            __import__(dep.replace("-", "_"))
            print(f"✅ {dep}: Instalado")
        except ImportError:
            print(f"❌ {dep}: Não instalado")

def main():
    """Função principal do teste"""
    
    print("🚀 INICIANDO TESTES DO SISTEMA DE IA")
    print("=" * 60)
    print()
    
    # Verificar ambiente
    check_environment()
    
    # Executar testes
    tests = [
        ("Provedores de IA", test_ai_providers),
        ("Processamento de Evolução", test_evolution_processing),
        ("Processamento de Importação", test_import_processing),
        ("Funcionalidade de Chat", test_chat_functionality)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 EXECUTANDO: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"💥 Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! Sistema de IA está funcionando.")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique a configuração.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
