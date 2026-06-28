import React, { useState } from 'react';
import { Button, TextField, Paper, Typography, Box, Alert, Link as MuiLink } from '@mui/material';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * SimpleLogin — rota de teste de diagnóstico (apenas em dev/staging).
 *
 * Em produção esta rota não está acessível pelo menu principal; fica disponível
 * apenas para QA / debugging manual via /test-login.
 *
 * MISSÃO 12 — UI Credibility Hardening: removidas credenciais hardcoded
 * e URLs localhost; usa o AuthContext (mesmo fluxo do /login).
 */
function SimpleLogin() {
  const [usuario, setUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    try {
      await login(usuario, senha);
      setMessage('Login realizado. Redirecionando...');
    } catch (err) {
      setMessage(err?.error || err?.message || 'Falha ao autenticar. Verifique suas credenciais.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, my: 4, maxWidth: 500, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Teste de Login
      </Typography>
      <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
        Rota de diagnóstico. Use a tela de{' '}
        <MuiLink component={Link} to="/login">login principal</MuiLink> se for um usuário regular.
      </Typography>

      {message && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

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
          sx={{ mt: 2 }}
          disabled={loading}
        >
          {loading ? 'Autenticando...' : 'Entrar'}
        </Button>
      </Box>
    </Paper>
  );
}

export default SimpleLogin;
