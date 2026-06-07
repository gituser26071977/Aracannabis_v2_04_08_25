"""
Speech-to-Text (STT) Engine para ARAOS Voice.

Implementa transcrição com faster-whisper (OpenAI Whisper otimizado).
Suporta:
    - Transcrição de segmentos completos
    - Detecção de idioma automática
    - Baixa latência com modelos compactos
"""

import asyncio
import io
import logging
import tempfile
import wave
from typing import Optional

logger = logging.getLogger("araos.voice.stt")


class STTEngine:
    """
    Engine de Speech-to-Text usando faster-whisper.
    
    Modelos disponíveis (por tamanho):
        - tiny: ~39M params, ~1GB VRAM, WER ~18%
        - base: ~74M params, ~1GB VRAM, WER ~14%
        - small: ~244M params, ~2GB VRAM, WER ~10%
        - medium: ~769M params, ~5GB VRAM, WER ~8%
        - large-v3: ~1550M params, ~10GB VRAM, WER ~4%
    
    Para produção em português médico, recomenda-se medium ou large-v3.
    Para desenvolvimento/teste, small é suficiente.
    """
    
    DEFAULT_MODEL_SIZE = "small"
    DEFAULT_DEVICE = "auto"  # auto, cpu, cuda
    DEFAULT_COMPUTE_TYPE = "int8"  # int8, float16, float32
    
    def __init__(self,
                 model_size: str = None,
                 device: str = None,
                 compute_type: str = None):
        self.model_size = model_size or self.DEFAULT_MODEL_SIZE
        self.device = device or self.DEFAULT_DEVICE
        self.compute_type = compute_type or self.DEFAULT_COMPUTE_TYPE
        
        self._model = None
        self._is_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    async def load_model(self):
        """Carrega o modelo Whisper em background."""
        if self._is_loaded:
            return
        
        logger.info(
            f"Loading Whisper model: {self.model_size} "
            f"(device={self.device}, compute={self.compute_type})"
        )
        
        try:
            from faster_whisper import WhisperModel
            
            # Carregar modelo (pode demorar na primeira vez pois baixa do HuggingFace)
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root="models/whisper",  # cache local
            )
            
            self._is_loaded = True
            logger.info(f"✅ Whisper model '{self.model_size}' loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def unload(self):
        """Descarrega o modelo para liberar memória."""
        if self._model:
            del self._model
            self._model = None
            self._is_loaded = False
            logger.info("Whisper model unloaded")
    
    async def transcribe(self, 
                         audio_bytes: bytes,
                         language: str = "pt",
                         initial_prompt: str = None,
                         condition_on_previous_text: bool = True) -> str:
        """
        Transcreve áudio PCM para texto.
        
        Args:
            audio_bytes: Áudio PCM 16-bit little-endian, mono, 16kHz
            language: Código do idioma ('pt', 'en', 'es', etc.)
            initial_prompt: Contexto para melhorar transcrição médica
            condition_on_previous_text: Usar texto anterior como contexto
        
        Returns:
            Texto transcrito
        """
        if not self._is_loaded or not self._model:
            raise RuntimeError("STT model not loaded. Call load_model() first.")
        
        # Prompt otimizado para português médico
        if initial_prompt is None:
            initial_prompt = (
                "Transcrição médica em português brasileiro. "
                "Termos técnicos: creatinina, hemoglobina glicada, "
                "prescrição, evolução, diagnóstico, sintomas."
            )
        
        try:
            # Converter PCM bytes para formato WAV em memória
            wav_buffer = self._pcm_to_wav(audio_bytes, sample_rate=16000)
            
            # Transcrever (rodar em thread pool para não bloquear o event loop)
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None,  # default executor
                lambda: list(self._model.transcribe(
                    wav_buffer,
                    language=language,
                    task="transcribe",
                    initial_prompt=initial_prompt,
                    condition_on_previous_text=condition_on_previous_text,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=500),
                ))
            )
            
            # Concatenar texto de todos os segmentos
            text_parts = [seg.text.strip() for seg in segments]
            full_text = " ".join(text_parts)
            
            logger.debug(
                f"Transcribed {len(audio_bytes)} bytes → "
                f"'{full_text[:80]}...' (detected lang: {info.language}, "
                f"prob: {info.language_probability:.2f})"
            )
            
            return full_text
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def _pcm_to_wav(self, pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        """
        Converte bytes PCM para arquivo WAV temporário.
        faster-whisper aceita path ou bytes; usamos path para compatibilidade.
        
        Returns:
            Path do arquivo WAV temporário
        """
        # Criar arquivo WAV temporário
        fd, wav_path = tempfile.mkstemp(suffix=".wav")
        
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_bytes)
        
        return wav_path
    
    async def detect_language(self, audio_bytes: bytes) -> tuple:
        """
        Detecta idioma do áudio.
        
        Returns:
            (language_code, probability)
        """
        if not self._is_loaded:
            raise RuntimeError("STT model not loaded")
        
        wav_buffer = self._pcm_to_wav(audio_bytes)
        
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            None,
            lambda: list(self._model.transcribe(wav_buffer, task="transcribe")),
        )
        
        return info.language, info.language_probability
