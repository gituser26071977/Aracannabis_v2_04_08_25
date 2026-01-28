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
import { Chat, Send, SmartToy } from '@mui/icons-material';
import { chatSimplesService, pacientesService } from '../services/api';

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

  useEffect(() => {
    if (chatListRef.current) {
      chatListRef.current.scrollTop = chatListRef.current.scrollHeight;
    }
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
        Esta experiência é baseada no mesmo chat inteligente utilizado pelo Aracannabis, com
        atalhos rápidos, histórico persistido e acesso ao prontuário selecionado. Use um paciente
        para contextualizar ou continue sem contexto para perguntas gerais.
      </Typography>

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
          border: '1px solid #e0e0e0',
          bgcolor: '#f5f5f5',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '70vh',
          overflow: 'hidden'
        }}
      >
        <Box
          sx={{
            background: '#fff',
            borderBottom: '1px solid #e0e0e0',
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
          <Button variant="text" size="small" onClick={clearHistory}>
            Limpar chat
          </Button>
        </Box>

        <Box
          ref={chatListRef}
          sx={{
            flex: 1,
            overflowY: 'auto',
            background: '#f5f5f5',
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
              const bubbleColor = isUser ? '#25d366' : '#ffffff';
              const textColor = isUser ? '#fff' : '#222';
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
                    </Box>
                  </Box>
                </Box>
              );
            })}
          </Box>
        </Box>

        <Box
          sx={{
            background: '#fff',
            borderTop: '1px solid #e0e0e0',
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
                  bgcolor: '#f5f5f5',
                  '&.Mui-focused': {
                    bgcolor: '#fff',
                    boxShadow: '0 0 0 2px rgba(37,211,102,0.25)'
                  }
                }
              }}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: '22px',
                  borderColor: '#e0e0e0',
                  bgcolor: '#f5f5f5'
                },
                '& .MuiOutlinedInput-root.Mui-focused': {
                  borderColor: '#25d366'
                }
              }}
            />
            <IconButton
              color="success"
              disabled={loading || !inputValue.trim()}
              onClick={() => handleSend()}
              sx={{
                width: 48,
                height: 48,
                borderRadius: '50%',
                bgcolor: loading ? '#b1d9c1' : '#25d366',
                color: '#fff',
                boxShadow: '0 8px 16px rgba(37,211,102,0.35)',
                '&:hover': {
                  bgcolor: loading ? '#b1d9c1' : '#1da851'
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
