/**
 * SecretariaPacientesPage — Lista de pacientes do tenant (read-only).
 *
 * A secretária pode visualizar dados básicos dos pacientes da clínica
 * para fazer atendimento, check-in e dispensation — mas NÃO pode editar
 * prontuário, prescrição ou evolução.
 */
import React, { useEffect, useState, useCallback } from 'react';
import {
    Container, Typography, Box, Paper, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, TablePagination, TextField,
    InputAdornment, CircularProgress, Alert, Chip, IconButton,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useNavigate } from 'react-router-dom';
import secretariaService from '../services/secretariaService';

const formatDate = (iso) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleDateString('pt-BR', {
        day: '2-digit', month: '2-digit', year: 'numeric',
    });
};

const formatCpf = (cpf) => {
    if (!cpf) return '—';
    const s = String(cpf).replace(/\D/g, '');
    if (s.length !== 11) return cpf;
    return `${s.slice(0, 3)}.${s.slice(3, 6)}.${s.slice(6, 9)}-${s.slice(9)}`;
};

const SecretariaPacientesPage = () => {
    const navigate = useNavigate();
    const [items, setItems] = useState([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [query, setQuery] = useState('');
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(20);

    const carregar = useCallback(async (q = '', limit = 20, offset = 0) => {
        setLoading(true);
        setError('');
        try {
            const res = await secretariaService.listPacientes({ q, limit, offset });
            setItems(res.items || []);
            setTotal(res.total || 0);
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao carregar pacientes.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        carregar('', rowsPerPage, page * rowsPerPage);
    }, [carregar, page, rowsPerPage]);

    // Debounce simples para busca
    useEffect(() => {
        const t = setTimeout(() => {
            setPage(0);
            carregar(query, rowsPerPage, 0);
        }, 350);
        return () => clearTimeout(t);
    }, [query, rowsPerPage, carregar]);

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box mb={3}>
                <Typography variant="h4" component="h1" fontWeight={700}>
                    👤 Pacientes da Clínica
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Visualização read-only. Para editar prontuário, consulte o médico responsável.
                </Typography>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}

            <Paper sx={{ p: 2 }}>
                <TextField
                    fullWidth
                    size="small"
                    placeholder="Buscar por nome ou CPF..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    sx={{ mb: 2 }}
                    InputProps={{
                        startAdornment: (
                            <InputAdornment position="start">
                                <SearchIcon fontSize="small" />
                            </InputAdornment>
                        ),
                    }}
                />

                {loading ? (
                    <Box textAlign="center" p={3}>
                        <CircularProgress />
                    </Box>
                ) : items.length === 0 ? (
                    <Box p={3} textAlign="center">
                        <Typography color="text.secondary">
                            {query ? 'Nenhum paciente encontrado.' : 'Sem pacientes cadastrados.'}
                        </Typography>
                    </Box>
                ) : (
                    <>
                        <TableContainer>
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Nome</TableCell>
                                        <TableCell>CPF</TableCell>
                                        <TableCell>Data Nasc.</TableCell>
                                        <TableCell>Convênio</TableCell>
                                        <TableCell>Status</TableCell>
                                        <TableCell align="right">Ações</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {items.map((p) => (
                                        <TableRow key={p.id} hover>
                                            <TableCell>{p.nome}</TableCell>
                                            <TableCell>{formatCpf(p.cpf)}</TableCell>
                                            <TableCell>{formatDate(p.data_nascimento)}</TableCell>
                                            <TableCell>{p.convenio || '—'}</TableCell>
                                            <TableCell>
                                                {p.ativo === false ? (
                                                    <Chip size="small" label="Inativo" color="default" />
                                                ) : (
                                                    <Chip size="small" label="Ativo" color="success" />
                                                )}
                                            </TableCell>
                                            <TableCell align="right">
                                                <IconButton
                                                    size="small"
                                                    onClick={() => navigate(`/pacientes/${p.id}`)}
                                                >
                                                    <VisibilityIcon fontSize="small" />
                                                </IconButton>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                        <TablePagination
                            component="div"
                            count={total}
                            page={page}
                            onPageChange={(_, newPage) => setPage(newPage)}
                            rowsPerPage={rowsPerPage}
                            onRowsPerPageChange={(e) => {
                                setRowsPerPage(parseInt(e.target.value, 10));
                                setPage(0);
                            }}
                            rowsPerPageOptions={[10, 20, 50, 100]}
                            labelRowsPerPage="Por página:"
                            labelDisplayedRows={({ from, to, count }) =>
                                `${from}-${to} de ${count}`
                            }
                        />
                    </>
                )}
            </Paper>
        </Container>
    );
};

export default SecretariaPacientesPage;
