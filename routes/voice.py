"""
Rotas Flask para ARAOS Voice.
Integra o servidor de voz FastAPI com a aplicação Flask principal.
"""

import logging
import os
from flask import Blueprint, jsonify, request, current_app
from functools import wraps

logger = logging.getLogger("araos.voice.routes")

voice_bp = Blueprint('voice', __name__, url_prefix='/api/voice')

VOICE_SERVER_URL = os.getenv('VOICE_SERVER_URL', 'ws://localhost:8765')
VOICE_SERVER_HTTP = os.getenv('VOICE_SERVER_HTTP', 'http://localhost:8765')


def get_current_user_id():
    """Recupera ID do usuário autenticado."""
    from flask_jwt_extended import get_jwt_identity
    try:
        return get_jwt_identity()
    except Exception:
        return None


@voice_bp.route('/config', methods=['GET'])
def get_voice_config():
    """
    Retorna configuração do Voice para o frontend.
    Inclui URL do WebSocket, wake word padrão, etc.
    """
    # TODO: Buscar configuração do tenant
    config = {
        "websocket_url": f"{VOICE_SERVER_URL}/ws/voice",
        "wake_word": "Ara",
        "supported_wake_words": ["Ara", "Ok Ara", "AraOS"],
        "language": "pt-BR",
        "supported_languages": ["pt-BR", "en-US", "es-ES"],
        "modes": ["full", "transcription_only", "command_only"],
        "default_mode": "full",
        "features": {
            "transcription": True,
            "diarization": False,  # Fase 2
            "wake_word": False,    # Fase 2
            "copilot": False,      # Fase 3
            "actions": False,      # Fase 4
            "voice_response": False,  # Fase 3
        },
        "sample_rate": 16000,
        "chunk_duration_ms": 100,
    }
    return jsonify(config)


@voice_bp.route('/status', methods=['GET'])
def get_voice_status():
    """
    Retorna status do servidor de voz.
    """
    import requests
    try:
        resp = requests.get(f"{VOICE_SERVER_HTTP}/health", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify({
                "online": True,
                "active_sessions": data.get("active_sessions", 0),
                "stt_loaded": data.get("stt_loaded", False),
                "vad_loaded": data.get("vad_loaded", False),
            })
    except Exception as e:
        logger.warning(f"Voice server health check failed: {e}")
    
    return jsonify({
        "online": False,
        "active_sessions": 0,
        "stt_loaded": False,
        "vad_loaded": False,
    }), 503


@voice_bp.route('/sessions', methods=['GET'])
def list_voice_sessions():
    """
    Lista sessões de voz ativas do tenant atual.
    """
    # TODO: Implementar com base no session_manager
    # Por enquanto, proxy para o servidor de voz
    import requests
    try:
        resp = requests.get(f"{VOICE_SERVER_HTTP}/sessions", timeout=2)
        if resp.status_code == 200:
            return jsonify(resp.json())
    except Exception as e:
        logger.warning(f"Failed to list sessions: {e}")
    
    return jsonify({"sessions": []})


@voice_bp.route('/sessions/<session_id>/transcript', methods=['GET'])
def get_session_transcript(session_id):
    """
    Retorna transcrição completa de uma sessão de voz.
    """
    # TODO: Buscar do banco de dados
    return jsonify({
        "session_id": session_id,
        "transcript": "",
        "segments": [],
        "summary": {},
    })


@voice_bp.route('/sessions/<session_id>/end', methods=['POST'])
def end_voice_session(session_id):
    """
    Finaliza uma sessão de voz.
    """
    # TODO: Implementar via WebSocket ou API interna
    return jsonify({"success": True, "session_id": session_id})
