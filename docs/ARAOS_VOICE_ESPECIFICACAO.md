# ARAOS Voice — Especificação Técnica do Copiloto Clínico por Voz

> **Versão:** 1.0  
> **Data:** 2026-06-07  
> **Status:** Especificação para implementação  
> **Base existente:** `services/live_audio_server.py` (Gemini Live API)

---

## Sumário Executivo

ARAOS Voice é um **Copiloto Clínico Multimodal** que transforma a consulta médica através de inteligência artificial por voz. Ele não apenas transcreve — ele **ouve, compreende, consulta, registra e navega**, sempre mantendo o médico como decisor final.

O módulo se divide em dois componentes principais:

| Componente | Função | Tecnologia Base |
|-----------|--------|-----------------|
| **Voice Listener** | Captura, transcrição, diarização, detecção de wake word | Whisper + WebRTC + VAD |
| **Voice Copilot** | Interpretação, RAG, execução de ações, resposta | Gemini 2.5 Pro + Function Calling + Memória Clínica |

---

## 1. Estado Atual e Evolução

### 1.1 O que já existe (`live_audio_server.py`)

```
✅ Servidor WebSocket (porta 8765)
✅ Comunicação bidirecional áudio com Gemini 2.0 Flash Live
✅ Resposta em áudio (voz "Aoede")
✅ Integração com PDFs de knowledge base
✅ Persona médica/farmacêutica configurável
❌ Sem wake word
❌ Sem diarização (não distingue médico de paciente)
❌ Sem integração com prontuário
❌ Sem execução de ações no sistema
❌ Sem memória clínica do paciente atual
❌ Sem estruturação automática
❌ Sem navegação por voz
❌ Sem auditabilidade completa
```

### 1.2 Evolução Proposta

```
live_audio_server.py  ──►  ARAOS Voice Platform
         │
         ├──► Voice Listener (novo)
         │    ├── Wake Word Engine
         │    ├── VAD (Voice Activity Detection)
         │    ├── Speaker Diarization
         │    ├── Real-time STT (Whisper streaming)
         │    └── Conversation Buffer
         │
         ├──► Voice Copilot (evolução do existente)
         │    ├── Intent Classifier
         │    ├── Clinical Entity Extractor
         │    ├── Prontuário RAG
         │    ├── Action Executor (Function Calling)
         │    ├── Response Generator
         │    └── TTS (Text-to-Speech)
         │
         ├──► Session Manager (novo)
         │    ├── Consulta State Machine
         │    ├── Entity Accumulator
         │    ├── Action Confirmation Queue
         │    └── Audit Logger
         │
         └──► Integration Layer (novo)
              ├── ARAOS CORE API
              ├── ARAOS AI (Memória Longitudinal)
              ├── ARAOS INTAKE (OCR/Documentos)
              └── ARAOS CONNECT (WhatsApp/Notificações)
```

---

## 2. Arquitetura Técnica

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND (Consultório)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ARAOS Voice Widget                                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐ │   │
│  │  │  Microphone  │  │   Speaker    │  │   Visual Feedback        │ │   │
│  │  │  (WebRTC)    │  │  (Web Audio) │  │   • Onda sonora          │ │   │
│  │  │              │  │              │  │   • Transcrição ao vivo  │ │   │
│  │  │  PCM 16kHz   │  │  PCM 16kHz   │  │   • Sugestões discretas  │ │   │
│  │  │  Mono        │  │  Stereo      │  │   • Confirmações         │ │   │
│  │  └──────┬───────┘  └──────▲───────┘  └──────────────────────────┘ │   │
│  │         │                 │                                        │   │
│  │         │    ┌────────────┴────────────┐                          │   │
│  │         │    │    Audio Processor      │                          │   │
│  │         │    │  • Echo Cancellation    │                          │   │
│  │         │    │  • Noise Suppression    │                          │   │
│  │         │    │  • Gain Control         │                          │   │
│  │         │    └────────────┬────────────┘                          │   │
│  │         │                 │                                        │   │
│  │         └─────────────────┘                                        │   │
│  │                    │                                               │   │
│  │              WebSocket (wss://)                                   │   │
│  └────────────────────┼───────────────────────────────────────────────┘   │
└───────────────────────┼───────────────────────────────────────────────────┘
                        │
┌───────────────────────┼───────────────────────────────────────────────────┐
│                       ▼                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                    ARAOS VOICE SERVER                                │  │
│  │                      (FastAPI + WebSocket)                           │  │
│  │                                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────┐    │  │
│  │  │  SESSION MANAGER                                           │    │  │
│  │  │  • SessionStateMachine                                     │    │  │
│  │  │    [idle] → [listening] → [processing] → [responding] → [idle]│  │  │
│  │  │  • PatientContext (quem está sendo atendido)               │    │  │
│  │  │  • ConsultationTimeline (eventos da consulta)              │    │  │
│  │  │  • ActionQueue (ações pendentes de confirmação)            │    │  │
│  │  │  • AuditLog (tudo logado)                                  │    │  │
│  │  └─────────────────────────────────────────────────────────────┘    │  │
│  │                              │                                      │  │
│  │         ┌────────────────────┼────────────────────┐                 │  │
│  │         ▼                    ▼                    ▼                 │  │
│  │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │  │
│  │  │ VOICE        │    │ VOICE        │    │ INTEGRATION  │          │  │
│  │  │ LISTENER     │    │ COPILOT      │    │ LAYER        │          │  │
│  │  │              │    │              │    │              │          │  │
│  │  │• Wake Word   │───►│• Intent      │───►│• CORE API    │          │  │
│  │  │  Detector    │    │  Classifier  │    │  (Paciente)  │          │  │
│  │  │              │    │              │    │              │          │  │
│  │  │• VAD         │───►│• Clinical    │───►│• AI Memory   │          │  │
│  │  │  (Silero/    │    │  Entity      │    │  (RAG)       │          │  │
│  │  │   webrtcvad) │    │  Extractor   │    │              │          │  │
│  │  │              │    │              │    │• INTAKE      │          │  │
│  │  │• Speaker     │───►│• Prontuário  │───►│  (OCR)       │          │  │
│  │  │  Diarization │    │  RAG         │    │              │          │  │
│  │  │  (pyannote)  │    │              │    │• CONNECT     │          │  │
│  │  │              │    │• Function    │───►│  (WhatsApp)  │          │  │
│  │  │• Real-time   │───►│  Calling     │    │              │          │  │
│  │  │  STT         │    │              │    │              │          │  │
│  │  │  (Whisper    │    │• Response    │◄───│              │          │  │
│  │  │   streaming) │    │  Generator   │    │              │          │  │
│  │  │              │    │              │    │              │          │  │
│  │  │• Conversation│───►│• TTS         │◄───│              │          │  │
│  │  │  Buffer      │    │  (Gemini Live│    │              │          │  │
│  │  │              │    │   or Coqui)  │    │              │          │  │
│  │  └──────────────┘    └──────────────┘    └──────────────┘          │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  DATA LAYER                                                        │  │
│  │  • PostgreSQL: voice_sessions, voice_transcripts, voice_actions   │  │
│  │  • Redis: session_state, real-time buffers                         │  │
│  │  • Qdrant: embeddings de consultas para similaridade               │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Tecnologias por Componente

| Componente | Tecnologia Principal | Alternativa | Justificativa |
|-----------|---------------------|-------------|---------------|
| **STT (Streaming)** | Whisper Large v3 (local) | Whisper API / Deepgram | Privacidade, latência, custo |
| **Wake Word** | Porcupine (Picovoice) | OpenWakeWord / Porcupine + custom | Offline, baixa latência, configurable |
| **VAD** | Silero VAD | WebRTC VAD | Precisão superior em português |
| **Diarização** | PyAnnote Audio | WhisperX | Estado da arte, suporta PT-BR |
| **LLM/NLP** | Gemini 2.5 Pro | GPT-4o / Claude 3.5 Sonnet | Function calling, multimodal, custo |
| **TTS** | Gemini Live (Aoede) | ElevenLabs / Coqui TTS | Latência, qualidade médica |
| **Embeddings** | text-embedding-004 | BGE-M3 | RAG multilíngue |
| **Vector DB** | Qdrant | Pinecone / Weaviate | On-premise, filtro metadata |
| **WebSocket** | FastAPI + native | Socket.IO | Async nativo, leve |

### 2.3 Protocolo de Mensagens WebSocket

```typescript
// Protocolo bidirecional entre Frontend e Voice Server

// ===== CLIENTE → SERVIDOR =====

interface VoiceMessage {
  type: 'audio_chunk' | 'wake_word' | 'command' | 'confirmation' | 'session_init' | 'heartbeat';
  session_id: string;
  timestamp: number;
  payload: unknown;
}

// Inicialização de sessão
interface SessionInitPayload {
  tenant_id: string;
  user_id: string;           // médico
  patient_id: string;        // paciente em atendimento
  specialty: string;         // 'cannabis' | 'cardio' | etc
  wake_word: string;         // 'Ara' | 'Ok Ara' | 'AraOS'
  language: string;          // 'pt-BR'
  mode: 'full' | 'transcription_only' | 'command_only';
}

// Chunk de áudio PCM
interface AudioChunkPayload {
  data: ArrayBuffer;         // PCM 16-bit, 16kHz, mono
  sequence: number;          // número de sequência para ordenação
  is_speech: boolean;        // resultado do VAD (opcional, client-side)
}

// Comando explícito (botão ou hotkey)
interface CommandPayload {
  action: 'start_recording' | 'stop_recording' | 'pause' | 'resume' | 'confirm_action' | 'cancel_action';
  action_id?: string;        // para confirmações
}

// Confirmação de ação proposta pelo copiloto
interface ConfirmationPayload {
  action_id: string;
  confirmed: boolean;        // true = executa, false = descarta
  modified?: object;         // dados modificados pelo médico
}


// ===== SERVIDOR → CLIENTE =====

interface VoiceResponse {
  type: 'transcription' | 'diarization' | 'entity' | 'suggestion' | 
        'action_proposal' | 'action_result' | 'tts_audio' | 'error' | 'state_change';
  session_id: string;
  timestamp: number;
  payload: unknown;
}

// Transcrição em tempo real
interface TranscriptionPayload {
  speaker: 'doctor' | 'patient' | 'unknown';
  text: string;
  is_final: boolean;         // true = segmento finalizado
  start_time: number;        // ms desde início da sessão
  end_time: number;
  confidence: number;
}

// Entidade clínica identificada
interface EntityPayload {
  entity_type: 'symptom' | 'diagnosis' | 'medication' | 'allergy' | 
               'exam' | 'dosage' | 'vital_sign' | 'habit' | 'procedure';
  text: string;              // texto original
  normalized: string;        // forma normalizada
  cui?: string;              // UMLS CUI (se disponível)
  confidence: number;
  context: 'patient_said' | 'doctor_said' | 'inferred';
  start_time: number;
}

// Sugestão contextual discreta
interface SuggestionPayload {
  suggestion_id: string;
  type: 'trend' | 'reminder' | 'reference' | 'alert';
  title: string;
  content: string;
  source: 'patient_history' | 'guideline' | 'calculation';
  priority: 'low' | 'medium' | 'high';
  data?: object;             // dados estruturados para visualização
}

// Proposta de ação (requer confirmação)
interface ActionProposalPayload {
  action_id: string;
  action_type: 'create_prescription' | 'schedule_exam' | 'schedule_return' | 
               'update_medication' | 'add_allergy' | 'add_diagnosis' |
               'generate_evolution' | 'send_notification';
  description: string;       // "Solicitar hemograma completo"
  preview: object;           // dados pré-preenchidos para revisão
  requires_confirmation: boolean;  // sempre true para ações clínicas
  timeout_seconds: number;   // tempo para confirmar (default: 30)
}

// Resultado de ação executada
interface ActionResultPayload {
  action_id: string;
  success: boolean;
  message: string;
  data?: object;             // resultado (ex: ID da prescrição criada)
  error?: string;
}

// Áudio TTS para reprodução
interface TTSAudioPayload {
  data: ArrayBuffer;         // áudio PCM/MP3
  text: string;              // texto falado
  voice: string;
}

// Mudança de estado da sessão
interface StateChangePayload {
  previous_state: 'idle' | 'listening' | 'processing' | 'responding' | 'waiting_confirmation';
  current_state: 'idle' | 'listening' | 'processing' | 'responding' | 'waiting_confirmation';
  reason: string;
}
```

---

## 3. Voice Listener — Especificação Detalhada

### 3.1 Wake Word Engine

```python
class WakeWordDetector:
    """
    Detecta palavras de ativação em stream de áudio.
    Usa Porcupine (Picovoice) para detecção offline de baixa latência.
    """
    
    SUPPORTED_WAKE_WORDS = {
        'ara': 'porcupine/ara_pt.ppn',
        'ok_ara': 'porcupine/ok_ara_pt.ppn', 
        'araos': 'porcupine/araos_pt.ppn',
        'custom': None,  # permite upload de .ppn customizado
    }
    
    def __init__(self, wake_word: str = 'ara', sensitivity: float = 0.7):
        self.wake_word = wake_word
        self.sensitivity = sensitivity
        self._porcupine = pvporcupine.create(
            keyword_paths=[self.SUPPORTED_WAKE_WORDS[wake_word]],
            sensitivities=[sensitivity]
        )
    
    def process(self, pcm_frame: np.ndarray) -> bool:
        """Processa um frame de áudio. Retorna True se wake word detectada."""
        keyword_index = self._porcupine.process(pcm_frame)
        return keyword_index >= 0
    
    def set_sensitivity(self, sensitivity: float):
        """Ajusta sensibilidade (0.0 a 1.0). Mais alto = mais falsos positivos."""
        ...
```

**Comportamento:**
- Wake word é configurável por tenant e por médico
- Sensibilidade padrão: 0.7 (balanceado)
- Após detecção, sistema entra em modo "listening" por 10 segundos
- Se nenhum comando for detectado, retorna para "idle"
- LED visual no widget muda de cor (verde = idle, azul = listening, amarelo = processing)

### 3.2 Voice Activity Detection (VAD)

```python
class VADProcessor:
    """
    Silero VAD para detectar fala vs silêncio.
    Segmenta o áudio em chunks de fala para processamento.
    """
    
    def __init__(self, threshold: float = 0.5, 
                 min_speech_duration_ms: int = 250,
                 max_silence_duration_ms: int = 500):
        self.model, self.utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False
        )
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.max_silence_duration_ms = max_silence_duration_ms
    
    def get_speech_timestamps(self, audio: np.ndarray, 
                              sample_rate: int = 16000) -> List[dict]:
        """Retorna timestamps de segmentos de fala."""
        return self.utils[0](
            audio, 
            self.model,
            sampling_rate=sample_rate,
            threshold=self.threshold,
            min_speech_duration_ms=self.min_speech_duration_ms,
            max_silence_duration_ms=self.max_silence_duration_ms
        )
```

**Parâmetros otimizados para consulta médica:**
- `threshold`: 0.5 (padrão, bom para ambiente clínico)
- `min_speech_duration_ms`: 250ms (descarta ruídos curtos)
- `max_silence_duration_ms`: 800ms (permite pausas naturais na fala)

### 3.3 Speaker Diarization

```python
class SpeakerDiarizer:
    """
    Identifica quem está falando: médico ou paciente.
    Usa pyannote.audio com modelo pré-treinado.
    
    Na prática clínica, assume 2 speakers (médico e paciente).
    O médico é identificado pelo perfil de voz cadastrado.
    """
    
    def __init__(self, auth_token: str):
        self.pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=auth_token
        )
    
    def diarize(self, audio_path: str, num_speakers: int = 2) -> List[Segment]:
        """
        Retorna lista de segmentos com speaker label.
        
        Exemplo de saída:
        [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 3.2, "text": "..."},
            {"speaker": "SPEAKER_01", "start": 3.5, "end": 8.1, "text": "..."},
        ]
        """
        diarization = self.pipeline(audio_path, num_speakers=num_speakers)
        return self._map_speakers(diarization)
    
    def _map_speakers(self, diarization) -> Dict[str, str]:
        """
        Mapeia SPEAKER_00/01 para 'doctor'/'patient'.
        
        Estratégias:
        1. Perfil de voz do médico cadastrado (embedding comparado)
        2. Heurística: quem fala mais = paciente (geralmente)
        3. Manual: médico diz "sou eu" na primeira consulta
        """
        ...
```

**Otimização para consulta:**
- Em vez de diarizar todo o áudio, usar approach "online":
  - Médico pressiona botão ou diz wake word → sistema sabe que próximo segmento é médico
  - Alternância de fala é detectada por VAD + pausas
  - Embedding de voz do médico é armazenado no perfil para matching futuro

### 3.4 Real-time STT (Speech-to-Text)

```python
class StreamingSTT:
    """
    Transcrição em tempo real usando Whisper com chunking.
    
    Estratégia: buffer circular de 5 segundos, 
    transcreve a cada chunk processado.
    """
    
    def __init__(self, model_size: str = 'large-v3'):
        self.model = WhisperModel(
            model_size,
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type="float16"
        )
        self.buffer = AudioBuffer(max_duration_ms=5000)
    
    def process_chunk(self, pcm_chunk: bytes) -> Optional[TranscriptionResult]:
        """
        Adiciona chunk ao buffer e tenta transcrever.
        Retorna resultado parcial ou None se insuficiente.
        """
        self.buffer.append(pcm_chunk)
        
        if self.buffer.is_ready():
            segments, info = self.model.transcribe(
                self.buffer.get_audio(),
                language="pt",
                task="transcribe",
                vad_filter=True,
                condition_on_previous_text=True,
            )
            return self._format_result(segments, info)
        return None
    
    def force_transcribe(self) -> TranscriptionResult:
        """Força transcrição do buffer atual (ex: fim de segmento de fala)."""
        ...
```

**Pipeline de STT otimizado:**
1. Áudio PCM 16kHz mono chega do frontend
2. VAD detecta início/fim de fala
3. Durante fala, chunks acumulam em buffer circular (5s)
4. A cada 2s ou ao detectar pausa, transcreve buffer
5. Resultado parcial enviado ao frontend (transcrição ao vivo)
6. Ao finalizar segmento, transcrição final enviada ao Copilot

### 3.5 Conversation Buffer

```python
@dataclass
class ConversationSegment:
    """Um segmento de conversa identificado."""
    id: str
    speaker: Literal['doctor', 'patient', 'unknown']
    text: str
    start_time_ms: int
    end_time_ms: int
    is_final: bool
    entities: List[ClinicalEntity]

class ConversationBuffer:
    """
    Buffer de conversação da consulta atual.
    Mantém histórico completo para contexto do Copilot.
    """
    
    def __init__(self, max_segments: int = 1000):
        self.segments: List[ConversationSegment] = []
        self.current_segment: Optional[ConversationSegment] = None
        self.max_segments = max_segments
    
    def add_partial(self, speaker: str, text: str, timestamp: int):
        """Adiciona transcrição parcial (em tempo real)."""
        ...
    
    def finalize_segment(self) -> ConversationSegment:
        """Finaliza segmento atual e inicia novo."""
        ...
    
    def get_recent_context(self, n_segments: int = 10) -> str:
        """Retorna os últimos N segmentos como texto para contexto do LLM."""
        recent = self.segments[-n_segments:]
        return "\n".join([
            f"[{s.speaker.upper()}]: {s.text}" 
            for s in recent
        ])
    
    def get_full_transcript(self) -> str:
        """Retorna transcrição completa da consulta."""
        ...
    
    def get_doctor_statements(self) -> List[str]:
        """Retorna apenas falas do médico."""
        ...
    
    def get_patient_statements(self) -> List[str]:
        """Retorna apenas falas do paciente."""
        ...
```

---

## 4. Voice Copilot — Especificação Detalhada

### 4.1 Intent Classifier

```python
class IntentClassifier:
    """
    Classifica a intenção do médico a partir do texto transcrito.
    Usa LLM com function calling para classificação estruturada.
    """
    
    INTENTS = {
        # Consultas ao prontuário
        'QUERY_EXAM': 'Consultar resultado de exame',
        'QUERY_MEDICATION': 'Consultar medicamentos atuais',
        'QUERY_HISTORY': 'Consultar histórico/evoluções',
        'QUERY_ALLERGY': 'Consultar alergias',
        'QUERY_DIAGNOSIS': 'Consultar diagnósticos',
        'QUERY_APPOINTMENT': 'Consultar última/próxima consulta',
        'QUERY_VITALS': 'Consultar sinais vitais',
        
        # Navegação
        'NAVIGATE_EXAMS': 'Abrir tela de exames',
        'NAVIGATE_PRESCRIPTIONS': 'Abrir tela de prescrições',
        'NAVIGATE_HISTORY': 'Abrir histórico',
        'NAVIGATE_DOCUMENTS': 'Abrir documentos',
        'NAVIGATE_SCHEDULE': 'Abrir agenda',
        'NAVIGATE_TELEMEDICINE': 'Iniciar teleconsulta',
        
        # Ações clínicas
        'ACTION_PRESCRIBE': 'Gerar prescrição',
        'ACTION_ORDER_EXAM': 'Solicitar exame',
        'ACTION_SCHEDULE_RETURN': 'Agendar retorno',
        'ACTION_ADD_ALLERGY': 'Adicionar alergia',
        'ACTION_ADD_DIAGNOSIS': 'Adicionar diagnóstico',
        'ACTION_UPDATE_MEDICATION': 'Atualizar medicação',
        'ACTION_GENERATE_EVOLUTION': 'Gerar evolução',
        'ACTION_SEND_NOTIFICATION': 'Enviar notificação ao paciente',
        
        # Consulta ao copiloto
        'ASK_GUIDELINE': 'Perguntar sobre guideline/protocolo',
        'ASK_CALCULATION': 'Solicitar cálculo (ex: creatinine clearance)',
        'ASK_DRUG_INTERACTION': 'Verificar interação medicamentosa',
        'ASK_GENERAL': 'Pergunta geral de conhecimento médico',
        
        # Conversação
        'CHAT': 'Conversa casual/não médica',
        'UNKNOWN': 'Não identificado',
    }
    
    async def classify(self, text: str, context: ConversationContext) -> IntentResult:
        """
        Classifica intenção do texto transcrito.
        
        Retorna:
        {
            "intent": "QUERY_EXAM",
            "confidence": 0.95,
            "parameters": {
                "exam_type": "hemoglobina_glicada",
                "time_range": "last"
            },
            "requires_confirmation": false
        }
        """
        ...
```

### 4.2 Clinical Entity Extractor

```python
@dataclass
class ClinicalEntity:
    entity_type: Literal[
        'SYMPTOM', 'DIAGNOSIS', 'MEDICATION', 'DOSAGE', 
        'ALLERGY', 'EXAM', 'VITAL_SIGN', 'HABIT', 
        'PROCEDURE', 'FAMILY_HISTORY', 'SOCIAL_HISTORY'
    ]
    text: str                    # Texto original falado
    normalized_name: str         # Nome normalizado (ex: "metformina")
    cui: Optional[str]           # UMLS Concept Unique Identifier
    icd10: Optional[str]         # Código CID-10 (se diagnóstico)
    atc: Optional[str]           # Código ATC (se medicação)
    loinc: Optional[str]         # Código LOINC (se exame)
    value: Optional[str]         # Valor (ex: "7,3%" para HbA1c)
    unit: Optional[str]          # Unidade
    temporal: Optional[str]      # "atual", "há 3 meses", "prévio"
    negated: bool = False        # "NÃO tem diabetes"
    confidence: float = 1.0
    source: Literal['patient', 'doctor', 'inferred'] = 'patient'
    start_time_ms: int = 0

class ClinicalEntityExtractor:
    """
    Extrai entidades clínicas da transcrição.
    
    Usa abordagem híbrida:
    1. Modelo NER médico (MedSpaCy / scispaCy) para identificação inicial
    2. LLM para normalização e vinculação a terminologias (UMLS, ICD-10)
    3. Regras para valores numéricos e unidades
    """
    
    def __init__(self):
        self.nlp = spacy.load("pt_core_news_sm")  # Base PT-BR
        self.med_nlp = self._load_medical_ner()   # Modelo médico customizado
        self.umls_linker = UMLSEntityLinker()     # Linkagem a UMLS
    
    async def extract(self, text: str, speaker: str) -> List[ClinicalEntity]:
        """Extrai entidades de um segmento de texto."""
        
        # Passo 1: NER médico
        doc = self.med_nlp(text)
        entities = []
        for ent in doc.ents:
            entity = ClinicalEntity(
                entity_type=self._map_entity_type(ent.label_),
                text=ent.text,
                source='patient' if speaker == 'patient' else 'doctor'
            )
            entities.append(entity)
        
        # Passo 2: LLM para normalização e códigos
        normalized = await self._normalize_with_llm(entities, text)
        
        # Passo 3: Extração de valores numéricos
        values = self._extract_numeric_values(text)
        
        return self._merge_entities(normalized, values)
    
    def _extract_numeric_values(self, text: str) -> List[dict]:
        """Extrai valores numéricos com unidades."""
        # Padrões: "7,3%", "120/80 mmHg", "1,5 mg/dL"
        patterns = [
            r'(\d+[,.]?\d*)\s*(mg/dL|mmHg|kg|cm|%|g|UI|ml)',
            r'(\d+)\s*x\s*(\d+)\s*(comprimidos|cp)',
        ]
        ...
```

### 4.3 Prontuário RAG (Retrieval-Augmented Generation)

```python
class ClinicalRAG:
    """
    Sistema de RAG para consulta ao prontuário do paciente.
    Combina busca vetorial (Qdrant) + busca estruturada (PostgreSQL).
    """
    
    def __init__(self, vector_db: QdrantClient, sql_db: Session):
        self.vector_db = vector_db
        self.sql_db = sql_db
        self.embedding_model = SentenceTransformer('intfloat/multilingual-e5-large')
    
    async def query(self, question: str, patient_id: str, 
                    tenant_id: str) -> ClinicalAnswer:
        """
        Responde perguntas sobre o prontuário do paciente.
        
        Ex: "Qual foi a última hemoglobina glicada?"
        → Busca exames do paciente → Retorna valor + data
        """
        
        # Passo 1: Determinar tipo de informação necessária
        info_type = self._classify_information_need(question)
        
        # Passo 2: Busca estruturada (SQL) para dados tabulares
        if info_type in ['exam', 'medication', 'vital', 'appointment']:
            result = await self._structured_query(info_type, question, patient_id)
        
        # Passo 3: Busca vetorial para documentos/evoluções
        else:
            embedding = self.embedding_model.encode(question)
            result = await self._vector_search(embedding, patient_id, tenant_id)
        
        # Passo 4: Formatar resposta
        return ClinicalAnswer(
            answer=result.text,
            sources=result.sources,
            confidence=result.confidence
        )
    
    async def _structured_query(self, info_type: str, question: str, 
                                patient_id: str) -> StructuredResult:
        """
        Consulta dados estruturados do prontuário.
        Usa NL-to-SQL com LLM + validação.
        """
        
        # Schema do banco para contexto
        schema = self._get_patient_schema()
        
        # Gerar SQL via LLM
        sql = await self._generate_sql(question, schema, patient_id)
        
        # Validar SQL (apenas SELECT, tabelas permitidas)
        if not self._is_safe_sql(sql):
            raise SecurityError("SQL gerado não passou na validação de segurança")
        
        # Executar
        result = self.sql_db.execute(text(sql))
        return self._format_structured_result(result)
```

**Exemplos de queries NL→SQL:**

| Pergunta Natural | SQL Gerado |
|------------------|-----------|
| "Qual foi a última hemoglobina glicada?" | `SELECT valor, data FROM exames WHERE paciente_id = ? AND nome ILIKE '%glicada%' ORDER BY data DESC LIMIT 1` |
| "Quais medicamentos o paciente usa?" | `SELECT nome, dosagem FROM medicamentos WHERE paciente_id = ? AND ativo = true` |
| "Quando foi a última consulta?" | `SELECT data FROM consultas WHERE paciente_id = ? ORDER BY data DESC LIMIT 1` |
| "A creatinina está subindo?" | `SELECT data, valor FROM exames WHERE paciente_id = ? AND nome ILIKE '%creatinina%' ORDER BY data` |

### 4.4 Function Calling — Ações no Sistema

```python
class VoiceActionExecutor:
    """
    Executa ações no sistema ARAOS mediante comando de voz + confirmação.
    
    Todas as ações clínicas exigem confirmação explícita.
    Ações de navegação não exigem confirmação.
    """
    
    # Funções disponíveis para o LLM
    FUNCTIONS = {
        # Navegação (sem confirmação)
        'navigate_to': {
            'description': 'Navegar para uma tela do sistema',
            'parameters': {'screen': 'string'},
            'requires_confirmation': False,
        },
        
        # Ações clínicas (com confirmação)
        'create_prescription': {
            'description': 'Criar prescrição médica',
            'parameters': {
                'patient_id': 'string',
                'medications': [{'name': 'string', 'dosage': 'string', 'frequency': 'string'}],
                'notes': 'string',
            },
            'requires_confirmation': True,
            'clinical_risk': 'high',
        },
        'schedule_exam': {
            'description': 'Solicitar exame laboratorial ou de imagem',
            'parameters': {
                'patient_id': 'string',
                'exam_type': 'string',
                'priority': 'string',
                'notes': 'string',
            },
            'requires_confirmation': True,
            'clinical_risk': 'medium',
        },
        'schedule_return': {
            'description': 'Agendar retorno do paciente',
            'parameters': {
                'patient_id': 'string',
                'days_from_now': 'integer',
                'specialty': 'string',
                'notes': 'string',
            },
            'requires_confirmation': True,
            'clinical_risk': 'low',
        },
        'add_allergy': {
            'description': 'Registrar alergia do paciente',
            'parameters': {
                'patient_id': 'string',
                'allergen': 'string',
                'reaction': 'string',
                'severity': 'string',
            },
            'requires_confirmation': True,
            'clinical_risk': 'high',
        },
        'add_diagnosis': {
            'description': 'Adicionar diagnóstico ao prontuário',
            'parameters': {
                'patient_id': 'string',
                'diagnosis': 'string',
                'icd10_code': 'string',
                'status': 'string',  # active, resolved, chronic
                'notes': 'string',
            },
            'requires_confirmation': True,
            'clinical_risk': 'high',
        },
        'generate_evolution': {
            'description': 'Gerar evolução clínica da consulta',
            'parameters': {
                'patient_id': 'string',
                'consultation_id': 'string',
                'content': 'string',  # pré-gerado pela IA
            },
            'requires_confirmation': True,
            'clinical_risk': 'high',
        },
        'send_notification': {
            'description': 'Enviar notificação ao paciente via WhatsApp/email',
            'parameters': {
                'patient_id': 'string',
                'channel': 'string',  # whatsapp, email, sms
                'message': 'string',
            },
            'requires_confirmation': True,
            'clinical_risk': 'low',
        },
    }
    
    async def execute(self, action: VoiceAction) -> ActionResult:
        """
        Executa uma ação após validação e confirmação.
        """
        func = self.FUNCTIONS.get(action.function_name)
        if not func:
            return ActionResult.error(f"Função desconhecida: {action.function_name}")
        
        # Validar parâmetros
        validation = self._validate_parameters(action.parameters, func['parameters'])
        if not validation.valid:
            return ActionResult.error(f"Parâmetros inválidos: {validation.errors}")
        
        # Verificar se requer confirmação
        if func.get('requires_confirmation', True):
            # Enviar proposta de ação para o médico confirmar
            return ActionResult.pending_confirmation(
                action_id=action.id,
                preview=self._generate_preview(action),
                timeout=30
            )
        
        # Executar diretamente (navegação, etc.)
        return await self._execute_action(action)
```

### 4.5 Assistência Contextual

```python
class ContextualAssistant:
    """
    Monitora a conversa em tempo real e sugere informações relevantes.
    Sugestões são discretas — não interrompem o médico.
    """
    
    async def monitor(self, segment: ConversationSegment, 
                      patient_context: PatientContext) -> List[Suggestion]:
        """
        Analisa segmento de conversa e gera sugestões contextuais.
        """
        suggestions = []
        
        # Trigger 1: Menção a exame com tendência
        if self._mentions_exam(segment.text):
            exam_name = self._extract_exam_name(segment.text)
            trend = await self._get_exam_trend(patient_context.id, exam_name)
            if trend and len(trend.values) >= 2:
                suggestions.append(Suggestion(
                    type='trend',
                    title=f'Tendência: {exam_name}',
                    content=self._format_trend(trend),
                    priority='medium',
                    data={'exam': exam_name, 'values': trend.values}
                ))
        
        # Trigger 2: Menção a sintoma com escala anterior
        if self._mentions_symptom(segment.text):
            symptom = self._extract_symptom(segment.text)
            previous_scale = await self._get_previous_scale(
                patient_context.id, symptom
            )
            if previous_scale:
                suggestions.append(Suggestion(
                    type='trend',
                    title=f'Evolução: {symptom}',
                    content=f"{symptom}: {previous_scale.comparison}",
                    priority='low'
                ))
        
        # Trigger 3: Medicação mencionada com interação
        if self._mentions_medication(segment.text):
            meds = self._extract_medications(segment.text)
            interactions = await self._check_interactions(
                meds, patient_context.active_medications
            )
            if interactions:
                suggestions.append(Suggestion(
                    type='alert',
                    title='Interação medicamentosa detectada',
                    content=interactions.description,
                    priority='high',
                    data={'interactions': interactions.list}
                ))
        
        # Trigger 4: Diagnóstico mencionado com guideline
        if self._mentions_diagnosis(segment.text):
            diagnosis = self._extract_diagnosis(segment.text)
            guideline = await self._get_guideline(diagnosis, patient_context.specialty)
            if guideline:
                suggestions.append(Suggestion(
                    type='reference',
                    title=f'Guideline: {diagnosis}',
                    content=guideline.summary,
                    priority='low',
                    data={'guideline_id': guideline.id}
                ))
        
        return suggestions
```

---

## 5. Modelo de Dados

### 5.1 voice_sessions

```sql
CREATE TABLE voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    patient_id UUID NOT NULL REFERENCES patients(id),
    doctor_id UUID NOT NULL REFERENCES users(id),
    
    -- Metadados da sessão
    specialty VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_seconds INT,
    
    -- Configurações
    wake_word VARCHAR(50) DEFAULT 'Ara',
    language VARCHAR(10) DEFAULT 'pt-BR',
    mode VARCHAR(20) DEFAULT 'full',  -- full, transcription_only, command_only
    
    -- Estado
    status VARCHAR(20) DEFAULT 'active',  -- active, paused, completed, error
    
    -- Métricas
    total_audio_duration_ms INT DEFAULT 0,
    speech_duration_ms INT DEFAULT 0,
    doctor_speech_duration_ms INT DEFAULT 0,
    patient_speech_duration_ms INT DEFAULT 0,
    
    -- Estruturação final
    structured_data JSONB,  -- entidades extraídas, resumo, evolução
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_voice_sessions_patient ON voice_sessions(patient_id, started_at DESC);
CREATE INDEX idx_voice_sessions_tenant ON voice_sessions(tenant_id, started_at DESC);
```

### 5.2 voice_transcripts

```sql
CREATE TABLE voice_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
    
    -- Segmento
    segment_index INT NOT NULL,
    speaker VARCHAR(20) NOT NULL,  -- doctor, patient, unknown
    
    -- Timing
    start_time_ms INT NOT NULL,
    end_time_ms INT NOT NULL,
    
    -- Conteúdo
    text TEXT NOT NULL,
    text_normalized TEXT,  -- texto normalizado (minúsculas, sem acentos)
    
    -- Qualidade
    confidence FLOAT,
    is_final BOOLEAN DEFAULT TRUE,
    
    -- Metadados
    language VARCHAR(10) DEFAULT 'pt-BR',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(session_id, segment_index)
);

CREATE INDEX idx_voice_transcripts_session ON voice_transcripts(session_id, segment_index);
```

### 5.3 voice_entities

```sql
CREATE TABLE voice_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
    transcript_id UUID REFERENCES voice_transcripts(id),
    
    -- Entidade
    entity_type VARCHAR(30) NOT NULL,  -- symptom, diagnosis, medication, etc.
    text TEXT NOT NULL,  -- texto original
    normalized_name VARCHAR(255),  -- nome normalizado
    
    -- Códigos
    cui VARCHAR(20),  -- UMLS
    icd10 VARCHAR(20),
    atc VARCHAR(20),
    loinc VARCHAR(20),
    
    -- Valor (se aplicável)
    value TEXT,
    unit VARCHAR(50),
    
    -- Contexto
    temporal VARCHAR(50),  -- current, past, family
    negated BOOLEAN DEFAULT FALSE,
    confidence FLOAT,
    source VARCHAR(20) DEFAULT 'patient',  -- patient, doctor, inferred
    
    -- Timing
    start_time_ms INT,
    end_time_ms INT,
    
    -- Persistência no prontuário
    persisted_to_ehr BOOLEAN DEFAULT FALSE,
    persisted_record_id UUID,  -- ID do registro no prontuário
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_voice_entities_session ON voice_entities(session_id, entity_type);
CREATE INDEX idx_voice_entities_patient ON voice_entities(patient_id, entity_type);
```

### 5.4 voice_actions

```sql
CREATE TABLE voice_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
    
    -- Ação
    action_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    
    -- Parâmetros
    parameters JSONB NOT NULL DEFAULT '{}',
    preview JSONB,  -- preview gerado para confirmação
    
    -- Estado
    status VARCHAR(20) DEFAULT 'proposed',  -- proposed, confirmed, rejected, executed, failed
    
    -- Confirmação
    confirmed_by UUID REFERENCES users(id),
    confirmed_at TIMESTAMPTZ,
    confirmation_method VARCHAR(20),  -- voice, button, timeout
    
    -- Execução
    executed_at TIMESTAMPTZ,
    result JSONB,  -- resultado da execução
    error_message TEXT,
    
    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5.5 voice_audit_log

```sql
CREATE TABLE voice_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES voice_sessions(id) ON DELETE CASCADE,
    
    -- Evento
    event_type VARCHAR(50) NOT NULL,  -- wake_word, transcription, intent, action, error
    event_data JSONB,
    
    -- Contexto
    doctor_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    
    -- Timestamp
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- IP e device (para segurança)
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX idx_voice_audit_session ON voice_audit_log(session_id, occurred_at);
```

---

## 6. Fluxos de Interação Detalhados

### 6.1 Fluxo Completo: Consulta com ARAOS Voice

```
┌─────────────────────────────────────────────────────────────────────────┐
│  TEMPO    │  MÉDICO              │  PACIENTE          │  SISTEMA        │
├─────────────────────────────────────────────────────────────────────────┤
│  T+0s     │  Entra na sala       │  Já está sentado   │  [IDLE]         │
│           │                      │                    │  LED verde      │
├─────────────────────────────────────────────────────────────────────────┤
│  T+5s     │  "Ok Ara, iniciar    │                    │  [LISTENING]    │
│           │   consulta"          │                    │  LED azul       │
├─────────────────────────────────────────────────────────────────────────┤
│  T+8s     │                      │  "Doutor, a dor    │  • Transcreve   │
│           │                      │   melhorou"        │  • Extrai:      │
│           │                      │                    │    entity:      │
│           │                      │                    │    symptom:     │
│           │                      │                    │    "dor"        │
├─────────────────────────────────────────────────────────────────────────┤
│  T+10s    │  "Ara, mostrar       │                    │  [PROCESSING]   │
│           │   evolução da dor"   │                    │  LED amarelo    │
├─────────────────────────────────────────────────────────────────────────┤
│  T+12s    │                      │                    │  SUGESTÃO:      │
│           │                      │                    │  "Escala de dor:│
│           │                      │                    │   8→6→4 nos     │
│           │                      │                    │   últimos 3     │
│           │                      │                    │   meses"        │
├─────────────────────────────────────────────────────────────────────────┤
│  T+15s    │  "Ara, qual foi a    │                    │  [PROCESSING]   │
│           │   última creatinina?"│                    │                 │
├─────────────────────────────────────────────────────────────────────────┤
│  T+17s    │                      │                    │  TTS:           │
│           │                      │                    │  "Última        │
│           │                      │                    │   creatinina:   │
│           │                      │                    │   1,8 mg/dL em  │
│           │                      │                    │   15/05/2026"   │
│           │                      │                    │  LED verde      │
├─────────────────────────────────────────────────────────────────────────┤
│  T+25s    │  "Vamos solicitar    │                    │  [PROCESSING]   │
│           │   hemograma"         │                    │                 │
├─────────────────────────────────────────────────────────────────────────┤
│  T+27s    │                      │                    │  PROPOSTA:      │
│           │                      │                    │  "Solicitar     │
│           │                      │                    │   hemograma     │
│           │                      │                    │   completo?"    │
│           │                      │                    │  [botões: Sim/  │
│           │                      │                    │   Não/Editar]   │
├─────────────────────────────────────────────────────────────────────────┤
│  T+30s    │  "Sim"               │                    │  [EXECUTING]    │
├─────────────────────────────────────────────────────────────────────────┤
│  T+32s    │                      │                    │  TTS:           │
│           │                      │                    │  "Hemograma     │
│           │                      │                    │   solicitado.   │
│           │                      │                    │   Protocolo     │
│           │                      │                    │   #12345"       │
├─────────────────────────────────────────────────────────────────────────┤
│  ...      │  Consulta continua   │                    │  • Continua     │
│           │  normalmente         │                    │    extraindo    │
│           │                      │                    │    entidades    │
├─────────────────────────────────────────────────────────────────────────┤
│  T+45min  │  "Ara, encerrar      │                    │  [PROCESSING]   │
│           │   consulta"          │                    │                 │
├─────────────────────────────────────────────────────────────────────────┤
│  T+45:05  │                      │                    │  GERA:          │
│           │                      │                    │  • Evolução     │
│           │                      │                    │    estruturada  │
│           │                      │                    │  • Resumo       │
│           │                      │                    │    clínico      │
│           │                      │                    │  • Lista de     │
│           │                      │                    │    entidades    │
├─────────────────────────────────────────────────────────────────────────┤
│  T+45:10  │                      │                    │  PROPOSTA:      │
│           │                      │                    │  "Gerar         │
│           │                      │                    │   evolução e    │
│           │                      │                    │   prescrição?"  │
├─────────────────────────────────────────────────────────────────────────┤
│  T+45:15  │  "Sim, e agendar     │                    │  [EXECUTING]    │
│           │   retorno em 90 dias"│                    │                 │
├─────────────────────────────────────────────────────────────────────────┤
│  T+45:20  │                      │                    │  • Evolução     │
│           │                      │                    │    salva        │
│           │                      │                    │  • Prescrição   │
│           │                      │                    │    gerada       │
│           │                      │                    │  • Retorno      │
│           │                      │                    │    agendado     │
│           │                      │                    │  • Notificação  │
│           │                      │                    │    enviada      │
│           │                      │                    │  [COMPLETED]    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Diagrama de Estado da Sessão

```
                    ┌─────────┐
                    │  IDLE   │◄─────────────────────────────────────┐
                    └────┬────┘                                      │
              wake_word │                                           │
                         ▼                                          │
                   ┌───────────┐     timeout (10s)                 │
         ┌────────►│ LISTENING │───────────────────────────────────┘
         │         └─────┬─────┘
         │    fala       │
         │   detectada   ▼
         │         ┌───────────┐     sem comando
         │         │PROCESSING │────────────────────────────────────►
         │         └─────┬─────┘
         │    comando    │ identificado
         │   identificado▼
         │         ┌───────────┐
         │         │RESPONDING │
         │         └─────┬─────┘
         │    ação       │ requer
         │   proposta    │ confirmação
         │               ▼
         │         ┌─────────────────┐    timeout (30s)
         │         │WAIT_CONFIRMATION│────────────────────────────────►
         │         └────────┬────────┘
         │    confirmação   │
         │                  ▼
         │         ┌───────────┐
         │         │EXECUTING  │
         │         └─────┬─────┘
         │    execução   │
         │   concluída   │
         │               ▼
         └───────────────┘
```

---

## 7. Segurança e Compliance

### 7.1 Princípios de Segurança

| Princípio | Implementação |
|-----------|--------------|
| **Human-in-the-loop** | Toda ação clínica exige confirmação explícita do médico |
| **Auditabilidade total** | Todo áudio, transcrição, comando e ação é logado |
| **Imutabilidade** | Áudio original é armazenado sem modificação |
| **Controle do médico** | Médico pode pausar, cancelar ou editar qualquer output |
| **Privacidade** | Dados de áudio não são usados para treinamento sem consentimento |

### 7.2 LGPD — Considerações Específicas

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CHECKLIST LGPD — ARAOS VOICE                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [x] Base legal: Execução de contrato (prestação de serviço médico)  │
│  [x] Consentimento específico para gravação de áudio                 │
│  [x] Finalidade clara: assistência à consulta e documentação        │
│  [x] Adequação: necessária para o serviço contratado                │
│  [x] Necessidade: minimização (apenas áudio da consulta)            │
│  [x] Livre acesso: médico pode acessar gravações                    │
│  [x] Correção: transcrições editáveis pelo médico                   │
│  [x] Eliminação: áudio apagado após prazo legal (mínimo 20 anos     │
│      para prontuário médico, conforme Resolução CFM 1.638/2002)     │
│  [x] Portabilidade: exportação em formato aberto                    │
│  [x] Informação: paciente informado sobre gravação                  │
│  [x] Revisão automática: política de retenção com deleção automática │
│                                                                       │
│  ADICIONAL:                                                           │
│  [ ] DPO deve avaliar se biometria de voz é dado sensível (LGPD)    │
│  [ ] Termo de consentimento separado para uso de IA na consulta     │
│  [ ] Opção de consulta sem gravação (modo apenas transcrição)       │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 7.3 Armazenamento de Áudio

| Aspecto | Política |
|---------|----------|
| **Formato** | PCM 16kHz mono (original) + OGG Opus (compactado) |
| **Localização** | MinIO/S3 com criptografia AES-256 |
| **Retenção** | 20 anos (prontuário médico) ou conforme política do tenant |
| **Acesso** | Apenas médico responsável + administradores autorizados |
| **Anonimização** | Áudio NÃO é anonimizado (identifica voz do paciente) |
| **Consentimento** | Paciente deve consentir explicitamente antes da gravação |

---

## 8. Roadmap de Implementação

### 8.1 Fase 1: Fundação (Semanas 1-3)

**Entregáveis:**
- [ ] Refatorar `live_audio_server.py` para arquitetura modular
- [ ] Implementar WebSocket server com Session Manager
- [ ] Integrar Whisper streaming para STT
- [ ] Implementar VAD (Silero)
- [ ] Criar modelo de dados (PostgreSQL)
- [ ] Widget frontend básico (microfone + visualização)

**Demo:** Médico fala → sistema transcreve em tempo real

### 8.2 Fase 2: Wake Word e Diarização (Semanas 4-5)

**Entregáveis:**
- [ ] Integrar Porcupine para wake word
- [ ] Implementar speaker diarization (pyannote)
- [ ] Distinguir médico vs paciente na transcrição
- [ ] Buffer de conversação com contexto
- [ ] Estado IDLE → LISTENING → PROCESSING

**Demo:** "Ok Ara, qual foi a última consulta?" → sistema responde

### 8.3 Fase 3: Copilot e RAG (Semanas 6-8)

**Entregáveis:**
- [ ] Intent classifier com LLM
- [ ] Clinical entity extractor
- [ ] Prontuário RAG (busca em exames, medicamentos, histórico)
- [ ] Integração com CORE API
- [ ] Respostas em áudio (TTS via Gemini Live)

**Demo:** Médico pergunta sobre exame → sistema consulta prontuário → responde com valor

### 8.4 Fase 4: Ações e Confirmação (Semanas 9-10)

**Entregáveis:**
- [ ] Function calling para ações do sistema
- [ ] Sistema de confirmação (voz + visual)
- [ ] Navegação por voz (abrir telas)
- [ ] Execução de prescrições, solicitações, agendamentos

**Demo:** "Ara, solicitar hemograma" → sistema propõe → médico confirma → executa

### 8.5 Fase 5: Estruturação e Assistência (Semanas 11-12)

**Entregáveis:**
- [ ] Extração automática de entidades durante consulta
- [ ] Sugestões contextuais discretas
- [ ] Geração automática de evolução
- [ ] Resumo clínico ao encerrar
- [ ] Memória longitudinal integrada

**Demo:** Consulta completa com estruturação automática e evolução gerada

### 8.6 Fase 6: Polish e Compliance (Semanas 13-14)

**Entregáveis:**
- [ ] Audit log completo
- [ ] Consentimento do paciente ( pré-consulta)
- [ ] Testes de segurança
- [ ] Documentação
- [ ] Performance tuning (latência < 2s para respostas)

---

## 9. Métricas de Sucesso

| Métrica | Target Fase 3 | Target Fase 6 |
|---------|--------------|---------------|
| **Latência STT** | < 3s (streaming) | < 1.5s (streaming) |
| **Latência resposta** | < 5s | < 2s |
| **Precisão transcrição médica** | 85% WER | 90% WER |
| **Precisão intent classification** | 90% | 95% |
| **Precisão entity extraction** | 80% F1 | 90% F1 |
| **Taxa de confirmação de ações** | — | > 95% (médico confirma) |
| **Tempo economizado por consulta** | — | 5-10 minutos |
| **Satisfação do médico** | — | NPS > 50 |

---

## 10. Diagrama de Deploy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         VPS / Kubernetes                                 │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  siap-voice (Novo Container)                                     │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                │   │
│  │  │ WebSocket  │  │  STT       │  │  Copilot   │                │   │
│  │  │ Server     │  │  Engine    │  │  Engine    │                │   │
│  │  │ (FastAPI)  │  │  (Whisper) │  │  (Gemini)  │                │   │
│  │  │ Port 8765  │  │            │  │            │                │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                │   │
│  │        │               │               │                        │   │
│  │        └───────────────┼───────────────┘                        │   │
│  │                        │                                        │   │
│  │                   ┌────┴────┐                                   │   │
│  │                   │ Redis   │ (session state, buffers)          │   │
│  │                   │ (6379)  │                                   │   │
│  │                   └────┬────┘                                   │   │
│  └────────────────────────┼────────────────────────────────────────┘   │
│                           │                                            │
│  ┌────────────────────────┼────────────────────────────────────────┐   │
│  │  siap-backend          │                                        │   │
│  │  ┌─────────────────────┴────────────────────────────────────┐   │   │
│  │  │  CORE API (Pacientes, Exames, Prescrições, etc.)        │   │   │
│  │  └─────────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                           │                                            │
│  ┌────────────────────────┼────────────────────────────────────────┐   │
│  │  siap-db               ▼                                        │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐               │   │
│  │  │ PostgreSQL │  │ Qdrant     │  │ MinIO      │               │   │
│  │  │ (dados)    │  │ (vetores)  │  │ (áudio)    │               │   │
│  │  └────────────┘  └────────────┘  └────────────┘               │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  Traefik: wss://voice.aracannabis.com.br → siap-voice:8765           │
└────────────────────────────────────────────────────────────────────────┘
```

---

*Especificação baseada na fundação existente (`live_audio_server.py`) e expandida para atender à visão completa de Copiloto Clínico Multimodal.*
