import React, { useState } from 'react';
import { 
  Paper, 
  Typography, 
  Box,
  Divider,
  FormControlLabel,
  Checkbox,
  Button,
  Alert,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import { 
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon
} from '@mui/icons-material';

const ConsentForm = ({ patientId, onConsent, initialConsent = false }) => {
  const [consent, setConsent] = useState(initialConsent);
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  
  const handleConsentChange = (event) => {
    setConsent(event.target.checked);
  };
  
  const handleSubmit = () => {
    if (onConsent && typeof onConsent === 'function') {
      onConsent(consent);
    }
    setSubmitted(true);
  };
  
  const handleOpenPrivacyPolicy = () => {
    setShowPrivacyPolicy(true);
  };
  
  const handleClosePrivacyPolicy = () => {
    setShowPrivacyPolicy(false);
  };
  
  return (
    <Paper elevation={3} sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Termo de Consentimento para Tratamento de Dados Pessoais
      </Typography>
      
      <Divider sx={{ my: 2 }} />
      
      {submitted && consent ? (
        <Alert 
          icon={<CheckCircleIcon fontSize="inherit" />} 
          severity="success"
          sx={{ mb: 2 }}
        >
          Obrigado! Seu consentimento foi registrado com sucesso.
        </Alert>
      ) : submitted && !consent ? (
        <Alert 
          severity="warning"
          sx={{ mb: 2 }}
        >
          Você optou por não fornecer consentimento. Algumas funcionalidades podem estar limitadas.
        </Alert>
      ) : null}
      
      <Typography variant="body1" paragraph>
        Ao utilizar os serviços da AraOS, você concorda com a coleta e processamento dos seus dados pessoais 
        conforme descrito em nossa Política de Privacidade. Este consentimento é necessário para que possamos 
        fornecer os serviços médicos e acompanhar seu tratamento adequadamente.
      </Typography>
      
      <Typography variant="body1" paragraph>
        Seus dados serão utilizados exclusivamente para:
      </Typography>
      
      <Box component="ul" sx={{ pl: 4 }}>
        <Typography component="li" variant="body1">
          Acompanhamento médico e registro de seu tratamento
        </Typography>
        <Typography component="li" variant="body1">
          Registro de sintomas, dosagens e evolução do tratamento
        </Typography>
        <Typography component="li" variant="body1">
          Comunicação relacionada ao seu tratamento
        </Typography>
        <Typography component="li" variant="body1">
          Cumprimento de obrigações legais e regulatórias
        </Typography>
      </Box>
      
      <Typography variant="body1" paragraph sx={{ mt: 2 }}>
        Você pode revogar este consentimento a qualquer momento, entrando em contato conosco. 
        No entanto, isso pode afetar nossa capacidade de fornecer determinados serviços.
      </Typography>
      
      <Box sx={{ mt: 3, mb: 2 }}>
        <Button
          variant="text"
          color="primary"
          onClick={handleOpenPrivacyPolicy}
          startIcon={<InfoIcon />}
          sx={{ mb: 2 }}
        >
          Ler Política de Privacidade Completa
        </Button>
        
        <FormControlLabel
          control={
            <Checkbox
              checked={consent}
              onChange={handleConsentChange}
              name="consent"
              color="primary"
            />
          }
          label="Eu li e concordo com a Política de Privacidade e autorizo o tratamento dos meus dados pessoais conforme descrito."
        />
      </Box>
      
      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={submitted}
        >
          {submitted ? 'Consentimento Registrado' : 'Confirmar Consentimento'}
        </Button>
      </Box>
      
      {/* Diálogo da Política de Privacidade */}
      <Dialog
        open={showPrivacyPolicy}
        onClose={handleClosePrivacyPolicy}
        scroll="paper"
        aria-labelledby="privacy-policy-dialog-title"
        aria-describedby="privacy-policy-dialog-description"
        maxWidth="md"
        fullWidth
      >
        <DialogTitle id="privacy-policy-dialog-title">
          Política de Privacidade
        </DialogTitle>
        <DialogContent dividers>
          <DialogContentText
            id="privacy-policy-dialog-description"
            tabIndex={-1}
          >
            <Typography variant="h6" gutterBottom>
              1. Dados Pessoais Coletados
            </Typography>
            <Typography variant="body1" paragraph>
              Coletamos os seguintes dados pessoais para fornecer nossos serviços médicos:
              • Dados de identificação: Nome, CPF, data de nascimento, gênero
              • Dados de contato: Endereço, telefone, e-mail
              • Dados de saúde: Diagnósticos, sintomas, dosagens, evoluções médicas
            </Typography>
            
            <Typography variant="h6" gutterBottom>
              2. Finalidade do Tratamento
            </Typography>
            <Typography variant="body1" paragraph>
              Seus dados pessoais são utilizados para:
              • Prestação de serviços médicos: Acompanhamento de tratamento, registro de sintomas e dosagens
              • Comunicação: Contato para agendamentos, resultados e orientações
              • Melhoria dos serviços: Análise de eficácia dos tratamentos e ajustes necessários
            </Typography>
            
            <Typography variant="h6" gutterBottom>
              3. Base Legal
            </Typography>
            <Typography variant="body1" paragraph>
              O tratamento dos seus dados pessoais é realizado com base no seu consentimento, 
              na execução de contrato de prestação de serviços médicos, no cumprimento de 
              obrigações legais e regulatórias, e no legítimo interesse em fornecer e 
              melhorar nossos serviços.
            </Typography>
            
            <Typography variant="h6" gutterBottom>
              4. Compartilhamento de Dados
            </Typography>
            <Typography variant="body1" paragraph>
              Seus dados pessoais podem ser compartilhados com:
              • Profissionais de saúde envolvidos no seu tratamento
              • Autoridades públicas, quando exigido por lei
              • Prestadores de serviços que nos auxiliam na operação do sistema, sempre com garantias adequadas de proteção
            </Typography>
            
            <Typography variant="h6" gutterBottom>
              5. Seus Direitos
            </Typography>
            <Typography variant="body1" paragraph>
              De acordo com a LGPD, você tem os seguintes direitos:
              • Acesso aos seus dados pessoais
              • Correção de dados incompletos, inexatos ou desatualizados
              • Exclusão dos seus dados, exceto em casos previstos em lei
              • Revogação do consentimento a qualquer momento
            </Typography>
            
            <Typography variant="h6" gutterBottom>
              6. Segurança
            </Typography>
            <Typography variant="body1" paragraph>
              Implementamos medidas técnicas e organizacionais para proteger seus dados pessoais, 
              incluindo criptografia, controle de acesso e auditoria.
            </Typography>
            
            <Typography variant="h6" gutterBottom>
              7. Período de Retenção
            </Typography>
            <Typography variant="body1" paragraph>
              Seus dados pessoais serão mantidos pelo tempo necessário para cumprir as finalidades 
              para as quais foram coletados, incluindo obrigações legais, contratuais, de prestação 
              de contas ou requisição de autoridades competentes.
            </Typography>
            
            <Typography variant="h6" gutterBottom>
              8. Contato
            </Typography>
            <Typography variant="body1" paragraph>
              Para exercer seus direitos ou obter mais informações sobre como tratamos seus dados pessoais, 
              entre em contato conosco através do e-mail: privacidade@arapath.com.br
            </Typography>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePrivacyPolicy} color="primary">
            Fechar
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default ConsentForm;
