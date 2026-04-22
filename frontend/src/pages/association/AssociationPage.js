import React, { useState, useEffect } from 'react';
import {
    Container, Typography, Paper, Button, Box, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, Dialog, DialogTitle, DialogContent,
    DialogActions, TextField, Alert, IconButton, Tooltip, CircularProgress
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import BusinessIcon from '@mui/icons-material/Business';
import { useNavigate } from 'react-router-dom';
import associationService from '../../services/associationService';
import api from '../../services/api';

const AssociationPage = () => {
    const [associations, setAssociations] = useState([]);
    const [open, setOpen] = useState(false);
    const [formData, setFormData] = useState({ nome: '', cnpj: '', endereco: '', cep: '' });
    const [lookupLoading, setLookupLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        fetchAssociations();
    }, []);

    const fetchAssociations = async () => {
        try {
            const data = await associationService.getAssociations();
            setAssociations(data);
        } catch (err) {
            setError('Erro ao carregar associações.');
            console.error(err);
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
            console.error('Erro ao buscar CEP:', err);
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
            console.error('Erro ao buscar CNPJ:', err);
        } finally {
            setLookupLoading(false);
        }
    };

    const handleCreate = async () => {
        try {
            if (!formData.nome || !formData.cnpj) {
                setError('Nome e CNPJ são obrigatórios.');
                return;
            }
            await associationService.createAssociation(formData);
            setSuccess('Associação criada com sucesso!');
            setOpen(false);
            setFormData({ nome: '', cnpj: '', endereco: '', cep: '' });
            fetchAssociations();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError('Erro ao criar associação.');
            console.error(err);
        }
    };

    const handleConnectAgrobuds = async () => {
        setLookupLoading(true);
        try {
            const agrobudsData = {
                nome: 'HC AGROBUDS',
                cnpj: '00.000.000/0001-00',
                endereco: 'Avenida Paulista, 1000 - São Paulo/SP',
                telefone: '(11) 99999-9999',
                email: 'contato@agrobuds.com.br'
            };
            await associationService.createAssociation(agrobudsData);
            setSuccess('Conexão com Agrobuds estabelecida com sucesso!');
            fetchAssociations();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError(err.error || 'Erro ao conectar com Agrobuds. Talvez já esteja conectada?');
            console.error(err);
        } finally {
            setLookupLoading(false);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" component="h1">
                    Gestão de Associações
                </Typography>
                <Box display="flex" gap={2}>
                    <Button
                        variant="outlined"
                        color="secondary"
                        startIcon={<BusinessIcon />}
                        onClick={handleConnectAgrobuds}
                        disabled={lookupLoading}
                    >
                        {lookupLoading ? <CircularProgress size={24} /> : 'Conectar Agrobuds'}
                    </Button>
                    <Button
                        variant="contained"
                        color="primary"
                        startIcon={<AddIcon />}
                        onClick={() => setOpen(true)}
                    >
                        Nova Associação
                    </Button>
                </Box>
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>Nome</TableCell>
                            <TableCell>CNPJ</TableCell>
                            <TableCell>Endereço</TableCell>
                            <TableCell align="center">Ações</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {associations.map((assoc) => (
                            <TableRow key={assoc.id}>
                                <TableCell>{assoc.id}</TableCell>
                                <TableCell>{assoc.nome}</TableCell>
                                <TableCell>{assoc.cnpj}</TableCell>
                                <TableCell>{assoc.endereco}</TableCell>
                                <TableCell align="center">
                                    <Tooltip title="Ver Membros">
                                        <IconButton color="primary" onClick={() => navigate(`/association/${assoc.id}/members`)}>
                                            <VisibilityIcon />
                                        </IconButton>
                                    </Tooltip>
                                    <Button size="small" onClick={() => navigate(`/association/${assoc.id}/stock`)}>
                                        Estoque
                                    </Button>
                                    <Button size="small" onClick={() => navigate(`/association/${assoc.id}/dispensation`)}>
                                        Dispensar
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                        {associations.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={5} align="center">
                                    Nenhuma associação cadastrada.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <Dialog open={open} onClose={() => setOpen(false)}>
                <DialogTitle>Nova Associação</DialogTitle>
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
                            disabled={lookupLoading || formData.cnpj.length < 14}
                            onClick={handleCnpjLookup}
                            sx={{ mt: 1 }}
                        >
                            {lookupLoading ? <CircularProgress size={24} /> : 'Consultar'}
                        </Button>
                    </Box>
                    <TextField
                        margin="dense"
                        name="nome"
                        label="Nome da Associação"
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
                            disabled={lookupLoading || formData.cep.length < 8}
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
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpen(false)} color="secondary">
                        Cancelar
                    </Button>
                    <Button onClick={handleCreate} color="primary">
                        Salvar
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default AssociationPage;
