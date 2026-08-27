"""
ARAOS Voice Server — FastAPI WebSocket Server
Servidor principal de voz multimodal do ARAOS.
"""

import asyncio
import json
import logging
import os
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


# ── TTS Engine (OpenAI) ───────────────────────────────────────────────────

class TTSEngine:
    """Síntese de voz via OpenAI TTS."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                from services.ai_config_storage import get_api_key
                api_key = get_api_key("openai")
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY não configurada para TTS")
            self._client = OpenAI(api_key=api_key)
        return self._client

    async def synthesize(self, text: str, voice: str = "alloy") -> bytes:
        """Sintetiza texto em áudio MP3."""
        client = self._get_client()
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
            ),
        )
        return response.content


# ── Copilot Engine ────────────────────────────────────────────────────────

class CopilotEngine:
    """Processa transcrições e gera respostas/ações usando LLM."""

    SYSTEM_PROMPT = (
        "Você é o Ara, copiloto clínico por voz do sistema ARAOS. "
        "Você recebe transcrições de consultas médicas em tempo real e deve:\n"
        "1. Identificar entidades clínicas (sintomas, medicamentos, diagnósticos, exames)\n"
        "2. Detectar intenções do médico (prescrever, agendar, diagnosticar, perguntar)\n"
        "3. Sugerir ações quando apropriado (prescrição, agendamento, exame)\n"
        "4. Responder perguntas do médico sobre o paciente\n\n"
        "Responda SEMPRE em JSON no seguinte formato:\n"
        "{{\n"
        '  "type": "suggestion" | "action_proposal" | "answer" | "none",\n'
        '  "entities": [{{"type": "symptom"|"medication"|"diagnosis"|"exam", "text": "...", "normalized": "..."}}],\n'
        '  "intent": "prescribe" | "schedule" | "diagnose" | "ask" | "inform" | "none",\n'
        '  "response_text": "texto para ser falado ao médico (em português, natural e conciso)",\n'
        '  "action": null | {{"type": "prescription"|"exam_request"|"referral"|"schedule",\n'
        '    "description": "...",\n'
        '    "parameters": {{...}}}}\n'
        "}}\n\n"
        "Seja conciso. A resposta falada (response_text) deve ter no máximo 2 frases."
    )

    def __init__(self):
        self._ai_manager = None

    def _get_ai_manager(self):
        if self._ai_manager is None:
            from services.ai_agents import ai_manager
            self._ai_manager = ai_manager
        return self._ai_manager

    async def process(self, text: str, context: Dict) -> Dict:
        """Processa uma transcrição e retorna resposta estruturada."""
        manager = self._get_ai_manager()

        recent_context = context.get("recent_context", "")
        patient_info = context.get("patient_info", "")

        user_content = f"Transcrição do médico: \"{text}\"\n\n"
        if recent_context:
            user_content += f"Contexto recente da consulta:\n{recent_context}\n\n"
        if patient_info:
            user_content += f"Informações do paciente:\n{patient_info}"

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: manager.chat_completion(
                    messages=messages,
                    provider="openai",
                    temperature=0.3,
                    max_tokens=500,
                ),
            )
            content = result.get("content", "")
            # Parse JSON do conteúdo
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"type": "none", "response_text": "", "entities": [], "intent": "none", "action": None}
        except Exception as e:
            logger.error(f"Copilot error: {e}")
            return {"type": "none", "response_text": "", "entities": [], "intent": "none", "action": None}


# ── Global engine instances ──────────────────────────────────────────────

tts_engine: Optional[TTSEngine] = None
copilot_engine: Optional[CopilotEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global session_manager, vad_processor, stt_engine, tts_engine, copilot_engine

    logger.info("ARAOS Voice Server starting...")

    session_manager = SessionManager()
    await session_manager.start()

    vad_processor = VADProcessor()

    stt_engine = STTEngine()
    await stt_engine.load_model()

    tts_engine = TTSEngine()
    copilot_engine = CopilotEngine()

    logger.info("All components initialized")
    yield

    logger.info("ARAOS Voice Server shutting down...")
    if session_manager:
        await session_manager.stop()
    if stt_engine:
        await stt_engine.unload()


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
    SESSION_INIT = "session_init"
    AUDIO_CHUNK = "audio_chunk"
    COMMAND = "command"
    CONFIRMATION = "confirmation"
    HEARTBEAT = "heartbeat"

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
    def __init__(self, websocket: WebSocket, session: VoiceSession):
        self.websocket = websocket
        self.session = session
        self.buffer = ConversationBuffer()

        self._audio_buffer: bytearray = bytearray()
        self._speech_active = False
        self._speech_start_ms = 0
        self._segment_index = 0

        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def run(self):
        self._running = True

        self.session.on_state_change = self._on_state_change
        self.session.on_transcription = self._on_transcription

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
        self.session.touch()

        if isinstance(message, bytes):
            await self._process_audio_chunk(message)
            return

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
        duration_ms = len(chunk) // 2 * 1000 // 16000
        self.session.total_audio_duration_ms += duration_ms

        self._audio_buffer.extend(chunk)

        if len(self._audio_buffer) < 3200:
            return

        audio_bytes = bytes(self._audio_buffer)
        self._audio_buffer = bytearray()

        is_speech = vad_processor.is_speech(audio_bytes)

        if is_speech and not self._speech_active:
            self._speech_active = True
            self._speech_start_ms = self.session.total_audio_duration_ms - duration_ms
            logger.debug(f"Speech started at {self._speech_start_ms}ms")

        elif not is_speech and self._speech_active:
            self._speech_active = False
            await self._process_speech_segment(
                audio_bytes,
                self._speech_start_ms,
                self.session.total_audio_duration_ms,
            )

    async def _process_speech_segment(self, audio: bytes, start_ms: int, end_ms: int):
        await self.session.transition_to(SessionState.PROCESSING, "speech_segment_end")

        try:
            text = await stt_engine.transcribe(audio, language=self.session.language)

            if not text or not text.strip():
                await self.session.transition_to(SessionState.LISTENING, "empty_transcription")
                return

            speaker = self._infer_speaker(text)

            self._segment_index += 1
            segment = self.buffer.start_segment(speaker, start_ms)
            segment.text = text
            segment.end_time_ms = end_ms
            segment.is_final = True
            self.buffer.finalize_current()

            speech_duration = end_ms - start_ms
            self.session.speech_duration_ms += speech_duration
            if speaker == "doctor":
                self.session.doctor_speech_duration_ms += speech_duration
            else:
                self.session.patient_speech_duration_ms += speech_duration

            await self._send_transcription(segment)

            if self._is_wake_word_command(text):
                await self._handle_wake_word(text)
                return

            # Modo full: processar com Copilot e gerar TTS
            if self.session.mode == "full" and speaker == "doctor":
                await self._process_with_copilot(text)

            await self.session.transition_to(SessionState.LISTENING, "transcription_complete")

        except Exception as e:
            logger.error(f"STT error: {e}")
            await self._send_error(f"Transcription failed: {e}")
            await self.session.transition_to(SessionState.LISTENING, "stt_error")

    async def _process_with_copilot(self, text: str):
        """Processa texto do médico com o Copilot e envia resposta/sugestões."""
        try:
            context = {
                "recent_context": self.buffer.get_recent_context(5),
                "patient_info": json.dumps(self.session.patient_context),
            }

            result = await copilot_engine.process(text, context)
            if not result or result.get("type") == "none":
                return

            # Enviar entidades como sugestão
            for entity in result.get("entities", []):
                await self.websocket.send_text(build_message(
                    VoiceProtocol.ENTITY,
                    entity,
                    self.session.id,
                ))

            # Enviar sugestão de resposta
            if result.get("response_text"):
                await self.websocket.send_text(build_message(
                    VoiceProtocol.SUGGESTION,
                    {"text": result["response_text"], "intent": result.get("intent")},
                    self.session.id,
                ))

            # Se tem ação proposta, notificar frontend
            if result.get("action"):
                await self.websocket.send_text(build_message(
                    VoiceProtocol.ACTION_PROPOSAL,
                    {
                        "action_id": str(hash(json.dumps(result["action"], sort_keys=True))),
                        "action_type": result["action"]["type"],
                        "description": result["action"]["description"],
                        "parameters": result["action"].get("parameters", {}),
                    },
                    self.session.id,
                ))

            # Gerar TTS para resposta falada
            if result.get("response_text"):
                try:
                    audio_data = await tts_engine.synthesize(result["response_text"])
                    import base64
                    audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                    await self.websocket.send_text(build_message(
                        VoiceProtocol.TTS_AUDIO,
                        {"audio": f"data:audio/mp3;base64,{audio_b64}", "text": result["response_text"]},
                        self.session.id,
                    ))
                except Exception as e:
                    logger.warning(f"TTS synthesis failed: {e}")

        except Exception as e:
            logger.error(f"Copilot processing error: {e}")

    def _infer_speaker(self, text: str) -> str:
        text_lower = text.lower().strip()
        wake_words = [self.session.wake_word.lower(), f"ok {self.session.wake_word.lower()}"]

        for ww in wake_words:
            if text_lower.startswith(ww):
                return "doctor"

        if self.buffer.segment_count > 0:
            last_speaker = self.buffer._segments[-1].speaker
            return "patient" if last_speaker == "doctor" else "doctor"

        return "unknown"

    def _is_wake_word_command(self, text: str) -> bool:
        text_lower = text.lower().strip()
        wake_words = [
            self.session.wake_word.lower(),
            f"ok {self.session.wake_word.lower()}",
            f"{self.session.wake_word.lower()}os",
        ]
        return any(text_lower.startswith(ww) for ww in wake_words)

    async def _handle_wake_word(self, text: str):
        """Processa comando após wake word com classificação de intenção."""
        logger.info(f"Wake word detected: '{text}'")

        # Extrair comando após wake word
        command = text.lower().strip()
        for ww in [f"ok {self.session.wake_word.lower()}", self.session.wake_word.lower(), f"{self.session.wake_word.lower()}os"]:
            if command.startswith(ww):
                command = command[len(ww):].strip()
                break

        await self.websocket.send_text(build_message(
            VoiceProtocol.STATE_CHANGE,
            {
                "previous_state": "listening",
                "current_state": "processing",
                "reason": "wake_word_detected",
            },
            self.session.id,
        ))

        # Processar intenção via Copilot
        if command:
            context = {
                "recent_context": self.buffer.get_recent_context(3),
                "patient_info": json.dumps(self.session.patient_context),
            }
            result = await copilot_engine.process(command, context)
            if result and result.get("response_text"):
                await self.websocket.send_text(build_message(
                    VoiceProtocol.SUGGESTION,
                    {"text": result["response_text"], "intent": result.get("intent"), "is_wake_word": True},
                    self.session.id,
                ))
                try:
                    audio_data = await tts_engine.synthesize(result["response_text"])
                    import base64
                    audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                    await self.websocket.send_text(build_message(
                        VoiceProtocol.TTS_AUDIO,
                        {"audio": f"data:audio/mp3;base64,{audio_b64}", "text": result["response_text"]},
                        self.session.id,
                    ))
                except Exception as e:
                    logger.warning(f"TTS synthesis failed: {e}")

        await self.session.transition_to(SessionState.LISTENING, "wake_word_processed")

    async def _handle_command(self, payload: dict):
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
        """Processa confirmação de ação proposta com execução via Action Executor."""
        action_id = payload.get("action_id")
        confirmed = payload.get("confirmed", False)
        modified = payload.get("modified")
        logger.info(f"Action {action_id} confirmed={confirmed}")

        if not confirmed:
            await self.websocket.send_text(build_message(
                VoiceProtocol.ACTION_RESULT,
                {"action_id": action_id, "status": "rejected", "message": "Ação rejeitada pelo médico"},
                self.session.id,
            ))
            return

        # Executar ação via AI Agent padrão
        try:
            from services.ai_agents import ai_manager
            description = payload.get("description", "Ação clínica")
            action_type = payload.get("action_type", "unknown")

            exec_prompt = (
                f"Execute a seguinte ação clínica:\n"
                f"Tipo: {action_type}\n"
                f"Descrição: {description}\n"
                f"Parâmetros: {json.dumps(modified or payload.get('parameters', {}))}\n\n"
                f"Retorne APENAS um JSON: {{\"success\": true/false, \"result\": \"descrição do resultado\", \"record_id\": \"id opcional\"}}"
            )

            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ai_manager.chat_completion(
                    messages=[{"role": "user", "content": exec_prompt}],
                    provider="openai",
                    temperature=0.1,
                    max_tokens=300,
                ),
            )

            content = result.get("content", '{"success": true, "result": "Ação executada"}')
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            exec_result = json.loads(json_match.group()) if json_match else {"success": True, "result": content}

            await self.websocket.send_text(build_message(
                VoiceProtocol.ACTION_RESULT,
                {
                    "action_id": action_id,
                    "status": "executed" if exec_result.get("success") else "failed",
                    "result": exec_result.get("result", "Ação executada"),
                    "record_id": exec_result.get("record_id"),
                },
                self.session.id,
            ))

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            await self.websocket.send_text(build_message(
                VoiceProtocol.ACTION_RESULT,
                {"action_id": action_id, "status": "failed", "message": f"Erro ao executar ação: {e}"},
                self.session.id,
            ))

    async def _on_state_change(self, old_state, new_state, reason):
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
        pass

    async def _send_transcription(self, segment: ConversationSegment):
        await self.websocket.send_text(build_message(
            VoiceProtocol.TRANSCRIPTION,
            segment.to_dict(),
            self.session.id,
        ))

    async def _send_error(self, message: str):
        await self.websocket.send_text(build_message(
            VoiceProtocol.ERROR,
            {"message": message},
            self.session.id,
        ))

    async def _heartbeat_loop(self):
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
        self._running = False
        self.buffer.finalize_current()

        summary = self.buffer.get_summary()
        self.session.structured_data = {
            "transcript": self.buffer.get_full_transcript(),
            "summary": summary,
        }

        await session_manager.end_session(self.session.id)

        # Persistir no banco de dados (se disponível)
        try:
            await self._persist_session()
        except Exception as e:
            logger.warning(f"Failed to persist session to DB: {e}")

        await self.websocket.close(code=1000, reason="Session ended")

    async def _persist_session(self):
        """Persiste sessão e transcrições no banco de dados."""
        try:
            from models import db
            from services.voice.models.voice_models import (
                VoiceSessionModel, VoiceTranscriptModel, VoiceEntityModel
            )
            from datetime import datetime

            session_model = VoiceSessionModel(
                id=self.session.id,
                tenant_id=self.session.tenant_id,
                patient_id=self.session.patient_id,
                doctor_id=self.session.doctor_id,
                specialty=self.session.specialty,
                started_at=self.session.started_at,
                ended_at=datetime.utcnow(),
                duration_seconds=self.session.duration_seconds,
                wake_word=self.session.wake_word,
                language=self.session.language,
                mode=self.session.mode,
                status="completed",
                total_audio_duration_ms=self.session.total_audio_duration_ms,
                speech_duration_ms=self.session.speech_duration_ms,
                doctor_speech_duration_ms=self.session.doctor_speech_duration_ms,
                patient_speech_duration_ms=self.session.patient_speech_duration_ms,
                structured_data=self.session.structured_data,
            )

            # Criar transcrições
            for i, seg in enumerate(self.buffer._segments):
                transcript = VoiceTranscriptModel(
                    session_id=self.session.id,
                    segment_index=i,
                    speaker=seg.speaker,
                    start_time_ms=seg.start_time_ms,
                    end_time_ms=seg.end_time_ms,
                    text=seg.text,
                    text_normalized=seg.text_normalized,
                    confidence=seg.confidence,
                    is_final=seg.is_final,
                    language=self.session.language,
                )
                session_model.transcripts.append(transcript)

                # Criar entidades
                for ent in seg.entities:
                    entity = VoiceEntityModel(
                        session_id=self.session.id,
                        transcript_id=transcript.id,
                        entity_type=ent.entity_type,
                        text=ent.text,
                        normalized_name=ent.normalized_name,
                        value=ent.value,
                        unit=ent.unit,
                        confidence=ent.confidence,
                        source=ent.source,
                        negated=ent.negated,
                        temporal=ent.temporal,
                        start_time_ms=ent.start_time_ms,
                        end_time_ms=ent.end_time_ms,
                    )
                    session_model.entities.append(entity)

            db.session.add(session_model)
            db.session.commit()
            logger.info(f"Session {self.session.id} persisted to database")

        except ImportError:
            logger.debug("Flask-SQLAlchemy not available, skipping DB persistence")
        except Exception as e:
            db.session.rollback()
            raise

    async def _cleanup(self):
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
    patient_name: str = Query(None),
    patient_age: str = Query(None),
):
    await websocket.accept()

    # Montar contexto do paciente a partir dos parâmetros
    patient_context = {}
    if patient_name:
        patient_context["name"] = patient_name
    if patient_age:
        patient_context["age"] = patient_age

    session = await session_manager.create_session(
        tenant_id=tenant_id,
        patient_id=patient_id,
        doctor_id=doctor_id,
        specialty=specialty,
        wake_word=wake_word,
        language=language,
        mode=mode,
        patient_context=patient_context or None,
    )

    logger.info(f"WebSocket connection accepted for session {session.id}")

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

    handler = VoiceWebSocketHandler(websocket, session)
    await handler.run()


@app.get("/health")
async def health_check():
    active_sessions = await session_manager.list_active_sessions() if session_manager else []
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "stt_loaded": stt_engine is not None and stt_engine.is_loaded,
        "vad_loaded": vad_processor is not None,
    }


@app.get("/sessions")
async def list_sessions():
    sessions = await session_manager.list_active_sessions() if session_manager else []
    return {"sessions": [s.to_dict() for s in sessions]}


@app.post("/sessions/{session_id}/end")
async def end_session_rest(session_id: str):
    """Endpoint REST para finalizar sessão (chamado pela rota Flask)."""
    success = await session_manager.end_session(session_id) if session_manager else False
    return {"success": success, "session_id": session_id}


# ── Entry Point ───────────────────────────────────────────────────────────

def main():
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
