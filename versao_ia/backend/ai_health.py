"""
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
