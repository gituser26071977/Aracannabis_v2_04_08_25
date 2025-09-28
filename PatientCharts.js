import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Tabs,
  Tab,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  BarChart as ChartIcon,
  Timeline as TimelineIcon,
  Description as DescriptionIcon,
  Add as AddIcon,
  Print as PrintIcon,
  Share as ShareIcon,
  Download as DownloadIcon
} from '@mui/icons-material';

// Importar componentes de gráficos
import SymptomsChart from './SymptomsChart';
import DosageChart from './DosageChart';

const PatientCharts = ({ pacienteId, pacienteNome }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" component="h1" color="primary" fontWeight="bold">
            Gráficos de Evolução - {pacienteNome || `Paciente #${pacienteId}`}
          </Typography>
          
          <Box>
            <Tooltip title="Imprimir relatório">
              <IconButton color="primary" sx={{ ml: 1 }}>
                <PrintIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Exportar dados">
              <IconButton color="primary" sx={{ ml: 1 }}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Compartilhar">
              <IconButton color="primary" sx={{ ml: 1 }}>
                <ShareIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          variant="fullWidth"
          textColor="primary"
          indicatorColor="primary"
          sx={{ mb: 3 }}
        >
          <Tab 
            icon={<ChartIcon />} 
            label="Sintomas" 
            iconPosition="start"
          />
          <Tab 
            icon={<TimelineIcon />} 
            label="Dosagens" 
            iconPosition="start"
          />
          <Tab 
            icon={<DescriptionIcon />} 
            label="Relatório Combinado" 
            iconPosition="start"
          />
        </Tabs>
        
        <Divider sx={{ mb: 3 }} />
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Box>
            {activeTab === 0 && (
              <SymptomsChart pacienteId={pacienteId} />
            )}
            
            {activeTab === 1 && (
              <DosageChart pacienteId={pacienteId} />
            )}
            
            {activeTab === 2 && (
              <Box>
                <Alert severity="info" sx={{ mb: 3 }}>
                  O relatório combinado permite visualizar a correlação entre sintomas e dosagens ao longo do tempo.
                </Alert>
                
                <Grid container spacing={3}>
                  <Grid item xs={12}>
                    <SymptomsChart pacienteId={pacienteId} />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <DosageChart pacienteId={pacienteId} />
                  </Grid>
                  
                  <Grid item xs={12}>
                    <Card sx={{ bgcolor: '#f5f5f5', borderRadius: 2 }}>
                      <CardContent>
                        <Typography variant="h6" color="primary" gutterBottom>
                          Análise de Correlação
                        </Typography>
                        
                        <Typography variant="body2" paragraph>
                          A análise de correlação entre sintomas e dosagens pode ajudar a identificar padrões e ajustar o tratamento de forma mais eficaz.
                        </Typography>
                        
                        <Typography variant="body2">
                          Selecione sintomas específicos e períodos de tempo para uma análise mais detalhada.
                        </Typography>
                      </CardContent>
                      <CardActions>
                        <Button 
                          variant="outlined" 
                          color="primary" 
                          startIcon={<AddIcon />}
                        >
                          Gerar Análise Detalhada
                        </Button>
                      </CardActions>
                    </Card>
                  </Grid>
                </Grid>
              </Box>
            )}
          </Box>
        )}
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

export default PatientCharts;
