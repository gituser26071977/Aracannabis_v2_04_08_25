#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de rede com agentes de IA
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv
import traceback

# Carregar variáveis de ambiente
load_dotenv()

def test_network_connectivity():
    """Testa conectividade básica de rede"""
    print("=== TESTE DE CONECTIVIDADE DE REDE ===")
    
    # URLs para testar
    test_urls = [
        "https://www.google.com",
        "https://api.openai.com",
        "https://api.groq.com",
        "https://api.anthropic.com",
        "https://generativelanguage.googleapis.com",
        "http://localhost:11434"  # Ollama local
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=10)
            print(f"✅ {url}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url}: Erro de conexão")
        except requests.exceptions.Timeout:
            print(f"⏰ {url}: Timeout")
        except Exception as e:
            print(f"❌ {url}: {str(e)}")
    print()

def test_api_keys():
    """Testa se as API keys estão configuradas"""
    print("=== TESTE DE API KEYS ===")
    
    api_keys = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'XAI_API_KEY': os.getenv('XAI_API_KEY')
    }
    
    for key_name, key_value in api_keys.items():
        if key_value:
            # Mascarar a chave para segurança
            masked_key = key_value[:8] + "..." + key_value[-4:] if len(key_value) > 12 else "***"
            print(f"✅ {key_name}: {masked_key}")
        else:
            print(f"❌ {key_name}: Não configurada")
    print()

def test_openai_api():
    """Testa especificamente a API da OpenAI"""
    print("=== TESTE DA API OPENAI ===")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY não configurada")
        return
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Teste simples de listagem de modelos
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ OpenAI API: Conectada com sucesso")
            models = response.json()
            print(f"   Modelos disponíveis: {len(models.get('data', []))}")
        else:
            print(f"❌ OpenAI API: Erro {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ OpenAI API: Erro de conexão - {str(e)}")
    print()

def test_groq_api():
    """Testa especificamente a API do Groq"""
    print("=== TESTE DA API GROQ ===")
    
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        print("❌ GROQ_API_KEY não configurada")
        return
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Teste simples de listagem de modelos
        response = requests.get(
            'https://api.groq.com/openai/v1/models',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Groq API: Conectada com sucesso")
            models = response.json()
            print(f"   Modelos disponíveis: {len(models.get('data', []))}")
        else:
            print(f"❌ Groq API: Erro {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Groq API: Erro de conexão - {str(e)}")
    print()

def test_ollama_local():
    """Testa se o Ollama está rodando localmente"""
    print("=== TESTE DO OLLAMA LOCAL ===")
    
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    try:
        # Testar se o Ollama está rodando
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        
        if response.status_code == 200:
            print("✅ Ollama: Rodando localmente")
            models = response.json()
            if 'models' in models:
                print(f"   Modelos instalados: {len(models['models'])}")
                for model in models['models'][:5]:  # Mostrar apenas os primeiros 5
                    print(f"   - {model['name']}")
            else:
                print("   Nenhum modelo instalado")
        else:
            print(f"❌ Ollama: Erro {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Ollama: Não está rodando ou não acessível")
        print("   Para instalar: curl -fsSL https://ollama.ai/install.sh | sh")
        print("   Para iniciar: ollama serve")
    except Exception as e:
        print(f"❌ Ollama: Erro - {str(e)}")
    print()

def test_ai_agents_import():
    """Testa se os módulos de IA podem ser importados"""
    print("=== TESTE DE IMPORTAÇÃO DOS MÓDULOS ===")
    
    try:
        from services.ai_agents import get_llm, process_evolution_input
        print("✅ services.ai_agents: Importado com sucesso")
    except ImportError as e:
        print(f"❌ services.ai_agents: Erro de importação - {str(e)}")
    except Exception as e:
        print(f"❌ services.ai_agents: Erro - {str(e)}")
    
    try:
        from crewai import Agent, Task, Crew
        print("✅ crewai: Importado com sucesso")
    except ImportError as e:
        print(f"❌ crewai: Erro de importação - {str(e)}")
        print("   Para instalar: pip install crewai")
    except Exception as e:
        print(f"❌ crewai: Erro - {str(e)}")
    
    try:
        from langchain_openai import ChatOpenAI
        print("✅ langchain_openai: Importado com sucesso")
    except ImportError as e:
        print(f"❌ langchain_openai: Erro de importação - {str(e)}")
        print("   Para instalar: pip install langchain-openai")
    except Exception as e:
        print(f"❌ langchain_openai: Erro - {str(e)}")
    
    try:
        from langchain_groq import ChatGroq
        print("✅ langchain_groq: Importado com sucesso")
    except ImportError as e:
        print(f"❌ langchain_groq: Erro de importação - {str(e)}")
        print("   Para instalar: pip install langchain-groq")
    except Exception as e:
        print(f"❌ langchain_groq: Erro - {str(e)}")
    
    try:
        from langchain_ollama import ChatOllama
        print("✅ langchain_ollama: Importado com sucesso")
    except ImportError as e:
        print(f"❌ langchain_ollama: Erro de importação - {str(e)}")
        print("   Para instalar: pip install langchain-ollama")
    except Exception as e:
        print(f"❌ langchain_ollama: Erro - {str(e)}")
    print()

def test_llm_creation():
    """Testa a criação de instâncias LLM"""
    print("=== TESTE DE CRIAÇÃO DE LLM ===")
    
    try:
        from services.ai_agents import get_llm
        
        # Testar diferentes provedores
        providers_to_test = []
        
        # Adicionar provedores baseado nas API keys disponíveis
        if os.getenv('OPENAI_API_KEY'):
            providers_to_test.append(('openai', 'gpt-4o-mini'))
        
        if os.getenv('GROQ_API_KEY'):
            providers_to_test.append(('groq', 'llama-3.1-8b-instant'))
        
        # Sempre testar Ollama (não precisa de API key)
        providers_to_test.append(('ollama', 'gemma3:4b'))
        
        for provider, model in providers_to_test:
            try:
                print(f"Testando {provider} com modelo {model}...")
                llm = get_llm(provider=provider, model_name=model)
                print(f"✅ {provider}: LLM criado com sucesso")
                
                # Teste simples de invocação
                try:
                    response = llm.invoke("Responda apenas 'OK'")
                    print(f"   Resposta: {str(response)[:100]}...")
                except Exception as invoke_error:
                    print(f"   ⚠️ Erro na invocação: {str(invoke_error)}")
                    
            except Exception as e:
                print(f"❌ {provider}: Erro - {str(e)}")
                
    except Exception as e:
        print(f"❌ Erro geral na criação de LLM: {str(e)}")
    print()

def test_simple_ai_processing():
    """Testa processamento simples com IA"""
    print("=== TESTE DE PROCESSAMENTO SIMPLES ===")
    
    try:
        from services.ai_agents import process_evolution_input
        
        # Texto simples para teste
        test_text = "Paciente relatou melhora nos sintomas após uso de 2 gotas de CBD."
        
        print(f"Testando com texto: '{test_text}'")
        
        # Tentar com diferentes provedores
        providers_to_test = []
        
        if os.getenv('GROQ_API_KEY'):
            providers_to_test.append('groq')
        
        if os.getenv('OPENAI_API_KEY'):
            providers_to_test.append('openai')
        
        providers_to_test.append('ollama')  # Sempre tentar Ollama
        
        for provider in providers_to_test:
            try:
                print(f"\nTestando processamento com {provider}...")
                result = process_evolution_input(
                    evolution_text_input=test_text,
                    llm_provider=provider
                )
                print(f"✅ {provider}: Processamento concluído")
                print(f"   Resultado: {json.dumps(result, indent=2, ensure_ascii=False)}")
                break  # Se um funcionar, parar aqui
                
            except Exception as e:
                print(f"❌ {provider}: Erro no processamento - {str(e)}")
                print(f"   Traceback: {traceback.format_exc()}")
                
    except Exception as e:
        print(f"❌ Erro geral no processamento: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
    print()

def main():
    """Função principal do diagnóstico"""
    print("🔍 DIAGNÓSTICO DE PROBLEMAS DE REDE COM AGENTES DE IA")
    print("=" * 60)
    
    # Executar todos os testes
    test_network_connectivity()
    test_api_keys()
    test_openai_api()
    test_groq_api()
    test_ollama_local()
    test_ai_agents_import()
    test_llm_creation()
    test_simple_ai_processing()
    
    print("=" * 60)
    print("🏁 DIAGNÓSTICO CONCLUÍDO")
    print("\nSe você encontrou erros:")
    print("1. Verifique sua conexão com a internet")
    print("2. Confirme se as API keys estão corretas no arquivo .env")
    print("3. Instale dependências faltantes com: pip install -r requirements.txt")
    print("4. Para Ollama local: ollama serve && ollama pull gemma3:4b")

if __name__ == "__main__":
    main()
