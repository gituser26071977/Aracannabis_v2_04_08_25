import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Container,
  Stack,
  Avatar,
  IconButton,
  Chip,
} from '@mui/material';
import { useParams } from 'react-router-dom';
import AutoAwesome from '@mui/icons-material/AutoAwesome';
import Send from '@mui/icons-material/Send';
import AttachFile from '@mui/icons-material/AttachFile';
import Image from '@mui/icons-material/Image';
import CheckCircle from '@mui/icons-material/CheckCircle';
import Person from '@mui/icons-material/Person';
import api from '../services/api';

const PreAtendimentoPage = () => {
  const { slug } = useParams();
  const [meta, setMeta] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [pronto, setPronto] = useState(false);
  const [finalizado, setFinalizado] = useState(false);
  const [dadosColetados, setDadosColetados] = useState([]);
  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (!slug) return;
    const init = async () => {
      setLoading(true);
      setError('');
      try {
        const r = await api.get(`/public/pre-atendimento/${slug}`);
        setMeta(r.data);

        // Iniciar sessão de chat
        const s = await api.post(`/public/pre-atendimento/${slug}/chat/iniciar`);
        setSessionId(s.data.session_id);

        setMessages([
          {
            role: 'assistant',
            content:
              r.data.boas_vindas +
              ' Vou fazer algumas perguntas para o seu pré-atendimento. Para começar, qual é o seu nome completo?',
          },
        ]);
      } catch (e) {
        setError(e?.response?.data?.error || 'Instituto não encontrado.');
      } finally {
        setLoading(false);
      }
    };
    init();
  }, [slug]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, enviando]);

  const enviarMensagem = async (texto, imagemB64 = null, mimeType = null) => {
    if (!sessionId || enviando) return;
    if (!texto.trim() && !imagemB64) return;

    setEnviando(true);
    setError('');

    const userMsg = imagemB64
      ? { role: 'user', content: texto || '📎 Enviei um documento', imagem: true }
      : { role: 'user', content: texto };
    setMessages((m) => [...m, userMsg]);
    setInput('');

    try {
      const payload = { session_id: sessionId, mensagem: texto };
      if (imagemB64) {
        payload.imagem_b64 = imagemB64;
        payload.mime_type = mimeType || 'image/jpeg';
      }
      const r = await api.post(`/public/pre-atendimento/${slug}/chat`, payload);
      setMessages((m) => [...m, { role: 'assistant', content: r.data.resposta }]);
      setPronto(Boolean(r.data.pronto));
      setDadosColetados(r.data.campos_respondidos || []);
    } catch (e) {
      setError(e?.response?.data?.error || 'Erro ao enviar. Tente novamente.');
    } finally {
      setEnviando(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      enviarMensagem(input);
    }
  };

  const onFile = async (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const b64 = String(reader.result);
      const mime = file.type || 'image/jpeg';
      await enviarMensagem('', b64, mime);
    };
    reader.readAsDataURL(file);
  };

  const finalizar = async () => {
    setEnviando(true);
    setError('');
    try {
      await api.post(`/public/pre-atendimento/${slug}/chat/finalizar`, {
        session_id: sessionId,
      });
      setFinalizado(true);
    } catch (e) {
      setError(e?.response?.data?.error || 'Erro ao finalizar.');
    } finally {
      setEnviando(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && !meta) {
    return (
      <Container maxWidth="sm" sx={{ mt: 6 }}>
        <Alert severity="warning">{error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ borderRadius: 3, overflow: 'hidden' }}>
        {/* Header */}
        <Box
          sx={{
            p: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            bgcolor: 'primary.main',
            color: 'white',
          }}
        >
          <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)' }}>
            <AutoAwesome />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700 }}>
              {meta?.instituto}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {meta?.profissional} · Pré-atendimento
            </Typography>
          </Box>
        </Box>

        {finalizado ? (
          <Box textAlign="center" py={6} px={3}>
            <CheckCircle color="success" sx={{ fontSize: 64, mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Pré-atendimento recebido!
            </Typography>
            <Typography color="text.secondary">
              Seus dados foram enviados para a equipe do {meta?.instituto}. Após a confirmação do
              pagamento e a conferência, você será liberado(a).
            </Typography>
          </Box>
        ) : (
          <>
            {/* Mensagens */}
            <Box
              sx={{ p: 2, minHeight: 420, maxHeight: 480, overflowY: 'auto', bgcolor: '#f5f7f9' }}
            >
              {messages.map((m, i) => (
                <Stack
                  key={i}
                  direction="row"
                  justifyContent={m.role === 'user' ? 'flex-end' : 'flex-start'}
                  mb={1}
                >
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="flex-start"
                    sx={{
                      maxWidth: '80%',
                      flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
                    }}
                  >
                    <Avatar
                      sx={{
                        width: 32,
                        height: 32,
                        bgcolor: m.role === 'user' ? 'primary.main' : 'secondary.main',
                        fontSize: 16,
                      }}
                    >
                      {m.role === 'user' ? (
                        <Person fontSize="small" />
                      ) : (
                        <AutoAwesome fontSize="small" />
                      )}
                    </Avatar>
                    <Box
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        bgcolor: m.role === 'user' ? 'primary.main' : 'white',
                        color: m.role === 'user' ? 'white' : 'inherit',
                        border: m.role === 'user' ? 'none' : '1px solid',
                        borderColor: 'divider',
                        whiteSpace: 'pre-wrap',
                      }}
                    >
                      <Typography variant="body2">{m.content}</Typography>
                    </Box>
                  </Stack>
                </Stack>
              ))}
              {enviando && (
                <Stack direction="row" spacing={1} alignItems="center">
                  <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main', fontSize: 16 }}>
                    <AutoAwesome fontSize="small" />
                  </Avatar>
                  <CircularProgress size={18} />
                </Stack>
              )}
              <div ref={bottomRef} />
            </Box>

            {/* Dados coletados */}
            {dadosColetados.length > 0 && (
              <Box sx={{ px: 2, pb: 1 }}>
                <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                  {dadosColetados.map((c) => (
                    <Chip
                      key={c}
                      size="small"
                      label={c.replace(/_/g, ' ')}
                      color="success"
                      variant="outlined"
                    />
                  ))}
                </Stack>
              </Box>
            )}

            {error && (
              <Box sx={{ px: 2, pb: 1 }}>
                <Alert severity="error">{error}</Alert>
              </Box>
            )}

            {/* Input */}
            <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider', bgcolor: 'white' }}>
              {pronto ? (
                <Button
                  variant="contained"
                  size="large"
                  fullWidth
                  startIcon={<CheckCircle />}
                  onClick={finalizar}
                  disabled={enviando}
                >
                  {enviando ? 'Finalizando...' : 'Finalizar pré-atendimento'}
                </Button>
              ) : (
                <>
                  <Stack direction="row" spacing={1} alignItems="flex-end">
                    <TextField
                      fullWidth
                      size="small"
                      placeholder="Digite sua resposta..."
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={onKeyDown}
                      multiline
                      maxRows={3}
                      disabled={enviando}
                    />
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/png,image/jpeg,image/jpg,application/pdf"
                      style={{ display: 'none' }}
                      onChange={(e) => {
                        const f = e.target.files?.[0];
                        if (f) onFile(f);
                        e.target.value = '';
                      }}
                    />
                    <IconButton
                      onClick={() => fileRef.current?.click()}
                      disabled={enviando}
                      title="Enviar documento/exame/laudo"
                    >
                      <Image />
                    </IconButton>
                    <IconButton
                      onClick={() => fileRef.current?.click()}
                      disabled={enviando}
                      title="Anexar arquivo"
                    >
                      <AttachFile />
                    </IconButton>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => enviarMensagem(input)}
                      disabled={enviando || !input.trim()}
                    >
                      <Send />
                    </Button>
                  </Stack>
                </>
              )}
            </Box>
          </>
        )}
      </Paper>
    </Container>
  );
};

export default PreAtendimentoPage;
