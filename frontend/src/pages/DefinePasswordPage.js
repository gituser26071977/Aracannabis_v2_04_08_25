import React, { useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Box, Button, Paper, TextField, Typography, Alert } from '@mui/material';
import { authService } from '../services/api';

const DefinePasswordPage = () => {
  const [searchParams] = useSearchParams();
  const [novaSenha, setNovaSenha] = useState('');
  const [confirmacao, setConfirmacao] = useState('');
  const [info, setInfo] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const token = searchParams.get('token') || '';
  const userId = searchParams.get('user_id') || '';

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setInfo('');

    console.log('DEFINE_PASSWORD: Init - Token:', token, 'UserId:', userId); // DEBUG log call

    if (!token || !userId) {
      console.error('DEFINE_PASSWORD: Missing parameters');
      setError('Link inválido ou incompleto. Verifique se copiou o link corretamente.');
      return;
    }

    if (novaSenha !== confirmacao) {
      setError('As senhas nao conferem.');
      return;
    }

    setLoading(true);
    try {
      const resp = await authService.definePassword({
        user_id: userId,
        token,
        nova_senha: novaSenha
      });
      setInfo(resp.message || 'Senha definida com sucesso.');
    } catch (err) {
      setError(err?.error || 'Nao foi possivel definir a senha.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, my: 4, maxWidth: 500, mx: 'auto' }}>
      <Typography variant="h5" component="h1" gutterBottom align="center">
        Definir Nova Senha
      </Typography>
      <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 2 }}>
        Escolha uma senha forte para acessar o sistema.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {info && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {info} <Link to="/login">Ir para login</Link>
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          label="Nova senha"
          type="password"
          variant="outlined"
          fullWidth
          margin="normal"
          value={novaSenha}
          onChange={(e) => setNovaSenha(e.target.value)}
          required
        />
        <TextField
          label="Confirmar senha"
          type="password"
          variant="outlined"
          fullWidth
          margin="normal"
          value={confirmacao}
          onChange={(e) => setConfirmacao(e.target.value)}
          required
        />
        <Button
          type="submit"
          variant="contained"
          fullWidth
          sx={{ mt: 2 }}
          disabled={loading}
        >
          {loading ? 'Salvando...' : 'Definir senha'}
        </Button>
      </Box>
    </Paper>
  );
};

export default DefinePasswordPage;
