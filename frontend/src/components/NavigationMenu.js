import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    Drawer, Box, List, ListItem, ListItemIcon, ListItemText, Typography, Divider, Avatar, Badge
} from '@mui/material';

// Icons
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import EventIcon from '@mui/icons-material/Event';
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

// ============================================
// EMOJIS POR ITEM DE MENU
// ============================================

const emojiMap = {
    'Dashboard': '📊',
    'Pacientes': '👤',
    'Consultas': '📅',
    'Configurar Receituário': '📝',
    'Importar Documentos': '📥',
    'Chat IA (LIA)': '🤖',
    'Configurar IA SDR': '⚙️',
    'Gestão da Clínica': '🏥',
    'Admin Geral': '🔐',
    'Config IA': '🔧',
    'Dashboard IA': '🧠',
    'Início': '🏠',
    'Assine Agora': '💎',
    'Cadastro Profissional': '👨‍⚕️',
    'Segurança': '🛡️',
    'Sair': '🚪',
    'Login': '🔑',
};

const getEmoji = (text) => {
    for (const key of Object.keys(emojiMap)) {
        if (text.includes(key)) return emojiMap[key];
    }
    return '•';
};

// ============================================
// COMPONENTE
// ============================================

const NavigationMenu = ({ open, onClose }) => {
    const location = useLocation();
    const { currentUser, logout, hasClinicaAccess } = useAuth();

    const getActiveModule = (pathname) => {
        if (pathname.startsWith('/association')) return 'SGAC';
        if (pathname.startsWith('/cultivo')) return 'SGC';
        const publicPages = ['/', '/login', '/planos', '/cadastro-profissionais', '/definir-senha', '/seguranca'];
        if (publicPages.some(p => pathname.startsWith(p)) && pathname !== '/') return 'PUBLIC';
        return 'AraOS';
    };

    const activeModule = getActiveModule(location.pathname);

    // --- Menu Definitions with emojis ---

    const commonItems = [
        { text: '🏠 Central de Controle', icon: <SpeedIcon />, path: '/dashboard', auth: true },
    ];

    const siapItems = [
        { text: '📊 Painel de Controle', icon: <SpeedIcon />, path: '/dashboard', auth: true },
        { text: '👤 Pacientes', icon: <PersonIcon />, path: '/pacientes', auth: true },
        { text: '📅 Consultas', icon: <EventIcon />, path: '/consultas', auth: true },
        { text: '📝 Configurar Receituário', icon: <LocalHospitalIcon />, path: '/configuracao-prescricao', auth: true },
        { text: '📥 Importar Documentos', icon: <PersonAddIcon />, path: '/importar-prescricoes', auth: true },
        { text: '🤖 Chat IA (LIA)', icon: <ChatIcon />, path: '/assistente-ia', auth: true },
        { text: '⚙️ Configurar IA SDR', icon: <SettingsIcon />, path: '/configuracao-ia', auth: true },
        { text: '📦 Catálogo → Importar por IA', icon: <LocalHospitalIcon />, path: '/catalogo', auth: true },
    ];

    // Itens do módulo "Gestão da Clínica" (ex-"Associação" / SGAC).
    // O médico/gestor cadastra a clínica e dispara convites via /association.
    // Os endpoints de convite (criar/listar/cancelar/reenviar/aceitar) vivem em
    // routes/secretaria.py e são consumidos por AssociationPage.js.
    // Item mostra 🔒 quando o user está em plano sem acesso (basico).
    const gestaoClinicaItems = [
        {
            text: hasClinicaAccess ? '🏥 Gestão da Clínica' : '🔒 Gestão da Clínica',
            icon: <BusinessIcon />,
            path: '/association',
            auth: true,
        },
    ];

    const adminItems = [
        { text: '🔐 Admin Geral', icon: <SecurityIcon />, path: '/admin', auth: true, adminOnly: true },
        { text: '🔧 Config IA', icon: <SettingsIcon />, path: '/ai-config', auth: true, adminOnly: true },
        { text: '🧠 Dashboard IA', icon: <SmartToyIcon />, path: '/ai-dashboard', auth: true, adminOnly: true },
    ];

    const publicItems = [
        { text: '🏠 Início', icon: <HomeIcon />, path: '/', auth: false },
        { text: '💎 Assine Agora', icon: <MonetizationOnIcon />, path: '/planos', auth: false, hideWhenLoggedIn: true },
        { text: '👨‍⚕️ Cadastro Profissional', icon: <PersonAddIcon />, path: '/cadastro-profissionais', auth: false, hideWhenLoggedIn: true },
        { text: '🛡️ Segurança', icon: <SecurityIcon />, path: '/seguranca', auth: false },
    ];

    // Build sections
    let sections = [];

    if (!currentUser) {
        sections.push({ title: '🌐 NAVEGAÇÃO', items: publicItems });
    } else {
        // AraOS Section — remove [...commonItems, ...] (era redundante: ambos → /dashboard).
        // Mantemos apenas siapItems, cujo 1º item agora é "Painel de Controle".
        const siapSectionItems = [...siapItems];
        sections.push({ title: '📋 PRONTUÁRIO', items: siapSectionItems });

        // Gestão da Clínica — visível para qualquer usuário autenticado.
        // O /association hospeda o cadastro da clínica E o diálogo de convite
        // (criar/listar/cancelar/reenviar). Endpoints em routes/secretaria.py.
        if (currentUser) {
            sections.push({ title: '🏥 GESTÃO DA CLÍNICA', items: [...gestaoClinicaItems] });
        }

        // Admin Section
        if (currentUser.role === 'admin') {
            sections.push({ title: '⚙️ ADMINISTRAÇÃO', items: adminItems });
        }
    }

    const authItems = currentUser
        ? [{ text: '🚪 Sair', icon: <LogoutIcon />, onClick: logout }]
        : [{ text: '🔑 Login', icon: <LoginIcon />, path: '/login' }];

    // User initials for avatar
    const getInitials = (name) => {
        if (!name) return '?';
        return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
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
                }
            }}
        >
            <Box sx={{ width: 300 }} role="presentation">

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
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, position: 'relative', zIndex: 1 }}>
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
                                    {getInitials(currentUser.name || currentUser.nome || currentUser.usuario || currentUser.email)}
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
                <Box sx={{ py: 1 }}>
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
                                    .filter(item => {
                                        if (item.auth && !currentUser) return false;
                                        if (currentUser && item.hideWhenLoggedIn) return false;
                                        if (item.adminOnly && (!currentUser || currentUser.role !== 'admin')) return false;
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
                                                    bgcolor: (theme) =>
                                                        `${theme.palette.primary.main}08`,
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
                            {sectionIdx < sections.length - 1 && (
                                <Divider sx={{ my: 1, mx: 2 }} />
                            )}
                        </Box>
                    ))}
                </Box>

                <Divider sx={{ my: 1, mx: 2 }} />

                {/* ===== AUTH ITEMS ===== */}
                <List dense sx={{ px: 1, pb: 2 }}>
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
