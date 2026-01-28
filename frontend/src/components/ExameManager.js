import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  Chip,
  Card,
  CardContent,
  CardMedia,
  Grid,
  Tabs,
  Tab,
  Divider,
  Autocomplete
} from '@mui/material';
import {
  CloudUpload,
  Delete,
  TextFields,
  InsertChart,
  Visibility,
  TrendingUp,
  Image as ImageIcon,
  Description,
  GetApp
} from '@mui/icons-material';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
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
import { exameService } from '../services/api';
import ImageViewer from './ImageViewer';
import MediaCapture from './MediaCapture';
import MobileConnectQR from './MobileConnectQR'; // Importação do componente de QR Code
import { CameraAlt, PhonelinkRing } from '@mui/icons-material';

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

const ExameManager = ({ patientId }) => {
  const [exames, setExames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [openQRDialog, setOpenQRDialog] = useState(false);
  const [selectedExame, setSelectedExame] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [tipoExame, setTipoExame] = useState('texto');
  const [examNames, setExamNames] = useState([]);
  const [newExame, setNewExame] = useState({
    titulo: '',
    descricao: '',
    arquivo: null,
    valor: '',
    unidade: '',
    data_exame: new Date().toISOString().split('T')[0] // data de hoje
  });

  useEffect(() => {
    const carregarExames = async () => {
      if (!patientId) return;

      try {
        setLoading(true);
        const response = await exameService.listarPorPaciente(patientId);
        setExames(response);
        setError('');
      } catch (err) {
        setError('Falha ao carregar exames');
        console.error('Erro ao carregar exames:', err);
      } finally {
        setLoading(false);
      }
    };

    carregarExames();
  }, [patientId]);

  useEffect(() => {
    const carregarNomesExames = async () => {
      try {
        const response = await exameService.obterNomesExamesUnicos();
        setExamNames(response.exames || []);
      } catch (err) {
        console.error('Erro ao carregar nomes de exames:', err);
        // Não definir erro para não interferir na experiência do usuário
      }
    };

    carregarNomesExames();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewExame({
      ...newExame,
      [name]: value
    });
  };

  const handleFileChange = (e) => {
    setNewExame({
      ...newExame,
      arquivo: e.target.files[0]
    });
  };

  const handleCapture = (file) => {
    setNewExame({
      ...newExame,
      arquivo: file
    });
  };

  const handleMobileUpload = (file) => {
    setNewExame({
      ...newExame,
      arquivo: file
    });
    setOpenQRDialog(false); // Fecha o QR code
  };

  const handleTipoExameChange = (event, newTipo) => {
    if (newTipo !== null) {
      setTipoExame(newTipo);
      setNewExame({
        ...newExame,
        arquivo: null,
        valor: '',
        unidade: ''
      });
    }
  };

  const handleSubmit = async () => {
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user || !user.id) {
      setError('Usuário não autenticado');
      return;
    }

    if (!newExame.titulo.trim()) {
      setError('Por favor, informe o título do exame');
      return;
    }

    if (tipoExame === 'arquivo' && !newExame.arquivo) {
      setError('Por favor, selecione um arquivo para upload');
      return;
    }

    if (tipoExame === 'numerico' && !newExame.valor) {
      setError('Por favor, informe o valor do exame');
      return;
    }

    try {
      setLoading(true);
      let formData = new FormData();
      formData.append('titulo', newExame.titulo);
      formData.append('descricao', newExame.descricao || '');
      formData.append('paciente_id', patientId);
      formData.append('profissional_id', user.id);
      formData.append('tipo_exame', tipoExame);
      formData.append('data_exame', newExame.data_exame);

      if (tipoExame === 'arquivo') {
        formData.append('arquivos', newExame.arquivo);
      } else if (tipoExame === 'numerico') {
        formData.append('valor', newExame.valor);
        formData.append('unidade', newExame.unidade || '');
      }

      const response = await exameService.criar(formData);

      setExames([...exames, response]);
      setNewExame({
        titulo: '',
        descricao: '',
        arquivo: null,
        valor: '',
        unidade: '',
        data_exame: new Date().toISOString().split('T')[0]
      });
      setOpenDialog(false);
      setError('');
    } catch (err) {
      setError('Falha ao enviar exame');
      console.error('Erro ao criar exame:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (exameId) => {
    if (window.confirm('Tem certeza que deseja excluir este exame?')) {
      try {
        setLoading(true);
        await exameService.excluir(exameId);
        setExames(exames.filter(e => e.id !== exameId));
        setError('');
      } catch (err) {
        setError('Falha ao excluir exame');
        console.error('Erro ao excluir exame:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleViewExame = (exame) => {
    setSelectedExame(exame);
    setOpenViewDialog(true);
  };

  const formatDate = (dateString) => {
    try {
      if (dateString) {
        const dateStr = dateString.split('T')[0];
        const [year, month, day] = dateStr.split('-');
        const date = new Date(year, month - 1, day);

        if (!isNaN(date.getTime())) {
          return date.toLocaleDateString('pt-BR');
        }
      }
    } catch (e) {
      console.error('Erro ao formatar data:', e);
    }
    return 'Data inválida';
  };

  const getExamesByType = (tipo) => {
    return exames.filter(exame => exame.tipo_exame === tipo);
  };

  const getNumericExamsChart = () => {
    const numericExams = getExamesByType('numerico');

    if (numericExams.length === 0) {
      return null;
    }

    // Agrupar por título/tipo de exame
    const groupedExams = {};
    numericExams.forEach(exame => {
      const key = exame.titulo;
      if (!groupedExams[key]) {
        groupedExams[key] = [];
      }
      groupedExams[key].push(exame);
    });

    // Criar labels únicos (datas)
    const allDates = [...new Set(numericExams.map(exame => formatDate(exame.data_exame)))].sort();

    const datasets = Object.keys(groupedExams).map((titulo, index) => {
      const examsGroup = groupedExams[titulo].sort((a, b) => new Date(a.data_exame) - new Date(b.data_exame));
      const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'];

      return {
        label: titulo,
        data: examsGroup.map(exame => parseFloat(exame.valor) || 0),
        borderColor: colors[index % colors.length],
        backgroundColor: colors[index % colors.length] + '20',
        tension: 0.1,
        fill: false
      };
    });

    return {
      labels: allDates,
      datasets: datasets
    };
  };

  const renderExameContent = (exame) => {
    if (exame.tipo_exame === 'texto') {
      return exame.descricao || '';
    } else if (exame.tipo_exame === 'numerico') {
      return `${exame.valor || ''} ${exame.unidade || ''}`.trim();
    } else if (exame.tipo_exame === 'arquivo') {
      return 'Arquivo anexado';
    }
    return '';
  };

  const getTypeIcon = (tipo) => {
    switch (tipo) {
      case 'texto': return <Description />;
      case 'numerico': return <InsertChart />;
      case 'arquivo': return <ImageIcon />;
      default: return <Description />;
    }
  };

  const getTypeColor = (tipo) => {
    switch (tipo) {
      case 'texto': return 'primary';
      case 'numerico': return 'success';
      case 'arquivo': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Exames do Paciente</Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<TrendingUp />}
            onClick={() => setTabValue(1)}
            sx={{ mr: 1 }}
          >
            Gráficos
          </Button>
          <Button
            variant="contained"
            startIcon={<CloudUpload />}
            onClick={() => setOpenDialog(true)}
          >
            Adicionar Exame
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
        <Tab label="Lista de Exames" />
        <Tab label="Gráficos de Tendência" />
        <Tab label="Visualização por Tipo" />
      </Tabs>

      {/* Tab 0: Lista de Exames */}
      {tabValue === 0 && (
        <>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : exames.length === 0 ? (
            <Typography variant="body1" sx={{ p: 2, textAlign: 'center' }}>
              Nenhum exame registrado para este paciente.
            </Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Tipo</TableCell>
                    <TableCell>Título</TableCell>
                    <TableCell>Conteúdo</TableCell>
                    <TableCell>Data</TableCell>
                    <TableCell>Ações</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {exames.map((exame) => (
                    <TableRow key={exame.id}>
                      <TableCell>
                        <Chip
                          icon={getTypeIcon(exame.tipo_exame)}
                          label={exame.tipo_exame}
                          color={getTypeColor(exame.tipo_exame)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{exame.titulo || 'Sem título'}</TableCell>
                      <TableCell>{renderExameContent(exame)}</TableCell>
                      <TableCell>{formatDate(exame.data_exame)}</TableCell>
                      <TableCell>
                        <IconButton onClick={() => handleViewExame(exame)} color="primary">
                          <Visibility />
                        </IconButton>
                        <IconButton onClick={() => handleDelete(exame.id)} color="error">
                          <Delete />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      )}

      {/* Tab 1: Gráficos de Tendência */}
      {tabValue === 1 && (
        <Box>
          {getExamesByType('numerico').length === 0 ? (
            <Alert severity="info">
              Nenhum exame numérico encontrado para gerar gráficos de tendência.
            </Alert>
          ) : (
            <Box sx={{ height: 400 }}>
              {(() => {
                const chartData = getNumericExamsChart();
                return chartData ? (
                  <Line
                    data={chartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top',
                        },
                        title: {
                          display: true,
                          text: 'Tendência dos Exames Numéricos'
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          title: {
                            display: true,
                            text: 'Valores'
                          }
                        },
                        x: {
                          title: {
                            display: true,
                            text: 'Data'
                          }
                        }
                      }
                    }}
                  />
                ) : (
                  <Alert severity="warning">
                    Erro ao gerar gráfico. Verifique os dados dos exames.
                  </Alert>
                );
              })()}
            </Box>
          )}
        </Box>
      )}

      {/* Tab 2: Visualização por Tipo */}
      {tabValue === 2 && (
        <Grid container spacing={3}>
          {['texto', 'numerico', 'arquivo'].map(tipo => {
            const examsByType = getExamesByType(tipo);
            return (
              <Grid item xs={12} md={4} key={tipo}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {getTypeIcon(tipo)} Exames de {tipo}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Total: {examsByType.length}
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                    {examsByType.length === 0 ? (
                      <Typography variant="body2">Nenhum exame deste tipo</Typography>
                    ) : (
                      examsByType.slice(0, 3).map(exame => (
                        <Box key={exame.id} sx={{ mb: 1 }}>
                          <Typography variant="body2" fontWeight="bold">
                            {exame.titulo}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatDate(exame.data_exame)}
                          </Typography>
                        </Box>
                      ))
                    )}
                    {examsByType.length > 3 && (
                      <Typography variant="caption" color="primary">
                        +{examsByType.length - 3} mais...
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}

      {/* Dialog para adicionar exame */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>Adicionar Novo Exame</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <ToggleButtonGroup
              value={tipoExame}
              exclusive
              onChange={handleTipoExameChange}
              aria-label="tipo de exame"
              sx={{ mb: 2 }}
            >
              <ToggleButton value="texto" aria-label="texto">
                <TextFields sx={{ mr: 1 }} /> Texto
              </ToggleButton>
              <ToggleButton value="arquivo" aria-label="arquivo">
                <CloudUpload sx={{ mr: 1 }} /> Arquivo
              </ToggleButton>
              <ToggleButton value="numerico" aria-label="numérico">
                <InsertChart sx={{ mr: 1 }} /> Numérico
              </ToggleButton>
            </ToggleButtonGroup>

            <Autocomplete
              fullWidth
              freeSolo
              options={examNames.map(exam => exam.titulo)}
              value={newExame.titulo}
              onChange={(event, newValue) => {
                setNewExame({
                  ...newExame,
                  titulo: newValue || ''
                });
              }}
              onInputChange={(event, newInputValue) => {
                setNewExame({
                  ...newExame,
                  titulo: newInputValue
                });
              }}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Título do Exame"
                  name="titulo"
                  required
                  sx={{ mb: 2 }}
                  helperText="Digite o nome do exame ou selecione uma sugestão"
                />
              )}
              renderOption={(props, option) => {
                const exam = examNames.find(e => e.titulo === option);
                return (
                  <li {...props}>
                    <Box>
                      <Typography variant="body1">{option}</Typography>
                      {exam && exam.frequencia > 1 && (
                        <Typography variant="caption" color="text.secondary">
                          Usado {exam.frequencia} vezes
                        </Typography>
                      )}
                    </Box>
                  </li>
                );
              }}
            />
            <TextField
              fullWidth
              label="Data do Exame"
              name="data_exame"
              type="date"
              value={newExame.data_exame}
              onChange={handleInputChange}
              sx={{ mb: 2 }}
              InputLabelProps={{ shrink: true }}
              required
            />

            {tipoExame === 'texto' && (
              <TextField
                fullWidth
                label="Descrição"
                name="descricao"
                value={newExame.descricao}
                onChange={handleInputChange}
                multiline
                rows={3}
                sx={{ mb: 2 }}
              />
            )}

            {tipoExame === 'arquivo' && (
              <Box sx={{ mb: 2 }}>
                <input
                  accept="image/*,application/pdf,text/plain"
                  type="file"
                  onChange={handleFileChange}
                  id="file-upload"
                  style={{ display: 'none' }}
                />
                <label htmlFor="file-upload">
                  <Button variant="outlined" component="span" startIcon={<CloudUpload />}>
                    Upload
                  </Button>
                </label>

                <MediaCapture
                  mode="camera"
                  onCapture={handleCapture}
                  triggerButton={
                    <Button
                      variant="outlined"
                      color="secondary"
                      startIcon={<CameraAlt />}
                      sx={{ ml: 2 }}
                    >
                      Tirar Foto
                    </Button>
                  }
                />

                <Button
                  variant="text"
                  startIcon={<PhonelinkRing />}
                  sx={{ ml: 2 }}
                  onClick={() => setOpenQRDialog(true)}
                >
                  Usar Celular
                </Button>

                {newExame.arquivo && (
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Arquivo selecionado: {newExame.arquivo.name}
                  </Typography>
                )}
              </Box>
            )}

            {/* Dialog específico para QR Code */}
            <Dialog open={openQRDialog} onClose={() => setOpenQRDialog(false)} maxWidth="xs">
              <DialogTitle>Conectar Celular</DialogTitle>
              <DialogContent>
                <MobileConnectQR onUploadComplete={handleMobileUpload} />
              </DialogContent>
              <DialogActions>
                <Button onClick={() => setOpenQRDialog(false)}>Cancelar</Button>
              </DialogActions>
            </Dialog>

            {tipoExame === 'numerico' && (
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                  fullWidth
                  label="Valor"
                  name="valor"
                  type="number"
                  value={newExame.valor}
                  onChange={handleInputChange}
                  required
                />
                <TextField
                  fullWidth
                  label="Unidade (opcional)"
                  name="unidade"
                  value={newExame.unidade}
                  onChange={handleInputChange}
                />
              </Box>
            )}

            <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
              {tipoExame === 'texto' && 'Texto será armazenado para análise futura'}
              {tipoExame === 'arquivo' && 'Arquivos serão processados com OCR posteriormente'}
              {tipoExame === 'numerico' && 'Dados numéricos serão usados para gerar gráficos de tendência'}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Salvar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para visualizar exame */}
      <Dialog
        open={openViewDialog}
        onClose={() => setOpenViewDialog(false)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>
          Detalhes do Exame
        </DialogTitle>
        <DialogContent>
          {selectedExame && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Título
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {selectedExame.titulo}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Data
                  </Typography>
                  <Typography variant="body1" gutterBottom>
                    {formatDate(selectedExame.data_exame)}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Tipo
                  </Typography>
                  <Chip
                    icon={getTypeIcon(selectedExame.tipo_exame)}
                    label={selectedExame.tipo_exame}
                    color={getTypeColor(selectedExame.tipo_exame)}
                    size="small"
                  />
                </Grid>
                {selectedExame.profissional_nome && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Profissional
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {selectedExame.profissional_nome}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Conteúdo
                  </Typography>
                  {selectedExame.tipo_exame === 'texto' && (
                    <Typography variant="body1">
                      {selectedExame.descricao || 'Sem descrição'}
                    </Typography>
                  )}
                  {selectedExame.tipo_exame === 'numerico' && (
                    <Typography variant="body1">
                      <strong>{selectedExame.valor}</strong> {selectedExame.unidade}
                    </Typography>
                  )}
                  {selectedExame.tipo_exame === 'arquivo' && (
                    <ImageViewer exameId={selectedExame.id} />
                  )}
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Fechar</Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ExameManager;
