import React from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { Link } from 'react-router-dom';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import HomeIcon from '@mui/icons-material/Home';
import LoginIcon from '@mui/icons-material/Login';

/**
 * 401 — Não autenticado
 * MISSÃO 12 — UI Credibility Hardening
 */
const UnauthorizedPage = () => {
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '70vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: { xs: 3, sm: 5 },
            width: '100%',
            textAlign: 'center',
            borderRadius: 3,
          }}
        >
          <LockOutlinedIcon
            sx={{ fontSize: 80, color: 'warning.main', mb: 2 }}
          />
          <Typography
            variant="h1"
            component="div"
            sx={{
              fontSize: { xs: '3.5rem', sm: '5rem' },
              fontWeight: 800,
              lineHeight: 1,
              mb: 1,
              color: 'warning.main',
            }}
          >
            401
          </Typography>
          <Typography variant="h5" component="h1" gutterBottom fontWeight={600}>
            Sessão expirada
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Sua sessão terminou ou você não está autenticado.
            Faça login novamente para continuar.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<LoginIcon />}
              component={Link}
              to="/login"
              size="large"
            >
              Fazer login
            </Button>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<HomeIcon />}
              component={Link}
              to="/"
              size="large"
            >
              Ir para o início
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default UnauthorizedPage;
