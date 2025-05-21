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
import MedicationIcon from '@mui/icons-material/Medication';
import AssessmentIcon from '@mui/icons-material/Assessment';
import HistoryIcon from '@mui/icons-material/History';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import Paper from '@mui/material/Paper';
import TextField from '@mui/material/TextField';
import Alert from '@mui/material/Alert';
import { useAuth } from './contexts/AuthContext';

// Importar páginas
import PacientesPageComponent from './pages/PacientesPage';

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
    <Paper elevation={3} sx={{ p: 4, my: 4, textAlign: 'center' }}>
      <Typography variant="h3" component="h1" gutterBottom>
        Aracannabis
      </Typography>
      <Typography variant="h5" component="h2" gutterBottom>
        Sistema de Prontuário Eletrônico para Pacientes de Cannabis Medicinal
      </Typography>
      <Typography variant="body1" paragraph>
        Bem-vindo{currentUser ? `, ${currentUser.nome}` : ''} ao sistema de prontuário eletrônico Aracannabis. 
        Este sistema permite o gerenciamento completo de pacientes, sintomas, dosagens e evolução 
        do tratamento com cannabis medicinal.
      </Typography>
      <Typography variant="body1">
        Utilize o menu para navegar entre as diferentes funcionalidades do sistema.
      </Typography>
    </Paper>
  );
}

function PacientesPage() {
  return (
    <Paper elevation={3} sx={{ p: 4, my: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Gerenciamento de Pacientes
      </Typography>
      <Typography variant="body1" paragraph>
        Aqui você pode cadastrar, visualizar e editar informações dos pacientes.
      </Typography>
      <Alert severity="info">
        Esta funcionalidade está em desenvolvimento. Em breve você poderá gerenciar pacientes aqui.
      </Alert>
    </Paper>
  );
}

function SintomasPage() {
  return (
    <Paper elevation={3} sx={{ p: 4, my: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Registro de Sintomas
      </Typography>
      <Typography variant="body1" paragraph>
        Registre e acompanhe os sintomas relatados pelos pacientes.
      </Typography>
      <Alert severity="info">
        Esta funcionalidade está em desenvolvimento. Em breve você poderá registrar sintomas aqui.
      </Alert>
    </Paper>
  );
}

function DosagensPage() {
  return (
    <Paper elevation={3} sx={{ p: 4, my: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Controle de Dosagens
      </Typography>
      <Typography variant="body1" paragraph>
        Gerencie as dosagens de cannabis medicinal prescritas aos pacientes.
      </Typography>
      <Alert severity="info">
        Esta funcionalidade está em desenvolvimento. Em breve você poderá controlar dosagens aqui.
      </Alert>
    </Paper>
  );
}

function EvolucoesPage() {
  return (
    <Paper elevation={3} sx={{ p: 4, my: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Histórico de Evolução
      </Typography>
      <Typography variant="body1" paragraph>
        Acompanhe a evolução do tratamento dos pacientes ao longo do tempo.
      </Typography>
      <Alert severity="info">
        Esta funcionalidade está em desenvolvimento. Em breve você poderá acompanhar evoluções aqui.
      </Alert>
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
    setLoginError('');
    setLoading(true);
    
    try {
      await login(usuario, senha);
    } catch (error) {
      setLoginError(error.error || 'Falha ao fazer login');
    } finally {
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
          Não tem uma conta? Entre em contato com o administrador.
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
    { text: 'Sintomas', icon: <MedicationIcon />, path: '/sintomas', auth: true },
    { text: 'Dosagens', icon: <AssessmentIcon />, path: '/dosagens', auth: true },
    { text: 'Evoluções', icon: <HistoryIcon />, path: '/evolucoes', auth: true },
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
            Aracannabis Prontuário
          </Typography>
          {currentUser && (
            <Typography variant="body1" sx={{ mr: 2 }}>
              Olá, {currentUser.nome}
            </Typography>
          )}
          {currentUser ? (
            <Button color="inherit" onClick={() => window.location.href = '/api/status'} target="_blank">
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
          <Route 
            path="/pacientes" 
            element={
              <ProtectedRoute>
                <PacientesPageComponent />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/sintomas" 
            element={
              <ProtectedRoute>
                <SintomasPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/dosagens" 
            element={
              <ProtectedRoute>
                <DosagensPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/evolucoes" 
            element={
              <ProtectedRoute>
                <EvolucoesPage />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Container>
    </ThemeProvider>
  );
}

export default App;
