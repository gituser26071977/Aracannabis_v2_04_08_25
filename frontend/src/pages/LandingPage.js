import React from 'react';
import {
    Box,
    Container,
    Typography,
    Button,
    Grid,
    Card,
    CardContent,
    useTheme,
    alpha,
    Avatar,
    Stack
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import {
    RocketLaunch as RocketIcon,
    Security as SecurityIcon,
    Psychology as BrainIcon,
    Speed as SpeedIcon,
    Devices as DevicesIcon,
    SupportAgent as SupportIcon,
    CheckCircle as CheckIcon,
    ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const LandingPage = () => {
    const theme = useTheme();
    const { currentUser } = useAuth();

    const features = [
        {
            icon: <BrainIcon sx={{ fontSize: 40 }} />,
            title: 'IA Assistiva Avançada',
            description: 'Assistentes inteligentes que ajudam na análise clínica, sugestão de tratamentos e monitoramento de pacientes.'
        },
        {
            icon: <SecurityIcon sx={{ fontSize: 40 }} />,
            title: 'Segurança & LGPD',
            description: 'Seus dados protegidos com criptografia de ponta a ponta e total conformidade com a legislação vigente.'
        },
        {
            icon: <DevicesIcon sx={{ fontSize: 40 }} />,
            title: 'Acesso Multiplataforma',
            description: 'Acesse de qualquer lugar. Desktop, tablet ou celular com experiência otimizada e sincronização em tempo real.'
        },
        {
            icon: <SpeedIcon sx={{ fontSize: 40 }} />,
            title: 'Alta Performance',
            description: 'Interface fluida e responsiva projetada para agilizar o atendimento médico sem travamentos.'
        }
    ];

    return (
        <Box sx={{ overflowX: 'hidden' }}>
            {/* Hero Section */}
            <Box
                sx={{
                    position: 'relative',
                    bgcolor: 'primary.main',
                    color: 'white',
                    pt: { xs: 8, md: 12 },
                    pb: { xs: 8, md: 12 },
                    overflow: 'hidden',
                    background: `linear-gradient(135deg, ${theme.palette.primary.dark} 0%, ${theme.palette.primary.main} 100%)`
                }}
            >
                {/* Abstract Background Shapes */}
                <Box
                    sx={{
                        position: 'absolute',
                        top: -100,
                        right: -100,
                        width: 400,
                        height: 400,
                        borderRadius: '50%',
                        bgcolor: alpha('#fff', 0.1),
                        zIndex: 0
                    }}
                />
                <Box
                    sx={{
                        position: 'absolute',
                        bottom: -50,
                        left: -50,
                        width: 200,
                        height: 200,
                        borderRadius: '50%',
                        bgcolor: alpha('#fff', 0.05),
                        zIndex: 0
                    }}
                />

                <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
                    <Grid container spacing={4} alignItems="center">
                        <Grid item xs={12} md={6}>
                            <Typography
                                variant="h2"
                                fontWeight="800"
                                gutterBottom
                                sx={{
                                    fontSize: { xs: '2.5rem', md: '3.5rem' },
                                    textShadow: '0px 2px 4px rgba(0,0,0,0.2)'
                                }}
                            >
                                O Futuro da <br />
                                <Box component="span" sx={{ color: theme.palette.secondary.main }}>Cannabis Medicinal</Box>
                            </Typography>
                            <Typography variant="h6" sx={{ mb: 4, opacity: 0.9, maxWidth: 500 }}>
                                O sistema de prontuário eletrônico maia avançado do mercado. Inteligência Artificial, segurança total e facilidade de uso em uma única plataforma.
                            </Typography>
                            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                                {currentUser ? (
                                    <Button
                                        component={RouterLink}
                                        to="/dashboard"
                                        variant="contained"
                                        color="secondary"
                                        size="large"
                                        endIcon={<ArrowForwardIcon />}
                                        sx={{
                                            px: 4,
                                            py: 1.5,
                                            borderRadius: 2,
                                            fontSize: '1.1rem',
                                            fontWeight: 'bold',
                                            boxShadow: theme.shadows[4]
                                        }}
                                    >
                                        Acessar Sistema
                                    </Button>
                                ) : (
                                    <Button
                                        component={RouterLink}
                                        to="/cadastro-profissionais"
                                        variant="contained"
                                        color="secondary"
                                        size="large"
                                        endIcon={<RocketIcon />}
                                        sx={{
                                            px: 4,
                                            py: 1.5,
                                            borderRadius: 2,
                                            fontSize: '1.1rem',
                                            fontWeight: 'bold',
                                            boxShadow: theme.shadows[4]
                                        }}
                                    >
                                        Começar Agora
                                    </Button>
                                )}
                                <Button
                                    component={RouterLink}
                                    to="/planos"
                                    variant="outlined"
                                    color="inherit"
                                    size="large"
                                    sx={{
                                        px: 4,
                                        py: 1.5,
                                        borderRadius: 2,
                                        fontSize: '1.1rem',
                                        borderWidth: 2,
                                        '&:hover': { borderWidth: 2, bgcolor: alpha('#fff', 0.1) }
                                    }}
                                >
                                    Ver Planos
                                </Button>
                            </Stack>
                        </Grid>
                        <Grid item xs={12} md={6} sx={{ display: { xs: 'none', md: 'block' } }}>
                            {/* Mockup / Image Placeholder */}
                            <Box
                                component="img"
                                src="/assets/dashboard-mockup.png"
                                alt="Dashboard do Sistema Aracannabis"
                                sx={{
                                    width: '100%',
                                    height: 'auto',
                                    display: 'block',
                                    borderRadius: 4,
                                    boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
                                    transform: 'perspective(1000px) rotateY(-5deg) rotateX(2deg)',
                                    transition: 'transform 0.5s ease',
                                    '&:hover': {
                                        transform: 'perspective(1000px) rotateY(0deg) rotateX(0deg) scale(1.02)'
                                    }
                                }}
                            />
                        </Grid>
                    </Grid>
                </Container>
            </Box>

            {/* Features Section */}
            <Container maxWidth="lg" sx={{ py: 10 }}>
                <Box sx={{ textAlign: 'center', mb: 8 }}>
                    <Typography variant="overline" color="primary" fontWeight="bold" letterSpacing={2}>
                        POR QUE ESCOLHER O ARACANNABIS?
                    </Typography>
                    <Typography variant="h3" fontWeight="bold" sx={{ mt: 1 }}>
                        Tudo o que você precisa em um só lugar
                    </Typography>
                </Box>

                <Grid container spacing={4}>
                    {features.map((feature, index) => (
                        <Grid item xs={12} md={6} lg={3} key={index}>
                            <Card
                                sx={{
                                    height: '100%',
                                    borderRadius: 4,
                                    transition: 'transform 0.3s ease',
                                    '&:hover': {
                                        transform: 'translateY(-8px)',
                                        boxShadow: theme.shadows[8]
                                    }
                                }}
                                elevation={1}
                            >
                                <CardContent sx={{ p: 4, textAlign: 'center' }}>
                                    <Box
                                        sx={{
                                            mb: 2,
                                            color: 'primary.main',
                                            p: 2,
                                            borderRadius: '50%',
                                            bgcolor: alpha(theme.palette.primary.main, 0.1),
                                            display: 'inline-flex'
                                        }}
                                    >
                                        {feature.icon}
                                    </Box>
                                    <Typography variant="h6" fontWeight="bold" gutterBottom>
                                        {feature.title}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {feature.description}
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            </Container>

            {/* Social Proof / Trust Section */}
            <Box sx={{ bgcolor: 'grey.50', py: 8 }}>
                <Container maxWidth="lg">
                    <Grid container spacing={4} alignItems="center" justifyContent="center">
                        <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
                            <Typography variant="h2" color="primary.main" fontWeight="bold">
                                +5.000
                            </Typography>
                            <Typography variant="h6" color="text.secondary">
                                Pacientes Atendidos
                            </Typography>
                        </Grid>
                        <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
                            <Typography variant="h2" color="primary.main" fontWeight="bold">
                                99.9%
                            </Typography>
                            <Typography variant="h6" color="text.secondary">
                                Uptime Garantido
                            </Typography>
                        </Grid>
                        <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
                            <Typography variant="h2" color="primary.main" fontWeight="bold">
                                24/7
                            </Typography>
                            <Typography variant="h6" color="text.secondary">
                                Suporte Especializado
                            </Typography>
                        </Grid>
                    </Grid>
                </Container>
            </Box>

            {/* CTA Plans Section */}
            <Container maxWidth="md" sx={{ py: 10 }}>
                <Box
                    sx={{
                        borderRadius: 4,
                        bgcolor: 'primary.dark',
                        color: 'white',
                        p: { xs: 4, md: 8 },
                        textAlign: 'center',
                        position: 'relative',
                        overflow: 'hidden'
                    }}
                >
                    <Box
                        sx={{
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            width: '100%',
                            height: '100%',
                            backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.05\'%3E%3Cpath d=\'M36 REDACTED 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
                        }}
                    />

                    <Typography variant="h3" fontWeight="bold" gutterBottom sx={{ position: 'relative' }}>
                        Pronto para transformar sua clínica?
                    </Typography>
                    <Typography variant="h6" sx={{ mb: 4, opacity: 0.9, position: 'relative' }}>
                        Escolha o plano ideal e comece a usar hoje mesmo. Sem cartão de crédito para testar.
                    </Typography>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center" sx={{ position: 'relative' }}>
                        <Button
                            component={RouterLink}
                            to="/planos"
                            variant="contained"
                            color="secondary"
                            size="large"
                            endIcon={<ArrowForwardIcon />}
                            sx={{ px: 4, py: 1.5, fontSize: '1.1rem', fontWeight: 'bold' }}
                        >
                            Ver Planos e Preços
                        </Button>
                    </Stack>
                </Box>
            </Container>
        </Box>
    );
};

export default LandingPage;
