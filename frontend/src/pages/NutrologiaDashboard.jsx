/**
 * Dashboard de Nutrologia - AraOS
 *
 * Dashboard completo com:
 * - Gráficos de tendências de peso/IMC
 * - Gráficos de evolução de exames laboratoriais
 * - Bioimpedância
 * - Metas e progresso
 *
 * Migrado de antd → MUI em 2026-06-11.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  MenuItem,
  TextField,
  Divider,
  Alert,
  AlertTitle,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  ShowChart as LineChartIcon,
  EmojiEvents as TrophyIcon,
  AccessTime as ClockIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import {
  Line, Bar, Doughnut,
} from 'react-chartjs-2';
import api from '../services/api';

const PERIODOS = [
  { value: 3, label: 'Últimos 3 meses' },
  { value: 6, label: 'Últimos 6 meses' },
  { value: 12, label: 'Último ano' },
];

const PARAMETROS = [
  { value: 'peso', label: 'Peso/IMC' },
  { value: 'glicemia_jejum', label: 'Glicemia' },
  { value: 'colesterol_total', label: 'Colesterol' },
  { value: 'vitamina_d', label: 'Vitamina D' },
];

const EXAMES_FAKE = [
  { data: '15/05/2026', exame: 'Hemograma', status: 'normal', observacao: 'Sem alterações' },
  { data: '15/05/2026', exame: 'Perfil Lipídico', status: 'alterado', observacao: 'LDL elevado' },
  { data: '15/05/2026', exame: 'Glicemia', status: 'normal', observacao: 'Dentro do normal' },
  { data: '15/05/2026', exame: 'Vitamina D', status: 'alterado', observacao: 'Insuficiência' },
  { data: '15/05/2026', exame: 'TSH', status: 'normal', observacao: 'Eutireoidismo' },
];

const NutrologiaDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [pacientes] = useState([
    { id: '1', label: 'Maria Silva - 45 anos' },
    { id: '2', label: 'João Santos - 38 anos' },
    { id: '3', label: 'Ana Oliveira - 52 anos' },
  ]);
  const [pacienteSelecionado, setPacienteSelecionado] = useState('');
  const [dados, setDados] = useState(null);
  const [tendencia, setTendencia] = useState('peso');
  const [periodo, setPeriodo] = useState(6);
  // tendência é o tipo de métrica selecionada (peso/glicemia/etc)

  useEffect(() => {
    carregarDashboard();
  }, []);

  const carregarDashboard = async () => {
    setLoading(true);
    try {
      const statsResponse = await api.get('/nutrologia/dashboard');
      setDados(statsResponse.data);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const recarregarTendencia = () => {
    // Tendência derivada do state atual; recarregamento local apenas.
    // Caso backend forneça endpoint por paciente/período, plugar aqui.
  };

  // Dados de exemplo para gráficos (em produção viriam da API)
  const pesoData = {
    labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
    datasets: [
      {
        label: 'Peso (kg)',
        data: [85.5, 84.2, 83.0, 81.5, 80.0, 78.5],
        borderColor: '#722ed1',
        backgroundColor: 'rgba(114, 46, 209, 0.1)',
        tension: 0.4,
        fill: true,
      },
      {
        label: 'IMC',
        data: [28.5, 28.0, 27.5, 27.0, 26.5, 26.0],
        borderColor: '#fa8c16',
        backgroundColor: 'rgba(250, 140, 22, 0.1)',
        tension: 0.4,
        fill: true,
        yAxisID: 'y1',
      },
    ],
  };

  const glicemiaData = {
    labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
    datasets: [
      {
        label: 'Glicemia Jejum (mg/dL)',
        data: [105, 102, 98, 95, 92, 88],
        borderColor: '#52c41a',
        backgroundColor: 'rgba(82, 196, 26, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const perfilLipidicoData = {
    labels: ['Colesterol Total', 'LDL', 'HDL', 'Triglicerídeos'],
    datasets: [
      {
        label: 'Atual',
        data: [210, 130, 55, 150],
        backgroundColor: 'rgba(114, 46, 209, 0.7)',
      },
      {
        label: 'Meta',
        data: [190, 100, 60, 100],
        backgroundColor: 'rgba(82, 196, 26, 0.7)',
      },
    ],
  };

  const composicaoCorporalData = {
    labels: ['Gordura', 'Músculo', 'Água', 'Outros'],
    datasets: [
      {
        data: [25, 40, 30, 5],
        backgroundColor: [
          'rgba(250, 140, 22, 0.8)',
          'rgba(114, 46, 209, 0.8)',
          'rgba(82, 196, 26, 0.8)',
          'rgba(108, 117, 125, 0.8)',
        ],
      },
    ],
  };

  const vitaminasData = {
    labels: ['Vitamina D', 'Vitamina B12', 'Ferritina', 'Folato'],
    datasets: [
      {
        data: [28, 350, 80, 5.5],
        borderColor: '#722ed1',
        backgroundColor: 'rgba(114, 46, 209, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { position: 'top' } },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: 'Peso (kg)' },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: { drawOnChartArea: false },
        title: { display: true, text: 'IMC' },
      },
    },
  };

  if (loading) {
    return (
      <Box sx={{ textAlign: 'center', py: 6 }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Carregando dashboard de nutrologia...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <LineChartIcon fontSize="large" />
          Dashboard Nutrologia
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Acompanhe tendências de peso, exames laboratoriais e bioimpedância dos seus pacientes
        </Typography>
      </Box>

      {/* Seletor de paciente */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Selecione o paciente:</Typography>
              <TextField
                select
                fullWidth
                value={pacienteSelecionado}
                onChange={(e) => setPacienteSelecionado(e.target.value)}
                placeholder="Buscar paciente..."
                size="small"
              >
                <MenuItem value="">Buscar paciente...</MenuItem>
                {pacientes.map((p) => (
                  <MenuItem key={p.id} value={p.id}>{p.label}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Parâmetro:</Typography>
              <TextField
                select
                fullWidth
                value={tendencia}
                onChange={(e) => setTendencia(e.target.value)}
                size="small"
              >
                {PARAMETROS.map((p) => (
                  <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} md={3}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Período:</Typography>
              <TextField
                select
                fullWidth
                value={periodo}
                onChange={(e) => setPeriodo(Number(e.target.value))}
                size="small"
              >
                {PERIODOS.map((p) => (
                  <MenuItem key={p.value} value={p.value}>{p.label}</MenuItem>
                ))}
              </TextField>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Estatísticas */}
      {dados?.estatisticas && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
                  <CheckCircleIcon sx={{ color: 'success.main' }} />
                  <Typography variant="overline">Total de Avaliações</Typography>
                </Box>
                <Typography variant="h4">{dados.estatisticas.total_avaliacoes || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
                  <TrophyIcon sx={{ color: 'warning.main' }} />
                  <Typography variant="overline">Metas Ativas</Typography>
                </Box>
                <Typography variant="h4">{dados.estatisticas.metas_ativas || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
                  <ClockIcon sx={{ color: 'secondary.main' }} />
                  <Typography variant="overline">Pacientes Ativos (30d)</Typography>
                </Box>
                <Typography variant="h4">{dados.estatisticas.pacientes_ativos_30d || 0}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="overline" color="text.secondary">IMC Médio</Typography>
                <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1 }}>
                  <Typography variant="h4">{(dados.estatisticas.imc_medio || 0).toFixed(1)}</Typography>
                  <Chip
                    size="small"
                    label={dados.estatisticas.imc_medio > 25 ? 'Sobrepeso' : 'Normal'}
                    color={dados.estatisticas.imc_medio > 25 ? 'warning' : 'success'}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Grid container spacing={2}>
        {/* Tendência de Peso e IMC */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardHeader
              title="Tendência de Peso e IMC"
              action={
                <Button startIcon={<RefreshIcon />} onClick={recarregarTendencia}>
                  Atualizar
                </Button>
              }
            />
            <CardContent>
              <Box sx={{ height: 300 }}>
                <Line data={pesoData} options={chartOptions} />
              </Box>
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Chip sx={{ mr: 1 }} color="secondary" label="Perda de 7kg em 6 meses" />
                <Chip color="success" label="IMC reduzido de 28.5 para 26.0" />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Composição Corporal */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardHeader title="Composição Corporal" />
            <CardContent>
              <Box sx={{ height: 300 }}>
                <Doughnut data={composicaoCorporalData} />
              </Box>
              <Grid container spacing={1} sx={{ mt: 1 }}>
                {[
                  { label: 'Gordura', value: '25%' },
                  { label: 'Músculo', value: '40%' },
                  { label: 'Água', value: '30%' },
                  { label: 'Outros', value: '5%' },
                ].map((item) => (
                  <Grid item xs={6} key={item.label}>
                    <Typography variant="caption" color="text.secondary">{item.label}: </Typography>
                    <Typography variant="body2" component="span" fontWeight="bold">{item.value}</Typography>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Glicemia */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader title="Evolução Glicemia" />
            <CardContent>
              <Box sx={{ height: 250 }}>
                <Line
                  data={glicemiaData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                    scales: { y: { min: 70, max: 130 } },
                  }}
                />
              </Box>
              <Alert
                icon={<CheckCircleIcon />}
                severity="success"
                sx={{ mt: 1.5 }}
              >
                Glicemia em nível normal
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        {/* Perfil Lipídico */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader title="Perfil Lipídico (Atual vs Meta)" />
            <CardContent>
              <Box sx={{ height: 250 }}>
                <Bar
                  data={perfilLipidicoData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Vitaminas */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader title="Evolução Vitaminas e Minerais" />
            <CardContent>
              <Box sx={{ height: 250 }}>
                <Line
                  data={vitaminasData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'top' } },
                  }}
                />
              </Box>
              <Chip color="warning" label="Vitamina D em insufficiency" sx={{ mt: 1 }} />
            </CardContent>
          </Card>
        </Grid>

        {/* Metas */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader
              title="Metas Nutricionais"
              action={<Button>+ Nova Meta</Button>}
            />
            <CardContent>
              {[
                { nome: 'Emagrecimento', valor: 75 },
                { nome: 'Normalizar Glicemia', valor: 100 },
                { nome: 'Aumentar Vit D', valor: 40 },
              ].map((meta, i) => (
                <Box key={meta.nome} sx={{ mb: i < 2 ? 2 : 0 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="body2" fontWeight="bold">{meta.nome}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {meta.valor}% completo
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={meta.valor}
                    color={meta.valor >= 100 ? 'success' : 'primary'}
                  />
                  {i < 2 && <Divider sx={{ mt: 2 }} />}
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabela de Exames Recentes */}
      <Card sx={{ mt: 3 }}>
        <CardHeader
          title="Últimos Exames Laboratoriais"
          action={<Button startIcon={<DownloadIcon />}>Exportar</Button>}
        />
        <TableContainer component={Paper} variant="outlined">
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Data</TableCell>
                <TableCell>Exame</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Observação</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {EXAMES_FAKE.map((row, i) => (
                <TableRow key={`${row.data}-${row.exame}-${i}`}>
                  <TableCell>{row.data}</TableCell>
                  <TableCell>{row.exame}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={row.status === 'normal' ? 'Normal' : 'Alterado'}
                      color={row.status === 'normal' ? 'success' : 'warning'}
                    />
                  </TableCell>
                  <TableCell>{row.observacao}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Alertas */}
      <Grid container spacing={2} sx={{ mt: 1 }}>
        <Grid item xs={12} md={6}>
          <Alert
            severity="warning"
            icon={<WarningIcon />}
            action={<Button size="small">Verificar</Button>}
          >
            <AlertTitle>Atenção: Vitamina D em insufficiency</AlertTitle>
            Recomenda-se suplementação e exposição solar
          </Alert>
        </Grid>
        <Grid item xs={12} md={6}>
          <Alert
            severity="info"
            icon={<ClockIcon />}
            action={<Button size="small">Ver Detalhes</Button>}
          >
            <AlertTitle>Exame agendado</AlertTitle>
            Perfil hepático agendado para 20/06/2026
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default NutrologiaDashboard;
