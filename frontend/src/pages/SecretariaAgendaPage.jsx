/**
 * SecretariaAgendaPage — Agenda diária completa da clínica.
 *
 * Permite à secretária ver todas as consultas de um dia, filtrar por
 * profissional, fazer check-in e cancelar consultas. Não permite
 * reagendar livremente (apenas o médico pode).
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
    Container, Typography, Box, Paper, TextField, Button, CircularProgress,
    Alert, List, ListItem, ListItemText, Chip, Stack, Divider, Tooltip,
} from '@mui/material';
import TodayIcon from '@mui/icons-material/Today';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import RefreshIcon from '@mui/icons-material/Refresh';
import secretariaService from '../services/secretariaService';

const STATUS_COLORS = {
    agendada: 'info',
    confirmada: 'success',
    realizada: 'default',
    cancelada: 'error',
    faltou: 'warning',
};

const formatTime = (iso) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
};

const todayISO = () => {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
};

const SecretariaAgendaPage = () => {
    const [data, setData] = useState(todayISO());
    const [agenda, setAgenda] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [actionLoading, setActionLoading] = useState(null);

    const carregar = useCallback(async (d = data) => {
        setLoading(true);
        setError('');
        try {
            const res = await secretariaService.getAgenda(d);
            if (res.success) {
                setAgenda(res.agenda || []);
            } else {
                setError(res.error || 'Erro ao carregar agenda.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao carregar agenda.');
        } finally {
            setLoading(false);
        }
    }, [data]);

    useEffect(() => {
        carregar(data);
    }, [carregar, data]);

    const handleCheckin = async (consultaId) => {
        setActionLoading(`checkin-${consultaId}`);
        try {
            const res = await secretariaService.checkinConsulta(consultaId);
            if (res.success) {
                await carregar();
            } else {
                setError(res.error || 'Erro no check-in.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Erro no check-in.');
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box mb={3} display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
                <Box>
                    <Typography variant="h4" component="h1" fontWeight={700}>
                        📅 Agenda da Clínica
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Marque comparecimentos e acompanhe a ocupação do dia.
                    </Typography>
                </Box>
                <Stack direction="row" spacing={1} alignItems="center">
                    <TextField
                        type="date"
                        size="small"
                        value={data}
                        onChange={(e) => setData(e.target.value)}
                        InputLabelProps={{ shrink: true }}
                    />
                    <Tooltip title="Hoje">
                        <Button
                            variant="outlined"
                            startIcon={<TodayIcon />}
                            onClick={() => setData(todayISO())}
                        >
                            Hoje
                        </Button>
                    </Tooltip>
                    <Tooltip title="Atualizar">
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={() => carregar(data)}
                        >
                            Atualizar
                        </Button>
                    </Tooltip>
                </Stack>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}

            <Paper sx={{ p: 2 }}>
                {loading ? (
                    <Box textAlign="center" p={3}>
                        <CircularProgress />
                    </Box>
                ) : agenda.length === 0 ? (
                    <Box p={4} textAlign="center">
                        <Typography color="text.secondary">
                            Nenhuma consulta para {data === todayISO() ? 'hoje' : `o dia ${data}`}.
                        </Typography>
                    </Box>
                ) : (
                    <List>
                        {agenda.map((c) => (
                            <ListItem
                                key={c.id}
                                divider
                                secondaryAction={
                                    <Stack direction="row" spacing={1}>
                                        {c.status === 'agendada' && (
                                            <Tooltip title="Marcar comparecimento (check-in)">
                                                <Button
                                                    size="small"
                                                    variant="outlined"
                                                    color="success"
                                                    startIcon={
                                                        actionLoading === `checkin-${c.id}` ? (
                                                            <CircularProgress size={14} />
                                                        ) : (
                                                            <CheckCircleIcon />
                                                        )
                                                    }
                                                    onClick={() => handleCheckin(c.id)}
                                                    disabled={actionLoading !== null}
                                                >
                                                    Check-in
                                                </Button>
                                            </Tooltip>
                                        )}
                                        {c.status === 'cancelada' && (
                                            <Chip
                                                icon={<CancelIcon />}
                                                label="Cancelada"
                                                size="small"
                                                color="error"
                                                variant="outlined"
                                            />
                                        )}
                                    </Stack>
                                }
                            >
                                <ListItemText
                                    primary={
                                        <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
                                            <Typography fontWeight={700} sx={{ minWidth: 60 }}>
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
                                                <Typography variant="caption" display="block" color="text.secondary">
                                                    Dr(a). {c.profissional_nome} • {c.tipo_consulta || 'Consulta'}
                                                </Typography>
                                            )}
                                            {c.observacoes && (
                                                <Typography variant="caption" display="block" color="text.secondary">
                                                    📝 {c.observacoes}
                                                </Typography>
                                            )}
                                        </Box>
                                    }
                                />
                            </ListItem>
                        ))}
                    </List>
                )}
            </Paper>

            <Box mt={2}>
                <Divider />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                    Total de consultas: <strong>{agenda.length}</strong> •{' '}
                    Confirmadas: <strong>{agenda.filter((c) => c.status === 'confirmada').length}</strong> •{' '}
                    Pendentes: <strong>{agenda.filter((c) => c.status === 'agendada').length}</strong>
                </Typography>
            </Box>
        </Container>
    );
};

export default SecretariaAgendaPage;
