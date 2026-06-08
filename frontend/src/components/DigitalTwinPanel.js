import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  LinearProgress,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tooltip,
  IconButton,
  Collapse,
  Button
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  TrendingFlat as TrendingFlatIcon,
  Event as EventIcon,
  MedicalServices as MedicalIcon,
  Medication as MedicationIcon,
  Assessment as AssessmentIcon,
  Science as ScienceIcon,
  Warning as WarningIcon,
  LocalHospital as HospitalIcon,
  CalendarToday as CalendarIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { twinService } from '../services/api';

const COUNT_COLORS = {
  symptoms: '#f44336',
  dosages: '#2196f3',
  evolutions: '#4caf50',
  consultations: '#ff9800',
  exams: '#9c27b0',
  cannabis_doses: '#00bcd4',
  cannabis_outcomes: '#8bc34a',
  active_alerts: '#ff5722'
};

const COUNT_LABELS = {
  symptoms: 'Sintomas',
  dosages: 'Dosagens',
  evolutions: 'Evoluções',
  consultations: 'Consultas',
  exams: 'Exames',
  cannabis_doses: 'Doses Cannabis',
  cannabis_outcomes: 'Outcomes Cannabis',
  active_alerts: 'Alertas Ativos'
};

const EVENT_ICONS = {
  consultation: <EventIcon color="primary" />,
  evolution: <MedicalIcon color="success" />,
  symptom: <WarningIcon color="error" />,
  dosage: <MedicationIcon color="info" />,
  exam: <ScienceIcon color="secondary" />,
  cannabis_dose: <MedicationIcon style={{ color: '#00bcd4' }} />,
  cannabis_outcome: <AssessmentIcon style={{ color: '#8bc34a' }} />
};

const TREND_ICONS = {
  improving: <TrendingDownIcon color="success" />,
  worsening: <TrendingUpIcon color="error" />,
  stable: <TrendingFlatIcon color="action" />,
  insufficient_data: <TrendingFlatIcon color="disabled" />
};

const TREND_LABELS = {
  improving: 'Melhorando',
  worsening: 'Piorando',
  stable: 'Estável',
  insufficient_data: 'Dados insuficientes'
};

const DigitalTwinPanel = ({ patientId }) => {
  const [twin, setTwin] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [outcomes, setOutcomes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedTimeline, setExpandedTimeline] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError('');
      try {
        const [twinData, dashData, timelineData, outcomesData] = await Promise.all([
          twinService.obterTwin(patientId).catch(() => null),
          twinService.obterDashboard(patientId).catch(() => null),
          twinService.obterTimeline(patientId).catch(() => null),
          twinService.obterOutcomes(patientId).catch(() => null)
        ]);
        setTwin(twinData);
        setDashboard(dashData);
        setTimeline(timelineData);
        setOutcomes(outcomesData);
      } catch (err) {
        console.error('Erro ao carregar Digital Twin:', err);
        setError('Não foi possível carregar o Digital Twin');
      } finally {
        setLoading(false);
      }
    };

    if (patientId) {
      fetchData();
    }
  }, [patientId]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const counts = dashboard?.counts || {};
  const patient = dashboard?.patient || twin?.patient || {};
  const clinical = twin?.clinical_summary || {};
  const cannabis = twin?.cannabis;

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon /> Digital Twin — {patient.name || 'Paciente'}
        </Typography>
        <Typography variant="body2" sx={{ opacity: 0.9 }}>
          Visão unificada do paciente em tempo real
        </Typography>
      </Paper>

      {/* Count Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(counts).map(([key, value]) => (
          <Grid item xs={6} sm={4} md={3} key={key}>
            <Card elevation={2}>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" sx={{ color: COUNT_COLORS[key] || '#666', fontWeight: 'bold' }}>
                  {value || 0}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {COUNT_LABELS[key] || key}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Clinical Summary */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HospitalIcon color="primary" /> Resumo Clínico
            </Typography>
            <Divider sx={{ mb: 2 }} />

            {/* Recent Symptoms */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Sintomas Recentes
              </Typography>
              {clinical.recent_symptoms?.length > 0 ? (
                clinical.recent_symptoms.map((s, i) => (
                  <Box key={i} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2">{s.symptom}</Typography>
                      <Chip size="small" label={`${s.intensity}/10`} color={s.intensity > 7 ? 'error' : s.intensity > 4 ? 'warning' : 'success'} />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(s.intensity / 10) * 100}
                      sx={{
                        height: 6,
                        borderRadius: 3,
                        backgroundColor: '#e0e0e0',
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: s.intensity > 7 ? '#f44336' : s.intensity > 4 ? '#ff9800' : '#4caf50'
                        }
                      }}
                    />
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">Nenhum sintoma recente</Typography>
              )}
            </Box>

            {/* Recent Evolutions */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Evoluções Recentes
              </Typography>
              {clinical.recent_evolutions?.length > 0 ? (
                clinical.recent_evolutions.map((e, i) => (
                  <Paper key={i} variant="outlined" sx={{ p: 1.5, mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(e.date)}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 0.5 }}>
                      {e.note?.substring(0, 120)}{e.note?.length > 120 ? '...' : ''}
                    </Typography>
                  </Paper>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">Nenhuma evolução recente</Typography>
              )}
            </Box>

            {/* Upcoming Consultations */}
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Próximas Consultas
              </Typography>
              {clinical.upcoming_consultations?.length > 0 ? (
                clinical.upcoming_consultations.map((c, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    <CalendarIcon color="primary" fontSize="small" />
                    <Typography variant="body2">
                      {formatDate(c.date)} — {c.type}
                    </Typography>
                    <Chip size="small" label={c.status} variant="outlined" />
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary">Nenhuma consulta agendada</Typography>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Cannabis Summary + Outcomes */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MedicationIcon style={{ color: '#00bcd4' }} /> Perfil Cannabis
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {cannabis ? (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="body2"><strong>Condição Primária:</strong> {cannabis.primary_condition || 'N/A'}</Typography>
                  <Chip
                    size="small"
                    label={cannabis.treatment_status || 'N/A'}
                    color={cannabis.treatment_status === 'active' ? 'success' : 'default'}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  <strong>Medicamentos Ativos:</strong> {cannabis.active_medications?.length || 0}
                </Typography>
                {cannabis.active_medications?.map((m, i) => (
                  <Paper key={i} variant="outlined" sx={{ p: 1, mb: 1 }}>
                    <Typography variant="body2">{m.product} — {m.dose_mg}mg</Typography>
                  </Paper>
                ))}
                {cannabis.active_alerts?.length > 0 && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    {cannabis.active_alerts.length} alerta(s) ativo(s)
                  </Alert>
                )}
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Nenhum perfil cannabis encontrado para este paciente.
              </Typography>
            )}
          </Paper>

          {/* Outcomes */}
          <Paper elevation={2} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon color="primary" /> Outcomes & Trends
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {/* Cannabis Outcomes */}
            {outcomes?.cannabis_outcomes && Object.keys(outcomes.cannabis_outcomes).length > 0 ? (
              Object.entries(outcomes.cannabis_outcomes).map(([name, data]) => (
                <Box key={name} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="body2" fontWeight="medium">{name}</Typography>
                    <Tooltip title={TREND_LABELS[data.trend]}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {TREND_ICONS[data.trend]}
                        <Typography variant="caption" color="text.secondary">
                          {data.scores?.length || 0} registros
                        </Typography>
                      </Box>
                    </Tooltip>
                  </Box>
                  {data.scores?.slice(-5).map((s, i) => (
                    <Box key={i} sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ minWidth: 70 }}>
                        {formatDate(s.date)}
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={(s.score / (s.max || 10)) * 100}
                        sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
                      />
                      <Typography variant="caption" sx={{ minWidth: 40, textAlign: 'right' }}>
                        {s.score}/{s.max || 10}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">Nenhum outcome cannabis registrado</Typography>
            )}

            {/* Legacy Symptoms */}
            {outcomes?.legacy_symptoms && Object.keys(outcomes.legacy_symptoms).length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Sintomas (Legado)
                </Typography>
                {Object.entries(outcomes.legacy_symptoms).map(([name, data]) => (
                  <Box key={name} sx={{ mb: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2">{name}</Typography>
                      <Tooltip title={TREND_LABELS[data.trend]}>
                        {TREND_ICONS[data.trend]}
                      </Tooltip>
                    </Box>
                  </Box>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Timeline */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0 }}>
                <TimelineIcon color="primary" /> Linha do Tempo Unificada
              </Typography>
              <Button
                size="small"
                onClick={() => setExpandedTimeline(!expandedTimeline)}
                endIcon={expandedTimeline ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              >
                {expandedTimeline ? 'Recolher' : `Ver todos (${timeline?.total_events || 0})`}
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />
            {timeline?.events?.length > 0 ? (
              <List dense>
                {(expandedTimeline ? timeline.events : timeline.events.slice(0, 10)).map((event, i) => (
                  <ListItem key={i} divider>
                    <ListItemIcon>
                      {EVENT_ICONS[event.type] || <EventIcon />}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2" fontWeight="medium">{event.title}</Typography>
                          <Chip size="small" label={event.type.replace('_', ' ')} variant="outlined" />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(event.date)}
                          </Typography>
                          {event.description && (
                            <Typography variant="body2" color="text.secondary">
                              {event.description?.substring(0, 150)}{event.description?.length > 150 ? '...' : ''}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">Nenhum evento na timeline</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DigitalTwinPanel;
