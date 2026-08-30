import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Grid, Card, CardActionArea, CardContent } from '@mui/material';
import PsychologyIcon from '@mui/icons-material/Psychology';
import {
  MonetizationOn as FinanceIcon,
  Business as GestaoIcon,
  LocalHospital as UnidadeIcon,
  Verified as CertificacaoIcon,
  Security as SegurancaIcon,
  People as UsuariosIcon,
  Inventory as CatalogoIcon,
  CloudUpload as ImportIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const AdminMenuPage = () => {
  const navigate = useNavigate();
  const { currentUser } = useAuth();

  const ehAdmin = currentUser?.role === 'admin' || currentUser?.role === 'superadmin';

  const adminCards = [
    {
      title: '💰 Financeiro',
      description: 'Planos, assinaturas, faturas, relatórios e pagamentos',
      icon: <FinanceIcon sx={{ fontSize: 40 }} />,
      path: '/faturamento',
      adminOnly: false,
    },
    {
      title: '👥 Usuários',
      description: 'Gerenciar usuários e permissões',
      icon: <UsuariosIcon sx={{ fontSize: 40 }} />,
      path: '/admin/usuarios',
      adminOnly: true,
    },
    {
      title: '📥 Importar Prescrições',
      description: 'Importar prescrições em lote',
      icon: <ImportIcon sx={{ fontSize: 40 }} />,
      path: '/importar-prescricoes',
      adminOnly: false,
    },
    {
      title: '📤 Importação Inteligente',
      description: 'Importar dados com IA',
      icon: <ImportIcon sx={{ fontSize: 40 }} />,
      path: '/importar-inteligente',
      adminOnly: false,
    },
    {
      title: '📦 Catálogo de Produtos',
      description: 'Gerenciar catálogo de produtos',
      icon: <CatalogoIcon sx={{ fontSize: 40 }} />,
      path: '/catalogo',
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
      title: '🔐 Certificação Digital',
      description: 'Certificados e assinatura digital',
      icon: <CertificacaoIcon sx={{ fontSize: 40 }} />,
      path: '/certificacao-digital',
      adminOnly: true,
    },
    {
      title: '🤖 Configurar IA',
      description: 'Provedores e modelos de IA',
      icon: <PsychologyIcon sx={{ fontSize: 40 }} />,
      path: '/configurar-ia',
      adminOnly: false,
    },
    {
      title: '🛡️ Segurança & LGPD',
      description: 'Políticas de privacidade e consentimentos',
      icon: <SegurancaIcon sx={{ fontSize: 40 }} />,
      path: '/seguranca',
      adminOnly: false,
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
