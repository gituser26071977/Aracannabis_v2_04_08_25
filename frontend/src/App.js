import React, { useState } from 'react';
import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
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
import { useAuth } from './contexts/AuthContext';

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

const APP_TITLE = 'Aracannabis Prontuário';
const APP_SUBTITLE = 'Sistema de Prontuário Eletrônico para Pacientes em Tratamento com Cannabis Medicinal';

// Tema personalizado
const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32', // Verde
    },
    secondary: {
      main: '#f9a825', // Amarelo
    },
  },
});

// Componente de rota protegida
function ProtectedRoute({ children }) {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return <Navigate to="/login" replace />;
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
    console.log('LOGIN_PAGE: Iniciando processo de login...');
    setLoginError('');
    setLoading(true);

    try {
      console.log('LOGIN_PAGE: Chamando função login com:', { usuario, senha: '***' });
      await login(usuario, senha);
      console.log('LOGIN_PAGE: Login bem-sucedido!');
    } catch (error) {
      console.error('LOGIN_PAGE: Erro no login:', error);
      setLoginError(error.error || error.message || 'Falha ao fazer login');
    } finally {
      console.log('LOGIN_PAGE: Finalizando processo de login...');
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, my: 4, maxWidth: 500, mx: 'auto' }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Acesso ao Sistema
      </Typography>

      {(loginError || error) && (
        <Alert severity="error" sx={{ mb: 2 }}>
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
        />

        {/* LINK DE RECUPERAÇÃO SECUNDÁRIO */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
          <Button
            component={Link}
            to="/definir-senha/solicitar"
            size="medium"
            color="secondary"
            sx={{ textTransform: 'none', fontWeight: 'bold' }}
          >
            Esqueceu a senha? Clique aqui.
          </Button>
        </Box>

        <Button
          type="submit"
          variant="contained"
          color="primary"
          fullWidth
          sx={{ mt: 2, height: 50, fontSize: '1.1rem' }}
          disabled={loading}
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </Button>
      </form>

      <Box sx={{ mt: 4, display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'center' }}>

        <Box sx={{ mt: 1, textAlign: 'center' }}>
          <Typography variant="body1" color="text.secondary">
            Não tem uma conta?
          </Typography>
          <Button
            component={Link}
            to="/cadastro-profissionais"
            variant="outlined"
            size="large"
            sx={{ mt: 1, textTransform: 'none' }}
          >
            Solicite seu cadastro aqui
          </Button>
        </Box>
      </Box>
    </Paper>
  );
}

// Menu de navegação
function NavigationMenu({ open, onClose }) {
  const location = useLocation();
  const { currentUser, logout } = useAuth();

  const menuItems = [
    { text: 'Início', icon: <HomeIcon />, path: '/', auth: false },
    { text: 'Dashboard', icon: <SpeedIcon />, path: '/dashboard', auth: true },
    { text: 'Assine Agora', icon: <MonetizationOnIcon />, path: '/planos', auth: false, hideWhenLoggedIn: true },
    // Novo atalho para cadastro de profissionais (visível apenas antes do login)
    { text: 'Cadastro de Profissionais', icon: <PersonAddIcon />, path: '/cadastro-profissionais', auth: false, hideWhenLoggedIn: true },
    { text: 'Pacientes', icon: <PersonIcon />, path: '/pacientes', auth: true },
    { text: 'Consultas', icon: <EventIcon />, path: '/consultas', auth: true },
    { text: 'Chat IA', icon: <ChatIcon />, path: '/assistente-ia', auth: true },
    { text: 'Configuração de IA/LLM', icon: <SettingsIcon />, path: '/ai-config', auth: true, adminOnly: true },
    { text: 'Dashboard de IA', icon: <SmartToyIcon />, path: '/ai-dashboard', auth: true, adminOnly: true },
    { text: 'Segurança e LGPD', icon: <SecurityIcon />, path: '/seguranca', auth: false },
    // Painel administrativo (apenas para admins)
    { text: 'Painel Admin', icon: <SecurityIcon />, path: '/admin', auth: true, adminOnly: true },
  ];

  const authItems = currentUser
    ? [{ text: 'Sair', icon: <LogoutIcon />, onClick: logout }]
    : [{ text: 'Login', icon: <LoginIcon />, path: '/login' }];

  return (
    <Drawer anchor="left" open={open} onClose={onClose}>
      <Box sx={{ width: 250 }} role="presentation" onClick={onClose}>
        <List>
          {menuItems
            .filter(item => {
              // Verificar autenticação
              if (item.auth && !currentUser) return false;
              // Esconder itens marcados como hideWhenLoggedIn quando o usuário estiver logado
              if (currentUser && item.hideWhenLoggedIn) return false;
              // Verificar se é apenas para admin
              if (item.adminOnly && (!currentUser || currentUser.role !== 'admin')) return false;
              return true;
            })
            .map((item) => (
              <ListItem
                button
                key={item.text}
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}

          <Box sx={{ borderTop: 1, borderColor: 'divider', my: 1 }} />

          {authItems.map((item) => (
            <ListItem
              button
              key={item.text}
              component={item.path ? Link : 'div'}
              to={item.path}
              onClick={item.onClick}
              selected={item.path && location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
}

function App() {
  const [menuOpen, setMenuOpen] = useState(false);
  const { currentUser } = useAuth();

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
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
          {currentUser && (
            <Typography variant="body1" sx={{ mr: 2 }}>
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
      <NavigationMenu open={menuOpen} onClose={() => setMenuOpen(false)} />
      <Container maxWidth="lg">
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
              <ProtectedRoute>
                <AdminPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai-dashboard"
            element={
              <ProtectedRoute>
                <AIDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ai-config"
            element={
              <ProtectedRoute>
                <AIConfigPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mobile-upload/:token"
            element={<MobileUploadPage />}
          />
          <Route path="/seguranca" element={<SecurityPage />} />
        </Routes>
      </Container>
    </ThemeProvider>
  );
}

export default App;
