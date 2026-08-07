import React, { useState } from 'react';
import { Paper, Typography, Box, Alert, AlertTitle, Divider, IconButton } from '@mui/material';
import {
  Security as SecurityIcon,
  Verified as VerifiedIcon,
  Shield as ShieldIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

const LGPDBanner = ({ variant = 'default', showTitle = true, closable = true }) => {
  // Variantes do banner
  const variants = {
    default: {
      icon: <SecurityIcon fontSize="large" />,
      title: 'Seus dados estão protegidos',
      message:
        'Não se preocupe. Seus dados estão seguros. O sistema é completamente compatível com a LGPD!',
      severity: 'info',
      color: 'primary',
    },
    form: {
      icon: <VerifiedIcon fontSize="large" />,
      title: 'Formulário seguro',
      message:
        'Este formulário é seguro e está em conformidade com a LGPD. Seus dados serão tratados com segurança.',
      severity: 'success',
      color: 'success',
    },
    dashboard: {
      icon: <ShieldIcon fontSize="large" />,
      title: 'Sistema protegido',
      message:
        'Sistema protegido e em conformidade com a LGPD. Todos os dados são criptografados e armazenados com segurança.',
      severity: 'info',
      color: 'primary',
    },
  };

  const [dismissed, setDismissed] = useState(() => {
    if (!closable) return false;
    try {
      return localStorage.getItem(`lgpd_banner_dismissed_${variant}`) === '1';
    } catch (e) {
      return false;
    }
  });

  const selectedVariant = variants[variant] || variants.default;

  const dismiss = () => {
    setDismissed(true);
    try {
      localStorage.setItem(`lgpd_banner_dismissed_${variant}`, '1');
    } catch (e) {
      // storage indisponível
    }
  };

  if (dismissed) return null;

  // Versão Alert (mais compacta)
  if (variant === 'compact') {
    return (
      <Alert
        severity={selectedVariant.severity}
        icon={selectedVariant.icon}
        action={
          closable ? (
            <IconButton size="small" color="inherit" onClick={dismiss} aria-label="fechar aviso">
              <CloseIcon fontSize="small" />
            </IconButton>
          ) : undefined
        }
        sx={{ mb: 2 }}
      >
        {showTitle && <AlertTitle>{selectedVariant.title}</AlertTitle>}
        {selectedVariant.message}
      </Alert>
    );
  }

  // Versão Paper (mais destacada)
  return (
    <Paper
      elevation={1}
      sx={{
        p: 2,
        mb: 3,
        border: 1,
        borderColor: `${selectedVariant.color}.main`,
        backgroundColor: `${selectedVariant.color}.50`,
        position: 'relative',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, pr: closable ? 4 : 0 }}>
        <Box
          sx={{
            color: `${selectedVariant.color}.main`,
            display: 'flex',
            alignItems: 'center',
            mr: 2,
          }}
        >
          {selectedVariant.icon}
        </Box>

        {showTitle && (
          <Typography variant="h6" component="div" color={`${selectedVariant.color}.main`}>
            {selectedVariant.title}
          </Typography>
        )}

        {closable && (
          <IconButton
            size="small"
            onClick={dismiss}
            aria-label="fechar aviso"
            sx={{ position: 'absolute', top: 8, right: 8 }}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        )}
      </Box>

      <Divider sx={{ my: 1 }} />

      <Typography variant="body1">{selectedVariant.message}</Typography>
    </Paper>
  );
};

export default LGPDBanner;
