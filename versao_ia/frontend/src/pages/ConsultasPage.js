import React from 'react';
import { Container, Typography, Box } from '@mui/material';
import CalendarioConsultas from '../components/CalendarioConsultas';

const ConsultasPage = () => {
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          📅 Consultas
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Gerencie agendamentos, visualize o calendário e envie lembretes
        </Typography>
      </Box>
      
      <CalendarioConsultas />
    </Container>
  );
};

export default ConsultasPage;
