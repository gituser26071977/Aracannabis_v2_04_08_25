import React from 'react';
import { Box, Typography, Paper, Button, Link } from '@mui/material';
import SecurityMeasures from '../components/SecurityMeasures';
import PrivacyPolicy from '../components/PrivacyPolicy';
import LGPDBanner from '../components/LGPDBanner';

const SecurityPage = () => {
  return (
    <Box sx={{ width: '100%', mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Segurança e Privacidade
      </Typography>
      
      <LGPDBanner variant="dashboard" />
      
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          Compromisso com a Segurança e Privacidade
        </Typography>
        
        <Typography variant="body1" paragraph>
          A Aracannabis está comprometida em proteger a privacidade e a segurança dos dados de nossos pacientes. 
          Implementamos medidas técnicas e organizacionais robustas para garantir a conformidade com a Lei Geral 
          de Proteção de Dados (LGPD) do Brasil e as melhores práticas de segurança da informação.
        </Typography>
        
        <Typography variant="body1" paragraph>
          Nossa abordagem de segurança e privacidade é baseada em três pilares fundamentais:
        </Typography>
        
        <Box component="ul" sx={{ pl: 4 }}>
          <Typography component="li" variant="body1" paragraph>
            <strong>Transparência:</strong> Fornecemos informações claras sobre como coletamos, usamos e protegemos seus dados.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Controle:</strong> Oferecemos mecanismos para que você exerça seus direitos sobre seus dados pessoais.
          </Typography>
          <Typography component="li" variant="body1" paragraph>
            <strong>Segurança:</strong> Implementamos medidas técnicas avançadas para proteger seus dados contra acesso não autorizado.
          </Typography>
        </Box>
        
        <Box sx={{ mt: 3, p: 2, bgcolor: 'primary.light', borderRadius: 1 }}>
          <Typography variant="body1" color="white" align="center">
            Não se preocupe. Seus dados estão seguros. O sistema é completamente compatível com a LGPD!
          </Typography>
        </Box>
      </Paper>
      
      <SecurityMeasures />
      
      <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
        Política de Privacidade
      </Typography>
      
      <PrivacyPolicy />
      
      <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
        <Typography variant="h5" gutterBottom>
          Dúvidas ou Solicitações
        </Typography>
        
        <Typography variant="body1" paragraph>
          Se você tiver dúvidas sobre nossa política de privacidade ou quiser exercer seus direitos como titular de dados, 
          entre em contato conosco através do e-mail: <Link href="mailto:privacidade@aracannabis.com.br">privacidade@aracannabis.com.br</Link>
        </Typography>
        
        <Typography variant="body1" paragraph>
          Estamos à disposição para esclarecer qualquer dúvida e atender às solicitações relacionadas aos seus dados pessoais.
        </Typography>
        
        <Button variant="contained" color="primary" href="mailto:privacidade@aracannabis.com.br">
          Contatar Responsável pela Proteção de Dados
        </Button>
      </Paper>
    </Box>
  );
};

export default SecurityPage;
