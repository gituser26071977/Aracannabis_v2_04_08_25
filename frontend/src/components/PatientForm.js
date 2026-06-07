import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Grid,
  Typography,
  Paper,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar,
  Alert,
  FormControlLabel,
  Checkbox,
  Divider,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Link,
  IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { PhotoCamera, Delete } from '@mui/icons-material';
import { pacientesService, lgpdService } from '../services/api';
import LGPDBanner from './LGPDBanner';
import PrivacyPolicy from './PrivacyPolicy';

const PatientForm = ({ onSave, initialData = null }) => {
  const [formData, setFormData] = useState({
    nome: initialData?.nome || '',
    data_nascimento: initialData?.data_nascimento || '',
    cpf: initialData?.cpf || '',
    telefone: initialData?.telefone || '',
    email: initialData?.email || '',
    endereco: initialData?.endereco || '',
    genero: initialData?.genero || '',
    diagnostico: initialData?.diagnostico || '',
    observacoes: initialData?.observacoes || '',
    associacao: initialData?.associacao || '',
    consentimento_lgpd: initialData?.consentimento_lgpd || false
  });

  const [fotoFile, setFotoFile] = useState(null);
  const [fotoPreview, setFotoPreview] = useState(initialData?.foto_nome ? `${process.env.REACT_APP_API_URL}/pacientes/foto/${initialData.foto_nome}` : null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [openPrivacyModal, setOpenPrivacyModal] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validar tipo de arquivo
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
      if (!allowedTypes.includes(file.type)) {
        setError('Tipo de arquivo não permitido. Use apenas JPG, PNG ou GIF.');
        return;
      }

      // Validar tamanho (máximo 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('Arquivo muito grande. Máximo 5MB.');
        return;
      }

      setFotoFile(file);
      setFotoPreview(URL.createObjectURL(file));
      setError('');
    }
  };

  const handleRemoverFoto = () => {
    setFotoFile(null);
    setFotoPreview(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    console.log('Enviando dados do formulário:', formData);

    try {
      let result;

      // Preparar dados para envio (FormData se houver foto, JSON caso contrário)
      let dadosEnvio;
      if (fotoFile) {
        dadosEnvio = new FormData();
        // Adicionar todos os campos do formulário
        Object.keys(formData).forEach(key => {
          dadosEnvio.append(key, formData[key]);
        });
        // Adicionar arquivo de foto
        dadosEnvio.append('foto', fotoFile);
      } else {
        dadosEnvio = formData;
      }

      if (initialData?.id) {
        // Atualizar paciente existente
        console.log('Atualizando paciente existente com ID:', initialData.id);
        result = await pacientesService.atualizar(initialData.id, dadosEnvio);
      } else {
        // Criar novo paciente
        console.log('Criando novo paciente');
        result = await pacientesService.criar(dadosEnvio);
      }

      console.log('Resposta do servidor:', result);

      // Registrar consentimento LGPD se for um novo paciente ou se o consentimento foi alterado
      if (formData.consentimento_lgpd &&
        (!initialData || initialData.consentimento_lgpd !== formData.consentimento_lgpd)) {
        try {
          await lgpdService.registrarConsentimento(
            result.paciente.id,
            formData.consentimento_lgpd
          );
          console.log('Consentimento LGPD registrado com sucesso');
        } catch (consentError) {
          console.error('Erro ao registrar consentimento LGPD:', consentError);
          // Não interromper o fluxo principal se houver erro no registro de consentimento
        }
      }

      setSuccess(true);

      // Limpar formulário se for um novo paciente
      if (!initialData) {
        setFormData({
          nome: '',
          data_nascimento: '',
          cpf: '',
          telefone: '',
          email: '',
          endereco: '',
          genero: '',
          diagnostico: '',
          observacoes: '',
          associacao: ''
        });
        setFotoFile(null);
        setFotoPreview(null);
      }

      // Notificar componente pai
      if (onSave) {
        onSave(result.paciente);
      }

    } catch (err) {
      console.error('Erro detalhado ao salvar paciente:', err);
      if (err.response) {
        console.error('Resposta do servidor:', err.response);
      }
      setError(err.error || 'Erro ao salvar paciente');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSuccess(false);
  };

  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {initialData ? 'Editar Paciente' : 'Novo Paciente'}
      </Typography>

      <LGPDBanner variant="form" />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              name="nome"
              label="Nome Completo"
              value={formData.nome}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              name="data_nascimento"
              label="Data de Nascimento"
              type="date"
              value={formData.data_nascimento}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" gutterBottom>
              Foto do Paciente
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Avatar
                src={fotoPreview}
                sx={{ width: 80, height: 80 }}
              >
                {!fotoPreview && formData.nome.charAt(0).toUpperCase()}
              </Avatar>
              <Box>
                <input
                  accept="image/*"
                  style={{ display: 'none' }}
                  id="foto-upload"
                  type="file"
                  onChange={handleFotoChange}
                />
                <label htmlFor="foto-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<PhotoCamera />}
                    size="small"
                  >
                    Escolher Foto
                  </Button>
                </label>
                {fotoFile && (
                  <Button
                    variant="outlined"
                    color="error"
                    size="small"
                    startIcon={<Delete />}
                    onClick={handleRemoverFoto}
                    sx={{ ml: 1 }}
                  >
                    Remover
                  </Button>
                )}
              </Box>
            </Box>
            <Typography variant="caption" color="text.secondary">
              Formatos aceitos: JPG, PNG, GIF. Tamanho máximo: 5MB
            </Typography>
            <Divider sx={{ my: 2 }} />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              name="cpf"
              label="CPF"
              value={formData.cpf}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Gênero</InputLabel>
              <Select
                name="genero"
                value={formData.genero}
                onChange={handleChange}
                label="Gênero"
              >
                <MenuItem value="masculino">Masculino</MenuItem>
                <MenuItem value="feminino">Feminino</MenuItem>
                <MenuItem value="outro">Outro</MenuItem>
                <MenuItem value="nao_informado">Prefiro não informar</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              name="telefone"
              label="Telefone"
              value={formData.telefone}
              onChange={handleChange}
              fullWidth
              margin="normal"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              name="email"
              label="E-mail"
              type="email"
              value={formData.email}
              onChange={handleChange}
              fullWidth
              margin="normal"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              name="endereco"
              label="Endereço"
              value={formData.endereco}
              onChange={handleChange}
              fullWidth
              margin="normal"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              name="associacao"
              label="Associação de Pacientes"
              value={formData.associacao}
              onChange={handleChange}
              fullWidth
              margin="normal"
              placeholder="Ex: ABRACE, Santa Cannabis (opcional)"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              name="diagnostico"
              label="Diagnóstico"
              value={formData.diagnostico}
              onChange={handleChange}
              fullWidth
              margin="normal"
              multiline
              rows={2}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              name="observacoes"
              label="Observações"
              value={formData.observacoes}
              onChange={handleChange}
              fullWidth
              margin="normal"
              multiline
              rows={3}
            />
          </Grid>

          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle1" color="primary" gutterBottom>
              Consentimento LGPD
            </Typography>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.consentimento_lgpd}
                  onChange={(e) => setFormData({ ...formData, consentimento_lgpd: e.target.checked })}
                  name="consentimento_lgpd"
                  color="primary"
                />
              }
              label={
                <Typography variant="body2">
                  Concordo com a coleta e processamento dos meus dados pessoais conforme a{' '}
                  <Link component="button" variant="body2" onClick={(e) => { e.preventDefault(); setOpenPrivacyModal(true); }}>
                    Política de Privacidade
                  </Link>
                </Typography>
              }
            />
          </Grid>

          <Grid item xs={12}>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? 'Salvando...' : initialData ? 'Atualizar' : 'Cadastrar'}
            </Button>
          </Grid>
        </Grid>
      </Box>

      <Snackbar
        open={success}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="success">
          Paciente {initialData ? 'atualizado' : 'cadastrado'} com sucesso!
        </Alert>
      </Snackbar>

      <Dialog
        open={openPrivacyModal}
        onClose={() => setOpenPrivacyModal(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Política de Privacidade
          <IconButton
            aria-label="close"
            onClick={() => setOpenPrivacyModal(false)}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
              color: (theme) => theme.palette.grey[500],
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          <PrivacyPolicy />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPrivacyModal(false)}>
            Fechar
          </Button>
          <Button onClick={() => {
            setFormData({ ...formData, consentimento_lgpd: true });
            setOpenPrivacyModal(false);
          }} variant="contained" color="primary">
            Concordar
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default PatientForm;
