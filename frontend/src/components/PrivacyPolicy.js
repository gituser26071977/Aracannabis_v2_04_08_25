import React from 'react';
import { 
  Paper, 
  Typography, 
  Box,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Security as SecurityIcon,
  Gavel as GavelIcon,
  Person as PersonIcon,
  Storage as StorageIcon,
  AccessTime as AccessTimeIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';

const PrivacyPolicy = () => {
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Política de Privacidade
      </Typography>
      
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Última atualização: 21 de Maio de 2025
      </Typography>
      
      <Divider sx={{ my: 2 }} />
      
      <Typography variant="body1" paragraph>
        A AraOS está comprometida com a proteção da sua privacidade e com o cumprimento da 
        Lei Geral de Proteção de Dados (LGPD) do Brasil. Esta política de privacidade descreve como 
        coletamos, usamos, compartilhamos e protegemos suas informações pessoais.
      </Typography>
      
      <Box sx={{ my: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <PersonIcon sx={{ mr: 1 }} /> Dados Pessoais Coletados
        </Typography>
        
        <Typography variant="body1" paragraph>
          Coletamos os seguintes dados pessoais para fornecer nossos serviços médicos:
        </Typography>
        
        <List>
          <ListItem>
            <ListItemText 
              primary="Dados de identificação" 
              secondary="Nome, CPF, data de nascimento, gênero"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Dados de contato" 
              secondary="Endereço, telefone, e-mail"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Dados de saúde" 
              secondary="Diagnósticos, sintomas, dosagens, evoluções médicas"
            />
          </ListItem>
        </List>
      </Box>
      
      <Box sx={{ my: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <StorageIcon sx={{ mr: 1 }} /> Finalidade do Tratamento
        </Typography>
        
        <Typography variant="body1" paragraph>
          Seus dados pessoais são utilizados para:
        </Typography>
        
        <List>
          <ListItem>
            <ListItemText 
              primary="Prestação de serviços médicos" 
              secondary="Acompanhamento de tratamento, registro de sintomas e dosagens"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Comunicação" 
              secondary="Contato para agendamentos, resultados e orientações"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Melhoria dos serviços" 
              secondary="Análise de eficácia dos tratamentos e ajustes necessários"
            />
          </ListItem>
        </List>
      </Box>
      
      <Box sx={{ my: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <SecurityIcon sx={{ mr: 1 }} /> Medidas de Segurança
        </Typography>
        
        <Typography variant="body1" paragraph>
          Implementamos medidas técnicas e organizacionais para proteger seus dados pessoais, incluindo:
        </Typography>
        
        <List>
          <ListItem>
            <ListItemText 
              primary="Criptografia" 
              secondary="Dados transmitidos e armazenados de forma segura"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Controle de acesso" 
              secondary="Apenas profissionais autorizados têm acesso aos seus dados"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Auditoria" 
              secondary="Registro de todas as atividades realizadas no sistema"
            />
          </ListItem>
        </List>
      </Box>
      
      <Box sx={{ my: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <GavelIcon sx={{ mr: 1 }} /> Seus Direitos
        </Typography>
        
        <Typography variant="body1" paragraph>
          De acordo com a LGPD, você tem os seguintes direitos:
        </Typography>
        
        <List>
          <ListItem>
            <ListItemText 
              primary="Acesso" 
              secondary="Solicitar acesso aos seus dados pessoais"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Correção" 
              secondary="Solicitar a correção de dados incompletos, inexatos ou desatualizados"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Exclusão" 
              secondary="Solicitar a exclusão dos seus dados, exceto em casos previstos em lei"
            />
          </ListItem>
          <ListItem>
            <ListItemText 
              primary="Revogação do consentimento" 
              secondary="Revogar o consentimento a qualquer momento"
            />
          </ListItem>
        </List>
      </Box>
      
      <Box sx={{ my: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <AccessTimeIcon sx={{ mr: 1 }} /> Período de Retenção
        </Typography>
        
        <Typography variant="body1" paragraph>
          Seus dados pessoais serão mantidos pelo tempo necessário para cumprir as finalidades para as quais foram coletados, 
          incluindo obrigações legais, contratuais, de prestação de contas ou requisição de autoridades competentes.
        </Typography>
        
        <Typography variant="body1" paragraph>
          Para dados médicos, seguimos os prazos estabelecidos pelo Conselho Federal de Medicina e legislação aplicável.
        </Typography>
      </Box>
      
      <Box sx={{ my: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <DeleteIcon sx={{ mr: 1 }} /> Como Exercer Seus Direitos
        </Typography>
        
        <Typography variant="body1" paragraph>
          Para exercer seus direitos ou obter mais informações sobre como tratamos seus dados pessoais, 
          entre em contato conosco através do e-mail: privacidade@arapath.com.br
        </Typography>
      </Box>
      
      <Divider sx={{ my: 2 }} />
      
      <Typography variant="body2" color="text.secondary">
        Esta política de privacidade pode ser atualizada periodicamente. Recomendamos que você revise 
        regularmente para estar ciente de quaisquer alterações.
      </Typography>
    </Paper>
  );
};

export default PrivacyPolicy;
