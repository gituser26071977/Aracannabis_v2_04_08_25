import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { Create as CreateIcon, DarkMode, LightMode } from '@mui/icons-material';
import { ThemeContextProvider, useColorMode } from './contexts/ThemeContext';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Button from '@mui/material/Button';
import MenuIcon from '@mui/icons-material/Menu';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import HomeIcon from '@mui/icons-material/Home';
import PersonIcon from '@mui/icons-material/Person';
import EventIcon from '@mui/icons-material/Event';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import SecurityIcon from '@mui/icons-material/Security';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import PaymentIcon from '@mui/icons-material/Payment';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ChatIcon from '@mui/icons-material/Chat';
import MonetizationOnIcon from '@mui/icons-material/MonetizationOn';
import SpeedIcon from '@mui/icons-material/Speed';
import SettingsIcon from '@mui/icons-material/Settings';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import CircularProgress from '@mui/material/CircularProgress';
import { AuthProvider, useAuth } from './contexts/AuthContext';
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
import AdminPage from './pages/AdminPage';
import LandingPage from './pages/LandingPage';
import InternalDashboard from './pages/InternalDashboard';
import AIDashboard from './pages/AIDashboard';
import AIChatPage from './pages/AIChatPage';
import BillingPage from './pages/BillingPage';
import AdBanner from './components/AdBanner';
import AIConfigPage from './pages/AIConfigPage';
import PasswordSetupRequestPage from './pages/PasswordSetupRequestPage';
import DefinePasswordPage from './pages/DefinePasswordPage';
import MobileUploadPage from './pages/MobileUploadPage';
import PaymentStatusPage from './pages/PaymentStatusPage';
import BatchImportPage from './pages/BatchImportPage';
import AssociationPage from './pages/association/AssociationPage';
import MembersPage from './pages/association/MembersPage';
import StockPage from './pages/association/StockPage';
import DispensationPage from './pages/association/DispensationPage';
import ConfiguracaoPrescricaoPage from './pages/ConfiguracaoPrescricaoPage';

import NavigationMenu from './components/NavigationMenu';
import BusinessIcon from '@mui/icons-material/Business';

// Patient Portal Pages
import PatientLogin from './pages/patient/PatientLogin';
import PatientRegister from './pages/patient/PatientRegister';
import PatientDashboard from './pages/patient/PatientDashboard';

const APP_TITLE = 'Aracannabis Prontuário';
const APP_SUBTITLE = 'Sistema de Prontuário Eletrônico para Pacientes em Tratamento com Cannabis Medicinal';

// Tema personalizado
// Theme removed from here as it is now managed by ThemeContext

// Componente de rota protegida
function ProtectedRoute({ children }) {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

// Componente de rota administrativa (apenas admin)
function AdminRoute({ children }) {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  if (currentUser.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}



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
  const theme = useColorMode(); // Access theme directly if needed, but Context handles it

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
        backgroundImage: mode === 'dark'
          ? 'url(/login-bg.png)'
          : `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%232e7d32' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
        backgroundColor: mode === 'dark' ? 'transparent' : '#fcfaf5',
        backgroundSize: mode === 'dark' ? 'cover' : 'auto',
        backgroundPosition: 'center',
        backgroundRepeat: mode === 'dark' ? 'no-repeat' : 'repeat',
        zIndex: 1000,
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: mode === 'dark' ? 'rgba(0, 0, 0, 0.6)' : 'rgba(46, 125, 50, 0.02)',
          backdropFilter: mode === 'dark' ? 'blur(4px)' : 'none',
          zIndex: 1
        }
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
          <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" sx={{ color: '#81c784' }}>
            Aracannabis
          </Typography>
          <Typography variant="subtitle1" sx={{ opacity: 0.8 }}>
            Prontuário Médico & Gestão
          </Typography>
        </Box>

        {(loginError || error) && (
          <Alert severity="error" sx={{ mb: 3, backgroundColor: 'rgba(211, 47, 47, 0.2)', color: '#ffcdd2' }}>
            {loginError || error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            label="Usuário"
            variant="outlined"
            fullWidth
            margin="normal"
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            required
            InputLabelProps={{ style: { color: mode === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'inherit' } }}
            sx={{
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
            label="Senha"
            type="password"
            variant="outlined"
            fullWidth
            margin="normal"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            InputLabelProps={{ style: { color: mode === 'dark' ? 'rgba(255, 255, 255, 0.7)' : 'inherit' } }}
            sx={{
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

          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <Button
              component={Link}
              to="/definir-senha/solicitar"
              size="small"
              sx={{ textTransform: 'none', color: '#f9a825', fontWeight: '500' }}
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
              fontSize: '1.1rem',
              fontWeight: 'bold',
              borderRadius: 2,
              boxShadow: '0 4px 14px 0 rgba(46, 125, 50, 0.39)',
              '&:hover': {
                boxShadow: '0 6px 20px rgba(46, 125, 50, 0.23)',
              }
            }}
            disabled={loading}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Entrar na Plataforma'}
          </Button>
        </form>

        <Box sx={{ mt: 5, textAlign: 'center' }}>
          <Typography variant="body2" sx={{ opacity: 0.6 }}>
            Novo por aqui?
          </Typography>
          <Button
            component={Link}
            to="/cadastro-profissionais"
            variant="text"
            sx={{ mt: 1, textTransform: 'none', color: '#81c784', fontWeight: 'bold' }}
          >
            Solicite seu cadastro como profissional
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
  const { currentUser } = useAuth();
  const location = useLocation();
  const { mode, toggleColorMode } = useColorMode();

  const isLoginPage = location.pathname === '/login' || location.pathname === '/patient/login';

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  return (
    <AssociationProvider>
      {!isLoginPage && (
        <AppBar position="static">
          <Toolbar>
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={toggleMenu}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              {APP_TITLE}
            </Typography>

            {/* Association Selector for SaaS */}
            {currentUser && <AssociationSelector />}

            <IconButton color="inherit" onClick={toggleColorMode}>
              {mode === 'dark' ? <LightMode /> : <DarkMode />}
            </IconButton>

            {currentUser && (
              <Typography variant="body1" sx={{ mr: 2, ml: 2 }}>
                Olá, {currentUser.nome}
              </Typography>
            )}
            {currentUser ? (
              <Button color="inherit" onClick={() => window.open(`${process.env.REACT_APP_API_URL || 'http://localhost:5002'}/api/status`, '_blank')} target="_blank">
                API
              </Button>
            ) : (
              <Button color="inherit" component={Link} to="/login">
                Login
              </Button>
            )}
          </Toolbar>
        </AppBar>
      )}
      <NavigationMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <Container maxWidth={isLoginPage ? false : "lg"} sx={isLoginPage ? { p: 0, m: 0 } : { mt: 4 }}>
        <Routes>
          <Route path="/" element={<LandingPage />} />

          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <InternalDashboard />
            </ProtectedRoute>
          } />
          <Route path="/definir-senha/solicitar" element={<PasswordSetupRequestPage />} />
          <Route path="/definir-senha" element={<DefinePasswordPage />} />
          <Route path="/pagamento" element={<PagamentoPage />} />
          <Route path="/planos" element={<PlanosPage />} />
          <Route path="/cadastro-profissionais" element={<CadastroProfissionaisPage />} />
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

          {/* Association Module Routes */}
          <Route path="/association" element={<ProtectedRoute><AssociationPage /></ProtectedRoute>} />
          <Route path="/association/members" element={<ProtectedRoute><MembersPage /></ProtectedRoute>} />
          <Route path="/association/stock" element={<ProtectedRoute><StockPage /></ProtectedRoute>} />
          <Route path="/association/dispensation" element={<ProtectedRoute><DispensationPage /></ProtectedRoute>} />

          {/* Patient Portal Routes (PUBLIC) */}
          <Route path="/patient/login" element={<PatientLogin />} />
          <Route path="/patient/register" element={<PatientRegister />} />
          <Route path="/patient/dashboard" element={<PatientDashboard />} />

        </Routes>
      </Container>
    </AssociationProvider>
  );
}

export default App;
