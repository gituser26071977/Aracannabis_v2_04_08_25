#!/usr/bin/env python3
"""
Script para aplicar correção direta nos arquivos que causam network error
"""

import os
import shutil
from datetime import datetime

def backup_and_fix_evolucoes():
    """Aplica correção direta na rota de evoluções"""
    print("=== CORRIGINDO ROTA DE EVOLUÇÕES ===")
    
    # Backup
    if os.path.exists('routes/evolucoes.py'):
        backup_path = f'routes/evolucoes_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
        shutil.copy('routes/evolucoes.py', backup_path)
        print(f"✅ Backup criado: {backup_path}")
    
    # Aplicar correção na função safe_ai_processing
    with open('routes/evolucoes.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar função de processamento seguro no início do arquivo
    safe_ai_function = '''
def safe_ai_processing(text_input, llm_provider=None, llm_model_name=None, timeout=30):
    """Processamento seguro com IA incluindo fallback e timeout"""
    try:
        current_app.logger.info(f"SAFE_AI: Iniciando processamento com timeout {timeout}s")
        
        # Tentar usar versão otimizada primeiro
        try:
            from services.ai_agents_optimized import process_evolution_input_optimized
            result = process_evolution_input_optimized(
                evolution_text_input=text_input,
                llm_provider=llm_provider or 'groq',
                llm_model_name=llm_model_name,
                timeout=timeout
            )
            current_app.logger.info(f"SAFE_AI: Processamento otimizado concluído")
            return result
        except ImportError:
            current_app.logger.warning(f"SAFE_AI: Versão otimizada não encontrada, usando original")
            pass
        
        # Fallback para versão original com timeout reduzido
        from services.ai_agents import process_evolution_input
        result = process_evolution_input(
            evolution_text_input=text_input,
            llm_provider=llm_provider or 'groq',
            llm_model_name=llm_model_name or 'llama-3.1-8b-instant'
        )
        current_app.logger.info(f"SAFE_AI: Processamento original concluído")
        return result
        
    except Exception as e:
        current_app.logger.error(f"SAFE_AI: Erro no processamento: {str(e)}")
        return {
            'narrative_evolution': text_input,
            'dosage_info': None,
            'error': f'IA temporariamente indisponível: {str(e)}'
        }

'''
    
    # Inserir a função após os imports
    import_end = content.find('evolucoes_bp = Blueprint')
    if import_end != -1:
        content = content[:import_end] + safe_ai_function + content[import_end:]
    
    # Substituir chamadas diretas para process_evolution_input por safe_ai_processing
    content = content.replace(
        'ai_analysis_result = process_evolution_input(',
        'ai_analysis_result = safe_ai_processing('
    )
    
    content = content.replace(
        'ai_result = process_evolution_input(',
        'ai_result = safe_ai_processing('
    )
    
    # Adicionar timeout configurável
    content = content.replace(
        "use_ai_processing = data.get('use_ai_processing', False)",
        """use_ai_processing = data.get('use_ai_processing', False)
        ai_timeout = int(data.get('ai_timeout', 30))  # Timeout configurável"""
    )
    
    # Adicionar timeout na chamada
    content = content.replace(
        '''ai_analysis_result = safe_ai_processing(
                text_input=input_text,
                llm_provider=llm_provider,
                llm_model_name=llm_model_name''',
        '''ai_analysis_result = safe_ai_processing(
                text_input=input_text,
                llm_provider=llm_provider,
                llm_model_name=llm_model_name,
                timeout=ai_timeout'''
    )
    
    # Salvar arquivo corrigido
    with open('routes/evolucoes.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Rota de evoluções corrigida")

def backup_and_fix_import_export():
    """Aplica correção direta na rota de import/export"""
    print("=== CORRIGINDO ROTA DE IMPORT/EXPORT ===")
    
    # Backup
    if os.path.exists('routes/import_export.py'):
        backup_path = f'routes/import_export_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.py'
        shutil.copy('routes/import_export.py', backup_path)
        print(f"✅ Backup criado: {backup_path}")
    
    with open('routes/import_export.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adicionar função de processamento seguro
    safe_import_function = '''
def safe_ai_import_processing(text_content, patient_id, timeout=30):
    """Processamento seguro de importação com IA"""
    try:
        # Tentar usar versão otimizada primeiro
        try:
            from services.ai_agents_optimized import process_evolution_input_optimized
            result = process_evolution_input_optimized(
                evolution_text_input=text_content,
                timeout=timeout
            )
            # Converter para formato de importação
            return {
                'tipo': 'evolucao',
                'data': None,
                'evolucoes': [{'descricao': result.get('narrative_evolution', text_content), 'observacoes': ''}],
                'dosagens': [],
                'sintomas': [],
                'confianca': 80,
                'ai_processed': True
            }
        except ImportError:
            pass
            
        # Fallback para versão original
        from services.ai_agents import process_import_data
        return process_import_data(text_content, patient_id)
        
    except Exception as e:
        return {
            'tipo': 'evolucao',
            'data': None,
            'evolucoes': [{'descricao': text_content, 'observacoes': ''}],
            'dosagens': [],
            'sintomas': [],
            'confianca': 0,
            'error': f'IA indisponível: {str(e)}'
        }

'''
    
    # Inserir função após imports
    import_end = content.find('import_export_bp = Blueprint')
    if import_end != -1:
        content = content[:import_end] + safe_import_function + content[import_end:]
    
    # Substituir chamadas diretas
    content = content.replace(
        'ai_result = process_import_data(',
        'ai_result = safe_ai_import_processing('
    )
    
    content = content.replace(
        'from services.ai_agents import chat_with_data',
        '''try:
            from services.ai_agents import chat_with_data
        except ImportError:
            def chat_with_data(question, context):
                return {
                    'resposta': 'IA temporariamente indisponível. Tente novamente mais tarde.',
                    'dados_citados': [],
                    'insights': [],
                    'sugestoes': [],
                    'error': 'Módulo de IA não disponível'
                }'''
    )
    
    # Salvar arquivo corrigido
    with open('routes/import_export.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Rota de import/export corrigida")

def create_network_error_middleware():
    """Cria middleware para capturar e tratar network errors"""
    print("=== CRIANDO MIDDLEWARE DE NETWORK ERROR ===")
    
    middleware_content = '''"""
Middleware para tratar network errors relacionados à IA
"""

from functools import wraps
from flask import jsonify, current_app
import traceback

def handle_ai_network_errors(f):
    """Decorator para tratar erros de rede da IA"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()
            
            # Detectar erros de rede específicos
            network_errors = [
                'network error', 'connection error', 'timeout', 
                'connection refused', 'network is unreachable',
                'name resolution failed', 'ssl error', 'certificate',
                'read timeout', 'connection timeout', 'socket timeout'
            ]
            
            is_network_error = any(err in error_msg for err in network_errors)
            
            if is_network_error:
                current_app.logger.warning(f"Network error detectado: {str(e)}")
                return jsonify({
                    'error': 'Serviço de IA temporariamente indisponível',
                    'message': 'Tente novamente em alguns momentos',
                    'fallback_available': True,
                    'technical_error': str(e) if current_app.debug else None
                }), 503  # Service Unavailable
            else:
                # Re-raise outros erros
                raise e
    
    return decorated_function

def safe_ai_call(ai_function, *args, **kwargs):
    """Executa chamada de IA de forma segura com fallback"""
    try:
        return ai_function(*args, **kwargs)
    except Exception as e:
        current_app.logger.error(f"Erro na chamada de IA: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        # Retornar resultado de fallback
        if 'evolution_text_input' in kwargs:
            text_input = kwargs['evolution_text_input']
        elif len(args) > 0:
            text_input = args[0]
        else:
            text_input = "Texto não disponível"
        
        return {
            'narrative_evolution': text_input,
            'dosage_info': None,
            'error': f'IA indisponível: {str(e)}',
            'fallback_used': True
        }
'''
    
    with open('ai_network_middleware.py', 'w', encoding='utf-8') as f:
        f.write(middleware_content)
    
    print("✅ Middleware criado: ai_network_middleware.py")

def update_env_with_network_settings():
    """Atualiza .env com configurações de rede otimizadas"""
    print("=== ATUALIZANDO CONFIGURAÇÕES DE REDE ===")
    
    network_settings = {
        'AI_NETWORK_TIMEOUT': '30',
        'AI_RETRY_ATTEMPTS': '2',
        'AI_FALLBACK_ENABLED': 'True',
        'AI_GRACEFUL_DEGRADATION': 'True',
        'REQUESTS_TIMEOUT': '30',
        'URLLIB3_DISABLE_WARNINGS': 'True'
    }
    
    # Ler .env atual
    env_content = ""
    if os.path.exists('.env'):
        with open('.env', 'r', encoding='utf-8') as f:
            env_content = f.read()
    
    # Adicionar configurações se não existirem
    for key, value in network_settings.items():
        if key not in env_content:
            env_content += f"\n{key}={value}"
            print(f"✅ Adicionado: {key}={value}")
    
    # Salvar .env atualizado
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Configurações de rede atualizadas")

def create_ai_health_check():
    """Cria endpoint de health check para IA"""
    print("=== CRIANDO HEALTH CHECK DE IA ===")
    
    health_check_content = '''"""
Health check para serviços de IA
"""

from flask import Blueprint, jsonify
import os
import requests
from datetime import datetime

ai_health_bp = Blueprint('ai_health', __name__)

@ai_health_bp.route('/health/ai', methods=['GET'])
def check_ai_health():
    """Verifica status dos serviços de IA"""
    
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'overall_status': 'healthy',
        'services': {}
    }
    
    # Verificar Groq
    if os.getenv('GROQ_API_KEY'):
        try:
            response = requests.get(
                'https://api.groq.com/openai/v1/models',
                headers={'Authorization': f'Bearer {os.getenv("GROQ_API_KEY")}'},
                timeout=10
            )
            health_status['services']['groq'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            health_status['services']['groq'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    # Verificar OpenAI
    if os.getenv('OPENAI_API_KEY'):
        try:
            response = requests.get(
                'https://api.openai.com/v1/models',
                headers={'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}'},
                timeout=10
            )
            health_status['services']['openai'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code
            }
        except Exception as e:
            health_status['services']['openai'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    # Verificar Ollama
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        health_status['services']['ollama'] = {
            'status': 'healthy' if response.status_code == 200 else 'unhealthy',
            'response_time': response.elapsed.total_seconds(),
            'status_code': response.status_code
        }
    except Exception as e:
        health_status['services']['ollama'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Determinar status geral
    unhealthy_services = [s for s in health_status['services'].values() if s['status'] == 'unhealthy']
    if len(unhealthy_services) == len(health_status['services']):
        health_status['overall_status'] = 'critical'
    elif unhealthy_services:
        health_status['overall_status'] = 'degraded'
    
    status_code = 200
    if health_status['overall_status'] == 'critical':
        status_code = 503
    elif health_status['overall_status'] == 'degraded':
        status_code = 206
    
    return jsonify(health_status), status_code
'''
    
    with open('routes/ai_health.py', 'w', encoding='utf-8') as f:
        f.write(health_check_content)
    
    print("✅ Health check criado: routes/ai_health.py")

def main():
    """Executa todas as correções"""
    print("🔧 APLICANDO CORREÇÕES PARA NETWORK ERROR DE IA")
    print("=" * 60)
    
    backup_and_fix_evolucoes()
    backup_and_fix_import_export()
    create_network_error_middleware()
    update_env_with_network_settings()
    create_ai_health_check()
    
    print("=" * 60)
    print("✅ TODAS AS CORREÇÕES APLICADAS!")
    print("\nPróximos passos:")
    print("1. Reinicie o aplicativo Flask")
    print("2. Teste as funcionalidades de IA")
    print("3. Verifique o health check em: /health/ai")
    print("4. Se ainda houver problemas, use: python quick_ai_test.py")
    print("\nOs arquivos originais foram salvos como backup.")

if __name__ == "__main__":
    main()
