import React, { useState, useEffect, useCallback } from 'react';
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
  Alert,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon,
  BarChart as ChartIcon,
  Inventory as ProductIcon
} from '@mui/icons-material';
import { dosagensService, produtosService } from '../services/api';
import ProductForm from './ProductForm';
import DosageChart from './DosageChart';

const DosageManager = ({ patientId }) => {
  const [dosages, setDosages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Estado para o formulário de nova dosagem
  const [newDosage, setNewDosage] = useState({
    data: new Date().toISOString().split('T')[0],
    dosagem: '',
    gotas: 0,
    frequencia_diaria: 1,
    concentracao_cbd: 0,
    concentracao_thc: 0,
    concentracao_cbg: 0,
    concentracao_cbn: 0,
    gotas_por_ml: 30
  });
  
  // Estado para o gráfico
  const [chartData, setChartData] = useState(null);
  const [showChart, setShowChart] = useState(true);
  const [chartLoading, setChartLoading] = useState(false);
  
  // Estado para diálogo de confirmação de exclusão
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [dosageToDelete, setDosageToDelete] = useState(null);
  
  // Estados para produtos
  const [produtos, setProdutos] = useState([]);
  const [produtoSelecionado, setProdutoSelecionado] = useState('');
  const [showProdutoForm, setShowProdutoForm] = useState(false);
  const [novoProduto, setNovoProduto] = useState({
    nome: '',
    tipo: 'oleo',
    concentracao_cbd: 0,
    concentracao_thc: 0,
    concentracao_cbg: 0,
    concentracao_cbn: 0,
    gotas_por_ml: 30,
    volume_ml: 30,
    fabricante: '',
    descricao: ''
  });
  
  // Estado para abas
  const [tabValue, setTabValue] = useState(0);
  
  // Carregar dosagens e produtos
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carregar dosagens do paciente
        const dosagesData = await dosagensService.listar(patientId);
        setDosages(dosagesData.dosagens || []);
        
        // Carregar produtos disponíveis
        const produtosData = await produtosService.listar();
        setProdutos(produtosData.produtos || []);
        
        // Carregar dados do gráfico automaticamente
        await loadChartData();
        
        setError('');
      } catch (err) {
        console.error('Erro ao carregar dados de dosagens:', err);
        setError('Não foi possível carregar as dosagens');
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
      const data = await dosagensService.obterDadosGrafico(patientId);
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
    
    // Converter valores numéricos
    let processedValue = value;
    if (['gotas', 'frequencia_diaria', 'gotas_por_ml'].includes(name)) {
      processedValue = parseInt(value) || 0;
    } else if (['concentracao_cbd', 'concentracao_thc', 'concentracao_cbg', 'concentracao_cbn'].includes(name)) {
      processedValue = parseFloat(value) || 0;
    }
    
    setNewDosage(prev => ({
      ...prev,
      [name]: processedValue
    }));
  };
  
  // Calcular dose diária (usando o mesmo método do backend)
  const calcularDoseDiaria = (dosagem) => {
    const gotasPorMl = dosagem.gotas_por_ml || 30; // Padrão 30 gotas/ml
    const mlPorGota = gotasPorMl > 0 ? 1 / gotasPorMl : 0.033; // Fallback se zero
    const mlPorDose = dosagem.gotas * mlPorGota;
    const mlPorDia = mlPorDose * dosagem.frequencia_diaria;
    
    return {
      ml_por_dia: mlPorDia.toFixed(2),
      cbd_mg: (mlPorDia * (dosagem.concentracao_cbd || 0)).toFixed(2),
      thc_mg: (mlPorDia * (dosagem.concentracao_thc || 0)).toFixed(2),
      cbg_mg: (mlPorDia * (dosagem.concentracao_cbg || 0)).toFixed(2),
      cbn_mg: (mlPorDia * (dosagem.concentracao_cbn || 0)).toFixed(2),
      canabinoides_totais: (mlPorDia * (
        (dosagem.concentracao_cbd || 0) + 
        (dosagem.concentracao_thc || 0) + 
        (dosagem.concentracao_cbg || 0) + 
        (dosagem.concentracao_cbn || 0)
      )).toFixed(2)
    };
  };
  
  // Registrar nova dosagem
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!newDosage.dosagem.trim()) {
      setError('Informe a dosagem');
      return;
    }
    
    try {
      const response = await dosagensService.criar({
        paciente_id: patientId,
        ...newDosage
      });
      
      // Adicionar nova dosagem à lista
      setDosages([response.dosagem, ...dosages]);
      
      // Recarregar dados do gráfico
      await loadChartData();
      
      // Resetar formulário
      setNewDosage({
        data: new Date().toISOString().split('T')[0],
        dosagem: '',
        gotas: 0,
        frequencia_diaria: 1,
        concentracao_cbd: 0,
        concentracao_thc: 0,
        concentracao_cbg: 0,
        concentracao_cbn: 0,
        gotas_por_ml: 30
      });
      
      setError('');
    } catch (err) {
      console.error('Erro ao registrar dosagem:', err);
      setError('Não foi possível registrar a dosagem');
    }
  };
  
  // Abrir diálogo de confirmação de exclusão
  const handleOpenDeleteDialog = (dosage) => {
    setDosageToDelete(dosage);
    setDeleteDialogOpen(true);
  };
  
  // Fechar diálogo de confirmação de exclusão
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setDosageToDelete(null);
  };
  
  // Excluir dosagem
  const handleDeleteDosage = async () => {
    if (!dosageToDelete) return;
    
    try {
      await dosagensService.excluir(dosageToDelete.id);
      setDosages(dosages.filter(d => d.id !== dosageToDelete.id));
      
      // Recarregar dados do gráfico
      await loadChartData();
      
      handleCloseDeleteDialog();
    } catch (err) {
      console.error('Erro ao excluir dosagem:', err);
      setError('Não foi possível excluir a dosagem');
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
        text: '💊 Evolução das Dosagens ao Longo do Tempo',
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
            return `Data: ${context[0].label}`;
          },
          label: function(context) {
            return `Dosagem: ${context.parsed.y} gotas`;
          },
          afterLabel: function(context) {
            const dataPoint = chartData && chartData.data ? chartData.data[context.dataIndex] : null;
            if (dataPoint && dataPoint.dosagem_texto) {
              return `Descrição: ${dataPoint.dosagem_texto}`;
            }
            return '';
          }
        }
      }
    },
    scales: {
      y: {
        min: 0,
        title: {
          display: true,
          text: 'Quantidade (gotas)',
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
            return value + ' gotas';
          }
        }
      },
      x: {
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
          }
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const element = elements[0];
        const dataIndex = element.index;
        const dataPoint = chartData && chartData.data ? chartData.data[dataIndex] : null;
        
        if (dataPoint) {
          // Mostrar informações detalhadas do ponto clicado
          alert(`Data: ${dataPoint.x}\nDosagem: ${dataPoint.y} gotas\nDescrição: ${dataPoint.dosagem_texto || 'N/A'}`);
        }
      }
    },
    onHover: (event, elements) => {
      event.native.target.style.cursor = elements.length > 0 ? 'pointer' : 'default';
    }
  };
  
  // Preparar dados para o gráfico
  const prepareChartData = () => {
    if (!chartData || !chartData.data || chartData.data.length === 0) return null;
    
    const colors = [
      'rgba(54, 162, 235, 1)',   // Azul
      'rgba(255, 99, 132, 1)',   // Vermelho
      'rgba(75, 192, 192, 1)',   // Verde
      'rgba(255, 206, 86, 1)',   // Amarelo
      'rgba(153, 102, 255, 1)',  // Roxo
      'rgba(255, 159, 64, 1)'    // Laranja
    ];
    
    return {
      datasets: [{
        label: chartData.label || 'Dosagens',
        data: chartData.data,
        borderColor: colors[0],
        backgroundColor: colors[0].replace('1)', '0.3)'),
        pointBackgroundColor: colors[0],
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8,
        tension: 0.3,
        borderWidth: 3,
        fill: false
      }]
    };
  };
  
  // Manipuladores para produtos
  const handleProdutoSelecionado = (e) => {
    const produtoId = e.target.value;
    setProdutoSelecionado(produtoId);
    
    if (produtoId) {
      const produto = produtos.find(p => p.id === parseInt(produtoId));
      if (produto) {
        setNewDosage(prev => ({
          ...prev,
          dosagem: produto.nome,
          concentracao_cbd: produto.concentracao_cbd,
          concentracao_thc: produto.concentracao_thc,
          concentracao_cbg: produto.concentracao_cbg,
          concentracao_cbn: produto.concentracao_cbn,
          gotas_por_ml: produto.gotas_por_ml
        }));
      }
    }
  };

  const handleNovoProdutoChange = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    const { name, value } = e.target;
    
    setNovoProduto(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);

  const handleCriarProduto = async (e) => {
    e.preventDefault();
    
    if (!novoProduto.nome.trim()) {
      setError('Nome do produto é obrigatório');
      return;
    }
    
    try {
      const response = await produtosService.criar(novoProduto);
      
      // Atualizar lista de produtos
      setProdutos([...produtos, response.produto]);
      
      // Resetar formulário
      setNovoProduto({
        nome: '',
        tipo: 'oleo',
        concentracao_cbd: 0,
        concentracao_thc: 0,
        concentracao_cbg: 0,
        concentracao_cbn: 0,
        gotas_por_ml: 30,
        volume_ml: 30,
        fabricante: '',
        descricao: ''
      });
      
      setShowProdutoForm(false);
      setError('');
      alert('Produto criado com sucesso!');
    } catch (err) {
      console.error('Erro ao criar produto:', err);
      setError('Não foi possível criar o produto');
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Componente TabPanel
  function TabPanel(props) {
    const { children, value, index, ...other } = props;
    return (
      <div
        role="tabpanel"
        hidden={value !== index}
        id={`dosage-tabpanel-${index}`}
        aria-labelledby={`dosage-tab-${index}`}
        {...other}
      >
        {value === index && (
          <Box sx={{ p: 3 }}>
            {children}
          </Box>
        )}
      </div>
    );
  }

  function a11yProps(index) {
    return {
      id: `dosage-tab-${index}`,
      'aria-controls': `dosage-tabpanel-${index}`,
    };
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Gerenciamento de Dosagens e Produtos
      </Typography>
      
      {/* Abas */}
      <Paper elevation={3} sx={{ mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="Abas de dosagens e produtos"
          variant="fullWidth"
        >
          <Tab label="Dosagens" {...a11yProps(0)} />
          <Tab label="📦 Produtos" {...a11yProps(1)} />
        </Tabs>
      </Paper>
      
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
          {/* Conteúdo das abas */}
          <TabPanel value={tabValue} index={0}>
            <Paper elevation={3} sx={{ p: 3 }}>
          {/* Formulário para registrar nova dosagem */}
          <Box component="form" onSubmit={handleSubmit} sx={{ mb: 4 }}>
            <Typography variant="subtitle1" gutterBottom>
              Registrar Nova Dosagem
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  name="data"
                  label="Data"
                  type="date"
                  value={newDosage.data}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Produto</InputLabel>
                  <Select
                    value={produtoSelecionado}
                    onChange={handleProdutoSelecionado}
                    label="Produto"
                  >
                    <MenuItem value="">
                      <em>Selecione um produto ou digite manualmente</em>
                    </MenuItem>
                    {produtos.map((produto) => (
                      <MenuItem key={produto.id} value={produto.id}>
                        {produto.nome} (CBD: {produto.concentracao_cbd}mg/ml)
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  name="dosagem"
                  label="Descrição da Dosagem"
                  value={newDosage.dosagem}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  helperText="Preenchido automaticamente ao selecionar produto"
                />
              </Grid>
              
              <Grid item xs={6} sm={3} md={2}>
                <TextField
                  name="gotas"
                  label="Gotas"
                  type="number"
                  value={newDosage.gotas || ''}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  inputProps={{ min: 1 }}
                  placeholder="Ex: 5"
                />
              </Grid>
              
              <Grid item xs={6} sm={3} md={2}>
                <TextField
                  name="frequencia_diaria"
                  label="Vezes ao dia"
                  type="number"
                  value={newDosage.frequencia_diaria}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  inputProps={{ min: 1, max: 4 }}
                  helperText="1 a 4 vezes"
                />
              </Grid>
              
              <Grid item xs={6} sm={3} md={2}>
                <TextField
                  name="gotas_por_ml"
                  label="Gotas/ml"
                  type="number"
                  value={newDosage.gotas_por_ml}
                  onChange={handleInputChange}
                  fullWidth
                  inputProps={{ min: 1, max: 50 }}
                  helperText="Padrão: 30"
                />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                  Concentrações de Canabinoides (mg/ml)
                </Typography>
              </Grid>
              
              <Grid item xs={6} sm={3}>
                <TextField
                  name="concentracao_cbd"
                  label="CBD (mg/ml)"
                  type="number"
                  value={newDosage.concentracao_cbd || ''}
                  onChange={handleInputChange}
                  fullWidth
                  inputProps={{ min: 0, step: 0.1 }}
                  placeholder="Ex: 25.5"
                />
              </Grid>
              
              <Grid item xs={6} sm={3}>
                <TextField
                  name="concentracao_thc"
                  label="THC (mg/ml)"
                  type="number"
                  value={newDosage.concentracao_thc || ''}
                  onChange={handleInputChange}
                  fullWidth
                  inputProps={{ min: 0, step: 0.1 }}
                  placeholder="Ex: 2.5"
                />
              </Grid>
              
              <Grid item xs={6} sm={3}>
                <TextField
                  name="concentracao_cbg"
                  label="CBG (mg/ml)"
                  type="number"
                  value={newDosage.concentracao_cbg || ''}
                  onChange={handleInputChange}
                  fullWidth
                  inputProps={{ min: 0, step: 0.1 }}
                  placeholder="Ex: 1.0"
                />
              </Grid>
              
              <Grid item xs={6} sm={3}>
                <TextField
                  name="concentracao_cbn"
                  label="CBN (mg/ml)"
                  type="number"
                  value={newDosage.concentracao_cbn || ''}
                  onChange={handleInputChange}
                  fullWidth
                  inputProps={{ min: 0, step: 0.1 }}
                  placeholder="Ex: 0.5"
                />
              </Grid>
              
              {/* Calculadora de dose diária */}
              {(newDosage.gotas > 0 && newDosage.frequencia_diaria > 0) && (
                <Grid item xs={12}>
                  <Paper elevation={1} sx={{ p: 2, mt: 1, bgcolor: 'background.paper' }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Cálculo de Dose Diária
                    </Typography>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={4} md={2}>
                        <Typography variant="body2" color="text.secondary">
                          Volume diário:
                        </Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {calcularDoseDiaria(newDosage).ml_por_dia} ml/dia
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={6} sm={4} md={2}>
                        <Typography variant="body2" color="text.secondary">
                          CBD:
                        </Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {calcularDoseDiaria(newDosage).cbd_mg} mg/dia
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={6} sm={4} md={2}>
                        <Typography variant="body2" color="text.secondary">
                          THC:
                        </Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {calcularDoseDiaria(newDosage).thc_mg} mg/dia
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={6} sm={4} md={2}>
                        <Typography variant="body2" color="text.secondary">
                          CBG:
                        </Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {calcularDoseDiaria(newDosage).cbg_mg} mg/dia
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={6} sm={4} md={2}>
                        <Typography variant="body2" color="text.secondary">
                          CBN:
                        </Typography>
                        <Typography variant="body1" fontWeight="bold">
                          {calcularDoseDiaria(newDosage).cbn_mg} mg/dia
                        </Typography>
                      </Grid>
                      
                      <Grid item xs={6} sm={4} md={2}>
                        <Typography variant="body2" color="text.secondary">
                          Total:
                        </Typography>
                        <Typography variant="body1" fontWeight="bold" color="primary">
                          {calcularDoseDiaria(newDosage).canabinoides_totais} mg/dia
                        </Typography>
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>
              )}
              
              <Grid item xs={12}>
                <Button
                  type="submit"
                  variant="contained"
                  color="primary"
                  startIcon={<AddIcon />}
                  sx={{ mt: 2 }}
                >
                  Registrar Dosagem
                </Button>
              </Grid>
            </Grid>
          </Box>
          
          {/* Gráfico de Dosagens */}
          <Paper 
            elevation={2} 
            sx={{ 
              p: 3, 
              mb: 3,
              background: 'linear-gradient(135deg, #f8f9fa 0%, #e3f2fd 100%)',
              border: '2px solid #2196f3',
              borderRadius: 2
            }}
          >
            <Typography 
              variant="h6" 
              gutterBottom 
              sx={{ 
                color: 'primary.main',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: 1
              }}
            >
              💊 Gráfico de Evolução das Dosagens
            </Typography>
            
            <DosageChart patientId={patientId} />
          </Paper>
          
          {/* Tabela de dosagens */}
          {dosages.length === 0 ? (
            <Alert severity="info">
              Nenhuma dosagem registrada para este paciente.
            </Alert>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Data</TableCell>
                    <TableCell>Descrição</TableCell>
                    <TableCell>Gotas</TableCell>
                    <TableCell>Freq.</TableCell>
                    <TableCell>CBD (mg/dia)</TableCell>
                    <TableCell>THC (mg/dia)</TableCell>
                    <TableCell>Total (mg/dia)</TableCell>
                    <TableCell align="center">Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {dosages.map((dosage) => {
                    // Calcular dose diária para exibição
                    const doseDiaria = dosage.dose_diaria || 
                      calcularDoseDiaria({
                        gotas: dosage.gotas || 0,
                        frequencia_diaria: dosage.frequencia_diaria || 1,
                        concentracao_cbd: dosage.concentracao_cbd || 0,
                        concentracao_thc: dosage.concentracao_thc || 0,
                        concentracao_cbg: dosage.concentracao_cbg || 0,
                        concentracao_cbn: dosage.concentracao_cbn || 0,
                        gotas_por_ml: dosage.gotas_por_ml || 30
                      });
                    
                    return (
                      <TableRow key={dosage.id}>
                        <TableCell>{formatDate(dosage.data)}</TableCell>
                        <TableCell>{dosage.dosagem}</TableCell>
                        <TableCell>{dosage.gotas || '-'}</TableCell>
                        <TableCell>{dosage.frequencia_diaria || '-'}x</TableCell>
                        <TableCell>{typeof doseDiaria === 'object' ? doseDiaria.cbd_mg : '-'}</TableCell>
                        <TableCell>{typeof doseDiaria === 'object' ? doseDiaria.thc_mg : '-'}</TableCell>
                        <TableCell>{typeof doseDiaria === 'object' ? doseDiaria.canabinoides_totais : '-'}</TableCell>
                        <TableCell align="center">
                          <IconButton
                            color="error"
                            onClick={() => handleOpenDeleteDialog(dosage)}
                            title="Excluir"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
            </Paper>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <Paper elevation={3} sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Gerenciamento de Produtos
              </Typography>
              
              {/* Botão para adicionar produto */}
              <Box sx={{ mb: 3 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={() => setShowProdutoForm(!showProdutoForm)}
                >
                  {showProdutoForm ? 'Cancelar' : 'Adicionar Produto'}
                </Button>
              </Box>
              
              {/* Formulário de novo produto */}
              {showProdutoForm && (
                <ProductForm
                  onSubmit={async (produtoData) => {
                    try {
                      const response = await produtosService.criar(produtoData);
                      setProdutos([...produtos, response.produto]);
                      setShowProdutoForm(false);
                      setError('');
                      alert('Produto criado com sucesso!');
                    } catch (err) {
                      console.error('Erro ao criar produto:', err);
                      setError('Não foi possível criar o produto');
                    }
                  }}
                  onCancel={() => setShowProdutoForm(false)}
                />
              )}
              
              <Divider sx={{ my: 3 }} />
              
              {/* Lista de produtos */}
              <Typography variant="subtitle1" gutterBottom>
                Produtos Cadastrados ({produtos.length})
              </Typography>
              
              {produtos.length === 0 ? (
                <Alert severity="info">
                  Nenhum produto cadastrado.
                </Alert>
              ) : (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Nome</TableCell>
                        <TableCell>Fabricante</TableCell>
                        <TableCell>CBD (mg/ml)</TableCell>
                        <TableCell>THC (mg/ml)</TableCell>
                        <TableCell>CBG (mg/ml)</TableCell>
                        <TableCell>CBN (mg/ml)</TableCell>
                        <TableCell>Gotas/ml</TableCell>
                        <TableCell align="center">Ações</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {produtos.map((produto) => (
                        <TableRow key={produto.id}>
                          <TableCell>{produto.nome}</TableCell>
                          <TableCell>{produto.fabricante || '-'}</TableCell>
                          <TableCell>{produto.concentracao_cbd}</TableCell>
                          <TableCell>{produto.concentracao_thc}</TableCell>
                          <TableCell>{produto.concentracao_cbg}</TableCell>
                          <TableCell>{produto.concentracao_cbn}</TableCell>
                          <TableCell>{produto.gotas_por_ml}</TableCell>
                          <TableCell align="center">
                            <IconButton
                              color="error"
                              onClick={() => {
                                if (window.confirm('Tem certeza que deseja excluir este produto?')) {
                                  produtosService.excluir(produto.id).then(() => {
                                    setProdutos(produtos.filter(p => p.id !== produto.id));
                                    alert('Produto excluído com sucesso!');
                                  }).catch(err => {
                                    console.error('Erro ao excluir produto:', err);
                                    setError('Não foi possível excluir o produto');
                                  });
                                }
                              }}
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
            </Paper>
          </TabPanel>
          
          {/* Diálogo de confirmação de exclusão */}
          <Dialog
            open={deleteDialogOpen}
            onClose={handleCloseDeleteDialog}
          >
            <DialogTitle>Confirmar exclusão</DialogTitle>
            <DialogContent>
              <DialogContentText>
                Tem certeza que deseja excluir o registro de dosagem 
                "{dosageToDelete?.dosagem}" do dia {formatDate(dosageToDelete?.data)}?
                Esta ação não pode ser desfeita.
              </DialogContentText>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDeleteDialog} color="primary">
                Cancelar
              </Button>
              <Button onClick={handleDeleteDosage} color="error" autoFocus>
                Excluir
              </Button>
            </DialogActions>
          </Dialog>
        </>
      )}
    </Box>
  );
};

export default DosageManager;
