from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from security_config import csrf_protect, sanitize_input
import json
import os
from dotenv import load_dotenv, set_key

ai_config_bp = Blueprint('ai_config', __name__)

# Configurações padrão dos provedores de IA - ATUALIZADAS COM DOCUMENTAÇÃO OFICIAL
AI_PROVIDERS = {
    'openai': {
        'name': 'OpenAI',
        'models': [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo',
            'o1-preview',
            'o1-mini',
            'gpt-4o-2024-11-20',
            'gpt-4o-mini-2024-07-18',
            'gpt-4-turbo-2024-04-09',
            'gpt-4-0613',
            'gpt-3.5-turbo-0125'
        ],
        'default_model': 'gpt-4o',
        'base_url': 'https://api.openai.com/v1',
        'requires_api_key': True,
        'description': 'OpenAI GPT models - Estado da arte em IA conversacional. Inclui modelos o1 para raciocínio avançado.'
    },
    'anthropic': {
        'name': 'Anthropic Claude',
        'models': [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
            'claude-3-5-sonnet-20240620'
        ],
        'default_model': 'claude-3-5-sonnet-20241022',
        'base_url': 'https://api.anthropic.com',
        'requires_api_key': True,
        'description': 'Claude 3.5 - Excelente para análise médica e raciocínio complexo. Sonnet oferece o melhor equilíbrio.'
    },
    'google': {
        'name': 'Google Gemini',
        'models': [
            'gemini-2.0-flash-exp',
            'gemini-1.5-pro',
            'gemini-1.5-pro-002',
            'gemini-1.5-flash',
            'gemini-1.5-flash-002',
            'gemini-1.5-flash-8b',
            'gemini-1.0-pro',
            'gemini-pro',
            'gemini-pro-vision'
        ],
        'default_model': 'gemini-1.5-pro',
        'base_url': 'https://generativelanguage.googleapis.com/v1beta',
        'requires_api_key': True,
        'description': 'Google Gemini - Multimodal e rápido. Flash para velocidade, Pro para qualidade.'
    },
    'groq': {
        'name': 'Groq',
        'models': [
            'llama-3.1-70b-versatile',
            'llama-3.1-8b-instant',
            'llama-3.2-1b-preview',
            'llama-3.2-3b-preview',
            'llama-3.2-11b-text-preview',
            'llama-3.2-90b-text-preview',
            'mixtral-8x7b-32768',
            'gemma-7b-it',
            'gemma2-9b-it'
        ],
        'default_model': 'llama-3.1-70b-versatile',
        'base_url': 'https://api.groq.com/openai/v1',
        'requires_api_key': True,
        'description': 'Groq - Inferência ultra-rápida com modelos open source. Llama 3.2 90B para máxima qualidade.'
    },
    'xai': {
        'name': 'xAI Grok',
        'models': [
            'grok-beta',
            'grok-vision-beta'
        ],
        'default_model': 'grok-beta',
        'base_url': 'https://api.x.ai/v1',
        'requires_api_key': True,
        'description': 'Grok - IA da xAI com acesso a dados em tempo real e personalidade única.'
    },
    'ollama': {
        'name': 'Ollama (Local)',
        'models': [
            'mistral-small3.1:24b',
            'llava:13b',
            'qwen3:14b',
            'qwen3:4b',
            'qwen3:1.7b',
            'qwen3:0.6b',
            'gemma3:12b',
            'gemma3:4b',
            'gemma3:1b',
            'deepseek-r1:latest',
            'deepseek-r1:14b',
            'deepseek-r1:8b',
            'llama3:8b-instruct-q4_1'
        ],
        'default_model': 'mistral-small3.1:24b',
        'base_url': 'http://localhost:11434',
        'requires_api_key': False,
        'description': 'Ollama - Modelos locais instalados (15GB total) para máxima privacidade. Seus modelos personalizados.'
    }
}

@ai_config_bp.route('/providers', methods=['GET'])
@jwt_required()
def get_ai_providers():
    """Retorna lista de provedores de IA disponíveis"""
    try:
        return jsonify({
            'providers': AI_PROVIDERS,
            'current_config': get_current_ai_config()
        })
    except Exception as e:
        return jsonify({'error': f'Erro ao obter provedores: {str(e)}'}), 500

@ai_config_bp.route('/config', methods=['GET'])
@jwt_required()
def get_ai_config():
    """Retorna configuração atual de IA"""
    try:
        config = get_current_ai_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': f'Erro ao obter configuração: {str(e)}'}), 500

@ai_config_bp.route('/config', methods=['POST'])
@jwt_required()
@csrf_protect
def update_ai_config():
    """Atualiza configuração de IA"""
    try:
        data = request.get_json()
        data = sanitize_input(data)
        
        # Validar dados obrigatórios
        required_fields = ['provider', 'model']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        provider = data['provider']
        model = data['model']
        api_key = data.get('api_key', '')
        base_url = data.get('base_url', '')
        
        # Validar provedor
        if provider not in AI_PROVIDERS:
            return jsonify({'error': 'Provedor de IA inválido'}), 400
        
        # Para modelos customizados, não validar se está na lista
        # Validar modelo apenas se não for customizado
        if model not in AI_PROVIDERS[provider]['models']:
            # Permitir modelos customizados - não retornar erro
            print(f"Modelo customizado detectado: {model} para provedor {provider}")
        
        # Validar API key se necessária
        if AI_PROVIDERS[provider]['requires_api_key'] and not api_key:
            return jsonify({'error': 'API key é obrigatória para este provedor'}), 400
        
        # Usar base_url padrão se não fornecida
        if not base_url:
            base_url = AI_PROVIDERS[provider]['base_url']
        
        # Atualizar variáveis de ambiente
        env_file = '.env'
        
        # Configurações principais
        set_key(env_file, 'DEFAULT_LLM_PROVIDER', provider)
        set_key(env_file, 'DEFAULT_LLM_MODEL', model)
        set_key(env_file, 'DEFAULT_LLM_BASE_URL', base_url)
        
        # API Keys específicas por provedor
        if provider == 'openai' and api_key:
            set_key(env_file, 'OPENAI_API_KEY', api_key)
        elif provider == 'anthropic' and api_key:
            set_key(env_file, 'ANTHROPIC_API_KEY', api_key)
        elif provider == 'google' and api_key:
            set_key(env_file, 'GOOGLE_API_KEY', api_key)
        elif provider == 'groq' and api_key:
            set_key(env_file, 'GROQ_API_KEY', api_key)
        elif provider == 'xai' and api_key:
            set_key(env_file, 'XAI_API_KEY', api_key)
        
        # Recarregar variáveis de ambiente
        load_dotenv(override=True)
        
        return jsonify({
            'message': 'Configuração de IA atualizada com sucesso',
            'config': {
                'provider': provider,
                'model': model,
                'base_url': base_url,
                'has_api_key': bool(api_key)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao atualizar configuração: {str(e)}'}), 500

@ai_config_bp.route('/test', methods=['POST'])
@jwt_required()
@csrf_protect
def test_ai_config():
    """Testa a configuração de IA atual"""
    try:
        data = request.get_json()
        provider = data.get('provider')
        model = data.get('model')
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        
        # Importar e testar a configuração
        from services.ai_agents import test_llm_connection
        
        result = test_llm_connection(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao testar configuração: {str(e)}'
        }), 500

@ai_config_bp.route('/models/<provider>', methods=['GET'])
@jwt_required()
def get_provider_models(provider):
    """Retorna modelos disponíveis para um provedor específico"""
    try:
        if provider not in AI_PROVIDERS:
            return jsonify({'error': 'Provedor não encontrado'}), 404
        
        return jsonify({
            'provider': provider,
            'models': AI_PROVIDERS[provider]['models'],
            'default_model': AI_PROVIDERS[provider]['default_model'],
            'base_url': AI_PROVIDERS[provider]['base_url'],
            'requires_api_key': AI_PROVIDERS[provider]['requires_api_key']
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter modelos: {str(e)}'}), 500

def get_current_ai_config():
    """Obtém configuração atual de IA das variáveis de ambiente"""
    return {
        'provider': os.getenv('DEFAULT_LLM_PROVIDER', 'groq'),
        'model': os.getenv('DEFAULT_LLM_MODEL', 'llama-3.1-70b-versatile'),
        'base_url': os.getenv('DEFAULT_LLM_BASE_URL', 'https://api.groq.com/openai/v1'),
        'has_openai_key': bool(os.getenv('OPENAI_API_KEY')),
        'has_anthropic_key': bool(os.getenv('ANTHROPIC_API_KEY')),
        'has_google_key': bool(os.getenv('GOOGLE_API_KEY')),
        'has_groq_key': bool(os.getenv('GROQ_API_KEY')),
        'has_xai_key': bool(os.getenv('XAI_API_KEY'))
    }
