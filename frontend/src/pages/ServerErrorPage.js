import React from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { Link } from 'react-router-dom';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import HomeIcon from '@mui/icons-material/Home';
import RefreshIcon from '@mui/icons-material/Refresh';

/**
 * 500 — Erro interno do servidor
 * MISSÃO 12 — UI Credibility Hardening
 */
const ServerErrorPage = () => {
  const handleReload = () => window.location.reload();

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
          <ReportProblemIcon
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
            500
          </Typography>
          <Typography variant="h5" component="h1" gutterBottom fontWeight={600}>
            Erro no servidor
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Encontramos um problema ao processar sua solicitação.
            Tente novamente em alguns instantes. Se o problema persistir, entre em contato com o suporte.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={handleReload}
              size="large"
            >
              Tentar novamente
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

export default ServerErrorPage;
