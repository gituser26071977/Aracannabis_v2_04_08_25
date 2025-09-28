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
} from 'chart.js';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend
);

const SymptomsManager = ({ patientId }) => {
  const [symptoms, setSymptoms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [standardSymptoms, setStandardSymptoms] = useState([]);
  const [customSymptoms, setCustomSymptoms] = useState([]);
  const [newCustomSymptom, setNewCustomSymptom] = useState('');
  const [customSymptomDialogOpen, setCustomSymptomDialogOpen] = useState(false);
  const [newSymptom, setNewSymptom] = useState({
    data: new Date().toISOString().split('T')[0],
    sintoma: '',
    intensidade: 5
  });
  
  // Estado para o gráfico
  const [chartData, setChartData] = useState(null);
  const [showChart, setShowChart] = useState(false);
  
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
    try {
      const data = await sintomasService.obterDadosGrafico(patientId);
      setChartData(data.dados_grafico);
      setShowChart(true);
    } catch (err) {
      console.error('Erro ao carregar dados do gráfico:', err);
      setError('Não foi possível carregar o gráfico de sintomas');
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
      handleCloseDeleteDialog();
    } catch (err) {
      console.error('Erro ao excluir sintoma:', err);
      setError('Não foi possível excluir o sintoma');
    }
  };
  
  // Formatar data
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };
  
  // Configuração do gráfico
  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Evolução dos Sintomas',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.parsed.y}`;
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
          text: 'Intensidade'
        }
      },
      x: {
        title: {
          display: true,
          text: 'Data'
        }
      }
    }
  };
  
  // Preparar dados para o gráfico
  const prepareChartData = () => {
    if (!chartData) return null;
    
    const colors = [
      'rgba(75, 192, 192, 1)',
      'rgba(255, 99, 132, 1)',
      'rgba(54, 162, 235, 1)',
      'rgba(255, 206, 86, 1)',
      'rgba(153, 102, 255, 1)',
      'rgba(255, 159, 64, 1)'
    ];
    
    return {
      datasets: chartData.map((dataset, index) => ({
        label: dataset.label,
        data: dataset.data,
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length].replace('1)', '0.2)'),
        tension: 0.2
      }))
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
                    {[...standardSymptoms, ...customSymptoms].map((symptom) => (
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
          
          {/* Botões para gráficos */}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2, gap: 2 }}>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<ChartIcon />}
              onClick={loadChartData}
            >
              Ver Gráfico
            </Button>
            <Button
              variant="outlined"
              color="info"
              startIcon={<ChartIcon />}
              onClick={() => {
                // Navegar para a aba de gráfico combinado
                const currentPath = window.location.pathname;
                if (currentPath.includes('/pacientes/detail/')) {
                  // Usar o router para navegar para a aba de gráfico combinado
                  window.dispatchEvent(new CustomEvent('navigateToTab', { detail: { tabIndex: 4 } }));
                }
              }}
            >
              Gráfico Combinado
            </Button>
          </Box>
          
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
          
          {/* Gráfico de sintomas */}
          {showChart && chartData && (
            <Box sx={{ mt: 4, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Evolução dos Sintomas
              </Typography>
              <Line options={chartOptions} data={prepareChartData()} />
            </Box>
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
