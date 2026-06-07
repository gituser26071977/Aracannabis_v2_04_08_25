"""
ARAOS Voice — Copiloto Clínico Multimodal por Voz
Módulo principal de voz do sistema ARAOS.

Componentes:
    - VoiceListener: captura, VAD, STT, diarização
    - VoiceCopilot: interpretação, RAG, execução de ações
    - SessionManager: gerenciamento de sessões de consulta por voz
    - ConversationBuffer: buffer de conversação da consulta
"""

from .components.session_manager import SessionManager, VoiceSession
from .components.conversation_buffer import ConversationBuffer, ConversationSegment

__all__ = [
    "SessionManager",
    "VoiceSession",
    "ConversationBuffer",
    "ConversationSegment",
]
