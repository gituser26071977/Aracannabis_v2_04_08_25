import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Box,
  Card,
  CardContent,
  Divider,
  Chip,
  IconButton,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Favorite as VitalIcon,
  Healing as ExameFisicoIcon,
  Biotech as DiagnosticoIcon,
} from '@mui/icons-material';
import { prontuarioService } from '../services/api';
import useNotifier from '../hooks/useNotifier';

const SISTEMAS = [
  { value: 'geral', label: 'Geral / Estado geral' },
  { value: 'cardiovascular', label: 'Cardiovascular' },
  { value: 'respiratorio', label: 'Respiratório' },
  { value: 'abdominal', label: 'Abdominal' },
  { value: 'neurologico', label: 'Neurológico' },
  { value: 'pele', label: 'Pele' },
  { value: 'osteomuscular', label: 'Osteomuscular' },
  { value: 'cabeca_pescoco', label: 'Cabeça e Pescoço' },
  { value: 'geniturinario', label: 'Geniturinário' },
  { value: 'outros', label: 'Outros' },
];

const camposVitais = [
  { name: 'pa_sistolica', label: 'PA sistólica (mmHg)' },
  { name: 'pa_diastolica', label: 'PA diastólica (mmHg)' },
  { name: 'fc', label: 'FC (bpm)' },
  { name: 'fr', label: 'FR (irpm)' },
  { name: 'temperatura', label: 'Temp. (°C)' },
  { name: 'spo2', label: 'SpO2 (%)' },
  { name: 'glicemia', label: 'Glicemia (mg/dL)' },
  { name: 'peso', label: 'Peso (kg)' },
  { name: 'altura', label: 'Altura (m)' },
];

const ProntuarioEstruturadoPanel = ({ patientId }) => {
  const { notify, NotifierElement } = useNotifier();
  const [loading, setLoading] = useState(true);

  // Sinais vitais
  const [sinaisVitais, setSinaisVitais] = useState([]);
  const [vital, setVital] = useState({
    pa_sistolica: '',
    pa_diastolica: '',
    fc: '',
    fr: '',
    temperatura: '',
    spo2: '',
    glicemia: '',
    peso: '',
    altura: '',
    data_medicao: new Date().toISOString().slice(0, 16),
  });

  // Exame físico
  const [exameFisico, setExameFisico] = useState([]);
  const [sistemasForm, setSistemasForm] = useState([{ sistema: 'geral', achados: '' }]);

  // Diagnósticos
  const [diagnosticos, setDiagnosticos] = useState([]);
  const [diag, setDiag] = useState({
    cid: '',
    descricao: '',
    tipo: 'hipotese',
    data_diagnostico: new Date().toISOString().slice(0, 10),
  });
  const [cidSuggestions, setCidSuggestions] = useState([]);

  const carregarTudo = async () => {
    setLoading(true);
    try {
      const [v, e, d] = await Promise.all([
        prontuarioService.listarSinaisVitais(patientId, 20),
        prontuarioService.listarExameFisico(patientId, 50),
        prontuarioService.listarDiagnosticos(patientId),
      ]);
      setSinaisVitais(v.sinais_vitais || []);
      setExameFisico(e.exame_fisico || []);
      setDiagnosticos(d.diagnosticos || []);
    } catch (err) {
      notify(err.error || 'Erro ao carregar prontuário estruturado', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    carregarTudo(); // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  // ── Sinais vitais ──
  const handleVitalChange = (e) => setVital({ ...vital, [e.target.name]: e.target.value });
  const handleVitalSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await prontuarioService.criarSinaisVitais(patientId, vital);
      notify(
        res.imc_calculado
          ? `Sinais vitais registrados (IMC ${res.imc_calculado})`
          : 'Sinais vitais registrados',
        'success',
      );
      setVital({
        pa_sistolica: '',
        pa_diastolica: '',
        fc: '',
        fr: '',
        temperatura: '',
        spo2: '',
        glicemia: '',
        peso: '',
        altura: '',
        data_medicao: new Date().toISOString().slice(0, 16),
      });
      carregarTudo();
    } catch (err) {
      notify(err.error || 'Erro ao registrar sinais vitais', 'error');
    }
  };
  const handleVitalDelete = async (id) => {
    try {
      await prontuarioService.excluirSinaisVitais(id);
      carregarTudo();
    } catch (err) {
      notify(err.error || 'Erro ao excluir medição', 'error');
    }
  };

  // ── Exame físico ──
  const handleSistemaChange = (idx, field, value) => {
    const next = [...sistemasForm];
    next[idx] = { ...next[idx], [field]: value };
    setSistemasForm(next);
  };
  const addSistema = () => setSistemasForm([...sistemasForm, { sistema: 'geral', achados: '' }]);
  const removeSistema = (idx) => setSistemasForm(sistemasForm.filter((_, i) => i !== idx));
  const handleExameFisicoSubmit = async (e) => {
    e.preventDefault();
    const validos = sistemasForm.filter((s) => (s.achados || '').trim());
    if (!validos.length) {
      notify('Preencha ao menos um sistema com achados', 'warning');
      return;
    }
    try {
      await prontuarioService.criarExameFisico(patientId, validos);
      notify('Exame físico registrado', 'success');
      setSistemasForm([{ sistema: 'geral', achados: '' }]);
      carregarTudo();
    } catch (err) {
      notify(err.error || 'Erro ao registrar exame físico', 'error');
    }
  };
  const handleExameFisicoDelete = async (id) => {
    try {
      await prontuarioService.excluirExameFisico(id);
      carregarTudo();
    } catch (err) {
      notify(err.error || 'Erro ao excluir registro', 'error');
    }
  };

  // ── Diagnósticos ──
  const handleDiagChange = (e) => {
    const val = e.target.value;
    setDiag({ ...diag, [e.target.name]: val });
    if (e.target.name === 'cid' && val) {
      prontuarioService
        .autocompleteCid(val)
        .then((r) => setCidSuggestions(r.cids || []))
        .catch(() => {});
    } else {
      setCidSuggestions([]);
    }
  };
  const handleDiagSubmit = async (e) => {
    e.preventDefault();
    if (!diag.descricao.trim()) {
      notify('Descrição do diagnóstico é obrigatória', 'warning');
      return;
    }
    try {
      await prontuarioService.criarDiagnostico(patientId, diag);
      notify('Diagnóstico registrado', 'success');
      setDiag({
        cid: '',
        descricao: '',
        tipo: 'hipotese',
        data_diagnostico: new Date().toISOString().slice(0, 10),
      });
      setCidSuggestions([]);
      carregarTudo();
    } catch (err) {
      notify(err.error || 'Erro ao registrar diagnóstico', 'error');
    }
  };
  const handleDiagDelete = async (id) => {
    try {
      await prontuarioService.excluirDiagnostico(id);
      carregarTudo();
    } catch (err) {
      notify(err.error || 'Erro ao desativar diagnóstico', 'error');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
      <NotifierElement />
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <DiagnosticoIcon sx={{ mr: 1, color: 'primary.main' }} /> Prontuário Estruturado
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Dados clínicos estruturados por medição, sistema e diagnóstico — base para tendências ao
        longo do tempo.
      </Typography>

      {/* ─── Sinais Vitais ─── */}
      <Card variant="outlined" sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
            <VitalIcon sx={{ mr: 1, color: 'error.main' }} /> Sinais Vitais
          </Typography>
          <Box component="form" onSubmit={handleVitalSubmit} sx={{ mt: 1 }}>
            <Grid container spacing={2}>
              {camposVitais.map((c) => (
                <Grid item xs={6} sm={4} md={3} key={c.name}>
                  <TextField
                    name={c.name}
                    label={c.label}
                    type="number"
                    value={vital[c.name]}
                    onChange={handleVitalChange}
                    fullWidth
                    size="small"
                  />
                </Grid>
              ))}
            </Grid>
            <Box sx={{ mt: 1 }}>
              <TextField
                name="data_medicao"
                label="Data/hora da medição"
                type="datetime-local"
                value={vital.data_medicao}
                onChange={handleVitalChange}
                size="small"
              />
              <Button type="submit" variant="contained" startIcon={<AddIcon />} sx={{ ml: 1 }}>
                Registrar
              </Button>
            </Box>
          </Box>
          {sinaisVitais.length > 0 && (
            <TableContainer sx={{ mt: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>PA</TableCell>
                    <TableCell>FC</TableCell>
                    <TableCell>FR</TableCell>
                    <TableCell>T°C</TableCell>
                    <TableCell>SpO2</TableCell>
                    <TableCell>Peso</TableCell>
                    <TableCell>IMC</TableCell>
                    <TableCell />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sinaisVitais
                    .slice()
                    .reverse()
                    .map((v) => (
                      <TableRow key={v.id}>
                        <TableCell>{new Date(v.data_medicao).toLocaleString('pt-BR')}</TableCell>
                        <TableCell>
                          {v.pa_sistolica && v.pa_diastolica
                            ? `${v.pa_sistolica}/${v.pa_diastolica}`
                            : '-'}
                        </TableCell>
                        <TableCell>{v.fc || '-'}</TableCell>
                        <TableCell>{v.fr || '-'}</TableCell>
                        <TableCell>{v.temperatura || '-'}</TableCell>
                        <TableCell>{v.spo2 || '-'}</TableCell>
                        <TableCell>{v.peso || '-'}</TableCell>
                        <TableCell>
                          <Chip
                            label={v.imc || '-'}
                            size="small"
                            color={v.imc ? 'primary' : 'default'}
                          />
                        </TableCell>
                        <TableCell>
                          <IconButton size="small" onClick={() => handleVitalDelete(v.id)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* ─── Exame Físico ─── */}
      <Card variant="outlined" sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
            <ExameFisicoIcon sx={{ mr: 1, color: 'success.main' }} /> Exame Físico (por sistema)
          </Typography>
          <Box component="form" onSubmit={handleExameFisicoSubmit} sx={{ mt: 1 }}>
            {sistemasForm.map((s, idx) => (
              <Box key={idx} sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                <FormControl size="small" sx={{ minWidth: 200 }}>
                  <InputLabel>Sistema</InputLabel>
                  <Select
                    value={s.sistema}
                    onChange={(e) => handleSistemaChange(idx, 'sistema', e.target.value)}
                    label="Sistema"
                  >
                    {SISTEMAS.map((opt) => (
                      <MenuItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <TextField
                  label="Achados"
                  value={s.achados}
                  onChange={(e) => handleSistemaChange(idx, 'achados', e.target.value)}
                  fullWidth
                  size="small"
                  multiline
                  minRows={1}
                />
                {sistemasForm.length > 1 && (
                  <IconButton size="small" onClick={() => removeSistema(idx)}>
                    <DeleteIcon />
                  </IconButton>
                )}
              </Box>
            ))}
            <Button size="small" onClick={addSistema} startIcon={<AddIcon />} sx={{ mr: 1 }}>
              + Sistema
            </Button>
            <Button type="submit" variant="contained" size="small">
              Registrar
            </Button>
          </Box>
          {exameFisico.length > 0 && (
            <Box sx={{ mt: 2 }}>
              {exameFisico
                .slice()
                .reverse()
                .map((e) => (
                  <Box
                    key={e.id}
                    sx={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: 1,
                      mb: 1,
                      p: 1,
                      bgcolor: 'background.default',
                      borderRadius: 1,
                    }}
                  >
                    <Chip
                      label={SISTEMAS.find((s) => s.value === e.sistema)?.label || e.sistema}
                      size="small"
                      color="success"
                    />
                    <Typography variant="body2" sx={{ flex: 1 }}>
                      {e.achados || '-'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(e.data_exame).toLocaleDateString('pt-BR')}
                    </Typography>
                    <IconButton size="small" onClick={() => handleExameFisicoDelete(e.id)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                ))}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* ─── Diagnósticos ─── */}
      <Card variant="outlined" sx={{ mt: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
            <DiagnosticoIcon sx={{ mr: 1, color: 'info.main' }} /> Diagnósticos (CID)
          </Typography>
          <Box component="form" onSubmit={handleDiagSubmit} sx={{ mt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={3}>
                <TextField
                  name="cid"
                  label="CID"
                  value={diag.cid}
                  onChange={handleDiagChange}
                  fullWidth
                  size="small"
                  placeholder="ex.: F41.2"
                  helperText={
                    cidSuggestions.length
                      ? `Sugestões: ${cidSuggestions
                          .slice(0, 3)
                          .map((c) => c.cid)
                          .join(', ')}`
                      : 'Autocomplete por prefixo (ex.: F, F4)'
                  }
                />
              </Grid>
              <Grid item xs={12} sm={5}>
                <TextField
                  name="descricao"
                  label="Descrição do diagnóstico"
                  value={diag.descricao}
                  onChange={handleDiagChange}
                  fullWidth
                  size="small"
                  required
                />
              </Grid>
              <Grid item xs={12} sm={2}>
                <FormControl fullWidth size="small">
                  <InputLabel>Tipo</InputLabel>
                  <Select name="tipo" value={diag.tipo} onChange={handleDiagChange} label="Tipo">
                    <MenuItem value="hipotese">Hipótese</MenuItem>
                    <MenuItem value="definitivo">Definitivo</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={2} sx={{ display: 'flex', alignItems: 'center' }}>
                <Button type="submit" variant="contained" startIcon={<AddIcon />} fullWidth>
                  Adicionar
                </Button>
              </Grid>
            </Grid>
          </Box>
          {diagnosticos.length > 0 && (
            <Box sx={{ mt: 2 }}>
              {diagnosticos.map((d) => (
                <Box
                  key={d.id}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1,
                    p: 1,
                    bgcolor: 'background.default',
                    borderRadius: 1,
                  }}
                >
                  <Chip
                    label={d.cid || '—'}
                    size="small"
                    color={d.tipo === 'definitivo' ? 'info' : 'warning'}
                  />
                  <Typography variant="body2" sx={{ flex: 1 }}>
                    {d.descricao}
                  </Typography>
                  <Chip label={d.tipo} size="small" variant="outlined" />
                  <Typography variant="caption" color="text.secondary">
                    {new Date(d.data_diagnostico).toLocaleDateString('pt-BR')}
                  </Typography>
                  <IconButton size="small" onClick={() => handleDiagDelete(d.id)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
              ))}
            </Box>
          )}
        </CardContent>
      </Card>

      <Divider sx={{ my: 2 }} />
    </Paper>
  );
};

export default ProntuarioEstruturadoPanel;
