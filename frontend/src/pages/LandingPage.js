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
    Stack
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import {
    RocketLaunch as RocketIcon,
    Security as SecurityIcon,
    Psychology as BrainIcon,
    Speed as SpeedIcon,
    Devices as DevicesIcon,
    Hub as HubIcon,
    ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const LandingPage = () => {
    const theme = useTheme();
    const { currentUser } = useAuth();

    const features = [
        {
            icon: <HubIcon sx={{ fontSize: 40 }} />,
            title: 'Operational Orchestration',
            description: 'Deterministic runtime connecting clinicians, AI systems and legacy infrastructure through supervised execution pipelines.'
        },
        {
            icon: <BrainIcon sx={{ fontSize: 40 }} />,
            title: 'Clinical Intelligence',
            description: 'Context-aware operational intelligence that augments clinical workflows without replacing human judgment.'
        },
        {
            icon: <SecurityIcon sx={{ fontSize: 40 }} />,
            title: 'Audit & Compliance',
            description: 'Full traceability, audit trails and LGPD compliance with end-to-end encryption and deterministic replay.'
        },
        {
            icon: <SpeedIcon sx={{ fontSize: 40 }} />,
            title: 'High Performance Runtime',
            description: 'Distributed execution engine designed for operational continuity in healthcare environments.'
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
                        <Grid item xs={12} md={7}>
                            <Typography
                                variant="overline"
                                sx={{ opacity: 0.8, letterSpacing: 3, fontWeight: 600 }}
                            >
                                VisualSmartFlow Platform
                            </Typography>
                            <Typography
                                variant="h2"
                                fontWeight="800"
                                gutterBottom
                                sx={{
                                    fontSize: { xs: '2.2rem', md: '3.2rem' },
                                    textShadow: '0px 2px 4px rgba(0,0,0,0.2)',
                                    mt: 1
                                }}
                            >
                                Operational Intelligence Infrastructure for Healthcare
                            </Typography>
                            <Typography variant="h6" sx={{ mb: 4, opacity: 0.9, maxWidth: 600 }}>
                                Connecting clinicians, AI and legacy systems through a deterministic, auditable and supervised operational runtime.
                            </Typography>
                            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
                                <Button
                                    component={RouterLink}
                                    to="/login"
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
                                    Explore AraOS
                                </Button>
                                <Button
                                    component={RouterLink}
                                    to="/cadastro-profissionais"
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
                                    Request Demo
                                </Button>
                            </Stack>
                        </Grid>
                        <Grid item xs={12} md={5} sx={{ display: { xs: 'none', md: 'block' } }}>
                            <Box
                                sx={{
                                    width: '100%',
                                    height: 320,
                                    borderRadius: 4,
                                    bgcolor: alpha('#fff', 0.08),
                                    border: `1px solid ${alpha('#fff', 0.15)}`,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexDirection: 'column',
                                    gap: 2
                                }}
                            >
                                <HubIcon sx={{ fontSize: 80, opacity: 0.4 }} />
                                <Typography variant="h6" sx={{ opacity: 0.6 }}>
                                    Distributed Runtime
                                </Typography>
                            </Box>
                        </Grid>
                    </Grid>
                </Container>
            </Box>

            {/* AraOS Product Banner */}
            <Box sx={{ bgcolor: 'grey.900', color: 'white', py: 4 }}>
                <Container maxWidth="lg">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
                        <Typography variant="h6" fontWeight="bold" sx={{ color: theme.palette.secondary.main }}>
                            AraOS
                        </Typography>
                        <Typography variant="body1" sx={{ opacity: 0.7 }}>
                            — Clinical Operations Module running on VisualSmartFlow Platform
                        </Typography>
                        <Button
                            component={RouterLink}
                            to="/login"
                            variant="outlined"
                            size="small"
                            sx={{
                                color: theme.palette.secondary.main,
                                borderColor: theme.palette.secondary.main,
                                '&:hover': { borderColor: theme.palette.secondary.light, bgcolor: alpha(theme.palette.secondary.main, 0.1) }
                            }}
                        >
                            Launch AraOS <ArrowForwardIcon fontSize="small" sx={{ ml: 0.5 }} />
                        </Button>
                    </Box>
                </Container>
            </Box>

            {/* Features Section */}
            <Container maxWidth="lg" sx={{ py: 10 }}>
                <Box sx={{ textAlign: 'center', mb: 8 }}>
                    <Typography variant="overline" color="primary" fontWeight="bold" letterSpacing={2}>
                        PLATFORM CAPABILITIES
                    </Typography>
                    <Typography variant="h3" fontWeight="bold" sx={{ mt: 1 }}>
                        Everything you need in one operational runtime
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

            {/* CTA Section */}
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
                        Ready to transform your clinical operations?
                    </Typography>
                    <Typography variant="h6" sx={{ mb: 4, opacity: 0.9, position: 'relative' }}>
                        Deploy AraOS on your VisualSmartFlow runtime. Start today.
                    </Typography>
                    <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} justifyContent="center" sx={{ position: 'relative' }}>
                        <Button
                            component={RouterLink}
                            to="/login"
                            variant="contained"
                            color="secondary"
                            size="large"
                            endIcon={<ArrowForwardIcon />}
                            sx={{ px: 4, py: 1.5, fontSize: '1.1rem', fontWeight: 'bold' }}
                        >
                            Launch AraOS
                        </Button>
                        <Button
                            component={RouterLink}
                            to="/cadastro-profissionais"
                            variant="outlined"
                            color="inherit"
                            size="large"
                            sx={{ px: 4, py: 1.5, fontSize: '1.1rem', borderWidth: 2 }}
                        >
                            Request Access
                        </Button>
                    </Stack>
                </Box>
            </Container>

            {/* Footer */}
            <Box sx={{ bgcolor: 'grey.50', py: 4, borderTop: '1px solid', borderColor: 'divider' }}>
                <Container maxWidth="lg">
                    <Box sx={{ textAlign: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                            AraOS • Powered by VisualSmartFlow Platform
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                            © {new Date().getFullYear()} Arapath. All rights reserved.
                        </Typography>
                    </Box>
                </Container>
            </Box>
        </Box>
    );
};

export default LandingPage;
