import React, { useState, useEffect } from 'react';
import {
    Container,
    Grid,
    Card,
    CardContent,
    Typography,
    Button,
    Box,
    Avatar,
    List,
    ListItem,
    ListItemText,
    Chip,
    AppBar,
    Toolbar,
    IconButton,
    Menu,
    MenuItem
} from '@mui/material';
import {
    AccountCircle,
    LocalHospital,
    Assignment,
    LocalPharmacy,
    Biotech,
    Logout
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

const PatientDashboard = () => {
    const navigate = useNavigate();
    const [patient, setPatient] = useState(null);
    const [stats, setStats] = useState(null);
    const [recentConsultations, setRecentConsultations] = useState([]);
    const [anchorEl, setAnchorEl] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadPatientData();
    }, []);

    const loadPatientData = async () => {
        try {
            // Carregar perfil
            const profileRes = await api.get('/patient-portal/me');
            setPatient(profileRes.data);

            // Carregar estatísticas
            const statsRes = await api.get('/patient-portal/me/stats');
            setStats(statsRes.data);

            // Carregar consultas recentes
            const consultasRes = await api.get('/patient-portal/me/consultas?limit=5');
            setRecentConsultations(consultasRes.data.consultas);

            setLoading(false);
        } catch (error) {
            console.error('Erro ao carregar dados:', error);
            if (error.response?.status === 401 || error.response?.status === 403) {
                // Token inválido ou não é paciente
                handleLogout();
            }
        }
    };

    const handleMenuOpen = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('userType');
        localStorage.removeItem('user');
        navigate('/patient/login');
    };

    if (loading || !patient) {
        return (
            <Container maxWidth="lg" sx={{ mt: 4 }}>
                <Typography>Carregando...</Typography>
            </Container>
        );
    }

    return (
        <>
            {/* Navbar */}
            <AppBar position="static">
                <Toolbar>
                    <LocalHospital sx={{ mr: 2 }} />
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        Portal do Paciente — AraOS
                    </Typography>

                    <IconButton
                        size="large"
                        edge="end"
                        color="inherit"
                        onClick={handleMenuOpen}
                    >
                        <AccountCircle />
                    </IconButton>

                    <Menu
                        anchorEl={anchorEl}
                        open={Boolean(anchorEl)}
                        onClose={handleMenuClose}
                    >
                        <MenuItem onClick={() => { navigate('/patient/profile'); handleMenuClose(); }}>
                            Meu Perfil
                        </MenuItem>
                        <MenuItem onClick={handleLogout}>
                            <Logout sx={{ mr: 1 }} /> Sair
                        </MenuItem>
                    </Menu>
                </Toolbar>
            </AppBar>

            {/* Dashboard Content */}
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                {/* Header */}
                <Box sx={{ mb: 4 }}>
                    <Typography variant="h4" gutterBottom>
                        Bem-vindo(a), {patient.nome}!
                    </Typography>
                    <Typography variant="body1" color="textSecondary">
                        Aqui você pode acess ar todo seu histórico médico
                    </Typography>
                </Box>

                {/* Stats Cards */}
                <Grid container spacing={3} sx={{ mb: 4 }}>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    <Assignment color="primary" sx={{ mr: 1 }} />
                                    <Typography variant="h6">Consultas</Typography>
                                </Box>
                                <Typography variant="h3">{stats?.total_consultas || 0}</Typography>
                                <Typography variant="body2" color="textSecondary">
                                    Total realizadas
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    <LocalPharmacy color="success" sx={{ mr: 1 }} />
                                    <Typography variant="h6">Prescrições</Typography>
                                </Box>
                                <Typography variant="h3">{stats?.prescricoes_ativas || 0}</Typography>
                                <Typography variant="body2" color="textSecondary">
                                    Ativas no momento
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    <Biotech color="info" sx={{ mr: 1 }} />
                                    <Typography variant="h6">Exames</Typography>
                                </Box>
                                <Typography variant="h3">{stats?.total_exames || 0}</Typography>
                                <Typography variant="body2" color="textSecondary">
                                    Realizados
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>Próxima Consulta</Typography>
                                {stats?.proxima_consulta ? (
                                    <>
                                        <Typography variant="body1">
                                            {new Date(stats.proxima_consulta.data).toLocaleDateString('pt-BR')}
                                        </Typography>
                                        <Typography variant="body2" color="textSecondary">
                                            {stats.proxima_consulta.tipo || 'Consulta'}
                                        </Typography>
                                    </>
                                ) : (
                                    <Typography variant="body2" color="textSecondary">
                                        Nenhuma agendada
                                    </Typography>
                                )}
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Quick Actions */}
                <Grid container spacing={3}>
                    <Grid item xs={12} md={8}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Consultas Recentes
                                </Typography>

                                {recentConsultations.length > 0 ? (
                                    <List>
                                        {recentConsultations.map((consulta) => (
                                            <ListItem key={consulta.id} divider>
                                                <ListItemText
                                                    primary={consulta.tipo || 'Consulta'}
                                                    secondary={`${new Date(consulta.data).toLocaleDateString('pt-BR')} - ${consulta.observacoes || 'Sem observações'}`}
                                                />
                                                <Chip
                                                    label={consulta.status || 'Realizada'}
                                                    size="small"
                                                    color="success"
                                                />
                                            </ListItem>
                                        ))}
                                    </List>
                                ) : (
                                    <Typography variant="body2" color="textSecondary">
                                        Nenhuma consulta registrada
                                    </Typography>
                                )}

                                <Button
                                    fullWidth
                                    sx={{ mt: 2 }}
                                    onClick={() => navigate('/patient/consultas')}
                                >
                                    Ver Todas as Consultas
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>

                    <Grid item xs={12} md={4}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Ações Rápidas
                                </Typography>

                                <Button
                                    fullWidth
                                    variant="contained"
                                    startIcon={<Assignment />}
                                    sx={{ mb: 2 }}
                                    onClick={() => navigate('/patient/prontuario')}
                                >
                                    Ver Prontuário
                                </Button>

                                <Button
                                    fullWidth
                                    variant="outlined"
                                    startIcon={<LocalPharmacy />}
                                    sx={{ mb: 2 }}
                                    onClick={() => navigate('/patient/prescricoes')}
                                >
                                    Minhas Prescrições
                                </Button>

                                <Button
                                    fullWidth
                                    variant="outlined"
                                    startIcon={<Biotech />}
                                    onClick={() => navigate('/patient/exames')}
                                >
                                    Meus Exames
                                </Button>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Container>
        </>
    );
};

export default PatientDashboard;
