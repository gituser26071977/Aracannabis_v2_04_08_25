/**
 * SecretariaDashboardPage — Painel principal da Secretária / Equipe.
 *
 * Mostra:
 *  - Saudação com data atual
 *  - Cards de resumo (consultas hoje, pacientes esperados, dispensações pendentes, total)
 *  - Lista da agenda do dia (com botão de check-in)
 *  - Próximas consultas (24h)
 *  - Quick search de pacientes
 *
 * Multi-tenant: o backend filtra por associacao_id automaticamente
 * (header X-Association-ID é injetado pelo secretariaService).
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
    Container, Typography, Box, Grid, Paper, Card, CardContent, Chip,
    Button, CircularProgress, Alert, List, ListItem, ListItemText,
    ListItemSecondaryAction, IconButton, TextField, InputAdornment,
    Divider,
} from '@mui/material';
import EventIcon from '@mui/icons-material/Event';
import PersonIcon from '@mui/icons-material/Person';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import InventoryIcon from '@mui/icons-material/Inventory';
    import SearchIcon from '@mui/icons-material/Search';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import secretariaService from '../services/secretariaService';

const STATUS_COLORS = {
    agendada: 'info',
    confirmada: 'success',
    realizada: 'default',
    cancelada: 'error',
};

const formatTime = (iso) => {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
};

const formatDate = (iso) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
};

const saudacao = () => {
    const h = new Date().getHours();
    if (h < 12) return 'Bom dia';
    if (h < 18) return 'Boa tarde';
    return 'Boa noite';
};

const SummaryCard = ({ icon, title, value, color = 'primary', subtitle }) => (
    <Card sx={{ height: '100%' }}>
        <CardContent>
            <Box display="flex" alignItems="center" mb={1}>
                <Box
                    sx={{
                        bgcolor: `${color}.light`,
                        color: `${color}.dark`,
                        borderRadius: '50%',
                        p: 1,
                        display: 'flex',
                        mr: 1.5,
                    }}
                >
                    {icon}
                </Box>
                <Typography variant="overline" color="text.secondary">
                    {title}
                </Typography>
            </Box>
            <Typography variant="h3" component="div" fontWeight={700}>
                {value}
            </Typography>
            {subtitle && (
                <Typography variant="caption" color="text.secondary">
                    {subtitle}
                </Typography>
            )}
        </CardContent>
    </Card>
);

const SecretariaDashboardPage = () => {
    const { currentUser } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [dashboardData, setDashboardData] = useState(null);
    const [checkinLoading, setCheckinLoading] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [searching, setSearching] = useState(false);

    const carregar = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const data = await secretariaService.getDashboard();
            if (data.success) {
                setDashboardData(data);
            } else {
                setError(data.error || 'Erro ao carregar dashboard.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao carregar dashboard.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        carregar();
    }, [carregar]);

    const handleCheckin = async (consultaId) => {
        setCheckinLoading(consultaId);
        try {
            const res = await secretariaService.checkinConsulta(consultaId);
            if (res.success) {
                await carregar();
            } else {
                setError(res.error || 'Erro no check-in.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Erro no check-in.');
            console.error(err);
        } finally {
            setCheckinLoading(null);
        }
    };

    const handleSearch = async (e) => {
        e?.preventDefault();
        if (!searchQuery || searchQuery.length < 2) {
            setSearchResults([]);
            return;
        }
        setSearching(true);
        try {
            const res = await secretariaService.quickSearchPacientes(searchQuery);
            setSearchResults(res.items || []);
        } catch (err) {
            console.error(err);
        } finally {
            setSearching(false);
        }
    };

    if (loading) {
        return (
            <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
                <CircularProgress />
                <Typography sx={{ mt: 2 }}>Carregando painel...</Typography>
            </Container>
        );
    }

    if (error && !dashboardData) {
        return (
            <Container maxWidth="lg" sx={{ mt: 4 }}>
                <Alert severity="error" onClose={() => setError('')}>
                    {error}
                </Alert>
            </Container>
        );
    }

    const resumo = dashboardData?.resumo || {};

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            {/* Header */}
            <Box mb={3}>
                <Typography variant="h4" component="h1" fontWeight={700}>
                    {saudacao()}, {currentUser?.nome?.split(' ')[0] || 'Secretária'}! 👋
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    {new Date().toLocaleDateString('pt-BR', {
                        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
                    })}
                </Typography>
            </Box>

            {error && (
                <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}

            {/* Cards de Resumo */}
            <Grid container spacing={3} mb={3}>
                <Grid item xs={12} sm={6} md={3}>
                    <SummaryCard
                        icon={<EventIcon />}
                        title="Consultas Hoje"
                        value={resumo.consultas_hoje || 0}
                        color="primary"
                        subtitle={`${resumo.consultas_confirmadas || 0} confirmadas`}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <SummaryCard
                        icon={<PersonIcon />}
                        title="Pacientes Esperados"
                        value={resumo.pacientes_esperados_hoje || 0}
                        color="success"
                        subtitle="Devem chegar hoje"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <SummaryCard
                        icon={<InventoryIcon />}
                        title="Dispensações Pendentes"
                        value={resumo.dispensacoes_pendentes || 0}
                        color="warning"
                        subtitle="Precisam de ação"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <SummaryCard
                        icon={<LocalHospitalIcon />}
                        title="Total Pacientes"
                        value={resumo.total_pacientes_tenant || 0}
                        color="info"
                        subtitle="Da clínica"
                    />
                </Grid>
            </Grid>

            <Grid container spacing={3}>
                {/* Agenda de Hoje */}
                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 2 }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                            <Typography variant="h6">
                                📅 Agenda de Hoje
                            </Typography>
                            <Button size="small" onClick={() => navigate('/secretaria/agenda')}>
                                Ver agenda completa →
                            </Button>
                        </Box>
                        <Divider />
                        {dashboardData?.agenda_hoje?.length === 0 ? (
                            <Box p={3} textAlign="center">
                                <Typography color="text.secondary">
                                    Nenhuma consulta agendada para hoje.
                                </Typography>
                            </Box>
                        ) : (
                            <List dense>
                                {dashboardData?.agenda_hoje?.map((c) => (
                                    <ListItem key={c.id} divider>
                                        <ListItemText
                                            primary={
                                                <Box display="flex" alignItems="center" gap={1}>
                                                    <Typography fontWeight={600}>
                                                        {formatTime(c.data_hora)}
                                                    </Typography>
                                                    <Typography>— {c.paciente_nome || 'Paciente'}</Typography>
                                                    <Chip
                                                        size="small"
                                                        label={c.status}
                                                        color={STATUS_COLORS[c.status] || 'default'}
                                                    />
                                                </Box>
                                            }
                                            secondary={
                                                <Box>
                                                    {c.profissional_nome && (
                                                        <Typography variant="caption" color="text.secondary">
                                                            Dr(a). {c.profissional_nome} • {c.tipo_consulta}
                                                        </Typography>
                                                    )}
                                                    {c.observacoes && (
                                                        <Typography variant="caption" display="block" color="text.secondary">
                                                            {c.observacoes}
                                                        </Typography>
                                                    )}
                                                </Box>
                                            }
                                        />
                                        <ListItemSecondaryAction>
                                            {c.status === 'agendada' && (
                                                <Button
                                                    size="small"
                                                    variant="outlined"
                                                    color="success"
                                                    startIcon={
                                                        checkinLoading === c.id
                                                            ? <CircularProgress size={14} />
                                                            : <CheckCircleIcon />
                                                    }
                                                    onClick={() => handleCheckin(c.id)}
                                                    disabled={checkinLoading !== null}
                                                >
                                                    Check-in
                                                </Button>
                                            )}
                                        </ListItemSecondaryAction>
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </Paper>
                </Grid>

                {/* Sidebar: Quick Search + Próximas */}
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, mb: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            🔍 Buscar Paciente
                        </Typography>
                        <form onSubmit={handleSearch}>
                            <TextField
                                fullWidth
                                size="small"
                                placeholder="Nome ou CPF..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <SearchIcon fontSize="small" />
                                        </InputAdornment>
                                    ),
                                }}
                            />
                        </form>
                        {searching && (
                            <Box display="flex" justifyContent="center" p={1}>
                                <CircularProgress size={20} />
                            </Box>
                        )}
                        {searchResults.length > 0 && (
                            <List dense sx={{ mt: 1 }}>
                                {searchResults.map((p) => (
                                    <ListItem
                                        key={p.id}
                                        button
                                        onClick={() => {
                                            setSearchQuery('');
                                            setSearchResults([]);
                                            navigate(`/pacientes/${p.id}`);
                                        }}
                                    >
                                        <ListItemText
                                            primary={p.nome}
                                            secondary={
                                                p.cpf ? `CPF: ${p.cpf}` :
                                                p.data_nascimento ? formatDate(p.data_nascimento) : '—'
                                            }
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        )}
                        {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
                            <Typography variant="caption" color="text.secondary" sx={{ p: 1, display: 'block' }}>
                                Nenhum paciente encontrado.
                            </Typography>
                        )}
                    </Paper>

                    <Paper sx={{ p: 2 }}>
                        <Typography variant="h6" gutterBottom>
                            ⏰ Próximas Consultas
                        </Typography>
                        <Divider sx={{ mb: 1 }} />
                        {dashboardData?.proximas_consultas?.length === 0 ? (
                            <Typography color="text.secondary" variant="body2" sx={{ p: 1 }}>
                                Sem consultas nas próximas 24h.
                            </Typography>
                        ) : (
                            dashboardData?.proximas_consultas?.map((c) => (
                                <Box key={c.id} py={1} borderBottom="1px solid #eee">
                                    <Typography variant="body2" fontWeight={600}>
                                        {formatTime(c.data_hora)} — {c.paciente_nome || 'Paciente'}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {c.profissional_nome && `Dr(a). ${c.profissional_nome}`}
                                    </Typography>
                                </Box>
                            ))
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Container>
    );
};

export default SecretariaDashboardPage;
