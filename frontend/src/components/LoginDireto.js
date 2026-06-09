import React, { useState } from 'react';
import { 
  Button, 
  TextField, 
  Paper, 
  Typography, 
  Box, 
  Alert,
  Container 
} from '@mui/material';

function LoginDireto() {
  const [usuario, setUsuario] = useState('admin');
  const [senha, setSenha] = useState('AraOS@2025');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');

  const handleLogin = async (e) => {
    e.preventDefault();
    console.log('LOGIN_DIRETO: Iniciando login...');
    setLoading(true);
    setMessage('Entrando...');
    setMessageType('info');

    try {
      // Passo 1: Obter token CSRF
      console.log('LOGIN_DIRETO: Obtendo token CSRF...');
      setMessage('Obtendo token de segurança...');
      
      const csrfResponse = await fetch('http://localhost:5000/api/csrf-token');
      
      if (!csrfResponse.ok) {
        throw new Error(`Erro ao obter token CSRF: ${csrfResponse.status}`);
      }
      
      const csrfData = await csrfResponse.json();
      console.log('LOGIN_DIRETO: Token CSRF obtido');

      // Passo 2: Fazer login
      console.log('LOGIN_DIRETO: Fazendo login...');
      setMessage('Verificando credenciais...');

      const loginResponse = await fetch('http://localhost:5000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfData.csrf_token
        },
        body: JSON.stringify({
          usuario: usuario,
          senha: senha
        })
      });

      console.log('LOGIN_DIRETO: Status da resposta:', loginResponse.status);

      if (loginResponse.ok) {
        const loginData = await loginResponse.json();
        console.log('LOGIN_DIRETO: Login bem-sucedido!');
        
        // Salvar dados no localStorage
        localStorage.setItem('token', loginData.access_token);
        localStorage.setItem('refresh_token', loginData.refresh_token);
        localStorage.setItem('user', JSON.stringify(loginData.user));
        localStorage.setItem('csrf_token', loginData.csrf_token);
        
        setMessage(`✅ Login realizado com sucesso! Bem-vindo, ${loginData.user.nome}!`);
        setMessageType('success');
        
        // Redirecionar após 2 segundos
        setTimeout(() => {
          window.location.href = '/';
        }, 2000);
        
      } else {
        const errorData = await loginResponse.json();
        console.error('LOGIN_DIRETO: Erro no login:', errorData);
        setMessage(`❌ Erro: ${errorData.error || 'Credenciais inválidas'}`);
        setMessageType('error');
      }

    } catch (error) {
      console.error('LOGIN_DIRETO: Erro capturado:', error);
      setMessage(`❌ Erro de conexão: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            🔐 Login AraOS — Clinical Intelligence Operating System
          </Typography>
          
          <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
            Sistema de Prontuário com IA Avançada
          </Typography>
          
          {message && (
            <Alert severity={messageType} sx={{ mb: 3 }}>
              {message}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleLogin}>
            <TextField
              label="Usuário"
              variant="outlined"
              fullWidth
              margin="normal"
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              required
              autoFocus
            />
            
            <TextField
              label="Senha"
              type="password"
              variant="outlined"
              fullWidth
              margin="normal"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
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
          
          <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
            <Typography variant="h6" gutterBottom>
              🔑 Credenciais de Teste:
            </Typography>
            <Typography variant="body2">
              <strong>Usuário:</strong> admin<br />
              <strong>Senha:</strong> AraOS@2025
            </Typography>
          </Box>
          
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              Sistema com 38+ modelos de IA configurados<br />
              Versão 2.1.6 - Login Direto
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default LoginDireto;
