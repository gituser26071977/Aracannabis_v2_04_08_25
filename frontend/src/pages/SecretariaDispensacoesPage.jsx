/**
 * SecretariaDispensacoesPage — Dispensações pendentes da clínica.
 *
 * Lista prescrições com produto a ser dispensado, prontas para a
 * secretária conferir, baixar estoque e finalizar. Cada item mostra:
 *  - Paciente + produto
 *  - Quantidade restante
 *  - Botão "Dispensar" (confirmação via modal)
 *  - Status da prescrição
 *
 * Mantém a separação de responsabilidades: secretária registra a entrega,
 * mas não altera a prescrição em si.
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
    Container, Typography, Box, Paper, CircularProgress, Alert, Chip,
    Button, Stack, List, ListItem, ListItemText, Divider, Tooltip,
    Dialog, DialogTitle, DialogContent, DialogActions, DialogContentText,
} from '@mui/material';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import RefreshIcon from '@mui/icons-material/Refresh';
import api from '../services/api';

const STATUS_COLORS = {
    pendente: 'warning',
    ativa: 'success',
    dispensada: 'info',
    cancelada: 'error',
    expirada: 'default',
};

const formatDate = (iso) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
    });
};

const associationHeader = () => {
    const id = localStorage.getItem('selectedAssociationId');
    return id ? { 'X-Association-ID': id } : {};
};

const SecretariaDispensacoesPage = () => {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [confirmItem, setConfirmItem] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);

    const carregar = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            // Endpoint ainda em construção no service. Mantemos fallback vazio
            // enquanto a rota de dispensações pendentes não é cabeada.
            const res = await api.get('/secretaria/dispensacoes/pendentes', {
                headers: associationHeader(),
            });
            setItems(res.data?.items || []);
        } catch (err) {
            // Não falhar a página inteira — dispensações vazias é estado válido
            if (err.response?.status === 404) {
                setItems([]);
            } else {
                setError(err.response?.data?.error || 'Erro ao carregar dispensações.');
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        carregar();
    }, [carregar]);

    const handleConfirm = async () => {
        if (!confirmItem) return;
        setActionLoading(true);
        try {
            await api.post(
                `/secretaria/dispensacoes/${confirmItem.id}/confirmar`,
                {},
                { headers: associationHeader() }
            );
            setConfirmItem(null);
            await carregar();
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao confirmar dispensação.');
        } finally {
            setActionLoading(false);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box mb={3} display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
                <Box>
                    <Typography variant="h4" component="h1" fontWeight={700}>
                        📦 Dispensações Pendentes
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                        Confirme a entrega de produtos prescritos e mantenha o estoque atualizado.
                    </Typography>
                </Box>
                <Tooltip title="Atualizar lista">
                    <Button
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                        onClick={carregar}
                    >
                        Atualizar
                    </Button>
                </Tooltip>
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
                ) : items.length === 0 ? (
                    <Box p={4} textAlign="center">
                        <LocalShippingIcon sx={{ fontSize: 60, color: 'text.disabled', mb: 1 }} />
                        <Typography color="text.secondary">
                            Nenhuma dispensação pendente no momento.
                        </Typography>
                        <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                            Quando o médico emitir uma prescrição, ela aparecerá aqui para entrega.
                        </Typography>
                    </Box>
                ) : (
                    <List>
                        {items.map((d) => (
                            <ListItem
                                key={d.id}
                                divider
                                secondaryAction={
                                    <Stack direction="row" spacing={1}>
                                        <Tooltip title="Confirmar entrega e baixar estoque">
                                            <Button
                                                size="small"
                                                variant="contained"
                                                color="success"
                                                startIcon={<CheckCircleIcon />}
                                                onClick={() => setConfirmItem(d)}
                                            >
                                                Dispensar
                                            </Button>
                                        </Tooltip>
                                    </Stack>
                                }
                            >
                                <ListItemText
                                    primary={
                                        <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
                                            <Typography fontWeight={700}>
                                                {d.produto_nome || d.produto || 'Produto'}
                                            </Typography>
                                            <Chip
                                                size="small"
                                                label={`${d.quantidade || 1} ${d.unidade || 'un'}`}
                                            />
                                            <Chip
                                                size="small"
                                                label={d.status || 'pendente'}
                                                color={STATUS_COLORS[d.status] || 'warning'}
                                            />
                                        </Box>
                                    }
                                    secondary={
                                        <Box>
                                            <Typography variant="caption" display="block" color="text.secondary">
                                                👤 {d.paciente_nome || d.paciente || 'Paciente'}
                                            </Typography>
                                            {d.profissional_nome && (
                                                <Typography variant="caption" display="block" color="text.secondary">
                                                    🩺 Dr(a). {d.profissional_nome}
                                                </Typography>
                                            )}
                                            {d.data_prescricao && (
                                                <Typography variant="caption" display="block" color="text.secondary">
                                                    📅 Prescrito em {formatDate(d.data_prescricao)}
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
                    Total pendente: <strong>{items.length}</strong>
                </Typography>
            </Box>

            {/* Modal de confirmação */}
            <Dialog open={!!confirmItem} onClose={() => !actionLoading && setConfirmItem(null)}>
                <DialogTitle>Confirmar dispensação</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Confirma a entrega de{' '}
                        <strong>{confirmItem?.quantidade} {confirmItem?.unidade || 'un'}</strong> de{' '}
                        <strong>{confirmItem?.produto_nome || confirmItem?.produto}</strong> para{' '}
                        <strong>{confirmItem?.paciente_nome || confirmItem?.paciente}</strong>?
                    </DialogContentText>
                    <DialogContentText sx={{ mt: 1 }}>
                        Esta ação baixará o estoque e registrará a entrega no histórico do paciente.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfirmItem(null)} disabled={actionLoading}>
                        Cancelar
                    </Button>
                    <Button
                        onClick={handleConfirm}
                        color="success"
                        variant="contained"
                        disabled={actionLoading}
                        startIcon={actionLoading ? <CircularProgress size={14} /> : <CheckCircleIcon />}
                    >
                        Confirmar entrega
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default SecretariaDispensacoesPage;
