import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    Drawer, Box, List, ListItem, ListItemIcon, ListItemText, Typography, Divider, Button
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
import AppsIcon from '@mui/icons-material/Apps';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';

const NavigationMenu = ({ open, onClose }) => {
    const location = useLocation();
    const { currentUser, logout } = useAuth();

    // Helper to determine active module
    const getActiveModule = (pathname) => {
        if (pathname.startsWith('/association')) return 'SGAC';
        if (pathname.startsWith('/cultivo')) return 'SGC';
        // Assume SIAP/Medical for others if logged in and not public pages
        const publicPages = ['/', '/login', '/planos', '/cadastro-profissionais', '/definir-senha', '/seguranca'];
        if (publicPages.some(p => pathname.startsWith(p)) && pathname !== '/') return 'PUBLIC';
        return 'SIAP';
    };

    const activeModule = getActiveModule(location.pathname);

    // --- Menu Definitions ---

    const commonItems = [
        { text: 'DEBUG - MENU', icon: <AppsIcon />, path: '/dashboard', auth: true },
    ];

    const siapItems = [
        { text: 'Dashboard Médico', icon: <SpeedIcon />, path: '/dashboard', auth: true },
        { text: 'Pacientes', icon: <PersonIcon />, path: '/pacientes', auth: true },
        { text: 'Consultas', icon: <EventIcon />, path: '/consultas', auth: true },
        { text: 'Configurar Receituário', icon: <LocalHospitalIcon />, path: '/configuracao-prescricao', auth: true },
        { text: 'Importar Documentos', icon: <PersonAddIcon />, path: '/importar-prescricoes', auth: true },
        { text: 'Assistente IA', icon: <ChatIcon />, path: '/assistente-ia', auth: true },
    ];

    const sgacItems = [
        { text: 'Dashboard Associação', icon: <BusinessIcon />, path: '/association', auth: true },
        // More specific links can be added here if we have detailed routes like /association/members directly accessible
    ];

    const adminItems = [
        { text: 'Admin Geral', icon: <SecurityIcon />, path: '/admin', auth: true, adminOnly: true },
        { text: 'Config IA', icon: <SettingsIcon />, path: '/ai-config', auth: true, adminOnly: true },
        { text: 'Dashboard IA', icon: <SmartToyIcon />, path: '/ai-dashboard', auth: true, adminOnly: true },
    ];

    const publicItems = [
        { text: 'Início', icon: <HomeIcon />, path: '/', auth: false },
        { text: 'Assine Agora', icon: <MonetizationOnIcon />, path: '/planos', auth: false, hideWhenLoggedIn: true },
        { text: 'Cadastro Profissional', icon: <PersonAddIcon />, path: '/cadastro-profissionais', auth: false, hideWhenLoggedIn: true },
        { text: 'Segurança', icon: <SecurityIcon />, path: '/seguranca', auth: false },
    ];

    // Decide which items to show
    let currentItems = [];
    if (!currentUser) {
        currentItems = [...publicItems];
    } else {
        currentItems = [...commonItems]; // Common items (currently empty)

        // Se for admin, garante acesso a todos os módulos, não importa onde esteja
        // "God Mode": Admins veem tudo.
        if (currentUser.role === 'admin') {
            // Reset current items and add everything
            currentItems = [...commonItems, ...siapItems, ...sgacItems, ...adminItems];
        } else {
            // Non-admin logic (Module based)
            if (activeModule === 'SIAP') {
                currentItems = [...currentItems, ...siapItems];
            } else if (activeModule === 'SGAC') {
                currentItems = [...currentItems, ...sgacItems];
            }
            
            // Se o usuário não for admin global, mas estiver no SIAP, 
            // ainda queremos dar a ele a opção de ir para o SGAC se ele tiver permissão de admin em alguma associação.
            // Para simplificar no MVP, se o módulo SGAC estiver visível no dashboard principal, 
            // vamos permitir que profissionais naveguem até lá.
            if (activeModule === 'SIAP' && !currentItems.some(item => item.path === '/association')) {
                // Adicionamos o link para o dashboard da associação se for um profissional querendo gerir sua clínica
                currentItems.push({ text: 'Gestão da Clínica', icon: <BusinessIcon />, path: '/association', auth: true });
            }
        }
    }

    const authItems = currentUser
        ? [{ text: 'Sair', icon: <LogoutIcon />, onClick: logout }]
        : [{ text: 'Login', icon: <LoginIcon />, path: '/login' }];

    return (
        <Drawer anchor="left" open={open} onClose={onClose}>
            <Box sx={{ width: 280 }} role="presentation" onClick={onClose}>

                {currentUser && (
                    <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
                        <Typography variant="subtitle2">Módulo Atual</Typography>
                        <Typography variant="h6" fontWeight="bold">
                            {activeModule === 'SIAP' ? 'Prontuário (SIAP)' :
                                activeModule === 'SGAC' ? 'Associação (SGAC)' :
                                    activeModule === 'SGC' ? 'Cultivo (SGC)' : 'Aracannabis'}
                        </Typography>
                    </Box>
                )}

                <List>
                    {currentItems
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
                                selected={location.pathname === item.path}
                            >
                                <ListItemIcon>{item.icon}</ListItemIcon>
                                <ListItemText primary={item.text} />
                            </ListItem>
                        ))}

                    <Divider sx={{ my: 1 }} />

                    {authItems.map((item) => (
                        <ListItem
                            button
                            key={item.text}
                            component={item.path ? Link : 'div'}
                            to={item.path}
                            onClick={item.onClick}
                        >
                            <ListItemIcon>{item.icon}</ListItemIcon>
                            <ListItemText primary={item.text} />
                        </ListItem>
                    ))}
                </List>
            </Box>
        </Drawer>
    );
};

export default NavigationMenu;
