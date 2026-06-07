/**
 * ARAOS Voice Widget
 * 
 * Componente visual para o Copiloto Clínico por Voz.
 * Integra com VoiceService para captura, transcrição e controle.
 * 
 * Estados visuais:
 *   - idle: Aguardando (botão verde)
 *   - listening: Capturando áudio (onda animada, azul)
 *   - processing: Processando STT (spinner, amarelo)
 *   - responding: Copilot respondendo (verde claro)
 *   - error: Erro (vermelho)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Fab,
  Paper,
  Typography,
  Chip,
  Fade,
  Slide,
  IconButton,
  Tooltip,
  Alert,
  Collapse,
  List,
  ListItem,
  ListItemText,
  Avatar,
} from '@mui/material';
import {
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Stop as StopIcon,
  GraphicEq as WaveIcon,
  Person as DoctorIcon,
  PersonOutline as PatientIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import voiceService from '../../services/voiceService';

const STATE_CONFIG = {
  disconnected: { color: '#9e9e9e', label: 'Desconectado', icon: MicOffIcon },
  connecting: { color: '#ff9800', label: 'Conectando...', icon: MicIcon },
  idle: { color: '#4caf50', label: 'Pronto', icon: MicIcon },
  listening: { color: '#2196f3', label: 'Ouvindo...', icon: WaveIcon },
  processing: { color: '#ff9800', label: 'Processando...', icon: MicIcon },
  responding: { color: '#00bcd4', label: 'Respondendo...', icon: WaveIcon },
  error: { color: '#f44336', label: 'Erro', icon: WarningIcon },
};

const SPEAKER_COLORS = {
  doctor: { bg: '#e3f2fd', text: '#1565c0', icon: <DoctorIcon fontSize="small" /> },
  patient: { bg: '#f3e5f5', text: '#6a1b9a', icon: <PatientIcon fontSize="small" /> },
  unknown: { bg: '#f5f5f5', text: '#616161', icon: <DoctorIcon fontSize="small" /> },
};

export default function VoiceWidget({
  tenantId,
  patientId,
  doctorId,
  specialty = 'general',
  onTranscriptUpdate,
  compact = false,
}) {
  const [state, setState] = useState('disconnected');
  const [isOpen, setIsOpen] = useState(false);
  const [transcript, setTranscript] = useState([]);
  const [error, setError] = useState(null);
  const [currentSegment, setCurrentSegment] = useState(null);
  const transcriptEndRef = useRef(null);

  // Conectar ao serviço de voz
  useEffect(() => {
    voiceService.onStateChange = (oldState, newState) => {
      setState(newState);
    };

    voiceService.onTranscription = (payload) => {
      setTranscript(prev => {
        // Evitar duplicatas
        const exists = prev.find(t => t.id === payload.id);
        if (exists) {
          return prev.map(t => t.id === payload.id ? payload : t);
        }
        return [...prev, payload];
      });
      setCurrentSegment(null);

      if (onTranscriptUpdate) {
        onTranscriptUpdate(payload);
      }
    };

    voiceService.onError = (message) => {
      setError(message);
      setTimeout(() => setError(null), 5000);
    };

    // Tentar conectar automaticamente quando o widget abrir
    if (isOpen && state === 'disconnected') {
      connect();
    }

    return () => {
      voiceService.disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, tenantId, patientId, doctorId]);

  // Auto-scroll do transcript
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [transcript, currentSegment]);

  const connect = useCallback(async () => {
    try {
      setError(null);
      await voiceService.connect({
        tenantId,
        patientId,
        doctorId,
        specialty,
      });
    } catch (err) {
      setError('Falha ao conectar ao servidor de voz');
    }
  }, [tenantId, patientId, doctorId, specialty]);

  const toggleRecording = useCallback(() => {
    if (state === 'listening') {
      voiceService.stopRecording();
    } else if (state === 'idle' || state === 'disconnected') {
      if (state === 'disconnected') {
        connect().then(() => voiceService.startRecording());
      } else {
        voiceService.startRecording();
      }
    }
  }, [state, connect]);

  const handleClose = useCallback(() => {
    voiceService.endSession();
    setIsOpen(false);
    setTranscript([]);
  }, []);

  const stateConfig = STATE_CONFIG[state] || STATE_CONFIG.idle;
  const StateIcon = stateConfig.icon;
  const isRecording = state === 'listening';

  // ─── Render ──────────────────────────────────────────────────────────

  if (!isOpen) {
    return (
      <Fab
        color="primary"
        aria-label="ARAOS Voice"
        onClick={() => setIsOpen(true)}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: 64,
          height: 64,
          bgcolor: state === 'listening' ? '#2196f3' : '#4caf50',
          '&:hover': { bgcolor: state === 'listening' ? '#1976d2' : '#388e3c' },
          animation: state === 'listening' ? 'pulse 1.5s infinite' : 'none',
          '@keyframes pulse': {
            '0%': { boxShadow: '0 0 0 0 rgba(33, 150, 243, 0.4)' },
            '70%': { boxShadow: '0 0 0 20px rgba(33, 150, 243, 0)' },
            '100%': { boxShadow: '0 0 0 0 rgba(33, 150, 243, 0)' },
          },
          zIndex: 1300,
        }}
      >
        <StateIcon sx={{ fontSize: 28, color: '#fff' }} />
      </Fab>
    );
  }

  return (
    <Slide direction="up" in={isOpen} mountOnEnter unmountOnExit>
      <Paper
        elevation={8}
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: compact ? 320 : 400,
          maxHeight: '70vh',
          display: 'flex',
          flexDirection: 'column',
          borderRadius: 3,
          overflow: 'hidden',
          zIndex: 1300,
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            bgcolor: stateConfig.color,
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <StateIcon />
            <Typography variant="subtitle1" fontWeight="bold">
              ARAOS Voice
            </Typography>
            <Chip
              size="small"
              label={stateConfig.label}
              sx={{
                bgcolor: 'rgba(255,255,255,0.25)',
                color: '#fff',
                fontWeight: 'bold',
                fontSize: '0.7rem',
              }}
            />
          </Box>
          <Box>
            <Tooltip title="Configurações">
              <IconButton size="small" sx={{ color: '#fff' }}>
                <SettingsIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Fechar">
              <IconButton size="small" sx={{ color: '#fff' }} onClick={handleClose}>
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Error Alert */}
        <Collapse in={!!error}>
          <Alert severity="error" sx={{ m: 1 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        </Collapse>

        {/* Transcript Area */}
        <Box
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: 2,
            minHeight: 200,
            maxHeight: 400,
            bgcolor: '#fafafa',
          }}
        >
          {transcript.length === 0 && !currentSegment && (
            <Typography
              variant="body2"
              color="text.secondary"
              align="center"
              sx={{ mt: 8 }}
            >
              A transcrição aparecerá aqui...
              <br />
              Pressione o botão do microfone para começar.
            </Typography>
          )}

          <List dense disablePadding>
            {transcript.map((segment) => {
              const speakerConfig = SPEAKER_COLORS[segment.speaker] || SPEAKER_COLORS.unknown;
              return (
                <ListItem
                  key={segment.id}
                  sx={{
                    mb: 1,
                    p: 1,
                    borderRadius: 2,
                    bgcolor: speakerConfig.bg,
                    alignItems: 'flex-start',
                  }}
                >
                  <Avatar
                    sx={{
                      bgcolor: speakerConfig.text,
                      color: '#fff',
                      width: 28,
                      height: 28,
                      fontSize: '0.8rem',
                      mr: 1,
                      mt: 0.3,
                    }}
                  >
                    {speakerConfig.icon}
                  </Avatar>
                  <ListItemText
                    primary={
                      <Typography
                        variant="body2"
                        sx={{ color: speakerConfig.text, fontWeight: 500 }}
                      >
                        {segment.speaker === 'doctor' ? 'Médico' : 'Paciente'}
                      </Typography>
                    }
                    secondary={
                      <Typography variant="body1" sx={{ color: '#333', mt: 0.5 }}>
                        {segment.text}
                      </Typography>
                    }
                  />
                </ListItem>
              );
            })}

            {/* Segmento parcial (em transcrição) */}
            {currentSegment && (
              <ListItem sx={{ opacity: 0.6, bgcolor: '#e3f2fd', borderRadius: 2, mb: 1 }}>
                <ListItemText
                  secondary={
                    <Typography variant="body2" sx={{ fontStyle: 'italic' }}>
                      {currentSegment}...
                    </Typography>
                  }
                />
              </ListItem>
            )}
          </List>
          <div ref={transcriptEndRef} />
        </Box>

        {/* Controls */}
        <Box
          sx={{
            p: 2,
            borderTop: '1px solid #e0e0e0',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            gap: 2,
            bgcolor: '#fff',
          }}
        >
          <Fab
            onClick={toggleRecording}
            sx={{
              width: 64,
              height: 64,
              bgcolor: isRecording ? '#f44336' : stateConfig.color,
              '&:hover': {
                bgcolor: isRecording ? '#d32f2f' : stateConfig.color,
              },
              animation: isRecording
                ? 'pulse-record 1.2s infinite'
                : 'none',
              '@keyframes pulse-record': {
                '0%': { transform: 'scale(1)' },
                '50%': { transform: 'scale(1.08)' },
                '100%': { transform: 'scale(1)' },
              },
            }}
          >
            {isRecording ? (
              <StopIcon sx={{ fontSize: 28, color: '#fff' }} />
            ) : (
              <MicIcon sx={{ fontSize: 28, color: '#fff' }} />
            )}
          </Fab>

          {isRecording && (
            <Fade in>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                {[...Array(5)].map((_, i) => (
                  <Box
                    key={i}
                    sx={{
                      width: 4,
                      height: 16 + Math.random() * 20,
                      bgcolor: '#2196f3',
                      borderRadius: 2,
                      animation: `wave 0.5s ease-in-out ${i * 0.1}s infinite alternate`,
                      '@keyframes wave': {
                        '0%': { height: 8 },
                        '100%': { height: 32 },
                      },
                    }}
                  />
                ))}
              </Box>
            </Fade>
          )}
        </Box>

        {/* Footer */}
        <Box sx={{ px: 2, pb: 1, textAlign: 'center' }}>
          <Typography variant="caption" color="text.secondary">
            {transcript.length > 0
              ? `${transcript.length} segmentos • ${transcript.filter(t => t.speaker === 'doctor').length} médico / ${transcript.filter(t => t.speaker === 'patient').length} paciente`
              : 'ARAOS Voice Copilot v1.0'}
          </Typography>
        </Box>
      </Paper>
    </Slide>
  );
}
