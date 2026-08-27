"""
Rotas Flask para ARAOS Voice.
Integra o servidor de voz FastAPI com a aplicação Flask principal.
"""

import logging
import os
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from services.voice.models.voice_models import VoiceSessionModel, VoiceTranscriptModel, VoiceEntityModel

logger = logging.getLogger("araos.voice.routes")

voice_bp = Blueprint('voice', __name__, url_prefix='/api/voice')

VOICE_SERVER_URL = os.getenv('VOICE_SERVER_URL', 'ws://localhost:8765')
VOICE_SERVER_HTTP = os.getenv('VOICE_SERVER_HTTP', 'http://localhost:8765')


def get_current_user_id():
    try:
        return get_jwt_identity()
    except Exception:
        return None


def get_tenant_config_from_db(tenant_id=None):
    """Busca configuração de voz do tenant no banco de dados."""
    try:
        from models import ConfiguracaoIA
        if tenant_id:
            config = ConfiguracaoIA.query.filter_by(tenant_id=tenant_id).first()
        else:
            identity = get_jwt_identity()
            if identity and isinstance(identity, dict):
                config = ConfiguracaoIA.query.filter_by(tenant_id=identity.get("tenant_id")).first()
            else:
                config = None
        if config:
            return {
                "wake_word": config.wake_word or "Ara",
                "tom_de_voz": config.tom_de_voz or "Empático e profissional",
            }
    except Exception as e:
        logger.debug(f"Could not load tenant config: {e}")
    return {}


@voice_bp.route('/config', methods=['GET'])
def get_voice_config():
    tenant_config = get_tenant_config_from_db()
    wake_word = tenant_config.get("wake_word", "Ara")
    config = {
        "websocket_url": f"{VOICE_SERVER_URL}/ws/voice",
        "wake_word": wake_word,
        "supported_wake_words": ["Ara", "Ok Ara", "AraOS"],
        "language": "pt-BR",
        "supported_languages": ["pt-BR", "en-US", "es-ES"],
        "modes": ["full", "transcription_only", "command_only"],
        "default_mode": "full",
        "features": {
            "transcription": True,
            "diarization": False,
            "wake_word": True,
            "copilot": True,
            "actions": True,
            "voice_response": True,
        },
        "sample_rate": 16000,
        "chunk_duration_ms": 100,
    }
    return jsonify(config)


@voice_bp.route('/status', methods=['GET'])
def get_voice_status():
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
@jwt_required()
def list_voice_sessions():
    identity = get_jwt_identity()
    tenant_id = identity.get("tenant_id") if isinstance(identity, dict) else None

    # Tenta buscar do servidor de voz (sessões ativas em memória)
    import requests
    try:
        resp = requests.get(f"{VOICE_SERVER_HTTP}/sessions", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            return jsonify(data)
    except Exception as e:
        logger.warning(f"Failed to list sessions from voice server: {e}")

    # Fallback: buscar do banco de dados
    if tenant_id:
        db_sessions = VoiceSessionModel.query.filter_by(tenant_id=tenant_id).order_by(
            VoiceSessionModel.started_at.desc()
        ).limit(50).all()
        return jsonify({
            "sessions": [{
                "id": s.id,
                "patient_id": s.patient_id,
                "doctor_id": s.doctor_id,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "duration_seconds": s.duration_seconds,
                "mode": s.mode,
            } for s in db_sessions]
        })

    return jsonify({"sessions": []})


@voice_bp.route('/sessions/<session_id>/transcript', methods=['GET'])
@jwt_required()
def get_session_transcript(session_id):
    identity = get_jwt_identity()
    tenant_id = identity.get("tenant_id") if isinstance(identity, dict) else None

    # Buscar do banco de dados
    session = VoiceSessionModel.query.filter_by(id=session_id).first()
    if not session:
        return jsonify({"error": "Sessão não encontrada"}), 404

    if tenant_id and session.tenant_id != tenant_id:
        return jsonify({"error": "Acesso negado"}), 403

    transcripts = VoiceTranscriptModel.query.filter_by(session_id=session_id).order_by(
        VoiceTranscriptModel.segment_index
    ).all()

    return jsonify({
        "session_id": session_id,
        "transcript": "\n".join(
            f"[{'MÉDICO' if t.speaker == 'doctor' else 'PACIENTE'}]: {t.text}"
            for t in transcripts
        ),
        "segments": [{
            "id": t.id,
            "speaker": t.speaker,
            "text": t.text,
            "start_time_ms": t.start_time_ms,
            "end_time_ms": t.end_time_ms,
            "confidence": t.confidence,
            "is_final": t.is_final,
        } for t in transcripts],
        "summary": session.structured_data.get("summary", {}) if session.structured_data else {},
    })


@voice_bp.route('/sessions/<session_id>/end', methods=['POST'])
@jwt_required()
def end_voice_session(session_id):
    identity = get_jwt_identity()
    tenant_id = identity.get("tenant_id") if isinstance(identity, dict) else None

    # Tenta finalizar via servidor de voz (sessão ativa em memória)
    import requests
    try:
        resp = requests.post(
            f"{VOICE_SERVER_HTTP}/sessions/{session_id}/end",
            json={"tenant_id": tenant_id},
            timeout=3,
        )
        if resp.status_code == 200:
            return jsonify(resp.json())
    except Exception as e:
        logger.warning(f"Failed to end session via voice server: {e}")

    # Fallback: finalizar no banco de dados
    session = VoiceSessionModel.query.filter_by(id=session_id).first()
    if not session:
        return jsonify({"error": "Sessão não encontrada"}), 404

    if tenant_id and session.tenant_id != tenant_id:
        return jsonify({"error": "Acesso negado"}), 403

    if session.status == "active":
        from datetime import datetime
        session.status = "completed"
        session.ended_at = datetime.utcnow()
        db.session.commit()

    return jsonify({"success": True, "session_id": session_id})
