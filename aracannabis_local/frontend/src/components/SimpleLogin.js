import React, { useState } from 'react';
import { Button, TextField, Paper, Typography, Box, Alert } from '@mui/material';

function SimpleLogin() {
  const [usuario, setUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const testLogin = async () => {
    console.log('SIMPLE_LOGIN: Botão clicado!');
    setMessage('Botão clicado - iniciando teste...');
    setLoading(true);

    try {
      console.log('SIMPLE_LOGIN: Fazendo requisição CSRF...');
      setMessage('Obtendo token CSRF...');
      
      const csrfResponse = await fetch('http://localhost:5011/api/csrf-token');
      console.log('SIMPLE_LOGIN: Resposta CSRF:', csrfResponse.status);
      
      if (!csrfResponse.ok) {
        throw new Error(`Erro CSRF: ${csrfResponse.status}`);
      }
      
      const csrfData = await csrfResponse.json();
      console.log('SIMPLE_LOGIN: Token CSRF obtido:', csrfData);
      setMessage('Token CSRF obtido, fazendo login...');

      const loginResponse = await fetch('http://localhost:5011/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfData.csrf_token
        },
        body: JSON.stringify({
          usuario: usuario || 'admin',
          senha: senha || 'Aracannabis@2025'
        })
      });

      console.log('SIMPLE_LOGIN: Resposta login:', loginResponse.status);
      
      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        console.log('SIMPLE_LOGIN: Login bem-sucedido:', loginData);
        setMessage('Login bem-sucedido! Token: ' + loginData.access_token.substring(0, 20) + '...');
      } else {
        const errorData = await loginResponse.text();
        console.error('SIMPLE_LOGIN: Erro no login:', errorData);
        setMessage('Erro no login: ' + errorData);
      }

    } catch (error) {
      console.error('SIMPLE_LOGIN: Erro capturado:', error);
      setMessage('Erro: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, my: 4, maxWidth: 500, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Teste de Login Simples
      </Typography>
      
      {message && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}
      
      <TextField
        label="Usuário"
        variant="outlined"
        fullWidth
        margin="normal"
        value={usuario}
        onChange={(e) => setUsuario(e.target.value)}
        placeholder="admin"
      />
      <TextField
        label="Senha"
        type="password"
        variant="outlined"
        fullWidth
        margin="normal"
        value={senha}
        onChange={(e) => setSenha(e.target.value)}
        placeholder="Aracannabis@2025"
      />
      
      <Button
        onClick={testLogin}
        variant="contained"
        color="primary"
        fullWidth
        sx={{ mt: 2 }}
        disabled={loading}
      >
        {loading ? 'Testando...' : 'Testar Login'}
      </Button>
      
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="body2">
          Este é um teste direto da API sem usar o contexto React
        </Typography>
      </Box>
    </Paper>
  );
}

export default SimpleLogin;
