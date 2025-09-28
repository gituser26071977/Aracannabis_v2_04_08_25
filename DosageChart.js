import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  CircularProgress,
  Alert
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { ptBR } from 'date-fns/locale';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

const DosageChart = ({ pacienteId }) => {
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Cores para o gráfico
  const colors = {
    dosage: 'rgba(138, 43, 226, 1)', // Roxo
    background: 'rgba(138, 43, 226, 0.2)'
  };

  // Função para buscar dados do gráfico
  const fetchChartData = async () => {
    setLoading(true);
    setError('');

    try {
      // Aqui seria feita a chamada à API para buscar os dados do gráfico
      // const filtros = {};
      // if (startDate) filtros.data_inicio = format(startDate, 'yyyy-MM-dd');
      // if (endDate) filtros.data_fim = format(endDate, 'yyyy-MM-dd');
      // const response = await dosagemService.obterDadosGrafico(pacienteId, filtros);
      // const apiData = response.data.dados_grafico;
      
      // Dados simulados para demonstração
      const today = new Date();
      const oneMonthAgo = new Date(today);
      oneMonthAgo.setMonth(today.getMonth() - 1);
      
      const generateRandomData = () => {
        const data = [];
        let currentDate = new Date(oneMonthAgo);
        let dosage = 5; // Dosagem inicial (gotas)
        
        while (currentDate <= today) {
          // Pequena variação na dosagem (ajuste médico)
          if (Math.random() > 0.7) {
            // 30% de chance de ajuste na dosagem
            dosage += Math.random() > 0.5 ? 1 : -1;
            // Garantir que a dosagem esteja entre 1 e 20
            dosage = Math.max(1, Math.min(20, dosage));
          }
          
          data.push({
            x: new Date(currentDate).toISOString().split('T')[0],
            y: dosage,
            dosagem_texto: `${dosage} gotas`
          });
          
          // Avançar 3 dias
          currentDate.setDate(currentDate.getDate() + 3);
        }
        
        return data;
      };
      
      const dosageData = generateRandomData();
      
      // Preparar dados para o gráfico
      const data = {
        datasets: [{
          label: 'Dosagem (gotas)',
          data: dosageData,
          borderColor: colors.dosage,
          backgroundColor: colors.background,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
        }]
      };
      
      setChartData(data);
    } catch (err) {
      console.error('Erro ao buscar dados do gráfico:', err);
      setError('Não foi possível carregar os dados do gráfico.');
    } finally {
      setLoading(false);
    }
  };

  // Carregar dados iniciais
  useEffect(() => {
    fetchChartData();
  }, [pacienteId]);

  // Opções do gráfico
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day',
          tooltipFormat: 'dd/MM/yyyy',
          displayFormats: {
            day: 'dd/MM'
          }
        },
        title: {
          display: true,
          text: 'Data'
        },
        adapters: {
          date: {
            locale: ptBR
          }
        }
      },
      y: {
        min: 0,
        title: {
          display: true,
          text: 'Dosagem (gotas)'
        },
        ticks: {
          stepSize: 5
        }
      }
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Evolução da Dosagem',
        font: {
          size: 16,
          weight: 'bold'
        }
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            const date = new Date(context[0].parsed.x);
            return date.toLocaleDateString('pt-BR');
          },
          label: (context) => {
            const dataPoint = context.dataset.data[context.dataIndex];
            return dataPoint.dosagem_texto || `${context.parsed.y} gotas`;
          }
        }
      }
    },
    interaction: {
      mode: 'index',
      intersect: false,
    },
    elements: {
      line: {
        borderWidth: 2
      }
    },
    backgroundColor: '#1E2130'
  };

  // Manipuladores de eventos
  const handleStartDateChange = (date) => {
    setStartDate(date);
  };

  const handleEndDateChange = (date) => {
    setEndDate(date);
  };

  const handleApplyFilters = () => {
    fetchChartData();
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 4, backgroundColor: '#1E2130', color: 'white' }}>
        <Typography variant="h6" gutterBottom sx={{ color: '#8A2BE2' }}>
          Evolução da Dosagem
        </Typography>
        
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={4}>
            <DatePicker
              label="Data Inicial"
              value={startDate}
              onChange={handleStartDateChange}
              slotProps={{
                textField: {
                  size: "small",
                  fullWidth: true,
                  sx: {
                    '.MuiInputBase-root': {
                      color: 'white',
                    },
                    '.MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.3)',
                    },
                    '&:hover .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                    },
                    '.MuiInputLabel-root': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    },
                    '.MuiSvgIcon-root': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    }
                  }
                }
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6} md={4}>
            <DatePicker
              label="Data Final"
              value={endDate}
              onChange={handleEndDateChange}
              slotProps={{
                textField: {
                  size: "small",
                  fullWidth: true,
                  sx: {
                    '.MuiInputBase-root': {
                      color: 'white',
                    },
                    '.MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.3)',
                    },
                    '&:hover .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(255, 255, 255, 0.5)',
                    },
                    '.MuiInputLabel-root': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    },
                    '.MuiSvgIcon-root': {
                      color: 'rgba(255, 255, 255, 0.7)',
                    }
                  }
                }
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Button 
              variant="contained" 
              onClick={handleApplyFilters}
              disabled={loading}
              fullWidth
              sx={{ 
                bgcolor: '#8A2BE2', 
                '&:hover': { bgcolor: '#6A0DAD' },
                height: '40px'
              }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : 'Aplicar Filtros'}
            </Button>
          </Grid>
        </Grid>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box sx={{ height: 400, position: 'relative' }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <CircularProgress />
            </Box>
          ) : chartData ? (
            <Line data={chartData} options={chartOptions} />
          ) : (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
              <Typography variant="body2" color="text.secondary">
                Nenhum dado de dosagem disponível para o período selecionado
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
    </LocalizationProvider>
  );
};

export default DosageChart;
