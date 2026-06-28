import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Box,
  Chip,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Share as ShareIcon,
  Delete as DeleteIcon,
  Person as PersonIcon
} from '@mui/icons-material';
import { pacientesService } from '../services/api';
import useConfirm from '../hooks/useConfirm';

const CompartilhamentoPaciente = ({
  open,
  onClose,
  pacienteId,
  pacienteNome,
  ehResponsavel,
  onCompartilhamentoAtualizado,
}) => {
  const { confirm, ConfirmDialog } = useConfirm();
  const [profissionais, setProfissionais] = useState([]);
  const [compartilhamentos, setCompartilhamentos] = useState([]);
  const [profissionalSelecionado, setProfissionalSelecionado] = useState('');
  const [nivelAcesso, setNivelAcesso] = useState('leitura');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (open && ehResponsavel) {
      carregarDados();
    }
  }, [open, ehResponsavel, pacienteId]);

  const carregarDados = async () => {
    setLoading(true);
    try {
      // Carregar profissionais disponíveis
      const profissionaisData = await pacientesService.listarProfissionais();
      setProfissionais(profissionaisData.profissionais || []);

      // Carregar compartilhamentos existentes
      const compartilhamentosData = await pacientesService.listarCompartilhamentos(pacienteId);
      setCompartilhamentos(compartilhamentosData.compartilhamentos || []);
    } catch (err) {
      setError('Erro ao carregar dados: ' + (err.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCompartilhar = async () => {
    if (!profissionalSelecionado || !nivelAcesso) {
      setError('Selecione um profissional e nível de acesso');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await pacientesService.compartilhar(pacienteId, profissionalSelecionado, nivelAcesso);
      setSuccess('Paciente compartilhado com sucesso!');
      setProfissionalSelecionado('');
      setNivelAcesso('leitura');
      
      // Recarregar compartilhamentos
      await carregarDados();
      
      if (onCompartilhamentoAtualizado) {
        onCompartilhamentoAtualizado();
      }
    } catch (err) {
      setError('Erro ao compartilhar: ' + (err.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handleRemoverCompartilhamento = async (compartilhamentoId) => {
    const ok = await confirm({
      title: 'Remover compartilhamento?',
      message: 'O profissional não terá mais acesso ao prontuário deste paciente.',
      confirmLabel: 'Remover',
      destructive: true,
    });
    if (!ok) return;

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await pacientesService.removerCompartilhamento(pacienteId, compartilhamentoId);
      setSuccess('Compartilhamento removido com sucesso!');
      
      // Recarregar compartilhamentos
      await carregarDados();
      
      if (onCompartilhamentoAtualizado) {
        onCompartilhamentoAtualizado();
      }
    } catch (err) {
      setError('Erro ao remover compartilhamento: ' + (err.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getNivelAcessoColor = (nivel) => {
    switch (nivel) {
      case 'leitura':
        return 'info';
      case 'escrita':
        return 'warning';
      case 'completo':
        return 'success';
      default:
        return 'default';
    }
  };

  const getNivelAcessoLabel = (nivel) => {
    switch (nivel) {
      case 'leitura':
        return 'Somente Leitura';
      case 'escrita':
        return 'Leitura e Escrita';
      case 'completo':
        return 'Acesso Completo';
      default:
        return nivel;
    }
  };

  if (!ehResponsavel) {
    return (
      <>
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
          <DialogTitle>
            <Box display="flex" alignItems="center" gap={1}>
              <ShareIcon />
              Compartilhamento de Paciente
            </Box>
          </DialogTitle>
          <DialogContent>
            <Alert severity="info">
              Apenas o profissional responsável pode gerenciar compartilhamentos.
            </Alert>
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>Fechar</Button>
          </DialogActions>
        </Dialog>
        <ConfirmDialog />
      </>
    );
  }

  return (
    <>
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <ShareIcon />
          Compartilhar Paciente: {pacienteNome}
        </Box>
      </DialogTitle>
      
      <DialogContent>
        {loading && (
          <Box display="flex" justifyContent="center" my={2}>
            <CircularProgress />
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        {/* Formulário para novo compartilhamento */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Compartilhar com novo profissional
          </Typography>
          
          <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Profissional</InputLabel>
              <Select
                value={profissionalSelecionado}
                onChange={(e) => setProfissionalSelecionado(e.target.value)}
                label="Profissional"
                disabled={loading}
              >
                {profissionais.map((prof) => (
                  <MenuItem key={prof.id} value={prof.id}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <PersonIcon fontSize="small" />
                      {prof.nome} - CRM: {prof.crm}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>Nível de Acesso</InputLabel>
              <Select
                value={nivelAcesso}
                onChange={(e) => setNivelAcesso(e.target.value)}
                label="Nível de Acesso"
                disabled={loading}
              >
                <MenuItem value="leitura">Somente Leitura</MenuItem>
                <MenuItem value="escrita">Leitura e Escrita</MenuItem>
                <MenuItem value="completo">Acesso Completo</MenuItem>
              </Select>
            </FormControl>

            <Button
              variant="contained"
              onClick={handleCompartilhar}
              disabled={loading || !profissionalSelecionado}
              startIcon={<ShareIcon />}
            >
              Compartilhar
            </Button>
          </Box>
        </Box>

        {/* Lista de compartilhamentos existentes */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Compartilhamentos ativos ({compartilhamentos.length})
          </Typography>
          
          {compartilhamentos.length === 0 ? (
            <Alert severity="info">
              Este paciente ainda não foi compartilhado com outros profissionais.
            </Alert>
          ) : (
            <List>
              {compartilhamentos.map((comp) => (
                <ListItem key={comp.id} divider>
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <PersonIcon />
                        {comp.profissional_nome}
                      </Box>
                    }
                    secondary={
                      <Box display="flex" flexDirection="column" gap={1} mt={1}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2" color="text.secondary">
                            Nível de acesso:
                          </Typography>
                          <Chip
                            label={getNivelAcessoLabel(comp.nivel_acesso)}
                            color={getNivelAcessoColor(comp.nivel_acesso)}
                            size="small"
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          Compartilhado em: {new Date(comp.data_compartilhamento).toLocaleDateString('pt-BR')}
                        </Typography>
                        {comp.compartilhador_nome && (
                          <Typography variant="body2" color="text.secondary">
                            Por: {comp.compartilhador_nome}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={() => handleRemoverCompartilhamento(comp.id)}
                      disabled={loading}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        {/* Informações sobre níveis de acesso */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            Níveis de Acesso:
          </Typography>
          <Typography variant="body2" component="div">
            • <strong>Somente Leitura:</strong> Pode visualizar dados do paciente<br/>
            • <strong>Leitura e Escrita:</strong> Pode visualizar e editar dados do paciente<br/>
            • <strong>Acesso Completo:</strong> Pode visualizar, editar e excluir dados (exceto o próprio paciente)
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Fechar</Button>
      </DialogActions>
    </Dialog>
    <ConfirmDialog />
    </>
  );
};

export default CompartilhamentoPaciente;
