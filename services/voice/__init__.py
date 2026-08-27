"""
ARAOS Voice — Copiloto Clínico Multimodal por Voz
Módulo principal de voz do sistema ARAOS.

Componentes:
    - VoiceListener: captura, VAD, STT, diarização
    - VoiceCopilot: interpretação, RAG, execução de ações
    - SessionManager: gerenciamento de sessões de consulta por voz
    - ConversationBuffer: buffer de conversação da consulta
"""

from .components.session_manager import SessionManager, VoiceSession, SessionState
from .components.conversation_buffer import ConversationBuffer, ConversationSegment, ClinicalEntity
from .components.vad_processor import VADProcessor
from .components.stt_engine import STTEngine

__all__ = [
    "SessionManager",
    "VoiceSession",
    "SessionState",
    "ConversationBuffer",
    "ConversationSegment",
    "ClinicalEntity",
    "VADProcessor",
    "STTEngine",
]
