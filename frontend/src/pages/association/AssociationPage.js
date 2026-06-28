import React, { useState, useEffect } from 'react';
import {
    Container, Typography, Paper, Button, Box, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, Dialog, DialogTitle, DialogContent,
    DialogActions, TextField, Alert, IconButton, Tooltip, CircularProgress
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import BusinessIcon from '@mui/icons-material/Business';
import LockIcon from '@mui/icons-material/Lock';
import { useNavigate } from 'react-router-dom';
import associationService from '../../services/associationService';
import api from '../../services/api';
import LockedFeatureAlert from '../../components/LockedFeatureAlert';
import { useAuth } from '../../contexts/AuthContext';

const AssociationPage = () => {
    const [clinicas, setClinicas] = useState([]);
    const [open, setOpen] = useState(false);
    const [editMode, setEditMode] = useState(false);
    const [editingId, setEditingId] = useState(null);
    const [confirmDelete, setConfirmDelete] = useState(null);
    const [formData, setFormData] = useState({ nome: '', cnpj: '', endereco: '', cep: '', telefone: '', email: '' });
    const [lookupLoading, setLookupLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const navigate = useNavigate();
    const { hasClinicaAccess } = useAuth();

    useEffect(() => {
        if (hasClinicaAccess) {
            fetchClinicas();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [hasClinicaAccess]);

    const fetchClinicas = async () => {
        try {
            const data = await associationService.getAssociations();
            setClinicas(data);
        } catch (err) {
            setError('Erro ao carregar clínicas.');
            if(process.env.NODE_ENV!=='production')console.error(err);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleCepLookup = async () => {
        if (!formData.cep || formData.cep.replace(/\D/g, '').length !== 8) return;

        setLookupLoading(true);
        try {
            const response = await api.get(`/utils/cep/${formData.cep}`);
            if (response.data.success) {
                const { street, neighborhood, city, state } = response.data.data;
                setFormData(prev => ({
                    ...prev,
                    endereco: `${street}, ${neighborhood}, ${city} - ${state}`
                }));
            }
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error('Erro ao buscar CEP:', err);
        } finally {
            setLookupLoading(false);
        }
    };

    const handleCnpjLookup = async () => {
        if (!formData.cnpj || formData.cnpj.replace(/\D/g, '').length < 14) return;

        setLookupLoading(true);
        try {
            const response = await api.get(`/utils/cnpj/${formData.cnpj}`);
            if (response.data.success) {
                const data = response.data.data;
                const addr = `${data.logradouro}, ${data.numero} ${data.complemento ? '(' + data.complemento + ')' : ''}, ${data.bairro}, ${data.municipio} - ${data.uf}`;
                setFormData(prev => ({
                    ...prev,
                    nome: data.razao_social || data.nome_fantasia || prev.nome,
                    endereco: addr,
                    cep: data.cep || prev.cep
                }));
            }
        } catch (err) {
            if(process.env.NODE_ENV!=='production')console.error('Erro ao buscar CNPJ:', err);
        } finally {
            setLookupLoading(false);
        }
    };

    const resetForm = () => {
        setFormData({ nome: '', cnpj: '', endereco: '', cep: '', telefone: '', email: '' });
        setEditMode(false);
        setEditingId(null);
    };

    const handleOpenCreate = () => {
        resetForm();
        setOpen(true);
    };

    const handleOpenEdit = async (clinica) => {
        try {
            const data = await associationService.getAssociationById(clinica.id);
            setFormData({
                nome: data.nome || '',
                cnpj: data.cnpj || '',
                endereco: data.endereco || '',
                cep: '',
                telefone: data.telefone || '',
                email: data.email || '',
            });
            setEditMode(true);
            setEditingId(data.id);
            setOpen(true);
        } catch (err) {
            setError('Erro ao carregar dados da clínica.');
        }
    };

    const handleSubmit = async () => {
        try {
            if (!formData.nome || !formData.cnpj) {
                setError('Nome e CNPJ são obrigatórios.');
                return;
            }
            if (editMode && editingId) {
                await associationService.updateAssociation(editingId, {
                    nome: formData.nome,
                    cnpj: formData.cnpj,
                    endereco: formData.endereco,
                    telefone: formData.telefone,
                    email: formData.email,
                });
                setSuccess('Clínica atualizada com sucesso!');
            } else {
                await associationService.createAssociation(formData);
                setSuccess('Clínica criada com sucesso!');
            }
            setOpen(false);
            resetForm();
            fetchClinicas();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            const status = err?.response?.status;
            if (status === 403) {
                const data = err.response?.data || {};
                setError(
                    data.message ||
                    'Seu plano atual não permite gerenciar clínicas. Faça upgrade para Premium ou Enterprise.'
                );
            } else {
                setError('Erro ao salvar clínica.');
            }
            if(process.env.NODE_ENV!=='production')console.error(err);
        }
    };

    const handleDelete = async (clinica) => {
        try {
            await associationService.deleteAssociation(clinica.id);
            setSuccess(`Clínica "${clinica.nome}" desativada com sucesso!`);
            setConfirmDelete(null);
            fetchClinicas();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            const status = err?.response?.status;
            if (status === 403) {
                setError('Você não tem permissão para desativar esta clínica.');
            } else {
                setError('Erro ao desativar clínica.');
            }
            if(process.env.NODE_ENV!=='production')console.error(err);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Box display="flex" alignItems="center" gap={1.5}>
                    <BusinessIcon color="primary" sx={{ fontSize: 32 }} />
                    <Typography variant="h4" component="h1">
                        Gestão da Clínica
                    </Typography>
                    {!hasClinicaAccess && (
                        <LockIcon sx={{ color: 'primary.main', ml: 1 }} titleAccess="Recurso Premium" />
                    )}
                </Box>
                {hasClinicaAccess && (
                    <Button
                        variant="contained"
                        color="primary"
                        startIcon={<AddIcon />}
                        onClick={handleOpenCreate}
                    >
                        Nova Clínica
                    </Button>
                )}
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

            {!hasClinicaAccess ? (
                <LockedFeatureAlert
                    feature="Gestão da Clínica"
                    planRequired="premium"
                    description="Cadastre a clínica, gerencie profissionais vinculados e faça a dispensa de produtos em um único lugar."
                />
            ) : (
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>ID</TableCell>
                                <TableCell>Nome</TableCell>
                                <TableCell>CNPJ</TableCell>
                                <TableCell>Endereço</TableCell>
                                <TableCell>Telefone</TableCell>
                                <TableCell align="center">Ações</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {clinicas.map((clinica) => (
                                <TableRow key={clinica.id}>
                                    <TableCell>{clinica.id}</TableCell>
                                    <TableCell>{clinica.nome}</TableCell>
                                    <TableCell>{clinica.cnpj}</TableCell>
                                    <TableCell>{clinica.endereco}</TableCell>
                                    <TableCell>{clinica.telefone || '—'}</TableCell>
                                    <TableCell align="center">
                                        <Tooltip title="Editar">
                                            <IconButton color="primary" onClick={() => handleOpenEdit(clinica)}>
                                                <EditIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Desativar">
                                            <IconButton
                                                color="error"
                                                onClick={() => setConfirmDelete(clinica)}
                                            >
                                                <DeleteIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="Ver Membros">
                                            <IconButton color="primary" onClick={() => navigate(`/association/${clinica.id}/members`)}>
                                                <VisibilityIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Button size="small" onClick={() => navigate(`/association/${clinica.id}/stock`)}>
                                            Estoque
                                        </Button>
                                        <Button size="small" onClick={() => navigate(`/association/${clinica.id}/dispensation`)}>
                                            Dispensar
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {clinicas.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6} align="center">
                                        Nenhuma clínica cadastrada.
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            {/* Create / Edit Dialog */}
            <Dialog open={open} onClose={() => { setOpen(false); resetForm(); }} maxWidth="sm" fullWidth>
                <DialogTitle>{editMode ? 'Editar Clínica' : 'Nova Clínica'}</DialogTitle>
                <DialogContent>
                    <Box display="flex" gap={1} alignItems="center">
                        <TextField
                            margin="dense"
                            name="cnpj"
                            label="CNPJ"
                            type="text"
                            fullWidth
                            value={formData.cnpj}
                            onChange={handleChange}
                        />
                        <Button
                            variant="outlined"
                            disabled={lookupLoading || formData.cnpj.replace(/\D/g, '').length < 14}
                            onClick={handleCnpjLookup}
                            sx={{ mt: 1 }}
                        >
                            {lookupLoading ? <CircularProgress size={24} /> : 'Consultar'}
                        </Button>
                    </Box>
                    <TextField
                        margin="dense"
                        name="nome"
                        label="Nome da Clínica"
                        type="text"
                        fullWidth
                        value={formData.nome}
                        onChange={handleChange}
                    />
                    <Box display="flex" gap={1} alignItems="center">
                        <TextField
                            margin="dense"
                            name="cep"
                            label="CEP"
                            type="text"
                            fullWidth
                            value={formData.cep}
                            onChange={handleChange}
                        />
                        <Button
                            variant="outlined"
                            disabled={lookupLoading || formData.cep.replace(/\D/g, '').length < 8}
                            onClick={handleCepLookup}
                            sx={{ mt: 1 }}
                        >
                            {lookupLoading ? <CircularProgress size={24} /> : 'Buscar'}
                        </Button>
                    </Box>
                    <TextField
                        margin="dense"
                        name="endereco"
                        label="Endereço"
                        type="text"
                        fullWidth
                        multiline
                        rows={2}
                        value={formData.endereco}
                        onChange={handleChange}
                    />
                    <TextField
                        margin="dense"
                        name="telefone"
                        label="Telefone"
                        type="text"
                        fullWidth
                        value={formData.telefone}
                        onChange={handleChange}
                    />
                    <TextField
                        margin="dense"
                        name="email"
                        label="Email"
                        type="email"
                        fullWidth
                        value={formData.email}
                        onChange={handleChange}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => { setOpen(false); resetForm(); }} color="secondary">
                        Cancelar
                    </Button>
                    <Button onClick={handleSubmit} color="primary" variant="contained">
                        {editMode ? 'Atualizar' : 'Salvar'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Confirm Delete Dialog */}
            <Dialog open={Boolean(confirmDelete)} onClose={() => setConfirmDelete(null)}>
                <DialogTitle>Desativar clínica</DialogTitle>
                <DialogContent>
                    <Typography>
                        Tem certeza que deseja desativar a clínica{' '}
                        <strong>{confirmDelete?.nome}</strong>?
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        A clínica será marcada como inativa e deixará de aparecer nas listagens.
                        Os dados serão preservados para fins de auditoria (LGPD).
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfirmDelete(null)} color="secondary">
                        Cancelar
                    </Button>
                    <Button
                        onClick={() => handleDelete(confirmDelete)}
                        color="error"
                        variant="contained"
                    >
                        Desativar
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default AssociationPage;
