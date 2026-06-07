import React, { useState, useEffect } from 'react';
import { 
  Paper, 
  Typography, 
  Grid, 
  TextField, 
  Button, 
  Box,
  Card,
  CardContent,
  CardActions,
  Divider,
  IconButton,
  Alert,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  InputAdornment,
  Chip
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  LocalHospital as SymptomsIcon,
  Medication as DosageIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import { evolucoesService, sintomasService, dosagensService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

// Componente TabPanel para exibir o conteúdo da aba selecionada
function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`evolution-tabpanel-${index}`}
      aria-labelledby={`evolution-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 0 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Função para criar propriedades de acessibilidade para as abas
function a11yProps(index) {
  return {
    id: `evolution-tab-${index}`,
    'aria-controls': `evolution-tabpanel-${index}`,
  };
}

const EvolutionManager = ({ patientId }) => {
  const { currentUser } = useAuth();
  const [evolutions, setEvolutions] = useState([]);
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Estado para o formulário de nova evolução
  const [newEvolution, setNewEvolution] = useState({
    nota_evolucao: '',
    data_evolucao: new Date().toISOString().split('T')[0]
  });
  
  // Estado para edição de evolução
  const [editMode, setEditMode] = useState(false);
  const [evolutionToEdit, setEvolutionToEdit] = useState(null);
  
  // Estado para diálogo de confirmação de exclusão
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [evolutionToDelete, setEvolutionToDelete] = useState(null);
  
  // Estado para busca
  const [searchTerm, setSearchTerm] = useState('');
  const [searching, setSearching] = useState(false);
  
  // Estados para registro rápido de sintomas
  const [showSymptomsForm, setShowSymptomsForm] = useState(false);
  const [standardSymptoms, setStandardSymptoms] = useState([]);
  const [customSymptoms, setCustomSymptoms] = useState([]);
  const [newSymptom, setNewSymptom] = useState({
    data: new Date().toISOString().split('T')[0],
    sintoma: '',
    intensidade: 5
  });
  
  // Estados para registro rápido de dosagens
  const [showDosageForm, setShowDosageForm] = useState(false);
  const [newDosage, setNewDosage] = useState({
    data: new Date().toISOString().split('T')[0],
    dosagem: '',
    gotas: 0,
    frequencia_diaria: 1,
    concentracao_cbd: 0,
    concentracao_thc: 0
  });
  

  
  // Carregar evoluções e sintomas padrão
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carregar evoluções e exames do paciente
        const evolutionsData = await evolucoesService.listar(patientId, searchTerm);
        setEvolutions(evolutionsData.evolucoes || []);
        setExams(evolutionsData.exames || []);
        
        // Carregar sintomas padrão para o formulário rápido
        const standardData = await sintomasService.listarPadrao();
        setStandardSymptoms(standardData.sintomas_padrao || []);
        setCustomSymptoms(standardData.sintomas_personalizados || []);
        
        setError('');
      } catch (err) {
        console.error('Erro ao carregar dados de evoluções:', err);
        setError('Não foi possível carregar as evoluções');
      } finally {
        setLoading(false);
        setSearching(false);
      }
    };
    
    if (patientId) {
      fetchData();
    }
  }, [patientId, searching]);
  
  // Manipulador de mudança no formulário
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    if (editMode) {
      setEvolutionToEdit(prev => ({
        ...prev,
        [name]: value
      }));
    } else {
      setNewEvolution(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };
  
  // Manipulador de mudança no campo de busca
  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };
  
  // Realizar busca
  const handleSearch = () => {
    setSearching(true);
  };
  
  // Limpar busca
  const handleClearSearch = () => {
    setSearchTerm('');
    setSearching(true);
  };
  
  // Realizar busca ao pressionar Enter
  const handleSearchKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };
  
  // Manipuladores para sintomas
  const handleSymptomInputChange = (e) => {
    const { name, value } = e.target;
    setNewSymptom(prev => ({
      ...prev,
      [name]: name === 'intensidade' ? parseInt(value) || 0 : value
    }));
  };
  
  const handleSymptomSubmit = async (e) => {
    e.preventDefault();
    
    if (!newSymptom.sintoma) {
      setError('Selecione um sintoma');
      return;
    }
    
    try {
      await sintomasService.criar({
        paciente_id: patientId,
        ...newSymptom
      });
      
      // Resetar formulário
      setNewSymptom({
        data: new Date().toISOString().split('T')[0],
        sintoma: '',
        intensidade: 5
      });
      
      setError('');
      alert('Sintoma registrado com sucesso!');
    } catch (err) {
      console.error('Erro ao registrar sintoma:', err);
      setError('Não foi possível registrar o sintoma');
    }
  };
  
  // Manipuladores para dosagens
  const handleDosageInputChange = (e) => {
    const { name, value } = e.target;
    
    let processedValue = value;
    if (['gotas', 'frequencia_diaria'].includes(name)) {
      processedValue = parseInt(value) || 0;
    } else if (['concentracao_cbd', 'concentracao_thc'].includes(name)) {
      processedValue = parseFloat(value) || 0;
    }
    
    setNewDosage(prev => ({
      ...prev,
      [name]: processedValue
    }));
  };
  
  const handleDosageSubmit = async (e) => {
    e.preventDefault();
    
    if (!newDosage.dosagem.trim()) {
      setError('Informe a descrição da dosagem');
      return;
    }
    
    try {
      await dosagensService.criar({
        paciente_id: patientId,
        ...newDosage
      });
      
      // Resetar formulário
      setNewDosage({
        data: new Date().toISOString().split('T')[0],
        dosagem: '',
        gotas: 0,
        frequencia_diaria: 1,
        concentracao_cbd: 0,
        concentracao_thc: 0
      });
      
      setError('');
      alert('Dosagem registrada com sucesso!');
    } catch (err) {
      console.error('Erro ao registrar dosagem:', err);
      setError('Não foi possível registrar a dosagem');
    }
  };
  
  
  // Registrar nova evolução
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (editMode) {
      // Atualizar evolução existente
      if (!evolutionToEdit.nota_evolucao.trim()) {
        setError('Informe a nota de evolução');
        return;
      }
      
      try {
        const response = await evolucoesService.atualizar(
          evolutionToEdit.id, 
          { nota_evolucao: evolutionToEdit.nota_evolucao }
        );
        
        // Atualizar evolução na lista
        const updatedEvolutions = evolutions.map(ev => 
          ev.id === evolutionToEdit.id ? response.evolucao : ev
        );
        
        setEvolutions(updatedEvolutions);
        
        // Sair do modo de edição
        setEditMode(false);
        setEvolutionToEdit(null);
        
        setError('');
      } catch (err) {
        console.error('Erro ao atualizar evolução:', err);
        setError('Não foi possível atualizar a evolução');
      }
    } else {
      // Criar nova evolução
      if (!newEvolution.nota_evolucao.trim()) {
        setError('Informe a nota de evolução');
        return;
      }
      
      try {
        const response = await evolucoesService.criar({
          paciente_id: patientId,
          ...newEvolution
        });
        
        // Adicionar nova evolução à lista
        setEvolutions([response.evolucao, ...evolutions]);
        
        // Resetar formulário
        setNewEvolution({
          nota_evolucao: '',
          data_evolucao: new Date().toISOString().split('T')[0]
        });
        
        setError('');
      } catch (err) {
        console.error('Erro ao registrar evolução:', err);
        setError('Não foi possível registrar a evolução');
      }
    }
  };
  
  // Iniciar edição de evolução
  const handleStartEdit = (evolution) => {
    setEvolutionToEdit(evolution);
    setEditMode(true);
  };
  
  // Cancelar edição
  const handleCancelEdit = () => {
    setEvolutionToEdit(null);
    setEditMode(false);
  };
  
  // Abrir diálogo de confirmação de exclusão
  const handleOpenDeleteDialog = (evolution) => {
    setEvolutionToDelete(evolution);
    setDeleteDialogOpen(true);
  };
  
  // Fechar diálogo de confirmação de exclusão
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setEvolutionToDelete(null);
  };
  
  // Excluir evolução
  const handleDeleteEvolution = async () => {
    if (!evolutionToDelete) return;
    
    try {
      await evolucoesService.excluir(evolutionToDelete.id);
      setEvolutions(evolutions.filter(e => e.id !== evolutionToDelete.id));
      handleCloseDeleteDialog();
    } catch (err) {
      console.error('Erro ao excluir evolução:', err);
      setError('Não foi possível excluir a evolução');
    }
  };
  
  
  // Combinar evoluções e exames em uma única lista ordenada por data
  const combinedItems = [
    ...evolutions.map(item => ({ ...item, type: 'evolution' })),
    ...exams.map(item => ({ ...item, type: 'exam' }))
  ].sort((a, b) => {
    const dateA = new Date(a.data_evolucao || a.data_exame);
    const dateB = new Date(b.data_evolucao || b.data_exame);
    return dateB - dateA;
  });

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Evoluções e Exames
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3 }}>
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
            {/* Campo de busca */}
            <Box sx={{ mb: 3 }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Buscar em evoluções e exames..."
                value={searchTerm}
                onChange={handleSearchChange}
                onKeyPress={handleSearchKeyPress}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                  endAdornment: searchTerm && (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="limpar busca"
                        onClick={handleClearSearch}
                        edge="end"
                      >
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  )
                }}
              />
              <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleSearch}
                  startIcon={<SearchIcon />}
                  disabled={loading}
                >
                  Buscar
                </Button>
              </Box>
            </Box>
            
            {/* Formulário para registrar nova evolução ou editar existente */}
            <Box component="form" onSubmit={handleSubmit} sx={{ mb: 4 }}>
              <Typography variant="subtitle1" gutterBottom>
                {editMode ? 'Editar Evolução' : 'Registrar Nova Evolução'}
              </Typography>
                    
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      name="data_evolucao"
                      label="Data"
                      type="date"
                      value={editMode ? 
                        (evolutionToEdit.data_evolucao ? evolutionToEdit.data_evolucao.split('T')[0] : new Date().toISOString().split('T')[0]) : 
                        newEvolution.data_evolucao}
                      onChange={handleInputChange}
                      fullWidth
                      required
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={9}>
                    <TextField
                      name="nota_evolucao"
                      label="Nota de Evolução"
                      value={editMode ? evolutionToEdit.nota_evolucao : newEvolution.nota_evolucao}
                      onChange={handleInputChange}
                      fullWidth
                      required
                      multiline
                      rows={4}
                      helperText="Digite informações sobre sintomas, dosagens e observações do paciente."
                    />
                  </Grid>
                  
                  <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      {editMode && (
                        <Button
                          variant="outlined"
                          color="secondary"
                          onClick={handleCancelEdit}
                        >
                          Cancelar
                        </Button>
                      )}
                      <Button
                        type="submit"
                        variant="contained"
                        color="primary"
                        startIcon={editMode ? <EditIcon /> : <AddIcon />}
                      >
                        {editMode ? 'Atualizar' : 'Registrar'}
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
              
              {/* Registro Rápido de Sintomas */}
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  mb: 3,
                  background: 'linear-gradient(135deg, #e8f5e8 0%, #f1f8e9 100%)',
                  border: '1px solid #4caf50'
                }}
              >
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    cursor: 'pointer',
                    mb: showSymptomsForm ? 2 : 0
                  }}
                  onClick={() => setShowSymptomsForm(!showSymptomsForm)}
                >
                  <SymptomsIcon sx={{ mr: 1, color: 'success.main' }} />
                  <Typography variant="h6" sx={{ flexGrow: 1, color: 'success.main', fontWeight: 'bold' }}>
                    📊 Registro Rápido de Sintomas
                  </Typography>
                  {showSymptomsForm ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </Box>
                
                {showSymptomsForm && (
                  <Box component="form" onSubmit={handleSymptomSubmit}>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} sm={3}>
                        <TextField
                          name="data"
                          label="Data"
                          type="date"
                          value={newSymptom.data}
                          onChange={handleSymptomInputChange}
                          fullWidth
                          size="small"
                          InputLabelProps={{ shrink: true }}
                        />
                      </Grid>
                      
                      <Grid item xs={12} sm={4}>
                        <TextField
                          name="sintoma"
                          label="Sintoma"
                          select
                          value={newSymptom.sintoma}
                          onChange={handleSymptomInputChange}
                          fullWidth
                          size="small"
                          SelectProps={{ native: true }}
                        >
                          <option value="">Selecione um sintoma</option>
                          {standardSymptoms.map((symptom) => (
                            <option key={symptom} value={symptom}>
                              {symptom}
                            </option>
                          ))}
                          {customSymptoms.map((symptom) => (
                            <option key={symptom} value={symptom}>
                              {symptom} (Personalizado)
                            </option>
                          ))}
                        </TextField>
                      </Grid>
                      
                      <Grid item xs={12} sm={3}>
                        <TextField
                          name="intensidade"
                          label="Intensidade (0-10)"
                          type="number"
                          value={newSymptom.intensidade}
                          onChange={handleSymptomInputChange}
                          fullWidth
                          size="small"
                          inputProps={{ min: 0, max: 10 }}
                        />
                      </Grid>
                      
                      <Grid item xs={12} sm={2}>
                        <Button
                          type="submit"
                          variant="contained"
                          color="success"
                          fullWidth
                          size="small"
                          startIcon={<AddIcon />}
                        >
                          Registrar
                        </Button>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </Paper>
              
              {/* Registro Rápido de Dosagens */}
              <Paper 
                elevation={2} 
                sx={{ 
                  p: 2, 
                  mb: 3,
                  background: 'linear-gradient(135deg, #e3f2fd 0%, #f1f8e9 100%)',
                  border: '1px solid #2196f3'
                }}
              >
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    cursor: 'pointer',
                    mb: showDosageForm ? 2 : 0
                  }}
                  onClick={() => setShowDosageForm(!showDosageForm)}
                >
                  <DosageIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6" sx={{ flexGrow: 1, color: 'primary.main', fontWeight: 'bold' }}>
                    💊 Registro Rápido de Dosagens
                  </Typography>
                  {showDosageForm ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                </Box>
                
                {showDosageForm && (
                  <Box component="form" onSubmit={handleDosageSubmit}>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} sm={2}>
                        <TextField
                          name="data"
                          label="Data"
                          type="date"
                          value={newDosage.data}
                          onChange={handleDosageInputChange}
                          fullWidth
                          size="small"
                          InputLabelProps={{ shrink: true }}
                        />
                      </Grid>
                      
                      <Grid item xs={12} sm={3}>
                        <TextField
                          name="dosagem"
                          label="Descrição"
                          value={newDosage.dosagem}
                          onChange={handleDosageInputChange}
                          fullWidth
                          size="small"
                          placeholder="Ex: Óleo CBD 10%"
                        />
                      </Grid>
                      
                      <Grid item xs={6} sm={1}>
                        <TextField
                          name="gotas"
                          label="Gotas"
                          type="number"
                          value={newDosage.gotas || ''}
                          onChange={handleDosageInputChange}
                          fullWidth
                          size="small"
                          inputProps={{ min: 1 }}
                        />
                      </Grid>
                      
                      <Grid item xs={6} sm={1}>
                        <TextField
                          name="frequencia_diaria"
                          label="Freq/dia"
                          type="number"
                          value={newDosage.frequencia_diaria}
                          onChange={handleDosageInputChange}
                          fullWidth
                          size="small"
                          inputProps={{ min: 1, max: 4 }}
                        />
                      </Grid>
                      
                      <Grid item xs={6} sm={2}>
                        <TextField
                          name="concentracao_cbd"
                          label="CBD (mg/ml)"
                          type="number"
                          value={newDosage.concentracao_cbd || ''}
                          onChange={handleDosageInputChange}
                          fullWidth
                          size="small"
                          inputProps={{ min: 0, step: 0.1 }}
                        />
                      </Grid>
                      
                      <Grid item xs={6} sm={2}>
                        <TextField
                          name="concentracao_thc"
                          label="THC (mg/ml)"
                          type="number"
                          value={newDosage.concentracao_thc || ''}
                          onChange={handleDosageInputChange}
                          fullWidth
                          size="small"
                          inputProps={{ min: 0, step: 0.1 }}
                        />
                      </Grid>
                      
                      <Grid item xs={12} sm={1}>
                        <Button
                          type="submit"
                          variant="contained"
                          color="primary"
                          fullWidth
                          size="small"
                          startIcon={<AddIcon />}
                        >
                          Registrar
                        </Button>
                      </Grid>
                    </Grid>
                  </Box>
                )}
              </Paper>
              
              {/* Lista combinada de evoluções e exames */}
              {combinedItems.length === 0 ? (
                <Alert severity="info">
                  Nenhum registro encontrado para este paciente.
                </Alert>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {combinedItems.map((item) => (
                    <Card key={`${item.type}-${item.id}`} variant="outlined">
                      <CardContent>
                        <Box sx={{ 
                          display: 'flex', 
                          justifyContent: 'space-between', 
                          alignItems: 'center',
                          mb: 1 
                        }}>
                          <Box>
                            <Typography variant="subtitle2" color="text.secondary">
                              {formatDate(item.data_evolucao || item.data_exame)}
                            </Typography>
                            <Chip 
                              label={item.type === 'evolution' ? 'Evolução' : 'Exame'} 
                              size="small"
                              color={item.type === 'evolution' ? 'primary' : 'secondary'}
                              sx={{ mt: 0.5 }}
                            />
                          </Box>
                          
                          <Typography variant="subtitle2" color="text.secondary">
                            {item.profissional_nome || 'Profissional não identificado'}
                          </Typography>
                        </Box>
                        
                        <Divider sx={{ mb: 2 }} />
                        
                        {item.type === 'evolution' ? (
                          <Typography variant="body1">
                            {item.nota_evolucao}
                          </Typography>
                        ) : (
                          <Box>
                            <Typography variant="subtitle1" gutterBottom>
                              {item.tipo_exame}
                            </Typography>
                            <Typography variant="body2">
                              <strong>Arquivo:</strong> {item.arquivo_nome}
                            </Typography>
                            {item.observacoes && (
                              <Typography variant="body2" sx={{ mt: 1 }}>
                                <strong>Observações:</strong> {item.observacoes}
                              </Typography>
                            )}
                          </Box>
                        )}
                      </CardContent>
                      
                      {/* Mostrar ações apenas para evoluções do usuário atual */}
                      {item.type === 'evolution' && currentUser && currentUser.id === item.profissional_id && (
                        <CardActions sx={{ justifyContent: 'flex-end' }}>
                          <IconButton 
                            size="small" 
                            color="primary"
                            onClick={() => handleStartEdit(item)}
                            title="Editar"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleOpenDeleteDialog(item)}
                            title="Excluir"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </CardActions>
                      )}
                    </Card>
                  ))}
                </Box>
              )}
            </>
          )}
      </Paper>
      
      {/* Diálogo de confirmação de exclusão */}
      <Dialog
          open={deleteDialogOpen}
          onClose={handleCloseDeleteDialog}
        >
          <DialogTitle>Confirmar exclusão</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Tem certeza que deseja excluir esta evolução? 
              Esta ação não pode ser desfeita.
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDeleteDialog} color="primary">
              Cancelar
            </Button>
            <Button onClick={handleDeleteEvolution} color="error" autoFocus>
              Excluir
            </Button>
          </DialogActions>
        </Dialog>
    </Box>
  );
};

// Função auxiliar para formatar data
function formatDate(dateString) {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
}

export default EvolutionManager;
