import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  TextField, 
  Button, 
  Paper, 
  Link,
  InputAdornment,
  IconButton,
  Alert,
  Grid
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { authService } from '../services/api';

const Register = () => {
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    nome: '',
    crm: '',
    usuario: '',
    senha: ''
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };
  
  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validação básica
    if (!formData.nome || !formData.crm || !formData.usuario || !formData.senha) {
      setError('Preencha todos os campos');
      return;
    }
    
    setError('');
    setLoading(true);
    
    try {
      await authService.register(formData);
      navigate('/login', { state: { message: 'Cadastro realizado com sucesso! Faça login para continuar.' } });
    } catch (err) {
      console.error('Erro no registro:', err);
      setError(
        err.response?.data?.error || 
        'Falha no registro. Verifique os dados e tente novamente.'
      );
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f5f5f5',
        py: 3
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={3}
          sx={{
            p: 4,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            borderRadius: 2
          }}
        >
          <Box 
            component="img"
            src="/logo.png"
            alt="Aracannabis"
            sx={{ 
              height: 60, 
              mb: 2,
              display: 'block'
            }}
          />
          
          <Typography component="h1" variant="h5" color="primary" fontWeight="bold" mb={3}>
            Registro de Profissional
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  id="nome"
                  label="Nome Completo"
                  name="nome"
                  autoComplete="name"
                  value={formData.nome}
                  onChange={handleChange}
                  disabled={loading}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  id="crm"
                  label="CRM"
                  name="crm"
                  autoComplete="off"
                  value={formData.crm}
                  onChange={handleChange}
                  disabled={loading}
                  helperText="Formato: UFXXXXX (ex: SP12345)"
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  id="usuario"
                  label="Usuário"
                  name="usuario"
                  autoComplete="username"
                  value={formData.usuario}
                  onChange={handleChange}
                  disabled={loading}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  required
                  fullWidth
                  name="senha"
                  label="Senha"
                  type={showPassword ? 'text' : 'password'}
                  id="senha"
                  autoComplete="new-password"
                  value={formData.senha}
                  onChange={handleChange}
                  disabled={loading}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          aria-label="toggle password visibility"
                          onClick={handleTogglePassword}
                          edge="end"
                        >
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
            </Grid>
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              sx={{ mt: 3, mb: 2, py: 1.5 }}
              disabled={loading}
            >
              {loading ? 'Registrando...' : 'Registrar'}
            </Button>
            
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Já tem uma conta?{' '}
                <Link component={RouterLink} to="/login" variant="body2" color="primary">
                  Faça login
                </Link>
              </Typography>
            </Box>
          </Box>
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
    </Box>
  );
};

export default Register;
