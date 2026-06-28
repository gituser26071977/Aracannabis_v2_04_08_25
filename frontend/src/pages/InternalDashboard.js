import React, { useEffect, useState } from 'react';
import {
    Box,
    Grid,
    Paper,
    Typography,
    CircularProgress,
    Card,
    CardContent,
    LinearProgress,
    useTheme,
    Alert,
    Avatar,
    Chip
} from '@mui/material';
import {
    People as PeopleIcon,
    LocalHospital as TreatmentIcon,
    TrendingUp as ImprovementIcon,
    Timer as StableIcon
} from '@mui/icons-material';
import {
    PieChart,
    Pie,
    Cell,
    Tooltip as RechartsTooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import { dashboardService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import QuickActionsBar from '../components/QuickActionsBar';
import {
  PersonAdd as PersonAddIcon,
  Event as EventIcon,
  SmartToy as SmartToyIcon,
  AssignmentInd as AssignmentIndIcon,
} from '@mui/icons-material';

// ============================================
// GLASS STAT CARD
// ============================================

const StatCard = ({ title, value, subtitle, icon, emoji, color, loading, delay = 0 }) => {
    const theme = useTheme();
    const isLight = theme.palette.mode === 'light';

    return (
        <Card
            sx={{
                height: '100%',
                position: 'relative',
                overflow: 'visible',
                background: isLight
                    ? 'rgba(255, 255, 255, 0.72)'
                    : 'rgba(26, 31, 29, 0.72)',
                backdropFilter: 'blur(12px)',
                borderRadius: '20px',
                border: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                boxShadow: isLight
                    ? '0 8px 32px rgba(0,0,0,0.06)'
                    : '0 8px 32px rgba(0,0,0,0.20)',
                transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                animation: `fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${delay}s both`,
                '@keyframes fadeInUp': {
                    from: { opacity: 0, transform: 'translateY(20px)' },
                    to: { opacity: 1, transform: 'translateY(0)' },
                },
                '&:hover': {
                    transform: 'translateY(-6px)',
                    boxShadow: isLight
                        ? '0 20px 40px rgba(0,0,0,0.10)'
                        : '0 20px 40px rgba(0,0,0,0.30)',
                },
            }}
        >
            <CardContent sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Avatar
                        sx={{
                            bgcolor: `${color}18`,
                            color: color,
                            width: 52,
                            height: 52,
                            fontSize: '1.5rem',
                            boxShadow: `0 4px 12px ${color}25`,
                            transition: 'all 0.3s ease',
                        }}
                    >
                        {emoji}
                    </Avatar>
                    {loading && <CircularProgress size={20} thickness={4} />}
                </Box>
                <Typography
                    variant="h3"
                    fontWeight={800}
                    sx={{
                        mb: 0.5,
                        background: `linear-gradient(135deg, ${color} 0%, ${color}dd 100%)`,
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        fontSize: { xs: '1.8rem', sm: '2.2rem' },
                    }}
                >
                    {value}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.7, fontWeight: 500 }}>
                    {title}
                </Typography>
                {subtitle && (
                    <Chip
                        size="small"
                        label={subtitle}
                        sx={{
                            mt: 1.5,
                            bgcolor: `${color}12`,
                            color: color,
                            fontWeight: 600,
                            fontSize: '0.7rem',
                            height: 24,
                            '& .MuiChip-label': {
                                px: 1,
                            },
                        }}
                    />
                )}
            </CardContent>
        </Card>
    );
};

// ============================================
// GLASS PAPER (Chart Container)
// ============================================

const GlassPaper = ({ children, sx = {}, delay = 0 }) => {
    const theme = useTheme();
    const isLight = theme.palette.mode === 'light';

    return (
        <Paper
            sx={{
                p: { xs: 2, sm: 3 },
                background: isLight
                    ? 'rgba(255, 255, 255, 0.72)'
                    : 'rgba(26, 31, 29, 0.72)',
                backdropFilter: 'blur(12px)',
                borderRadius: '20px',
                border: `1px solid ${isLight ? 'rgba(13,115,119,0.08)' : 'rgba(0,212,170,0.08)'}`,
                boxShadow: isLight
                    ? '0 8px 32px rgba(0,0,0,0.06)'
                    : '0 8px 32px rgba(0,0,0,0.20)',
                animation: `fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${delay}s both`,
                '@keyframes fadeInUp': {
                    from: { opacity: 0, transform: 'translateY(20px)' },
                    to: { opacity: 1, transform: 'translateY(0)' },
                },
                ...sx,
            }}
        >
            {children}
        </Paper>
    );
};

// ============================================
// MAIN DASHBOARD
// ============================================

const InternalDashboard = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const { currentUser } = useAuth();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const data = await dashboardService.getStats();
            setStats(data);
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error('Erro ao carregar dashboard:', err);
            setError('Falha ao carregar métricas.');
        } finally {
            setLoading(false);
        }
    };

    const COLORS = ['#0d7377', '#14a085', '#f5a623', '#e94560', '#2ecc71', '#8884d8'];

    if (loading && !stats) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
                <CircularProgress size={48} thickness={4} />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ mt: 2 }}>
                {error}
            </Alert>
        );
    }

    return (
        <Box sx={{ flexGrow: 1, py: { xs: 1, sm: 2 } }}>
            {/* Quick Actions */}
            <QuickActionsBar
                title="Acesso Rápido"
                actions={[
                    { label: 'Novo Paciente', description: 'Cadastrar prontuário', icon: <PersonAddIcon />, onClick: () => navigate('/pacientes') },
                    { label: 'Nova Consulta', description: 'Agendar no calendário', icon: <EventIcon />, onClick: () => navigate('/consultas') },
                    { label: 'Chat IA', description: 'Assistente multiagente', icon: <SmartToyIcon />, onClick: () => navigate('/ai-chat'), color: 'success.main' },
                    { label: 'Meus Pacientes', description: 'Lista de prontuários', icon: <AssignmentIndIcon />, onClick: () => navigate('/pacientes') },
                ]}
            />

            {/* Header */}
            <Box sx={{ mb: { xs: 3, sm: 4 } }}>
                <Typography
                    variant="h3"
                    fontWeight={800}
                    gutterBottom
                    sx={{
                        letterSpacing: '-0.03em',
                        background: theme.palette.mode === 'dark'
                            ? 'linear-gradient(135deg, #00d4aa 0%, #ffd166 100%)'
                            : 'linear-gradient(135deg, #0d7377 0%, #14a085 100%)',
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                        backgroundClip: 'text',
                        fontSize: { xs: '1.8rem', sm: '2.5rem' },
                    }}
                >
                    📊 Dashboard Clínico
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.65, fontWeight: 500 }}>
                    Visão geral do seu consultório e performance de tratamentos.
                </Typography>
            </Box>

            {/* KPIs */}
            <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mb: { xs: 3, sm: 4 } }}>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Total de Pacientes"
                        value={stats?.total_pacientes || 0}
                        emoji="👥"
                        icon={<PeopleIcon />}
                        color={theme.palette.primary.main}
                        delay={0}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Medicação com Dose Estável > 3 meses"
                        value={`${stats?.dose_estavel_pct || 0}%`}
                        subtitle="Estabilidade Clínica"
                        emoji="⏱️"
                        icon={<StableIcon />}
                        color={theme.palette.info.main}
                        delay={0.1}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={4}>
                    <StatCard
                        title="Atividade Recente"
                        value={stats?.atividade_recente || 0}
                        subtitle="Consultas/evoluções (30d)"
                        emoji="⚡"
                        icon={<ImprovementIcon />}
                        color={theme.palette.success.main}
                        delay={0.2}
                    />
                </Grid>
            </Grid>

            {/* Gráficos */}
            <Grid container spacing={{ xs: 2, sm: 3 }}>
                {/* Gráfico de Pizza - Condições Médicas */}
                <Grid item xs={12} md={8}>
                    <GlassPaper sx={{ height: 420 }} delay={0.4}>
                        <Typography variant="h6" gutterBottom fontWeight={700} sx={{ mb: 2 }}>
                            🏥 Principais Condições Tratadas
                        </Typography>
                        {stats?.principais_condicoes?.length > 0 ? (
                            <ResponsiveContainer width="100%" height="90%">
                                <PieChart>
                                    <Pie
                                        data={stats.principais_condicoes}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                        outerRadius={110}
                                        innerRadius={50}
                                        fill="#8884d8"
                                        dataKey="value"
                                        stroke="none"
                                    >
                                        {stats.principais_condicoes.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <RechartsTooltip
                                        contentStyle={{
                                            borderRadius: '12px',
                                            border: 'none',
                                            boxShadow: theme.palette.mode === 'dark'
                                                ? '0 8px 32px rgba(0,0,0,0.30)'
                                                : '0 8px 32px rgba(0,0,0,0.10)',
                                            background: theme.palette.mode === 'dark'
                                                ? 'rgba(26,31,29,0.95)'
                                                : 'rgba(255,255,255,0.95)',
                                        }}
                                    />
                                    <Legend
                                        wrapperStyle={{
                                            paddingTop: '20px',
                                        }}
                                    />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                                <Typography sx={{ opacity: 0.5, fontWeight: 500 }}>
                                    Sem dados suficientes para exibir gráfico.
                                </Typography>
                            </Box>
                        )}
                    </GlassPaper>
                </Grid>

                {/* Painel Lateral - Insights Rápidos */}
                <Grid item xs={12} md={4}>
                    <GlassPaper sx={{ height: 420, overflowY: 'auto' }} delay={0.5}>
                        <Typography variant="h6" gutterBottom fontWeight={700} sx={{ mb: 2 }}>
                            💡 Insights do Sistema
                        </Typography>

                        <Box sx={{ mt: 2 }}>
                            <Typography variant="subtitle2" gutterBottom fontWeight={600} sx={{ opacity: 0.8 }}>
                                📊 Status da Base
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, mt: 1 }}>
                                <Typography variant="body2" sx={{ flexGrow: 1, fontWeight: 500 }}>Ativos</Typography>
                                <Typography variant="body2" fontWeight={700} color="primary">
                                    {stats?.em_tratamento_pct}%
                                </Typography>
                            </Box>
                            <LinearProgress
                                variant="determinate"
                                value={stats?.em_tratamento_pct || 0}
                                sx={{
                                    mb: 3,
                                    height: 10,
                                    borderRadius: 5,
                                    bgcolor: theme.palette.mode === 'dark'
                                        ? 'rgba(0,212,170,0.08)'
                                        : 'rgba(13,115,119,0.08)',
                                }}
                            />

                            <Typography variant="subtitle2" gutterBottom fontWeight={600} sx={{ opacity: 0.8 }}>
                                🎯 Eficácia Observada
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, mt: 1 }}>
                                <Typography variant="body2" sx={{ flexGrow: 1, fontWeight: 500 }}>Melhora Clínica</Typography>
                                <Typography variant="body2" fontWeight={700} color="success.main">
                                    {stats?.melhora_pct}%
                                </Typography>
                            </Box>
                            <LinearProgress
                                variant="determinate"
                                color="success"
                                value={stats?.melhora_pct || 0}
                                sx={{
                                    mb: 3,
                                    height: 10,
                                    borderRadius: 5,
                                    bgcolor: theme.palette.mode === 'dark'
                                        ? 'rgba(46,204,113,0.08)'
                                        : 'rgba(46,204,113,0.08)',
                                }}
                            />

                            <Alert severity="info" sx={{ mt: 2 }}>
                                <Typography variant="caption" fontWeight={500}>
                                    Métricas baseadas nos registros de evolução e dosagem dos últimos 90 dias.
                                </Typography>
                            </Alert>
                        </Box>
                    </GlassPaper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default InternalDashboard;
