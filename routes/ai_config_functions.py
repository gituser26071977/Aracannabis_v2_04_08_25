"""
Endpoints adicionais para configuração de IA por função
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required
from services.ai_agents import ai_manager
from services.ai_config_storage import set_api_key, set_base_url, update_config

def _set_function_provider(provider_name: str, function_key: str, function_label: str):
    """Função auxiliar para configurar provedor de uma função específica"""
    try:
        data = request.get_json()
        model = data.get('model')
        api_key = data.get('api_key')
        base_url = data.get('base_url')
        
        # Configurar API key se fornecida (ANTES de validar disponibilidade)
        if api_key:
            set_api_key(provider_name, api_key)
            ai_manager._initialize_clients()
        
        # Configurar base_url se fornecida
        if base_url:
            set_base_url(provider_name, base_url)
        
        # Validar disponibilidade APÓS configurar API key
        available_providers = ai_manager.get_available_providers()
        if provider_name not in available_providers:
            return jsonify({'error': f'Provedor {provider_name} não disponível. Verifique a API key e tente novamente.'}), 400
        
        # Persistir configuração
        config_key_provider = f'{function_key}_provider'
        config_key_model = f'{function_key}_model'
        
        # Obter modelo padrão do provedor se não fornecido
        from routes.ai_config import PROVIDERS_METADATA
        default_model = PROVIDERS_METADATA.get(provider_name, {}).get('default_model', '')
        
        update_config({
            config_key_provider: provider_name,
            config_key_model: model or default_model
        })
        
        return jsonify({
            'message': f'Configuração de {function_label} atualizada e salva',
            'provider': provider_name,
            'model': model or default_model
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def register_function_routes(bp):
    """Registra as rotas de configuração por função"""
    
    @bp.route('/providers/chat/<provider_name>', methods=['POST'])
    @jwt_required()
    def set_ai_chat_provider(provider_name):
        """Define o provedor de Chat padrão"""
        return _set_function_provider(provider_name, 'chat', 'Chat')

    @bp.route('/providers/audio/<provider_name>', methods=['POST'])
    @jwt_required()
    def set_ai_audio_provider(provider_name):
        """Define o provedor de Áudio padrão"""
        return _set_function_provider(provider_name, 'audio', 'Áudio')

    @bp.route('/providers/spreadsheet/<provider_name>', methods=['POST'])
    @jwt_required()
    def set_ai_spreadsheet_provider(provider_name):
        """Define o provedor de Planilhas padrão"""
        return _set_function_provider(provider_name, 'spreadsheet', 'Planilhas')

    @bp.route('/providers/pdf/<provider_name>', methods=['POST'])
    @jwt_required()
    def set_ai_pdf_provider(provider_name):
        """Define o provedor de PDFs padrão"""
        return _set_function_provider(provider_name, 'pdf', 'PDFs')
