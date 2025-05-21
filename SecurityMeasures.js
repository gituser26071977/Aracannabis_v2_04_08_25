import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Grid,
  Button,
  Divider,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import { 
  Security as SecurityIcon,
  Lock as LockIcon,
  VerifiedUser as VerifiedUserIcon,
  DataUsage as DataUsageIcon
} from '@mui/icons-material';

const SecurityMeasures = () => {
  const [showDetails, setShowDetails] = useState(false);
  
  const toggleDetails = () => {
    setShowDetails(!showDetails);
  };
  
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
        <Typography variant="h5" component="h1" color="primary" gutterBottom fontWeight="bold">
          Medidas de Segurança e Proteção de Dados
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          O Aracannabis implementa rigorosas medidas de segurança para proteger seus dados pessoais e de saúde, em conformidade com a LGPD (Lei 13.709/2018).
        </Typography>
        
        <Alert severity="info" sx={{ mb: 3 }}>
          <AlertTitle>Compromisso com sua privacidade</AlertTitle>
          Seus dados são protegidos por medidas técnicas e organizacionais adequadas para prevenir acessos não autorizados, perdas acidentais, destruição ou danos.
        </Alert>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SecurityIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Segurança da Informação
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <LockIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Criptografia de dados" 
                  secondary="Todos os dados sensíveis são criptografados em repouso e em trânsito"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <LockIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Backups regulares" 
                  secondary="Realizamos backups criptografados diários para garantir a disponibilidade dos dados"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <LockIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Proteção contra invasões" 
                  secondary="Utilizamos firewalls, detecção de intrusão e monitoramento contínuo"
                />
              </ListItem>
            </List>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <VerifiedUserIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Controle de Acesso
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <DataUsageIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Autenticação de dois fatores" 
                  secondary="Camada adicional de segurança para verificar a identidade dos usuários"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <DataUsageIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Níveis de permissão" 
                  secondary="Acesso baseado em função, garantindo que cada profissional acesse apenas os dados necessários"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <DataUsageIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Registros detalhados" 
                  secondary="Logs de todas as atividades para fins de auditoria e rastreabilidade"
                />
              </ListItem>
            </List>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ textAlign: 'center' }}>
          <Button 
            variant="outlined" 
            color="primary" 
            onClick={toggleDetails}
            sx={{ mb: 2 }}
          >
            {showDetails ? 'Ocultar Detalhes Técnicos' : 'Mostrar Detalhes Técnicos'}
          </Button>
          
          {showDetails && (
            <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1, textAlign: 'left' }}>
              <Typography variant="subtitle1" color="primary" gutterBottom>
                Detalhes Técnicos das Medidas de Segurança
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Criptografia:</strong> Utilizamos criptografia AES-256 para dados em repouso e TLS 1.3 para dados em trânsito.
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Autenticação:</strong> Implementamos JWT (JSON Web Tokens) com expiração curta e rotação de tokens.
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Proteção contra ataques:</strong> Implementamos proteção contra ataques de injeção SQL, XSS, CSRF e limitação de taxa de requisições.
              </Typography>
              
              <Typography variant="body2" paragraph>
                <strong>Anonimização:</strong> Dados utilizados para pesquisa e estatísticas são anonimizados, removendo todos os identificadores pessoais.
              </Typography>
              
              <Typography variant="body2">
                <strong>Monitoramento:</strong> Sistema de monitoramento 24/7 com alertas automáticos para detecção de atividades suspeitas.
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

export default SecurityMeasures;
