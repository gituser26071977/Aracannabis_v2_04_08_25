import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Container, Paper, Typography, Box, Button, CircularProgress } from '@mui/material';
import { CheckCircle, Error, HourglassEmpty, Home } from '@mui/icons-material';

const PaymentStatusPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [status, setStatus] = useState('loading');

    useEffect(() => {
        // Determinar status baseado na URL
        if (location.pathname.includes('pagamento-sucesso')) {
            setStatus('success');
        } else if (location.pathname.includes('pagamento-erro')) {
            setStatus('error');
        } else if (location.pathname.includes('pagamento-pendente')) {
            setStatus('pending');
        }
    }, [location]);

    const renderContent = () => {
        switch (status) {
            case 'success':
                return (
                    <>
                        <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
                        <Typography variant="h4" gutterBottom color="success.main">
                            Pagamento Aprovado!
                        </Typography>
                        <Typography variant="body1" paragraph align="center">
                            Sua assinatura foi ativada com sucesso. Você já pode acessar todos os recursos do sistema.
                        </Typography>
                        <Button
                            variant="contained"
                            size="large"
                            onClick={() => navigate('/login')}
                            sx={{ mt: 2 }}
                        >
                            Acessar Sistema
                        </Button>
                    </>
                );
            case 'error':
                return (
                    <>
                        <Error sx={{ fontSize: 80, color: 'error.main', mb: 2 }} />
                        <Typography variant="h4" gutterBottom color="error.main">
                            Erro no Pagamento
                        </Typography>
                        <Typography variant="body1" paragraph align="center">
                            Houve um problema ao processar seu pagamento. Por favor, tente novamente ou entre em contato com o suporte.
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                            <Button variant="outlined" onClick={() => navigate('/')}>
                                Voltar ao Início
                            </Button>
                            <Button variant="contained" onClick={() => navigate('/planos')}>
                                Tentar Novamente
                            </Button>
                        </Box>
                    </>
                );
            case 'pending':
                return (
                    <>
                        <HourglassEmpty sx={{ fontSize: 80, color: 'warning.main', mb: 2 }} />
                        <Typography variant="h4" gutterBottom color="warning.main">
                            Pagamento em Análise
                        </Typography>
                        <Typography variant="body1" paragraph align="center">
                            Seu pagamento está sendo processado. Assim que for confirmado, você receberá um email e seu acesso será liberado.
                        </Typography>
                        <Button variant="outlined" onClick={() => navigate('/')} sx={{ mt: 2 }}>
                            Voltar ao Início
                        </Button>
                    </>
                );
            default:
                return <CircularProgress />;
        }
    };

    return (
        <Container maxWidth="sm">
            <Paper elevation={3} sx={{ p: 4, mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                {renderContent()}
            </Paper>
        </Container>
    );
};

export default PaymentStatusPage;
