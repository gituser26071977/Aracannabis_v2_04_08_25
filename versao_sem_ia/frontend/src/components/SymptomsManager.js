import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  Typography, 
  Grid, 
  TextField, 
  Button, 
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Alert,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Divider,
  Chip,
  Tooltip,
  Tabs,
  Tab
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon,
  BarChart as ChartIcon,
  AddCircleOutline as AddCustomIcon
} from '@mui/icons-material';
import { sintomasService } from '../services/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import { ptBR } from 'date-fns/locale';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  TimeScale
);

const SymptomsManager = ({ patientId }) => {
  const [symptoms, setSymptoms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [standardSymptoms, setStandardSymptoms] = useState([]);
  const [customSymptoms, setCustomSymptoms] = useState([]);
  const [newCustomSymptom, setNewCustomSymptom] = useState('');
  const [customSymptomDialogOpen, setCustomSymptomDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  
  // Estado para o formulário de novo sintoma
  const [newSymptom, setNewSymptom] = useState({
    data: new Date().toISOString().split('T')[0],
    sintoma: '',
    intensidade: 5
  });
  
  // Estado para o gráfico
  const [chartData, setChartData] = useState(null);
  const [showChart, setShowChart] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  
  // Estado para diálogo de confirmação de exclusão
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [symptomToDelete, setSymptomToDelete] = useState(null);
  
  // Carregar sintomas e sintomas padrão
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carregar sintomas do paciente
        const symptomsData = await sintomasService.listar(patientId);
        setSymptoms(symptomsData.sintomas || []);
        
        // Carregar sintomas padrão e personalizados
        const standardData = await sintomasService.listarPadrao();
        setStandardSymptoms(standardData.sintomas_padrao || []);
        setCustomSymptoms(standardData.sintomas_personalizados || []);
        
        // Carregar dados do gráfico automaticamente
        await loadChartData();
        
        setError('');
      } catch (err) {
        console.error('Erro ao carregar dados de sintomas:', err);
        setError('Não foi possível carregar os sintomas');
      } finally {
        setLoading(false);
      }
    };
    
    if (patientId) {
      fetchData();
    }
  }, [patientId]);
  
  // Carregar dados do gráfico
  const loadChartData = async () => {
    setChartLoading(true);
    try {
      const data = await sintomasService.obterDadosGrafico(patientId);
      setChartData(data.dados_grafico);
    } catch (err) {
      console.error('Erro ao carregar dados do gráfico:', err);
      // Não mostrar erro se não houver dados suficientes
      setChartData(null);
    } finally {
      setChartLoading(false);
    }
  };
  
  // Manipulador de mudança no formulário
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewSymptom(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Manipulador de mudança no campo de novo sintoma personalizado
  const handleCustomSymptomChange = (e) => {
    setNewCustomSymptom(e.target.value);
  };
  
  // Abrir diálogo para adicionar sintoma personalizado
  const handleOpenCustomSymptomDialog = () => {
    setCustomSymptomDialogOpen(true);
  };
  
  // Fechar diálogo de sintoma personalizado
  const handleCloseCustomSymptomDialog = () => {
    setCustomSymptomDialogOpen(false);
    setNewCustomSymptom('');
  };
  
  // Adicionar novo sintoma personalizado
  const handleAddCustomSymptom = async () => {
    if (!newCustomSymptom.trim()) {
      setError('O nome do sintoma não pode estar vazio');
      return;
    }
    
    try {
      const response = await sintomasService.criarPersonalizado(newCustomSymptom);
      
      // Recarregar a lista completa de sintomas padrão e personalizados
      const standardData = await sintomasService.listarPadrao();
      setStandardSymptoms(standardData.sintomas_padrao || []);
      setCustomSymptoms(standardData.sintomas_personalizados || []);
      
      // Fechar diálogo e limpar campo
      handleCloseCustomSymptomDialog();
      
      // Mostrar mensagem de sucesso
      setError('');
    } catch (err) {
      console.error('Erro ao adicionar sintoma personalizado:', err);
      setError(err.error || 'Não foi possível adicionar o sintoma personalizado');
    }
  };
  
  // Manipulador de mudança de tab
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };
  
  // Manipulador de mudança no slider de intensidade
  const handleIntensityChange = (event, newValue) => {
    setNewSymptom(prev => ({
      ...prev,
      intensidade: newValue
    }));
  };
  
  // Registrar novo sintoma
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!newSymptom.sintoma) {
      setError('Selecione um sintoma');
      return;
    }
    
    try {
      const response = await sintomasService.criar({
        paciente_id: patientId,
        ...newSymptom
      });
      
      // Adicionar novo sintoma à lista ou atualizar existente
      const updatedSymptoms = [...symptoms];
      const existingIndex = updatedSymptoms.findIndex(
        s => s.data === newSymptom.data && s.sintoma === newSymptom.sintoma
      );
      
      if (existingIndex >= 0) {
        updatedSymptoms[existingIndex] = response.sintoma;
      } else {
        updatedSymptoms.push(response.sintoma);
      }
      
      setSymptoms(updatedSymptoms);
      
      // Recarregar dados do gráfico
      await loadChartData();
      
      // Resetar formulário
      setNewSymptom({
        data: new Date().toISOString().split('T')[0],
        sintoma: '',
        intensidade: 5
      });
      
      setError('');
    } catch (err) {
      console.error('Erro ao registrar sintoma:', err);
      setError('Não foi possível registrar o sintoma');
    }
  };
  
  // Abrir diálogo de confirmação de exclusão
  const handleOpenDeleteDialog = (symptom) => {
    setSymptomToDelete(symptom);
    setDeleteDialogOpen(true);
  };
  
  // Fechar diálogo de confirmação de exclusão
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setSymptomToDelete(null);
  };
  
  // Excluir sintoma
  const handleDeleteSymptom = async () => {
    if (!symptomToDelete) return;
    
    try {
      await sintomasService.excluir(symptomToDelete.id);
      setSymptoms(symptoms.filter(s => s.id !== symptomToDelete.id));
      
      // Recarregar dados do gráfico
      await loadChartData();
      
      handleCloseDeleteDialog();
    } catch (err) {
      console.error('Erro ao excluir sintoma:', err);
      setError('Não foi possível excluir o sintoma');
    }
  };
  
  // Formatar data para dd/mm/yyyy
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString + 'T00:00:00'); // Evitar problemas de timezone
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };
  
  // Função robusta para formatar data
  const formatDateRobust = (dateValue) => {
    try {
      let date;
      
      // Se já é um objeto Date
      if (dateValue instanceof Date) {
        date = dateValue;
      }
      // Se é uma string ou timestamp
      else {
        date = new Date(dateValue);
      }
      
      // Verificar se a data é válida
      if (isNaN(date.getTime())) {
        return 'Data inválida';
      }
      
      return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch (error) {
      console.error('Erro ao formatar data:', error, dateValue);
      return 'Data inválida';
    }
  };
  
  // Configuração do gráfico
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 20,
          font: {
            size: 14,
            weight: 'bold'
          }
        }
      },
      title: {
        display: true,
        text: '📊 Evolução dos Sintomas ao Longo do Tempo',
        font: {
          size: 18,
          weight: 'bold'
        },
        padding: 20
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          title: function(context) {
            const dateStr = context[0].label;
            const formattedDate = formatDate(dateStr);
            return `Data: ${formattedDate}`;
          },
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y}/10`;
          },
          afterLabel: function(context) {
            const intensity = context.parsed.y;
            let description = '';
            if (intensity <= 2) description = '(Muito Leve)';
            else if (intensity <= 4) description = '(Leve)';
            else if (intensity <= 6) description = '(Moderado)';
            else if (intensity <= 8) description = '(Intenso)';
            else description = '(Muito Intenso)';
            return description;
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        max: 10,
        title: {
          display: true,
          text: 'Intensidade (0-10)',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          font: {
            size: 12,
            weight: 'bold'
          },
          callback: function(value) {
            return value + '/10';
          }
        }
      },
      x: {
        type: 'time',
        time: {
          unit: 'month',
          stepSize: 1,
          displayFormats: {
            month: 'MMM/yyyy'
          },
          tooltipFormat: 'dd/MM/yyyy'
        },
        adapters: {
          date: {
            locale: ptBR
          }
        },
        title: {
          display: true,
          text: 'Período',
          font: {
            size: 14,
            weight: 'bold'
          }
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        },
        ticks: {
          font: {
            size: 12,
            weight: 'bold'
          },
          maxTicksLimit: 8,
          autoSkip: true,
          source: 'auto'
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const element = elements[0];
        const datasetIndex = element.datasetIndex;
        const dataIndex = element.index;
        const dataset = chartData[datasetIndex];
        const point = dataset.data[dataIndex];
        
        const dataFormatada = formatDateRobust(point.x);
        
        // Mostrar informações detalhadas do ponto clicado
        alert(`Sintoma: ${dataset.label}\nData: ${dataFormatada}\nIntensidade: ${point.y}/10`);
      }
    },
    onHover: (event, elements) => {
      event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
    }
  };
  
  // Preparar dados para o gráfico
  const prepareChartData = () => {
    if (!chartData || chartData.length === 0) return null;
    
    const colors = [
      'rgba(75, 192, 192, 1)',
      'rgba(255, 99, 132, 1)',
      'rgba(54, 162, 235, 1)',
      'rgba(255, 206, 86, 1)',
      'rgba(153, 102, 255, 1)',
      'rgba(255, 159, 64, 1)',
      'rgba(255, 193, 7, 1)',
      'rgba(76, 175, 80, 1)',
      'rgba(156, 39, 176, 1)',
      'rgba(233, 30, 99, 1)'
    ];
    
    return {
      datasets: chartData.map((dataset, index) => {
        // Converter strings de data para objetos Date e ordenar cronologicamente
        const processedData = dataset.data.map(point => ({
          ...point,
          x: new Date(point.x)
        })).sort((a, b) => new Date(a.x) - new Date(b.x));
        
        return {
          label: dataset.label,
          data: processedData,
          borderColor: colors[index % colors.length],
          backgroundColor: colors[index % colors.length].replace('1)', '0.3)'),
          pointBackgroundColor: colors[index % colors.length],
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          tension: 0.3,
          borderWidth: 3,
          fill: false
        };
      })
    };
  };
  
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Gerenciamento de Sintomas
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Formulário para registrar novo sintoma */}
          <Box component="form" onSubmit={handleSubmit} sx={{ mb: 4 }}>
            <Typography variant="subtitle1" gutterBottom>
              Registrar Novo Sintoma
            </Typography>
            
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={3}>
                <TextField
                  name="data"
                  label="Data"
                  type="date"
                  value={newSymptom.data}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth required>
                  <InputLabel>Sintoma</InputLabel>
                  <Select
                    name="sintoma"
                    value={newSymptom.sintoma}
                    onChange={handleInputChange}
                    label="Sintoma"
                  >
                    {standardSymptoms.map((symptom) => (
                      <MenuItem key={symptom} value={symptom}>
                        {symptom}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <Button
                  variant="outlined"
                  color="primary"
                  size="small"
                  startIcon={<AddCustomIcon />}
                  onClick={handleOpenCustomSymptomDialog}
                  sx={{ mt: 1 }}
                  fullWidth
                >
                  Adicionar Sintoma Personalizado
                </Button>
              </Grid>
              
              <Grid item xs={12} sm={3}>
                <Typography gutterBottom>
                  Intensidade: {newSymptom.intensidade}
                </Typography>
                <Slider
                  value={newSymptom.intensidade}
                  onChange={handleIntensityChange}
                  min={0}
                  max={10}
                  step={1}
                  marks
                  valueLabelDisplay="auto"
                />
              </Grid>
              
              <Grid item xs={12} sm={2}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  fullWidth
                  startIcon={<AddIcon />}
                >
                  Registrar
                </Button>
              </Grid>
            </Grid>
          </Box>
          
          {/* Gráfico de Sintomas */}
          <Paper 
            elevation={2} 
            sx={{ 
              p: 3, 
              mb: 3,
              background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
              border: '2px solid #28a745',
              borderRadius: 2
            }}
          >
            <Typography 
              variant="h6" 
              gutterBottom 
              sx={{ 
                color: 'success.main',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              📊 Gráfico de Evolução dos Sintomas
            </Typography>
            
            {chartLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : chartData && chartData.length > 0 ? (
              <>
                <Typography 
                  variant="body2" 
                  color="text.secondary" 
                  sx={{ mb: 2, fontStyle: 'italic' }}
                >
                  Clique nos pontos do gráfico para ver detalhes. Passe o mouse sobre as linhas para informações adicionais.
                </Typography>
                <Box sx={{ height: 400, width: '100%' }}>
                  <Line data={prepareChartData()} options={chartOptions} />
                </Box>
              </>
            ) : (
              <Alert severity="info" sx={{ mt: 2 }}>
                Registre alguns sintomas para visualizar o gráfico de evolução.
              </Alert>
            )}
          </Paper>
          
          {/* Tabela de sintomas */}
          {symptoms.length === 0 ? (
            <Alert severity="info">
              Nenhum sintoma registrado para este paciente.
            </Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>Sintoma</TableCell>
                    <TableCell>Intensidade</TableCell>
                    <TableCell align="center">Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {symptoms.map((symptom) => (
                    <TableRow key={symptom.id}>
                      <TableCell>{formatDate(symptom.data)}</TableCell>
                      <TableCell>{symptom.sintoma}</TableCell>
                      <TableCell>{symptom.intensidade}</TableCell>
                      <TableCell align="center">
                        <IconButton
                          color="error"
                          onClick={() => handleOpenDeleteDialog(symptom)}
                          title="Excluir"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
          
          
          {/* Diálogo de confirmação de exclusão */}
          <Dialog
            open={deleteDialogOpen}
            onClose={handleCloseDeleteDialog}
          >
            <DialogTitle>Confirmar exclusão</DialogTitle>
            <DialogContent>
              <DialogContentText>
                Tem certeza que deseja excluir o registro de sintoma 
                "{symptomToDelete?.sintoma}" do dia {formatDate(symptomToDelete?.data)}?
                Esta ação não pode ser desfeita.
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDeleteDialog} color="primary">
                Cancelar
              </Button>
              <Button onClick={handleDeleteSymptom} color="error" autoFocus>
                Excluir
              </Button>
            </DialogActions>
          </Dialog>
          
          {/* Diálogo para adicionar sintoma personalizado */}
          <Dialog
            open={customSymptomDialogOpen}
            onClose={handleCloseCustomSymptomDialog}
            maxWidth="sm"
            fullWidth
          >
            <DialogTitle>Adicionar Sintoma Personalizado</DialogTitle>
            <DialogContent>
              <DialogContentText sx={{ mb: 2 }}>
                Adicione um novo sintoma personalizado para monitorar. Este sintoma estará disponível para todos os pacientes.
              </DialogContentText>
              <TextField
                autoFocus
                margin="dense"
                label="Nome do Sintoma"
                type="text"
                fullWidth
                value={newCustomSymptom}
                onChange={handleCustomSymptomChange}
                variant="outlined"
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseCustomSymptomDialog} color="primary">
                Cancelar
              </Button>
              <Button 
                onClick={handleAddCustomSymptom} 
                color="primary" 
                variant="contained"
                disabled={!newCustomSymptom.trim()}
              >
                Adicionar
              </Button>
            </DialogActions>
          </Dialog>
        </>
      )}
    </Paper>
  );
};

export default SymptomsManager;
