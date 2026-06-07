"""
Session Manager para ARAOS Voice.
Gerencia o ciclo de vida das sessões de consulta por voz.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger("araos.voice.session")


class SessionState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    WAITING_CONFIRMATION = "waiting_confirmation"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class VoiceSession:
    """Representa uma sessão de consulta por voz ativa."""
    id: str
    tenant_id: str
    patient_id: str
    doctor_id: str
    specialty: str
    wake_word: str = "Ara"
    language: str = "pt-BR"
    mode: str = "full"
    
    state: SessionState = SessionState.IDLE
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    # Timing
    total_audio_duration_ms: int = 0
    speech_duration_ms: int = 0
    doctor_speech_duration_ms: int = 0
    patient_speech_duration_ms: int = 0
    
    # Contexto
    patient_context: Dict[str, Any] = field(default_factory=dict)
    
    # Callbacks para comunicação com frontend
    on_state_change: Optional[Callable] = None
    on_transcription: Optional[Callable] = None
    on_suggestion: Optional[Callable] = None
    on_action_proposal: Optional[Callable] = None
    on_tts_audio: Optional[Callable] = None
    
    # Metadados
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self._state_lock = asyncio.Lock()
        self._last_activity = datetime.utcnow()
        self._state_history: List[Dict] = []
        self._record_state_change(self.state, "session_initialized")
    
    @property
    def is_active(self) -> bool:
        return self.state not in (SessionState.COMPLETED, SessionState.ERROR)
    
    @property
    def duration_seconds(self) -> int:
        end = self.ended_at or datetime.utcnow()
        return int((end - self.started_at).total_seconds())
    
    def touch(self):
        """Atualiza timestamp de última atividade."""
        self._last_activity = datetime.utcnow()
    
    def is_stale(self, timeout_seconds: int = 300) -> bool:
        """Verifica se sessão está inativa por muito tempo."""
        elapsed = (datetime.utcnow() - self._last_activity).total_seconds()
        return elapsed > timeout_seconds
    
    async def transition_to(self, new_state: SessionState, reason: str = ""):
        """Transiciona para novo estado com logging e callbacks."""
        async with self._state_lock:
            old_state = self.state
            if old_state == new_state:
                return
            
            self.state = new_state
            self._record_state_change(new_state, reason)
            self.touch()
            
            logger.info(
                f"Session {self.id}: {old_state.value} -> {new_state.value} "
                f"(reason: {reason})"
            )
            
            if self.on_state_change:
                try:
                    await self.on_state_change(old_state, new_state, reason)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")
    
    def _record_state_change(self, state: SessionState, reason: str):
        self._state_history.append({
            "state": state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
        })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "doctor_id": self.doctor_id,
            "specialty": self.specialty,
            "state": self.state.value,
            "wake_word": self.wake_word,
            "language": self.language,
            "mode": self.mode,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.duration_seconds,
            "total_audio_duration_ms": self.total_audio_duration_ms,
            "speech_duration_ms": self.speech_duration_ms,
            "state_history": self._state_history,
        }
    
    def complete(self):
        """Finaliza a sessão."""
        self.ended_at = datetime.utcnow()
        self.state = SessionState.COMPLETED
        logger.info(f"Session {self.id} completed. Duration: {self.duration_seconds}s")
    
    def fail(self, error_message: str):
        """Marca sessão com erro."""
        self.ended_at = datetime.utcnow()
        self.state = SessionState.ERROR
        self.metadata["error"] = error_message
        logger.error(f"Session {self.id} failed: {error_message}")


class SessionManager:
    """
    Gerenciador central de sessões de voz.
    Mantém sessões ativas em memória e gerencia ciclo de vida.
    """
    
    def __init__(self, stale_timeout_seconds: int = 300,
                 cleanup_interval_seconds: int = 60):
        self._sessions: Dict[str, VoiceSession] = {}
        self._stale_timeout = stale_timeout_seconds
        self._cleanup_interval = cleanup_interval_seconds
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Inicia o gerenciador e a tarefa de cleanup."""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("SessionManager started")
    
    async def stop(self):
        """Para o gerenciador e finaliza todas as sessões."""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        async with self._lock:
            for session in list(self._sessions.values()):
                if session.is_active:
                    session.complete()
            self._sessions.clear()
        
        logger.info("SessionManager stopped")
    
    async def create_session(
        self,
        tenant_id: str,
        patient_id: str,
        doctor_id: str,
        specialty: str = "general",
        wake_word: str = "Ara",
        language: str = "pt-BR",
        mode: str = "full",
        patient_context: Optional[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
    ) -> VoiceSession:
        """Cria uma nova sessão de voz."""
        session_id = str(uuid.uuid4())
        
        session = VoiceSession(
            id=session_id,
            tenant_id=tenant_id,
            patient_id=patient_id,
            doctor_id=doctor_id,
            specialty=specialty,
            wake_word=wake_word,
            language=language,
            mode=mode,
            patient_context=patient_context or {},
            on_state_change=callbacks.get("on_state_change") if callbacks else None,
            on_transcription=callbacks.get("on_transcription") if callbacks else None,
            on_suggestion=callbacks.get("on_suggestion") if callbacks else None,
            on_action_proposal=callbacks.get("on_action_proposal") if callbacks else None,
            on_tts_audio=callbacks.get("on_tts_audio") if callbacks else None,
        )
        
        async with self._lock:
            self._sessions[session_id] = session
        
        logger.info(f"Session created: {session_id} for patient {patient_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Recupera uma sessão ativa pelo ID."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.touch()
            return session
    
    async def end_session(self, session_id: str) -> bool:
        """Finaliza uma sessão."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.complete()
            return True
    
    async def list_active_sessions(self) -> List[VoiceSession]:
        """Lista todas as sessões ativas."""
        async with self._lock:
            return [s for s in self._sessions.values() if s.is_active]
    
    async def _cleanup_loop(self):
        """Loop periódico que remove sessões inativas."""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                await self._cleanup_stale_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def _cleanup_stale_sessions(self):
        """Remove sessões que ficaram inativas por muito tempo."""
        to_remove = []
        
        async with self._lock:
            for session_id, session in self._sessions.items():
                if session.is_stale(self._stale_timeout):
                    to_remove.append(session_id)
                    if session.is_active:
                        session.complete()
            
            for session_id in to_remove:
                del self._sessions[session_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} stale sessions")
