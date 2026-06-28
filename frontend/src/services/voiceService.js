/**
 * Serviço de comunicação com ARAOS Voice Server.
 * Gerencia WebSocket, estados e callbacks.
 */

const VOICE_CONFIG = {
  WS_BASE_URL: process.env.REACT_APP_VOICE_WS_URL || 'ws://localhost:8765',
  HTTP_BASE_URL: process.env.REACT_APP_VOICE_HTTP_URL || 'http://localhost:8765',
  RECONNECT_INTERVAL: 3000,
  MAX_RECONNECT_ATTEMPTS: 5,
};

class VoiceService {
  constructor() {
    this.ws = null;
    this.sessionId = null;
    this.state = 'disconnected'; // disconnected, connecting, idle, listening, processing, responding, error
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    
    // Callbacks
    this.onStateChange = null;
    this.onTranscription = null;
    this.onEntity = null;
    this.onSuggestion = null;
    this.onActionProposal = null;
    this.onActionResult = null;
    this.onTTSAudio = null;
    this.onError = null;
    
    // Buffer de áudio
    this.audioContext = null;
    this.mediaStream = null;
    this.mediaRecorder = null;
    this.audioQueue = [];
  }

  /**
   * Inicializa conexão WebSocket com o servidor de voz.
   */
  async connect({
    tenantId,
    patientId,
    doctorId,
    specialty = 'general',
    wakeWord = 'Ara',
    language = 'pt-BR',
    mode = 'full',
  }) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      if(process.env.NODE_ENV!=='production')console.warn('[Voice] Already connected');
      return;
    }

    this._setState('connecting');

    const wsUrl = new URL(`${VOICE_CONFIG.WS_BASE_URL}/ws/voice`);
    wsUrl.searchParams.set('tenant_id', tenantId);
    wsUrl.searchParams.set('patient_id', patientId);
    wsUrl.searchParams.set('doctor_id', doctorId);
    wsUrl.searchParams.set('specialty', specialty);
    wsUrl.searchParams.set('wake_word', wakeWord);
    wsUrl.searchParams.set('language', language);
    wsUrl.searchParams.set('mode', mode);

    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(wsUrl.toString());

      this.ws.onopen = () => {
        if(process.env.NODE_ENV!=='production')console.log('[Voice] WebSocket connected');
        this.reconnectAttempts = 0;
        this._setState('idle');
        resolve();
      };

      this.ws.onmessage = (event) => {
        this._handleMessage(JSON.parse(event.data));
      };

      this.ws.onerror = (error) => {
        if(process.env.NODE_ENV!=='production')console.error('[Voice] WebSocket error:', error);
        this._setState('error');
        if (this.onError) this.onError('Connection error');
        reject(error);
      };

      this.ws.onclose = () => {
        if(process.env.NODE_ENV!=='production')console.log('[Voice] WebSocket closed');
        this._setState('disconnected');
        this._attemptReconnect({
          tenantId, patientId, doctorId, specialty, wakeWord, language, mode,
        });
      };
    });
  }

  /**
   * Desconecta do servidor de voz.
   */
  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this._stopRecording();
    this._setState('disconnected');
  }

  /**
   * Inicia captura de áudio do microfone.
   */
  async startRecording() {
    if (this.state !== 'idle' && this.state !== 'listening') {
      if(process.env.NODE_ENV!=='production')console.warn(`[Voice] Cannot start recording in state: ${this.state}`);
      return;
    }

    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      this.audioContext = new AudioContext({ sampleRate: 16000 });
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

      source.connect(processor);
      processor.connect(this.audioContext.destination);

      processor.onaudioprocess = (event) => {
        if (this.ws?.readyState !== WebSocket.OPEN) return;

        const inputData = event.inputBuffer.getChannelData(0);
        const pcmData = this._float32ToInt16(inputData);
        this.ws.send(pcmData.buffer);
      };

      this._processor = processor;
      this._setState('listening');
      if(process.env.NODE_ENV!=='production')console.log('[Voice] Recording started');

    } catch (error) {
      if(process.env.NODE_ENV!=='production')console.error('[Voice] Failed to start recording:', error);
      this._setState('error');
      if (this.onError) this.onError('Microphone access denied');
    }
  }

  /**
   * Para captura de áudio.
   */
  stopRecording() {
    this._stopRecording();
    if (this.ws?.readyState === WebSocket.OPEN) {
      this._sendCommand('stop_recording');
    }
    this._setState('idle');
    if(process.env.NODE_ENV!=='production')console.log('[Voice] Recording stopped');
  }

  /**
   * Envia comando para o servidor.
   */
  sendCommand(action, payload = {}) {
    this._sendMessage('command', { action, ...payload });
  }

  /**
   * Confirma ou rejeita uma ação proposta.
   */
  confirmAction(actionId, confirmed, modified = null) {
    this._sendMessage('confirmation', {
      action_id: actionId,
      confirmed,
      modified,
    });
  }

  /**
   * Finaliza a sessão de voz.
   */
  endSession() {
    this._sendCommand('end_session');
    this.disconnect();
  }

  // ─── Private Methods ─────────────────────────────────────────────────

  _setState(newState) {
    const oldState = this.state;
    this.state = newState;
    if (this.onStateChange) {
      this.onStateChange(oldState, newState);
    }
  }

  _handleMessage(message) {
    const { type, payload } = message;

    switch (type) {
      case 'state_change':
        this._setState(payload.current_state);
        break;

      case 'transcription':
        if (this.onTranscription) this.onTranscription(payload);
        break;

      case 'entity':
        if (this.onEntity) this.onEntity(payload);
        break;

      case 'suggestion':
        if (this.onSuggestion) this.onSuggestion(payload);
        break;

      case 'action_proposal':
        if (this.onActionProposal) this.onActionProposal(payload);
        break;

      case 'action_result':
        if (this.onActionResult) this.onActionResult(payload);
        break;

      case 'tts_audio':
        if (this.onTTSAudio) this.onTTSAudio(payload);
        break;

      case 'error':
        if(process.env.NODE_ENV!=='production')console.error('[Voice] Server error:', payload.message);
        if (this.onError) this.onError(payload.message);
        break;

      default:
        if(process.env.NODE_ENV!=='production')console.log('[Voice] Unknown message type:', type, payload);
    }
  }

  _sendMessage(type, payload) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload, timestamp: Date.now() }));
    }
  }

  _sendCommand(action) {
    this._sendMessage('command', { action });
  }

  _stopRecording() {
    if (this._processor) {
      this._processor.disconnect();
      this._processor = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    if (this.audioContext) {
      this.audioContext.close();
      this.audioContext = null;
    }
  }

  _float32ToInt16(float32Array) {
    const int16Array = new Int16Array(float32Array.length);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      int16Array[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return int16Array;
  }

  _attemptReconnect(config) {
    if (this.reconnectAttempts >= VOICE_CONFIG.MAX_RECONNECT_ATTEMPTS) {
      if(process.env.NODE_ENV!=='production')console.error('[Voice] Max reconnect attempts reached');
      if (this.onError) this.onError('Connection lost. Please refresh.');
      return;
    }

    this.reconnectAttempts++;
    if(process.env.NODE_ENV!=='production')console.log(`[Voice] Reconnecting in ${VOICE_CONFIG.RECONNECT_INTERVAL}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect(config).catch(() => {
        // Falha silenciosa, próxima tentativa será agendada pelo onclose
      });
    }, VOICE_CONFIG.RECONNECT_INTERVAL);
  }
}

// Singleton
const voiceService = new VoiceService();
export default voiceService;
