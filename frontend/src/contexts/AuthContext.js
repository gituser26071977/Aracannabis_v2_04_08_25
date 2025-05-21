import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/api';
import { useNavigate } from 'react-router-dom';

// Criar o contexto de autenticação
const AuthContext = createContext();

// Hook personalizado para usar o contexto de autenticação
export const useAuth = () => {
  return useContext(AuthContext);
};

// Provedor do contexto de autenticação
export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  // Verificar se o usuário está autenticado ao carregar a página
  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          const user = authService.getUser();
          setCurrentUser(user);
        }
      } catch (error) {
        console.error('Erro ao verificar autenticação:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Função para fazer login
  const login = async (usuario, senha) => {
    setError('');
    try {
      const data = await authService.login(usuario, senha);
      setCurrentUser(data.user);
      navigate('/');
      return data;
    } catch (error) {
      setError(error.error || 'Erro ao fazer login');
      throw error;
    }
  };

  // Função para fazer logout
  const logout = () => {
    authService.logout();
    setCurrentUser(null);
    navigate('/login');
  };

  // Função para registrar um novo usuário
  const register = async (nome, crm, usuario, senha) => {
    setError('');
    try {
      const data = await authService.register(nome, crm, usuario, senha);
      navigate('/login');
      return data;
    } catch (error) {
      setError(error.error || 'Erro ao registrar');
      throw error;
    }
  };

  // Valor do contexto
  const value = {
    currentUser,
    login,
    logout,
    register,
    error,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
