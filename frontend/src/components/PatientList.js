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
  FormControl,
  Select,
  MenuItem,
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
  Group as CompartilhadoIcon,
} from '@mui/icons-material';
import { Avatar, Fab } from '@mui/material';
import { pacientesService } from '../services/api';
import CompartilhamentoPaciente from './CompartilhamentoPaciente';
import { useAuth } from '../contexts/AuthContext';
import EmptyState from './EmptyState';
import useConfirm from '../hooks/useConfirm';

const PatientList = ({ onEdit, onAdd, refreshTrigger }) => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();
  const { confirm, ConfirmDialog } = useConfirm();
  const [patients, setPatients] = useState([]);
  const [filteredPatients, setFilteredPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [compartilhamentoDialogOpen, setCompartilhamentoDialogOpen] = useState(false);
  const [pacienteParaCompartilhar, setPacienteParaCompartilhar] = useState(null);
  const [upgradeDialogOpen, setUpgradeDialogOpen] = useState(false);

  // Calcular idade a partir da data de nascimento
  const calcularIdade = (dataNascimento) => {
    if (!dataNascimento) return '';
    const hoje = new Date();
    const nascimento = new Date(dataNascimento);
    let idade = hoje.getFullYear() - nascimento.getFullYear();
    const mes = hoje.getMonth() - nascimento.getMonth();

    if (mes < 0 || (mes === 0 && hoje.getDate() < nascimento.getDate())) {
      idade--;
    }

    return `${idade} anos`;
  };

  // Função para obter URL da foto do paciente
  const getFotoUrl = (patient) => {
    if (patient.foto_nome) {
      return `${process.env.REACT_APP_API_URL}/pacientes/foto/${patient.foto_nome}`;
    }
    return null;
  };

  // Filtros
  const [filterPeriodo, setFilterPeriodo] = useState('');
  const [filterAssociacao, setFilterAssociacao] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Carregar pacientes com filtros
  useEffect(() => {
    const fetchPatients = async () => {
      setLoading(true);
      try {
        const filtros = {};
        if (searchTerm) filtros.nome = searchTerm;
        if (filterAssociacao) filtros.associacao = filterAssociacao;
        if (filterPeriodo) filtros.periodo_cadastro = filterPeriodo;

        const data = await pacientesService.listar(filtros);
        setPatients(data.pacientes || []);
        setFilteredPatients(data.pacientes || []); // Agora o backend filtra
        setError('');
      } catch (err) {
        if (process.env.NODE_ENV !== 'production')
          console.error('Erro ao carregar pacientes:', err);
        setError('Não foi possível carregar a lista de pacientes');
      } finally {
        setLoading(false);
      }
    };

    // Debounce na busca por nome para evitar muitas chamadas
    const timeoutId = setTimeout(() => {
      fetchPatients();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [refreshTrigger, filterPeriodo, filterAssociacao, searchTerm]);

  // Remover client-side effect de busca já que agora é server-side
  // useEffect(() => { ... }, [searchTerm, patients]); excluido.

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

  // Excluir paciente (com confirmação via useConfirm)
  const handleDeletePatient = async (patient) => {
    const ok = await confirm({
      title: `Excluir ${patient.nome}?`,
      message:
        'Esta ação não pode ser desfeita. Todos os dados do prontuário, consultas e histórico serão removidos permanentemente.',
      confirmLabel: 'Excluir permanentemente',
      destructive: true,
    });
    if (!ok) return;

    try {
      await pacientesService.excluir(patient.id);
      setPatients(patients.filter((p) => p.id !== patient.id));
    } catch (err) {
      if (process.env.NODE_ENV !== 'production') console.error('Erro ao excluir paciente:', err);
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
        if (process.env.NODE_ENV !== 'production')
          console.error('Erro ao recarregar pacientes:', err);
      }
    };
    fetchPatients();
  };

  // Calcular estatísticas dos pacientes

  return (
    <Paper elevation={3} sx={{ p: 2, position: 'relative' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Pacientes</Typography>
      </Box>

      <Fab
        color="primary"
        aria-label="Novo paciente"
        onClick={() => {
          const exp = currentUser?.data_expiracao ? new Date(currentUser.data_expiracao) : null;
          if (currentUser?.role !== 'admin' && exp && exp < new Date()) {
            setUpgradeDialogOpen(true);
          } else {
            onAdd();
          }
        }}
        sx={{ position: 'absolute', top: 16, right: 16 }}
      >
        <AddIcon />
      </Fab>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Contador de pacientes e campo de busca */}
      {!loading && patients.length > 0 && (
        <Box sx={{ mb: 2, display: 'flex', gap: 1.5, alignItems: 'center' }}>
          <TextField
            size="small"
            sx={{ flexGrow: 1 }}
            variant="outlined"
            placeholder="Buscar por nome ou associação..."
            value={searchTerm}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
              endAdornment: searchTerm && (
                <InputAdornment position="end">
                  <IconButton onClick={handleClearSearch} edge="end" size="small">
                    <ClearIcon fontSize="small" />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <Select
              value={filterPeriodo}
              displayEmpty
              onChange={(e) => setFilterPeriodo(e.target.value)}
              inputProps={{ 'aria-label': 'Período de cadastro' }}
            >
              <MenuItem value="">Todos os períodos</MenuItem>
              <MenuItem value="hoje">Hoje</MenuItem>
              <MenuItem value="ontem">Ontem</MenuItem>
              <MenuItem value="7dias">Últimos 7 dias</MenuItem>
              <MenuItem value="30dias">Últimos 30 dias</MenuItem>
              <MenuItem value="mes_atual">Mês Atual</MenuItem>
            </Select>
          </FormControl>
        </Box>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : patients.length === 0 ? (
        <EmptyState
          icon={<PeopleIcon sx={{ fontSize: 72 }} />}
          title="Nenhum paciente cadastrado"
          description="Comece adicionando seu primeiro paciente para gerenciar consultas, prescrições e prontuários."
          actionLabel="Cadastrar paciente"
          onAction={onAdd}
        />
      ) : filteredPatients.length === 0 ? (
        <EmptyState
          icon={<SearchIcon sx={{ fontSize: 72 }} />}
          title="Nenhum resultado encontrado"
          description="Nenhum paciente corresponde aos critérios de busca atuais. Tente ajustar os filtros."
          actionLabel="Limpar busca"
          onAction={() => {
            setSearchTerm('');
            setFilterPeriodo('');
            setFilterAssociacao('');
          }}
        />
      ) : (
        <>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Nome</TableCell>
                  <TableCell>Idade</TableCell>
                  <TableCell>Diagnóstico</TableCell>
                  <TableCell>Associação</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell align="center">Acesso</TableCell>
                  <TableCell align="center">Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPatients
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((patient) => (
                    <TableRow key={patient.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Avatar src={getFotoUrl(patient)} sx={{ width: 36, height: 36 }}>
                            {!getFotoUrl(patient) && patient.nome.charAt(0).toUpperCase()}
                          </Avatar>
                          <Typography variant="body2">{patient.nome}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{calcularIdade(patient.data_nascimento)}</TableCell>
                      <TableCell>{patient.diagnostico}</TableCell>
                      <TableCell>{patient.associacao || '-'}</TableCell>
                      <TableCell align="center">
                        <Box
                          sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 0.5,
                            alignItems: 'center',
                          }}
                        >
                          {patient.em_tratamento ? (
                            <Chip
                              label="Em tratamento"
                              color="success"
                              variant="outlined"
                              size="small"
                            />
                          ) : (
                            <Chip label="Inativo" color="default" variant="outlined" size="small" />
                          )}
                          {patient.tdah_positivo && (
                            <Chip
                              label="TDAH"
                              color="warning"
                              variant="filled"
                              size="small"
                              sx={{ fontWeight: 'bold' }}
                            />
                          )}
                        </Box>
                      </TableCell>
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
                            label={
                              patient.nivel_acesso === 'leitura'
                                ? 'Leitura'
                                : patient.nivel_acesso === 'escrita'
                                  ? 'Escrita'
                                  : 'Completo'
                            }
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
                          size="medium"
                        >
                          <ViewIcon fontSize="medium" />
                        </IconButton>
                        <IconButton
                          color="secondary"
                          onClick={() => onEdit(patient)}
                          title="Editar"
                          size="medium"
                        >
                          <EditIcon fontSize="medium" />
                        </IconButton>
                        {patient.eh_responsavel && (
                          <IconButton
                            color="info"
                            onClick={() => handleOpenCompartilhamento(patient)}
                            title="Compartilhar"
                            size="medium"
                          >
                            <ShareIcon fontSize="medium" />
                          </IconButton>
                        )}
                        <IconButton
                          color="error"
                          onClick={() => handleDeletePatient(patient)}
                          title="Excluir"
                          size="medium"
                        >
                          <DeleteIcon fontSize="medium" />
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
            sx={{
              '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows, & .MuiTablePagination-select':
                { fontSize: '1.1rem' },
            }}
          />
        </>
      )}

      {/* Diálogo de confirmação de exclusão via useConfirm */}

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

      {/* Modal de Paywall / Upgrade */}
      <Dialog
        open={upgradeDialogOpen}
        onClose={() => setUpgradeDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          Plano Expirado ou Perfil Avulso
        </DialogTitle>
        <DialogContent>
          <DialogContentText sx={{ fontSize: '1.1rem', mt: 1 }}>
            Sua assinatura atual não permite o cadastro de{' '}
            <strong>novos pacientes como titular</strong>. Isso ocorre porque seu período de
            avaliação expirou ou você é um profissional de equipe colaborativa.
          </DialogContentText>
          <DialogContentText sx={{ fontSize: '1.1rem', mt: 2 }}>
            Para ser o responsável clínico (cadastrar, gerenciar faturamento e manter os prontuários
            seguros), é necessário ativar um plano.
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button onClick={() => setUpgradeDialogOpen(false)} color="inherit">
            Entendi
          </Button>
          <Button
            onClick={() => navigate('/planos')}
            color="primary"
            variant="contained"
            size="large"
          >
            Ver Planos de Assinatura
          </Button>
        </DialogActions>
      </Dialog>
      <ConfirmDialog />
    </Paper>
  );
};

export default PatientList;
