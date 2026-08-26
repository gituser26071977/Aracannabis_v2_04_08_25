import React, { useState, useEffect, useMemo } from 'react';
import {
  Typography,
  Box,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Chip,
} from '@mui/material';
import { useParams, Link } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { prontuarioService, pacientesService } from '../services/api';
import ArrowBack from '@mui/icons-material/ArrowBack';

// Séries disponíveis (nome -> rótulo e cor)
const SERIES_VITAIS = [
  { key: 'peso', label: 'Peso (kg)', color: '#1976d2', unit: 'kg' },
  { key: 'imc', label: 'IMC', color: '#2e7d32', unit: '' },
  { key: 'fc', label: 'FC (bpm)', color: '#d32f2f', unit: 'bpm' },
  { key: 'pa_sistolica', label: 'PA Sistólica (mmHg)', color: '#ed6c02', unit: 'mmHg' },
  { key: 'pa_diastolica', label: 'PA Diastólica (mmHg)', color: '#9c27b0', unit: 'mmHg' },
  { key: 'temperatura', label: 'Temperatura (°C)', color: '#00897b', unit: '°C' },
  { key: 'spo2', label: 'SpO2 (%)', color: '#5e35b1', unit: '%' },
  { key: 'glicemia', label: 'Glicemia (mg/dL)', color: '#e91e63', unit: 'mg/dL' },
];

const SINTOMA_CORES = [
  '#1976d2',
  '#2e7d32',
  '#d32f2f',
  '#ed6c02',
  '#9c27b0',
  '#00897b',
  '#5e35b1',
  '#e91e63',
  '#795548',
];

const TrendsPage = () => {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [serieSelecionada, setSerieSelecionada] = useState('imc');
  const [sintomasSelecionados, setSintomasSelecionados] = useState([]);
  const [testesLab, setTestesLab] = useState([]);
  const [testeLabSelecionado, setTesteLabSelecionado] = useState('');

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [p, t] = await Promise.all([
          pacientesService.obter(patientId),
          prontuarioService.tendencias(patientId),
        ]);
        if (active) {
          setPatient(p.paciente || p);
          setData(t);
          const sintomas = Object.keys(t.series.sintomas || {});
          if (sintomas.length) setSintomasSelecionados([sintomas[0]]);
          const labs = Object.keys(t.series.exames_laboratoriais || {});
          setTestesLab(labs);
          if (labs.length) setTesteLabSelecionado(labs[0]);
        }
      } catch (err) {
        if (active) setError(err.error || 'Erro ao carregar tendências');
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [patientId]);

  const dadosSerie = useMemo(() => {
    if (!data) return [];
    const pts = (data.series[serieSelecionada] || []).map((p) => ({
      data: p.data ? new Date(p.data).toLocaleDateString('pt-BR') : '',
      valor: p.valor,
    }));
    return pts;
  }, [data, serieSelecionada]);

  const dadosSintomas = useMemo(() => {
    if (!data) return [];
    const agrupado = {};
    for (const nome of sintomasSelecionados) {
      for (const p of data.series.sintomas[nome] || []) {
        const key = p.data ? new Date(p.data).toLocaleDateString('pt-BR') : '';
        agrupado[key] = agrupado[key] || { data: key };
        agrupado[key][nome] = p.valor;
      }
    }
    return Object.values(agrupado);
  }, [data, sintomasSelecionados]);

  const dadosLab = useMemo(() => {
    if (!data || !testeLabSelecionado) return [];
    return (data.series.exames_laboratoriais[testeLabSelecionado] || []).map((p) => ({
      data: p.data ? new Date(p.data).toLocaleDateString('pt-BR') : '',
      valor: p.valor,
      referencia: p.referencia,
    }));
  }, [data, testeLabSelecionado]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 6 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 3 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Link to={`/pacientes/detail/${patientId}`} style={{ display: 'flex', color: 'inherit' }}>
          <ArrowBack />
        </Link>
        <Typography variant="h5">Tendências Clínicas</Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {patient?.nome || 'Paciente'} — evolução de dados clínicos ao longo do tempo
      </Typography>

      <Grid container spacing={2}>
        {/* Sinais vitais */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                📏 Sinais Vitais
              </Typography>
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Métrica</InputLabel>
                <Select
                  value={serieSelecionada}
                  onChange={(e) => setSerieSelecionada(e.target.value)}
                  label="Métrica"
                >
                  {SERIES_VITAIS.map((s) => (
                    <MenuItem key={s.key} value={s.key}>
                      {s.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {dadosSerie.length === 0 ? (
                <Alert severity="info" sx={{ mt: 1 }}>
                  Sem medições desta métrica.
                </Alert>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={dadosSerie}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="data" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="valor"
                      name={
                        SERIES_VITAIS.find((s) => s.key === serieSelecionada)?.label ||
                        serieSelecionada
                      }
                      stroke={
                        SERIES_VITAIS.find((s) => s.key === serieSelecionada)?.color || '#1976d2'
                      }
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Exames laboratoriais */}
        <Grid item xs={12} md={6}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                🧪 Exames Laboratoriais
              </Typography>
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Teste</InputLabel>
                <Select
                  value={testeLabSelecionado}
                  onChange={(e) => setTesteLabSelecionado(e.target.value)}
                  label="Teste"
                >
                  {testesLab.length === 0 && <MenuItem value="">—</MenuItem>}
                  {testesLab.map((t) => (
                    <MenuItem key={t} value={t}>
                      {t}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              {!testeLabSelecionado || dadosLab.length === 0 ? (
                <Alert severity="info" sx={{ mt: 1 }}>
                  {testesLab.length === 0
                    ? 'Nenhum exame laboratorial registrado.'
                    : 'Sem dados deste teste.'}
                </Alert>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={dadosLab}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="data" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="valor"
                      name={testeLabSelecionado}
                      stroke="#00897b"
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Sintomas */}
        <Grid item xs={12}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                😣 Evolução de Sintomas (0-10)
              </Typography>
              <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {Object.keys(data?.series?.sintomas || {}).map((nome, i) => (
                  <Chip
                    key={nome}
                    label={nome}
                    clickable
                    color={sintomasSelecionados.includes(nome) ? 'primary' : 'default'}
                    onClick={() =>
                      setSintomasSelecionados((prev) =>
                        prev.includes(nome) ? prev.filter((n) => n !== nome) : [...prev, nome],
                      )
                    }
                  />
                ))}
                {Object.keys(data?.series?.sintomas || {}).length === 0 && (
                  <Alert severity="info">Nenhum sintoma registrado.</Alert>
                )}
              </Box>
              {dadosSintomas.length > 0 && sintomasSelecionados.length > 0 && (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={dadosSintomas}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="data" />
                    <YAxis domain={[0, 10]} />
                    <Tooltip />
                    <Legend />
                    {sintomasSelecionados.map((nome, i) => (
                      <Line
                        key={nome}
                        type="monotone"
                        dataKey={nome}
                        stroke={SINTOMA_CORES[i % SINTOMA_CORES.length]}
                        dot={{ r: 3 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default TrendsPage;
