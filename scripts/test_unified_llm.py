import os
import json
import requests

def test_llm_pipeline():
    print("=== TESTANDO PIPELINE DE LLM UNIFICADO ===")
    
    # 1. Carregar Configurações
    config_path = "config/ai_settings.json"
    if not os.path.exists(config_path):
        print("❌ Erro: ai_settings.json não encontrado!")
        return
        
    with open(config_path, "r") as f:
        settings = json.load(f)
    
    print(f"📍 Provedor Chat: {settings.get('chat_provider')}")
    print(f"📍 Modelo Chat: {settings.get('chat_model')}")
    print(f"📍 Provedor Vision/OCR: {settings.get('default_vision_provider')}")
    
    # 2. Testar LLM Gateway (Zhipu/GLM 4.7)
    # Nota: Assumindo que o gateway está rodando em http://localhost:8000 via docker mappings ou similar
    # Mas como estamos rodando dentro do host, e o gateway está no docker, vamos tentar via porta exposta
    # Verificando porta do gateway no docker-compose... (8000 no container, no compose principal está 8000?)
    # No override está apenas internal_services_net. No principal?
    
    gateway_url = "http://localhost:8000/health" # Ajustar se necessário
    print(f"\n🔍 Checando Gateway em {gateway_url}...")
    try:
        resp = requests.get(gateway_url, timeout=5)
        print(f"✅ Gateway Status: {resp.status_code} - {resp.json()}")
    except Exception as e:
        print(f"❌ Gateway Offline na porta 8000: {e}")
        print("💡 O gateway pode estar rodando dentro da rede do docker sem porta exposta no host.")

    # 3. Testar Anonimizador (Porta 8000 no container, mapeada?)
    # O anonymizer está Up 21 mins (unhealthy). Vamos ver por que.
    print("\n🔍 Checando Anonimizador...")
    try:
        # Tentar porta padrão 8000 se exposta
        resp = requests.get("http://localhost:8000/health", timeout=2)
        print(f"✅ Anonimizador Status: {resp.status_code}")
    except:
        print("❌ Anonimizador inacessível via localhost:8000")

    # 4. Explicação da Programação
    print("\n📝 PROGRAMAÇÃO DO USO DE LLM:")
    print("-" * 40)
    print("1. ANONIMIZAÇÃO (Local):")
    print("   - Usa spaCy (NER) + Regex para remover dados óbvios.")
    print("   - NOVO: Chama Ollama (qwen3:1.7b) localmente para 'auditoria residual' antes de sair.")
    print("2. LLM GATEWAY (Nuvem):")
    print("   - Recebe apenas texto [TOKENIZADO].")
    print("   - Roteia para Zhipu (GLM-4 Plus) para Chat/Raciocínio.")
    print("   - Roteia para Gemini 1.5 Flash para OCR/Visão.")
    print("3. REIDRATAÇÃO (Local):")
    print("   - O retorno da IA chega ao médico e o Anonymizer troca os tokens de volta pelos dados reais.")
    print("-" * 40)

if __name__ == "__main__":
    test_llm_pipeline()
