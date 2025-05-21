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

const SymptomsChart = ({ pacienteId }) => {
  const [selectedSymptoms, setSelectedSymptoms] = useState([]);
  const [availableSymptoms, setAvailableSymptoms] = useState([]);
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Cores para os diferentes sintomas
  const colors = [
    'rgba(75, 192, 192, 1)',
    'rgba(255, 99, 132, 1)',
    'rgba(54, 162, 235, 1)',
    'rgba(255, 206, 86, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)',
    'rgba(199, 199, 199, 1)',
    'rgba(83, 102, 255, 1)',
    'rgba(78, 205, 196, 1)',
  ];

  // Buscar sintomas disponíveis
  useEffect(() => {
    const fetchAvailableSymptoms = async () => {
      try {
        // Aqui seria feita a chamada à API para buscar os sintomas disponíveis
        // const response = await sintomaService.obterSintomasPadrao();
        // setAvailableSymptoms(response.data.sintomas_padrao);
        
        // Dados simulados para demonstração
        setAvailableSymptoms([
          'Dor', 
          'Ansiedade', 
          'Medo', 
          'Dificuldade de raciocínio', 
          'Qualidade do sono', 
          'Apetite', 
          'Humor', 
          'Energia', 
          'Memória'
        ]);
      } catch (err) {
        console.error('Erro ao buscar sintomas disponíveis:', err);
        setError('Não foi possível carregar a lista de sintomas.');
      }
    };

    fetchAvailableSymptoms();
  }, []);

  // Função para buscar dados do gráfico
  const fetchChartData = async () => {
    if (selectedSymptoms.length === 0) {
      setError('Selecione pelo menos um sintoma para visualizar.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Aqui seria feita a chamada à API para buscar os dados do gráfico
      // const filtros = {};
      // if (startDate) filtros.data_inicio = format(startDate, 'yyyy-MM-dd');
      // if (endDate) filtros.data_fim = format(endDate, 'yyyy-MM-dd');
      // const response = await sintomaService.obterDadosGrafico(pacienteId, filtros);
      // const apiData = response.data.dados_grafico;
      
      // Dados simulados para demonstração
      const today = new Date();
      const oneMonthAgo = new Date(today);
      oneMonthAgo.setMonth(today.getMonth() - 1);
      
      const generateRandomData = (symptom) => {
        const data = [];
        let currentDate = new Date(oneMonthAgo);
        
        while (currentDate <= today) {
          // Gerar pontuação aleatória entre 0 e 10
          const intensity = Math.floor(Math.random() * 11);
          
          data.push({
            x: new Date(currentDate).toISOString().split('T')[0],
            y: intensity
          });
          
          // Avançar 3 dias
          currentDate.setDate(currentDate.getDate() + 3);
        }
        
        return {
          label: symptom,
          data: data
        };
      };
      
      const apiData = selectedSymptoms.map((symptom, index) => ({
        ...generateRandomData(symptom),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length].replace('1)', '0.2)'),
      }));
      
      // Preparar dados para o gráfico
      const data = {
        datasets: apiData.map(dataset => ({
          label: dataset.label,
          data: dataset.data,
          borderColor: dataset.borderColor,
          backgroundColor: dataset.backgroundColor,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
        }))
      };
      
      setChartData(data);
    } catch (err) {
      console.error('Erro ao buscar dados do gráfico:', err);
      setError('Não foi possível carregar os dados do gráfico.');
    } finally {
      setLoading(false);
    }
  };

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
        max: 10,
        title: {
          display: true,
          text: 'Intensidade'
        },
        ticks: {
          stepSize: 1
        }
      }
    },
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Evolução dos Sintomas',
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
            return `${context.dataset.label}: ${context.parsed.y} de intensidade`;
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
  const handleSymptomsChange = (event) => {
    setSelectedSymptoms(event.target.value);
  };

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
          Evolução dos Sintomas
        </Typography>
        
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth size="small">
              <InputLabel id="symptoms-select-label" sx={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                Sintomas
              </InputLabel>
              <Select
                labelId="symptoms-select-label"
                id="symptoms-select"
                multiple
                value={selectedSymptoms}
                onChange={handleSymptomsChange}
                label="Sintomas"
                sx={{
                  color: 'white',
                  '.MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: '#8A2BE2',
                  },
                  '.MuiSvgIcon-root': {
                    color: 'rgba(255, 255, 255, 0.7)',
                  }
                }}
              >
                {availableSymptoms.map((symptom) => (
                  <MenuItem key={symptom} value={symptom}>
                    {symptom}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
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
          
          <Grid item xs={12} sm={6} md={3}>
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
          
          <Grid item xs={12}>
            <Button 
              variant="contained" 
              onClick={handleApplyFilters}
              disabled={loading}
              sx={{ 
                bgcolor: '#8A2BE2', 
                '&:hover': { bgcolor: '#6A0DAD' } 
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
                Selecione os sintomas e aplique os filtros para visualizar o gráfico
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
    </LocalizationProvider>
  );
};

export default SymptomsChart;
