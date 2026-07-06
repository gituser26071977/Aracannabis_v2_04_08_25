import React, { useState, useEffect } from 'react';
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
  CardActions,
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
  Chip,
  Divider,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Star as StarIcon,
  Business as BusinessIcon,
  RocketLaunch as RocketIcon
} from '@mui/icons-material';
import api from '../services/api';

const ESTADOS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

const ESPECIALIDADES = [
  'Clínica Médica',
  'Enfermagem',
  'Fisioterapia',
  'Fonoaudiologia',
  'Nutrição',
  'Nutrologia',
  'Odontologia',
  'Psicologia',
  'Serviço Social',
  'Terapia Ocupacional',
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
  'Escolha do Plano',
  'Confirmação',
  'Aguardar Aprovação'
];

// Planos sincronizados com /api/planos/. O slug é a fonte de verdade no backend.
const PLANOS_CADASTRO = [
  {
    slug: 'basico',
    nome: 'Plano Sem IA',
    preco: 99,
    periodo: '/mês',
    cor: '#2196F3',
    icone: <BusinessIcon />,
    descricao: 'Prontuário digital, gestão de pacientes, agenda e LGPD.',
    features: ['Até 100 pacientes', 'Sem IA', '5 GB de armazenamento', 'Suporte por e-mail'],
  },
  {
    slug: 'premium',
    nome: 'Plano Com IA',
    preco: 249,
    periodo: '/mês',
    cor: '#FF9800',
    icone: <RocketIcon />,
    popular: true,
    descricao: 'Tudo do Básico + agentes de IA (EuSouLia), chatbot e dashboard SDR.',
    features: ['Até 500 pacientes', '10 agentes de IA', '10 GB de armazenamento', 'Suporte prioritário'],
  },
  {
    slug: 'enterprise',
    nome: 'Plano Enterprise',
    preco: 499.9,
    periodo: '/mês',
    cor: '#7B1FA2',
    icone: <StarIcon />,
    descricao: 'Clínicas multi-unidade, VSF, reconhecimento facial e métricas avançadas.',
    features: ['Pacientes ilimitados', '50 agentes de IA', '10 GB de armazenamento', 'Onboarding dedicado'],
  },
];

const CadastroProfissionaisPage = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [solicitacaoId, setSolicitacaoId] = useState(null);
  const [planosDb, setPlanosDb] = useState([]);

  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    crm: '',
    uf_crm: '',
    especialidade: '',
    instituicao: '',
    tipo_vinculo: 'pessoal', // 'pessoal' ou 'existente'
    associacao_id: '',
    plano_slug: 'basico',   // padrão: começar com plano mais barato
  });

  const [associacoes, setAssociacoes] = React.useState([]);

  React.useEffect(() => {
    const fetchAssociacoes = async () => {
      try {
        const response = await api.get('/association/list');
        if (response.data.success) {
          setAssociacoes(response.data.associacoes);
        }
      } catch (err) {
        if(process.env.NODE_ENV!=='production')console.error('Erro ao buscar associações:', err);
      }
    };
    fetchAssociacoes();
  }, []);

  // Carrega planos reais do backend (preço, slug, features) para exibir no passo 2.
  React.useEffect(() => {
    let cancelado = false;
    (async () => {
      try {
        const r = await api.get('/planos/');
        if (!cancelado && Array.isArray(r.data) && r.data.length) {
          setPlanosDb(r.data);
          const basico = r.data.find((p) => p.slug === 'basico');
          if (basico) {
            setFormData((prev) => ({ ...prev, plano_slug: basico.slug }));
          }
        }
      } catch (_) {
        // silencioso: usa fallback estático PLANOS_CADASTRO
      }
    })();
    return () => { cancelado = true; };
  }, []);

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
          setError('Número do Registro é obrigatório');
          return false;
        }
        if (!formData.uf_crm) {
          setError('UF do Registro é obrigatória');
          return false;
        }
        if (!formData.especialidade) {
          setError('Especialidade é obrigatória');
          return false;
        }
        break;

      case 2: // Escolha do Plano
        if (!formData.plano_slug) {
          setError('Selecione um plano para continuar');
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
    // Valida todos os passos anteriores antes de enviar
    for (let s = 0; s <= 2; s++) {
      if (!validateStep(s)) return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/cadastro_profissionais/solicitar-cadastro', formData);

      if (response.data.success) {
        setSolicitacaoId(response.data.solicitacao_id);
        setSuccess('Solicitação enviada com sucesso!');
        setActiveStep(4); // passo 4 = "Aguardar Aprovação"
      } else {
        setError(response.data.error || 'Erro ao enviar solicitação');
      }
    } catch (err) {
      if(process.env.NODE_ENV!=='production')console.error('Erro ao solicitar cadastro:', err);
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
                label="Número do Registro (Ex: CRM, COREN, CRP)"
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
                label="UF do Registro"
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
            <Grid item xs={12}>
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                Como deseja atuar?
              </Typography>
              <TextField
                name="tipo_vinculo"
                label="Tipo de Vínculo"
                select
                value={formData.tipo_vinculo}
                onChange={handleInputChange}
                fullWidth
                required
                helperText="Escolha entre criar seu próprio consultório ou se vincular a uma clínica existente."
              >
                <MenuItem value="pessoal">Meu Consultório Virtual (Novo Espaço Personalizado)</MenuItem>
                <MenuItem value="existente">Vincular a uma Clínica/Associação Existente</MenuItem>
              </TextField>
            </Grid>

            {formData.tipo_vinculo === 'existente' && (
              <Grid item xs={12}>
                <TextField
                  name="associacao_id"
                  label="Selecione a Clínica/Associação"
                  select
                  value={formData.associacao_id}
                  onChange={handleInputChange}
                  fullWidth
                  required
                >
                  {associacoes.map((assoc) => (
                    <MenuItem key={assoc.id} value={assoc.id}>
                      {assoc.nome}
                    </MenuItem>
                  ))}
                  {associacoes.length === 0 && (
                    <MenuItem disabled>Nenhuma clínica encontrada</MenuItem>
                  )}
                </TextField>
              </Grid>
            )}
          </Grid>
        );

      case 2:
        {
          // Mescla dados do backend (preço/limites/features) com fallback estático
          const planosParaExibir = planosDb.length
            ? planosDb.map((p) => ({
                slug: p.slug,
                nome: p.nome,
                preco: p.preco_mensal,
                periodo: '/mês',
                cor: p.cor,
                popular: p.is_popular,
                descricao: p.descricao,
                features: [
                  `${p.limite_pacientes >= 99999 ? 'Pacientes ilimitados' : `Até ${p.limite_pacientes} pacientes`}`,
                  p.permite_agentes_sdr
                    ? `${p.limite_agentes_ia} agentes de IA`
                    : 'Sem IA',
                  `${p.limite_armazenamento_mb / 1024} GB de armazenamento`,
                  p.slug === 'enterprise' ? 'Onboarding dedicado' : 'Suporte por e-mail',
                ],
                icone: p.slug === 'enterprise'
                  ? <StarIcon />
                  : p.slug === 'premium'
                  ? <RocketIcon />
                  : <BusinessIcon />,
              }))
            : PLANOS_CADASTRO;

          return (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Escolha o plano ideal para você
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Você poderá fazer upgrade ou downgrade a qualquer momento após o cadastro.
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <FormControl component="fieldset" fullWidth>
                  <RadioGroup
                    name="plano_slug"
                    value={formData.plano_slug}
                    onChange={handleInputChange}
                  >
                    <Grid container spacing={2}>
                      {planosParaExibir.map((plano) => (
                        <Grid item xs={12} md={4} key={plano.slug}>
                          <Card
                            variant={formData.plano_slug === plano.slug ? 'elevation' : 'outlined'}
                            elevation={formData.plano_slug === plano.slug ? 4 : 0}
                            sx={{
                              borderRadius: 3,
                              height: '100%',
                              position: 'relative',
                              border: formData.plano_slug === plano.slug
                                ? `2px solid ${plano.cor}`
                                : '1px solid #e0e0e0',
                              transition: 'all 0.2s ease',
                              '&:hover': { transform: 'translateY(-4px)', boxShadow: 3 },
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
                              <Box sx={{ color: plano.cor, mb: 1 }}>{plano.icone}</Box>
                              <Typography variant="h6" gutterBottom>
                                {plano.nome}
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 1 }}>
                                <Typography variant="h4" fontWeight="bold">
                                  R$ {Number(plano.preco).toFixed(plano.preco % 1 === 0 ? 0 : 2)}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {plano.periodo}
                                </Typography>
                              </Box>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                {plano.descricao}
                              </Typography>
                              <Divider sx={{ my: 1 }} />
                              {plano.features.map((feat, idx) => (
                                <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                                  <CheckCircleIcon sx={{ fontSize: 16, color: plano.cor }} />
                                  <Typography variant="body2">{feat}</Typography>
                                </Box>
                              ))}
                              <FormControlLabel
                                value={plano.slug}
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
        }

      case 3:
        {
          const planoEscolhido = (planosDb.length
            ? planosDb.find((p) => p.slug === formData.plano_slug)
            : PLANOS_CADASTRO.find((p) => p.slug === formData.plano_slug));
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
                    <Typography>Registro (CRM/COREN/etc): {formData.crm}/{formData.uf_crm}</Typography>
                    <Typography>Especialidade/Profissão: {formData.especialidade}</Typography>
                    {formData.instituicao && <Typography>Instituição: {formData.instituicao}</Typography>}

                    <Typography variant="subtitle2" sx={{ mt: 1 }}>
                      Vínculo: {formData.tipo_vinculo === 'pessoal'
                        ? 'Novo Consultório Virtual'
                        : `Vincular a ${associacoes.find(a => a.id === formData.associacao_id)?.nome || 'Associação'}`}
                    </Typography>

                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle1" gutterBottom>
                      <strong>Plano Escolhido:</strong>
                    </Typography>
                    {planoEscolhido ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Chip
                          label={planoEscolhido.nome}
                          sx={{
                            bgcolor: planoEscolhido.cor,
                            color: 'white',
                            fontWeight: 'bold',
                          }}
                          size="small"
                        />
                        <Typography variant="body2">
                          R$ {Number(planoEscolhido.preco).toFixed(planoEscolhido.preco % 1 === 0 ? 0 : 2)}/mês
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">—</Typography>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          );
        }

      case 4:
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
                  1. Nossa equipe irá analisar sua solicitação<br />
                  2. Verificaremos seus dados profissionais<br />
                  3. Após aprovação, você receberá um email com suas credenciais temporárias<br />
                  4. As credenciais serão válidas por 14 dias para avaliação do sistema
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
                      instituicao: '',
                      tipo_vinculo: 'pessoal',
                      associacao_id: '',
                      plano_slug: 'basico',
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
            Solicite acesso ao AraOS — Clinical Intelligence Operating System
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
            disabled={activeStep === 0 || activeStep === 4}
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

        {activeStep < 4 && (
          <Alert severity="info" sx={{ mt: 4 }}>
            <Typography variant="subtitle2" gutterBottom>
              Informações importantes:
            </Typography>
            <Typography variant="body2">
              • Apenas profissionais de saúde com registro ativo (CRM, COREN, CRP, etc) podem se cadastrar<br />
              • Todas as informações serão verificadas junto aos respectivos Conselhos de Classe antes da aprovação<br />
              • Após aprovação, você receberá credenciais temporárias válidas por 14 dias<br />
              • O sistema é destinado ao acompanhamento de pacientes em tratamento com cannabis medicinal
            </Typography>
          </Alert>
        )}
      </Paper>
    </Container>
  );
};

export default CadastroProfissionaisPage;
