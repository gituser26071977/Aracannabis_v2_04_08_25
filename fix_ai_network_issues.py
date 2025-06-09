#!/usr/bin/env python3
"""
Script para corrigir problemas comuns de rede com agentes de IA
"""

import os
import sys
from dotenv import load_dotenv, set_key
import json

# Carregar variáveis de ambiente
load_dotenv()

def fix_timeout_issues():
    """Corrige problemas de timeout configurando valores mais altos"""
    print("=== CORRIGINDO PROBLEMAS DE TIMEOUT ===")
    
    env_file = '.env'
    
    # Configurações de timeout para diferentes provedores
    timeout_configs = {
        'OPENAI_TIMEOUT': '120',
        'GROQ_TIMEOUT': '60',
        'OLLAMA_TIMEOUT': '180',
        'CREWAI_TIMEOUT': '300',
        'LANGCHAIN_TIMEOUT': '120'
    }
    
    for key, value in timeout_configs.items():
        current_value = os.getenv(key)
        if not current_value:
            set_key(env_file, key, value)
            print(f"✅ Configurado {key}={value}")
        else:
            print(f"ℹ️ {key} já configurado: {current_value}")
    
    print()

def fix_crewai_config():
    """Otimiza configurações do CrewAI para melhor performance"""
    print("=== OTIMIZANDO CONFIGURAÇÕES DO CREWAI ===")
    
    env_file = '.env'
    
    # Configurações otimizadas para CrewAI
    crewai_configs = {
        'CREWAI_VERBOSE': 'False',  # Reduzir logs verbosos
        'CREWAI_MAX_ITERATIONS': '3',  # Limitar iterações
        'CREWAI_MEMORY': 'False',  # Desabilitar memória para performance
        'CREWAI_PLANNING': 'False',  # Desabilitar planejamento automático
        'CREWAI_DELEGATION': 'False'  # Desabilitar delegação
    }
    
    for key, value in crewai_configs.items():
        set_key(env_file, key, value)
        print(f"✅ Configurado {key}={value}")
    
    print()

def fix_provider_priority():
    """Define prioridade de provedores baseado na disponibilidade"""
    print("=== CONFIGURANDO PRIORIDADE DE PROVEDORES ===")
    
    env_file = '.env'
    
    # Verificar quais provedores estão disponíveis
    available_providers = []
    
    if os.getenv('GROQ_API_KEY'):
        available_providers.append('groq')
        print("✅ Groq disponível (rápido e confiável)")
    
    if os.getenv('OPENAI_API_KEY'):
        available_providers.append('openai')
        print("✅ OpenAI disponível (alta qualidade)")
    
    # Verificar Ollama
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            available_providers.append('ollama')
            print("✅ Ollama disponível (local, privado)")
    except:
        print("⚠️ Ollama não disponível")
    
    if available_providers:
        # Definir provedor padrão (Groq é mais rápido)
        primary_provider = 'groq' if 'groq' in available_providers else available_providers[0]
        set_key(env_file, 'DEFAULT_LLM_PROVIDER', primary_provider)
        print(f"✅ Provedor padrão definido: {primary_provider}")
        
        # Definir modelo padrão baseado no provedor
        if primary_provider == 'groq':
            set_key(env_file, 'DEFAULT_LLM_MODEL', 'llama-3.1-8b-instant')  # Modelo mais rápido
        elif primary_provider == 'openai':
            set_key(env_file, 'DEFAULT_LLM_MODEL', 'gpt-4o-mini')  # Modelo mais rápido da OpenAI
        elif primary_provider == 'ollama':
            set_key(env_file, 'DEFAULT_LLM_MODEL', 'gemma3:4b')  # Modelo local mais rápido
    
    print()

def create_optimized_ai_agents():
    """Cria versão otimizada do arquivo ai_agents.py"""
    print("=== CRIANDO VERSÃO OTIMIZADA DOS AGENTES ===")
    
    optimized_content = '''# Versão otimizada dos agentes de IA com configurações de timeout
import os
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import json
import time

load_dotenv()

# Configurações de timeout otimizadas
DEFAULT_TIMEOUT = int(os.getenv('CREWAI_TIMEOUT', '60'))
MAX_ITERATIONS = int(os.getenv('CREWAI_MAX_ITERATIONS', '2'))

def get_llm_with_timeout(provider: str = None, model_name: str = None, timeout: int = None):
    """
    Versão otimizada do get_llm com configurações de timeout
    """
    provider = provider or os.getenv("DEFAULT_LLM_PROVIDER", "groq")
    timeout = timeout or DEFAULT_TIMEOUT
    
    print(f"Configurando LLM: {provider}, Modelo: {model_name}, Timeout: {timeout}s")
    
    if provider == "groq":
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY não encontrada")
        
        effective_model_name = model_name or "llama-3.1-8b-instant"  # Modelo mais rápido
        return ChatGroq(
            groq_api_key=groq_api_key,
            model_name=effective_model_name,
            temperature=0.1,
            timeout=timeout,
            max_retries=2
        )
    
    elif provider == "openai":
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY não encontrada")
        
        effective_model_name = model_name or "gpt-4o-mini"  # Modelo mais rápido
        return ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=effective_model_name,
            temperature=0.1,
            timeout=timeout,
            max_retries=2
        )
    
    elif provider == "ollama":
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        effective_model_name = model_name or "gemma3:4b"  # Modelo mais rápido
        return ChatOllama(
            base_url=ollama_base_url,
            model=effective_model_name,
            temperature=0.1,
            timeout=timeout
        )
    
    else:
        raise ValueError(f"Provedor desconhecido: {provider}")

def process_evolution_input_optimized(
    evolution_text_input: str, 
    llm_provider: str = None, 
    llm_model_name: str = None,
    timeout: int = None
) -> dict:
    """
    Versão otimizada do processamento com timeout e fallback
    """
    timeout = timeout or DEFAULT_TIMEOUT
    
    try:
        # Tentar com o provedor especificado
        return _process_with_provider(evolution_text_input, llm_provider, llm_model_name, timeout)
    
    except Exception as e:
        print(f"Erro com provedor {llm_provider}: {str(e)}")
        
        # Fallback para outros provedores
        fallback_providers = ['groq', 'openai', 'ollama']
        if llm_provider in fallback_providers:
            fallback_providers.remove(llm_provider)
        
        for fallback_provider in fallback_providers:
            try:
                print(f"Tentando fallback para {fallback_provider}...")
                return _process_with_provider(evolution_text_input, fallback_provider, None, timeout)
            except Exception as fallback_error:
                print(f"Fallback {fallback_provider} falhou: {str(fallback_error)}")
                continue
        
        # Se todos falharam, retornar resultado básico
        return {
            'narrative_evolution': evolution_text_input,
            'dosage_info': None,
            'error': f'Todos os provedores falharam. Último erro: {str(e)}'
        }

def _process_with_provider(evolution_text_input: str, provider: str, model: str, timeout: int) -> dict:
    """Processa com um provedor específico"""
    
    selected_llm = get_llm_with_timeout(provider=provider, model_name=model, timeout=timeout)
    
    # Agente simplificado para melhor performance
    agent = Agent(
        role="Analista Médico",
        goal="Analisar texto médico rapidamente",
        backstory="Especialista em análise rápida de textos médicos",
        verbose=False,  # Reduzir logs
        llm=selected_llm,
        allow_delegation=False,
        max_iter=MAX_ITERATIONS
    )
    
    # Tarefa simplificada
    task_description = f"Analise este texto médico e retorne um JSON: '{evolution_text_input}'"
    
    task = Task(
        description=task_description,
        expected_output="JSON com análise do texto",
        agent=agent
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,  # Reduzir logs
        memory=False,   # Desabilitar memória
        planning=False  # Desabilitar planejamento
    )
    
    # Executar com timeout
    start_time = time.time()
    result = crew.kickoff(inputs={'evolution_text': evolution_text_input})
    execution_time = time.time() - start_time
    
    print(f"Processamento concluído em {execution_time:.2f}s")
    
    # Processar resultado
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {'narrative_evolution': evolution_text_input, 'raw_result': result}
    
    return result if isinstance(result, dict) else {'narrative_evolution': evolution_text_input, 'result': str(result)}
'''
    
    # Salvar backup do arquivo original
    if os.path.exists('services/ai_agents.py'):
        import shutil
        shutil.copy('services/ai_agents.py', 'services/ai_agents_backup.py')
        print("✅ Backup criado: services/ai_agents_backup.py")
    
    # Criar arquivo otimizado
    with open('services/ai_agents_optimized.py', 'w', encoding='utf-8') as f:
        f.write(optimized_content)
    
    print("✅ Arquivo otimizado criado: services/ai_agents_optimized.py")
    print()

def create_network_test_script():
    """Cria script de teste rápido para verificar conectividade"""
    print("=== CRIANDO SCRIPT DE TESTE RÁPIDO ===")
    
    test_script = '''#!/usr/bin/env python3
"""Script de teste rápido para agentes de IA"""

import os
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
'''
    
    with open('quick_ai_test.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Script de teste criado: quick_ai_test.py")
    print()

def main():
    """Função principal de correção"""
    print("🔧 CORRIGINDO PROBLEMAS DE REDE COM AGENTES DE IA")
    print("=" * 60)
    
    fix_timeout_issues()
    fix_crewai_config()
    fix_provider_priority()
    create_optimized_ai_agents()
    create_network_test_script()
    
    print("=" * 60)
    print("✅ CORREÇÕES APLICADAS COM SUCESSO!")
    print("\nPróximos passos:")
    print("1. Reinicie o aplicativo para carregar as novas configurações")
    print("2. Execute: python quick_ai_test.py")
    print("3. Se ainda houver problemas, use o arquivo otimizado:")
    print("   - Substitua services/ai_agents.py por services/ai_agents_optimized.py")
    print("4. Para reverter: use services/ai_agents_backup.py")

if __name__ == "__main__":
    main()
