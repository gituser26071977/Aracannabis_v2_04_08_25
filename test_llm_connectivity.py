
import os
import sys
import logging
from datetime import datetime

# Adicionar o diretório atual ao path para importar services
sys.path.append(os.getcwd())

# Configurar logging para ser minimalista
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("test_llm")


try:
    from services.ai_agents import ai_manager, OPENAI_AVAILABLE, GROQ_AVAILABLE, ANTHROPIC_AVAILABLE, GOOGLE_AVAILABLE, OLLAMA_AVAILABLE
    from services.ai_config_storage import load_config
    print(f"📦 Disponibilidade de Pacotes:")
    print(f"   - OpenAI: {OPENAI_AVAILABLE}")
    print(f"   - Groq: {GROQ_AVAILABLE}")
    print(f"   - Anthropic: {ANTHROPIC_AVAILABLE}")
    print(f"   - Google: {GOOGLE_AVAILABLE}")
    print(f"   - Ollama: {OLLAMA_AVAILABLE}")
except ImportError as e:
    print(f"❌ Erro ao importar serviços: {e}")
    sys.exit(1)


def test_provider(provider, model):
    print(f"🔍 Testando {provider} (modelo: {model})... ", end="", flush=True)
    try:
        messages = [{"role": "user", "content": "Diga 'Conectado' se você estiver funcionando."}]
        start_time = datetime.now()
        response = ai_manager.chat_completion(
            messages=messages,
            provider=provider,
            model=model,
            temperature=0.1,
            max_tokens=10
        )
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.get('error'):
            print(f"❌ FALHOU: {response.get('error')}")
            return False
        
        content = response.get('content', '').strip()
        print(f"✅ SUCESSO ({duration:.2f}s) -> '{content}'")
        return True
    except Exception as e:
        print(f"❌ ERRO: {str(e)}")
        return False

def main():
    print("════════════════════════════════════════════════════════════")
    print("  🤖 VERIFICAÇÃO DE CONECTIVIDADE LLM PARA LANÇAMENTO V1")
    print("════════════════════════════════════════════════════════════")
    print("")
    
    config = load_config()
    default_provider = config.get('default_provider', 'zhipu')
    default_model = config.get('chat_model', 'glm-4-plus')
    
    print(f"Padrão configurado: {default_provider} / {default_model}")
    print(f"Provedores inicializados no ai_manager: {ai_manager.get_available_providers()}")
    print("-" * 60)

    
    # Lista de provedores para testar
    # 0. Maritaca (Novo Padrão)
    test_provider('maritaca', 'sabiazinho-4')
    
    # 1. Zhipu (Principal)
    test_provider('zhipu', 'glm-4-plus')
    
    # 2. DeepSeek (Alternativa)
    test_provider('deepseek', 'deepseek-chat')
    
    # 3. Google (Visão/Fallback)
    test_provider('google', 'gemini-1.5-flash')
    
    # 4. Ollama (Local/Fallback Crítico)
    # Primeiro checar se Ollama está rodando na porta padrão
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", 11434))
        print("✅ Ollama Local Service: Rodando na porta 11434")
        test_provider('ollama_local', 'gemma3:4b')
    except:
        print("❌ Ollama Local Service: NÃO ENCONTRADO na porta 11434")
    finally:
        s.close()
        
    print("")
    print("════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()
