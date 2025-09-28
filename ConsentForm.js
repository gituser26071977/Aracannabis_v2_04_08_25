import React, { useState } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Grid,
  Button,
  Checkbox,
  FormControlLabel,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Alert
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const ConsentForm = ({ pacienteId, onConsent }) => {
  const [openDialog, setOpenDialog] = useState(false);
  const [consents, setConsents] = useState({
    dadosPessoais: false,
    dadosSaude: false,
    compartilhamento: false,
    comunicacoes: false
  });
  const [error, setError] = useState('');

  const handleChange = (event) => {
    setConsents({
      ...consents,
      [event.target.name]: event.target.checked
    });
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleSubmit = () => {
    // Verificar se os consentimentos obrigatórios foram dados
    if (!consents.dadosPessoais || !consents.dadosSaude) {
      setError('Os consentimentos para dados pessoais e dados de saúde são obrigatórios para o tratamento.');
      return;
    }

    // Fechar o diálogo e chamar a função de callback com os consentimentos
    setOpenDialog(false);
    setError('');
    
    if (onConsent) {
      onConsent(consents);
    }
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Paper elevation={2} sx={{ p: 3, borderRadius: 2, border: '1px solid #e0e0e0' }}>
        <Typography variant="h6" color="primary" gutterBottom>
          Consentimento para Tratamento de Dados
        </Typography>
        
        <Typography variant="body2" color="text.secondary" paragraph>
          De acordo com a Lei Geral de Proteção de Dados (LGPD - Lei 13.709/2018), precisamos do seu consentimento explícito para coletar e processar seus dados pessoais.
        </Typography>
        
        <Button 
          variant="outlined" 
          color="primary" 
          onClick={handleOpenDialog}
          sx={{ mt: 1 }}
        >
          Gerenciar Consentimentos
        </Button>
        
        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md">
          <DialogTitle>Termos de Consentimento</DialogTitle>
          <DialogContent>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            
            <DialogContentText paragraph>
              Por favor, leia atentamente e marque as opções para as quais você concede seu consentimento:
            </DialogContentText>
            
            <Box sx={{ mt: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={consents.dadosPessoais} 
                    onChange={handleChange} 
                    name="dadosPessoais" 
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2">
                    <strong>Dados Pessoais (Obrigatório)</strong>: Autorizo a coleta e o processamento dos meus dados pessoais (nome, CPF, data de nascimento, contato) para fins de identificação e comunicação necessária ao tratamento.
                  </Typography>
                }
              />
              
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={consents.dadosSaude} 
                    onChange={handleChange} 
                    name="dadosSaude" 
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2">
                    <strong>Dados de Saúde (Obrigatório)</strong>: Autorizo a coleta e o processamento dos meus dados de saúde (sintomas, tratamentos, evolução clínica) para fins de acompanhamento médico e tratamento com cannabis medicinal.
                  </Typography>
                }
              />
              
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={consents.compartilhamento} 
                    onChange={handleChange} 
                    name="compartilhamento" 
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2">
                    <strong>Compartilhamento de Dados (Opcional)</strong>: Autorizo o compartilhamento dos meus dados anonimizados para fins de pesquisa científica e melhoria dos tratamentos com cannabis medicinal.
                  </Typography>
                }
              />
              
              <FormControlLabel
                control={
                  <Checkbox 
                    checked={consents.comunicacoes} 
                    onChange={handleChange} 
                    name="comunicacoes" 
                    color="primary"
                  />
                }
                label={
                  <Typography variant="body2">
                    <strong>Comunicações (Opcional)</strong>: Autorizo o envio de comunicações sobre meu tratamento, novidades e informações relacionadas à cannabis medicinal.
                  </Typography>
                }
              />
            </Box>
            
            <Box sx={{ mt: 3 }}>
              <Typography variant="body2" color="text.secondary" paragraph>
                Você pode revogar estes consentimentos a qualquer momento, entrando em contato com nosso Encarregado de Proteção de Dados através do e-mail dpo@aracannabis.com.br.
              </Typography>
              
              <Typography variant="body2" color="text.secondary">
                Para mais informações sobre como tratamos seus dados, consulte nossa{' '}
                <RouterLink to="/privacy-policy" style={{ color: '#6A0DAD' }}>
                  Política de Privacidade
                </RouterLink>.
              </Typography>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog} color="inherit">
              Cancelar
            </Button>
            <Button onClick={handleSubmit} color="primary" variant="contained">
              Confirmar Consentimentos
            </Button>
          </DialogActions>
        </Dialog>
      </Paper>
    </Box>
  );
};

export default ConsentForm;
