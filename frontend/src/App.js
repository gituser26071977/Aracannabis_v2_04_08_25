import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { DarkMode, LightMode } from '@mui/icons-material';
import { ThemeContextProvider, useColorMode } from './contexts/ThemeContext';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import MenuIcon from '@mui/icons-material/Menu';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import { useAuth } from './contexts/AuthContext';
import { AssociationProvider } from './contexts/AssociationContext';
import AssociationSelector from './components/AssociationSelector';

// Importar páginas
import PacientesPageComponent from './pages/PacientesPage';
import PatientDetailPage from './pages/PatientDetailPage';
import PatientEditPage from './pages/PatientEditPage';
import SecurityPage from './pages/SecurityPage';
import ConsultasPage from './pages/ConsultasPage';
import SimpleLogin from './components/SimpleLogin';
import CadastroProfissionaisPage from './pages/CadastroProfissionaisPage';
import PagamentoPage from './pages/PagamentoPage';
import PlanosPage from './pages/PlanosPage';
import LandingPage from './pages/LandingPage';
import AdminPage from './pages/AdminPage';

import InternalDashboard from './pages/InternalDashboard';
import AIDashboard from './pages/AIDashboard';
import AIChatPage from './pages/AIChatPage';
import BillingPage from './pages/BillingPage';
import FaturamentoPage from './pages/FaturamentoPage';
import DailyBoardPage from './pages/DailyBoardPage';
import OnboardingPacientesPage from './pages/OnboardingPacientesPage';
import GestaoPage from './pages/GestaoPage';
import CertificacaoDigitalPage from './pages/CertificacaoDigitalPage';
import AIConfigPage from './pages/AIConfigPage';
import PasswordSetupRequestPage from './pages/PasswordSetupRequestPage';
import DefinePasswordPage from './pages/DefinePasswordPage';
import MobileUploadPage from './pages/MobileUploadPage';
import PaymentStatusPage from './pages/PaymentStatusPage';
import BatchImportPage from './pages/BatchImportPage';
import IntelligentImportPage from './pages/IntelligentImportPage';
import AssociationPage from './pages/association/AssociationPage';
import MembersPage from './pages/association/MembersPage';
import StockPage from './pages/association/StockPage';
import DispensationPage from './pages/association/DispensationPage';
import ConfiguracaoPrescricaoPage from './pages/ConfiguracaoPrescricaoPage';
import ConfiguracaoIAPage from './pages/ConfiguracaoIAPage';
import CatalogoPage from './pages/CatalogoPage';
import OnboardingPage from './pages/OnboardingPage';
import TrialEndingPage from './pages/TrialEndingPage';
import VerifyEmailPage from './pages/VerifyEmailPage';
import ModulosPage from './pages/ModulosPage';
import TrialBanner from './components/TrialBanner';
import ErrorBoundary from './components/ErrorBoundary';
import NotFoundPage from './pages/NotFoundPage';
import UnauthorizedPage from './pages/UnauthorizedPage';
import ForbiddenPage from './pages/ForbiddenPage';
import ServerErrorPage from './pages/ServerErrorPage';

import NavigationMenu from './components/NavigationMenu';

// Patient Portal Pages
import PatientLogin from './pages/patient/PatientLogin';
import PatientRegister from './pages/patient/PatientRegister';
import PatientDashboard from './pages/patient/PatientDashboard';

const APP_TITLE = 'AraOS';
// Tema personalizado
// Theme removed from here as it is now managed by ThemeContext

// Componente de rota protegida
function ProtectedRoute({ children }) {
  const { currentUser } = useAuth();
  const location = useLocation();

  if (!currentUser) {
    return <Navigate to="/401" replace />;
  }

  // Bloqueio suave: se trial expirou, redirecionar para trial-ending (exceto se já estiver lá)
  if (location.pathname !== '/trial-ending' && currentUser.data_expiracao) {
    const exp = new Date(currentUser.data_expiracao);
    const now = new Date();
    if (exp < now && currentUser.role !== 'admin' && currentUser.role !== 'superadmin') {
      return <Navigate to="/trial-ending" replace />;
    }
  }

  return children;
}

// Componente de rota administrativa (apenas admin)
function AdminRoute({ children }) {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return <Navigate to="/401" replace />;
  }

  if (currentUser.role !== 'admin') {
    return <Navigate to="/403" replace />;
  }

  return children;
}

// Home por perfil: assistencial = Daily Board (lista do dia); demais = dashboard.
function HomeByProfile() {
  const { currentUser } = useAuth();
  const perfil =
    currentUser?.perfil_efetivo ||
    (currentUser?.role === 'admin' || currentUser?.role === 'superadmin' ? 'solo' : 'assistencial');
  if (perfil === 'assistencial') {
    return <DailyBoardPage />;
  }
  return <InternalDashboard />;
}

// ===== PAGE TRANSITION WRAPPER =====
function LoginPage() {
  const [usuario, setUsuario] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [loginError, setLoginError] = useState('');
  const { login, error } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoading(true);

    try {
      await login(usuario, senha);
    } catch (error) {
      setLoginError(error.error || error.message || 'Falha ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  const { mode, toggleColorMode } = useColorMode();

  const bgGradient =
    mode === 'dark'
      ? 'radial-gradient(ellipse at 20% 0%, #0d2f28 0%, #0a1512 40%, #050a08 100%)'
      : 'radial-gradient(ellipse at 20% 0%, #e0f2e9 0%, #f0f4f1 40%, #e8ecea 100%)';

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
        background: bgGradient,
        zIndex: 1000,
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          opacity: mode === 'dark' ? 0.04 : 0.025,
          pointerEvents: 'none',
        },
      }}
    >
      {/* Floating decorative elements */}
      <Box
        sx={{
          position: 'absolute',
          top: '10%',
          left: '10%',
          width: 200,
          height: 200,
          borderRadius: '50%',
          background:
            mode === 'dark'
              ? 'radial-gradient(circle, rgba(0,212,170,0.08) 0%, transparent 70%)'
              : 'radial-gradient(circle, rgba(13,115,119,0.06) 0%, transparent 70%)',
          filter: 'blur(40px)',
          animation: 'float 6s ease-in-out infinite',
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: '15%',
          right: '15%',
          width: 300,
          height: 300,
          borderRadius: '50%',
          background:
            mode === 'dark'
              ? 'radial-gradient(circle, rgba(245,166,35,0.06) 0%, transparent 70%)'
              : 'radial-gradient(circle, rgba(245,166,35,0.04) 0%, transparent 70%)',
          filter: 'blur(50px)',
          animation: 'float 8s ease-in-out infinite reverse',
        }}
      />

      {/* Theme Toggle Button */}
      <IconButton
        onClick={toggleColorMode}
        sx={{
          position: 'absolute',
          top: 24,
          right: 24,
          zIndex: 1002,
          color: 'text.primary',
          bgcolor: mode === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.04)',
          backdropFilter: 'blur(8px)',
          border: `1px solid ${mode === 'dark' ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.06)'}`,
          transition: 'all 0.3s ease',
          '&:hover': {
            bgcolor: mode === 'dark' ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.08)',
            transform: 'scale(1.1) rotate(15deg)',
          },
        }}
      >
        {mode === 'dark' ? <LightMode /> : <DarkMode />}
      </IconButton>

      <Paper
        elevation={0}
        sx={{
          p: { xs: 3, sm: 5 },
          width: '100%',
          maxWidth: 460,
          position: 'relative',
          zIndex: 2,
          background: mode === 'dark' ? 'rgba(26, 31, 29, 0.75)' : 'rgba(255, 255, 255, 0.72)',
          backdropFilter: 'blur(24px) saturate(180%)',
          WebkitBackdropFilter: 'blur(24px) saturate(180%)',
          borderRadius: '24px',
          border: `1px solid ${mode === 'dark' ? 'rgba(0,212,170,0.1)' : 'rgba(13,115,119,0.1)'}`,
          boxShadow:
            mode === 'dark'
              ? '0 25px 50px rgba(0,0,0,0.35), 0 0 0 1px rgba(0,212,170,0.05)'
              : '0 25px 50px rgba(0,0,0,0.08), 0 0 0 1px rgba(13,115,119,0.05)',
          animation: 'scaleIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards',
          '@keyframes scaleIn': {
            from: { opacity: 0, transform: 'scale(0.95) translateY(10px)' },
            to: { opacity: 1, transform: 'scale(1) translateY(0)' },
          },
        }}
      >
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          <Typography
            variant="h3"
            component="h1"
            gutterBottom
            fontWeight={800}
            sx={{
              background:
                mode === 'dark'
                  ? 'linear-gradient(135deg, #00d4aa 0%, #33ddbf 50%, #ffd166 100%)'
                  : 'linear-gradient(135deg, #0d7377 0%, #14a085 50%, #f5a623 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              letterSpacing: '-0.03em',
              fontSize: { xs: '2rem', sm: '2.5rem' },
            }}
          >
            AraOS
          </Typography>
          <Typography
            variant="subtitle1"
            sx={{
              opacity: 0.7,
              fontWeight: 500,
              letterSpacing: '0.02em',
            }}
          >
            Powered by VisualSmartFlow Platform
          </Typography>
        </Box>

        {(loginError || error) && (
          <Alert
            severity="error"
            sx={{
              mb: 3,
              animation: 'shake 0.5s ease',
              '@keyframes shake': {
                '0%, 100%': { transform: 'translateX(0)' },
                '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-4px)' },
                '20%, 40%, 60%, 80%': { transform: 'translateX(4px)' },
              },
            }}
          >
            {loginError || error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            label="👤 Usuário"
            variant="outlined"
            fullWidth
            margin="normal"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            required
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '14px',
                transition: 'all 0.3s ease',
              },
            }}
          />
          <TextField
            label="🔒 Senha"
            type="password"
            variant="outlined"
            fullWidth
            margin="normal"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: '14px',
                transition: 'all 0.3s ease',
              },
            }}
          />

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <Button
              component={Link}
              to="/definir-senha/solicitar"
              size="small"
              sx={{
                textTransform: 'none',
                fontWeight: 600,
                color: 'secondary.main',
                position: 'relative',
                '&::after': {
                  content: '""',
                  position: 'absolute',
                  bottom: 2,
                  left: 0,
                  width: 0,
                  height: '1px',
                  background: 'currentColor',
                  transition: 'width 0.3s ease',
                },
                '&:hover::after': {
                  width: '100%',
                },
              }}
            >
              Esqueceu a senha?
            </Button>
          </Box>

          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{
              mt: 4,
              height: 56,
              fontSize: '1.05rem',
              fontWeight: 700,
              borderRadius: '14px',
              background:
                mode === 'dark'
                  ? 'linear-gradient(135deg, #00d4aa 0%, #33ddbf 100%)'
                  : 'linear-gradient(135deg, #0d7377 0%, #14a085 100%)',
              boxShadow:
                mode === 'dark'
                  ? '0 4px 20px rgba(0,212,170,0.35)'
                  : '0 4px 20px rgba(13,115,119,0.30)',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                transform: 'scale(1.02) translateY(-2px)',
                boxShadow:
                  mode === 'dark'
                    ? '0 8px 30px rgba(0,212,170,0.45)'
                    : '0 8px 30px rgba(13,115,119,0.40)',
              },
              '&:active': {
                transform: 'scale(0.98)',
              },
            }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} sx={{ color: 'inherit' }} /> : '✨ Entrar'}
          </Button>
        </form>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" sx={{ opacity: 0.5, mb: 0.5 }}>
            Novo por aqui?
          </Typography>
          <Button
            component={Link}
            to="/cadastro-profissionais"
            variant="text"
            sx={{
              textTransform: 'none',
              fontWeight: 700,
              color: 'primary.main',
              position: 'relative',
              '&::after': {
                content: '""',
                position: 'absolute',
                bottom: 2,
                left: 0,
                width: 0,
                height: '2px',
                background: 'currentColor',
                transition: 'width 0.3s ease',
                borderRadius: '1px',
              },
              '&:hover::after': {
                width: '100%',
              },
            }}
          >
            👨‍⚕️ Solicite seu cadastro como profissional
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}

function App() {
  return (
    <ThemeContextProvider>
      <AppContent />
    </ThemeContextProvider>
  );
}

function AppContent() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { currentUser } = useAuth();
  const location = useLocation();
  const { mode, toggleColorMode } = useColorMode();

  const isLoginPage = location.pathname === '/login' || location.pathname === '/patient/login';
  const isOnboardingPage = location.pathname === '/onboarding';
  const showTrialBanner = currentUser && !isLoginPage && !isOnboardingPage;

  // Scroll-aware AppBar
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  return (
    <ErrorBoundary>
      <AssociationProvider>
        {showTrialBanner && <TrialBanner />}
        {!isLoginPage && (
          <AppBar
            position="sticky"
            elevation={scrolled ? 2 : 0}
            sx={{
              transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
              bgcolor: scrolled
                ? mode === 'dark'
                  ? 'rgba(10,15,13,0.85)'
                  : 'rgba(255,255,255,0.85)'
                : mode === 'dark'
                  ? 'transparent'
                  : 'transparent',
              backdropFilter: scrolled ? 'blur(20px) saturate(180%)' : 'none',
              WebkitBackdropFilter: scrolled ? 'blur(20px) saturate(180%)' : 'none',
              borderBottom: scrolled
                ? `1px solid ${mode === 'dark' ? 'rgba(0,212,170,0.08)' : 'rgba(13,115,119,0.08)'}`
                : '1px solid transparent',
            }}
          >
            <Toolbar sx={{ minHeight: { xs: 56, sm: 64 } }}>
              <IconButton
                edge="start"
                color="inherit"
                aria-label="menu"
                onClick={toggleMenu}
                sx={{
                  mr: 2,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    transform: 'scale(1.1)',
                    bgcolor: (theme) => `${theme.palette.primary.main}14`,
                  },
                }}
              >
                <MenuIcon />
              </IconButton>

              <Typography
                variant="h6"
                component="div"
                sx={{
                  flexGrow: 1,
                  fontWeight: 800,
                  letterSpacing: '-0.02em',
                  background:
                    mode === 'dark'
                      ? 'linear-gradient(135deg, #00d4aa 0%, #ffd166 100%)'
                      : 'linear-gradient(135deg, #0d7377 0%, #14a085 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  fontSize: { xs: '1.1rem', sm: '1.25rem' },
                }}
              >
                🌿 {APP_TITLE}
              </Typography>

              {/* Association Selector for SaaS */}
              {currentUser && <AssociationSelector />}

              <IconButton
                color="inherit"
                onClick={toggleColorMode}
                aria-label={mode === 'dark' ? 'Ativar modo claro' : 'Ativar modo escuro'}
                sx={{
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'rotate(20deg) scale(1.1)',
                    bgcolor: (theme) => `${theme.palette.primary.main}14`,
                  },
                }}
              >
                {mode === 'dark' ? <LightMode /> : <DarkMode />}
              </IconButton>

              {currentUser && (
                <Typography
                  variant="body2"
                  sx={{
                    mr: 2,
                    ml: 2,
                    fontWeight: 600,
                    opacity: 0.8,
                    display: { xs: 'none', sm: 'block' },
                  }}
                >
                  👋 Olá, {currentUser.nome}
                </Typography>
              )}
              {currentUser ? (
                <Button
                  color="inherit"
                  onClick={() =>
                    window.open(`${process.env.REACT_APP_API_URL || ''}/api/status`, '_blank')
                  }
                  target="_blank"
                  disabled={!process.env.REACT_APP_API_URL}
                  sx={{
                    textTransform: 'none',
                    fontWeight: 600,
                    borderRadius: '10px',
                    px: 2,
                    display: { xs: 'none', sm: 'flex' },
                    '&:hover': {
                      bgcolor: (theme) => `${theme.palette.primary.main}14`,
                    },
                  }}
                >
                  🔌 API
                </Button>
              ) : (
                <Button
                  color="inherit"
                  component={Link}
                  to="/login"
                  sx={{
                    textTransform: 'none',
                    fontWeight: 600,
                    borderRadius: '10px',
                    px: 2,
                    '&:hover': {
                      bgcolor: (theme) => `${theme.palette.primary.main}14`,
                    },
                  }}
                >
                  🔑 Login
                </Button>
              )}
            </Toolbar>
          </AppBar>
        )}
        <NavigationMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
        <Container
          maxWidth={isLoginPage ? false : 'xl'}
          sx={isLoginPage ? { p: 0, m: 0 } : { mt: { xs: 2, sm: 4 }, mb: { xs: 2, sm: 4 } }}
        >
          <Routes>
            <Route path="/" element={<LandingPage />} />

            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <HomeByProfile />
                </ProtectedRoute>
              }
            />
            <Route path="/definir-senha/solicitar" element={<PasswordSetupRequestPage />} />
            <Route path="/definir-senha" element={<DefinePasswordPage />} />
            <Route path="/pagamento" element={<PagamentoPage />} />
            <Route path="/planos" element={<PlanosPage />} />
            <Route path="/cadastro-profissionais" element={<CadastroProfissionaisPage />} />
            <Route path="/verificar-email" element={<VerifyEmailPage />} />
            <Route
              path="/onboarding"
              element={
                <ProtectedRoute>
                  <OnboardingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/trial-ending"
              element={
                <ProtectedRoute>
                  <TrialEndingPage />
                </ProtectedRoute>
              }
            />
            <Route path="/test-login" element={<SimpleLogin />} />
            <Route path="/pagamento-sucesso" element={<PaymentStatusPage />} />
            <Route path="/pagamento-erro" element={<PaymentStatusPage />} />
            <Route path="/pagamento-pendente" element={<PaymentStatusPage />} />
            <Route
              path="/pacientes"
              element={
                <ProtectedRoute>
                  <PacientesPageComponent />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pacientes/detail/:patientId"
              element={
                <ProtectedRoute>
                  <PatientDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pacientes/edit/:patientId"
              element={
                <ProtectedRoute>
                  <PatientEditPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/importar-prescricoes"
              element={
                <ProtectedRoute>
                  <BatchImportPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/consultas"
              element={
                <ProtectedRoute>
                  <ConsultasPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assistente-ia"
              element={
                <ProtectedRoute>
                  <AIChatPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/billing"
              element={
                <ProtectedRoute>
                  <BillingPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/faturamento"
              element={
                <ProtectedRoute>
                  <FaturamentoPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/onboarding-pacientes"
              element={
                <ProtectedRoute>
                  <OnboardingPacientesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/gestao"
              element={
                <ProtectedRoute>
                  <GestaoPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/certificacao-digital"
              element={
                <ProtectedRoute>
                  <CertificacaoDigitalPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminPage />
                </AdminRoute>
              }
            />
            <Route
              path="/ai-dashboard"
              element={
                <AdminRoute>
                  <AIDashboard />
                </AdminRoute>
              }
            />
            <Route
              path="/ai-config"
              element={
                <AdminRoute>
                  <AIConfigPage />
                </AdminRoute>
              }
            />
            <Route path="/mobile-upload/:token" element={<MobileUploadPage />} />
            <Route path="/seguranca" element={<SecurityPage />} />
            <Route
              path="/configuracao-prescricao"
              element={
                <ProtectedRoute>
                  <ConfiguracaoPrescricaoPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/configuracao-ia"
              element={
                <ProtectedRoute>
                  <ConfiguracaoIAPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/catalogo"
              element={
                <ProtectedRoute>
                  <CatalogoPage />
                </ProtectedRoute>
              }
            />

            {/* Association Module Routes */}
            <Route
              path="/association"
              element={
                <ProtectedRoute>
                  <AssociationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/association/members"
              element={
                <ProtectedRoute>
                  <MembersPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/association/stock"
              element={
                <ProtectedRoute>
                  <StockPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/association/dispensation"
              element={
                <ProtectedRoute>
                  <DispensationPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/intelligent-import"
              element={
                <ProtectedRoute>
                  <IntelligentImportPage />
                </ProtectedRoute>
              }
            />

            {/* Specialty Modules */}
            <Route
              path="/modulos"
              element={
                <ProtectedRoute>
                  <ModulosPage />
                </ProtectedRoute>
              }
            />

            {/* Patient Portal Routes (PUBLIC) */}
            <Route path="/patient/login" element={<PatientLogin />} />
            <Route path="/patient/register" element={<PatientRegister />} />
            <Route path="/patient/dashboard" element={<PatientDashboard />} />

            {/* Error Pages (MISSÃO 12) */}
            <Route path="/401" element={<UnauthorizedPage />} />
            <Route path="/403" element={<ForbiddenPage />} />
            <Route path="/500" element={<ServerErrorPage />} />

            {/* Catch-all 404 */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Container>
      </AssociationProvider>
    </ErrorBoundary>
  );
}

export default App;
