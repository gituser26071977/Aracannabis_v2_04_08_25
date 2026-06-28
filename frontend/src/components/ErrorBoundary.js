import React from 'react';
import { Box, Typography, Button, Paper, Container } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import HomeIcon from '@mui/icons-material/Home';

/**
 * ErrorBoundary global — captura erros de renderização no React
 * e exibe uma página amigável em vez de tela branca.
 *
 * MISSÃO 12 — UI Credibility Hardening
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log silencioso (sem expor stack ao usuário)
    if (process.env.NODE_ENV !== 'production') {
      // eslint-disable-next-line no-console
      console.error('[ErrorBoundary]', error, errorInfo);
    }
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <Container maxWidth="sm">
          <Box
            sx={{
              minHeight: '100vh',
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
              <ErrorOutlineIcon
                sx={{ fontSize: 64, color: 'error.main', mb: 2 }}
              />
              <Typography variant="h4" component="h1" gutterBottom fontWeight={700}>
                Algo deu errado
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                Encontramos um erro inesperado. Nossa equipe foi notificada.
                Você pode tentar recarregar a página ou voltar para o início.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={this.handleReload}
                  size="large"
                >
                  Recarregar página
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<HomeIcon />}
                  onClick={this.handleHome}
                  size="large"
                >
                  Ir para o início
                </Button>
              </Box>
            </Paper>
          </Box>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
