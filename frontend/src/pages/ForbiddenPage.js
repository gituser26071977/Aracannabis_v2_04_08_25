import React from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { Link } from 'react-router-dom';
import BlockIcon from '@mui/icons-material/Block';
import HomeIcon from '@mui/icons-material/Home';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

/**
 * 403 — Sem permissão
 * MISSÃO 12 — UI Credibility Hardening
 */
const ForbiddenPage = () => {
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
          <BlockIcon
            sx={{ fontSize: 80, color: 'error.main', mb: 2 }}
          />
          <Typography
            variant="h1"
            component="div"
            sx={{
              fontSize: { xs: '3.5rem', sm: '5rem' },
              fontWeight: 800,
              lineHeight: 1,
              mb: 1,
              color: 'error.main',
            }}
          >
            403
          </Typography>
          <Typography variant="h5" component="h1" gutterBottom fontWeight={600}>
            Acesso negado
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Você não tem permissão para acessar esta página.
            Se acredita que deveria ter acesso, entre em contato com o administrador.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<HomeIcon />}
              component={Link}
              to="/dashboard"
              size="large"
            >
              Ir para o painel
            </Button>
            <Button
              variant="outlined"
              color="primary"
              startIcon={<ArrowBackIcon />}
              onClick={() => window.history.back()}
              size="large"
            >
              Voltar
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default ForbiddenPage;
