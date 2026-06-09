import React from 'react';
import { 
  Paper, 
  Typography, 
  Box, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import { 
  Security as SecurityIcon,
  VerifiedUser as VerifiedUserIcon,
  Lock as LockIcon,
  Visibility as VisibilityIcon,
  DataUsage as DataUsageIcon,
  Https as HttpsIcon,
  VerifiedUser as ShieldIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';

const SecurityMeasures = () => {
  return (
    <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <SecurityIcon color="primary" sx={{ fontSize: 32, mr: 2 }} />
        <Typography variant="h5" component="h2">
          Medidas de Segurança e Conformidade com LGPD
        </Typography>
      </Box>
      
      <Divider sx={{ mb: 3 }} />
      
      <Typography variant="body1" paragraph>
        O sistema AraOS implementa diversas medidas de segurança e está em conformidade com a Lei Geral de Proteção de Dados (LGPD) do Brasil. Abaixo estão as principais medidas implementadas:
      </Typography>
      
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel1a-content"
          id="panel1a-header"
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <LockIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">Autenticação e Autorização</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Autenticação Segura" 
                secondary="Sistema de autenticação baseado em JWT com tempo de expiração definido"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Senhas Protegidas" 
                secondary="Senhas armazenadas com hash seguro, nunca em texto plano"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Controle de Acesso" 
                secondary="Verificação de identidade em todas as rotas protegidas"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel2a-content"
          id="panel2a-header"
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <DataUsageIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">Proteção de Dados</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Dados Sensíveis Protegidos" 
                secondary="Dados de pacientes armazenados em banco de dados com acesso controlado"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Transmissão Segura" 
                secondary="Dados transmitidos via HTTPS para garantir a segurança durante a comunicação"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Validação de Entrada" 
                secondary="Validação rigorosa de todos os dados inseridos para prevenir injeções maliciosas"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel3a-content"
          id="panel3a-header"
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <VisibilityIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">Auditoria e Transparência</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Logs de Atividades" 
                secondary="Registro detalhado de todas as ações realizadas no sistema"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Rastreabilidade" 
                secondary="Identificação de quem acessou quais dados e quando"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Política de Privacidade" 
                secondary="Informações claras sobre como seus dados são tratados"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
      
      <Accordion>
        <AccordionSummary
          expandIcon={<ExpandMoreIcon />}
          aria-controls="panel4a-content"
          id="panel4a-header"
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ShieldIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">Conformidade com LGPD</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Consentimento" 
                secondary="Obtenção e gestão de consentimento explícito para tratamento de dados"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Direitos do Titular" 
                secondary="Mecanismos para exercício dos direitos previstos na LGPD"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <VerifiedUserIcon color="success" />
              </ListItemIcon>
              <ListItemText 
                primary="Minimização de Dados" 
                secondary="Coleta apenas dos dados necessários para a finalidade específica"
              />
            </ListItem>
          </List>
        </AccordionDetails>
      </Accordion>
      
      <Box sx={{ mt: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
        <Typography variant="body1" color="white" align="center">
          Não se preocupe. Seus dados estão seguros. O sistema é completamente compatível com a LGPD!
        </Typography>
      </Box>
    </Paper>
  );
};

export default SecurityMeasures;
