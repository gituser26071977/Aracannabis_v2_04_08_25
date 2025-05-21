import React, { useState, useEffect } from 'react';
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
  Alert
} from '@mui/material';
import { 
  Edit as EditIcon, 
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { pacientesService } from '../services/api';

const PatientList = ({ onEdit, onView, onAdd, refreshTrigger }) => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [patientToDelete, setPatientToDelete] = useState(null);
  
  // Carregar pacientes
  useEffect(() => {
    const fetchPatients = async () => {
      setLoading(true);
      try {
        const data = await pacientesService.listar();
        setPatients(data.pacientes || []);
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
  
  // Formatar data
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
  };
  
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
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : patients.length === 0 ? (
        <Alert severity="info">
          Nenhum paciente cadastrado. Clique em "Novo Paciente" para adicionar.
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
                  <TableCell align="center">Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {patients
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((patient) => (
                    <TableRow key={patient.id}>
                      <TableCell>{patient.nome}</TableCell>
                      <TableCell>{formatDate(patient.data_nascimento)}</TableCell>
                      <TableCell>{patient.cpf}</TableCell>
                      <TableCell>{patient.telefone}</TableCell>
                      <TableCell>{patient.diagnostico}</TableCell>
                      <TableCell align="center">
                        <IconButton 
                          color="primary" 
                          onClick={() => onView(patient)}
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
            count={patients.length}
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
    </Paper>
  );
};

export default PatientList;
