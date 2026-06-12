import React, { useState, useEffect } from 'react';
import {
    Container, Typography, Paper, Button, Box, Table, TableBody, TableCell,
    TableContainer, TableHead, TableRow, Dialog, DialogTitle, DialogContent,
    DialogActions, TextField, Alert, IconButton, Tooltip, CircularProgress,
    Tabs, Tab, Chip, MenuItem, Select, FormControl, InputLabel
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import VisibilityIcon from '@mui/icons-material/Visibility';
import BusinessIcon from '@mui/icons-material/Business';
import SendIcon from '@mui/icons-material/Send';
import BlockIcon from '@mui/icons-material/Block';
import { useNavigate } from 'react-router-dom';
import associationService from '../../services/associationService';
import api from '../../services/api';

const STAFF_ROLE_LABELS = {
    secretary: { label: 'Secretária', color: 'secondary' },
    manager: { label: 'Gestor(a)', color: 'warning' },
    admin: { label: 'Admin', color: 'error' },
};

const INVITE_STATUS_LABELS = {
    pending: { label: 'Pendente', color: 'info' },
    accepted: { label: 'Aceito', color: 'success' },
    revoked: { label: 'Revogado', color: 'default' },
    expired: { label: 'Expirado', color: 'default' },
};

const AssociationPage = () => {
    const [associations, setAssociations] = useState([]);
    const [open, setOpen] = useState(false);
    const [formData, setFormData] = useState({ nome: '', cnpj: '', endereco: '', cep: '' });
    const [lookupLoading, setLookupLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Estado do dialog de convite
    const [inviteOpen, setInviteOpen] = useState(false);
    const [inviteLoading, setInviteLoading] = useState(false);
    const [selectedAssociation, setSelectedAssociation] = useState(null);
    const [inviteForm, setInviteForm] = useState({
        nome: '', email: '', telefone: '',
        invite_type: 'professional',
        role: 'secretary',
    });
    const [inviteLink, setInviteLink] = useState('');
    const [inviteTab, setInviteTab] = useState(0);

    // Estado do dialog de listagem de convites
    const [invitesListOpen, setInvitesListOpen] = useState(false);
    const [invites, setInvites] = useState([]);
    const [invitesLoading, setInvitesLoading] = useState(false);

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

    // === Convite ===
    const openInviteDialog = (association) => {
        setSelectedAssociation(association);
        setInviteForm({
            nome: '', email: '', telefone: '',
            invite_type: 'professional',
            role: 'secretary',
        });
        setInviteLink('');
        setError('');
        setInviteTab(0);
        setInviteOpen(true);
    };

    const openInvitesListDialog = (association) => {
        setSelectedAssociation(association);
        setInvitesListOpen(true);
        fetchInvites(association.id);
    };

    const fetchInvites = async (associationId) => {
        setInvitesLoading(true);
        try {
            const data = await associationService.listInvites(associationId);
            setInvites(data.convites || []);
        } catch (err) {
            setError('Erro ao listar convites.');
            console.error(err);
        } finally {
            setInvitesLoading(false);
        }
    };

    const handleInviteSubmit = async () => {
        if (!inviteForm.email && !inviteForm.telefone) {
            setError('Informe email ou telefone para gerar o convite.');
            return;
        }

        setInviteLoading(true);
        setError('');
        try {
            let response;
            if (inviteForm.invite_type === 'staff') {
                response = await associationService.inviteStaff(selectedAssociation.id, {
                    nome: inviteForm.nome,
                    email: inviteForm.email,
                    telefone: inviteForm.telefone,
                    role: inviteForm.role,
                });
            } else {
                response = await associationService.inviteProfessional(selectedAssociation.id, {
                    nome: inviteForm.nome,
                    email: inviteForm.email,
                    telefone: inviteForm.telefone,
                });
            }
            setInviteLink(response.invite_link);
            setSuccess(response.email_sent ? 'Convite gerado e enviado por email.' : 'Convite gerado. Compartilhe o link abaixo.');
            setTimeout(() => setSuccess(''), 4000);
            if (selectedAssociation) fetchInvites(selectedAssociation.id);
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao gerar convite.');
            console.error(err);
        } finally {
            setInviteLoading(false);
        }
    };

    const handleRevokeInvite = async (inviteId) => {
        if (!window.confirm('Revogar este convite? O link deixará de funcionar.')) return;
        try {
            await associationService.revokeInvite(inviteId);
            setSuccess('Convite revogado.');
            setTimeout(() => setSuccess(''), 3000);
            if (selectedAssociation) fetchInvites(selectedAssociation.id);
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao revogar.');
            console.error(err);
        }
    };

    const handleResendInvite = async (inviteId) => {
        try {
            const res = await associationService.resendInvite(inviteId);
            setSuccess(res.message || 'Email reenviado.');
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao reenviar.');
            console.error(err);
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
                                    <Button size="small" onClick={() => openInviteDialog(assoc)}>
                                        Convidar
                                    </Button>
                                    <Button size="small" onClick={() => openInvitesListDialog(assoc)}>
                                        Ver Convites
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

            {/* Dialog: Nova Associação */}
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

            {/* Dialog: Convidar (Profissional OU Staff) */}
            <Dialog open={inviteOpen} onClose={() => setInviteOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>
                    Convidar {inviteForm.invite_type === 'staff' ? 'Membro da Equipe' : 'Profissional'}
                </DialogTitle>
                <DialogContent>
                    <Tabs
                        value={inviteTab}
                        onChange={(_, v) => {
                            setInviteTab(v);
                            setInviteForm({
                                ...inviteForm,
                                invite_type: v === 0 ? 'professional' : 'staff',
                            });
                            setInviteLink('');
                        }}
                        sx={{ mb: 2 }}
                    >
                        <Tab label="Profissional de Saúde" />
                        <Tab label="Equipe (Secretária/Gestor)" />
                    </Tabs>

                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {inviteForm.invite_type === 'staff'
                            ? 'A pessoa receberá um link para criar a conta já vinculada à equipe administrativa da clínica. Não exige CRM/conselho de classe.'
                            : `O profissional receberá um link privado para solicitar cadastro já vinculado a ${selectedAssociation?.nome}.`}
                    </Typography>

                    <FormControl fullWidth sx={{ mb: 2 }} size="small">
                        <InputLabel>Função</InputLabel>
                        <Select
                            value={inviteForm.invite_type === 'staff' ? inviteForm.role : 'member'}
                            label="Função"
                            disabled={inviteForm.invite_type !== 'staff'}
                            onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                        >
                            {inviteForm.invite_type === 'staff' ? (
                                [
                                    <MenuItem key="secretary" value="secretary">👩‍💼 Secretária</MenuItem>,
                                    <MenuItem key="manager" value="manager">🏥 Gestor(a) da Clínica</MenuItem>,
                                    <MenuItem key="admin" value="admin">👑 Administrador(a)</MenuItem>,
                                ]
                            ) : (
                                <MenuItem value="member">🩺 Membro da Equipe Clínica</MenuItem>
                            )}
                        </Select>
                    </FormControl>

                    <TextField
                        margin="dense"
                        name="nome"
                        label="Nome"
                        type="text"
                        fullWidth
                        value={inviteForm.nome}
                        onChange={(e) => setInviteForm({ ...inviteForm, nome: e.target.value })}
                    />
                    <TextField
                        margin="dense"
                        name="email"
                        label="Email"
                        type="email"
                        fullWidth
                        value={inviteForm.email}
                        onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                    />
                    <TextField
                        margin="dense"
                        name="telefone"
                        label="WhatsApp/Telefone"
                        type="text"
                        fullWidth
                        value={inviteForm.telefone}
                        onChange={(e) => setInviteForm({ ...inviteForm, telefone: e.target.value })}
                        helperText="Se não houver email, o sistema gera o link para envio manual por WhatsApp."
                    />
                    {inviteLink && (
                        <TextField
                            margin="dense"
                            label="Link do convite"
                            type="text"
                            fullWidth
                            value={inviteLink}
                            InputProps={{ readOnly: true }}
                            sx={{ mt: 2 }}
                        />
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setInviteOpen(false)} color="secondary">
                        Fechar
                    </Button>
                    {inviteLink && (
                        <Button onClick={() => navigator.clipboard?.writeText(inviteLink)}>
                            Copiar Link
                        </Button>
                    )}
                    <Button onClick={handleInviteSubmit} color="primary" disabled={inviteLoading}>
                        {inviteLoading ? <CircularProgress size={20} /> : 'Gerar Convite'}
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Dialog: Lista de Convites */}
            <Dialog
                open={invitesListOpen}
                onClose={() => setInvitesListOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    Convites — {selectedAssociation?.nome}
                </DialogTitle>
                <DialogContent>
                    {invitesLoading ? (
                        <Box display="flex" justifyContent="center" p={3}>
                            <CircularProgress />
                        </Box>
                    ) : invites.length === 0 ? (
                        <Typography color="text.secondary" sx={{ p: 2 }}>
                            Nenhum convite emitido.
                        </Typography>
                    ) : (
                        <TableContainer component={Paper} variant="outlined">
                            <Table size="small">
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Nome</TableCell>
                                        <TableCell>Email</TableCell>
                                        <TableCell>Tipo</TableCell>
                                        <TableCell>Função</TableCell>
                                        <TableCell>Status</TableCell>
                                        <TableCell>Expira em</TableCell>
                                        <TableCell align="center">Ações</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {invites.map((c) => (
                                        <TableRow key={c.id}>
                                            <TableCell>{c.nome || '—'}</TableCell>
                                            <TableCell>{c.email || c.telefone || '—'}</TableCell>
                                            <TableCell>
                                                <Chip
                                                    size="small"
                                                    label={c.invite_type === 'staff' ? 'Equipe' : 'Profissional'}
                                                    color={c.invite_type === 'staff' ? 'secondary' : 'primary'}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                {c.invite_type === 'staff' && STAFF_ROLE_LABELS[c.role] ? (
                                                    <Chip size="small" label={STAFF_ROLE_LABELS[c.role].label} color={STAFF_ROLE_LABELS[c.role].color} />
                                                ) : (
                                                    <Chip size="small" label="Membro" />
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                <Chip
                                                    size="small"
                                                    label={INVITE_STATUS_LABELS[c.status]?.label || c.status}
                                                    color={INVITE_STATUS_LABELS[c.status]?.color || 'default'}
                                                />
                                            </TableCell>
                                            <TableCell>
                                                {c.expires_at ? new Date(c.expires_at).toLocaleDateString('pt-BR') : '—'}
                                            </TableCell>
                                            <TableCell align="center">
                                                {c.status === 'pending' && (
                                                    <>
                                                        {c.email && (
                                                            <Tooltip title="Reenviar email">
                                                                <IconButton size="small" onClick={() => handleResendInvite(c.id)}>
                                                                    <SendIcon fontSize="small" />
                                                                </IconButton>
                                                            </Tooltip>
                                                        )}
                                                        <Tooltip title="Revogar">
                                                            <IconButton size="small" color="error" onClick={() => handleRevokeInvite(c.id)}>
                                                                <BlockIcon fontSize="small" />
                                                            </IconButton>
                                                        </Tooltip>
                                                    </>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setInvitesListOpen(false)} color="primary">Fechar</Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default AssociationPage;
