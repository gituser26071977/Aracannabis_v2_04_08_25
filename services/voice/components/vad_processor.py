"""
Voice Activity Detection (VAD) para ARAOS Voice.

Implementações:
    - Silero VAD (recomendado, alta precisão para PT-BR)
    - WebRTC VAD (fallback, leve)
    - Mock/Pass-through (para desenvolvimento sem dependências pesadas)
"""

import logging
import struct
from typing import Optional

logger = logging.getLogger("araos.voice.vad")


class VADProcessor:
    """
    Processador de VAD para ARAOS Voice.
    
    Por padrão tenta usar Silero VAD. Se não disponível,
    fallback para WebRTC VAD ou pass-through.
    """
    
    def __init__(self, 
                 threshold: float = 0.5,
                 min_speech_duration_ms: int = 250,
                 sample_rate: int = 16000):
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.sample_rate = sample_rate
        
        self._silero = None
        self._webrtc = None
        self._mode = "mock"
        
        self._load_vad()
    
    def _load_vad(self):
        """Tenta carregar o melhor VAD disponível."""
        # Tentar Silero VAD
        try:
            import torch
            self._silero_model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
            )
            self._silero_utils = utils
            self._mode = "silero"
            logger.info("✅ Silero VAD loaded")
            return
        except Exception as e:
            logger.warning(f"Silero VAD not available: {e}")
        
        # Tentar WebRTC VAD
        try:
            import webrtcvad
            self._webrtc = webrtcvad.Vad(2)  # Mode 2 (agressivo médio)
            self._mode = "webrtc"
            logger.info("✅ WebRTC VAD loaded")
            return
        except Exception as e:
            logger.warning(f"WebRTC VAD not available: {e}")
        
        # Fallback: pass-through (considera tudo como fala)
        self._mode = "mock"
        logger.warning("⚠️ Using mock VAD (no speech detection)")
    
    def is_speech(self, audio_bytes: bytes) -> bool:
        """
        Determina se o chunk de áudio contém fala.
        
        Args:
            audio_bytes: Áudio PCM 16-bit little-endian, mono
        
        Returns:
            True se contém fala, False caso contrário
        """
        if self._mode == "silero":
            return self._is_speech_silero(audio_bytes)
        elif self._mode == "webrtc":
            return self._is_speech_webrtc(audio_bytes)
        else:
            return self._is_speech_mock(audio_bytes)
    
    def _is_speech_silero(self, audio_bytes: bytes) -> bool:
        """VAD usando Silero."""
        try:
            import torch
            import numpy as np
            
            # Converter bytes para float32 tensor
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0
            
            # Silero espera chunks de 30ms, 60ms, 90ms, 120ms, 150ms, 180ms, 210ms, 240ms, 270ms, 300ms
            # ou full audio
            tensor = torch.from_numpy(audio_float32)
            
            with torch.no_grad():
                speech_prob = self._silero_model(tensor, self.sample_rate).item()
            
            return speech_prob > self.threshold
            
        except Exception as e:
            logger.error(f"Silero VAD error: {e}")
            return True  # fallback: assume speech
    
    def _is_speech_webrtc(self, audio_bytes: bytes) -> bool:
        """VAD usando WebRTC."""
        try:
            # WebRTC VAD espera frames de 10ms, 20ms ou 30ms
            frame_duration_ms = 30
            frame_size = int(self.sample_rate * frame_duration_ms / 1000) * 2  # 16-bit
            
            # Processar múltiplos frames e fazer votação
            num_frames = len(audio_bytes) // frame_size
            if num_frames == 0:
                return False
            
            speech_frames = 0
            for i in range(num_frames):
                frame = audio_bytes[i * frame_size:(i + 1) * frame_size]
                if len(frame) < frame_size:
                    break
                if self._webrtc.is_speech(frame, self.sample_rate):
                    speech_frames += 1
            
            # Considera speech se mais de 30% dos frames são speech
            return speech_frames / num_frames > 0.3
            
        except Exception as e:
            logger.error(f"WebRTC VAD error: {e}")
            return True
    
    def _is_speech_mock(self, audio_bytes: bytes) -> bool:
        """
        Mock VAD: heurística simples baseada em energia.
        Útil para desenvolvimento sem dependências pesadas.
        """
        try:
            # Calcular energia RMS do sinal
            num_samples = len(audio_bytes) // 2
            if num_samples == 0:
                return False
            
            sum_squares = 0
            for i in range(num_samples):
                sample = struct.unpack('<h', audio_bytes[i*2:i*2+2])[0]
                sum_squares += sample * sample
            
            rms = (sum_squares / num_samples) ** 0.5
            
            # Threshold empírico para áudio de voz (silêncio ~0-500, fala ~1000-10000)
            return rms > 800
            
        except Exception as e:
            logger.error(f"Mock VAD error: {e}")
            return True
    
    def get_speech_timestamps(self, audio_bytes: bytes) -> list:
        """
        Retorna timestamps de segmentos de fala.
        Útil para processamento em lote (não real-time).
        
        Returns:
            Lista de dicts com 'start', 'end' em segundos
        """
        if self._mode == "silero":
            try:
                import torch
                import numpy as np
                
                audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
                audio_float32 = audio_int16.astype(np.float32) / 32768.0
                tensor = torch.from_numpy(audio_float32)
                
                timestamps = self._silero_utils[0](
                    tensor,
                    self._silero_model,
                    sampling_rate=self.sample_rate,
                    threshold=self.threshold,
                    min_speech_duration_ms=self.min_speech_duration_ms,
                )
                return timestamps
            except Exception as e:
                logger.error(f"Silero timestamps error: {e}")
        
        # Fallback: retorna o áudio inteiro como um segmento
        duration = len(audio_bytes) / (self.sample_rate * 2)  # 16-bit
        return [{"start": 0.0, "end": duration}]
