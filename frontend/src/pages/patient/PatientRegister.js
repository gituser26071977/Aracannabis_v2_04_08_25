import React, { useState } from 'react';
import {
    Container,
    Paper,
    Typography,
    TextField,
    Button,
    Box,
    Alert,
    Link,
    Stepper,
    Step,
    StepLabel,
    Checkbox,
    FormControlLabel,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    IconButton
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import PrivacyPolicy from '../../components/PrivacyPolicy';

const PatientRegister = () => {
    const navigate = useNavigate();
    const [activeStep, setActiveStep] = useState(0);
    const [cpf, setCpf] = useState('');
    const [email, setEmail] = useState('');
    const [senha, setSenha] = useState('');
    const [confirmarSenha, setConfirmarSenha] = useState('');
    const [pacienteNome, setPacienteNome] = useState('');
    const [consentimentoLgpd, setConsentimentoLgpd] = useState(false);
    const [openPrivacyModal, setOpenPrivacyModal] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const steps = ['Verificar CPF', 'Criar Conta'];

    const formatCPF = (value) => {
        const numbers = value.replace(/\D/g, '');
        if (numbers.length <= 11) {
            return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
        }
        return value;
    };

    const handleCPFChange = (e) => {
        const formatted = formatCPF(e.target.value);
        setCpf(formatted);
    };

    const handleVerifyCPF = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await api.post('/patient-auth/verify-cpf', {
                cpf: cpf.replace(/\D/g, '')
            });

            if (response.data.exists && !response.data.has_account) {
                setPacienteNome(response.data.nome);
                setActiveStep(1);
            } else if (response.data.can_import) {
                setPacienteNome(response.data.nome);
                if (response.data.message) {
                    alert(response.data.message);
                }
                setActiveStep(1);
            } else if (response.data.exists && response.data.has_account) {
                setError('Este CPF já possui conta cadastrada. Faça login.');
            } else {
                setError('CPF não encontrado no sistema. Consulte seu médico para cadastro.');
            }
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao verificar CPF');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setError('');

        // Validações
        if (senha.length < 6) {
            setError('A senha deve ter no mínimo 6 caracteres');
            return;
        }

        if (senha !== confirmarSenha) {
            setError('As senhas não coincidem');
            return;
        }

        if (!consentimentoLgpd) {
            setError('Você deve concordar com a Política de Privacidade para cadastrar-se.');
            return;
        }

        setLoading(true);

        try {
            await api.post('/patient-auth/register', {
                cpf: cpf.replace(/\D/g, ''),
                email,
                senha,
                consentimento_lgpd: consentimentoLgpd
            });

            alert('Conta criada com sucesso! Você será redirecionado para o login.');
            navigate('/patient/login');
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao criar conta');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm" sx={{ mt: 8 }}>
            <Paper elevation={3} sx={{ p: 4 }}>
                <Typography variant="h4" gutterBottom align="center">
                    Portal do Paciente
                </Typography>

                <Typography variant="subtitle1" gutterBottom align="center" color="textSecondary">
                    Cadastre-se
                </Typography>

                <Stepper activeStep={activeStep} sx={{ mt: 3, mb: 3 }}>
                    {steps.map((label) => (
                        <Step key={label}>
                            <StepLabel>{label}</StepLabel>
                        </Step>
                    ))}
                </Stepper>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {activeStep === 0 && (
                    <Box component="form" onSubmit={handleVerifyCPF}>
                        <Typography variant="body2" sx={{ mb: 3 }}>
                            Primeiro, vamos verificar se você está cadastrado em nosso sistema.
                        </Typography>

                        <TextField
                            fullWidth
                            label="CPF"
                            value={cpf}
                            onChange={handleCPFChange}
                            placeholder="000.000.000-00"
                            required
                            sx={{ mb: 3 }}
                            inputProps={{ maxLength: 14 }}
                        />

                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            size="large"
                            disabled={loading || cpf.replace(/\D/g, '').length !== 11}
                        >
                            {loading ? 'Verificando...' : 'Continuar'}
                        </Button>
                    </Box>
                )}

                {activeStep === 1 && (
                    <Box component="form" onSubmit={handleRegister}>
                        <Alert severity="success" sx={{ mb: 3 }}>
                            Olá, <strong>{pacienteNome}</strong>! Crie sua conta abaixo.
                        </Alert>

                        <TextField
                            fullWidth
                            label="Email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            sx={{ mb: 2 }}
                        />

                        <TextField
                            fullWidth
                            label="Senha"
                            type="password"
                            value={senha}
                            onChange={(e) => setSenha(e.target.value)}
                            required
                            helperText="Mínimo 6 caracteres"
                            sx={{ mb: 2 }}
                        />

                        <TextField
                            fullWidth
                            label="Confirmar Senha"
                            type="password"
                            value={confirmarSenha}
                            onChange={(e) => setConfirmarSenha(e.target.value)}
                            required
                            sx={{ mb: 3 }}
                        />

                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={consentimentoLgpd}
                                    onChange={(e) => setConsentimentoLgpd(e.target.checked)}
                                    color="primary"
                                />
                            }
                            label={
                                <Typography variant="body2">
                                    Li e concordo com a{' '}
                                    <Link component="button" variant="body2" onClick={(e) => { e.preventDefault(); setOpenPrivacyModal(true); }}>
                                        Política de Privacidade
                                    </Link>{' '}
                                    (LGPD)
                                </Typography>
                            }
                            sx={{ mb: 3 }}
                        />

                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <Button
                                variant="outlined"
                                onClick={() => setActiveStep(0)}
                                disabled={loading}
                                fullWidth
                            >
                                Voltar
                            </Button>

                            <Button
                                type="submit"
                                variant="contained"
                                disabled={loading}
                                fullWidth
                            >
                                {loading ? 'Criando...' : 'Criar Conta'}
                            </Button>
                        </Box>
                    </Box>
                )}

                <Box sx={{ mt: 3, textAlign: 'center' }}>
                    <Typography variant="body2">
                        Já tem uma conta?{' '}
                        <Link
                            component="button"
                            variant="body2"
                            onClick={() => navigate('/patient/login')}
                        >
                            Fazer login
                        </Link>
                    </Typography>
                </Box>
            </Paper>

            <Dialog
                open={openPrivacyModal}
                onClose={() => setOpenPrivacyModal(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    Política de Privacidade
                    <IconButton
                        aria-label="close"
                        onClick={() => setOpenPrivacyModal(false)}
                        sx={{
                            position: 'absolute',
                            right: 8,
                            top: 8,
                            color: (theme) => theme.palette.grey[500],
                        }}
                    >
                        <CloseIcon />
                    </IconButton>
                </DialogTitle>
                <DialogContent dividers>
                    <PrivacyPolicy />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenPrivacyModal(false)}>
                        Fechar e retornar
                    </Button>
                    <Button onClick={() => {
                        setConsentimentoLgpd(true);
                        setOpenPrivacyModal(false);
                    }} variant="contained" color="primary">
                        Concordar
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default PatientRegister;
