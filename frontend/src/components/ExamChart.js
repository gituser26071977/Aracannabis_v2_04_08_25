import React, { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  ButtonGroup,
  Button,
  Chip,
  useTheme
} from '@mui/material';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Brush,
  ReferenceLine
} from 'recharts';
import {
  ShowChart as ChartIcon,
  Timeline as TimelineIcon,
  Functions as FunctionsIcon,
  ArrowUpward as MaxIcon,
  ArrowDownward as MinIcon,
  LastPage as LastIcon
} from '@mui/icons-material';
import { exameService } from '../services/api';

const ExamChart = ({ patientId }) => {
  const theme = useTheme();
  const [chartableExams, setChartableExams] = useState([]);
  const [selectedExam, setSelectedExam] = useState('');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [period, setPeriod] = useState('all'); // '1m', '3m', '6m', '1y', 'all'

  // Carregar exames disponíveis para gráfico
  useEffect(() => {
    const loadChartableExams = async () => {
      try {
        const response = await exameService.listarPorPaciente(patientId);
        const numericExams = response.filter(exam => exam.tipo_exame === 'numerico');

        // Agrupar por título e contar exames
        const examGroups = {};
        numericExams.forEach(exam => {
          if (!examGroups[exam.titulo]) {
            examGroups[exam.titulo] = {
              titulo: exam.titulo,
              unidade: exam.unidade || '',
              count: 0
            };
          }
          examGroups[exam.titulo].count += 1;
        });

        // Filtrar apenas exames com pelo menos 2 registros
        const availableExams = Object.values(examGroups).filter(exam => exam.count >= 2);
        setChartableExams(availableExams);

        // Selecionar automaticamente o primeiro exame se disponível
        if (availableExams.length > 0) {
          setSelectedExam(availableExams[0].titulo);
        }
      } catch (err) {
        console.error('Erro ao carregar exames para gráfico:', err);
        setError('Erro ao carregar exames disponíveis');
      }
    };

    if (patientId) {
      loadChartableExams();
    }
  }, [patientId]);

  // Carregar dados do gráfico quando o exame selecionado muda
  useEffect(() => {
    const loadChartData = async () => {
      if (!selectedExam) {
        setChartData(null);
        return;
      }

      setLoading(true);
      setError('');

      try {
        // Simulando chamada de API real se a rota específica não existir ou falhar
        // Na prática, a rota existente retornava { dados: [], titulo: '', unidade: '' }
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/pacientes/${patientId}/exames/chart/${encodeURIComponent(selectedExam)}`);

        if (!response.ok) {
          throw new Error('Erro ao carregar dados');
        }

        const data = await response.json();

        // Ordenar dados por data (forçar meio-dia para evitar deslocamento de timezone)
        if (data.dados && Array.isArray(data.dados)) {
          data.dados.sort((a, b) => new Date(a.data + 'T12:00:00') - new Date(b.data + 'T12:00:00'));
        }

        setChartData(data);
      } catch (err) {
        console.error('Erro ao carregar dados do gráfico:', err);
        setError('Erro ao carregar dados do gráfico');
        setChartData(null);
      } finally {
        setLoading(false);
      }
    };

    loadChartData();
  }, [selectedExam, patientId]);

  // Filtrar dados com base no período selecionado
  const filteredData = useMemo(() => {
    if (!chartData || !chartData.dados) return [];

    const now = new Date();
    let startDate = new Date(0); // Default to generic past

    switch (period) {
      case '1m':
        startDate = new Date();
        startDate.setMonth(now.getMonth() - 1);
        break;
      case '3m':
        startDate = new Date();
        startDate.setMonth(now.getMonth() - 3);
        break;
      case '6m':
        startDate = new Date();
        startDate.setMonth(now.getMonth() - 6);
        break;
      case '1y':
        startDate = new Date();
        startDate.setFullYear(now.getFullYear() - 1);
        break;
      default:
        break;
    }

    return chartData.dados.filter(item => new Date(item.data + 'T12:00:00') >= startDate);
  }, [chartData, period]);

  // Calcular estatísticas
  const stats = useMemo(() => {
    if (filteredData.length === 0) return null;
    const values = filteredData.map(d => parseFloat(d.valor));
    const min = Math.min(...values);
    const max = Math.max(...values);
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    const last = values[values.length - 1];

    return { min, max, avg, last };
  }, [filteredData]);

  const handleExamChange = (event) => {
    setSelectedExam(event.target.value);
  };

  const formatTooltipValue = (value, name) => {
    const exam = chartableExams.find(e => e.titulo === selectedExam);
    const unidade = exam?.unidade || '';
    return [`${value}${unidade ? ' ' + unidade : ''}`, name];
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <Paper elevation={4} sx={{ p: 2, bgcolor: 'background.paper', border: '1px solid #ccc' }}>
          <Typography variant="subtitle2" color="text.secondary">
            {new Date(label + 'T12:00:00').toLocaleDateString('pt-BR')}
          </Typography>
          <Box sx={{ mt: 1 }}>
            <Typography variant="h6" color="primary" fontWeight="bold">
              {payload[0].value} {chartData?.unidade}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {payload[0].name}
            </Typography>
          </Box>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3, borderRadius: 2 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" color="primary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <TimelineIcon /> Evolução Clínica: Exames
        </Typography>
      </Box>

      <Typography variant="body2" color="text.secondary" paragraph>
        Acompanhe o histórico e a tendência dos resultados de exames ao longo do tempo.
      </Typography>

      {chartableExams.length === 0 ? (
        <Alert severity="info" sx={{ mt: 2 }}>
          Nenhum exame numérico encontrado com dados suficientes (mínimo 2 registros) para gerar análise gráfica.
        </Alert>
      ) : (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={5}>
              <FormControl fullWidth size="medium">
                <InputLabel id="select-exam-label">Selecione o Exame para Análise</InputLabel>
                <Select
                  labelId="select-exam-label"
                  value={selectedExam}
                  onChange={handleExamChange}
                  label="Selecione o Exame para Análise"
                >
                  {chartableExams.map((exam) => (
                    <MenuItem key={exam.titulo} value={exam.titulo}>
                      {exam.titulo}
                      <Chip
                        label={`${exam.count} reg.`}
                        size="small"
                        color="primary"
                        variant="outlined"
                        sx={{ ml: 1, height: 20, fontSize: '0.65rem' }}
                      />
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={7} sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ mr: 2, color: 'text.secondary' }}>Período:</Typography>
              <ButtonGroup variant="outlined" aria-label="filtro de período" size="small">
                <Button onClick={() => setPeriod('1m')} variant={period === '1m' ? 'contained' : 'outlined'}>1 Mês</Button>
                <Button onClick={() => setPeriod('3m')} variant={period === '3m' ? 'contained' : 'outlined'}>3 Meses</Button>
                <Button onClick={() => setPeriod('6m')} variant={period === '6m' ? 'contained' : 'outlined'}>6 Meses</Button>
                <Button onClick={() => setPeriod('1y')} variant={period === '1y' ? 'contained' : 'outlined'}>1 Ano</Button>
                <Button onClick={() => setPeriod('all')} variant={period === 'all' ? 'contained' : 'outlined'}>Tudo</Button>
              </ButtonGroup>
            </Grid>
          </Grid>

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
              <CircularProgress />
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {chartData && !loading && filteredData.length > 0 && (
            <>
              {/* STATISTICS CARDS */}
              {stats && (
                <Grid container spacing={2} sx={{ mb: 4 }}>
                  <Grid item xs={6} sm={3}>
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05), border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}` }}>
                      <CardContent sx={{ p: '16px !important', textAlign: 'center' }}>
                        <Typography variant="overline" color="text.secondary" display="block">Mínimo</Typography>
                        <Typography variant="h6" color="primary" fontWeight="bold">
                          <MinIcon fontSize="small" color="error" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                          {stats.min.toFixed(1)} <Typography component="span" variant="caption">{chartData.unidade}</Typography>
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05), border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}` }}>
                      <CardContent sx={{ p: '16px !important', textAlign: 'center' }}>
                        <Typography variant="overline" color="text.secondary" display="block">Máximo</Typography>
                        <Typography variant="h6" color="primary" fontWeight="bold">
                          <MaxIcon fontSize="small" color="success" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                          {stats.max.toFixed(1)} <Typography component="span" variant="caption">{chartData.unidade}</Typography>
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05), border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}` }}>
                      <CardContent sx={{ p: '16px !important', textAlign: 'center' }}>
                        <Typography variant="overline" color="text.secondary" display="block">Média</Typography>
                        <Typography variant="h6" color="primary" fontWeight="bold">
                          <FunctionsIcon fontSize="small" color="action" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                          {stats.avg.toFixed(1)} <Typography component="span" variant="caption">{chartData.unidade}</Typography>
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6} sm={3}>
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.primary.main, 0.1), border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}` }}>
                      <CardContent sx={{ p: '16px !important', textAlign: 'center' }}>
                        <Typography variant="overline" color="text.secondary" display="block">Último</Typography>
                        <Typography variant="h6" color="primary" fontWeight="bold">
                          <LastIcon fontSize="small" color="action" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                          {stats.last.toFixed(1)} <Typography component="span" variant="caption">{chartData.unidade}</Typography>
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              )}

              {/* CHART AREA */}
              <Box sx={{ width: '100%', height: 450 }}>
                <ResponsiveContainer>
                  <AreaChart
                    data={filteredData}
                    margin={{
                      top: 10,
                      right: 30,
                      left: 0,
                      bottom: 0,
                    }}
                  >
                    <defs>
                      <linearGradient id="colorValor" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.8} />
                        <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eee" />
                    <XAxis
                      dataKey="data"
                      tickFormatter={(date) => new Date(date + 'T12:00:00').toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
                      tick={{ fontSize: 12, fill: '#666' }}
                      axisLine={{ stroke: '#ddd' }}
                      tickLine={false}
                      dy={10}
                    />
                    <YAxis
                      tick={{ fontSize: 12, fill: '#666' }}
                      axisLine={false}
                      tickLine={false}
                      dx={-10}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend verticalAlign="top" height={36} />
                    <ReferenceLine y={stats?.avg} label="Média" stroke="red" strokeDasharray="3 3" />
                    <Area
                      type="monotone"
                      dataKey="valor"
                      name={chartData.titulo}
                      stroke={theme.palette.primary.main}
                      fillOpacity={1}
                      fill="url(#colorValor)"
                      activeDot={{ r: 8, strokeWidth: 0 }}
                      strokeWidth={3}
                      animationDuration={1500}
                    />
                    <Brush dataKey="data" height={30} stroke={theme.palette.primary.main} fill="#f5f5f5" />
                  </AreaChart>
                </ResponsiveContainer>
              </Box>
            </>
          )}

          {chartData && !loading && filteredData.length === 0 && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              Não há dados para o período selecionado ({period}). Tente selecionar um período maior.
            </Alert>
          )}

          {chartData && (
            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Typography variant="caption" color="text.secondary">
                Total de registros: {filteredData.length} (Filtrado) / {chartData.total_pontos} (Total)
              </Typography>
            </Box>
          )}
        </>
      )}
    </Paper>
  );
};

// Helper for alpha color - simple version as mui alpha might duplicate
function alpha(color, opacity) {
  // Simple mock if not using mui system alpha
  // Returns a generic rgba string assuming color is hex. 
  // Ideally use 'import { alpha } from "@mui/material/styles"' but 'useTheme' gives us access.
  // For simplicity, let's just use a hardcoded color overlap or try importing alpha from mui/material
  return color + Math.round(opacity * 255).toString(16).padStart(2, '0');
}

export default ExamChart;