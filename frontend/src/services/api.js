import axios from 'axios';

// Criar uma instância do axios com a URL base da API
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
});

// Interceptor para adicionar o token de autenticação em todas as requisições
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Serviço de autenticação
export const authService = {
  login: async (usuario, senha) => {
    try {
      const response = await api.post('/auth/login', { usuario, senha });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  register: async (nome, crm, usuario, senha) => {
    try {
      const response = await api.post('/auth/register', { nome, crm, usuario, senha });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  
  getProfile: async () => {
    try {
      const response = await api.get('/auth/profile');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },
  
  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }
};

// Serviço de pacientes
export const pacientesService = {
  listar: async () => {
    try {
      const response = await api.get('/pacientes/');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obter: async (id) => {
    try {
      const response = await api.get(`/pacientes/${id}/`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (paciente) => {
    try {
      console.log('Enviando dados para API:', paciente);
      const response = await api.post('/pacientes/', paciente);
      console.log('Resposta da API:', response);
      return response.data;
    } catch (error) {
      console.error('Erro completo da API:', error);
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  atualizar: async (id, paciente) => {
    try {
      const response = await api.put(`/pacientes/${id}`, paciente);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  excluir: async (id) => {
    try {
      const response = await api.delete(`/pacientes/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de sintomas
export const sintomasService = {
  listar: async (pacienteId) => {
    try {
      const response = await api.get(`/sintomas?paciente_id=${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (sintoma) => {
    try {
      const response = await api.post('/sintomas', sintoma);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de dosagens
export const dosagensService = {
  listar: async (pacienteId) => {
    try {
      const response = await api.get(`/dosagens?paciente_id=${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (dosagem) => {
    try {
      const response = await api.post('/dosagens', dosagem);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de evoluções
export const evolucoesService = {
  listar: async (pacienteId) => {
    try {
      const response = await api.get(`/evolucoes?paciente_id=${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (evolucao) => {
    try {
      const response = await api.post('/evolucoes', evolucao);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

export default api;
