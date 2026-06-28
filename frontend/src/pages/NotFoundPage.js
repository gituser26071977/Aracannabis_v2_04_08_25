import React from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import { Link } from 'react-router-dom';
import SearchOffIcon from '@mui/icons-material/SearchOff';
import HomeIcon from '@mui/icons-material/Home';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

/**
 * 404 — Página não encontrada
 * MISSÃO 12 — UI Credibility Hardening
 */
const NotFoundPage = () => {
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
          <SearchOffIcon
            sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }}
          />
          <Typography
            variant="h1"
            component="div"
            sx={{
              fontSize: { xs: '3.5rem', sm: '5rem' },
              fontWeight: 800,
              lineHeight: 1,
              mb: 1,
              color: 'primary.main',
            }}
          >
            404
          </Typography>
          <Typography variant="h5" component="h1" gutterBottom fontWeight={600}>
            Página não encontrada
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            A página que você procura não existe ou foi movida.
            Verifique o endereço digitado ou volte para o início.
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<HomeIcon />}
              component={Link}
              to="/"
              size="large"
            >
              Ir para o início
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

export default NotFoundPage;
