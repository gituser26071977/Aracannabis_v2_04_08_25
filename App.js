import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ThemeConfig from './theme';

// Páginas
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import PacientesList from './pages/PacientesList';
import PacienteForm from './pages/PacienteForm';
import PacienteDetail from './pages/PacienteDetail';
import SintomasForm from './pages/SintomasForm';
import DosagemForm from './pages/DosagemForm';
import EvolucaoForm from './pages/EvolucaoForm';
import GraficosView from './pages/GraficosView';
import NotFound from './pages/NotFound';

// Componente para rotas protegidas
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return children;
};

function App() {
  return (
    <BrowserRouter>
      <ThemeConfig>
        <AuthProvider>
          <Routes>
            {/* Rotas públicas */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Rotas protegidas */}
            <Route path="/" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes" element={
              <ProtectedRoute>
                <PacientesList />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes/novo" element={
              <ProtectedRoute>
                <PacienteForm />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes/editar/:id" element={
              <ProtectedRoute>
                <PacienteForm />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes/:id" element={
              <ProtectedRoute>
                <PacienteDetail />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes/:id/sintomas" element={
              <ProtectedRoute>
                <SintomasForm />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes/:id/dosagem" element={
              <ProtectedRoute>
                <DosagemForm />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes/:id/evolucao" element={
              <ProtectedRoute>
                <EvolucaoForm />
              </ProtectedRoute>
            } />
            
            <Route path="/pacientes/:id/graficos" element={
              <ProtectedRoute>
                <GraficosView />
              </ProtectedRoute>
            } />
            
            {/* Rota para página não encontrada */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </ThemeConfig>
    </BrowserRouter>
  );
}

export default App;
