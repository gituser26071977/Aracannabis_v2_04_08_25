import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  Button
} from '@mui/material';
import { CheckCircle as CheckCircleIcon, Error as ErrorIcon } from '@mui/icons-material';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { emailVerificationService } from '../services/api';

const VerifyEmailPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading, success, error
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setStatus('error');
      setMessage('Token de verificação não encontrado na URL.');
      return;
    }

    const verify = async () => {
      try {
        const data = await emailVerificationService.verify(token);
        setStatus('success');
        setMessage(data.message || 'Email verificado com sucesso!');
      } catch (err) {
        setStatus('error');
        setMessage(err.error || 'Erro ao verificar email. O link pode ter expirado.');
      }
    };

    verify();
  }, [searchParams]);

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper elevation={2} sx={{ p: 4, borderRadius: 4, textAlign: 'center' }}>
        <Typography variant="h4" gutterBottom fontWeight={700}>
          🌿 Aracannabis
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          Verificação de Email
        </Typography>

        <Box sx={{ my: 4 }}>
          {status === 'loading' && (
            <>
              <CircularProgress size={60} sx={{ mb: 2 }} />
              <Typography>Verificando seu email...</Typography>
            </>
          )}

          {status === 'success' && (
            <>
              <CheckCircleIcon color="success" sx={{ fontSize: 80, mb: 2 }} />
              <Alert severity="success" sx={{ mb: 3, textAlign: 'left' }}>
                {message}
              </Alert>
              <Typography variant="body1" gutterBottom>
                Sua conta está ativa e você já pode fazer login.
              </Typography>
              <Button
                variant="contained"
                onClick={() => navigate('/login')}
                sx={{ mt: 2 }}
              >
                Ir para Login
              </Button>
            </>
          )}

          {status === 'error' && (
            <>
              <ErrorIcon color="error" sx={{ fontSize: 80, mb: 2 }} />
              <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
                {message}
              </Alert>
              <Button
                variant="outlined"
                onClick={() => navigate('/login')}
                sx={{ mt: 2 }}
              >
                Voltar para Login
              </Button>
            </>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default VerifyEmailPage;
