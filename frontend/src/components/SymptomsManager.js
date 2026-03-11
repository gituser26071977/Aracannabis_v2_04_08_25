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

} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  BarChart as ChartIcon,
  AddCircleOutline as AddCustomIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';
import api, { sintomasService, gad7Service, phq9Service } from '../services/api';
import { Line } from 'react-chartjs-2';

import PHQ9Test from './PHQ9Test';
import GAD7Test from './GAD7Test';
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
  const [chartDataType, setChartDataType] = useState('all'); // 'all', 'manual', 'test'

  // Estado para diálogo de confirmação de exclusão
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [symptomToDelete, setSymptomToDelete] = useState(null);



  // Estado para teste GAD-7 (Ansiedade)
  const [gad7DialogOpen, setGad7DialogOpen] = useState(false);


  // Estado para teste PHQ-9
  const [phq9DialogOpen, setPhq9DialogOpen] = useState(false);

  // Estado para último teste PHQ-9
  const [ultimoTestePHQ9, setUltimoTestePHQ9] = useState(null);

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


        // Carregar último teste PHQ-9
        await carregarUltimoTestePHQ9();
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




  // Estados para histórico de testes
  const [testsDialogOpen, setTestsDialogOpen] = useState(false);
  const [gad7Tests, setGad7Tests] = useState([]);
  const [phq9Tests, setPhq9Tests] = useState([]);

  // Load Tests History
  const loadTestsHistory = async () => {
    try {
      const gad7Data = await gad7Service.listar(patientId);
      setGad7Tests(gad7Data.testes || []);

      const phq9Data = await phq9Service.listar(patientId);
      setPhq9Tests(phq9Data.testes || []);
    } catch (error) {
      console.error("Erro ao carregar histórico de testes:", error);
    }
  };

  // Delete Test Handler
  const handleDeleteTest = async (type, id) => {
    if (!window.confirm('Tem certeza que deseja excluir este teste? Essa ação não pode ser desfeita.')) return;

    try {
      if (type === 'gad7') {
        await gad7Service.excluir(id);
        setGad7Tests(prev => prev.filter(t => t.id !== id));
      } else if (type === 'phq9') {
        await phq9Service.excluir(id);
        setPhq9Tests(prev => prev.filter(t => t.id !== id));
      }
      // Reload chart to reflect changes
      await loadChartData();
    } catch (error) {
      console.error("Erro ao excluir teste:", error);
      setError("Erro ao excluir o teste.");
    }
  };

  // Carregar último teste PHQ-9
  const carregarUltimoTestePHQ9 = async () => {
    try {
      const response = await api.get(`/phq9/paciente/${patientId}/ultimo`);
      setUltimoTestePHQ9(response.data.teste);
    } catch (err) {
      // Se não encontrar teste, não é erro
      console.log('Nenhum teste PHQ-9 encontrado para este paciente');
    }
  };


  // Carregar dados do gráfico
  const loadChartData = async (periodo = '1y') => {
    setChartLoading(true);
    try {
      const data = await sintomasService.obterDadosGrafico(patientId, periodo);
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

    // Acionar testes específicos se o sintoma mudar
    if (name === 'sintoma') {
      if (value === 'Depressão') {
        setPhq9DialogOpen(true);
      } else if (value === 'Ansiedade') {
        setGad7DialogOpen(true);
      }
    }
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


  // Abrir diálogo do teste PHQ-9
  const handleOpenPHQ9Dialog = () => {
    setPhq9DialogOpen(true);
  };

  // Fechar diálogo do teste PHQ-9
  const handleClosePHQ9Dialog = () => {
    setPhq9DialogOpen(false);
  };

  // Callback quando o teste PHQ-9 é concluído
  const handlePHQ9Completed = (testeData) => {
    // Normalizar pontuação (0-27) para escala 0-10
    // Pontuação máxima PHQ-9 = 27
    const intensidade = Math.round((testeData.rawScore / 27) * 10);

    setNewSymptom(prev => ({
      ...prev,
      intensidade: intensidade
    }));

    setPhq9DialogOpen(false);

    // Opcional: Salvar o teste no banco (já é salvo pelo componente PHQ9Test se configurado,
    // mas aqui estamos usando o valor para preencher o sintoma)
  };
  // Handlers para GAD-7
  const handleCloseGAD7Dialog = () => {
    setGad7DialogOpen(false);
  };

  const handleGAD7Completed = async (testeData) => {
    // Normalizar pontuação (0-21) para escala 0-10
    // Pontuação máxima GAD-7 = 21
    const intensidade = Math.round((testeData.rawScore / 21) * 10);

    setNewSymptom(prev => ({
      ...prev,
      intensidade: intensidade
    }));

    // Save GAD-7 test to backend if api service is available
    if (testeData.testData) {
      try {
        const payload = {
          ...testeData.testData,
          data_realizacao: newSymptom.data
        };
        await gad7Service.criarTeste(patientId, payload);
        console.log('Teste GAD-7 salvo com sucesso!');
      } catch (error) {
        console.error('Erro ao salvar teste GAD-7:', error);
        setError('Erro ao salvar os resultados detalhados do teste GAD-7, mas a intensidade do sintoma foi atualizada.');
      }
    }

    setGad7DialogOpen(false);
  };

  // Adicionar novo sintoma personalizado
  const handleAddCustomSymptom = async () => {
    if (!newCustomSymptom.trim()) {
      setError('O nome do sintoma não pode estar vazio');
      return;
    }

    try {
      const response = await sintomasService.criarPersonalizado(newCustomSymptom, patientId);

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

  // Remover sintoma personalizado
  const handleRemoveCustomSymptom = async (symptom) => {
    try {
      await sintomasService.excluirPersonalizado(symptom);

      // Atualizar lista de sintomas personalizados
      setCustomSymptoms(prev => prev.filter(s => s !== symptom));

      // Atualizar sintomas padrão também (caso o sintoma removido esteja na lista)
      const standardData = await sintomasService.listarPadrao();
      setStandardSymptoms(standardData.sintomas_padrao || []);

      setError('');
    } catch (err) {
      console.error('Erro ao remover sintoma personalizado:', err);
      setError('Não foi possível remover o sintoma personalizado');
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
    // Handle ISO dates (with 'T') and simple date strings
    let date;
    if (dateString.includes('T')) {
      date = new Date(dateString);
    } else {
      date = new Date(dateString + 'T00:00:00');
    }
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
          title: function (context) {
            const rawData = context[0].raw;
            if (!rawData || !rawData.x) return 'Data: N/A';
            return `Data: ${formatDateRobust(rawData.x)}`;
          },
          label: function (context) {
            const raw = context.raw;
            if (raw && raw.original_value !== undefined && raw.max_value) {
              return `${context.dataset.label}: ${raw.original_value}/${raw.max_value} pontos`;
            }
            return `${context.dataset.label}: ${context.parsed.y}/10`;
          },
          afterLabel: function (context) {
            const raw = context.raw;
            if (raw && raw.original_value !== undefined && raw.max_value) {
              return `(Normalizado: ${context.parsed.y}/10)`;
            }

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
          callback: function (value) {
            return value + '/10';
          }
        }
      },
      x: {
        type: 'time',
        time: {
          unit: 'month',
          displayFormats: {
            month: 'MM/yyyy',
            day: 'dd/MM/yyyy'
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
          major: {
            enabled: true
          },
          maxTicksLimit: 12,
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
        if (point.original_value !== undefined && point.max_value) {
          alert(`Teste: ${dataset.label}\nData: ${dataFormatada}\nPontuação: ${point.original_value}/${point.max_value} pontos`);
        } else {
          alert(`Sintoma: ${dataset.label}\nData: ${dataFormatada}\nIntensidade: ${point.y}/10`);
        }
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
      '#4bc0c0', // Teal
      '#ff6384', // Pink
      '#36a2eb', // Blue
      '#ffce56', // Yellow
      '#9966ff', // Purple
      '#ff9f40', // Orange
      '#28a745', // Green
      '#dc3545', // Red
    ];

    const filteredDatasets = chartData.filter(dataset => {
      const isTest = dataset.data.some(p => p.original_value !== undefined);
      if (chartDataType === 'manual') return !isTest;
      if (chartDataType === 'test') return isTest;
      return true;
    });

    if (filteredDatasets.length === 0) return null;

    return {
      datasets: filteredDatasets.map((dataset, index) => {
        const isTest = dataset.data.some(p => p.original_value !== undefined);
        // Converter strings de data para objetos Date e ordenar cronologicamente
        const processedData = dataset.data.map(point => ({
          ...point,
          x: new Date(point.x)
        })).sort((a, b) => new Date(a.x) - new Date(b.x));

        const baseColor = colors[index % colors.length];

        return {
          label: isTest ? `📋 ${dataset.label} (IA)` : `✍️ ${dataset.label}`,
          data: processedData,
          borderColor: baseColor,
          backgroundColor: baseColor + '4D', // 0.3 opacity
          pointBackgroundColor: baseColor,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          tension: isTest ? 0 : 0.4, // Linhas retas para testes, curvas para sintomas
          borderWidth: 3,
          borderDash: isTest ? [5, 5] : [], // Tracejado para testes
          fill: false
        };
      })
    };
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Gerenciamento de Sintomas
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>


        </Box>
      </Box>

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
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography
                variant="h6"
                component="div"
                sx={{
                  color: '#28a745',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <ChartIcon sx={{ mr: 1 }} />
                Análise Gráfica
              </Typography>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel>Ver dados</InputLabel>
                  <Select
                    value={chartDataType}
                    label="Ver dados"
                    onChange={(e) => setChartDataType(e.target.value)}
                    sx={{ backgroundColor: 'white' }}
                  >
                    <MenuItem value="all">Todos os Dados</MenuItem>
                    <MenuItem value="manual">Sintomas Manuais</MenuItem>
                    <MenuItem value="test">Testes Clínicos (IA)</MenuItem>
                  </Select>
                </FormControl>

                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    loadTestsHistory();
                    setTestsDialogOpen(true);
                  }}
                >
                  Gerenciar Testes
                </Button>

                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Período</InputLabel>
                  <Select
                    value={'1y'} // Use state if period was in state
                    label="Período"
                    onChange={(e) => loadChartData(e.target.value)}
                    defaultValue="1y"
                  >
                    <MenuItem value="1m">Último mês</MenuItem>
                    <MenuItem value="3m">Últimos 3 meses</MenuItem>
                    <MenuItem value="6m">Últimos 6 meses</MenuItem>
                    <MenuItem value="1y">Último ano</MenuItem>
                    <MenuItem value="integral">Todo o histórico</MenuItem>
                  </Select>
                </FormControl>
              </Box>
            </Box>


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

          {/* Diálogo para Gerenciar Testes (Histórico e Exclusão) */}
          <Dialog
            open={testsDialogOpen}
            onClose={() => setTestsDialogOpen(false)}
            maxWidth="md"
            fullWidth
          >
            <DialogTitle>Histórico de Testes Realizados</DialogTitle>
            <DialogContent>
              <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, fontWeight: 'bold' }}>
                  Testes de Ansiedade (GAD-7)
                </Typography>
                {gad7Tests.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Nenhum teste GAD-7 realizado.
                  </Typography>
                ) : (
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                          <TableCell>Data</TableCell>
                          <TableCell>Pontuação</TableCell>
                          <TableCell>Nível</TableCell>
                          <TableCell align="right">Ações</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {gad7Tests.map((teste) => (
                          <TableRow key={teste.id}>
                            <TableCell>{formatDateRobust(teste.data_realizacao)}</TableCell>
                            <TableCell>{teste.resultados.pontuacao_total}/21</TableCell>
                            <TableCell>{teste.resultados.nivel_ansiedade.replace('_', ' ')}</TableCell>
                            <TableCell align="right">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteTest('gad7', teste.id)}
                                title="Excluir Teste"
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}

                <Typography variant="subtitle1" gutterBottom sx={{ mt: 2, fontWeight: 'bold' }}>
                  Testes de Depressão (PHQ-9)
                </Typography>
                {phq9Tests.length === 0 ? (
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Nenhum teste PHQ-9 realizado.
                  </Typography>
                ) : (
                  <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
                    <Table size="small">
                      <TableHead>
                        <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                          <TableCell>Data</TableCell>
                          <TableCell>Pontuação</TableCell>
                          <TableCell>Nível</TableCell>
                          <TableCell align="right">Ações</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {phq9Tests.map((teste) => (
                          <TableRow key={teste.id}>
                            <TableCell>{formatDateRobust(teste.data_realizacao)}</TableCell>
                            <TableCell>{teste.resultados.pontuacao_total}/27</TableCell>
                            <TableCell>{teste.resultados.nivel_depressao.replace('_', ' ')}</TableCell>
                            <TableCell align="right">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteTest('phq9', teste.id)}
                                title="Excluir Teste"
                              >
                                <DeleteIcon fontSize="small" />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setTestsDialogOpen(false)}>Fechar</Button>
            </DialogActions>
          </Dialog>

        </>
      )
      }


      {/* Diálogo do Teste PHQ-9 */}
      <PHQ9Test
        patientId={patientId}
        open={phq9DialogOpen}
        onClose={handleClosePHQ9Dialog}
        onTestCompleted={handlePHQ9Completed}
      />
      {/* Diálogo do Teste GAD-7 (Ansiedade) */}
      <GAD7Test
        open={gad7DialogOpen}
        onClose={handleCloseGAD7Dialog}
        onCompleted={handleGAD7Completed}
      />

      {/* Diálogo para Gerenciar Sintomas Personalizados */}
      <Dialog
        open={customSymptomDialogOpen}
        onClose={handleCloseCustomSymptomDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Gerenciar Sintomas Personalizados</DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>
            Sintomas Personalizados Existentes
          </Typography>

          {customSymptoms.length === 0 ? (
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Nenhum sintoma personalizado cadastrado.
            </Typography>
          ) : (
            <Box sx={{ maxHeight: 200, overflow: 'auto', mb: 2 }}>
              {customSymptoms.map((symptom, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    py: 1,
                    borderBottom: '1px solid rgba(0, 0, 0, 0.12)'
                  }}
                >
                  <Typography>{symptom}</Typography>
                  <IconButton
                    size="small"
                    color="error"
                    onClick={() => handleRemoveCustomSymptom(symptom)}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Box>
              ))}
            </Box>
          )}

          <Divider sx={{ my: 2 }} />

          <Typography variant="h6" gutterBottom>
            Adicionar Novo Sintoma Personalizado
          </Typography>
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

    </Paper >
  );
};


export default SymptomsManager;
