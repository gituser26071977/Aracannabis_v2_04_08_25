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
  Alert
} from '@mui/material';
import { pacientesService } from '../services/api';

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
    observacoes: initialData?.observacoes || ''
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    console.log('Enviando dados do formulário:', formData);
    
    try {
      let result;
      
      if (initialData?.id) {
        // Atualizar paciente existente
        console.log('Atualizando paciente existente com ID:', initialData.id);
        result = await pacientesService.atualizar(initialData.id, formData);
      } else {
        // Criar novo paciente
        console.log('Criando novo paciente');
        result = await pacientesService.criar(formData);
      }
      
      console.log('Resposta do servidor:', result);
      
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
          observacoes: ''
        });
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
    </Paper>
  );
};

export default PatientForm;
