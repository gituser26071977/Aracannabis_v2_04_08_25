import React, { useState } from 'react';
import {
  Button,
  TextField,
  Paper,
  Typography,
  Box,
  Alert,
  Container,
  Link as MuiLink
} from '@mui/material';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * LoginDireto — DESCONTINUADO.
 *
 * Este componente era usado como rota de diagnóstico direto da API, mas foi
 * substituído pelo AuthContext compartilhado. Removidas credenciais hardcoded
 * e URLs localhost; agora redireciona para a tela de login principal.
 *
 * MISSÃO 12 — UI Credibility Hardening.
 */
function LoginDireto() {
  const [message] = useState('Esta tela foi descontinuada. Use o login principal abaixo.');
  const { login } = useAuth();
  const [usuario, setUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(usuario, senha);
    } catch (err) {
      // erro tratado pelo AuthContext
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            AraOS — Sistema de Prontuário
          </Typography>

          <Alert severity="warning" sx={{ mb: 3 }}>
            {message}
          </Alert>

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Usuário"
              variant="outlined"
              fullWidth
              margin="normal"
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              autoComplete="username"
              required
            />
            <TextField
              label="Senha"
              type="password"
              variant="outlined"
              fullWidth
              margin="normal"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              autoComplete="current-password"
              required
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              size="large"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </Button>
          </Box>

          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <MuiLink component={Link} to="/login" variant="body2">
              Voltar para a tela de login
            </MuiLink>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default LoginDireto;
