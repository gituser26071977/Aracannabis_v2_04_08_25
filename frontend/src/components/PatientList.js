import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  TablePagination,
  IconButton,
  Typography,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
  Chip,
  Grid
} from '@mui/material';
import { 
  Edit as EditIcon, 
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Add as AddIcon,
  Search as SearchIcon,
  Clear as ClearIcon,
  People as PeopleIcon,
  Share as ShareIcon,
  AccountCircle as ResponsavelIcon,
  Group as CompartilhadoIcon
} from '@mui/icons-material';
import { pacientesService } from '../services/api';
import CompartilhamentoPaciente from './CompartilhamentoPaciente';

const PatientList = ({ onEdit, onAdd, refreshTrigger }) => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [filteredPatients, setFilteredPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [patientToDelete, setPatientToDelete] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [compartilhamentoDialogOpen, setCompartilhamentoDialogOpen] = useState(false);
  const [pacienteParaCompartilhar, setPacienteParaCompartilhar] = useState(null);
  
  // Carregar pacientes
  useEffect(() => {
    const fetchPatients = async () => {
      setLoading(true);
      try {
        const data = await pacientesService.listar();
        setPatients(data.pacientes || []);
        setFilteredPatients(data.pacientes || []);
        setError('');
      } catch (err) {
        console.error('Erro ao carregar pacientes:', err);
        setError('Não foi possível carregar a lista de pacientes');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPatients();
  }, [refreshTrigger]);

  // Filtrar pacientes baseado no termo de busca
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredPatients(patients);
    } else {
      const filtered = patients.filter(patient => 
        patient.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.cpf.includes(searchTerm) ||
        patient.telefone.includes(searchTerm) ||
        (patient.diagnostico && patient.diagnostico.toLowerCase().includes(searchTerm.toLowerCase()))
      );
      setFilteredPatients(filtered);
    }
    setPage(0); // Reset para primeira página ao buscar
  }, [searchTerm, patients]);

  // Manipular busca
  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };

  const handleClearSearch = () => {
    setSearchTerm('');
  };
  
  // Paginação
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // Diálogo de confirmação de exclusão
  const handleOpenDeleteDialog = (patient) => {
    setPatientToDelete(patient);
    setDeleteDialogOpen(true);
  };
  
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setPatientToDelete(null);
  };
  
  // Excluir paciente
  const handleDeletePatient = async () => {
    if (!patientToDelete) return;
    
    try {
      await pacientesService.excluir(patientToDelete.id);
      setPatients(patients.filter(p => p.id !== patientToDelete.id));
      handleCloseDeleteDialog();
    } catch (err) {
      console.error('Erro ao excluir paciente:', err);
      setError('Não foi possível excluir o paciente');
    }
  };

  // Compartilhamento
  const handleOpenCompartilhamento = (patient) => {
    setPacienteParaCompartilhar(patient);
    setCompartilhamentoDialogOpen(true);
  };

  const handleCloseCompartilhamento = () => {
    setCompartilhamentoDialogOpen(false);
    setPacienteParaCompartilhar(null);
  };

  const handleCompartilhamentoAtualizado = () => {
    // Recarregar lista de pacientes para atualizar informações de compartilhamento
    const fetchPatients = async () => {
      try {
        const data = await pacientesService.listar();
        setPatients(data.pacientes || []);
        setFilteredPatients(data.pacientes || []);
      } catch (err) {
        console.error('Erro ao recarregar pacientes:', err);
      }
    };
    fetchPatients();
  };
  
  // Formatar data
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };

  // Calcular estatísticas dos pacientes
  const patientsInTreatment = patients.filter(patient => patient.em_tratamento).length;
  const totalPatients = patients.length;
  
  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Pacientes</Typography>
        <Button 
          variant="contained" 
          color="primary" 
          startIcon={<AddIcon />}
          onClick={onAdd}
        >
          Novo Paciente
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {/* Contador de pacientes e campo de busca */}
      {!loading && patients.length > 0 && (
        <>
          {/* Estatísticas dos pacientes */}
          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Chip
                icon={<PeopleIcon />}
                label={`Total: ${totalPatients} pacientes`}
                color="primary"
                variant="outlined"
                sx={{ width: '100%', justifyContent: 'flex-start' }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Chip
                icon={<PeopleIcon />}
                label={`Em tratamento: ${patientsInTreatment}`}
                color="success"
                variant="outlined"
                sx={{ width: '100%', justifyContent: 'flex-start' }}
              />
            </Grid>
          </Grid>

          {/* Campo de busca */}
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Buscar por nome, CPF, telefone ou diagnóstico..."
              value={searchTerm}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
                endAdornment: searchTerm && (
                  <InputAdornment position="end">
                    <IconButton onClick={handleClearSearch} edge="end">
                      <ClearIcon />
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : patients.length === 0 ? (
        <Alert severity="info">
          Nenhum paciente cadastrado. Clique em "Novo Paciente" para adicionar.
        </Alert>
      ) : filteredPatients.length === 0 ? (
        <Alert severity="info">
          Nenhum paciente encontrado com os critérios de busca.
        </Alert>
      ) : (
        <>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Nome</TableCell>
                  <TableCell>Data de Nascimento</TableCell>
                  <TableCell>CPF</TableCell>
                  <TableCell>Telefone</TableCell>
                  <TableCell>Diagnóstico</TableCell>
                  <TableCell align="center">Acesso</TableCell>
                  <TableCell align="center">Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPatients
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((patient) => (
                    <TableRow key={patient.id}>
                      <TableCell>{patient.nome}</TableCell>
                      <TableCell>{formatDate(patient.data_nascimento)}</TableCell>
                      <TableCell>{patient.cpf}</TableCell>
                      <TableCell>{patient.telefone}</TableCell>
                      <TableCell>{patient.diagnostico}</TableCell>
                      <TableCell align="center">
                        {patient.eh_responsavel ? (
                          <Chip
                            icon={<ResponsavelIcon />}
                            label="Responsável"
                            color="primary"
                            size="small"
                          />
                        ) : (
                          <Chip
                            icon={<CompartilhadoIcon />}
                            label={patient.nivel_acesso === 'leitura' ? 'Leitura' : 
                                   patient.nivel_acesso === 'escrita' ? 'Escrita' : 'Completo'}
                            color="secondary"
                            size="small"
                          />
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <IconButton 
                          color="primary" 
                          onClick={() => navigate(`/pacientes/detail/${patient.id}`)}
                          title="Visualizar"
                        >
                          <ViewIcon />
                        </IconButton>
                        <IconButton 
                          color="secondary" 
                          onClick={() => onEdit(patient)}
                          title="Editar"
                        >
                          <EditIcon />
                        </IconButton>
                        {patient.eh_responsavel && (
                          <IconButton 
                            color="info" 
                            onClick={() => handleOpenCompartilhamento(patient)}
                            title="Compartilhar"
                          >
                            <ShareIcon />
                          </IconButton>
                        )}
                        <IconButton 
                          color="error" 
                          onClick={() => handleOpenDeleteDialog(patient)}
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
          
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={filteredPatients.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            labelRowsPerPage="Linhas por página:"
            labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
          />
        </>
      )}
      
      {/* Diálogo de confirmação de exclusão */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
      >
        <DialogTitle>Confirmar exclusão</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Tem certeza que deseja excluir o paciente {patientToDelete?.nome}? 
            Esta ação não pode ser desfeita.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog} color="primary">
            Cancelar
          </Button>
          <Button onClick={handleDeletePatient} color="error" autoFocus>
            Excluir
          </Button>
        </DialogActions>
      </Dialog>

      {/* Diálogo de compartilhamento */}
      {pacienteParaCompartilhar && (
        <CompartilhamentoPaciente
          open={compartilhamentoDialogOpen}
          onClose={handleCloseCompartilhamento}
          pacienteId={pacienteParaCompartilhar.id}
          pacienteNome={pacienteParaCompartilhar.nome}
          ehResponsavel={pacienteParaCompartilhar.eh_responsavel}
          onCompartilhamentoAtualizado={handleCompartilhamentoAtualizado}
        />
      )}
    </Paper>
  );
};

export default PatientList;
