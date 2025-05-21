import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  InputAdornment
} from '@mui/material';
import { 
  Search as SearchIcon,
  FilterList as FilterIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

const ActivityLogs = ({ profissionalId }) => {
  const [logs, setLogs] = useState([]);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Simulação de dados para demonstração
  useEffect(() => {
    const fetchLogs = async () => {
      setLoading(true);
      try {
        // Aqui seria feita a chamada à API para buscar os logs
        // const response = await api.get(`/evolucoes/logs?limite=${rowsPerPage}`);
        // setLogs(response.data.logs);
        
        // Dados simulados para demonstração
        const mockLogs = [
          { id: 1, data_hora: new Date(), profissional: 'Dr. João Silva', acao: 'Acesso', detalhes: 'Paciente ID #2 - Maria Oliveira' },
          { id: 2, data_hora: new Date(Date.now() - 3600000), profissional: 'Anderson B. Holzwarth', acao: 'Cadastro', detalhes: 'Novo paciente ID #1 - João Silva' },
          { id: 3, data_hora: new Date(Date.now() - 7200000), profissional: 'Dra. Ana Ferreira', acao: 'Atualização', detalhes: 'Paciente ID #2 - Ajuste de dosagem' },
          { id: 4, data_hora: new Date(Date.now() - 86400000), profissional: 'Dr. João Silva', acao: 'Registro', detalhes: 'Novo sintoma: Ansiedade - Paciente ID #1' },
          { id: 5, data_hora: new Date(Date.now() - 172800000), profissional: 'Dra. Ana Ferreira', acao: 'Consulta', detalhes: 'Listagem de pacientes' },
        ];
        
        setLogs(mockLogs);
      } catch (error) {
        console.error('Erro ao buscar logs:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchLogs();
  }, [rowsPerPage]);
  
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
    setPage(0);
  };
  
  // Filtrar logs com base no termo de pesquisa
  const filteredLogs = logs.filter(log => 
    log.profissional.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.acao.toLowerCase().includes(searchTerm.toLowerCase()) ||
    log.detalhes.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Obter logs para a página atual
  const currentLogs = filteredLogs.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );
  
  // Função para formatar data e hora
  const formatDateTime = (date) => {
    return format(new Date(date), "dd/MM/yyyy HH:mm:ss", { locale: ptBR });
  };
  
  // Função para obter cor do chip com base na ação
  const getActionColor = (action) => {
    const colors = {
      'Acesso': 'info',
      'Cadastro': 'success',
      'Atualização': 'warning',
      'Exclusão': 'error',
      'Registro': 'success',
      'Consulta': 'info'
    };
    
    return colors[action] || 'default';
  };
  
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Typography variant="h5" component="h1" color="primary" gutterBottom fontWeight="bold">
          Registro de Atividades (Logs de Auditoria)
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          Este registro mantém o histórico de todas as operações realizadas no sistema, em conformidade com a LGPD (Lei 13.709/2018).
        </Typography>
        
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
          <TextField
            variant="outlined"
            size="small"
            placeholder="Pesquisar logs..."
            value={searchTerm}
            onChange={handleSearchChange}
            sx={{ minWidth: 300 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            }}
          />
          
          <Tooltip title="Filtros avançados">
            <IconButton sx={{ ml: 1 }}>
              <FilterIcon />
            </IconButton>
          </Tooltip>
        </Box>
        
        <TableContainer>
          <Table sx={{ minWidth: 650 }} aria-label="tabela de logs">
            <TableHead>
              <TableRow>
                <TableCell>Data/Hora</TableCell>
                <TableCell>Usuário</TableCell>
                <TableCell>Ação</TableCell>
                <TableCell>Detalhes</TableCell>
                <TableCell align="right">Opções</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">Carregando...</TableCell>
                </TableRow>
              ) : currentLogs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">Nenhum registro encontrado</TableCell>
                </TableRow>
              ) : (
                currentLogs.map((log) => (
                  <TableRow key={log.id} hover>
                    <TableCell>{formatDateTime(log.data_hora)}</TableCell>
                    <TableCell>{log.profissional}</TableCell>
                    <TableCell>
                      <Chip 
                        label={log.acao} 
                        size="small" 
                        color={getActionColor(log.acao)}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>{log.detalhes}</TableCell>
                    <TableCell align="right">
                      <Tooltip title="Ver detalhes">
                        <IconButton size="small">
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredLogs.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Linhas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
      
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

export default ActivityLogs;
