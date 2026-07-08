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
  Stepper,
  Step,
  StepLabel,
  CircularProgress,
  Chip,
  Divider
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Email as EmailIcon,
  CheckCircle as CheckCircleIcon
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

// rc.15 — Stepper reduzido de 5 para 4 passos.
// O 'Escolha do Plano' foi REMOVIDO do fluxo de cadastro.
// Novos profissionais entram automaticamente em TRIAL de 14 dias (grátis,
// com todas as funcionalidades) e recebem email com link para /planos
// caso queiram antecipar a escolha.
// O `plano_slug` continua no formData por compatibilidade do backend
// (que aceita e ignora) mas seu valor default agora é null.
const steps = [
  'Dados Pessoais',
  'Dados Profissionais',
  'Confirmação',
  'Aguardar Aprovação'
];

// rc.15 — PLANOS_CADASTRO removido. Plano agora é escolha voluntária
// em /planos após aprovação. Cadastro entra direto em trial 14d.

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
    instituicao: '',
    tipo_vinculo: 'pessoal', // 'pessoal' ou 'existente'
    associacao_id: '',
    plano_slug: null,        // rc.15: trial 14d é o padrão. Plano vira escolha voluntária em /planos.
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

  // rc.15 — Removido fetch de /planos/. Cadastro é livre (trial 14d grátis).
  // Planos ficam disponíveis em /planos após aprovação.

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

      // rc.15 — case 2 (Escolha do Plano) foi removido. Trial 14d é automático.

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
    // rc.15 — Valida passos 0 e 1 antes de enviar. Step 2 (Confirmação)
    // é apenas visual, sem validação própria.
    for (let s = 0; s <= 1; s++) {
      if (!validateStep(s)) return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/cadastro_profissionais/solicitar-cadastro', formData);

      if (response.data.success) {
        setSolicitacaoId(response.data.solicitacao_id);
        setSuccess('Solicitação enviada com sucesso!');
        setActiveStep(3); // rc.15: passo 3 = "Aguardar Aprovação" (era 4)
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

      // rc.15 — case 2 (Escolha do Plano) REMOVIDO. Antigos case 3 e 4
      // viraram case 2 e 3 respectivamente.

      case 2: {
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
                      <strong>Acesso Inicial:</strong>
                    </Typography>
                    <Typography variant="body2">
                      Após aprovação, você terá <strong>14 dias de trial gratuito</strong> com todas as funcionalidades
                      (CRM, prontuário, agenda, módulos). Você poderá assinar um plano a qualquer momento em /planos.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          );
        }

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
                      plano_slug: null,
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
