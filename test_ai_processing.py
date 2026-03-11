"""
Script de teste para verificar o processamento de IA
"""

import requests

# URL base da API
BASE_URL = "http://localhost:5003"

def test_ai_health():
    """Testa o endpoint de saúde da IA"""
    print("🔍 Testando saúde da IA...")
    try:
        response = requests.get(f"{BASE_URL}/api/ai-config/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Saúde da IA: {data['status']}")
            print(f"📡 Provedores disponíveis: {data['available_providers']}")
            print(f"⚙️  Provedor padrão: {data['default_provider']}")
            print(f"🤖 Modelo padrão: {data['default_model']}")
            return True
        else:
            print(f"❌ Erro na saúde da IA: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar saúde da IA: {str(e)}")
        return False

def test_evolution_processing():
    """Testa o processamento de evolução com IA"""
    print("\n🧪 Testando processamento de evolução...")
    
    # Texto de exemplo para processamento
    evolution_text = """
    Paciente relata melhora significativa na dor crônica após iniciar tratamento com óleo de CBD.
    Está usando 20mg de CBD duas vezes ao dia. Relata que o sono melhorou e a ansiedade diminuiu.
    Sem efeitos colaterais significativos. Sugerir continuar com a mesma dosagem por mais 2 semanas.
    """
    
    # Importar função diretamente para teste
    try:
        from services.ai_agents import process_evolution_input_optimized
        
        print("📝 Processando evolução com IA...")
        result = process_evolution_input_optimized(evolution_text)
        
        print("✅ Processamento concluído!")
        print(f"🤖 Provedor usado: {result.get('ai_provider', 'N/A')}")
        print(f"🔄 Modelo usado: {result.get('ai_model', 'N/A')}")
        print(f"📊 Sintomas detectados: {result.get('symptoms_detected', [])}")
        print(f"💊 Efeitos do tratamento: {result.get('treatment_effects', 'N/A')}")
        print(f"📝 Observações: {result.get('observations', 'N/A')}")
        print(f"💡 Sugestões: {result.get('suggestions', [])}")
        
        if result.get('fallback_used'):
            print("⚠️  AVISO: Fallback usado - IA pode não estar funcionando corretamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no processamento de evolução: {str(e)}")
        return False

def test_import_processing():
    """Testa o processamento de importação com IA"""
    print("\n📥 Testando processamento de importação...")
    
    import_data = """
    Evolução: 15/11/2025 - Paciente relata melhora na dor. CBD 25mg 2x/dia.
    Dosagem: THC 5mg 1x/dia para dor noturna.
    Sintomas: Dor leve (2/10), ansiedade moderada.
    """
    
    try:
        from services.ai_agents import process_import_data
        
        print("📝 Processando dados de importação...")
        result = process_import_data(import_data, patient_id=1)
        
        print("✅ Importação processada!")
        print(f"🤖 Provedor usado: {result.get('ai_provider', 'N/A')}")
        print(f"🔄 Modelo usado: {result.get('ai_model', 'N/A')}")
        print(f"📊 Tipo de dados: {result.get('tipo', 'N/A')}")
        print(f"📈 Evoluções extraídas: {len(result.get('evolucoes', []))}")
        print(f"💊 Dosagens extraídas: {len(result.get('dosagens', []))}")
        print(f"🩺 Sintomas extraídos: {len(result.get('sintomas', []))}")
        print(f"🎯 Confiança: {result.get('confianca', 'N/A')}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no processamento de importação: {str(e)}")
        return False

def test_chat_with_data():
    """Testa o chat com dados"""
    print("\n💬 Testando chat com dados...")
    
    try:
        from services.ai_agents import chat_with_data
        
        # Contexto de exemplo
        context = {
            'paciente': {
                'nome': 'João Silva',
                'condicao_medica': 'Dor crônica'
            },
            'evolucoes': [
                {'descricao': 'Melhora significativa na dor após CBD'},
                {'descricao': 'Sono melhorado, ansiedade reduzida'}
            ],
            'dosagens': [
                {'medicamento': 'CBD', 'dose': '20mg', 'frequencia': '2x/dia'}
            ],
            'sintomas': [
                {'sintoma': 'Dor', 'intensidade': '2/10'},
                {'sintoma': 'Ansiedade', 'intensidade': 'Moderada'}
            ]
        }
        
        question = "Quais são os principais benefícios que o paciente está relatando?"
        
        print("💭 Enviando pergunta para IA...")
        result = chat_with_data(question, context)
        
        print("✅ Resposta recebida!")
        print(f"🤖 Provedor usado: {result.get('ai_provider', 'N/A')}")
        print(f"🔄 Modelo usado: {result.get('ai_model', 'N/A')}")
        print(f"💬 Resposta: {result.get('resposta', 'N/A')[:200]}...")
        print(f"📊 Dados citados: {result.get('dados_citados', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no chat com dados: {str(e)}")
        return False

def test_ai_providers():
    """Testa os provedores de IA disponíveis"""
    print("\n🔧 Testando provedores de IA...")
    
    try:
        from services.ai_agents import ai_manager
        
        available_providers = ai_manager.get_available_providers()
        print(f"✅ Provedores disponíveis: {available_providers}")
        
        # Testar cada provedor
        for provider in available_providers:
            print(f"\n🧪 Testando provedor: {provider}")
            
            test_messages = [
                {"role": "system", "content": "Você é um assistente útil. Responda apenas 'OK'."},
                {"role": "user", "content": "Teste"}
            ]
            
            try:
                response = ai_manager.chat_completion(
                    messages=test_messages,
                    provider=provider,
                    temperature=0.1,
                    max_tokens=10
                )
                
                print(f"   ✅ {provider}: Funcionando")
                print(f"   📝 Resposta: {response.get('content', 'N/A')}")
                
            except Exception as e:
                print(f"   ❌ {provider}: Erro - {str(e)}")
        
        return len(available_providers) > 0
        
    except Exception as e:
        print(f"❌ Erro ao testar provedores: {str(e)}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 INICIANDO TESTES DE IA")
    print("=" * 50)
    
    # Testar saúde da IA
    health_ok = test_ai_health()
    
    # Testar provedores
    providers_ok = test_ai_providers()
    
    # Testar processamento de evolução
    evolution_ok = test_evolution_processing()
    
    # Testar processamento de importação
    import_ok = test_import_processing()
    
    # Testar chat com dados
    chat_ok = test_chat_with_data()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print(f"🔍 Saúde da IA: {'✅' if health_ok else '❌'}")
    print(f"🔧 Provedores: {'✅' if providers_ok else '❌'}")
    print(f"🧪 Processamento de evolução: {'✅' if evolution_ok else '❌'}")
    print(f"📥 Processamento de importação: {'✅' if import_ok else '❌'}")
    print(f"💬 Chat com dados: {'✅' if chat_ok else '❌'}")
    
    total_tests = 5
    passed_tests = sum([health_ok, providers_ok, evolution_ok, import_ok, chat_ok])
    
    print(f"\n🎯 Resultado: {passed_tests}/{total_tests} testes passaram")
    
    if passed_tests == total_tests:
        print("🎉 SISTEMA DE IA FUNCIONANDO PERFEITAMENTE!")
    else:
        print("⚠️  Alguns testes falharam. Verifique as configurações de IA.")

if __name__ == "__main__":
    main()
