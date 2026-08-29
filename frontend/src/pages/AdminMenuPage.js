import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Grid, Card, CardActionArea, CardContent } from '@mui/material';
import {
  MonetizationOn as FinanceIcon,
  Business as GestaoIcon,
  LocalHospital as UnidadeIcon,
  PersonAdd as OnboardingIcon,
  Description as RelatoriosIcon,
  Verified as CertificacaoIcon,
  Security as SegurancaIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const AdminMenuPage = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  const ehAdmin = currentUser?.role === 'admin' || currentUser?.role === 'superadmin';

  const adminCards = [
    {
      title: '💰 Financeiro',
      description: 'Planos, assinaturas, faturas e pagamentos',
      icon: <FinanceIcon sx={{ fontSize: 40 }} />,
      path: '/financeiro',
      adminOnly: false,
    },
    {
      title: '📊 Relatórios Financeiros',
      description: 'Relatórios gerenciais e DRE',
      icon: <RelatoriosIcon sx={{ fontSize: 40 }} />,
      path: '/relatorios-financeiros',
      adminOnly: false,
    },
    {
      title: '🏢 Gestão da Clínica',
      description: 'Configurações da clínica e equipe',
      icon: <GestaoIcon sx={{ fontSize: 40 }} />,
      path: '/gestao',
      adminOnly: true,
    },
    {
      title: '🏬 Unidade Física',
      description: 'Configurar salas, andares e setores',
      icon: <UnidadeIcon sx={{ fontSize: 40 }} />,
      path: '/configurar-unidade',
      adminOnly: true,
    },
    {
      title: '📋 Onboarding de Pacientes',
      description: 'Cadastro manual com IA, fila de pendências',
      icon: <OnboardingIcon sx={{ fontSize: 40 }} />,
      path: '/onboarding-pacientes',
      adminOnly: false,
    },
    {
      title: '🤖 Onboarding Inteligente',
      description: 'Upload de docs com IA (câmera/arquivo) — dentro do Agente IA',
      icon: <OnboardingIcon sx={{ fontSize: 40 }} />,
      path: '/assistente-ia',
      adminOnly: false,
    },
    {
      title: '🛡️ Segurança & LGPD',
      description: 'Políticas de privacidade e consentimentos',
      icon: <SegurancaIcon sx={{ fontSize: 40 }} />,
      path: '/seguranca',
      adminOnly: false,
    },
    {
      title: '🔐 Certificação Digital',
      description: 'Certificados e assinatura digital',
      icon: <CertificacaoIcon sx={{ fontSize: 40 }} />,
      path: '/certificacao-digital',
      adminOnly: true,
    },
  ];

  const visibleCards = ehAdmin ? adminCards : adminCards.filter((c) => !c.adminOnly);

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        ⚙️ Menu Administrativo
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Acesso rápido às ferramentas de gestão, finanças e configurações
      </Typography>

      <Grid container spacing={3}>
        {visibleCards.map((card) => (
          <Grid item xs={12} sm={6} md={4} key={card.path}>
            <Card
              elevation={2}
              sx={{
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                  cursor: 'pointer',
                },
              }}
              onClick={() => navigate(card.path)}
            >
              <CardActionArea>
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <Box sx={{ color: 'primary.main', mb: 2 }}>{card.icon}</Box>
                  <Typography variant="h6" gutterBottom>
                    {card.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {card.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default AdminMenuPage;
