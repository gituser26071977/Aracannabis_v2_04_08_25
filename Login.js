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
  Alert
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [formData, setFormData] = useState({
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
    if (!formData.usuario || !formData.senha) {
      setError('Preencha todos os campos');
      return;
    }
    
    setError('');
    setLoading(true);
    
    try {
      await login(formData);
      navigate('/');
    } catch (err) {
      console.error('Erro no login:', err);
      setError(
        err.response?.data?.error || 
        'Falha na autenticação. Verifique suas credenciais.'
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
      <Container maxWidth="xs">
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
            Login
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="usuario"
              label="Usuário"
              name="usuario"
              autoComplete="username"
              autoFocus
              value={formData.usuario}
              onChange={handleChange}
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Box component="span" sx={{ color: 'text.secondary' }}>
                      👤
                    </Box>
                  </InputAdornment>
                ),
              }}
            />
            
            <TextField
              margin="normal"
              required
              fullWidth
              name="senha"
              label="Senha"
              type={showPassword ? 'text' : 'password'}
              id="senha"
              autoComplete="current-password"
              value={formData.senha}
              onChange={handleChange}
              disabled={loading}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Box component="span" sx={{ color: 'text.secondary' }}>
                      🔒
                    </Box>
                  </InputAdornment>
                ),
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
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              sx={{ mt: 3, mb: 2, py: 1.5 }}
              disabled={loading}
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
            
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Não tem uma conta?{' '}
                <Link component={RouterLink} to="/register" variant="body2" color="primary">
                  Registre-se
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

export default Login;
