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
  Alert,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon,
  BarChart as ChartIcon
} from '@mui/icons-material';
import { dosagensService } from '../services/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Registrar componentes do Chart.js
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

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
  const [showChart, setShowChart] = useState(false);
  
  // Estado para diálogo de confirmação de exclusão
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [dosageToDelete, setDosageToDelete] = useState(null);
  
  // Carregar dosagens
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carregar dosagens do paciente
        const dosagesData = await dosagensService.listar(patientId);
        setDosages(dosagesData.dosagens || []);
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
    try {
      const data = await dosagensService.obterDadosGrafico(patientId);
      setChartData(data.dados_grafico);
      setShowChart(true);
    } catch (err) {
      console.error('Erro ao carregar dados do gráfico:', err);
      setError('Não foi possível carregar o gráfico de dosagens');
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
      handleCloseDeleteDialog();
    } catch (err) {
      console.error('Erro ao excluir dosagem:', err);
      setError('Não foi possível excluir a dosagem');
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
        text: 'Evolução das Dosagens',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const dataPoint = chartData.data[context.dataIndex];
            return `${dataPoint.dosagem_texto}`;
          }
        }
      }
    },
    scales: {
      y: {
        title: {
          display: true,
          text: 'Dosagem'
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
    
    return {
      datasets: [{
        label: chartData.label,
        data: chartData.data,
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.2
      }]
    };
  };
  
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Gerenciamento de Dosagens
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
                <TextField
                  name="dosagem"
                  label="Descrição da Dosagem"
                  value={newDosage.dosagem}
                  onChange={handleInputChange}
                  fullWidth
                  required
                  helperText="Ex: Óleo Full Spectrum 10%"
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
                  // Usar o evento personalizado para navegar para a aba de gráfico combinado
                  window.dispatchEvent(new CustomEvent('navigateToTab', { detail: { tabIndex: 4 } }));
                }
              }}
            >
              Gráfico Combinado
            </Button>
          </Box>
          
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
          
          {/* Gráfico de dosagens */}
          {showChart && chartData && (
            <Box sx={{ mt: 4, height: 400 }}>
              <Typography variant="h6" gutterBottom>
                Evolução das Dosagens
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
    </Paper>
  );
};

export default DosageManager;
