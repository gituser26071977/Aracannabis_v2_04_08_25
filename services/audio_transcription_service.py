import os
import base64
import tempfile
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

class AudioTranscriptionService:
    """Serviço de transcrição de áudio usando Groq Whisper (ou OpenAI fallback)."""

    def __init__(self):
        self.groq_key = GROQ_API_KEY
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    def transcribe_base64(self, base64_string: str, mime_type: str = "audio/ogg") -> dict:
        """
        Transcreve áudio em base64 para texto.
        Retorna: {"texto": str, "idioma": str, "duracao_estimada": int}
        """
        try:
            # Limpar prefixo data:audio/...;base64,
            if ',' in base64_string:
                base64_string = base64_string.split(',', 1)[1]

            audio_bytes = base64.b64decode(base64_string)

            # Determinar extensão do arquivo pelo mime_type
            ext_map = {
                "audio/ogg": ".ogg",
                "audio/ogg; codecs=opus": ".ogg",
                "audio/mp3": ".mp3",
                "audio/mpeg": ".mp3",
                "audio/wav": ".wav",
                "audio/x-wav": ".wav",
                "audio/m4a": ".m4a",
                "audio/mp4": ".m4a",
            }
            ext = ext_map.get(mime_type, ".ogg")

            # Salvar em arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            try:
                result = self._transcribe_file(tmp_path)
                return result
            finally:
                os.unlink(tmp_path)

        except Exception as e:
            logger.error(f"Erro transcrição áudio base64: {e}")
            return {"texto": "", "idioma": "", "duracao_estimada": 0, "erro": str(e)}

    def _transcribe_file(self, file_path: str) -> dict:
        """Transcreve arquivo de áudio usando Groq Whisper."""
        # Tentar Groq primeiro (mais barato)
        if self.groq_key:
            try:
                url = "https://api.groq.com/openai/v1/audio/transcriptions"
                with open(file_path, "rb") as audio_file:
                    files = {"file": (os.path.basename(file_path), audio_file)}
                    data = {
                        "model": "whisper-large-v3",
                        "response_format": "json",
                        "language": "pt",
                    }
                    headers = {"Authorization": f"Bearer {self.groq_key}"}

                    resp = requests.post(url, files=files, data=data, headers=headers, timeout=60)

                if resp.status_code == 200:
                    result = resp.json()
                    return {
                        "texto": result.get("text", ""),
                        "idioma": result.get("language", "pt"),
                        "duracao_estimada": result.get("duration", 0),
                    }
                else:
                    logger.warning(f"Groq transcrição falhou: {resp.status_code} - {resp.text}")
            except Exception as e:
                logger.warning(f"Erro Groq transcrição: {e}")

        # Fallback para OpenAI
        if self.openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_key)
                with open(file_path, "rb") as audio_file:
                    result = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="pt",
                    )
                return {
                    "texto": result.text,
                    "idioma": "pt",
                    "duracao_estimada": 0,
                }
            except Exception as e:
                logger.warning(f"Erro OpenAI transcrição: {e}")

        return {"texto": "", "idioma": "", "duracao_estimada": 0, "erro": "Nenhum serviço de transcrição disponível"}

    def transcribe_url(self, audio_url: str) -> dict:
        """Baixa áudio de URL e transcreve."""
        try:
            resp = requests.get(audio_url, timeout=30)
            resp.raise_for_status()
            base64_str = base64.b64encode(resp.content).decode('utf-8')
            # Tentar detectar mime_type da resposta
            mime = resp.headers.get('content-type', 'audio/ogg')
            return self.transcribe_base64(base64_str, mime)
        except Exception as e:
            logger.error(f"Erro transcrição URL: {e}")
            return {"texto": "", "idioma": "", "duracao_estimada": 0, "erro": str(e)}


# Instância global
audio_transcription_service = AudioTranscriptionService()
