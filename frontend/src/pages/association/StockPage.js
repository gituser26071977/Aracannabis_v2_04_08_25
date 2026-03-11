import React, { useState, useEffect } from 'react';
import {
    Container, Typography, Paper, Button, Box, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, Dialog, DialogTitle, DialogContent,
    DialogActions, TextField, Alert, Breadcrumbs, Link as MuiLink,
    Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { useParams, Link, useNavigate } from 'react-router-dom';
import associationService from '../../services/associationService';

const StockPage = () => {
    const { id } = useParams();
    const Navigate = useNavigate();
    const [stock, setStock] = useState([]);
    const [association, setAssociation] = useState(null);
    const [open, setOpen] = useState(false);
    const [formData, setFormData] = useState({ produto_id: '', lote: '', quantidade: '', validade: '' });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [produtos, setProdutos] = useState([]);

    useEffect(() => {
        const fetchProdutos = async () => {
            try {
                const response = await associationService.getProdutos();
                setProdutos(response);
            } catch (err) {
                console.error('Erro ao carregar produtos:', err);
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
            const stockData = await associationService.getStock(id);
            setStock(stockData);
        } catch (err) {
            setError('Erro ao carregar dados de estoque.');
            console.error(err);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleAddStock = async () => {
        try {
            if (!formData.produto_id || !formData.lote || !formData.quantidade || !formData.validade) {
                setError('Todos os campos são obrigatórios.');
                return;
            }

            const payload = {
                ...formData,
                quantidade: parseInt(formData.quantidade),
                produto_id: parseInt(formData.produto_id)
            };

            await associationService.addStock(id, payload);
            setSuccess('Estoque adicionado com sucesso!');
            setOpen(false);
            setFormData({ produto_id: '', lote: '', quantidade: '', validade: '' });
            fetchData();
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError('Erro ao adicionar estoque.');
            console.error(err);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
                <MuiLink component={Link} to="/association" color="inherit">
                    Associações
                </MuiLink>
                <MuiLink component={Link} to={`/association/${id}/members`} color="inherit">
                    Membros
                </MuiLink>
                <Typography color="text.primary">Estoque</Typography>
            </Breadcrumbs>

            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" component="h1">
                    Estoque - {association ? association.nome : 'Carregando...'}
                </Typography>
                <Box>
                    <Button
                        variant="outlined"
                        sx={{ mr: 2 }}
                        onClick={() => Navigate('/association')}
                    >
                        Voltar
                    </Button>
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={() => setOpen(true)}
                    >
                        Adicionar Estoque
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
                            <TableCell>Produto ID</TableCell>
                            <TableCell>Lote</TableCell>
                            <TableCell>Quantidade</TableCell>
                            <TableCell>Validade</TableCell>
                            <TableCell>Data Entrada</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {stock.map((item) => (
                            <TableRow key={item.id}>
                                <TableCell>{item.id}</TableCell>
                                <TableCell>{item.produto_id}</TableCell>
                                <TableCell>{item.lote}</TableCell>
                                <TableCell>{item.quantidade}</TableCell>
                                <TableCell>{new Date(item.validade).toLocaleDateString()}</TableCell>
                                <TableCell>{new Date(item.data_entrada).toLocaleDateString()}</TableCell>
                            </TableRow>
                        ))}
                        {stock.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={6} align="center">
                                    Estoque vazio.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            <Dialog open={open} onClose={() => setOpen(false)}>
                <DialogTitle>Adicionar Estoque</DialogTitle>
                <DialogContent>
                    {/* TODO: Substituir por um Selector de Produtos do Backend */}
                    <FormControl fullWidth margin="dense">
                        <InputLabel id="produto-label">Produto</InputLabel>
                        <Select
                            labelId="produto-label"
                            name="produto_id"
                            value={formData.produto_id}
                            onChange={handleChange}
                            label="Produto"
                        >
                            {produtos.map(p => (
                                <MenuItem key={p.id} value={p.id}>{p.nome}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    <TextField
                        margin="dense"
                        name="lote"
                        label="Lote"
                        type="text"
                        fullWidth
                        value={formData.lote}
                        onChange={handleChange}
                    />
                    <TextField
                        margin="dense"
                        name="quantidade"
                        label="Quantidade"
                        type="number"
                        fullWidth
                        value={formData.quantidade}
                        onChange={handleChange}
                    />
                    <TextField
                        margin="dense"
                        name="validade"
                        label="Validade"
                        type="date"
                        fullWidth
                        InputLabelProps={{ shrink: true }}
                        value={formData.validade}
                        onChange={handleChange}
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpen(false)} color="secondary">
                        Cancelar
                    </Button>
                    <Button onClick={handleAddStock} color="primary">
                        Adicionar
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default StockPage;
