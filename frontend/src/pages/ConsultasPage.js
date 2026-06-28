import React from 'react';
import { Container } from '@mui/material';
import EventIcon from '@mui/icons-material/Event';
import PageHeader from '../components/PageHeader';
import CalendarioConsultas from '../components/CalendarioConsultas';

const ConsultasPage = () => {
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <PageHeader
        title="Consultas"
        subtitle="Gerencie agendamentos, visualize o calendário e envie lembretes"
        icon={<EventIcon />}
      />
      <CalendarioConsultas />
    </Container>
  );
};

export default ConsultasPage;
