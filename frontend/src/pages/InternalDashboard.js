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
    Alert
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

const StatCard = ({ title, value, subtitle, icon, color, loading }) => (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
        <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box
                    sx={{
                        bgcolor: `${color}15`,
                        p: 1.5,
                        borderRadius: '50%',
                        color: color
                    }}
                >
                    {icon}
                </Box>
                {loading && <CircularProgress size={20} />}
            </Box>
            <Typography variant="h4" fontWeight="bold" sx={{ mb: 1 }}>
                {value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
                {title}
            </Typography>
            {subtitle && (
                <Typography variant="caption" sx={{ color: color, fontWeight: 'bold', mt: 1, display: 'block' }}>
                    {subtitle}
                </Typography>
            )}
        </CardContent>
    </Card>
);

const InternalDashboard = () => {
    const theme = useTheme();
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
            console.error('Erro ao carregar dashboard:', err);
            setError('Falha ao carregar métricas.');
        } finally {
            setLoading(false);
        }
    };

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

    if (loading && !stats) {
        return (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return <Alert severity="error">{error}</Alert>;
    }

    return (
        <Box sx={{ flexGrow: 1, py: 2 }}>
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" fontWeight="bold" gutterBottom>
                    Dashboard Clínico
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Visão geral do seu consultório e performance de tratamentos.
                </Typography>
            </Box>

            {/* KPIs */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Total de Pacientes"
                        value={stats?.total_pacientes || 0}
                        icon={<PeopleIcon />}
                        color={theme.palette.primary.main}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Em Tratamento Ativo"
                        value={`${stats?.em_tratamento_pct || 0}%`}
                        subtitle="Taxa de Adesão"
                        icon={<TreatmentIcon />}
                        color={theme.palette.secondary.main}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Melhora Registrada"
                        value={`${stats?.melhora_pct || 0}%`}
                        subtitle="Evolução Positiva"
                        icon={<ImprovementIcon />}
                        color={theme.palette.success.main}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Dose Estável > 3 Meses"
                        value={`${stats?.dose_estavel_pct || 0}%`}
                        subtitle="Estabilidade Clínica"
                        icon={<StableIcon />}
                        color={theme.palette.info.main}
                    />
                </Grid>
            </Grid>

            {/* Gráficos */}
            <Grid container spacing={3}>
                {/* Gráfico de Pizza - Condições Médicas */}
                <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 3, height: 400 }}>
                        <Typography variant="h6" gutterBottom fontWeight="bold">
                            Principais Condições Tratadas
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
                                        outerRadius={120}
                                        fill="#8884d8"
                                        dataKey="value"
                                    >
                                        {stats.principais_condicoes.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <RechartsTooltip />
                                    <Legend />
                                </PieChart>
                            </ResponsiveContainer>
                        ) : (
                            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                                <Typography color="text.secondary">Sem dados suficientes para exibir gráfico.</Typography>
                            </Box>
                        )}
                    </Paper>
                </Grid>

                {/* Painel Lateral - Insights Rápidos */}
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3, height: 400, overflowY: 'auto' }}>
                        <Typography variant="h6" gutterBottom fontWeight="bold">
                            Insights do Sistema
                        </Typography>

                        <Box sx={{ mt: 2 }}>
                            <Typography variant="subtitle2" gutterBottom>
                                Status da Base
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Typography variant="body2" sx={{ flexGrow: 1 }}>Ativos</Typography>
                                <Typography variant="body2" fontWeight="bold">{stats?.em_tratamento_pct}%</Typography>
                            </Box>
                            <LinearProgress variant="determinate" value={stats?.em_tratamento_pct || 0} sx={{ mb: 3, height: 8, borderRadius: 4 }} />

                            <Typography variant="subtitle2" gutterBottom>
                                Eficácia Observada
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Typography variant="body2" sx={{ flexGrow: 1 }}>Melhora Clínica</Typography>
                                <Typography variant="body2" fontWeight="bold">{stats?.melhora_pct}%</Typography>
                            </Box>
                            <LinearProgress variant="determinate" color="success" value={stats?.melhora_pct || 0} sx={{ mb: 3, height: 8, borderRadius: 4 }} />

                            <Alert severity="info" sx={{ mt: 2 }}>
                                <Typography variant="caption">
                                    Métricas baseadas nos registros de evolução e dosagem dos últimos 90 dias.
                                </Typography>
                            </Alert>
                        </Box>
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default InternalDashboard;
