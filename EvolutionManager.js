import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import {
  NoteAdd as NoteAddIcon,
  History as HistoryIcon
} from '@mui/icons-material';

// Importar componentes de evolução médica
import MedicalEvolution from './MedicalEvolution';
import EvolutionHistory from './EvolutionHistory';

const EvolutionManager = ({ pacienteId, pacienteNome }) => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
        <Typography variant="h5" component="h1" color="primary" fontWeight="bold" gutterBottom>
          Evolução Médica - {pacienteNome || `Paciente #${pacienteId}`}
        </Typography>
        
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          variant="fullWidth"
          textColor="primary"
          indicatorColor="primary"
          sx={{ mb: 3 }}
        >
          <Tab 
            icon={<NoteAddIcon />} 
            label="Registrar Evolução" 
            iconPosition="start"
          />
          <Tab 
            icon={<HistoryIcon />} 
            label="Histórico de Evoluções" 
            iconPosition="start"
          />
        </Tabs>
        
        <Divider sx={{ mb: 3 }} />
        
        <Box>
          {activeTab === 0 && (
            <MedicalEvolution pacienteId={pacienteId} pacienteNome={pacienteNome} />
          )}
          
          {activeTab === 1 && (
            <EvolutionHistory pacienteId={pacienteId} pacienteNome={pacienteNome} />
          )}
        </Box>
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

export default EvolutionManager;
