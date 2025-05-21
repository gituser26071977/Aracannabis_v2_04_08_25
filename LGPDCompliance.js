import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, Typography, Paper, Divider } from '@mui/material';

// Importando componentes LGPD
import PrivacyPolicy from '../../pages/PrivacyPolicy';
import ConsentForm from './ConsentForm';
import DataSubjectRights from './DataSubjectRights';
import ActivityLogs from './ActivityLogs';
import SecurityMeasures from './SecurityMeasures';

const LGPDCompliance = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" color="primary" gutterBottom fontWeight="bold">
          Conformidade com a LGPD
        </Typography>
        
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Gestão de conformidade com a Lei Geral de Proteção de Dados (Lei 13.709/2018)
        </Typography>
        
        <Divider sx={{ my: 3 }} />
        
        <Routes>
          <Route path="/" element={
            <Box>
              <Typography variant="h6" color="primary" gutterBottom>
                Visão Geral da Conformidade LGPD
              </Typography>
              
              <Typography variant="body1" paragraph>
                O Aracannabis está comprometido com a proteção dos seus dados pessoais e com o cumprimento da Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018).
              </Typography>
              
              <Typography variant="body1" paragraph>
                Nesta seção, você encontrará informações sobre como tratamos seus dados, seus direitos como titular dos dados, nossas medidas de segurança e como exercer seus direitos.
              </Typography>
              
              <Box sx={{ mt: 4 }}>
                <ConsentForm />
              </Box>
              
              <Box sx={{ mt: 4 }}>
                <DataSubjectRights />
              </Box>
            </Box>
          } />
          <Route path="/privacy-policy" element={<PrivacyPolicy />} />
          <Route path="/security" element={<SecurityMeasures />} />
          <Route path="/logs" element={<ActivityLogs />} />
        </Routes>
      </Paper>
      
      <Box sx={{ mt: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Aracannabis © {new Date().getFullYear()} - Sistema de Controle de Pacientes
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Dados protegidos conforme LGPD (Lei 13.709/2018)
        </Typography>
      </Box>
    </Container>
  );
};

export default LGPDCompliance;
