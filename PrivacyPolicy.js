import React from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Grid,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import { 
  Shield as ShieldIcon,
  Lock as LockIcon,
  Person as PersonIcon,
  DataUsage as DataUsageIcon,
  Security as SecurityIcon
} from '@mui/icons-material';

const PrivacyPolicy = () => {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" color="primary" gutterBottom fontWeight="bold">
          Política de Privacidade
        </Typography>
        
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          O Aracannabis está comprometido com a proteção dos seus dados pessoais. Nossa política de privacidade explica:
        </Typography>
        
        <Grid container spacing={4} sx={{ mt: 2 }}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <ShieldIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Quais dados coletamos e por quê
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <PersonIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Dados de identificação" 
                  secondary="Nome, CPF, data de nascimento para identificação do paciente"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <PersonIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Dados de contato" 
                  secondary="E-mail, telefone, endereço para comunicação necessária"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <PersonIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Dados de saúde" 
                  secondary="Sintomas, tratamentos, evolução clínica para acompanhamento médico"
                />
              </ListItem>
            </List>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <DataUsageIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Como usamos esses dados
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemIcon>
                  <LockIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Tratamento médico" 
                  secondary="Para execução de procedimentos preliminares ou necessários à prestação do serviço"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <LockIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Consentimento" 
                  secondary="O tratamento dos dados é realizado com base no consentimento do titular"
                />
              </ListItem>
              
              <ListItem>
                <ListItemIcon>
                  <LockIcon fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Obrigação legal" 
                  secondary="Para cumprimento de obrigações legais ou regulatórias"
                />
              </ListItem>
            </List>
          </Grid>
          
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <PersonIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Seus direitos em relação aos seus dados
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemText 
                  primary="Confirmação e acesso" 
                  secondary="Você pode solicitar a confirmação da existência de tratamento e o acesso aos seus dados"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Correção" 
                  secondary="Você pode solicitar a correção de dados incompletos, inexatos ou desatualizados"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Eliminação" 
                  secondary="Você pode solicitar a eliminação dos dados tratados com base no consentimento"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Portabilidade" 
                  secondary="Você pode solicitar a portabilidade dos seus dados para outro fornecedor de serviço"
                />
              </ListItem>
            </List>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <SecurityIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6" component="h2">
                Medidas de segurança que implementamos
              </Typography>
            </Box>
            
            <List>
              <ListItem>
                <ListItemText 
                  primary="Criptografia" 
                  secondary="Todos os dados são criptografados e armazenados em servidores seguros"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Controle de acesso" 
                  secondary="Apenas profissionais de saúde devidamente registrados têm acesso ao sistema"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Autenticação de dois fatores" 
                  secondary="Proteção adicional para garantir a segurança do acesso"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Registros detalhados" 
                  secondary="Logs de acesso e operações para fins de auditoria e controle"
                />
              </ListItem>
            </List>
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary" paragraph>
            Para exercer seus direitos ou obter mais informações, entre em contato com nosso Encarregado de Proteção de Dados:
          </Typography>
          
          <Typography variant="body2" color="text.secondary" paragraph>
            E-mail: dpo@aracannabis.com.br
          </Typography>
          
          <Button variant="outlined" color="primary" sx={{ mt: 2 }}>
            Voltar
          </Button>
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

export default PrivacyPolicy;
