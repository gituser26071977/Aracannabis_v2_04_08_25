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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  LinearProgress,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import {
  Add as AddIcon,
  Timeline as TimelineIcon,
  CheckCircle as CheckCircleIcon,
  RadioButtonUnchecked as PendingIcon,
  Warning as WarningIcon,
  Assignment as AssignmentIcon,
  Event as EventIcon,
  Flag as FlagIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  DoneAll as DoneAllIcon
} from '@mui/icons-material';
import { followupService } from '../services/api';

const STATUS_COLORS = {
  active: 'success',
  paused: 'warning',
  completed: 'info',
  cancelled: 'error'
};

const STATUS_ICONS = {
  active: <PlayIcon fontSize="small" />,
  paused: <PauseIcon fontSize="small" />,
  completed: <DoneAllIcon fontSize="small" />,
  cancelled: <WarningIcon fontSize="small" />
};

const STATUS_LABELS = {
  active: 'Ativo',
  paused: 'Pausado',
  completed: 'Concluído',
  cancelled: 'Cancelado'
};

const SEVERITY_COLORS = {
  low: 'info',
  medium: 'warning',
  high: 'error',
  critical: 'error'
};

const FollowupPanel = ({ patientId }) => {
  const [programs, setPrograms] = useState([]);
  const [checkpoints, setCheckpoints] = useState([]);
  const [questionnaires, setQuestionnaires] = useState([]);
  const [responses, setResponses] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Dialog states
  const [openProgramDialog, setOpenProgramDialog] = useState(false);
  const [programForm, setProgramForm] = useState({
    patient_id: parseInt(patientId),
    name: '',
    specialty_code: 'cannabis',
    status: 'active'
  });

  const fetchAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [programsData, checkpointsData, questionnairesData, responsesData, alertsData] = await Promise.all([
        followupService.listarProgramas(patientId).catch(() => []),
        followupService.listarCheckpoints({}).catch(() => []),
        followupService.listarQuestionarios().catch(() => []),
        followupService.listarRespostas({ patient_id: patientId }).catch(() => []),
        followupService.listarAlertas({ patient_id: patientId }).catch(() => [])
      ]);
      setPrograms(programsData || []);
      setCheckpoints(checkpointsData || []);
      setQuestionnaires(questionnairesData || []);
      setResponses(responsesData || []);
      setAlerts(alertsData || []);
    } catch (err) {
      if(process.env.NODE_ENV!=='production')console.error('Erro ao carregar follow-up:', err);
      setError('Erro ao carregar dados de acompanhamento');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (patientId) fetchAll();
  }, [patientId]);

  const handleCreateProgram = async () => {
    try {
      await followupService.criarPrograma(programForm);
      setOpenProgramDialog(false);
      setProgramForm({ patient_id: parseInt(patientId), name: '', specialty_code: 'cannabis', status: 'active' });
      fetchAll();
    } catch (err) {
      setError(err?.error?.message || 'Erro ao criar programa');
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await followupService.resolverAlerta(alertId);
      fetchAll();
    } catch (err) {
      setError(err?.error?.message || 'Erro ao resolver alerta');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric'
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimelineIcon /> Acompanhamento
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              Programas de acompanhamento e checkpoints do paciente
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenProgramDialog(true)}
            sx={{ backgroundColor: 'rgba(255,255,255,0.9)', color: '#764ba2', '&:hover': { backgroundColor: 'white' } }}
          >
            Novo Programa
          </Button>
        </Box>
      </Paper>

      {programs.length === 0 ? (
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
          <FlagIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Nenhum Programa de Acompanhamento
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Este paciente ainda não está em nenhum programa de acompanhamento.
          </Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpenProgramDialog(true)}>
            Criar Programa
          </Button>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {/* Programs */}
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PlayIcon color="primary" /> Programas Ativos
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Grid container spacing={2}>
                {programs.map((program) => {
                  const programCheckpoints = checkpoints.filter(cp => cp.program_id === program.id);
                  const completedCp = programCheckpoints.filter(cp => cp.status === 'completed').length;
                  const totalCp = programCheckpoints.length;
                  const progress = totalCp > 0 ? (completedCp / totalCp) * 100 : 0;

                  return (
                    <Grid item xs={12} md={6} key={program.id}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                            <Typography variant="h6" fontSize="1.1rem">{program.name}</Typography>
                            <Chip
                              size="small"
                              icon={STATUS_ICONS[program.status]}
                              label={STATUS_LABELS[program.status] || program.status}
                              color={STATUS_COLORS[program.status] || 'default'}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            Especialidade: {program.specialty_code}
                          </Typography>
                          <Box sx={{ mt: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                              <Typography variant="caption">Progresso</Typography>
                              <Typography variant="caption">{completedCp}/{totalCp} checkpoints</Typography>
                            </Box>
                            <LinearProgress
                              variant="determinate"
                              value={progress}
                              sx={{ height: 8, borderRadius: 4 }}
                            />
                          </Box>
                          {program.started_at && (
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                              Iniciado: {formatDate(program.started_at)}
                            </Typography>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            </Paper>
          </Grid>

          {/* Checkpoints */}
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <EventIcon color="primary" /> Checkpoints
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {checkpoints.length > 0 ? (
                <List dense>
                  {checkpoints.map((cp) => (
                    <ListItem key={cp.id} divider>
                      <ListItemIcon>
                        {cp.status === 'completed' ? <CheckCircleIcon color="success" /> : <PendingIcon color="action" />}
                      </ListItemIcon>
                      <ListItemText
                        primary={cp.name}
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              {cp.description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Vencimento: {formatDate(cp.due_date)}
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip size="small" label={cp.status} color={cp.status === 'completed' ? 'success' : 'warning'} />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">Nenhum checkpoint definido</Typography>
              )}
            </Paper>
          </Grid>

          {/* Questionnaires & Responses */}
          <Grid item xs={12} md={6}>
            <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssignmentIcon color="primary" /> Questionários & Respostas
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {questionnaires.length > 0 ? (
                <List dense>
                  {questionnaires.map((qn) => {
                    const qnResponses = responses.filter(r => r.questionnaire_id === qn.id);
                    return (
                      <ListItem key={qn.id} divider>
                        <ListItemText
                          primary={qn.name}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {qn.description}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {qn.questions?.length || 0} questões | {qnResponses.length} respostas
                              </Typography>
                            </Box>
                          }
                        />
                        <Chip size="small" label={qn.status} color={qn.status === 'active' ? 'success' : 'default'} />
                      </ListItem>
                    );
                  })}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary">Nenhum questionário definido</Typography>
              )}

              {responses.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Respostas Recentes
                  </Typography>
                  {responses.slice(0, 5).map((resp) => (
                    <Paper key={resp.id} variant="outlined" sx={{ p: 1, mb: 1 }}>
                      <Typography variant="body2">
                        <strong>{resp.value}</strong> {resp.numeric_value !== null && `(${resp.numeric_value})`}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(resp.responded_at)} — por {resp.responded_by}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              )}
            </Paper>
          </Grid>

          {/* Alerts */}
          <Grid item xs={12}>
            <Paper elevation={2} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon color="warning" /> Alertas de Acompanhamento
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {alerts.length > 0 ? (
                <Grid container spacing={2}>
                  {alerts.map((alert) => (
                    <Grid item xs={12} md={6} key={alert.id}>
                      <Alert
                        severity={SEVERITY_COLORS[alert.severity] || 'info'}
                        action={
                          alert.status === 'active' && (
                            <Button size="small" onClick={() => handleResolveAlert(alert.id)}>
                              Resolver
                            </Button>
                          )
                        }
                      >
                        <Typography variant="body2" fontWeight="medium">{alert.title}</Typography>
                        <Typography variant="caption">{alert.description}</Typography>
                      </Alert>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography variant="body2" color="text.secondary">Nenhum alerta de acompanhamento</Typography>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Program Dialog */}
      <Dialog open={openProgramDialog} onClose={() => setOpenProgramDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Novo Programa de Acompanhamento</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Nome do Programa"
            fullWidth
            value={programForm.name}
            onChange={(e) => setProgramForm({ ...programForm, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Especialidade</InputLabel>
            <Select
              value={programForm.specialty_code}
              label="Especialidade"
              onChange={(e) => setProgramForm({ ...programForm, specialty_code: e.target.value })}
            >
              <MenuItem value="cannabis">Cannabis</MenuItem>
              <MenuItem value="general">Geral</MenuItem>
              <MenuItem value="pain">Dor</MenuItem>
              <MenuItem value="mental_health">Saúde Mental</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              value={programForm.status}
              label="Status"
              onChange={(e) => setProgramForm({ ...programForm, status: e.target.value })}
            >
              <MenuItem value="active">Ativo</MenuItem>
              <MenuItem value="paused">Pausado</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenProgramDialog(false)}>Cancelar</Button>
          <Button onClick={handleCreateProgram} variant="contained">Criar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FollowupPanel;
