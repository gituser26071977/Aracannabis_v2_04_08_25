/**
 * AcceptStaffInvitePage
 *
 * Página pública (sem JWT) que aceita um convite de STAFF (secretária/gestor)
 * emitido por um gestor/administrador de uma clínica.
 *
 * Fluxo:
 *   1. Carrega `?token=<TOKEN>` (ou via path /convite-staff/<token>)
 *   2. Busca informações do convite via GET /association/professional-invites/<token>
 *   3. Pré-preenche o formulário com nome/email do convite
 *   4. Usuário define telefone + senha e submete via POST /cadastro_profissionais/solicitar-cadastro-staff
 *   5. Sucesso → tela de confirmação com credenciais + botão "Ir para login"
 *
 * Diferenças do CadastroProfissionaisPage:
 *   - NÃO exige CRM/UF (staff não tem conselho de classe)
 *   - Fluxo simplificado (uma única tela)
 *   - Aceita apenas convites com invite_type='staff'
 */
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
    Container, Paper, Typography, TextField, Button, Box, Alert,
    CircularProgress, Card, CardContent, Chip, Divider
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LockIcon from '@mui/icons-material/Lock';
import api from '../services/api';
import associationService from '../services/associationService';

const ROLE_LABELS = {
    secretary: { label: 'Secretária', color: 'secondary' },
    manager: { label: 'Gestor(a) da Clínica', color: 'warning' },
    admin: { label: 'Administrador(a)', color: 'error' },
};

const AcceptStaffInvitePage = () => {
    const params = useParams();
    const location = useLocation();
    const navigate = useNavigate();

    // Token pode vir do path (`/convite-staff/:token`) ou query string
    const token = params.token || new URLSearchParams(location.search).get('token');

    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [convite, setConvite] = useState(null);
    const [form, setForm] = useState({
        nome: '',
        email: '',
        telefone: '',
        senha: '',
        senha_confirmacao: '',
    });
    const [result, setResult] = useState(null);

    useEffect(() => {
        if (!token) {
            setError('Token de convite não encontrado na URL.');
            setLoading(false);
            return;
        }
        fetchConvite(token);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [token]);

    const fetchConvite = async (tk) => {
        try {
            const data = await associationService.getInviteByToken(tk);
            if (!data.success) {
                setError(data.error || 'Convite inválido.');
                return;
            }
            const c = data.convite;
            if (c.invite_type !== 'staff') {
                setError('Este convite não é para equipe administrativa. Use o link correto.');
                return;
            }
            setConvite(c);
            setForm((prev) => ({
                ...prev,
                nome: c.nome || '',
                email: c.email || '',
            }));
        } catch (err) {
            const status = err.response?.status;
            if (status === 404) {
                setError('Convite não encontrado. Verifique se o link está correto.');
            } else if (status === 410) {
                setError('Este convite expirou, foi aceito ou foi revogado pelo gestor.');
            } else {
                setError(err.response?.data?.error || 'Erro ao carregar convite.');
            }
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        // Validações client-side
        if (!form.nome.trim() || form.nome.trim().length < 2) {
            setError('Nome deve ter pelo menos 2 caracteres.');
            return;
        }
        if (!form.email.trim()) {
            setError('Email é obrigatório.');
            return;
        }
        if (form.senha && form.senha.length < 8) {
            setError('Senha deve ter no mínimo 8 caracteres (ou deixe vazio para gerar uma temporária).');
            return;
        }
        if (form.senha && form.senha !== form.senha_confirmacao) {
            setError('As senhas não coincidem.');
            return;
        }

        setSubmitting(true);
        try {
            const payload = {
                convite_token: token,
                nome: form.nome.trim(),
                email: form.email.trim().toLowerCase(),
                telefone: form.telefone.trim() || null,
            };
            if (form.senha) payload.senha = form.senha;

            const response = await api.post(
                '/cadastro_profissionais/solicitar-cadastro-staff',
                payload
            );

            if (response.data.success) {
                setResult(response.data);
            } else {
                setError(response.data.error || 'Erro ao processar cadastro.');
            }
        } catch (err) {
            const status = err.response?.status;
            if (status === 410) {
                setError('Este convite expirou ou já foi utilizado.');
            } else if (status === 409) {
                setError('Já existe um usuário com este email. Faça login ou use outro email.');
            } else if (status === 403) {
                setError(err.response?.data?.error || 'Este convite foi emitido para outro email.');
            } else {
                setError(err.response?.data?.error || 'Erro ao processar cadastro.');
            }
            console.error(err);
        } finally {
            setSubmitting(false);
        }
    };

    // ── Loading ────────────────────────────────────────────────────────
    if (loading) {
        return (
            <Container maxWidth="sm" sx={{ mt: 8, textAlign: 'center' }}>
                <CircularProgress />
                <Typography sx={{ mt: 2 }}>Validando convite...</Typography>
            </Container>
        );
    }

    // ── Convite inválido / expirado ───────────────────────────────────
    if (error && !convite) {
        return (
            <Container maxWidth="sm" sx={{ mt: 8 }}>
                <Paper sx={{ p: 4 }}>
                    <Alert severity="error">{error}</Alert>
                    <Box mt={2} textAlign="center">
                        <Button variant="outlined" onClick={() => navigate('/login')}>
                            Ir para o Login
                        </Button>
                    </Box>
                </Paper>
            </Container>
        );
    }

    // ── Sucesso — mostra credenciais ─────────────────────────────────
    if (result) {
        return (
            <Container maxWidth="sm" sx={{ mt: 8 }}>
                <Paper sx={{ p: 4 }}>
                    <Box textAlign="center" mb={3}>
                        <CheckCircleIcon color="success" sx={{ fontSize: 60 }} />
                        <Typography variant="h5" sx={{ mt: 2 }}>
                            Bem-vindo(a) à equipe de {result.associacao_nome}!
                        </Typography>
                    </Box>

                    <Alert severity="info" sx={{ mb: 2 }}>
                        Sua conta foi criada com sucesso. Guarde suas credenciais em local seguro.
                    </Alert>

                    <Card variant="outlined" sx={{ mb: 2 }}>
                        <CardContent>
                            <Typography variant="body2" color="text.secondary">Usuário</Typography>
                            <Typography variant="h6">{result.usuario}</Typography>

                            <Divider sx={{ my: 1.5 }} />

                            <Typography variant="body2" color="text.secondary">Função</Typography>
                            <Chip
                                label={ROLE_LABELS[result.role]?.label || result.role}
                                color={ROLE_LABELS[result.role]?.color || 'primary'}
                                sx={{ mt: 0.5 }}
                            />
                        </CardContent>
                    </Card>

                    {result.data_expiracao && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                            Sua senha temporária expira em {new Date(result.data_expiracao).toLocaleDateString('pt-BR')}.
                            Faça login e altere-a o quanto antes.
                        </Alert>
                    )}

                    <Typography variant="body2" sx={{ mt: 2 }}>
                        Um email com sua senha temporária foi enviado para <strong>{form.email}</strong> (em modo
                        desenvolvimento, verifique a pasta <code>emails_simulados/</code>).
                    </Typography>

                    <Box mt={3} display="flex" gap={2} justifyContent="center">
                        <Button
                            variant="contained"
                            onClick={() => navigate('/login?next=/secretaria/dashboard')}
                        >
                            Ir para o Login
                        </Button>
                    </Box>
                </Paper>
            </Container>
        );
    }

    // ── Formulário principal ──────────────────────────────────────────
    const roleInfo = ROLE_LABELS[convite.role] || { label: convite.role, color: 'primary' };

    return (
        <Container maxWidth="sm" sx={{ mt: 6, mb: 6 }}>
            <Paper sx={{ p: 4 }}>
                <Box textAlign="center" mb={3}>
                    <Typography variant="h4" color="primary">
                        🏥 {convite.associacao_nome}
                    </Typography>
                    <Typography variant="subtitle1" color="text.secondary" sx={{ mt: 1 }}>
                        Convite para integrar a equipe administrativa
                    </Typography>
                    <Chip
                        label={roleInfo.label}
                        color={roleInfo.color}
                        sx={{ mt: 1.5 }}
                    />
                </Box>

                <Alert severity="info" sx={{ mb: 3 }}>
                    Você foi convidado(a) a fazer parte da equipe de <strong>{convite.associacao_nome}</strong>.
                    Crie sua conta para acessar o AraOS.
                </Alert>

                <form onSubmit={handleSubmit}>
                    <TextField
                        fullWidth
                        margin="normal"
                        label="Nome completo"
                        value={form.nome}
                        onChange={(e) => setForm({ ...form, nome: e.target.value })}
                        required
                    />
                    <TextField
                        fullWidth
                        margin="normal"
                        label="Email"
                        type="email"
                        value={form.email}
                        onChange={(e) => setForm({ ...form, email: e.target.value })}
                        required
                        helperText={convite.email ? 'Este email deve bater com o do convite' : ''}
                    />
                    <TextField
                        fullWidth
                        margin="normal"
                        label="Telefone / WhatsApp"
                        value={form.telefone}
                        onChange={(e) => setForm({ ...form, telefone: e.target.value })}
                    />

                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 2, mb: 1 }}>
                        <LockIcon fontSize="small" sx={{ mr: 1, color: 'action.active' }} />
                        <Typography variant="subtitle2">Defina sua senha</Typography>
                    </Box>

                    <TextField
                        fullWidth
                        margin="dense"
                        label="Senha (deixe vazio para gerar temporária)"
                        type="password"
                        value={form.senha}
                        onChange={(e) => setForm({ ...form, senha: e.target.value })}
                        helperText="Mínimo 8 caracteres"
                    />
                    <TextField
                        fullWidth
                        margin="dense"
                        label="Confirme a senha"
                        type="password"
                        value={form.senha_confirmacao}
                        onChange={(e) => setForm({ ...form, senha_confirmacao: e.target.value })}
                        disabled={!form.senha}
                    />

                    {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        size="large"
                        sx={{ mt: 3 }}
                        disabled={submitting}
                    >
                        {submitting ? <CircularProgress size={20} /> : 'Criar conta e entrar'}
                    </Button>
                </form>

                <Box textAlign="center" mt={2}>
                    <Button size="small" onClick={() => navigate('/login')}>
                        Já tenho conta — voltar para o login
                    </Button>
                </Box>
            </Paper>
        </Container>
    );
};

export default AcceptStaffInvitePage;
