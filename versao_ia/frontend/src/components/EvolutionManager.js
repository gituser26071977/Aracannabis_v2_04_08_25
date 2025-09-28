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
  Chip,
  Tabs,
  Tab
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { evolucoesService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import ExameManager from './ExameManager';

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tabValue, setTabValue] = useState(0);
  
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
  

  // Manipulador de mudança de aba
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Carregar evoluções
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carregar evoluções do paciente
        const evolutionsData = await evolucoesService.listar(patientId, searchTerm);
        setEvolutions(evolutionsData.evolucoes || []);
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
  
  // Formatar data
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('pt-BR');
  };
  
  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom>
        Evoluções e Exames
      </Typography>
      
      {/* Abas */}
      <Paper elevation={3} sx={{ mb: 3 }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="Abas de evoluções e exames"
          variant="fullWidth"
        >
          <Tab label="Evoluções" {...a11yProps(0)} />
          <Tab label="Exames" {...a11yProps(1)} />
        </Tabs>
      </Paper>
      
      {/* Conteúdo das abas */}
      <TabPanel value={tabValue} index={0}>
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
                  placeholder="Buscar nas evoluções..."
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
              
              {/* Lista de evoluções */}
              {evolutions.length === 0 ? (
                <Alert severity="info">
                  Nenhuma evolução registrada para este paciente.
                </Alert>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {evolutions.map((evolution) => (
                    <Card key={evolution.id} variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="subtitle2" color="text.secondary">
                            {formatDate(evolution.data_evolucao)}
                          </Typography>
                          <Typography variant="subtitle2" color="text.secondary">
                            {evolution.profissional_nome || 'Profissional não identificado'}
                          </Typography>
                        </Box>
                        <Divider sx={{ mb: 2 }} />
                        <Typography variant="body1">
                          {evolution.nota_evolucao}
                        </Typography>
                      </CardContent>
                      
                      {/* Mostrar ações apenas se o usuário for o autor da evolução */}
                      {currentUser && currentUser.id === evolution.profissional_id && (
                        <CardActions sx={{ justifyContent: 'flex-end' }}>
                          <IconButton 
                            size="small" 
                            color="primary"
                            onClick={() => handleStartEdit(evolution)}
                            title="Editar"
                          >
                            <EditIcon />
                          </IconButton>
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => handleOpenDeleteDialog(evolution)}
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
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        <ExameManager pacienteId={patientId} />
      </TabPanel>
      
      
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

export default EvolutionManager;
