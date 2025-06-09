import React from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  Alert, 
  AlertTitle,
  Divider
} from '@mui/material';
import { 
  Security as SecurityIcon,
  Verified as VerifiedIcon,
  Shield as ShieldIcon
} from '@mui/icons-material';

const LGPDBanner = ({ variant = 'default', showTitle = true }) => {
  // Variantes do banner
  const variants = {
    default: {
      icon: <SecurityIcon fontSize="large" />,
      title: 'Seus dados estão protegidos',
      message: 'Não se preocupe. Seus dados estão seguros. O sistema é completamente compatível com a LGPD!',
      severity: 'info',
      color: 'primary'
    },
    form: {
      icon: <VerifiedIcon fontSize="large" />,
      title: 'Formulário seguro',
      message: 'Este formulário é seguro e está em conformidade com a LGPD. Seus dados serão tratados com segurança.',
      severity: 'success',
      color: 'success'
    },
    dashboard: {
      icon: <ShieldIcon fontSize="large" />,
      title: 'Sistema protegido',
      message: 'Sistema protegido e em conformidade com a LGPD. Todos os dados são criptografados e armazenados com segurança.',
      severity: 'info',
      color: 'primary'
    }
  };
  
  const selectedVariant = variants[variant] || variants.default;
  
  // Versão Alert (mais compacta)
  if (variant === 'compact') {
    return (
      <Alert 
        severity={selectedVariant.severity}
        icon={selectedVariant.icon}
        sx={{ mb: 2 }}
      >
        {showTitle && (
          <AlertTitle>{selectedVariant.title}</AlertTitle>
        )}
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
        backgroundColor: `${selectedVariant.color}.50`
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Box sx={{ 
          color: `${selectedVariant.color}.main`, 
          display: 'flex', 
          alignItems: 'center',
          mr: 2
        }}>
          {selectedVariant.icon}
        </Box>
        
        {showTitle && (
          <Typography variant="h6" component="div" color={`${selectedVariant.color}.main`}>
            {selectedVariant.title}
          </Typography>
        )}
      </Box>
      
      <Divider sx={{ my: 1 }} />
      
      <Typography variant="body1">
        {selectedVariant.message}
      </Typography>
    </Paper>
  );
};

export default LGPDBanner;
