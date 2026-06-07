"""
Conversation Buffer para ARAOS Voice.
Mantém o histórico de conversação da consulta com segmentos identificados.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal

logger = logging.getLogger("araos.voice.conversation")


@dataclass
class ClinicalEntity:
    """Entidade clínica extraída de um segmento de conversa."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = ""
    text: str = ""
    normalized_name: str = ""
    value: Optional[str] = None
    unit: Optional[str] = None
    confidence: float = 1.0
    source: Literal["patient", "doctor", "inferred"] = "patient"
    negated: bool = False
    temporal: str = "current"
    start_time_ms: int = 0
    end_time_ms: int = 0


@dataclass
class ConversationSegment:
    """Um segmento de conversa identificado (fala de uma pessoa)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    speaker: Literal["doctor", "patient", "unknown"] = "unknown"
    text: str = ""
    text_normalized: str = ""
    is_final: bool = False
    start_time_ms: int = 0
    end_time_ms: int = 0
    confidence: float = 1.0
    language: str = "pt-BR"
    entities: List[ClinicalEntity] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "speaker": self.speaker,
            "text": self.text,
            "is_final": self.is_final,
            "start_time_ms": self.start_time_ms,
            "end_time_ms": self.end_time_ms,
            "confidence": self.confidence,
            "entities": [
                {
                    "entity_type": e.entity_type,
                    "text": e.text,
                    "normalized_name": e.normalized_name,
                    "value": e.value,
                    "unit": e.unit,
                    "confidence": e.confidence,
                }
                for e in self.entities
            ],
            "created_at": self.created_at.isoformat(),
        }


class ConversationBuffer:
    """
    Buffer de conversação da consulta atual.
    Mantém histórico completo para contexto do Copilot.
    """
    
    def __init__(self, max_segments: int = 2000):
        self._segments: List[ConversationSegment] = []
        self._current_segment: Optional[ConversationSegment] = None
        self._max_segments = max_segments
        self._segment_counter = 0
    
    @property
    def segment_count(self) -> int:
        return len(self._segments)
    
    @property
    def total_duration_ms(self) -> int:
        if not self._segments:
            return 0
        return self._segments[-1].end_time_ms
    
    def start_segment(self, speaker: Literal["doctor", "patient", "unknown"],
                      start_time_ms: int = 0) -> ConversationSegment:
        """Inicia um novo segmento de conversa."""
        self._finalize_current()
        
        self._segment_counter += 1
        self._current_segment = ConversationSegment(
            speaker=speaker,
            start_time_ms=start_time_ms,
            is_final=False,
        )
        logger.debug(f"Started segment {self._segment_counter} for {speaker}")
        return self._current_segment
    
    def append_to_current(self, text: str, end_time_ms: int,
                          confidence: float = 1.0) -> ConversationSegment:
        """Adiciona texto ao segmento atual (transcrição parcial)."""
        if self._current_segment is None:
            self.start_segment("unknown", end_time_ms - 1000)
        
        self._current_segment.text = text
        self._current_segment.end_time_ms = end_time_ms
        self._current_segment.confidence = confidence
        return self._current_segment
    
    def finalize_current(self, entities: Optional[List[ClinicalEntity]] = None
                         ) -> Optional[ConversationSegment]:
        """Finaliza o segmento atual e o adiciona ao histórico."""
        if self._current_segment is None:
            return None
        
        self._current_segment.is_final = True
        if entities:
            self._current_segment.entities = entities
        
        self._segments.append(self._current_segment)
        segment = self._current_segment
        self._current_segment = None
        
        # Trim se exceder limite
        if len(self._segments) > self._max_segments:
            self._segments = self._segments[-self._max_segments:]
        
        logger.debug(f"Finalized segment: [{segment.speaker}] {segment.text[:80]}...")
        return segment
    
    def _finalize_current(self):
        """Auxiliar: finaliza segmento atual se existir."""
        if self._current_segment is not None:
            self.finalize_current()
    
    def get_recent_context(self, n_segments: int = 10) -> str:
        """Retorna os últimos N segmentos como texto formatado."""
        recent = self._segments[-n_segments:] if self._segments else []
        lines = []
        for seg in recent:
            speaker_label = "MÉDICO" if seg.speaker == "doctor" else "PACIENTE"
            lines.append(f"[{speaker_label}]: {seg.text}")
        return "\n".join(lines)
    
    def get_full_transcript(self) -> str:
        """Retorna transcrição completa da consulta."""
        lines = []
        for seg in self._segments:
            speaker_label = "MÉDICO" if seg.speaker == "doctor" else "PACIENTE"
            lines.append(f"[{speaker_label}]: {seg.text}")
        return "\n".join(lines)
    
    def get_doctor_statements(self) -> List[str]:
        """Retorna apenas falas do médico."""
        return [s.text for s in self._segments if s.speaker == "doctor"]
    
    def get_patient_statements(self) -> List[str]:
        """Retorna apenas falas do paciente."""
        return [s.text for s in self._segments if s.speaker == "patient"]
    
    def get_all_entities(self) -> List[ClinicalEntity]:
        """Retorna todas as entidades extraídas."""
        entities = []
        for seg in self._segments:
            entities.extend(seg.entities)
        return entities
    
    def get_entities_by_type(self, entity_type: str) -> List[ClinicalEntity]:
        """Retorna entidades filtradas por tipo."""
        return [
            e for seg in self._segments
            for e in seg.entities
            if e.entity_type == entity_type
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo estatístico da conversação."""
        doctor_segments = [s for s in self._segments if s.speaker == "doctor"]
        patient_segments = [s for s in self._segments if s.speaker == "patient"]
        
        return {
            "total_segments": len(self._segments),
            "doctor_segments": len(doctor_segments),
            "patient_segments": len(patient_segments),
            "doctor_word_count": sum(len(s.text.split()) for s in doctor_segments),
            "patient_word_count": sum(len(s.text.split()) for s in patient_segments),
            "total_entities": len(self.get_all_entities()),
            "entity_types": list(set(
                e.entity_type for seg in self._segments for e in seg.entities
            )),
            "duration_ms": self.total_duration_ms,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "segments": [s.to_dict() for s in self._segments],
            "summary": self.get_summary(),
        }
