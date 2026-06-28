import React, { useState, useEffect } from 'react';
import {
    Container, Typography, Paper, Button, Box, TextField, Alert, Breadcrumbs,
    Link as MuiLink, Select, MenuItem, FormControl, InputLabel, Grid
} from '@mui/material';
import { useParams, Link, useNavigate } from 'react-router-dom';
import associationService from '../../services/associationService';

const DispensationPage = () => {
    const { id } = useParams();
    const Navigate = useNavigate();
    const [association, setAssociation] = useState(null);
    const [members, setMembers] = useState([]);
    const [formData, setFormData] = useState({ membro_id: '', produto_id: '', quantidade: 1, observacao: '' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [produtos, setProdutos] = useState([]);

    useEffect(() => {
        const fetchProdutos = async () => {
            try {
                const response = await associationService.getProdutos();
                setProdutos(response);
            } catch (err) {
                if(process.env.NODE_ENV!=='production')console.error('Erro ao carregar produtos:', err);
            }
        };
        fetchProdutos();
    }, []);

    useEffect(() => {
        fetchData();
    }, [id]);

    const fetchData = async () => {
        try {
            const assocData = await associationService.getAssociationById(id);
            setAssociation(assocData);
            const membersData = await associationService.getMembers(id);
            setMembers(membersData);
        } catch (err) {
            setError('Erro ao carregar dados.');
            if(process.env.NODE_ENV!=='production')console.error(err);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleDispense = async (e) => {
        e.preventDefault();
        try {
            if (!formData.membro_id || !formData.produto_id || !formData.quantidade) {
                setError('Preencha os campos obrigatórios (Membro, Produto, Quantidade).');
                return;
            }

            const payload = {
                membro_id: parseInt(formData.membro_id),
                produto_id: parseInt(formData.produto_id),
                quantidade: parseInt(formData.quantidade),
                observacao: formData.observacao
            };

            await associationService.dispenseItem(id, payload);
            setSuccess('Dispensação realizada com sucesso!');
            setFormData({ membro_id: '', produto_id: '', quantidade: 1, observacao: '' });
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao realizar dispensação. Verifique o estoque.');
            if(process.env.NODE_ENV!=='production')console.error(err);
        }
    };

    return (
        <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
            <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
                <MuiLink component={Link} to="/association" color="inherit">
                    Associações
                </MuiLink>
                <MuiLink component={Link} to={`/association/${id}/stock`} color="inherit">
                    Estoque
                </MuiLink>
                <Typography color="text.primary">Dispensação</Typography>
            </Breadcrumbs>

            <Typography variant="h4" component="h1" gutterBottom>
                Dispensação - {association ? association.nome : '...'}
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

            <Paper sx={{ p: 4, mt: 2 }}>
                <form onSubmit={handleDispense}>
                    <Grid container spacing={3}>
                        <Grid item xs={12}>
                            <FormControl fullWidth>
                                <InputLabel id="membro-label">Membro (Paciente)</InputLabel>
                                <Select
                                    labelId="membro-label"
                                    name="membro_id"
                                    value={formData.membro_id}
                                    onChange={handleChange}
                                    label="Membro (Paciente)"
                                    required
                                >
                                    {members.map(m => (
                                        <MenuItem key={m.id} value={m.id}>
                                            {m.paciente_nome ? `${m.paciente_nome} (CPF: ${m.cpf})` : `Membro #${m.id} - ${m.cpf}`}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12}>
                            <FormControl fullWidth>
                                <InputLabel id="produto-label">Produto</InputLabel>
                                <Select
                                    labelId="produto-label"
                                    name="produto_id"
                                    value={formData.produto_id}
                                    onChange={handleChange}
                                    label="Produto"
                                    required
                                >
                                    {produtos.map(p => (
                                        <MenuItem key={p.id} value={p.id}>{p.nome}</MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={6}>
                            <TextField
                                name="quantidade"
                                label="Quantidade"
                                type="number"
                                fullWidth
                                value={formData.quantidade}
                                onChange={handleChange}
                                required
                                inputProps={{ min: 1 }}
                            />
                        </Grid>
                        <Grid item xs={12}>
                            <TextField
                                name="observacao"
                                label="Observação (Opcional)"
                                type="text"
                                fullWidth
                                multiline
                                rows={2}
                                value={formData.observacao}
                                onChange={handleChange}
                            />
                        </Grid>
                        <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
                            <Button variant="outlined" onClick={() => Navigate('/association')}>
                                Cancelar
                            </Button>
                            <Button type="submit" variant="contained" color="primary" size="large">
                                Confirmar Dispensação
                            </Button>
                        </Grid>
                    </Grid>
                </form>
            </Paper>
        </Container>
    );
};

export default DispensationPage;
