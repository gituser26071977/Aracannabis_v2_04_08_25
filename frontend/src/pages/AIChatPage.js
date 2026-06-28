import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Paper,
  Alert,
  Grid,
  CircularProgress,
  IconButton
} from '@mui/material';
import { Chat, Send, SmartToy, Mic, StopCircle, VolumeUp, PhoneInTalk, PhoneDisabled } from '@mui/icons-material';
import { chatSimplesService, pacientesService } from '../services/api';
import ContextualTip from '../components/ContextualTip';

const CHAT_QUICK_ACTIONS = [
  {
    id: 'report',
    icon: '📄',
    title: 'Relatórios',
    description: 'Gerar PDF com observações e enviar por email',
    intent: 'report_request',
    prompt: 'Preciso de um relatório com evolução clínica, exames e recomendações.',
    metadata: {
      entrypoint: 'quick_action',
      type: 'report',
      scope: 'completo'
    }
  },
  {
    id: 'insights',
    icon: '💡',
    title: 'Insights rápidos',
    description: 'Análises em segundos com base nos dados do cultivo',
    intent: 'insight_request',
    prompt: 'Liste os principais insights que posso usar hoje para este paciente.',
    metadata: { entrypoint: 'quick_action', type: 'insights' }
  },
  {
    id: 'dashboard',
    icon: '📊',
    title: 'Dashboards vivos',
    description: 'Atualizar gráficos e preparar apresentação',
    intent: 'dashboard_request',
    prompt: 'Atualize os dashboards do paciente e destaque o que mudou.',
    metadata: { entrypoint: 'quick_action', type: 'dashboards' }
  }
];

const formatTimestamp = (timestamp) =>
  new Date(timestamp).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  });

const createAssistantMessage = (content) => ({
  id: `assistant-${Date.now()}`,
  role: 'assistant',
  content,
  timestamp: new Date().toISOString(),
  status: 'done'
});

const AIChatPage = () => {
  const [messages, setMessages] = useState(() => [
    createAssistantMessage('Olá! Revisei a agenda e os registros recentes. Como posso ajudar hoje?')
  ]);
  const [inputValue, setInputValue] = useState('');
  const [pacienteId, setPacienteId] = useState('');
  const [pacientes, setPacientes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeQuickAction, setActiveQuickAction] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [playingTTSId, setPlayingTTSId] = useState(null);

  // States and Refs for Full-Duplex Live Call
  const [isLiveCallActive, setIsLiveCallActive] = useState(false);
  const liveAudioWsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const processorRef = useRef(null);
  const streamRef = useRef(null);
  const nextPlayTimeRef = useRef(0);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatListRef = useRef(null);

  useEffect(() => {
    const carregarPacientes = async () => {
      try {
        const resp = await pacientesService.listar();
        setPacientes(resp?.pacientes || []);
      } catch (err) {
        setError('Não foi possível carregar os pacientes para o chat.');
      }
    };
    carregarPacientes();
  }, []);

  const scrollToBottom = () => {
    if (chatListRef.current) {
      chatListRef.current.scrollTo({
        top: chatListRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const appendMessage = (message) => {
    setMessages((prev) => [...prev, message]);
  };

  const updateMessage = (id, patch) => {
    setMessages((prev) =>
      prev.map((message) => (message.id === id ? { ...message, ...patch } : message))
    );
  };

  const clearHistory = () => {
    setMessages([createAssistantMessage('Olá novamente! Como posso ajudar agora?')]);
    setError('');
    setInputValue('');
    setActiveQuickAction(null);
  };

  const toggleLiveCall = async () => {
    if (isLiveCallActive) {
      // Desconectar o túnel
      if (liveAudioWsRef.current) {
        liveAudioWsRef.current.close();
      }
      if (processorRef.current) {
        processorRef.current.disconnect();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioCtxRef.current) {
        audioCtxRef.current.close();
      }
      setIsLiveCallActive(false);
      return;
    }

    try {
      // 1. Configurar o Microfone para Áudio Mono em 16kHz (padrão do Gemini)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 16000 } });
      streamRef.current = stream;

      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      audioCtxRef.current = audioCtx;
      nextPlayTimeRef.current = 0;

      const source = audioCtx.createMediaStreamSource(stream);
      // Processor minúsculo para capturar áudio continuamente (4096 frames por chunk)
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      // 2. Conectar no Backend Gateway (WebSocket)
      const wsUrl = process.env.REACT_APP_VOICE_WS_URL
        || (window.location.protocol === 'https:' ? 'wss://api.aracannabis.local/ws/voice' : 'ws://localhost:8765');
      const ws = new WebSocket(wsUrl);
      liveAudioWsRef.current = ws;

      ws.onopen = () => {
        setIsLiveCallActive(true);
        // Mandar o "Alô" inicial invisível pro Gemini começar a falar
        ws.send(JSON.stringify({ client_content: "Iniciei a chamada. Diga um 'Olá, doutor, o Copiloto de voz está ativado.'" }));
      };

      // 3. Ao falar no microfone: Transformar Float32 em PCM 16-bits e enviar pro WS
      processor.onaudioprocess = (e) => {
        if (ws.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          const pcm16 = new Int16Array(inputData.length);
          for (let i = 0; i < inputData.length; i++) {
            let s = Math.max(-1, Math.min(1, inputData[i]));
            pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          ws.send(pcm16.buffer); // Envia binário cru
        }
      };

      // 4. Ao ouvir reposta do Gemini via WS: Transformar PCM 16-bits em Som e colocar no Speaker
      ws.onmessage = async (event) => {
        if (event.data instanceof Blob) {
          const arrayBuffer = await event.data.arrayBuffer();
          const pcm16 = new Int16Array(arrayBuffer);
          const float32 = new Float32Array(pcm16.length);
          for (let i = 0; i < pcm16.length; i++) {
            float32[i] = pcm16[i] / 32768.0;
          }

          const audioBuffer = audioCtx.createBuffer(1, float32.length, 16000);
          audioBuffer.copyToChannel(float32, 0);

          const sourceNode = audioCtx.createBufferSource();
          sourceNode.buffer = audioBuffer;
          sourceNode.connect(audioCtx.destination);

          // Tocar o som engatado no próximo segundo livre para não cortar as palavras (Buffer Scheduling)
          if (nextPlayTimeRef.current < audioCtx.currentTime) {
            nextPlayTimeRef.current = audioCtx.currentTime;
          }
          sourceNode.start(nextPlayTimeRef.current);
          nextPlayTimeRef.current += audioBuffer.duration;

        } else if (typeof event.data === 'string') {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'text' && data.text) {
              appendMessage(createAssistantMessage('📞 (Live): ' + data.text));
              // Scroll to bottom
              setTimeout(scrollToBottom, 100);
            }
          } catch (e) { }
        }
      };

      ws.onclose = () => {
        setIsLiveCallActive(false);
        if (processorRef.current) processorRef.current.disconnect();
        if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop());
      };

      // Iniciar a esteira
      source.connect(processor);
      processor.connect(audioCtx.destination);

    } catch (err) {
      setError('Erro ao iniciar Assistente de Voz: ' + err.message);
    }
  };

  const startRecording = async () => {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
          setLoading(true);
          try {
            const base64Audio = reader.result;
            const resp = await chatSimplesService.stt(base64Audio);
            if (resp && resp.text) {
              setInputValue((prev) => prev ? prev + ' ' + resp.text : resp.text);
            }
          } catch (err) {
            setError(err?.error || 'Erro ao transcrever áudio.');
          } finally {
            setLoading(false);
          }
        };
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      setError('Acesso ao microfone negado ou não suportado no seu navegador.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleTTS = async (message) => {
    if (playingTTSId === message.id) return;
    setPlayingTTSId(message.id);
    try {
      const resp = await chatSimplesService.tts(message.content);
      if (resp && resp.audio_base64) {
        const audio = new Audio(resp.audio_base64);
        audio.play();
        audio.onended = () => setPlayingTTSId(null);
        audio.onerror = () => {
          setError('Erro ao reproduzir o áudio fornecido.');
          setPlayingTTSId(null);
        }
      }
    } catch (err) {
      setError(err?.error || 'Erro na síntese de voz (TTS).');
      setPlayingTTSId(null);
    }
  };

  const handleSend = async (forcedMessage = null, contextExtras = {}) => {
    const trimmed =
      typeof forcedMessage === 'string' ? forcedMessage.trim() : inputValue.trim();
    if (!trimmed) return;

    setError('');
    setLoading(true);
    const timestamp = new Date().toISOString();
    const userMessage = {
      id: `user-${timestamp}`,
      role: 'user',
      content: trimmed,
      timestamp,
      status: 'done'
    };
    appendMessage(userMessage);

    const placeholderId = `assistant-${timestamp}`;
    appendMessage({
      id: placeholderId,
      role: 'assistant',
      content: 'Pensando...',
      timestamp,
      status: 'pending'
    });

    try {
      const resp = await chatSimplesService.chat({
        mensagem: trimmed,
        paciente_id: pacienteId || null
      });

      const assistantContent = resp?.resposta ?? 'Assistente não respondeu.';
      updateMessage(placeholderId, {
        content: assistantContent,
        status: 'done',
        timestamp: new Date().toISOString()
      });
    } catch (err) {
      const message = err?.error || 'Erro ao conversar com o assistente.';
      updateMessage(placeholderId, {
        content: message,
        status: 'error'
      });
      setError(message);
    } finally {
      setLoading(false);
      if (!forcedMessage) {
        setInputValue('');
      }
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !loading) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (action) => {
    if (loading) return;
    setActiveQuickAction(action.id);
    handleSend(action.prompt, {
      quick_action: action.id,
      intent: action.intent,
      metadata: action.metadata,
      context_hint: action.description
    }).finally(() => {
      setActiveQuickAction((current) => (current === action.id ? null : current));
    });
  };

  return (
    <Box sx={{ py: 4 }}>
      <Stack direction="row" spacing={1} alignItems="center" mb={2} flexWrap="wrap">
        <SmartToy color="success" fontSize="large" />
        <Typography variant="h4">Assistente IA</Typography>
        <Chip label="Multiagente" color="success" size="small" />
        <Chip label="Prontuário completo" size="small" variant="outlined" />
      </Stack>

      <Typography variant="body1" color="text.secondary" mb={3} maxWidth={750}>
        Esta experiência é baseada no mesmo chat inteligente utilizado pelo AraOS, com
        atalhos rápidos, histórico persistido e acesso ao prontuário selecionado. Use um paciente
        para contextualizar ou continue sem contexto para perguntas gerais.
      </Typography>

      <ContextualTip
        severity="tip"
        storageKey="aichat_voz_tts"
        title="🎙️ Recursos escondidos:"
        sx={{ mb: 2 }}
      >
        <strong>Copiloto de Voz</strong> (canto superior) faz chamada full-duplex com Gemini Live. O ícone 🔊 em cada resposta reproduz o áudio (TTS) — passe o mouse para descobrir.
      </ContextualTip>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={2}
        alignItems="center"
        justifyContent="space-between"
        mb={2}
      >
        <Box sx={{ minWidth: 220, width: '100%' }}>
          <FormControl fullWidth>
            <InputLabel>Paciente (opcional)</InputLabel>
            <Select
              label="Paciente (opcional)"
              value={pacienteId}
              onChange={(event) => setPacienteId(event.target.value)}
              size="small"
            >
              <MenuItem value="">
                <em>Sem contexto de paciente</em>
              </MenuItem>
              {pacientes.map((paciente) => (
                <MenuItem key={paciente.id} value={paciente.id}>
                  {paciente.nome}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        <Button
          variant="outlined"
          color="inherit"
          startIcon={<Chat />}
          onClick={clearHistory}
          sx={{ whiteSpace: 'nowrap' }}
        >
          Limpar histórico
        </Button>
      </Stack>

      <Typography variant="subtitle1" gutterBottom>
        Atalhos inteligentes
      </Typography>

      <Grid container spacing={2} mb={3}>
        {CHAT_QUICK_ACTIONS.map((action) => {
          const isActive = activeQuickAction === action.id;
          return (
            <Grid key={action.id} item xs={12} md={4}>
              <Paper
                variant="outlined"
                sx={{
                  p: 2,
                  height: '100%',
                  borderColor: isActive ? 'primary.main' : 'divider',
                  boxShadow: isActive ? 4 : 1,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 1
                }}
              >
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="h5">{action.icon}</Typography>
                  <Typography variant="h6">{action.title}</Typography>
                </Stack>
                <Typography variant="body2" color="text.secondary">
                  {action.description}
                </Typography>
                <Box sx={{ mt: 'auto' }}>
                  <Button
                    size="small"
                    variant={isActive ? 'contained' : 'outlined'}
                    onClick={() => handleQuickAction(action)}
                    disabled={loading}
                    fullWidth
                  >
                    {isActive ? 'Executando...' : 'Usar atalho'}
                  </Button>
                </Box>
              </Paper>
            </Grid>
          );
        })}
      </Grid>

      <Paper
        variant="outlined"
        sx={{
          borderRadius: 3,
          borderColor: 'divider',
          bgcolor: 'background.default',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '70vh',
          overflow: 'hidden'
        }}
      >
        <Box
          sx={{
            background: 'background.paper',
            borderBottom: 1,
            borderColor: 'divider',
            px: { xs: 2, md: 4 },
            py: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 2
          }}
        >
          <Stack spacing={0.5}>
            <Typography variant="h6">Assistente IA</Typography>
            <Typography variant="body2" color="text.secondary">
              Online • Multiespecializado em prontuários
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Button
              variant={isLiveCallActive ? "contained" : "outlined"}
              color={isLiveCallActive ? "error" : "primary"}
              size="small"
              startIcon={isLiveCallActive ? <PhoneDisabled /> : <PhoneInTalk />}
              onClick={toggleLiveCall}
              sx={{
                borderRadius: 20,
                animation: isLiveCallActive ? 'pulseLive 2s infinite' : 'none',
                '@keyframes pulseLive': {
                  '0%': { boxShadow: (theme) => `0 0 0 0 ${theme.palette.error.main}66` },
                  '70%': { boxShadow: (theme) => `0 0 0 8px ${theme.palette.error.main}00` },
                  '100%': { boxShadow: (theme) => `0 0 0 0 ${theme.palette.error.main}00` }
                }
              }}
            >
              {isLiveCallActive ? 'Desligar Copiloto' : 'Ligar Copiloto de Voz'}
            </Button>
            <Button variant="text" size="small" onClick={clearHistory}>
              Limpar chat
            </Button>
          </Stack>
        </Box>

        <Box
          ref={chatListRef}
          sx={{
            flex: 1,
            overflowY: 'auto',
            bgcolor: 'background.default',
            py: 2,
            px: { xs: 1, md: 3 }
          }}
        >
          <Box
            sx={{
              maxWidth: '960px',
              mx: 'auto',
              display: 'flex',
              flexDirection: 'column',
              gap: 24
            }}
          >
            {messages.map((message) => {
              const isUser = message.role === 'user';
              const bubbleColor = isUser ? 'primary.main' : 'background.paper';
              const textColor = isUser ? 'primary.contrastText' : 'text.primary';
              return (
                <Box
                  key={message.id}
                  sx={{
                    display: 'flex',
                    justifyContent: isUser ? 'flex-end' : 'flex-start'
                  }}
                >
                  <Box
                    sx={{
                      position: 'relative',
                      maxWidth: '72%',
                      px: { xs: 2.5, sm: 3 },
                      py: 1.75,
                      borderRadius: 30,
                      background: bubbleColor,
                      color: textColor,
                      border: isUser ? 'none' : '1px solid #e0e0e0',
                      boxShadow: isUser
                        ? '0 1px 3px rgba(0,0,0,0.25)'
                        : '0 1px 2px rgba(0,0,0,0.08)',
                      '&::after': {
                        content: '""',
                        position: 'absolute',
                        bottom: 10,
                        width: 12,
                        height: 12,
                        background: bubbleColor,
                        clipPath: 'polygon(0 0, 100% 50%, 0 100%)',
                        right: isUser ? -6 : 'auto',
                        left: isUser ? 'auto' : -6,
                        boxShadow: isUser ? '0 -1px 2px rgba(0,0,0,0.25)' : '0 1px 2px rgba(0,0,0,0.08)'
                      }
                    }}
                  >
                    <Typography
                      variant="body1"
                      sx={{ whiteSpace: 'pre-line', color: message.status === 'error' ? '#ffebee' : textColor }}
                    >
                      {message.content}
                    </Typography>
                    <Box
                      sx={{
                        display: 'flex',
                        justifyContent: isUser ? 'flex-end' : 'flex-start',
                        alignItems: 'center',
                        gap: 0.75,
                        mt: 0.75
                      }}
                    >
                      <Typography
                        variant="caption"
                        sx={{
                          color: message.status === 'error' ? '#ffebee' : 'rgba(0,0,0,0.55)'
                        }}
                      >
                        {isUser ? 'Você' : 'Assistente'} • {formatTimestamp(message.timestamp)}
                      </Typography>
                      {message.status === 'pending' && (
                        <CircularProgress size={12} sx={{ color: message.status === 'error' ? '#ffebee' : 'inherit' }} />
                      )}
                      {!isUser && message.status === 'done' && (
                        <IconButton
                          size="small"
                          onClick={() => handleTTS(message)}
                          disabled={playingTTSId === message.id}
                          sx={{ padding: 0, ml: 1, color: playingTTSId === message.id ? 'success.main' : 'rgba(0,0,0,0.45)' }}
                        >
                          {playingTTSId === message.id ? <CircularProgress size={16} color="inherit" /> : <VolumeUp fontSize="small" />}
                        </IconButton>
                      )}
                    </Box>
                  </Box>
                </Box>
              );
            })}
            {/* Âncora de scroll para a última mensagem */}
            <Box
              ref={(el) => {
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'end' });
              }}
              sx={{ height: 1 }}
            />
          </Box>
        </Box>

        <Box
          sx={{
            background: 'background.paper',
            borderTop: 1,
            borderColor: 'divider',
            px: { xs: 2, md: 4 },
            py: 2
          }}
        >
          <Box
            sx={{
              maxWidth: '960px',
              mx: 'auto',
              display: 'flex',
              alignItems: 'flex-end',
              gap: 2
            }}
          >
            <TextField
              placeholder="Envie uma mensagem"
              fullWidth
              multiline
              minRows={2}
              maxRows={5}
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              InputProps={{
                sx: {
                  borderRadius: '22px',
                  bgcolor: 'action.hover',
                  '&.Mui-focused': {
                    bgcolor: 'background.paper',
                    boxShadow: (theme) => `0 0 0 2px ${theme.palette.success.main}40`
                  }
                }
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '22px',
                  borderColor: 'divider',
                  bgcolor: 'action.hover'
                },
                '& .MuiOutlinedInput-root.Mui-focused': {
                  borderColor: 'success.main'
                }
              }}
            />
            {isRecording ? (
              <IconButton
                color="error"
                onClick={stopRecording}
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  bgcolor: 'error.main',
                  color: 'error.contrastText',
                  boxShadow: (theme) => `0 8px 16px ${theme.palette.mode === 'dark' ? 'rgba(255,107,107,0.35)' : 'rgba(229,57,96,0.35)'}`,
                  animation: 'pulse 1.5s infinite',
                  '@keyframes pulse': {
                    '0%': { boxShadow: (theme) => `0 0 0 0 ${theme.palette.mode === 'dark' ? 'rgba(255,107,107,0.7)' : 'rgba(229,57,96,0.7)'}` },
                    '70%': { boxShadow: (theme) => `0 0 0 10px ${theme.palette.mode === 'dark' ? 'rgba(255,107,107,0)' : 'rgba(229,57,96,0)'}` },
                    '100%': { boxShadow: (theme) => `0 0 0 0 ${theme.palette.mode === 'dark' ? 'rgba(255,107,107,0)' : 'rgba(229,57,96,0)'}` }
                  }
                }}
              >
                <StopCircle />
              </IconButton>
            ) : (
              <IconButton
                color="secondary"
                disabled={loading}
                onClick={startRecording}
                sx={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  bgcolor: loading ? 'action.disabled' : 'secondary.main',
                  color: 'secondary.contrastText',
                  '&:hover': {
                    bgcolor: loading ? 'action.disabled' : 'secondary.dark'
                  }
                }}
              >
                <Mic />
              </IconButton>
            )}

            <IconButton
              color="success"
              disabled={loading || !inputValue.trim()}
              onClick={() => handleSend()}
              sx={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                bgcolor: loading ? 'action.disabled' : 'success.main',
                color: 'success.contrastText',
                '&:hover': {
                  bgcolor: loading ? 'action.disabled' : 'success.dark'
                }
              }}
            >
              {loading ? <CircularProgress size={20} color="inherit" /> : <Send />}
            </IconButton>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default AIChatPage;
