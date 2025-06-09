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
import PlanosPage from './pages/PlanosPage';
import PagamentoPage from './pages/PagamentoPage';
import AdBanner from './components/AdBanner';
import PrescriptionView from './components/PrescriptionView';

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

// Componentes de página
function HomePage() {
  const { currentUser } = useAuth();

  return (
    <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 }, my: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h2" component="h1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
          Aracannabis
        </Typography>
        <Typography variant="h5" component="h2" color="text.secondary" gutterBottom>
          Sistema de Prontuário Eletrônico para Pacientes de Cannabis Medicinal
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2, fontStyle: 'italic' }}>
          Versão Básica (Sem IA)
        </Typography>
      </Box>

      <Box sx={{ textAlign: 'left', maxWidth: '800px', mx: 'auto' }}>
        <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
          Bem-vindo{currentUser ? `, ${currentUser.nome}` : ''} ao sistema de prontuário eletrônico Aracannabis.
        </Typography>
        <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem', lineHeight: 1.7 }}>
          Este sistema foi cuidadosamente desenvolvido para oferecer uma plataforma segura e eficiente 
          para o gerenciamento completo de informações de pacientes, acompanhamento de sintomas, 
          ajuste de dosagens e registro da evolução do tratamento com cannabis medicinal.
        </Typography>
        <Typography variant="body1" sx={{ fontSize: '1.1rem', lineHeight: 1.7, mt: 3 }}>
          Utilize o menu lateral para navegar pelas diversas funcionalidades disponíveis e otimizar 
          o cuidado e acompanhamento dos seus pacientes.
        </Typography>
        
        {!currentUser && (
          <>
            <Box sx={{ mt: 4, p: 3, backgroundColor: '#e8f5e9', borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom color="primary">
                🌿 Profissional de Saúde?
              </Typography>
              <Typography variant="body1" paragraph>
                Solicite acesso ao sistema Aracannabis e experimente todas as funcionalidades por 7 dias gratuitamente.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  color="primary"
                  component={Link}
                  to="/cadastro-profissionais"
                  startIcon={<PersonAddIcon />}
                >
                  Solicitar Cadastro
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  component={Link}
                  to="/planos"
                  startIcon={<PaymentIcon />}
                >
                  Ver Planos e Preços
                </Button>
              </Box>
            </Box>
            
            {/* Anúncios para usuários não logados */}
            <Box sx={{ mt: 4 }}>
              <AdBanner position="banner" maxAds={3} />
            </Box>
          </>
        )}
      </Box>
    </Paper>
  );
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
        Login
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
        <Button
          type="submit"
          variant="contained"
          color="primary"
          fullWidth
          sx={{ mt: 2 }}
          disabled={loading}
        >
          {loading ? 'Entrando...' : 'Entrar'}
        </Button>
      </form>
      
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Typography variant="body2">
          Não tem uma conta?{' '}
          <Link to="/cadastro-profissionais" style={{ color: '#2e7d32', textDecoration: 'none' }}>
            Solicite seu cadastro aqui
          </Link>
          {' ou '}
          <Link to="/planos" style={{ color: '#2e7d32', textDecoration: 'none' }}>
            veja nossos planos
          </Link>
        </Typography>
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
    { text: 'Pacientes', icon: <PersonIcon />, path: '/pacientes', auth: true },
    { text: 'Consultas', icon: <EventIcon />, path: '/consultas', auth: true },
    { text: 'Planos e Preços', icon: <PaymentIcon />, path: '/planos', auth: false },
    { text: 'Segurança e LGPD', icon: <SecurityIcon />, path: '/seguranca', auth: false },
    { text: 'Cadastro Profissionais', icon: <PersonAddIcon />, path: '/cadastro-profissionais', auth: false },
  ];

  const authItems = currentUser
    ? [{ text: 'Sair', icon: <LogoutIcon />, onClick: logout }]
    : [{ text: 'Login', icon: <LoginIcon />, path: '/login' }];

  return (
    <Drawer anchor="left" open={open} onClose={onClose}>
      <Box sx={{ width: 250 }} role="presentation" onClick={onClose}>
        <List>
          {menuItems
            .filter(item => !item.auth || (item.auth && currentUser))
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
            Aracannabis Prontuário - Versão Básica
          </Typography>
          {currentUser && (
            <Typography variant="body1" sx={{ mr: 2 }}>
              Olá, {currentUser.nome}
            </Typography>
          )}
          {currentUser ? (
            <Button color="inherit" onClick={() => window.open('http://localhost:5010/api/status', '_blank')} target="_blank">
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
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/planos" element={<PlanosPage />} />
          <Route path="/pagamento" element={<PagamentoPage />} />
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
            path="/consultas/:consultaId/prescricao" 
            element={
              <ProtectedRoute>
                <PrescriptionView />
              </ProtectedRoute>
            } 
          />
          <Route path="/seguranca" element={<SecurityPage />} />
        </Routes>
      </Container>
    </ThemeProvider>
  );
}

export default App;
