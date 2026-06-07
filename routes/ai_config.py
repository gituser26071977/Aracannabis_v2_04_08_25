"""
Rotas de configuração de IA para o Aracannabis
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import os
from services.ai_agents import ai_manager
from services.ai_config_storage import set_api_key, set_base_url, update_config
from routes.ai_config_functions import register_function_routes

ai_config_bp = Blueprint('ai_config', __name__)

# Registrar rotas de configuração por função
register_function_routes(ai_config_bp)

# Metadados dos provedores para o frontend
PROVIDERS_METADATA = {
    'groq': {
        'name': 'Groq',
        'description': 'Plataforma de inferência de IA com velocidade superior. Oferece acesso aos modelos Llama e Mixtral com baixa latência.',
        'requires_api_key': True,
        'base_url': 'https://api.groq.com',
        'default_model': 'llama-3.3-70b-versatile'
    },
    'openai': {
        'name': 'OpenAI',
        'description': 'API oficial da OpenAI. Acesso aos modelos GPT-4o, GPT-4 Turbo e GPT-3.5 Turbo.',
        'requires_api_key': True,
        'base_url': 'https://api.openai.com',
        'default_model': 'gpt-4o'
    },
    'anthropic': {
        'name': 'Anthropic',
        'description': 'Modelos Claude da Anthropic. Especializados em análises médicas e textos longos.',
        'requires_api_key': True,
        'base_url': 'https://api.anthropic.com',
        'default_model': 'claude-3-5-sonnet-20241022'
    },
    'google': {
        'name': 'Google AI',
        'description': 'API Gemini do Google. Modelos multimodais com excelente desempenho.',
        'requires_api_key': True,
        'base_url': 'https://generativelanguage.googleapis.com',
        'default_model': 'gemini-2.0-flash-exp'
    },
    'ollama_local': {
        'name': 'Ollama Local',
        'description': 'Execute modelos localmente via Ollama. Não requer chave de API, apenas instalação local.',
        'requires_api_key': False,
        'base_url': 'http://localhost:11434',
        'default_model': 'llama3.2:3b'
    },
    'ollama_cloud': {
        'name': 'Ollama Cloud',
        'description': 'Instância Ollama em servidor remoto. Configure a URL do seu servidor.',
        'requires_api_key': False,
        'base_url': 'http://seu-servidor:11434',
        'default_model': 'llama3.2:3b'
    },
    'deepseek': {
        'name': 'DeepSeek',
        'description': 'Modelos DeepSeek para coding e chat. API compatível com OpenAI.',
        'requires_api_key': True,
        'base_url': 'https://api.deepseek.com',
        'default_model': 'deepseek-chat'
    },
    'xai': {
        'name': 'xAI (Grok)',
        'description': 'API do Grok da xAI. Ainda não disponível publicamente.',
        'requires_api_key': True,
        'base_url': 'https://api.xai.com',
        'default_model': 'grok-beta'
    },
    'zhipu': {
        'name': 'Zhipu AI',
        'description': 'Modelos ChatGLM da Zhipu AI. Alto desempenho em chinês e inglês, compatível com API OpenAI.',
        'requires_api_key': True,
        'base_url': 'https://open.bigmodel.cn/api/paas/v4/',
        'default_model': 'glm-4'
    }
}

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
    elif provider_name == 'zhipu':
        return bool(os.getenv('ZHIPU_API_KEY'))
    return False

def _get_provider_base_url(provider_name):
    """Retorna a URL base configurada para o provedor"""
    if provider_name == 'ollama_local':
        return os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    elif provider_name == 'ollama_cloud':
        return os.getenv('OLLAMA_CLOUD_URL', 'http://localhost:11434')
    elif provider_name in PROVIDERS_METADATA:
        return os.getenv(f'{provider_name.upper()}_BASE_URL', PROVIDERS_METADATA[provider_name]['base_url'])
    return ''

@ai_config_bp.route('/providers', methods=['GET'])
@jwt_required()
def get_ai_providers():
    """Retorna lista de provedores de IA disponíveis e configurados"""
    try:
        available_providers = ai_manager.get_available_providers()
        
        providers_info = {}
        # Lista de todos os provedores suportados
        supported_providers = ['groq', 'openai', 'anthropic', 'google', 'ollama_local', 'ollama_cloud', 'deepseek', 'xai', 'zhipu']
        for provider in supported_providers:
            if provider in ai_manager.providers:
                metadata = PROVIDERS_METADATA.get(provider, {})
                providers_info[provider] = {
                    'name': metadata.get('name', provider),
                    'description': metadata.get('description', ''),
                    'requires_api_key': metadata.get('requires_api_key', True),
                    'base_url': _get_provider_base_url(provider),
                    'default_model': metadata.get('default_model', ai_manager.providers[provider]['models'][0]),
                    'models': ai_manager.providers[provider]['models'],
                    'available': provider in available_providers,
                    'type': ai_manager.providers[provider].get('type', 'cloud'),
                    'configured': _is_provider_configured(provider)
                }
        
        # Montar objeto current_config no formato esperado pelo frontend
        current_config = {
            'provider': ai_manager.default_provider,
            'model': ai_manager.default_model,
            'base_url': _get_provider_base_url(ai_manager.default_provider),
            'has_openai_key': bool(os.getenv('OPENAI_API_KEY')),
            'has_anthropic_key': bool(os.getenv('ANTHROPIC_API_KEY')),
            'has_google_key': bool(os.getenv('GOOGLE_API_KEY')),
            'has_groq_key': bool(os.getenv('GROQ_API_KEY')),
            'has_xai_key': bool(os.getenv('XAI_API_KEY')),
            'has_deepseek_key': bool(os.getenv('DEEPSEEK_API_KEY')),
            'has_zhipu_key': bool(os.getenv('ZHIPU_API_KEY'))
        }
        
        return jsonify({
            'providers': providers_info,
            'current_config': current_config,
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
    """Define o provedor de IA padrão com configurações completas"""
    try:
        data = request.get_json()
        model = data.get('model')
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        
        supported_providers = ['groq', 'openai', 'anthropic', 'google', 'ollama_local', 'ollama_cloud', 'deepseek', 'xai', 'zhipu']
        if provider_name not in supported_providers:
            return jsonify({'error': 'Provedor não suportado'}), 400
        
        # Verificar se o provedor está disponível (ou será configurado com nova API key)
        available_providers = ai_manager.get_available_providers()
        
        # Se fornecer uma API key, tentar configurar o provedor
        if api_key and provider_name != 'ollama_local':
            env_var_name = f'{provider_name.upper()}_API_KEY'
            if provider_name == 'google':
                env_var_name = 'GOOGLE_API_KEY'
            os.environ[env_var_name] = api_key
            # Re-inicializar o cliente do provedor
            try:
                if provider_name == 'groq' and ai_manager.providers['groq']['available']:
                    import groq
                    ai_manager.providers['groq']['client'] = groq.Groq(api_key=api_key)
                elif provider_name == 'openai' and ai_manager.providers['openai']['available']:
                    from openai import OpenAI
                    ai_manager.providers['openai']['client'] = OpenAI(api_key=api_key)
                elif provider_name == 'anthropic' and ai_manager.providers['anthropic']['available']:
                    import anthropic
                    ai_manager.providers['anthropic']['client'] = anthropic.Anthropic(api_key=api_key)
                elif provider_name == 'google' and ai_manager.providers['google']['available']:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    ai_manager.providers['google']['client'] = genai
                elif provider_name == 'deepseek' and ai_manager.providers['deepseek']['available']:
                    from openai import OpenAI
                    base_url = base_url or 'https://api.deepseek.com'
                    ai_manager.providers['deepseek']['client'] = OpenAI(api_key=api_key, base_url=base_url)
                elif provider_name == 'zhipu':
                    # Para Zhipu, tentamos configurar mesmo se não estiver disponível
                    from openai import OpenAI
                    base_url = base_url or 'https://open.bigmodel.cn/api/paas/v4/'
                    ai_manager.providers['zhipu']['client'] = OpenAI(api_key=api_key, base_url=base_url)
                    ai_manager.providers['zhipu']['available'] = True
            except Exception as client_error:
                return jsonify({'error': f'Erro ao configurar cliente: {str(client_error)}'}), 400
        
        # Atualizar base_url se fornecido
        if base_url:
            if provider_name == 'ollama_local':
                os.environ['OLLAMA_BASE_URL'] = base_url
            elif provider_name == 'ollama_cloud':
                os.environ['OLLAMA_CLOUD_URL'] = base_url
            elif provider_name == 'zhipu':
                # No special env var for zhipu base url in this code, but we set it in client init
                pass 
            else:
                os.environ[f'{provider_name.upper()}_BASE_URL'] = base_url
        
        # Verificar novamente disponibilidade após possível configuração
        available_providers = ai_manager.get_available_providers()
        # Nota: zhipu só fica disponível se tiver client. Se o bloco acima falhou, não vai estar.
        
        if provider_name not in available_providers and provider_name != 'zhipu': # zhipu might be tricky if not re-inited correctly in manager
             # Forcing re-init in manager might be needed if not done above.
             # The above code directly updates ai_manager.providers[...]['client'], so it should be fine.
             pass

        if provider_name not in available_providers:
             return jsonify({'error': f'Provedor {provider_name} não disponível. Verifique a chave de API.'}), 400
        
        # Verificar se o modelo é válido (ou aceitar modelo customizado)
        if model and model not in ai_manager.providers[provider_name]['models']:
            # Se não for um modelo pré-configurado, ainda assim permitir (modelo customizado)
            pass
        
        # Atualizar configurações
        ai_manager.default_provider = provider_name
        if model:
            ai_manager.default_model = model
        
        # Persistir configurações
        config_updates = {
            'default_provider': provider_name,
            'default_model': model or ai_manager.default_model
        }
        
        # Salvar API key se fornecida
        if api_key:
            set_api_key(provider_name, api_key)
        
        # Salvar base_url se fornecida
        if base_url:
            set_base_url(provider_name, base_url)
        
        # Atualizar arquivo de configuração
        update_config(config_updates)
        
        # Retornar current_config atualizado
        current_config = {
            'provider': ai_manager.default_provider,
            'model': ai_manager.default_model,
            'base_url': _get_provider_base_url(ai_manager.default_provider),
            'has_openai_key': bool(os.getenv('OPENAI_API_KEY')),
            'has_anthropic_key': bool(os.getenv('ANTHROPIC_API_KEY')),
            'has_google_key': bool(os.getenv('GOOGLE_API_KEY')),
            'has_groq_key': bool(os.getenv('GROQ_API_KEY')),
            'has_xai_key': bool(os.getenv('XAI_API_KEY')),
            'has_deepseek_key': bool(os.getenv('DEEPSEEK_API_KEY')),
            'has_zhipu_key': bool(os.getenv('ZHIPU_API_KEY'))
        }
        
        return jsonify({
            'message': 'Configuração atualizada e salva com sucesso',
            'provider': provider_name,
            'model': model or ai_manager.default_model,
            'current_config': current_config
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao alterar provedor: {str(e)}'}), 500

@ai_config_bp.route('/providers/vision/<provider_name>', methods=['POST'])
@jwt_required()
def set_ai_vision_provider(provider_name):
    """Define o provedor de Visão padrão com suporte a customização"""
    try:
        data = request.get_json()
        model = data.get('model')
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        
        # Lista simplificada para visão
        supported_providers = ['openai', 'google', 'ollama_local', 'ollama_cloud', 'zhipu']
        if provider_name not in supported_providers:
            return jsonify({'error': 'Provedor não suporta visão ou não é suportado'}), 400
        
        # Configurar API key se fornecida (ANTES de validar disponibilidade)
        if api_key:
            set_api_key(provider_name, api_key)
            # Re-inicializar cliente para ativar o provedor
            ai_manager._initialize_clients()
        
        # Configurar base_url se fornecida
        if base_url:
            set_base_url(provider_name, base_url)
        
        # Validar disponibilidade APÓS configurar API key
        available_providers = ai_manager.get_available_providers()
        if provider_name not in available_providers:
            return jsonify({'error': f'Provedor {provider_name} não disponível. Verifique a API key e tente novamente.'}), 400
        
        ai_manager.default_vision_provider = provider_name
        if model:
            ai_manager.default_vision_model = model
        
        # Persistir
        update_config({
            'default_vision_provider': provider_name,
            'default_vision_model': model or ai_manager.default_vision_model
        })
        
        return jsonify({
            'message': 'Configuração de Visão atualizada e salva',
            'provider': provider_name,
            'model': ai_manager.default_vision_model
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_config_bp.route('/providers/multimodal/<provider_name>', methods=['POST'])
@jwt_required()
def set_ai_multimodal_provider(provider_name):
    """Define o provedor Multimodal padrão (usado para OCR complexo) com suporte a customização"""
    try:
        data = request.get_json()
        model = data.get('model')
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        
        supported_providers = ['openai', 'google', 'ollama_local', 'ollama_cloud', 'zhipu']
        if provider_name not in supported_providers:
            return jsonify({'error': 'Provedor não é suportado para multimodalidade'}), 400
        
        # Configurar API key se fornecida (ANTES de validar disponibilidade)
        if api_key:
            set_api_key(provider_name, api_key)
            # Re-inicializar cliente para ativar o provedor
            ai_manager._initialize_clients()
        
        # Configurar base_url se fornecida
        if base_url:
            set_base_url(provider_name, base_url)
        
        # Validar disponibilidade APÓS configurar API key
        available_providers = ai_manager.get_available_providers()
        if provider_name not in available_providers:
            return jsonify({'error': f'Provedor {provider_name} não disponível. Verifique a API key e tente novamente.'}), 400
        
        ai_manager.default_multimodal_provider = provider_name
        if model:
            ai_manager.default_multimodal_model = model
        
        # Persistir
        update_config({
            'default_multimodal_provider': provider_name,
            'default_multimodal_model': model or ai_manager.default_multimodal_model
        })
        
        return jsonify({
            'message': 'Configuração Multimodal atualizada e salva',
            'provider': provider_name,
            'model': ai_manager.default_multimodal_model
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_config_bp.route('/test', methods=['POST'])
@jwt_required()
def test_ai_connection():
    """Testa a conexão com os provedores de IA"""
    try:
        data = request.get_json()
        provider = data.get('provider', ai_manager.default_provider)
        model = data.get('model', ai_manager.default_model)
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        
        test_messages = [
            {"role": "system", "content": "Você é um assistente útil. Responda apenas 'Teste de conexão bem-sucedido!'."},
            {"role": "user", "content": "Teste de conexão"}
        ]
        
        try:
            # Se API key fornecida, usar temporariamente para teste
            if api_key and provider != 'ollama_local':
                # Criar cliente temporário com a API key fornecida
                if provider == 'groq':
                    import groq
                    temp_client = groq.Groq(api_key=api_key)
                    # Fazer chamada direta
                    chat_response = temp_client.chat.completions.create(
                        model=model,
                        messages=test_messages,
                        temperature=0.1,
                        max_tokens=50
                    )
                    return jsonify({
                        'success': True,
                        'provider': provider,
                        'model': model,
                        'response': chat_response.choices[0].message.content,
                        'used_provider': provider,
                        'used_model': model
                    })
                elif provider in ['openai', 'deepseek']:
                    from openai import OpenAI
                    url = base_url
                    if provider == 'deepseek':
                        url = base_url or 'https://api.deepseek.com'
                    temp_client = OpenAI(api_key=api_key, base_url=url)
                    chat_response = temp_client.chat.completions.create(
                        model=model,
                        messages=test_messages,
                        temperature=0.1,
                        max_tokens=50
                    )
                    return jsonify({
                        'success': True,
                        'provider': provider,
                        'model': model,
                        'response': chat_response.choices[0].message.content,
                        'used_provider': provider,
                        'used_model': model
                    })
            
            # Usar configuração existente
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
                'ZHIPU_API_KEY': '***' if os.getenv('ZHIPU_API_KEY') else None,
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
