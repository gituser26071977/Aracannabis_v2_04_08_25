"""
Serviço de ingestão inteligente de produtos (medicamentos).

Permite cadastrar produtos a partir de texto, áudio ou imagem usando IA,
com fallback seguro quando algum provedor não está disponível.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .ai_agents import ai_manager, OPENAI_AVAILABLE
from .ocr_service import ocr_service

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - ambiente sem OpenAI instalado
    OpenAI = None  # type: ignore


class ProductIntakeService:
    """Processa texto, áudio ou imagem para sugerir cadastro de produtos."""

    def __init__(self) -> None:
        self.audio_ext = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
        self.image_ext = {".png", ".jpg", ".jpeg"}
        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")

    # ======== Processamento de entrada ========
    def process_input(
        self,
        texto: Optional[str] = None,
        file_path: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Processa a entrada e retorna um produto sugerido."""
        fonte = "texto"
        extracted_text = texto.strip() if texto else ""
        meta: Dict[str, Any] = {}

        if file_path and filename:
            ext = os.path.splitext(filename.lower())[1]
            if ext in self.audio_ext:
                fonte = "audio"
                extracted_text = self._transcribe_audio(file_path)
            elif ext in self.image_ext:
                fonte = "imagem"
                extracted_text, meta = self._extract_from_image(file_path)
            else:
                fonte = "arquivo"
                extracted_text = self._read_text_file(file_path)

        if not extracted_text:
            raise ValueError("Nenhum texto encontrado para processar")

        produto_sugerido = self._parse_product_text(extracted_text)

        return {
            "produto_sugerido": produto_sugerido,
            "fonte": fonte,
            "texto_processado": extracted_text,
            "meta": meta,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ======== Extração ========
    def _transcribe_audio(self, file_path: str) -> str:
        """Transcreve áudio usando Whisper/OpenAI."""
        if not OPENAI_AVAILABLE or OpenAI is None:
            raise ValueError("Transcrição de áudio indisponível (OpenAI não instalado)")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY não configurada para transcrição")

        client = ai_manager.providers.get("openai", {}).get("client")
        if client is None:
            client = OpenAI(api_key=api_key)  # type: ignore

        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(  # type: ignore
                model=self.whisper_model,
                file=audio_file,
                response_format="text",
            )

        # Algumas versões retornam string, outras objeto com .text
        return response if isinstance(response, str) else getattr(response, "text", "")

    def _extract_from_image(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """Extrai texto de imagem via OCR."""
        ocr_result = ocr_service.extract_text(file_path)
        return ocr_result.get("texto", ""), {
            "confianca_ocr": ocr_result.get("confianca"),
            "fonte": "ocr_service",
        }

    def _read_text_file(self, file_path: str) -> str:
        """Lê arquivos texto simples."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""

    # ======== Parsing com IA ========
    def _parse_product_text(self, texto: str) -> Dict[str, Any]:
        """Pede para o LLM estruturar o produto e faz fallback heurístico."""
        system_prompt = """
Você é um agente cadastrado de produtos de cannabis medicinal.
Extraia do texto as seguintes informações e retorne APENAS um JSON:
{
  "nome": "...",
  "tipo": "oleo|capsula|topico|outro",
  "fabricante": "...",
  "descricao": "...",
  "concentracao_cbd": float mg/ml,
  "concentracao_thc": float mg/ml,
  "concentracao_cbg": float mg/ml,
  "concentracao_cbn": float mg/ml,
  "gotas_por_ml": int,
  "volume_ml": float,
  "confianca": 0-100
}
Se algum campo não existir no texto, deixe null e mantenha a unidade mg/ml.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Texto para cadastro: {texto}"},
        ]

        response = ai_manager.chat_completion(messages=messages, temperature=0.2, max_tokens=900)
        content = response.get("content", "")

        if content.startswith("```"):
            content = content.strip("`")
            content = content.replace("json", "", 1).strip()

        parsed = self._fallback_parse(texto)
        try:
            parsed = json.loads(content)
        except Exception:
            # Mantém fallback heurístico
            pass

        produto = self._normalize_product(parsed)
        produto["ai_provider"] = response.get("provider", "unknown")
        produto["ai_model"] = response.get("model", "unknown")
        return produto

    def _fallback_parse(self, texto: str) -> Dict[str, Any]:
        """Heurística básica caso o LLM falhe."""
        def find_value(label: str) -> Optional[float]:
            pattern = rf"{label}[:\s]*([\d.,]+)"
            match = re.search(pattern, texto, flags=re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1).replace(",", "."))
                except ValueError:
                    return None
            return None

        return {
            "nome": texto.splitlines()[0][:120] if texto else None,
            "tipo": "oleo",
            "fabricante": None,
            "descricao": texto[:400],
            "concentracao_cbd": find_value("cbd"),
            "concentracao_thc": find_value("thc"),
            "concentracao_cbg": find_value("cbg"),
            "concentracao_cbn": find_value("cbn"),
            "gotas_por_ml": 30,
            "volume_ml": find_value("ml") or 30,
            "confianca": 45,
        }

    def _normalize_product(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Garante campos e tipos coerentes com o modelo Produto."""
        def to_float(value: Any) -> Optional[float]:
            try:
                return float(value)
            except Exception:
                return None

        def to_int(value: Any) -> Optional[int]:
            try:
                return int(value)
            except Exception:
                return None

        return {
            "nome": (data or {}).get("nome"),
            "tipo": (data or {}).get("tipo") or "oleo",
            "fabricante": (data or {}).get("fabricante"),
            "descricao": (data or {}).get("descricao"),
            "concentracao_cbd": to_float((data or {}).get("concentracao_cbd")) or 0,
            "concentracao_thc": to_float((data or {}).get("concentracao_thc")) or 0,
            "concentracao_cbg": to_float((data or {}).get("concentracao_cbg")) or 0,
            "concentracao_cbn": to_float((data or {}).get("concentracao_cbn")) or 0,
            "gotas_por_ml": to_int((data or {}).get("gotas_por_ml")) or 30,
            "volume_ml": to_float((data or {}).get("volume_ml")) or 30,
            "confianca": to_int((data or {}).get("confianca")) or 60,
        }


product_intake_service = ProductIntakeService()
