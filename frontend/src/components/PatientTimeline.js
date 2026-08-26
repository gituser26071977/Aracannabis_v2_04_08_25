import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Chip,
  CircularProgress,
  Divider,
  Alert,
  IconButton,
} from '@mui/material';
import {
  Event as EventIcon,
  Medication as ConsultaIcon,
  EditNote as EvolucaoIcon,
  MonitorHeart as VitalIcon,
  Healing as ExameFisicoIcon,
  Biotech as ExameIcon,
  Psychology as SintomaIcon,
  MedicalInformation as DiagnosticoIcon,
  HistoryEdu as AnamneseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
} from '@mui/icons-material';
import { prontuarioService } from '../services/api';

const TYPE_META = {
  consultation: { color: 'primary', icon: ConsultaIcon, label: 'Consulta' },
  evolution: { color: 'info', icon: EvolucaoIcon, label: 'Evolução' },
  anamnesis: { color: 'secondary', icon: AnamneseIcon, label: 'Anamnese' },
  vital: { color: 'error', icon: VitalIcon, label: 'Sinais Vitais' },
  physical_exam: { color: 'success', icon: ExameFisicoIcon, label: 'Exame Físico' },
  symptom: { color: 'warning', icon: SintomaIcon, label: 'Sintoma' },
  exam: { color: 'primary', icon: ExameIcon, label: 'Exame' },
  diagnosis: { color: 'error', icon: DiagnosticoIcon, label: 'Diagnóstico' },
};

const PatientTimeline = ({ patientId }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const res = await prontuarioService.timeline(patientId);
        if (active) setEvents(res.events || []);
      } catch (err) {
        if (active) setError(err.error || 'Erro ao carregar timeline');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [patientId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress size={28} />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!events.length) {
    return (
      <Alert severity="info" sx={{ mt: 2 }}>
        Nenhum evento registrado ainda. Registre evoluções, sinais vitais, exames ou consultas para
        ver a linha do tempo.
      </Alert>
    );
  }

  const VISIVEIS_INICIAL = 8;
  const visiveis = expanded ? events : events.slice(0, VISIVEIS_INICIAL);

  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
          <EventIcon sx={{ mr: 1, color: 'primary.main' }} /> Linha do Tempo
        </Typography>
        {events.length > VISIVEIS_INICIAL && (
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        )}
      </Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Histórico unificado do paciente — consultas, evoluções, exames, sintomas e diagnósticos.
      </Typography>
      <Divider sx={{ my: 1 }} />

      <Box sx={{ position: 'relative', pl: 3 }}>
        {/* Linha vertical */}
        <Box
          sx={{
            position: 'absolute',
            left: 10,
            top: 4,
            bottom: 4,
            width: 2,
            bgcolor: 'divider',
          }}
        />
        {visiveis.map((ev, idx) => {
          const meta = TYPE_META[ev.type] || { color: 'default', icon: EventIcon, label: ev.type };
          const Icon = meta.icon;
          return (
            <Box key={`${ev.type}-${idx}`} sx={{ position: 'relative', mb: 2, pl: 2 }}>
              {/* Dot */}
              <Box
                sx={{
                  position: 'absolute',
                  left: -22,
                  top: 4,
                  width: 18,
                  height: 18,
                  borderRadius: '50%',
                  bgcolor: `${meta.color}.main`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Icon sx={{ fontSize: 12, color: 'white' }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                <Chip size="small" color={meta.color} label={meta.label} />
                <Typography variant="body2" fontWeight="medium">
                  {ev.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {ev.date
                    ? new Date(ev.date).toLocaleString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : ''}
                </Typography>
              </Box>
              {ev.description && (
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {ev.description}
                </Typography>
              )}
            </Box>
          );
        })}
      </Box>
      {events.length > VISIVEIS_INICIAL && (
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{ display: 'block', textAlign: 'center', mt: 1 }}
        >
          {expanded
            ? `Ocultar (${events.length} eventos)`
            : `Mostrar todos (${events.length} eventos)`}
        </Typography>
      )}
    </Paper>
  );
};

export default PatientTimeline;
