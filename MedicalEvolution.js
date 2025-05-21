import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Card,
  CardContent,
  CardActions,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  NoteAdd as NoteAddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Person as PersonIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  History as HistoryIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const MedicalEvolution = ({ pacienteId, pacienteNome }) => {
  const [evolucoes, setEvolucoes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [deleteId, setDeleteId] = useState(null);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [evolucaoText, setEvolucaoText] = useState('');

  // Buscar evoluções do paciente
  useEffect(() => {
    const fetchEvolucoes = async () => {
      setLoading(true);
      setError('');
      
      try {
        // Aqui seria feita a chamada à API para buscar as evoluções
        // const response = await evolucaoService.listarEvolucoes(pacienteId);
        // setEvolucoes(response.data.evolucoes);
        
        // Dados simulados para demonstração
        const mockEvolucoes = [
          {
            id: 1,
            paciente_id: pacienteId,
            profissional_id: 1,
            profissional_nome: 'Dr. João Silva',
            data_evolucao: new Date(),
            nota_evolucao: 'Paciente relata melhora significativa na qualidade do sono após ajuste na dosagem. Mantém queixa de ansiedade leve durante o dia, mas com intensidade reduzida. Recomendado manter dosagem atual e reavaliar em 15 dias.'
          },
          {
            id: 2,
            paciente_id: pacienteId,
            profissional_id: 2,
            profissional_nome: 'Dra. Ana Ferreira',
            data_evolucao: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000), // 15 dias atrás
            nota_evolucao: 'Primeira consulta após início do tratamento. Paciente relata melhora parcial dos sintomas de ansiedade, mas ainda com dificuldades para dormir. Ajustada dosagem para 15 gotas 2x ao dia. Solicitados exames complementares para próxima consulta.'
          },
          {
            id: 3,
            paciente_id: pacienteId,
            profissional_id: 1,
            profissional_nome: 'Dr. João Silva',
            data_evolucao: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 dias atrás
            nota_evolucao: 'Consulta inicial. Paciente apresenta quadro de ansiedade generalizada e insônia. Iniciado tratamento com CBD 20mg/ml, 10 gotas 2x ao dia. Orientado sobre possíveis efeitos colaterais e necessidade de acompanhamento regular.'
          }
        ];
        
        setEvolucoes(mockEvolucoes);
      } catch (err) {
        console.error('Erro ao buscar evoluções:', err);
        setError('Não foi possível carregar as evoluções médicas.');
      } finally {
        setLoading(false);
      }
    };
    
    if (pacienteId) {
      fetchEvolucoes();
    }
  }, [pacienteId]);

  // Abrir diálogo para nova evolução
  const handleOpenDialog = () => {
    setEditingId(null);
    setEvolucaoText('');
    setOpenDialog(true);
  };

  // Abrir diálogo para editar evolução
  const handleEditEvolucao = (evolucao) => {
    setEditingId(evolucao.id);
    setEvolucaoText(evolucao.nota_evolucao);
    setOpenDialog(true);
  };

  // Fechar diálogo
  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingId(null);
    setEvolucaoText('');
  };

  // Abrir confirmação de exclusão
  const handleConfirmDelete = (id) => {
    setDeleteId(id);
    setConfirmDeleteOpen(true);
  };

  // Fechar confirmação de exclusão
  const handleCloseConfirmDelete = () => {
    setConfirmDeleteOpen(false);
    setDeleteId(null);
  };

  // Salvar evolução (nova ou editada)
  const handleSaveEvolucao = async () => {
    if (!evolucaoText.trim()) {
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      if (editingId) {
        // Editar evolução existente
        // await evolucaoService.atualizarEvolucao(editingId, { nota_evolucao: evolucaoText });
        
        // Simulação para demonstração
        setEvolucoes(evolucoes.map(ev => 
          ev.id === editingId 
            ? { ...ev, nota_evolucao: evolucaoText, data_evolucao: new Date() } 
            : ev
        ));
      } else {
        // Criar nova evolução
        // const response = await evolucaoService.registrarEvolucao(pacienteId, { nota_evolucao: evolucaoText });
        
        // Simulação para demonstração
        const novaEvolucao = {
          id: Date.now(), // ID temporário
          paciente_id: pacienteId,
          profissional_id: 1,
          profissional_nome: 'Dr. João Silva', // Usuário atual simulado
          data_evolucao: new Date(),
          nota_evolucao: evolucaoText
        };
        
        setEvolucoes([novaEvolucao, ...evolucoes]);
      }
      
      handleCloseDialog();
    } catch (err) {
      console.error('Erro ao salvar evolução:', err);
      setError('Não foi possível salvar a evolução médica.');
    } finally {
      setLoading(false);
    }
  };

  // Excluir evolução
  const handleDeleteEvolucao = async () => {
    if (!deleteId) return;
    
    setLoading(true);
    setError('');
    
    try {
      // await evolucaoService.excluirEvolucao(deleteId);
      
      // Simulação para demonstração
      setEvolucoes(evolucoes.filter(ev => ev.id !== deleteId));
      
      handleCloseConfirmDelete();
    } catch (err) {
      console.error('Erro ao excluir evolução:', err);
      setError('Não foi possível excluir a evolução médica.');
    } finally {
      setLoading(false);
    }
  };

  // Formatar data
  const formatDate = (date) => {
    return format(new Date(date), "dd 'de' MMMM 'de' yyyy 'às' HH:mm", { locale: ptBR });
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h1" color="primary" fontWeight="bold">
            Evolução Médica - {pacienteNome || `Paciente #${pacienteId}`}
          </Typography>
          
          <Button 
            variant="contained" 
            color="primary" 
            startIcon={<NoteAddIcon />}
            onClick={handleOpenDialog}
          >
            Nova Evolução
          </Button>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {loading && !openDialog ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : evolucoes.length === 0 ? (
          <Card sx={{ bgcolor: '#f5f5f5', borderRadius: 2, mb: 3 }}>
            <CardContent>
              <Typography variant="h6" color="text.secondary" align="center">
                Nenhuma evolução médica registrada
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                Clique em "Nova Evolução" para adicionar a primeira evolução médica para este paciente.
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <List sx={{ width: '100%' }}>
            {evolucoes.map((evolucao, index) => (
              <React.Fragment key={evolucao.id}>
                {index > 0 && <Divider variant="inset" component="li" />}
                <ListItem 
                  alignItems="flex-start"
                  secondaryAction={
                    <Box>
                      <IconButton 
                        edge="end" 
                        aria-label="editar"
                        onClick={() => handleEditEvolucao(evolucao)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton 
                        edge="end" 
                        aria-label="excluir"
                        onClick={() => handleConfirmDelete(evolucao.id)}
                        sx={{ ml: 1 }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  }
                >
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      <PersonIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography variant="subtitle1" color="primary" component="span">
                          {evolucao.profissional_nome}
                        </Typography>
                        <Chip 
                          icon={<HistoryIcon fontSize="small" />}
                          label={formatDate(evolucao.data_evolucao)}
                          size="small"
                          variant="outlined"
                          sx={{ ml: 2 }}
                        />
                      </Box>
                    }
                    secondary={
                      <Typography
                        sx={{ display: 'inline', whiteSpace: 'pre-line' }}
                        component="span"
                        variant="body2"
                        color="text.primary"
                      >
                        {evolucao.nota_evolucao}
                      </Typography>
                    }
                  />
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>
      
      {/* Diálogo para adicionar/editar evolução */}
      <Dialog open={openDialog} onClose={handleCloseDialog} fullWidth maxWidth="md">
        <DialogTitle>
          {editingId ? 'Editar Evolução Médica' : 'Nova Evolução Médica'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ mb: 2 }}>
            Registre suas observações clínicas, avaliações e recomendações para o tratamento do paciente.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="evolucao"
            label="Evolução Médica"
            type="text"
            fullWidth
            multiline
            rows={8}
            variant="outlined"
            value={evolucaoText}
            onChange={(e) => setEvolucaoText(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} startIcon={<CancelIcon />} color="inherit">
            Cancelar
          </Button>
          <Button 
            onClick={handleSaveEvolucao} 
            startIcon={<SaveIcon />} 
            variant="contained" 
            color="primary"
            disabled={!evolucaoText.trim()}
          >
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Diálogo de confirmação de exclusão */}
      <Dialog
        open={confirmDeleteOpen}
        onClose={handleCloseConfirmDelete}
      >
        <DialogTitle>
          Confirmar Exclusão
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Tem certeza que deseja excluir esta evolução médica? Esta ação não pode ser desfeita.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseConfirmDelete} color="inherit">
            Cancelar
          </Button>
          <Button onClick={handleDeleteEvolucao} color="error" variant="contained">
            Excluir
          </Button>
        </DialogActions>
      </Dialog>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Aracannabis © {new Date().getFullYear()} - Sistema de Controle de Pacientes
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Dados protegidos conforme LGPD (Lei 13.709/2018)
        </Typography>
      </Box>
    </Container>
  );
};

export default MedicalEvolution;
