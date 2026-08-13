import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Button,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Breadcrumbs,
  Link as MuiLink,
} from '@mui/material';
import { useParams, Link, useNavigate } from 'react-router-dom';
import associationService from '../../services/associationService';
import { useAssociation } from '../../contexts/AssociationContext';

const MembersPage = () => {
  const { id: idParam } = useParams();
  const { currentAssociation } = useAssociation();
  const Navigate = useNavigate();
  // A rota /association/members não carrega :id; resolver a associação
  // ativa do contexto (currentAssociation) ou do localStorage.
  const id =
    idParam || currentAssociation?.id || localStorage.getItem('selectedAssociationId') || '';
  const [members, setMembers] = useState([]);
  const [association, setAssociation] = useState(null);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    cpf: '',
    nome: '',
    data_nascimento: '',
    rg: '',
    telefone: '',
    email: '',
    endereco: '',
    nome_responsavel: '',
    observacoes: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchData = async () => {
    try {
      const assocData = await associationService.getAssociationById(id);
      setAssociation(assocData);
      const membersData = await associationService.getMembers(id);
      setMembers(membersData);
    } catch (err) {
      setError('Erro ao carregar dados da associação ou membros.');
      if (process.env.NODE_ENV !== 'production') console.error(err);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleAddMember = async () => {
    try {
      if (!formData.cpf) {
        setError('CPF é obrigatório para vincular um membro.');
        return;
      }
      // O backend deve lidar com a busca de paciente_id pelo CPF usando o IntegrationService
      await associationService.addMember(id, formData);
      setSuccess('Membro adicionado com sucesso!');
      setOpen(false);
      setFormData({
        cpf: '',
        nome: '',
        data_nascimento: '',
        rg: '',
        telefone: '',
        email: '',
        endereco: '',
        nome_responsavel: '',
        observacoes: '',
      });
      fetchData();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Erro ao adicionar membro. Verifique se o CPF existe no sistema de pacientes.');
      if (process.env.NODE_ENV !== 'production') console.error(err);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
        <MuiLink component={Link} to="/association" color="inherit">
          Associações
        </MuiLink>
        <Typography color="text.primary">Membros</Typography>
      </Breadcrumbs>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Membros - {association ? association.nome : 'Carregando...'}
        </Typography>
        <Box>
          <Button variant="outlined" sx={{ mr: 2 }} onClick={() => Navigate('/association')}>
            Voltar
          </Button>
          <Button variant="contained" color="primary" onClick={() => setOpen(true)}>
            Novo Membro
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Nome (Paciente)</TableCell>
              <TableCell>CPF</TableCell>
              <TableCell>Data de Cadastro</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {members.map((member) => (
              <TableRow key={member.id}>
                <TableCell>{member.id}</TableCell>
                {/* Assumindo que o serializador do backend retorna detalhes do paciente ou pelo menos o nome via join se possível, 
                    ou se IntegrationService popula isso. Se não, mostrar apenas dados raw por enquanto. */}
                <TableCell>{member.paciente_nome || 'Não vinculado/Associado apenas'}</TableCell>
                <TableCell>{member.cpf}</TableCell>
                <TableCell>{new Date(member.data_filiacao).toLocaleDateString()}</TableCell>
                <TableCell>{member.status === 'ativo' ? 'Ativo' : 'Inativo'}</TableCell>
              </TableRow>
            ))}
            {members.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  Nenhum membro cadastrado nesta associação.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>Adicionar Membro</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Insira o CPF do paciente já cadastrado no sistema AraOS para vinculá-lo como membro
            desta associação.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            name="cpf"
            label="CPF do Paciente"
            type="text"
            fullWidth
            value={formData.cpf}
            onChange={handleChange}
            required
          />
          <TextField
            margin="dense"
            name="nome"
            label="Nome (opcional, será preenchido automaticamente se encontrado)"
            type="text"
            fullWidth
            value={formData.nome}
            onChange={handleChange}
            helperText="Deixe em branco para usar o nome do cadastro de pacientes"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} color="secondary">
            Cancelar
          </Button>
          <Button onClick={handleAddMember} color="primary">
            Adicionar
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MembersPage;
