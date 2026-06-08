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
  ListItemSecondaryAction,
  IconButton,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import {
  Add as AddIcon,
  LocalHospital as HospitalIcon,
  Medication as MedicationIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  Science as ScienceIcon
} from '@mui/icons-material';
import { cannabisService } from '../services/api';

const SEVERITY_COLORS = {
  low: 'info',
  medium: 'warning',
  high: 'error',
  critical: 'error'
};

const ENTRY_TYPE_LABELS = {
  administered: 'Administrada',
  skipped: 'Omitida',
  adjusted: 'Ajustada',
  prn: 'SOS/PRN'
};

const CannabisProfilePanel = ({ patientId }) => {
  const [profile, setProfile] = useState(null);
  const [doses, setDoses] = useState([]);
  const [outcomes, setOutcomes] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Dialog states
  const [openProfileDialog, setOpenProfileDialog] = useState(false);
  const [openDoseDialog, setOpenDoseDialog] = useState(false);
  const [openOutcomeDialog, setOpenOutcomeDialog] = useState(false);

  // Form states
  const [profileForm, setProfileForm] = useState({ primary_condition: '', notes: '' });
  const [doseForm, setDoseForm] = useState({
    patient_id: patientId,
    dose_mg: '',
    thc_mg: '',
    cbd_mg: '',
    entry_type: 'administered',
    reason: ''
  });
  const [outcomeForm, setOutcomeForm] = useState({
    patient_id: patientId,
    metric_name: '',
    score: '',
    max_score: 10,
    unit: '',
    context: ''
  });

  const fetchAll = async () => {
    setLoading(true);
    setError('');
    try {
      const [profileData, dosesData, outcomesData, alertsData, productsData] = await Promise.all([
        cannabisService.obterPerfil(patientId).catch(() => null),
        cannabisService.listarDoses(patientId).catch(() => []),
        cannabisService.listarOutcomes(patientId).catch(() => []),
        cannabisService.listarAlertas({ patient_id: patientId }).catch(() => []),
        cannabisService.listarProdutos().catch(() => [])
      ]);
      setProfile(profileData);
      setDoses(dosesData || []);
      setOutcomes(outcomesData || []);
      setAlerts(alertsData || []);
      setProducts(productsData || []);
    } catch (err) {
      console.error('Erro ao carregar perfil cannabis:', err);
      setError('Erro ao carregar dados do perfil cannabis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (patientId) fetchAll();
  }, [patientId]);

  const handleCreateProfile = async () => {
    try {
      await cannabisService.criarPerfil({
        patient_id: parseInt(patientId),
        primary_condition: profileForm.primary_condition,
        notes: profileForm.notes
      });
      setOpenProfileDialog(false);
      fetchAll();
    } catch (err) {
      setError(err?.error?.message || 'Erro ao criar perfil');
    }
  };

  const handleCreateDose = async () => {
    try {
      await cannabisService.criarDose(doseForm);
      setOpenDoseDialog(false);
      setDoseForm({ patient_id: patientId, dose_mg: '', thc_mg: '', cbd_mg: '', entry_type: 'administered', reason: '' });
      fetchAll();
    } catch (err) {
      setError(err?.error?.message || 'Erro ao registrar dose');
    }
  };

  const handleCreateOutcome = async () => {
    try {
      await cannabisService.criarOutcome(outcomeForm);
      setOpenOutcomeDialog(false);
      setOutcomeForm({ patient_id: patientId, metric_name: '', score: '', max_score: 10, unit: '', context: '' });
      fetchAll();
    } catch (err) {
      setError(err?.error?.message || 'Erro ao registrar outcome');
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await cannabisService.resolverAlerta(alertId);
      fetchAll();
    } catch (err) {
      setError(err?.error?.message || 'Erro ao resolver alerta');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  // No profile yet
  if (!profile) {
    return (
      <Box sx={{ width: '100%' }}>
        <Paper elevation={2} sx={{ p: 4, textAlign: 'center' }}>
          <ScienceIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Nenhum Perfil Cannabis
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Este paciente ainda não possui um perfil cannabis. Crie um para começar o acompanhamento.
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenProfileDialog(true)}
          >
            Criar Perfil Cannabis
          </Button>
        </Paper>

        <Dialog open={openProfileDialog} onClose={() => setOpenProfileDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Criar Perfil Cannabis</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Condição Primária"
              fullWidth
              value={profileForm.primary_condition}
              onChange={(e) => setProfileForm({ ...profileForm, primary_condition: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Observações"
              fullWidth
              multiline
              rows={3}
              value={profileForm.notes}
              onChange={(e) => setProfileForm({ ...profileForm, notes: e.target.value })}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenProfileDialog(false)}>Cancelar</Button>
            <Button onClick={handleCreateProfile} variant="contained">Criar</Button>
          </DialogActions>
        </Dialog>
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

      {/* Profile Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)', color: 'white' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ScienceIcon /> Perfil Cannabis
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.9 }}>
              {profile.primary_condition || 'Sem condição primária definida'}
            </Typography>
          </Box>
          <Chip
            label={profile.treatment_status === 'active' ? 'Ativo' : profile.treatment_status}
            sx={{
              backgroundColor: 'rgba(255,255,255,0.9)',
              color: profile.treatment_status === 'active' ? '#2e7d32' : '#666',
              fontWeight: 'bold'
            }}
          />
        </Box>
        {profile.started_at && (
          <Typography variant="caption" sx={{ opacity: 0.8, mt: 1, display: 'block' }}>
            Iniciado em: {formatDate(profile.started_at)}
          </Typography>
        )}
      </Paper>

      <Grid container spacing={3}>
        {/* Medications */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <MedicationIcon color="primary" /> Medicações
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {profile.medications?.length > 0 ? (
              profile.medications.map((med) => (
                <Card key={med.id} variant="outlined" sx={{ mb: 1 }}>
                  <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
                    <Typography variant="body2" fontWeight="medium">
                      {med.product?.name || 'Produto desconhecido'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {med.prescribed_dose_mg}mg — {med.frequency}
                    </Typography>
                    <Chip size="small" label={med.status} color={med.status === 'active' ? 'success' : 'default'} sx={{ mt: 0.5 }} />
                  </CardContent>
                </Card>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">Nenhuma medicação registrada</Typography>
            )}
          </Paper>
        </Grid>

        {/* Alerts */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WarningIcon color="warning" /> Alertas
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {alerts.length > 0 ? (
              alerts.map((alert) => (
                <Alert
                  key={alert.id}
                  severity={SEVERITY_COLORS[alert.severity] || 'info'}
                  action={
                    alert.status === 'active' && (
                      <Button size="small" onClick={() => handleResolveAlert(alert.id)}>
                        Resolver
                      </Button>
                    )
                  }
                  sx={{ mb: 1 }}
                >
                  <Typography variant="body2" fontWeight="medium">{alert.title}</Typography>
                  <Typography variant="caption">{alert.description}</Typography>
                </Alert>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">Nenhum alerta ativo</Typography>
            )}
          </Paper>
        </Grid>

        {/* Doses */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <HospitalIcon color="primary" /> Registro de Doses
              </Typography>
              <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => setOpenDoseDialog(true)}>
                Nova Dose
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />
            {doses.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Data</TableCell>
                      <TableCell>Tipo</TableCell>
                      <TableCell>Dose (mg)</TableCell>
                      <TableCell>THC (mg)</TableCell>
                      <TableCell>CBD (mg)</TableCell>
                      <TableCell>Motivo</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {doses.map((dose) => (
                      <TableRow key={dose.id}>
                        <TableCell>{formatDate(dose.entry_date)}</TableCell>
                        <TableCell>
                          <Chip size="small" label={ENTRY_TYPE_LABELS[dose.entry_type] || dose.entry_type} />
                        </TableCell>
                        <TableCell>{dose.dose_mg || '-'}</TableCell>
                        <TableCell>{dose.thc_mg || '-'}</TableCell>
                        <TableCell>{dose.cbd_mg || '-'}</TableCell>
                        <TableCell>{dose.reason || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography variant="body2" color="text.secondary">Nenhuma dose registrada</Typography>
            )}
          </Paper>
        </Grid>

        {/* Outcomes */}
        <Grid item xs={12}>
          <Paper elevation={2} sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssessmentIcon color="primary" /> Outcomes
              </Typography>
              <Button variant="contained" size="small" startIcon={<AddIcon />} onClick={() => setOpenOutcomeDialog(true)}>
                Novo Outcome
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />
            {outcomes.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Data</TableCell>
                      <TableCell>Métrica</TableCell>
                      <TableCell>Score</TableCell>
                      <TableCell>Unidade</TableCell>
                      <TableCell>Contexto</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {outcomes.map((outcome) => (
                      <TableRow key={outcome.id}>
                        <TableCell>{formatDate(outcome.recorded_at)}</TableCell>
                        <TableCell>{outcome.metric_name}</TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={`${outcome.score}/${outcome.max_score}`}
                            color={outcome.score > outcome.max_score * 0.7 ? 'error' : outcome.score > outcome.max_score * 0.4 ? 'warning' : 'success'}
                          />
                        </TableCell>
                        <TableCell>{outcome.unit || '-'}</TableCell>
                        <TableCell>{outcome.context || '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography variant="body2" color="text.secondary">Nenhum outcome registrado</Typography>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Dose Dialog */}
      <Dialog open={openDoseDialog} onClose={() => setOpenDoseDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nova Dose</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={6}>
              <TextField label="Dose (mg)" type="number" fullWidth value={doseForm.dose_mg} onChange={(e) => setDoseForm({ ...doseForm, dose_mg: parseFloat(e.target.value) || '' })} />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Tipo</InputLabel>
                <Select value={doseForm.entry_type} label="Tipo" onChange={(e) => setDoseForm({ ...doseForm, entry_type: e.target.value })}>
                  {Object.entries(ENTRY_TYPE_LABELS).map(([key, label]) => (
                    <MenuItem key={key} value={key}>{label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField label="THC (mg)" type="number" fullWidth value={doseForm.thc_mg} onChange={(e) => setDoseForm({ ...doseForm, thc_mg: parseFloat(e.target.value) || '' })} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="CBD (mg)" type="number" fullWidth value={doseForm.cbd_mg} onChange={(e) => setDoseForm({ ...doseForm, cbd_mg: parseFloat(e.target.value) || '' })} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Motivo / Observação" fullWidth multiline rows={2} value={doseForm.reason} onChange={(e) => setDoseForm({ ...doseForm, reason: e.target.value })} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDoseDialog(false)}>Cancelar</Button>
          <Button onClick={handleCreateDose} variant="contained">Registrar</Button>
        </DialogActions>
      </Dialog>

      {/* Outcome Dialog */}
      <Dialog open={openOutcomeDialog} onClose={() => setOpenOutcomeDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Novo Outcome</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12}>
              <TextField label="Nome da Métrica" fullWidth value={outcomeForm.metric_name} onChange={(e) => setOutcomeForm({ ...outcomeForm, metric_name: e.target.value })} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Score" type="number" fullWidth value={outcomeForm.score} onChange={(e) => setOutcomeForm({ ...outcomeForm, score: parseFloat(e.target.value) || '' })} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Score Máximo" type="number" fullWidth value={outcomeForm.max_score} onChange={(e) => setOutcomeForm({ ...outcomeForm, max_score: parseFloat(e.target.value) || 10 })} />
            </Grid>
            <Grid item xs={6}>
              <TextField label="Unidade" fullWidth value={outcomeForm.unit} onChange={(e) => setOutcomeForm({ ...outcomeForm, unit: e.target.value })} />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Contexto" fullWidth multiline rows={2} value={outcomeForm.context} onChange={(e) => setOutcomeForm({ ...outcomeForm, context: e.target.value })} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenOutcomeDialog(false)}>Cancelar</Button>
          <Button onClick={handleCreateOutcome} variant="contained">Registrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CannabisProfilePanel;
