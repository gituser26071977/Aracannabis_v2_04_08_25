import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Snackbar,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import { Save as SaveIcon, Chat as ChatIcon } from '@mui/icons-material';
import { configIaTenantService } from '../services/api';

const ConfiguracaoIAPage = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  const [config, setConfig] = useState({
    nome_assistente: 'Assistente Virtual',
    tom_de_voz: 'Empático e profissional',
    valor_consulta: '',
    regras_adicionais: '',
    instance_name: '',
    ativo: false,
  });

  useEffect(() => {
    carregarConfiguracao();
  }, []);

  const carregarConfiguracao = async () => {
    try {
      setLoading(true);
      const data = await configIaTenantService.obter();
      setConfig(data);
    } catch (error) {
      exibirMensagem('Erro ao carregar configurações de IA', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, checked, type } = e.target;
    setConfig((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      setSaving(true);
      await configIaTenantService.salvar(config);
      exibirMensagem('Configurações salvas com sucesso!', 'success');
    } catch (error) {
      exibirMensagem(error.error || 'Erro ao salvar configurações', 'error');
    } finally {
      setSaving(false);
    }
  };

  const exibirMensagem = (msg, severity) => {
    setSnackbar({ open: true, message: msg, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar((prev) => ({ ...prev, open: false }));
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <ChatIcon color="primary" fontSize="large" />
        Configurar Assistente IA (SDR)
      </Typography>

      <Typography variant="body1" color="text.secondary" paragraph>
        Configure a personalidade do seu atendente virtual e informe as regras da clínica. 
        A IA utilizará essas informações para marcar consultas para você de forma autônoma.
      </Typography>

      <Paper sx={{ p: 4, borderRadius: 2 }}>
        <form onSubmit={handleSubmit}>
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={config.ativo}
                  onChange={handleChange}
                  name="ativo"
                  color="primary"
                />
              }
              label={config.ativo ? "Assistente Ativo" : "Assistente Desativado"}
            />
          </Box>

          <Typography variant="h6" gutterBottom>Identidade</Typography>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3, mb: 4 }}>
            <TextField
              label="Nome do Assistente"
              name="nome_assistente"
              value={config.nome_assistente}
              onChange={handleChange}
              fullWidth
              variant="outlined"
              required
              helperText="Ex: LIA, Assistente Ana, Recepção Virtual"
            />
            <TextField
              label="Tom de Voz"
              name="tom_de_voz"
              value={config.tom_de_voz}
              onChange={handleChange}
              fullWidth
              variant="outlined"
              required
              helperText="Ex: Animador e empático; Formal e direto"
            />
          </Box>

          <Divider sx={{ my: 4 }} />

          <Typography variant="h6" gutterBottom>Regras de Negócio</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mb: 4 }}>
            <TextField
              label="Valor da Consulta"
              name="valor_consulta"
              value={config.valor_consulta}
              onChange={handleChange}
              fullWidth
              variant="outlined"
              helperText="Se a IA for questionada sobre preço, usará este valor. Ex: R$ 450,00 (Dinheiro ou Pix)"
            />
            <TextField
              label="Informações e Regras Adicionais"
              name="regras_adicionais"
              value={config.regras_adicionais}
              onChange={handleChange}
              multiline
              rows={4}
              fullWidth
              variant="outlined"
              helperText="Adicione informações sobre estacionamento, formas de pagamento aceitas, regras de atraso, o que é necessário trazer, etc."
            />
          </Box>

          <Divider sx={{ my: 4 }} />

          <Typography variant="h6" gutterBottom>Conexão WhatsApp (Evolution API)</Typography>
          <Box sx={{ mb: 4 }}>
            <TextField
              label="Nome da Instância (Device)"
              name="instance_name"
              value={config.instance_name}
              onChange={handleChange}
              fullWidth
              variant="outlined"
              helperText="O nome exato da sua instância configurada no motor de WhatsApp (Evolution API). Deixe em branco caso a clínica ainda não possua o número conectado."
            />
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 4 }}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              size="large"
              startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
              disabled={saving}
            >
              Salvar Configurações
            </Button>
          </Box>
        </form>
      </Paper>

      <Snackbar open={snackbar.open} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ConfiguracaoIAPage;
