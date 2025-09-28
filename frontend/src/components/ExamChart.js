import React, { useState, useEffect } from 'react';
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
  CardContent
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { exameService } from '../services/api';

const ExamChart = ({ patientId }) => {
  const [chartableExams, setChartableExams] = useState([]);
  const [selectedExam, setSelectedExam] = useState('');
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
        const response = await fetch(`${process.env.REACT_APP_API_URL}/api/pacientes/${patientId}/exames/chart/${encodeURIComponent(selectedExam)}`);
        if (!response.ok) {
          throw new Error('Erro ao carregar dados do gráfico');
        }

        const data = await response.json();
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

  const handleExamChange = (event) => {
    setSelectedExam(event.target.value);
  };

  const formatTooltipValue = (value, name) => {
    const exam = chartableExams.find(e => e.titulo === selectedExam);
    const unidade = exam?.unidade || '';
    return [`${value}${unidade ? ' ' + unidade : ''}`, name];
  };

  const formatYAxisLabel = (value) => {
    const exam = chartableExams.find(e => e.titulo === selectedExam);
    const unidade = exam?.unidade || '';
    return `${value}${unidade ? ' ' + unidade : ''}`;
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom>
        Gráfico de Evolução de Exames
      </Typography>

      {chartableExams.length === 0 ? (
        <Alert severity="info">
          Nenhum exame numérico encontrado com dados suficientes para gerar gráfico.
          Adicione pelo menos 2 exames do mesmo tipo para visualizar a evolução.
        </Alert>
      ) : (
        <>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Selecionar Exame</InputLabel>
                <Select
                  value={selectedExam}
                  onChange={handleExamChange}
                  label="Selecionar Exame"
                >
                  {chartableExams.map((exam) => (
                    <MenuItem key={exam.titulo} value={exam.titulo}>
                      {exam.titulo} ({exam.count} registros{exam.unidade ? ` - ${exam.unidade}` : ''})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {chartData && !loading && (
            <Box sx={{ width: '100%', height: 400 }}>
              <ResponsiveContainer>
                <LineChart
                  data={chartData.dados}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="data"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickFormatter={formatYAxisLabel}
                  />
                  <Tooltip
                    formatter={formatTooltipValue}
                    labelStyle={{ color: '#000' }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="valor"
                    stroke="#8884d8"
                    strokeWidth={2}
                    dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
                    activeDot={{ r: 6 }}
                    name={chartData.titulo}
                  />
                </LineChart>
              </ResponsiveContainer>
            </Box>
          )}

          {chartData && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Total de pontos: {chartData.total_pontos} | Unidade: {chartData.unidade || 'N/A'}
              </Typography>
            </Box>
          )}
        </>
      )}
    </Paper>
  );
};

export default ExamChart;