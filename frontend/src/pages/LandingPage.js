// AraOS — Landing Page
// Sistema Operacional de Inteligência Clínica
// Paleta: Emerald Cannabis (primary #0d7377, secondary #f5a623)
import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  Stack,
  useTheme,
  alpha,
  Divider,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import {
  RocketLaunch as RocketIcon,
  Security as SecurityIcon,
  Psychology as BrainIcon,
  EventNote as EventIcon,
  Description as RecordIcon,
  Medication as MedIcon,
  Hub as HubIcon,
  Groups as GroupsIcon,
  VerifiedUser as LgpdIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckIcon,
  LocalHospital as HospitalIcon,
  Biotech as CannabisIcon,
  Restaurant as NutritionIcon,
  MonitorHeart as CardioIcon,
  Spa as PsicoIcon,
  Science as ScienceIcon,
  Speed as SpeedIcon,
  Bolt as BoltIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';

// =====================================================================
// ILUSTRAÇÕES SVG inline — mantém a identidade visual e evita 404 de assets
// =====================================================================

const HeroIllustration = () => (
  <svg
    viewBox="0 0 480 360"
    xmlns="http://www.w3.org/2000/svg"
    role="img"
    aria-label="Profissional de saúde com prontuário digital conectado a IA"
    style={{ width: '100%', height: 'auto', maxWidth: 520 }}
  >
    <defs>
      <linearGradient id="bg-grad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="#14a085" />
        <stop offset="100%" stopColor="#0d7377" />
      </linearGradient>
      <linearGradient id="card-grad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#ffffff" />
        <stop offset="100%" stopColor="#f0f4f1" />
      </linearGradient>
      <filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur stdDeviation="6" />
      </filter>
    </defs>

    {/* Background rounded panel */}
    <rect x="20" y="20" width="440" height="320" rx="32" fill="url(#bg-grad)" />
    <circle cx="380" cy="80" r="48" fill="rgba(255,255,255,0.08)" />
    <circle cx="100" cy="280" r="32" fill="rgba(245,166,35,0.18)" />

    {/* Prontuário (card principal) */}
    <g transform="translate(60,70)">
      <rect width="240" height="220" rx="14" fill="url(#card-grad)" filter="url(#soft-shadow)" />
      <rect x="14" y="14" width="60" height="6" rx="3" fill="#0d7377" />
      <rect x="14" y="28" width="120" height="10" rx="2" fill="#1a1f1d" />
      <rect x="14" y="50" width="212" height="6" rx="2" fill="rgba(26,31,29,0.18)" />
      <rect x="14" y="62" width="180" height="6" rx="2" fill="rgba(26,31,29,0.18)" />

      {/* Avatar do paciente */}
      <circle cx="32" cy="100" r="14" fill="#14a085" />
      <rect x="52" y="92" width="100" height="8" rx="2" fill="#1a1f1d" />
      <rect x="52" y="104" width="60" height="6" rx="2" fill="rgba(26,31,29,0.4)" />

      {/* Linha de prescrição */}
      <rect x="14" y="130" width="60" height="20" rx="4" fill="rgba(245,166,35,0.18)" />
      <rect x="80" y="130" width="60" height="20" rx="4" fill="rgba(13,115,119,0.12)" />
      <rect x="146" y="130" width="80" height="20" rx="4" fill="rgba(13,115,119,0.12)" />

      {/* Gráfico (linha) */}
      <polyline
        points="14,180 50,170 80,178 110,160 140,165 170,150 200,156 220,140"
        fill="none"
        stroke="#0d7377"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      <circle cx="220" cy="140" r="4" fill="#f5a623" />
    </g>

    {/* Badge IA (canto superior) */}
    <g transform="translate(310,90)">
      <rect width="110" height="60" rx="12" fill="#f5a623" />
      <circle cx="22" cy="30" r="12" fill="#fff" />
      <text x="22" y="35" textAnchor="middle" fontSize="14" fontWeight="700" fill="#f5a623">
        IA
      </text>
      <text x="42" y="26" fontSize="11" fontWeight="700" fill="#1a1a1a">
        EuSouLia
      </text>
      <text x="42" y="40" fontSize="9" fill="#1a1a1a">
        análise ativa
      </text>
    </g>

    {/* Notificação (canto inferior direito) */}
    <g transform="translate(330,200)">
      <rect width="130" height="50" rx="10" fill="#fff" />
      <circle cx="20" cy="25" r="8" fill="#14a085" />
      <rect x="36" y="14" width="80" height="6" rx="2" fill="#1a1f1d" />
      <rect x="36" y="26" width="60" height="5" rx="2" fill="rgba(26,31,29,0.4)" />
    </g>
  </svg>
);

const SectionDivider = () => (
  <Box
    sx={{
      width: 64,
      height: 4,
      borderRadius: 2,
      background: (t) =>
        `linear-gradient(90deg, ${t.palette.primary.main} 0%, ${t.palette.secondary.main} 100%)`,
      mx: 'auto',
      mb: 2,
    }}
  />
);

const FeatureCard = ({ icon, title, description, accent }) => {
  const theme = useTheme();
  return (
    <Card
      sx={{
        height: '100%',
        borderRadius: 4,
        border: '1px solid',
        borderColor: 'divider',
        transition: 'transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease',
        '&:hover': {
          transform: 'translateY(-6px)',
          boxShadow: theme.shadows[8],
          borderColor: accent || theme.palette.primary.main,
        },
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Box
          sx={{
            width: 56,
            height: 56,
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: alpha(accent || theme.palette.primary.main, 0.12),
            color: accent || theme.palette.primary.main,
            mb: 2,
          }}
        >
          {icon}
        </Box>
        <Typography variant="h6" fontWeight={700} gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
          {description}
        </Typography>
      </CardContent>
    </Card>
  );
};

const PlanCard = ({ plan, popular }) => {
  const theme = useTheme();
  const color = plan.cor || theme.palette.primary.main;
  return (
    <Card
      sx={{
        height: '100%',
        position: 'relative',
        borderRadius: 4,
        border: '2px solid',
        borderColor: popular ? color : 'divider',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
        '&:hover': { transform: 'translateY(-4px)', boxShadow: theme.shadows[6] },
      }}
    >
      {popular && (
        <Chip
          label="Mais popular"
          color="warning"
          size="small"
          sx={{
            position: 'absolute',
            top: 16,
            right: 16,
            fontWeight: 700,
          }}
        />
      )}
      <CardContent sx={{ p: 4 }}>
        <Typography variant="overline" sx={{ color, fontWeight: 700, letterSpacing: 1.5 }}>
          {plan.nome}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'baseline', mt: 1, mb: 2 }}>
          <Typography variant="h3" fontWeight={800}>
            R$ {Number(plan.preco_mensal).toFixed(plan.preco_mensal % 1 === 0 ? 0 : 2)}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
            /mês
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3, minHeight: 48 }}>
          {plan.descricao}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Stack spacing={1.2}>
          {[
            `${plan.limite_pacientes >= 99999 ? 'Pacientes ilimitados' : `Até ${plan.limite_pacientes} pacientes`}`,
            plan.permite_agentes_sdr ? `${plan.limite_agentes_ia} agentes de IA` : 'Sem IA',
            `${Math.round(plan.limite_armazenamento_mb / 1024)} GB de armazenamento`,
            plan.permite_gestao_clinica ? 'Gestão da clínica' : 'Prontuário digital',
            plan.slug === 'enterprise' ? 'Onboarding dedicado' : 'Suporte por e-mail',
          ].map((feat, i) => (
            <Stack key={i} direction="row" spacing={1} alignItems="center">
              <CheckIcon sx={{ fontSize: 18, color }} />
              <Typography variant="body2">{feat}</Typography>
            </Stack>
          ))}
        </Stack>
        <Button
          component={RouterLink}
          to="/cadastro-profissionais"
          variant={popular ? 'contained' : 'outlined'}
          fullWidth
          size="large"
          endIcon={<ArrowForwardIcon />}
          sx={{
            mt: 3,
            bgcolor: popular ? color : 'transparent',
            borderColor: color,
            color: popular ? '#fff' : color,
            '&:hover': {
              bgcolor: popular ? alpha(color, 0.9) : alpha(color, 0.08),
              borderColor: color,
            },
          }}
        >
          Começar com {plan.nome}
        </Button>
      </CardContent>
    </Card>
  );
};

const EspecialidadeCard = ({ icon, name, color }) => (
  <Card
    sx={{
      borderRadius: 3,
      border: '1px solid',
      borderColor: 'divider',
      transition: 'all 0.2s ease',
      '&:hover': { transform: 'translateY(-4px)', borderColor: color, boxShadow: 4 },
    }}
  >
    <CardContent sx={{ textAlign: 'center', py: 3 }}>
      <Box sx={{ color, mb: 1 }}>{icon}</Box>
      <Typography variant="subtitle1" fontWeight={600}>
        {name}
      </Typography>
    </CardContent>
  </Card>
);

const HowItWorksStep = ({ number, title, description }) => {
  const theme = useTheme();
  return (
    <Stack direction="row" spacing={3} alignItems="flex-start">
      <Box
        sx={{
          flexShrink: 0,
          width: 48,
          height: 48,
          borderRadius: '50%',
          bgcolor: theme.palette.primary.main,
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          fontSize: 20,
          boxShadow: theme.shadows[3],
        }}
      >
        {number}
      </Box>
      <Box>
        <Typography variant="h6" fontWeight={700} gutterBottom>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
          {description}
        </Typography>
      </Box>
    </Stack>
  );
};

// =====================================================================
// PÁGINA PRINCIPAL
// =====================================================================

const LandingPage = () => {
  const theme = useTheme();
  const { currentUser } = useAuth();
  const [planos, setPlanos] = useState([]);
  const planosRef = useRef(null);

  useEffect(() => {
    let cancelado = false;
    api
      .get('/planos/')
      .then((r) => {
        if (!cancelado && Array.isArray(r.data)) {
          setPlanos(r.data.filter((p) => p.ativo !== false));
        }
      })
      .catch(() => {});
    return () => {
      cancelado = true;
    };
  }, []);

  const features = [
    {
      icon: <RecordIcon sx={{ fontSize: 32 }} />,
      title: 'Prontuário eletrônico completo',
      description:
        'Histórico clínico estruturado, exames, sintomas, evolução, prescrições e anexos. Tudo em um só lugar, com busca semântica.',
      accent: '#0d7377',
    },
    {
      icon: <EventIcon sx={{ fontSize: 32 }} />,
      title: 'Agenda inteligente',
      description:
        'Confirmação automática via WhatsApp, lembretes, encaixes e sync com Google Calendar. Menos no-show, mais atendimento.',
      accent: '#14a085',
    },
    {
      icon: <BrainIcon sx={{ fontSize: 32 }} />,
      title: 'Agente SDR — EuSouLia',
      description:
        'Triagem 24/7 por WhatsApp, anamnese conversacional e agendamento automático. A IA faz o trabalho pesado, você aprova.',
      accent: '#f5a623',
    },
    {
      icon: <MedIcon sx={{ fontSize: 32 }} />,
      title: 'Prescrição digital',
      description:
        'Modelos por especialidade, controle de posologia, alertas de interação e versão ANVISA/CFM atualizada.',
      accent: '#0d7377',
    },
    {
      icon: <HubIcon sx={{ fontSize: 32 }} />,
      title: 'Multi-clínica e multi-tenant',
      description:
        'Gerencie várias unidades, equipe, secretarias e permissões por perfil. Isolamento total de dados por tenant.',
      accent: '#7B1FA2',
    },
    {
      icon: <LgpdIcon sx={{ fontSize: 32 }} />,
      title: 'LGPD by design',
      description:
        'Criptografia em repouso, anonimização de campos sensíveis, consentimento explícito e trilha de auditoria completa.',
      accent: '#085e61',
    },
  ];

  const especialidades = [
    { name: 'Cannabis Medicinal', icon: <CannabisIcon sx={{ fontSize: 36 }} />, color: '#0d7377' },
    { name: 'Nutrologia', icon: <NutritionIcon sx={{ fontSize: 36 }} />, color: '#f5a623' },
    { name: 'Psiquiatria', icon: <PsicoIcon sx={{ fontSize: 36 }} />, color: '#7B1FA2' },
    { name: 'Cardiologia', icon: <CardioIcon sx={{ fontSize: 36 }} />, color: '#c62828' },
    { name: 'Clínica Médica', icon: <HospitalIcon sx={{ fontSize: 36 }} />, color: '#1565c0' },
    { name: 'Pesquisa Clínica', icon: <ScienceIcon sx={{ fontSize: 36 }} />, color: '#2e7d32' },
  ];

  return (
    <Box sx={{ overflowX: 'hidden', bgcolor: 'background.default' }}>
      {/* ─── HERO ─────────────────────────────────────────────── */}
      <Box
        sx={{
          position: 'relative',
          background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
          color: '#fff',
          pt: { xs: 8, md: 12 },
          pb: { xs: 8, md: 14 },
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: -120,
            right: -120,
            width: 420,
            height: 420,
            borderRadius: '50%',
            bgcolor: alpha('#fff', 0.06),
            zIndex: 0,
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            bottom: -80,
            left: -80,
            width: 240,
            height: 240,
            borderRadius: '50%',
            bgcolor: alpha(theme.palette.secondary.main, 0.18),
            zIndex: 0,
          }}
        />

        <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
          <Grid container spacing={6} alignItems="center">
            <Grid item xs={12} md={7}>
              <Chip
                icon={<BoltIcon sx={{ color: theme.palette.secondary.main }} />}
                label="Inteligência Clínica Operacional"
                sx={{
                  bgcolor: alpha('#fff', 0.12),
                  color: '#fff',
                  fontWeight: 600,
                  mb: 2,
                  backdropFilter: 'blur(8px)',
                }}
              />
              <Typography
                variant="h2"
                fontWeight={800}
                sx={{
                  fontSize: { xs: '2.4rem', md: '3.4rem' },
                  lineHeight: 1.1,
                  textShadow: '0px 2px 12px rgba(0,0,0,0.2)',
                }}
              >
                Prontuário, agenda e IA
                <br />
                em um único sistema.
              </Typography>
              <Typography
                variant="h6"
                sx={{ mt: 3, mb: 4, opacity: 0.92, maxWidth: 580, fontWeight: 400 }}
              >
                O AraOS conecta profissionais de saúde, agentes de IA e fluxos operacionais em uma
                plataforma auditável, em conformidade com a LGPD e desenhada para o dia a dia da sua
                clínica.
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                <Button
                  component={RouterLink}
                  to={currentUser ? '/dashboard' : '/cadastro-profissionais'}
                  variant="contained"
                  color="secondary"
                  size="large"
                  endIcon={<RocketIcon />}
                  sx={{
                    px: 4,
                    py: 1.6,
                    borderRadius: 2,
                    fontSize: '1.05rem',
                    fontWeight: 700,
                    boxShadow: theme.shadows[6],
                  }}
                >
                  {currentUser ? 'Ir para o dashboard' : 'Começar gratuitamente'}
                </Button>
                <Button
                  component={RouterLink}
                  to="/planos"
                  variant="outlined"
                  size="large"
                  endIcon={<ArrowForwardIcon />}
                  sx={{
                    px: 4,
                    py: 1.6,
                    borderRadius: 2,
                    fontSize: '1.05rem',
                    fontWeight: 600,
                    color: '#fff',
                    borderColor: alpha('#fff', 0.5),
                    borderWidth: 2,
                    '&:hover': {
                      borderColor: '#fff',
                      borderWidth: 2,
                      bgcolor: alpha('#fff', 0.08),
                    },
                  }}
                >
                  Ver planos
                </Button>
              </Stack>
              <Typography variant="caption" sx={{ display: 'block', mt: 2, opacity: 0.8 }}>
                14 dias de trial · sem cartão · cancele quando quiser
              </Typography>
            </Grid>

            <Grid item xs={12} md={5} sx={{ display: { xs: 'none', md: 'block' } }}>
              <HeroIllustration />
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* ─── TRUST BAR ───────────────────────────────────────── */}
      <Box sx={{ bgcolor: alpha(theme.palette.primary.main, 0.04), py: 3 }}>
        <Container maxWidth="lg">
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={3}
            alignItems="center"
            justifyContent="center"
            divider={<Divider orientation="vertical" flexItem />}
          >
            {[
              { icon: <LgpdIcon fontSize="small" />, label: 'LGPD compliant' },
              { icon: <SecurityIcon fontSize="small" />, label: 'Auditoria completa' },
              { icon: <GroupsIcon fontSize="small" />, label: 'Multi-tenant' },
              { icon: <SpeedIcon fontSize="small" />, label: '99,9% SLA' },
              { icon: <HospitalIcon fontSize="small" />, label: 'CFM/ANVISA ready' },
            ].map((item) => (
              <Stack key={item.label} direction="row" spacing={1} alignItems="center">
                <Box sx={{ color: theme.palette.primary.main }}>{item.icon}</Box>
                <Typography variant="body2" fontWeight={600} color="text.secondary">
                  {item.label}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Container>
      </Box>

      {/* ─── FEATURES ────────────────────────────────────────── */}
      <Box sx={{ py: { xs: 8, md: 12 } }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 8 }}>
            <SectionDivider />
            <Typography variant="overline" color="primary" fontWeight={700} letterSpacing={2}>
              O QUE O ARAOS FAZ
            </Typography>
            <Typography
              variant="h3"
              fontWeight={800}
              sx={{ mt: 1, fontSize: { xs: '2rem', md: '2.6rem' } }}
            >
              Tudo que sua clínica precisa, em um só lugar
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ mt: 2, maxWidth: 680, mx: 'auto' }}
            >
              Construído para clínicas, consultórios e programas de pesquisa que precisam de
              prontuário sério, automação inteligente e conformidade regulatória desde o dia 1.
            </Typography>
          </Box>
          <Grid container spacing={3}>
            {features.map((f) => (
              <Grid item xs={12} sm={6} md={4} key={f.title}>
                <FeatureCard {...f} />
              </Grid>
            ))}
          </Grid>
        </Container>
      </Box>

      {/* ─── ESPECIALIDADES ─────────────────────────────────── */}
      <Box sx={{ py: { xs: 6, md: 10 }, bgcolor: alpha(theme.palette.primary.main, 0.03) }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 6 }}>
            <SectionDivider />
            <Typography variant="overline" color="primary" fontWeight={700} letterSpacing={2}>
              ESPECIALIDADES
            </Typography>
            <Typography variant="h3" fontWeight={800} sx={{ mt: 1 }}>
              Modelos clínicos prontos para sua área
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
              Workflows e campos específicos para cada especialidade, com trial gratuito de 14 dias.
            </Typography>
          </Box>
          <Grid container spacing={2}>
            {especialidades.map((esp) => (
              <Grid item xs={6} sm={4} md={2} key={esp.name}>
                <EspecialidadeCard {...esp} />
              </Grid>
            ))}
          </Grid>
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Button
              component={RouterLink}
              to="/modulos"
              variant="text"
              color="primary"
              endIcon={<ArrowForwardIcon />}
            >
              Ver todos os módulos
            </Button>
          </Box>
        </Container>
      </Box>

      {/* ─── HOW IT WORKS ──────────────────────────────────── */}
      <Box sx={{ py: { xs: 8, md: 12 } }}>
        <Container maxWidth="md">
          <Box sx={{ textAlign: 'center', mb: 6 }}>
            <SectionDivider />
            <Typography variant="overline" color="primary" fontWeight={700} letterSpacing={2}>
              COMO FUNCIONA
            </Typography>
            <Typography variant="h3" fontWeight={800} sx={{ mt: 1 }}>
              Em 3 passos você está operando
            </Typography>
          </Box>
          <Stack spacing={4}>
            <HowItWorksStep
              number={1}
              title="Crie sua conta de profissional"
              description="Cadastro em menos de 3 minutos. Informe CRM/registro, escolha a especialidade e selecione o plano."
            />
            <HowItWorksStep
              number={2}
              title="Configure sua clínica"
              description="Importe pacientes via planilha, conecte WhatsApp e Google Calendar, ative os módulos de especialidade que quiser."
            />
            <HowItWorksStep
              number={3}
              title="Comece a atender com IA"
              description="A EuSouLia faz a triagem inicial, sua agenda se auto-organiza e o prontuário se preenche enquanto você conversa com o paciente."
            />
          </Stack>
        </Container>
      </Box>

      {/* ─── PRICING ───────────────────────────────────────── */}
      <Box
        ref={planosRef}
        sx={{ py: { xs: 8, md: 12 }, bgcolor: alpha(theme.palette.primary.main, 0.04) }}
      >
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', mb: 6 }}>
            <SectionDivider />
            <Typography variant="overline" color="primary" fontWeight={700} letterSpacing={2}>
              PLANOS
            </Typography>
            <Typography variant="h3" fontWeight={800} sx={{ mt: 1 }}>
              Comece grátis. Cresça quando precisar.
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
              Todos os planos incluem prontuário, agenda, prescrição e suporte LGPD. Faça upgrade a
              qualquer momento.
            </Typography>
          </Box>
          {planos.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6 }}>
              <Typography variant="body2" color="text.secondary">
                Carregando planos…
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={3} alignItems="stretch">
              {planos
                .slice()
                .sort((a, b) => a.preco_mensal - b.preco_mensal)
                .map((plan) => (
                  <Grid item xs={12} md={4} key={plan.id}>
                    <PlanCard plan={plan} popular={plan.is_popular} />
                  </Grid>
                ))}
            </Grid>
          )}
          <Box sx={{ textAlign: 'center', mt: 5 }}>
            <Button
              component={RouterLink}
              to="/planos"
              variant="outlined"
              color="primary"
              size="large"
            >
              Comparar planos em detalhe
            </Button>
          </Box>
        </Container>
      </Box>

      {/* ─── SECURITY / LGPD ──────────────────────────────── */}
      <Box sx={{ py: { xs: 8, md: 10 } }}>
        <Container maxWidth="lg">
          <Card
            sx={{
              borderRadius: 4,
              background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.08)} 0%, ${alpha(theme.palette.secondary.main, 0.08)} 100%)`,
              border: '1px solid',
              borderColor: 'divider',
            }}
          >
            <CardContent sx={{ p: { xs: 4, md: 6 } }}>
              <Grid container spacing={4} alignItems="center">
                <Grid item xs={12} md={2} sx={{ textAlign: 'center' }}>
                  <Box
                    sx={{
                      width: 80,
                      height: 80,
                      borderRadius: '50%',
                      bgcolor: theme.palette.primary.main,
                      color: '#fff',
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <LgpdIcon sx={{ fontSize: 44 }} />
                  </Box>
                </Grid>
                <Grid item xs={12} md={7}>
                  <Typography variant="h5" fontWeight={800} gutterBottom>
                    Segurança e LGPD desde o design
                  </Typography>
                  <Typography variant="body1" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                    Dados criptografados em repouso e em trânsito, anonimização de campos sensíveis,
                    controle granular de consentimento, retenção configurável por tenant e trilha de
                    auditoria completa para fiscalizações do CFM e ANVISA.
                  </Typography>
                </Grid>
                <Grid item xs={12} md={3} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
                  <Button
                    component={RouterLink}
                    to="/seguranca"
                    variant="outlined"
                    color="primary"
                    endIcon={<ArrowForwardIcon />}
                  >
                    Ver política completa
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Container>
      </Box>

      {/* ─── FINAL CTA ────────────────────────────────────── */}
      <Box
        sx={{
          py: { xs: 8, md: 12 },
          background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`,
          color: '#fff',
          textAlign: 'center',
        }}
      >
        <Container maxWidth="md">
          <Typography
            variant="h3"
            fontWeight={800}
            gutterBottom
            sx={{ fontSize: { xs: '2rem', md: '2.6rem' } }}
          >
            Pronto para operar sua clínica com IA?
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9, mb: 4, fontWeight: 400 }}>
            14 dias de trial gratuito. Sem cartão, sem instalação, sem complicação.
          </Typography>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center">
            <Button
              component={RouterLink}
              to="/cadastro-profissionais"
              variant="contained"
              color="secondary"
              size="large"
              endIcon={<RocketIcon />}
              sx={{ px: 4, py: 1.6, fontSize: '1.05rem', fontWeight: 700 }}
            >
              Criar minha conta
            </Button>
            <Button
              component={RouterLink}
              to="/login"
              variant="outlined"
              size="large"
              sx={{
                px: 4,
                py: 1.6,
                fontSize: '1.05rem',
                fontWeight: 600,
                color: '#fff',
                borderColor: alpha('#fff', 0.5),
                borderWidth: 2,
                '&:hover': { borderColor: '#fff', borderWidth: 2, bgcolor: alpha('#fff', 0.08) },
              }}
            >
              Já tenho conta
            </Button>
          </Stack>
        </Container>
      </Box>

      {/* ─── FOOTER ───────────────────────────────────────── */}
      <Box sx={{ bgcolor: '#0a1f1f', color: '#cfd8d8', py: 4 }}>
        <Container maxWidth="lg">
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="h6" fontWeight={800} sx={{ color: '#fff' }}>
                AraOS
              </Typography>
              <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.7 }}>
                Operational Intelligence Infrastructure for Healthcare · parte do ecossistema
                VisualSmartFlow Platform
              </Typography>
            </Grid>
            <Grid item xs={12} md={6} sx={{ textAlign: { xs: 'left', md: 'right' } }}>
              <Stack
                direction="row"
                spacing={3}
                justifyContent={{ xs: 'flex-start', md: 'flex-end' }}
                flexWrap="wrap"
              >
                {[
                  { label: 'Planos', to: '/planos' },
                  { label: 'Cadastro', to: '/cadastro-profissionais' },
                  { label: 'Login', to: '/login' },
                  { label: 'Privacidade', to: '/privacy' },
                ].map((link) => (
                  <Button
                    key={link.label}
                    component={RouterLink}
                    to={link.to}
                    size="small"
                    sx={{ color: '#cfd8d8', '&:hover': { color: '#fff', bgcolor: 'transparent' } }}
                  >
                    {link.label}
                  </Button>
                ))}
              </Stack>
              <Typography variant="caption" sx={{ display: 'block', mt: 1, opacity: 0.6 }}>
                © {new Date().getFullYear()} AraOS · Aracannabis · VisualSmartFlow
              </Typography>
            </Grid>
          </Grid>
        </Container>
      </Box>
    </Box>
  );
};

export default LandingPage;
