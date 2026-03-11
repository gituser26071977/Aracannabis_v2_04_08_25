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
    CircularProgress,
    IconButton
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { DarkMode, LightMode } from '@mui/icons-material';
import { useColorMode } from '../../contexts/ThemeContext';
import api from '../../services/api';

const PatientLogin = () => {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [senha, setSenha] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { mode, toggleColorMode } = useColorMode();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const response = await api.post('/patient-auth/login', {
                email,
                senha
            });

            // Salvar token
            localStorage.setItem('token', response.data.access_token);
            localStorage.setItem('userType', 'patient');
            localStorage.setItem('user', JSON.stringify(response.data.user));

            // Redirecionar para dashboard
            navigate('/patient/dashboard');
        } catch (err) {
            setError(err.response?.data?.error || 'Erro ao fazer login');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box
            sx={{
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundImage: mode === 'dark' ? 'url(/login-bg.png)' : 'none',
                backgroundColor: mode === 'dark' ? 'transparent' : '#f5f5f5',
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundRepeat: 'no-repeat',
                zIndex: 1000,
                '&::before': mode === 'dark' ? {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    backgroundColor: 'rgba(0, 0, 0, 0.6)',
                    backdropFilter: 'blur(4px)',
                    zIndex: 1
                } : {}
            }}
        >
            {/* Theme Toggle Button */}
            <IconButton
                onClick={toggleColorMode}
                sx={{
                    position: 'absolute',
                    top: 20,
                    right: 20,
                    zIndex: 1002,
                    color: mode === 'dark' ? 'white' : 'primary.main',
                    bgcolor: mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
                    '&:hover': {
                        bgcolor: mode === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)'
                    }
                }}
            >
                {mode === 'dark' ? <LightMode /> : <DarkMode />}
            </IconButton>

            <Paper
                elevation={mode === 'dark' ? 24 : 3}
                sx={{
                    p: 5,
                    width: '100%',
                    maxWidth: 450,
                    position: 'relative',
                    zIndex: 2,
                    backgroundColor: mode === 'dark' ? 'rgba(30, 30, 30, 0.8)' : 'background.paper',
                    backdropFilter: mode === 'dark' ? 'blur(20px)' : 'none',
                    borderRadius: 4,
                    border: mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
                    color: mode === 'dark' ? 'white' : 'text.primary',
                    boxShadow: mode === 'dark' ? '0 8px 32px 0 rgba(0, 0, 0, 0.8)' : 3
                }}
            >
                <Box sx={{ mb: 4, textAlign: 'center' }}>
                    <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" sx={{ color: mode === 'dark' ? '#81c784' : 'primary.main' }}>
                        Portal do Paciente
                    </Typography>
                    <Typography variant="subtitle1" sx={{ opacity: 0.8 }}>
                        Aracannabis - Sua Saúde em Primeiro Lugar
                    </Typography>
                </Box>

                {error && (
                    <Alert severity="error" sx={{ mb: 3, backgroundColor: 'rgba(211, 47, 47, 0.2)', color: '#ffcdd2' }}>
                        {error}
                    </Alert>
                )}

                <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
                    <TextField
                        fullWidth
                        label="Email"
                        type="email"
                        variant="outlined"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        InputLabelProps={{ style: { color: mode === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'inherit' } }}
                        sx={{
                            mb: 2,
                            '& .MuiOutlinedInput-root': {
                                '& fieldset': {
                                    borderColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.23)'
                                },
                                '&:hover fieldset': {
                                    borderColor: mode === 'dark' ? '#81c784' : 'primary.main'
                                },
                                '&.Mui-focused fieldset': {
                                    borderColor: mode === 'dark' ? '#81c784' : 'primary.main'
                                },
                                color: mode === 'dark' ? 'white' : 'inherit'
                            }
                        }}
                    />

                    <TextField
                        fullWidth
                        label="Senha"
                        type="password"
                        variant="outlined"
                        value={senha}
                        onChange={(e) => setSenha(e.target.value)}
                        required
                        InputLabelProps={{ style: { color: mode === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'inherit' } }}
                        sx={{
                            mb: 3,
                            '& .MuiOutlinedInput-root': {
                                '& fieldset': {
                                    borderColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.23)'
                                },
                                '&:hover fieldset': {
                                    borderColor: mode === 'dark' ? '#81c784' : 'primary.main'
                                },
                                '&.Mui-focused fieldset': {
                                    borderColor: mode === 'dark' ? '#81c784' : 'primary.main'
                                },
                                color: mode === 'dark' ? 'white' : 'inherit'
                            }
                        }}
                    />

                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        size="large"
                        disabled={loading}
                        sx={{
                            height: 56,
                            fontSize: '1.1rem',
                            fontWeight: 'bold',
                            borderRadius: 2,
                            boxShadow: '0 4px 14px 0 rgba(46, 125, 50, 0.39)',
                            '&:hover': {
                                boxShadow: '0 6px 20px rgba(46, 125, 50, 0.23)',
                            }
                        }}
                    >
                        {loading ? <CircularProgress size={24} color="inherit" /> : 'Entrar no Portal'}
                    </Button>
                </Box>

                <Box sx={{ mt: 4, textAlign: 'center' }}>
                    <Typography variant="body2" sx={{ opacity: 0.6 }}>
                        Não tem uma conta?{' '}
                        <Button
                            variant="text"
                            size="small"
                            onClick={() => navigate('/patient/register')}
                            sx={{ color: mode === 'dark' ? '#81c784' : 'primary.main', fontWeight: 'bold', textTransform: 'none' }}
                        >
                            Cadastre-se aqui
                        </Button>
                    </Typography>
                </Box>

                <Box sx={{ mt: 2, textAlign: 'center', borderTop: '1px solid rgba(255, 255, 255, 0.1)', pt: 2 }}>
                    <Button
                        variant="text"
                        size="small"
                        onClick={() => navigate('/login')}
                        sx={{ color: mode === 'dark' ? 'rgba(255, 255, 255, 0.5)' : 'text.secondary', textTransform: 'none' }}
                    >
                        Área de Profissionais de Saúde
                    </Button>
                </Box>
            </Paper>
        </Box>
    );
};

export default PatientLogin;
