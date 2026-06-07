"""
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
