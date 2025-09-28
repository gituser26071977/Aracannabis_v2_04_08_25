import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  Grid,
  MenuItem,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  CircularProgress
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import api from '../services/api';

const ESTADOS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

const ESPECIALIDADES = [
  'Clínica Médica',
  'Neurologia',
  'Psiquiatria',
  'Oncologia',
  'Cardiologia',
  'Endocrinologia',
  'Gastroenterologia',
  'Reumatologia',
  'Dermatologia',
  'Ortopedia',
  'Anestesiologia',
  'Medicina da Dor',
  'Medicina Paliativa',
  'Outras'
];

const steps = [
  'Dados Pessoais',
  'Dados Profissionais',
  'Confirmação',
  'Aguardar Aprovação'
];

const CadastroProfissionaisPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [solicitacaoId, setSolicitacaoId] = useState(null);
  
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    crm: '',
    uf_crm: '',
    especialidade: '',
    instituicao: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const validateStep = (step) => {
    switch (step) {
      case 0: // Dados Pessoais
        if (!formData.nome.trim()) {
          setError('Nome é obrigatório');
          return false;
        }
        if (!formData.email.trim()) {
          setError('Email é obrigatório');
          return false;
        }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
          setError('Email inválido');
          return false;
        }
        break;
      
      case 1: // Dados Profissionais
        if (!formData.crm.trim()) {
          setError('CRM é obrigatório');
          return false;
        }
        if (!formData.uf_crm) {
          setError('UF do CRM é obrigatória');
          return false;
        }
        if (!formData.especialidade) {
          setError('Especialidade é obrigatória');
          return false;
        }
        break;
      
      default:
        break;
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep(activeStep)) {
      setActiveStep(prev => prev + 1);
    }
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep(1)) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/cadastro_profissionais/solicitar-cadastro', formData);
      
      if (response.data.success) {
        setSolicitacaoId(response.data.solicitacao_id);
        setSuccess('Solicitação enviada com sucesso!');
        setActiveStep(3);
      } else {
        setError(response.data.error || 'Erro ao enviar solicitação');
      }
    } catch (err) {
      console.error('Erro ao solicitar cadastro:', err);
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Erro interno do servidor');
      }
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Dados Pessoais
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <TextField
                name="nome"
                label="Nome Completo"
                value={formData.nome}
                onChange={handleInputChange}
                fullWidth
                required
                placeholder="Dr. João Silva"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="email"
                label="Email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                fullWidth
                required
                placeholder="joao.silva@email.com"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="telefone"
                label="Telefone"
                value={formData.telefone}
                onChange={handleInputChange}
                fullWidth
                placeholder="(11) 99999-9999"
              />
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Dados Profissionais
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="crm"
                label="Número do CRM"
                value={formData.crm}
                onChange={handleInputChange}
                fullWidth
                required
                placeholder="123456"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                name="uf_crm"
                label="UF do CRM"
                select
                value={formData.uf_crm}
                onChange={handleInputChange}
                fullWidth
                required
              >
                {ESTADOS_BRASIL.map((estado) => (
                  <MenuItem key={estado} value={estado}>
                    {estado}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                name="especialidade"
                label="Especialidade"
                select
                value={formData.especialidade}
                onChange={handleInputChange}
                fullWidth
                required
              >
                {ESPECIALIDADES.map((esp) => (
                  <MenuItem key={esp} value={esp}>
                    {esp}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                name="instituicao"
                label="Instituição/Hospital"
                value={formData.instituicao}
                onChange={handleInputChange}
                fullWidth
                placeholder="Hospital das Clínicas"
              />
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Confirme seus dados
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    <strong>Dados Pessoais:</strong>
                  </Typography>
                  <Typography>Nome: {formData.nome}</Typography>
                  <Typography>Email: {formData.email}</Typography>
                  {formData.telefone && <Typography>Telefone: {formData.telefone}</Typography>}
                  
                  <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                    <strong>Dados Profissionais:</strong>
                  </Typography>
                  <Typography>CRM: {formData.crm}/{formData.uf_crm}</Typography>
                  <Typography>Especialidade: {formData.especialidade}</Typography>
                  {formData.instituicao && <Typography>Instituição: {formData.instituicao}</Typography>}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );

      case 3:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} sx={{ textAlign: 'center' }}>
              <CheckCircleIcon sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                Solicitação Enviada!
              </Typography>
              <Typography variant="body1" paragraph>
                Sua solicitação de cadastro foi enviada com sucesso.
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                ID da Solicitação: #{solicitacaoId}
              </Typography>
              
              <Alert severity="info" sx={{ mt: 3, textAlign: 'left' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Próximos passos:
                </Typography>
                <Typography variant="body2">
                  1. Nossa equipe irá analisar sua solicitação<br/>
                  2. Verificaremos seus dados profissionais<br/>
                  3. Após aprovação, você receberá um email com suas credenciais temporárias<br/>
                  4. As credenciais serão válidas por 7 dias para avaliação do sistema
                </Typography>
              </Alert>
              
              <Box sx={{ mt: 3 }}>
                <Button
                  variant="outlined"
                  onClick={() => {
                    setActiveStep(0);
                    setFormData({
                      nome: '',
                      email: '',
                      telefone: '',
                      crm: '',
                      uf_crm: '',
                      especialidade: '',
                      instituicao: ''
                    });
                    setSolicitacaoId(null);
                    setSuccess('');
                  }}
                >
                  Nova Solicitação
                </Button>
              </Box>
            </Grid>
          </Grid>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <PersonAddIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Cadastro de Profissionais
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Solicite acesso ao sistema Aracannabis
          </Typography>
        </Box>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 3 }}>
            {success}
          </Alert>
        )}

        {renderStepContent(activeStep)}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            disabled={activeStep === 0 || activeStep === 3}
            onClick={handleBack}
          >
            Voltar
          </Button>
          
          <Box>
            {activeStep === steps.length - 2 ? (
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <EmailIcon />}
              >
                {loading ? 'Enviando...' : 'Enviar Solicitação'}
              </Button>
            ) : activeStep < steps.length - 2 ? (
              <Button
                variant="contained"
                onClick={handleNext}
              >
                Próximo
              </Button>
            ) : null}
          </Box>
        </Box>

        {activeStep < 3 && (
          <Alert severity="info" sx={{ mt: 4 }}>
            <Typography variant="subtitle2" gutterBottom>
              Informações importantes:
            </Typography>
            <Typography variant="body2">
              • Apenas profissionais de saúde com CRM válido podem se cadastrar<br/>
              • Todas as informações serão verificadas antes da aprovação<br/>
              • Após aprovação, você receberá credenciais temporárias válidas por 7 dias<br/>
              • O sistema é destinado ao acompanhamento de pacientes em tratamento com cannabis medicinal
            </Typography>
          </Alert>
        )}
      </Paper>
    </Container>
  );
};

export default CadastroProfissionaisPage;
