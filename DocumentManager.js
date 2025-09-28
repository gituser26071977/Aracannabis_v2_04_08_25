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
  CloudUpload as CloudUploadIcon,
  History as HistoryIcon
} from '@mui/icons-material';

// Importar componentes de documentos
import DocumentUpload from './DocumentUpload';
import DocumentHistory from './DocumentHistory';

const DocumentManager = ({ pacienteId, pacienteNome }) => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
        <Typography variant="h5" component="h1" color="primary" fontWeight="bold" gutterBottom>
          Exames e Documentos - {pacienteNome || `Paciente #${pacienteId}`}
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
            icon={<CloudUploadIcon />} 
            label="Gerenciar Documentos" 
            iconPosition="start"
          />
          <Tab 
            icon={<HistoryIcon />} 
            label="Histórico de Uploads" 
            iconPosition="start"
          />
        </Tabs>
        
        <Divider sx={{ mb: 3 }} />
        
        <Box>
          {activeTab === 0 && (
            <DocumentUpload pacienteId={pacienteId} pacienteNome={pacienteNome} />
          )}
          
          {activeTab === 1 && (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="h6" color="text.secondary">
                Histórico de Uploads
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Esta funcionalidade permite visualizar um log detalhado de todos os documentos enviados, incluindo quem fez o upload e quando.
              </Typography>
            </Box>
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

export default DocumentManager;
