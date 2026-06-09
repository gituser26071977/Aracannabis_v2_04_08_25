import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Grid,
  MenuItem,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  Divider,
  Chip
} from '@mui/material';
import {
  Save as SaveIcon,
  CheckCircle as CheckCircleIcon,
  WorkspacePremium as PremiumIcon,
  Star as StarIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import OnboardingStepper from '../components/OnboardingStepper';
import api from '../services/api';

const ESPECIALIDADES = [
  'Clínica Médica', 'Neurologia', 'Psiquiatria', 'Oncologia',
  'Cardiologia', 'Endocrinologia', 'Gastroenterologia', 'Reumatologia',
  'Dermatologia', 'Ortopedia', 'Anestesiologia', 'Medicina da Dor',
  'Medicina Paliativa', 'Outras'
];

const TIMEZONES = [
  'America/Sao_Paulo', 'America/Rio_de_Janeiro', 'America/Bahia',
  'America/Fortaleza', 'America/Recife', 'America/Belem', 'America/Manaus'
];

const PLANOS = [
  {
    id: 'trial',
    nome: 'Trial Gratuito',
    preco: 'R$ 0',
    periodo: '/7 dias',
    descricao: 'Acesso completo por 7 dias para testar todas as funcionalidades.',
    features: ['Pacientes ilimitados', 'IA Assistida', 'Relatórios', 'Suporte por email'],
    cor: '#4CAF50',
    icone: <StarIcon />
  },
  {
    id: 'basico',
    nome: 'Plano Básico',
    preco: 'R$ 99',
    periodo: '/mês',
    descricao: 'Ideal para profissionais individuais que estão começando.',
    features: ['Até 50 pacientes', 'Sem IA', 'Relatórios básicos', 'Suporte por email'],
    cor: '#2196F3',
    icone: <BusinessIcon />
  },
  {
    id: 'profissional',
    nome: 'Plano Profissional',
    preco: 'R$ 250',
    periodo: '/mês',
    descricao: 'Para clínicas e consultórios que precisam de mais poder.',
    features: ['Pacientes ilimitados', 'IA Completa', 'Relatórios avançados', 'Suporte prioritário'],
    cor: '#FF9800',
    icone: <PremiumIcon />,
    popular: true
  }
];

const OnboardingPage = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState({
    step1: { nome: '', cpf: '', crm: '', uf_crm: '', especialidade: '' },
    step2: { nome_clinica: '', cnpj: '', endereco: '', telefone_clinica: '' },
    step3: { timezone: 'America/Sao_Paulo', cor_tema: '#0d7377', logo: '' },
    step4: { plano_id: 'trial' }
  });

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const response = await api.get('/onboarding/status');
        if (response.data.progress) {
          const prog = response.data.progress;
          setActiveStep(prog.current_step || 1);
          setFormData(prev => ({
            step1: prog.step_1_data || prev.step1,
            step2: prog.step_2_data || prev.step2,
            step3: prog.step_3_data || prev.step3,
            step4: prog.step_4_data || prev.step4,
          }));
        }
        if (response.data.onboarding_completed) {
          navigate('/dashboard');
        }
      } catch (err) {
        console.error('Erro ao buscar progresso:', err);
        // Se onboarding está desabilitado (403) ou outro erro, redirecionar para dashboard
        if (err.response?.status === 403 || err.response?.status >= 500) {
          navigate('/dashboard');
          return;
        }
      }
    };
    fetchProgress();
  }, [navigate]);

  const handleInputChange = (step, field, value) => {
    setFormData(prev => ({
      ...prev,
      [step]: { ...prev[step], [field]: value }
    }));
    setError('');
  };

  const validateStep = (step) => {
    switch (step) {
      case 1:
        if (!formData.step1.nome.trim()) return 'Nome é obrigatório';
        if (!formData.step1.cpf.trim()) return 'CPF é obrigatório';
        if (!formData.step1.crm.trim()) return 'CRM é obrigatório';
        if (!formData.step1.uf_crm.trim()) return 'UF do CRM é obrigatória';
        if (!formData.step1.especialidade) return 'Especialidade é obrigatória';
        break;
      case 2:
        if (!formData.step2.nome_clinica.trim()) return 'Nome da clínica é obrigatório';
        if (!formData.step2.endereco.trim()) return 'Endereço é obrigatório';
        if (!formData.step2.telefone_clinica.trim()) return 'Telefone da clínica é obrigatório';
        break;
      case 3:
        if (!formData.step3.timezone) return 'Timezone é obrigatório';
        break;
      case 4:
        if (!formData.step4.plano_id) return 'Escolha um plano';
        break;
      default:
        break;
    }
    return null;
  };

  const saveStep = async (stepNumber) => {
    const validationError = validateStep(stepNumber);
    if (validationError) {
      setError(validationError);
      return false;
    }

    setSaving(true);
    try {
      const stepKey = `step${stepNumber}`;
      await api.post(`/onboarding/step/${stepNumber}`, { data: formData[stepKey] });
      setSuccess('Progresso salvo!');
      setTimeout(() => setSuccess(''), 2000);
      return true;
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao salvar progresso');
      return false;
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    const saved = await saveStep(activeStep);
    if (saved && activeStep < 4) {
      setActiveStep(prev => prev + 1);
    } else if (saved && activeStep === 4) {
      handleFinish();
    }
  };

  const handleBack = () => {
    if (activeStep > 1) {
      setActiveStep(prev => prev - 1);
    }
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      await api.post('/onboarding/skip');
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Erro ao finalizar onboarding');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Dados Pessoais
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Preencha seus dados profissionais para personalizarmos sua experiência.
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Nome Completo"
                value={formData.step1.nome}
                onChange={(e) => handleInputChange('step1', 'nome', e.target.value)}
                fullWidth
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="CPF"
                value={formData.step1.cpf}
                onChange={(e) => handleInputChange('step1', 'cpf', e.target.value)}
                fullWidth
                required
                placeholder="000.000.000-00"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="CRM"
                value={formData.step1.crm}
                onChange={(e) => handleInputChange('step1', 'crm', e.target.value)}
                fullWidth
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="UF do CRM"
                select
                value={formData.step1.uf_crm}
                onChange={(e) => handleInputChange('step1', 'uf_crm', e.target.value)}
                fullWidth
                required
              >
                {['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'].map(uf => (
                  <MenuItem key={uf} value={uf}>{uf}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Especialidade"
                select
                value={formData.step1.especialidade}
                onChange={(e) => handleInputChange('step1', 'especialidade', e.target.value)}
                fullWidth
                required
              >
                {ESPECIALIDADES.map(esp => (
                  <MenuItem key={esp} value={esp}>{esp}</MenuItem>
                ))}
              </TextField>
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Dados da Clínica
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Informe os dados do seu consultório ou clínica.
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Nome da Clínica / Consultório"
                value={formData.step2.nome_clinica}
                onChange={(e) => handleInputChange('step2', 'nome_clinica', e.target.value)}
                fullWidth
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="CNPJ (opcional)"
                value={formData.step2.cnpj}
                onChange={(e) => handleInputChange('step2', 'cnpj', e.target.value)}
                fullWidth
                placeholder="00.000.000/0000-00"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Telefone da Clínica"
                value={formData.step2.telefone_clinica}
                onChange={(e) => handleInputChange('step2', 'telefone_clinica', e.target.value)}
                fullWidth
                required
                placeholder="(11) 99999-9999"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Endereço Completo"
                value={formData.step2.endereco}
                onChange={(e) => handleInputChange('step2', 'endereco', e.target.value)}
                fullWidth
                required
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        );

      case 3:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Configurações
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Personalize o sistema de acordo com suas preferências.
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Fuso Horário"
                select
                value={formData.step3.timezone}
                onChange={(e) => handleInputChange('step3', 'timezone', e.target.value)}
                fullWidth
                required
              >
                {TIMEZONES.map(tz => (
                  <MenuItem key={tz} value={tz}>{tz}</MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                label="Cor do Tema"
                type="color"
                value={formData.step3.cor_tema}
                onChange={(e) => handleInputChange('step3', 'cor_tema', e.target.value)}
                fullWidth
                required
                helperText="Escolha a cor principal do sistema"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="URL do Logo (opcional)"
                value={formData.step3.logo}
                onChange={(e) => handleInputChange('step3', 'logo', e.target.value)}
                fullWidth
                placeholder="https://seusite.com/logo.png"
              />
            </Grid>
          </Grid>
        );

      case 4:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Escolha do Plano
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Selecione o plano ideal para você. Comece com o trial gratuito de 7 dias.
              </Typography>
            </Grid>
            <Grid item xs={12}>
              <FormControl component="fieldset" fullWidth>
                <RadioGroup
                  value={formData.step4.plano_id}
                  onChange={(e) => handleInputChange('step4', 'plano_id', e.target.value)}
                >
                  <Grid container spacing={3}>
                    {PLANOS.map((plano) => (
                      <Grid item xs={12} md={4} key={plano.id}>
                        <Card
                          variant={formData.step4.plano_id === plano.id ? 'elevation' : 'outlined'}
                          elevation={formData.step4.plano_id === plano.id ? 4 : 0}
                          sx={{
                            border: formData.step4.plano_id === plano.id ? `2px solid ${plano.cor}` : '1px solid #e0e0e0',
                            borderRadius: 3,
                            height: '100%',
                            position: 'relative',
                            transition: 'all 0.3s ease',
                            '&:hover': { transform: 'translateY(-4px)', boxShadow: 3 }
                          }}
                        >
                          {plano.popular && (
                            <Chip
                              label="Mais Popular"
                              color="warning"
                              size="small"
                              sx={{ position: 'absolute', top: 12, right: 12 }}
                            />
                          )}
                          <CardContent>
                            <Box sx={{ color: plano.cor, mb: 1 }}>
                              {plano.icone}
                            </Box>
                            <Typography variant="h6" gutterBottom>
                              {plano.nome}
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 2 }}>
                              <Typography variant="h4" fontWeight="bold">
                                {plano.preco}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {plano.periodo}
                              </Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                              {plano.descricao}
                            </Typography>
                            <Divider sx={{ my: 1.5 }} />
                            {plano.features.map((feature, idx) => (
                              <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                <CheckCircleIcon sx={{ fontSize: 16, color: plano.cor }} />
                                <Typography variant="body2">{feature}</Typography>
                              </Box>
                            ))}
                            <FormControlLabel
                              value={plano.id}
                              control={<Radio />}
                              label="Selecionar"
                              sx={{ mt: 2 }}
                            />
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </RadioGroup>
              </FormControl>
            </Grid>
          </Grid>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={2} sx={{ p: { xs: 2, sm: 4 }, borderRadius: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h4" gutterBottom fontWeight={700}>
            AraOS — Clinical Intelligence Operating System
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Vamos configurar sua conta em poucos passos
          </Typography>
        </Box>

        <OnboardingStepper activeStep={activeStep} />

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

        <Box sx={{ mb: 4 }}>
          {renderStepContent()}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button
            onClick={handleBack}
            disabled={activeStep === 1 || loading}
            variant="outlined"
          >
            Voltar
          </Button>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              onClick={() => saveStep(activeStep)}
              disabled={saving}
              variant="outlined"
              startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
            >
              Salvar
            </Button>
            <Button
              onClick={handleNext}
              disabled={loading}
              variant="contained"
              endIcon={activeStep === 4 ? <CheckCircleIcon /> : null}
            >
              {loading ? <CircularProgress size={20} /> : activeStep === 4 ? 'Finalizar' : 'Próximo'}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default OnboardingPage;
