"""
ARAOS Voice Server — FastAPI WebSocket Server
Servidor principal de voz multimodal do ARAOS.

Integra:
    - Session Manager (gerenciamento de sessões)
    - VAD (Voice Activity Detection)
    - STT (Speech-to-Text com faster-whisper)
    - Conversation Buffer
    - Voice Copilot (futuro)

Baseado em live_audio_server.py mas evoluído para arquitetura modular.
"""

import asyncio
import json
import logging
import struct
import time
import traceback
from contextlib import asynccontextmanager
from typing import Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from .components.session_manager import SessionManager, SessionState, VoiceSession
from .components.conversation_buffer import ConversationBuffer, ConversationSegment
from .components.vad_processor import VADProcessor
from .components.stt_engine import STTEngine

logger = logging.getLogger("araos.voice.server")


# ── Global State ──────────────────────────────────────────────────────────

session_manager: Optional[SessionManager] = None
vad_processor: Optional[VADProcessor] = None
stt_engine: Optional[STTEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida do servidor."""
    global session_manager, vad_processor, stt_engine
    
    logger.info("🚀 ARAOS Voice Server starting...")
    
    # Inicializar componentes
    session_manager = SessionManager()
    await session_manager.start()
    
    vad_processor = VADProcessor()
    
    stt_engine = STTEngine()
    await stt_engine.load_model()
    
    logger.info("✅ All components initialized")
    yield
    
    # Cleanup
    logger.info("🛑 ARAOS Voice Server shutting down...")
    if session_manager:
        await session_manager.stop()
    if stt_engine:
        await stt_engine.unload()
    logger.info("👋 Goodbye")


app = FastAPI(
    title="ARAOS Voice Server",
    description="Copiloto Clínico Multimodal por Voz",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Protocolo de Mensagens ────────────────────────────────────────────────

class VoiceProtocol:
    """Protocolo de mensagens bidirecional Voice Server ↔ Frontend."""
    
    # Cliente → Servidor
    SESSION_INIT = "session_init"
    AUDIO_CHUNK = "audio_chunk"
    COMMAND = "command"
    CONFIRMATION = "confirmation"
    HEARTBEAT = "heartbeat"
    
    # Servidor → Cliente
    TRANSCRIPTION = "transcription"
    ENTITY = "entity"
    SUGGESTION = "suggestion"
    ACTION_PROPOSAL = "action_proposal"
    ACTION_RESULT = "action_result"
    TTS_AUDIO = "tts_audio"
    STATE_CHANGE = "state_change"
    ERROR = "error"


# ── Helpers ───────────────────────────────────────────────────────────────

def build_message(msg_type: str, payload: dict, session_id: str) -> str:
    return json.dumps({
        "type": msg_type,
        "session_id": session_id,
        "timestamp": int(time.time() * 1000),
        "payload": payload,
    })


# ── WebSocket Handler ─────────────────────────────────────────────────────

class VoiceWebSocketHandler:
    """
    Handler para uma conexão WebSocket de voz.
    Gerencia uma sessão única de consulta por voz.
    """
    
    def __init__(self, websocket: WebSocket, session: VoiceSession):
        self.websocket = websocket
        self.session = session
        self.buffer = ConversationBuffer()
        
        # Áudio acumulado para STT
        self._audio_buffer: bytearray = bytearray()
        self._speech_active = False
        self._speech_start_ms = 0
        self._segment_index = 0
        
        # Tasks
        self._tasks: list[asyncio.Task] = []
        self._running = False
    
    async def run(self):
        """Loop principal da conexão."""
        self._running = True
        
        # Configurar callbacks da sessão
        self.session.on_state_change = self._on_state_change
        self.session.on_transcription = self._on_transcription
        
        # Iniciar task de heartbeat
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._tasks.append(heartbeat_task)
        
        try:
            while self._running and self.session.is_active:
                message = await self.websocket.receive()
                await self._handle_message(message)
        except WebSocketDisconnect:
            logger.info(f"Client disconnected: {self.session.id}")
        except Exception as e:
            logger.error(f"Error in WebSocket loop: {e}")
            await self._send_error(str(e))
        finally:
            await self._cleanup()
    
    async def _handle_message(self, message):
        """Processa mensagem recebida do cliente."""
        self.session.touch()
        
        # Se for bytes (áudio PCM)
        if isinstance(message, bytes):
            await self._process_audio_chunk(message)
            return
        
        # Se for texto (JSON)
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            logger.warning("Received invalid JSON")
            return
        
        msg_type = data.get("type")
        
        if msg_type == VoiceProtocol.HEARTBEAT:
            await self.websocket.send_text(json.dumps({
                "type": VoiceProtocol.HEARTBEAT,
                "timestamp": int(time.time() * 1000),
            }))
        
        elif msg_type == VoiceProtocol.COMMAND:
            await self._handle_command(data.get("payload", {}))
        
        elif msg_type == VoiceProtocol.CONFIRMATION:
            await self._handle_confirmation(data.get("payload", {}))
        
        else:
            logger.warning(f"Unknown message type: {msg_type}")
    
    async def _process_audio_chunk(self, chunk: bytes):
        """Processa chunk de áudio PCM."""
        # Atualizar métricas
        duration_ms = len(chunk) // 2 * 1000 // 16000  # 16-bit, 16kHz
        self.session.total_audio_duration_ms += duration_ms
        
        # Acumular no buffer
        self._audio_buffer.extend(chunk)
        
        # Verificar se temos áudio suficiente para processar (100ms = 3200 bytes)
        if len(self._audio_buffer) < 3200:
            return
        
        # Processar VAD
        audio_bytes = bytes(self._audio_buffer)
        self._audio_buffer = bytearray()
        
        is_speech = vad_processor.is_speech(audio_bytes)
        
        if is_speech and not self._speech_active:
            # Início de fala
            self._speech_active = True
            self._speech_start_ms = self.session.total_audio_duration_ms - duration_ms
            logger.debug(f"Speech started at {self._speech_start_ms}ms")
        
        elif not is_speech and self._speech_active:
            # Fim de fala — processar STT
            self._speech_active = False
            await self._process_speech_segment(
                audio_bytes,
                self._speech_start_ms,
                self.session.total_audio_duration_ms,
            )
    
    async def _process_speech_segment(self, audio: bytes, start_ms: int, end_ms: int):
        """Processa um segmento de fala com STT."""
        await self.session.transition_to(SessionState.PROCESSING, "speech_segment_end")
        
        try:
            # Transcrever
            text = await stt_engine.transcribe(audio, language=self.session.language)
            
            if not text or not text.strip():
                await self.session.transition_to(SessionState.LISTENING, "empty_transcription")
                return
            
            # Determinar speaker (simplificado: alternância ou default doctor)
            speaker = self._infer_speaker(text)
            
            # Criar segmento
            self._segment_index += 1
            segment = self.buffer.start_segment(speaker, start_ms)
            segment.text = text
            segment.end_time_ms = end_ms
            segment.is_final = True
            self.buffer.finalize_current()
            
            # Atualizar métricas de fala
            speech_duration = end_ms - start_ms
            self.session.speech_duration_ms += speech_duration
            if speaker == "doctor":
                self.session.doctor_speech_duration_ms += speech_duration
            else:
                self.session.patient_speech_duration_ms += speech_duration
            
            # Enviar transcrição para frontend
            await self._send_transcription(segment)
            
            # Verificar wake word (futuro: Porcupine)
            if self._is_wake_word_command(text):
                await self._handle_wake_word(text)
                return
            
            # Se estiver em modo full, processar com Copilot (futuro)
            if self.session.mode == "full":
                # Por enquanto, apenas volta a escutar
                pass
            
            await self.session.transition_to(SessionState.LISTENING, "transcription_complete")
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            await self._send_error(f"Transcription failed: {e}")
            await self.session.transition_to(SessionState.LISTENING, "stt_error")
    
    def _infer_speaker(self, text: str) -> str:
        """
        Inferir se quem falou é médico ou paciente.
        
        Estratégias:
        1. Se texto começa com wake word → médico (comando)
        2. Alternância simples (se último foi paciente, este é médico)
        3. Default: unknown (será corrigido pela UI ou diarização futura)
        """
        text_lower = text.lower().strip()
        wake_words = [self.session.wake_word.lower(), f"ok {self.session.wake_word.lower()}"]
        
        for ww in wake_words:
            if text_lower.startswith(ww):
                return "doctor"
        
        # Alternância simples
        if self.buffer.segment_count > 0:
            last_speaker = self.buffer._segments[-1].speaker
            return "patient" if last_speaker == "doctor" else "doctor"
        
        return "unknown"
    
    def _is_wake_word_command(self, text: str) -> bool:
        """Verifica se o texto contém wake word."""
        text_lower = text.lower().strip()
        wake_words = [
            self.session.wake_word.lower(),
            f"ok {self.session.wake_word.lower()}",
            f"{self.session.wake_word.lower()}os",
        ]
        return any(text_lower.startswith(ww) for ww in wake_words)
    
    async def _handle_wake_word(self, text: str):
        """Processa comando após wake word."""
        logger.info(f"Wake word detected: '{text}'")
        # Futuro: enviar para Intent Classifier
        # Por enquanto, enviar confirmação visual
        await self.websocket.send_text(build_message(
            VoiceProtocol.STATE_CHANGE,
            {
                "previous_state": "listening",
                "current_state": "processing",
                "reason": "wake_word_detected",
            },
            self.session.id,
        ))
    
    async def _handle_command(self, payload: dict):
        """Processa comando explícito do frontend."""
        action = payload.get("action")
        
        if action == "start_recording":
            await self.session.transition_to(SessionState.LISTENING, "user_start")
        
        elif action == "stop_recording":
            await self.session.transition_to(SessionState.IDLE, "user_stop")
        
        elif action == "pause":
            await self.session.transition_to(SessionState.PAUSED, "user_pause")
        
        elif action == "resume":
            await self.session.transition_to(SessionState.LISTENING, "user_resume")
        
        elif action == "end_session":
            await self._end_session()
    
    async def _handle_confirmation(self, payload: dict):
        """Processa confirmação de ação proposta."""
        action_id = payload.get("action_id")
        confirmed = payload.get("confirmed", False)
        logger.info(f"Action {action_id} confirmed={confirmed}")
        # Futuro: executar ação via Action Executor
    
    async def _on_state_change(self, old_state, new_state, reason):
        """Callback: sessão mudou de estado."""
        await self.websocket.send_text(build_message(
            VoiceProtocol.STATE_CHANGE,
            {
                "previous_state": old_state.value,
                "current_state": new_state.value,
                "reason": reason,
            },
            self.session.id,
        ))
    
    async def _on_transcription(self, segment: ConversationSegment):
        """Callback: nova transcrição disponível."""
        pass  # Já enviado diretamente em _send_transcription
    
    async def _send_transcription(self, segment: ConversationSegment):
        """Envia transcrição para o frontend."""
        await self.websocket.send_text(build_message(
            VoiceProtocol.TRANSCRIPTION,
            segment.to_dict(),
            self.session.id,
        ))
    
    async def _send_error(self, message: str):
        """Envia mensagem de erro."""
        await self.websocket.send_text(build_message(
            VoiceProtocol.ERROR,
            {"message": message},
            self.session.id,
        ))
    
    async def _heartbeat_loop(self):
        """Envia heartbeat periódico."""
        while self._running:
            try:
                await asyncio.sleep(30)
                await self.websocket.send_text(json.dumps({
                    "type": VoiceProtocol.HEARTBEAT,
                    "timestamp": int(time.time() * 1000),
                }))
            except Exception:
                break
    
    async def _end_session(self):
        """Finaliza a sessão."""
        self._running = False
        
        # Finalizar segmento atual se houver
        self.buffer.finalize_current()
        
        # Gerar resumo
        summary = self.buffer.get_summary()
        self.session.structured_data = {
            "transcript": self.buffer.get_full_transcript(),
            "summary": summary,
        }
        
        await session_manager.end_session(self.session.id)
        await self.websocket.close(code=1000, reason="Session ended")
    
    async def _cleanup(self):
        """Limpa recursos."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        
        if self.session.is_active:
            await session_manager.end_session(self.session.id)


# ── FastAPI Routes ────────────────────────────────────────────────────────

@app.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
    tenant_id: str = Query(...),
    patient_id: str = Query(...),
    doctor_id: str = Query(...),
    specialty: str = Query("general"),
    wake_word: str = Query("Ara"),
    language: str = Query("pt-BR"),
    mode: str = Query("full"),
):
    """
    Endpoint WebSocket principal para ARAOS Voice.
    
    Query Parameters:
        tenant_id: ID do tenant (clínica)
        patient_id: ID do paciente em atendimento
        doctor_id: ID do médico
        specialty: Especialidade ('general', 'cannabis', 'cardio', etc.)
        wake_word: Palavra de ativação ('Ara', 'Ok Ara', 'AraOS')
        language: Idioma ('pt-BR', 'en-US', etc.)
        mode: Modo de operação ('full', 'transcription_only', 'command_only')
    """
    await websocket.accept()
    
    # Criar sessão
    session = await session_manager.create_session(
        tenant_id=tenant_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        specialty=specialty,
        wake_word=wake_word,
        language=language,
        mode=mode,
    )
    
    logger.info(f"WebSocket connection accepted for session {session.id}")
    
    # Enviar confirmação de inicialização
    await websocket.send_text(build_message(
        VoiceProtocol.STATE_CHANGE,
        {
            "previous_state": "none",
            "current_state": "idle",
            "reason": "session_initialized",
            "session": session.to_dict(),
        },
        session.id,
    ))
    
    # Iniciar handler
    handler = VoiceWebSocketHandler(websocket, session)
    await handler.run()


@app.get("/health")
async def health_check():
    """Health check do servidor de voz."""
    active_sessions = await session_manager.list_active_sessions() if session_manager else []
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "stt_loaded": stt_engine is not None and stt_engine.is_loaded,
        "vad_loaded": vad_processor is not None,
    }


@app.get("/sessions")
async def list_sessions():
    """Lista sessões ativas (para monitoramento)."""
    sessions = await session_manager.list_active_sessions() if session_manager else []
    return {
        "sessions": [s.to_dict() for s in sessions],
    }


# ── Entry Point ───────────────────────────────────────────────────────────

def main():
    """Ponto de entrada para execução standalone."""
    import uvicorn
    uvicorn.run(
        "services.voice.server:app",
        host="0.0.0.0",
        port=8765,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
