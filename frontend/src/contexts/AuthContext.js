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

  const handlePostLoginRedirect = (user) => {
    if (!user) return;
    const path = window.location.pathname;
    if (path === '/login' || path === '/verificar-email') return;

    // Redirecionar para onboarding se não completou
    if (user.onboarding_completed === false) {
      navigate('/onboarding');
      return;
    }

    // Redirecionar para trial ending se trial expirou ou está no último dia
    if (user.data_expiracao) {
      const exp = new Date(user.data_expiracao);
      const now = new Date();
      const daysLeft = Math.ceil((exp - now) / (1000 * 60 * 60 * 24));
      if (daysLeft <= 1) {
        navigate('/trial-ending');
        return;
      }
    }
  };

  // Verificar se o usuário está autenticado ao carregar a página
  useEffect(() => {
    const checkAuth = async () => {
      try {
        if (authService.isAuthenticated()) {
          try {
            // Obter perfil do usuário do servidor
            const response = await authService.getProfile();
            setCurrentUser(response.user);
            handlePostLoginRedirect(response.user);
          } catch (profileError) {
            console.error('Erro ao obter perfil:', profileError);
            // Se falhar, usar dados do localStorage como fallback
            const user = authService.getUser();
            setCurrentUser(user);
            handlePostLoginRedirect(user);
          }

          // Carregar plano do usuário (para gating de features)
          try {
            const planResp = await billingService.getMyPlan();
            // Resposta pode vir como { assinatura: {...}, plano: {...} } ou só o plano
            const plano = planResp?.plano || planResp;
            setUserPlan(plano);
          } catch (planError) {
            console.warn('Não foi possível carregar plano do usuário:', planError);
          }
        }
      } catch (error) {
        console.error('Erro ao verificar autenticação:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Helper para refresh manual do plano (usado após upgrade)
  const refreshUserPlan = async () => {
    try {
      const planResp = await billingService.getMyPlan();
      const plano = planResp?.plano || planResp;
      setUserPlan(plano);
    } catch (e) {
      console.warn('Falha ao atualizar plano:', e);
    }
  };

  // Função para fazer login
  const login = async (usuario, senha) => {
    console.log('AUTH_CONTEXT: Iniciando login...');
    setError('');
    try {
      console.log('AUTH_CONTEXT: Chamando authService.login...');
      const data = await authService.login(usuario, senha);
      console.log('AUTH_CONTEXT: Resposta recebida:', data);
      setCurrentUser(data.user);

      // Carregar plano logo após login
      try {
        const planResp = await billingService.getMyPlan();
        const plano = planResp?.plano || planResp;
        setUserPlan(plano);
      } catch (planError) {
        console.warn('Plano não carregado após login:', planError);
      }

      console.log('AUTH_CONTEXT: Usuário definido, navegando para home...');

      // Usar setTimeout para garantir que o estado seja atualizado antes da navegação
      setTimeout(() => {
        // Verificar redirecionamentos pós-login
        if (data.trial_expired) {
          navigate('/trial-ending');
        } else if (data.user?.onboarding_completed === false) {
          navigate('/onboarding');
        } else if (data.user?.data_expiracao) {
          const exp = new Date(data.user.data_expiracao);
          const now = new Date();
          const daysLeft = Math.ceil((exp - now) / (1000 * 60 * 60 * 24));
          if (daysLeft <= 1) {
            navigate('/trial-ending');
          } else {
            navigate('/dashboard');
          }
        } else {
          navigate('/dashboard');
        }
      }, 100);

      return data;
    } catch (error) {
      console.error('AUTH_CONTEXT: Erro capturado:', error);
      setError(error.error || error.message || 'Erro ao fazer login');
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
    userPlan,
    hasClinicaAccess,
    refreshUserPlan,
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
