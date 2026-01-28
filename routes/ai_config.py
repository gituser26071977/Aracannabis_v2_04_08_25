"""
Rotas de configuração de IA para o Aracannabis
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import json
from services.ai_agents import ai_manager

ai_config_bp = Blueprint('ai_config', __name__)

def _is_provider_configured(provider_name):
    """Verifica se um provedor está configurado com variáveis de ambiente"""
    if provider_name == 'openai':
        return bool(os.getenv('OPENAI_API_KEY'))
    elif provider_name == 'groq':
        return bool(os.getenv('GROQ_API_KEY'))
    elif provider_name == 'anthropic':
        return bool(os.getenv('ANTHROPIC_API_KEY'))
    elif provider_name == 'google':
        return bool(os.getenv('GOOGLE_API_KEY'))
    elif provider_name == 'deepseek':
        return bool(os.getenv('DEEPSEEK_API_KEY'))
    elif provider_name in ['ollama_local', 'ollama_cloud']:
        # Ollama não precisa de chave de API, apenas verifica se a variável de URL está configurada
        ollama_url = os.getenv('OLLAMA_BASE_URL') or os.getenv('OLLAMA_CLOUD_URL')
        return bool(ollama_url)
    elif provider_name == 'xai':
        # xAI Grok API ainda não está publicamente disponível
        return bool(os.getenv('XAI_API_KEY'))
    return False

@ai_config_bp.route('/providers', methods=['GET'])
@jwt_required()
def get_ai_providers():
    """Retorna lista de provedores de IA disponíveis e configurados"""
    try:
        available_providers = ai_manager.get_available_providers()
        
        providers_info = {}
        # Lista de todos os provedores suportados
        supported_providers = ['groq', 'openai', 'anthropic', 'google', 'ollama_local', 'ollama_cloud', 'deepseek', 'xai']
        for provider in supported_providers:
            if provider in ai_manager.providers:
                providers_info[provider] = {
                    'available': provider in available_providers,
                    'models': ai_manager.providers[provider]['models'],
                    'type': ai_manager.providers[provider].get('type', 'cloud'),
                    'configured': _is_provider_configured(provider)
                }
        
        return jsonify({
            'providers': providers_info,
            'default_provider': ai_manager.default_provider,
            'default_model': ai_manager.default_model,
            'default_vision_provider': ai_manager.default_vision_provider,
            'default_vision_model': ai_manager.default_vision_model,
            'default_multimodal_provider': ai_manager.default_multimodal_provider,
            'default_multimodal_model': ai_manager.default_multimodal_model,
            'available_providers': available_providers
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter provedores: {str(e)}'}), 500

@ai_config_bp.route('/providers/<provider_name>', methods=['POST'])
@jwt_required()
def set_ai_provider(provider_name):
    """Define o provedor de IA padrão"""
    try:
        data = request.get_json()
        model = data.get('model')
        
        supported_providers = ['groq', 'openai', 'anthropic', 'google', 'ollama_local', 'ollama_cloud', 'deepseek', 'xai']
        if provider_name not in supported_providers:
            return jsonify({'error': 'Provedor não suportado'}), 400
        
        # Verificar se o provedor está disponível
        available_providers = ai_manager.get_available_providers()
        if provider_name not in available_providers:
            return jsonify({'error': f'Provedor {provider_name} não disponível. Verifique a chave de API.'}), 400
        
        # Verificar se o modelo é válido
        if model and model not in ai_manager.providers[provider_name]['models']:
            return jsonify({'error': f'Modelo {model} não é válido para o provedor {provider_name}'}), 400
        
        # Atualizar configurações
        ai_manager.default_provider = provider_name
        if model:
            ai_manager.default_model = model
        
        return jsonify({
            'message': f'Provedor padrão alterado para {provider_name}',
            'provider': provider_name,
            'model': model or ai_manager.default_model
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao alterar provedor: {str(e)}'}), 500

@ai_config_bp.route('/test', methods=['POST'])
@jwt_required()
def test_ai_connection():
    """Testa a conexão com os provedores de IA"""
    try:
        data = request.get_json()
        provider = data.get('provider', ai_manager.default_provider)
        model = data.get('model', ai_manager.default_model)
        
        test_messages = [
            {"role": "system", "content": "Você é um assistente útil. Responda apenas 'Teste de conexão bem-sucedido!'."},
            {"role": "user", "content": "Teste de conexão"}
        ]
        
        try:
            response = ai_manager.chat_completion(
                messages=test_messages,
                provider=provider,
                model=model,
                temperature=0.1,
                max_tokens=50
            )
            
            return jsonify({
                'success': True,
                'provider': provider,
                'model': model,
                'response': response.get('content', ''),
                'used_provider': response.get('provider', 'unknown'),
                'used_model': response.get('model', 'unknown')
            })
            
        except Exception as ai_error:
            return jsonify({
                'success': False,
                'provider': provider,
                'model': model,
                'error': str(ai_error),
                'available_providers': ai_manager.get_available_providers()
            }), 400
            
    except Exception as e:
        return jsonify({'error': f'Erro no teste de conexão: {str(e)}'}), 500

@ai_config_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_ai_settings():
    """Retorna as configurações atuais de IA"""
    try:
        settings = {
            'default_provider': ai_manager.default_provider,
            'default_model': ai_manager.default_model,
            'default_vision_provider': ai_manager.default_vision_provider,
            'default_vision_model': ai_manager.default_vision_model,
            'default_multimodal_provider': ai_manager.default_multimodal_provider,
            'default_multimodal_model': ai_manager.default_multimodal_model,
            'available_providers': ai_manager.get_available_providers(),
            'environment_variables': {
                'OPENAI_API_KEY': '***' if os.getenv('OPENAI_API_KEY') else None,
                'GROQ_API_KEY': '***' if os.getenv('GROQ_API_KEY') else None,
                'ANTHROPIC_API_KEY': '***' if os.getenv('ANTHROPIC_API_KEY') else None,
                'GOOGLE_API_KEY': '***' if os.getenv('GOOGLE_API_KEY') else None,
                'DEEPSEEK_API_KEY': '***' if os.getenv('DEEPSEEK_API_KEY') else None,
                'XAI_API_KEY': '***' if os.getenv('XAI_API_KEY') else None,
                'OLLAMA_BASE_URL': os.getenv('OLLAMA_BASE_URL'),
                'OLLAMA_CLOUD_URL': os.getenv('OLLAMA_CLOUD_URL'),
                'DEFAULT_LLM_PROVIDER': os.getenv('DEFAULT_LLM_PROVIDER'),
                'DEFAULT_LLM_MODEL': os.getenv('DEFAULT_LLM_MODEL'),
                'DEFAULT_LLM_VISION_PROVIDER': os.getenv('DEFAULT_LLM_VISION_PROVIDER'),
                'DEFAULT_LLM_VISION_MODEL': os.getenv('DEFAULT_LLM_VISION_MODEL'),
                'DEFAULT_LLM_MULTIMODAL_PROVIDER': os.getenv('DEFAULT_LLM_MULTIMODAL_PROVIDER'),
                'DEFAULT_LLM_MULTIMODAL_MODEL': os.getenv('DEFAULT_LLM_MULTIMODAL_MODEL')
            }
        }
        
        return jsonify(settings)
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter configurações: {str(e)}'}), 500

@ai_config_bp.route('/health', methods=['GET'])
def ai_health():
    """Endpoint de saúde para verificar status da IA"""
    try:
        available_providers = ai_manager.get_available_providers()
        
        return jsonify({
            'status': 'healthy' if available_providers else 'degraded',
            'available_providers': available_providers,
            'default_provider': ai_manager.default_provider,
            'default_model': ai_manager.default_model,
            'default_vision_provider': ai_manager.default_vision_provider,
            'default_vision_model': ai_manager.default_vision_model,
            'default_multimodal_provider': ai_manager.default_multimodal_provider,
            'default_multimodal_model': ai_manager.default_multimodal_model,
            'message': 'Sistema de IA operacional' if available_providers else 'Nenhum provedor de IA disponível'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Erro no sistema de IA'
        }), 500
