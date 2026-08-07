import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  Drawer,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Avatar,
  Badge,
} from '@mui/material';

// Icons
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import EventIcon from '@mui/icons-material/Event';
import ReceiptIcon from '@mui/icons-material/ReceiptLong';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import SecurityIcon from '@mui/icons-material/Security';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ChatIcon from '@mui/icons-material/Chat';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import SpeedIcon from '@mui/icons-material/Speed';
import SettingsIcon from '@mui/icons-material/Settings';
import BusinessIcon from '@mui/icons-material/Business';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import VerifiedIcon from '@mui/icons-material/Verified';
import ExtensionIcon from '@mui/icons-material/Extension';

// ============================================
// ============================================
// COMPONENTE
// ============================================

const NavigationMenu = ({ open, onClose }) => {
  const location = useLocation();
  const { currentUser, logout, hasClinicaAccess } = useAuth();

  // --- Menu Definitions with emojis ---

  const assistencialItems = [
    { text: '📊 Lista do dia', icon: <SpeedIcon />, path: '/dashboard', auth: true },
    {
      text: '👤 Pacientes',
      icon: <PersonIcon />,
      path: '/pacientes',
      auth: true,
      area: 'assistencial',
    },
    {
      text: '📅 Consultas',
      icon: <EventIcon />,
      path: '/consultas',
      auth: true,
      area: 'assistencial',
    },
    {
      text: '📥 Importar Documentos',
      icon: <PersonAddIcon />,
      path: '/importar-prescricoes',
      auth: true,
      area: 'assistencial',
    },
    {
      text: '📦 Catálogo → Importar por IA',
      icon: <LocalHospitalIcon />,
      path: '/catalogo',
      auth: true,
      area: 'assistencial',
    },
    {
      text: '🧩 Módulos de Especialidade',
      icon: <ExtensionIcon />,
      path: '/modulos',
      auth: true,
      area: 'assistencial',
    },
    {
      text: '🤖 Chat IA (LIA)',
      icon: <ChatIcon />,
      path: '/assistente-ia',
      auth: true,
      area: 'assistencial',
    },
  ];

  const gestaoItems = [
    {
      text: hasClinicaAccess ? '🏥 Gestão da Clínica' : '🔒 Gestão da Clínica',
      icon: <BusinessIcon />,
      path: '/association',
      auth: true,
    },
    {
      text: '💳 Faturamento',
      icon: <ReceiptIcon />,
      path: '/faturamento',
      auth: true,
      area: 'administrativo',
    },
    {
      text: '🧩 Cadastro de pacientes',
      icon: <PersonAddIcon />,
      path: '/onboarding-pacientes',
      auth: true,
      area: 'administrativo',
    },
  ];

  const configItems = [
    {
      text: '📝 Configurar Receituário',
      icon: <LocalHospitalIcon />,
      path: '/configuracao-prescricao',
      auth: true,
      area: 'assistencial',
    },
    {
      text: '⚙️ Configurar IA SDR',
      icon: <SettingsIcon />,
      path: '/configuracao-ia',
      auth: true,
      area: 'administrativo',
    },
    {
      text: '🔧 Config IA',
      icon: <SettingsIcon />,
      path: '/ai-config',
      auth: true,
      adminOnly: true,
    },
    {
      text: '🧠 Dashboard IA',
      icon: <SmartToyIcon />,
      path: '/ai-dashboard',
      auth: true,
      adminOnly: true,
    },
  ];

  const adminItems = [
    { text: '🔐 Admin Geral', icon: <SecurityIcon />, path: '/admin', auth: true, adminOnly: true },
  ];

  const publicItems = [
    { text: '🏠 Início', icon: <HomeIcon />, path: '/', auth: false },
    {
      text: '💎 Assine Agora',
      icon: <MonetizationOnIcon />,
      path: '/planos',
      auth: false,
      hideWhenLoggedIn: true,
    },
    {
      text: '👨‍⚕️ Cadastro Profissional',
      icon: <PersonAddIcon />,
      path: '/cadastro-profissionais',
      auth: false,
      hideWhenLoggedIn: true,
    },
    { text: '🛡️ Segurança', icon: <SecurityIcon />, path: '/seguranca', auth: false },
  ];

  // Build sections
  let sections = [];

  if (!currentUser) {
    sections.push({ title: '🌐 NAVEGAÇÃO', items: publicItems });
  } else {
    // Menu organizado por função: ASSISTENCIAL (atendimento), GESTÃO
    // (operações), CONFIGURAÇÕES (setup) e ADMINISTRAÇÃO (superadmin).
    // A visibilidade continua por perfil (item.area): assistencial vê só o
    // clínico; administrativo vê gestão + configurações; solo vê tudo.
    const ehAdmin = currentUser.role === 'admin' || currentUser.role === 'superadmin';
    const perfil = currentUser?.perfil_efetivo || (ehAdmin ? 'solo' : 'assistencial');
    const podeVer = (item) => {
      if (item.adminOnly && !ehAdmin) return false;
      if (!item.area) return true;
      if (perfil === 'solo') return true;
      return perfil === item.area;
    };
    const grupos = [
      { title: '📋 ASSISTENCIAL', items: assistencialItems },
      { title: '🏥 GESTÃO', items: gestaoItems },
      { title: '⚙️ CONFIGURAÇÕES', items: configItems },
      { title: '🔐 ADMINISTRAÇÃO', items: adminItems },
    ];
    for (const g of grupos) {
      const visiveis = g.items.filter(podeVer);
      if (visiveis.length) sections.push({ title: g.title, items: visiveis });
    }
  }

  const authItems = currentUser
    ? [{ text: '🚪 Sair', icon: <LogoutIcon />, onClick: logout }]
    : [{ text: '🔑 Login', icon: <LoginIcon />, path: '/login' }];

  // User initials for avatar
  const getInitials = (name) => {
    if (!name) return '?';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const isActive = (path) => location.pathname === path;

  return (
    <Drawer
      anchor="left"
      open={open}
      onClose={onClose}
      PaperProps={{
        sx: {
          borderRadius: '0 24px 24px 0',
          overflow: 'hidden',
        },
      }}
    >
      <Box
        sx={{
          width: 300,
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          overflow: 'hidden',
        }}
        role="presentation"
      >
        {/* ===== USER HEADER ===== */}
        {currentUser && (
          <Box
            sx={{
              p: 3,
              pb: 2,
              background: (theme) =>
                `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.light} 100%)`,
              color: '#fff',
              position: 'relative',
              overflow: 'hidden',
              '&::after': {
                content: '""',
                position: 'absolute',
                top: '-50%',
                right: '-30%',
                width: '200px',
                height: '200px',
                background: 'rgba(255,255,255,0.08)',
                borderRadius: '50%',
              },
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                position: 'relative',
                zIndex: 1,
              }}
            >
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                badgeContent={
                  currentUser.role === 'admin' ? (
                    <VerifiedIcon sx={{ fontSize: 16, color: '#ffd700' }} />
                  ) : null
                }
              >
                <Avatar
                  sx={{
                    width: 52,
                    height: 52,
                    bgcolor: 'rgba(255,255,255,0.25)',
                    border: '2px solid rgba(255,255,255,0.4)',
                    fontWeight: 700,
                    fontSize: '1.1rem',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                  }}
                >
                  {getInitials(
                    currentUser.name ||
                      currentUser.nome ||
                      currentUser.usuario ||
                      currentUser.email,
                  )}
                </Avatar>
              </Badge>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography
                  variant="subtitle1"
                  fontWeight={700}
                  noWrap
                  sx={{ textShadow: '0 1px 2px rgba(0,0,0,0.2)' }}
                >
                  {currentUser.name || currentUser.nome || currentUser.usuario || 'Usuário'}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    opacity: 0.85,
                    display: 'block',
                    textOverflow: 'ellipsis',
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {currentUser.email || ''}
                </Typography>
                <Box
                  sx={{
                    mt: 0.5,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 0.5,
                    px: 1,
                    py: 0.25,
                    borderRadius: '10px',
                    bgcolor: 'rgba(255,255,255,0.2)',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  {currentUser.role === 'admin' ? '👑 Admin' : '👨‍⚕️ Profissional'}
                </Box>
              </Box>
            </Box>
          </Box>
        )}

        {/* ===== MENU SECTIONS ===== */}
        <Box sx={{ py: 1, flex: 1, overflowY: 'auto' }}>
          {sections.map((section, sectionIdx) => (
            <Box key={section.title}>
              <Typography
                variant="overline"
                sx={{
                  px: 3,
                  pt: 2,
                  pb: 0.5,
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  letterSpacing: '0.12em',
                  color: 'text.secondary',
                  opacity: 0.7,
                }}
              >
                {section.title}
              </Typography>
              <List dense sx={{ px: 1 }}>
                {section.items
                  .filter((item) => {
                    if (item.auth && !currentUser) return false;
                    if (currentUser && item.hideWhenLoggedIn) return false;
                    if (item.adminOnly && (!currentUser || currentUser.role !== 'admin'))
                      return false;
                    return true;
                  })
                  .map((item) => (
                    <ListItem
                      button
                      key={item.text}
                      component={item.path ? Link : 'div'}
                      to={item.path}
                      selected={isActive(item.path)}
                      onClick={item.onClick || onClose}
                      sx={{
                        borderRadius: '12px',
                        mb: 0.5,
                        mx: 1,
                        py: 1,
                        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                        '&.Mui-selected': {
                          bgcolor: (theme) =>
                            `linear-gradient(90deg, ${theme.palette.primary.main}15 0%, ${theme.palette.primary.light}08 100%)`,
                          borderLeft: (theme) => `3px solid ${theme.palette.primary.main}`,
                          '& .MuiListItemIcon-root': {
                            color: 'primary.main',
                            transform: 'scale(1.1)',
                          },
                          '& .MuiListItemText-primary': {
                            color: 'primary.main',
                            fontWeight: 700,
                          },
                        },
                        '&:hover': {
                          bgcolor: (theme) => `${theme.palette.primary.main}08`,
                          transform: 'translateX(4px)',
                          '& .MuiListItemIcon-root': {
                            transform: 'scale(1.15) rotate(-5deg)',
                            color: 'primary.main',
                          },
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 40,
                          color: 'text.secondary',
                          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={item.text}
                        primaryTypographyProps={{
                          fontSize: '0.9rem',
                          fontWeight: 500,
                          noWrap: true,
                        }}
                      />
                    </ListItem>
                  ))}
              </List>
              {sectionIdx < sections.length - 1 && <Divider sx={{ my: 1, mx: 2 }} />}
            </Box>
          ))}
        </Box>

        <Divider sx={{ my: 1, mx: 2 }} />

        {/* ===== AUTH ITEMS ===== */}
        <List dense sx={{ px: 1, pb: 2, flexShrink: 0 }}>
          {authItems.map((item) => (
            <ListItem
              button
              key={item.text}
              component={item.path ? Link : 'div'}
              to={item.path}
              onClick={() => {
                if (item.onClick) item.onClick();
                onClose();
              }}
              sx={{
                borderRadius: '12px',
                mb: 0.5,
                mx: 1,
                py: 1,
                transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
                '&:hover': {
                  bgcolor: (theme) =>
                    item.text.includes('Sair')
                      ? 'rgba(233,69,96,0.08)'
                      : `${theme.palette.primary.main}08`,
                  transform: 'translateX(4px)',
                  '& .MuiListItemIcon-root': {
                    transform: 'scale(1.15)',
                    color: item.text.includes('Sair') ? 'error.main' : 'primary.main',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: item.text.includes('Sair') ? 'error.main' : 'text.secondary',
                  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.9rem',
                  fontWeight: 500,
                  color: item.text.includes('Sair') ? 'error.main' : 'inherit',
                }}
              />
            </ListItem>
          ))}
        </List>

        {/* ===== FOOTER ===== */}
        <Box
          sx={{
            p: 2,
            pt: 0,
            textAlign: 'center',
            opacity: 0.5,
          }}
        >
          <Typography variant="caption" sx={{ fontSize: '0.65rem', letterSpacing: '0.05em' }}>
            AraOS • Powered by VisualSmartFlow Platform
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};

export default NavigationMenu;
