import axios from 'axios';

// Criar uma instância do axios com a URL base da API
const api = axios.create({
  baseURL: 'http://localhost:5000/api',
});

// Interceptor para adicionar o token de autenticação e CSRF em todas as requisições
api.interceptors.request.use(
  (config) => {
    // Adicionar token JWT
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Adicionar token CSRF para métodos não seguros
    const csrfToken = localStorage.getItem('csrf_token');
    if (csrfToken && ['post', 'put', 'delete', 'patch'].includes(config.method)) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor para tratar erros de resposta
api.interceptors.response.use(
  (response) => {
    // Armazenar token CSRF se estiver presente na resposta
    if (response.data && response.data.csrf_token) {
      localStorage.setItem('csrf_token', response.data.csrf_token);
    }
    return response;
  },
  (error) => {
    // Tratar erros de autenticação (401)
    if (error.response && error.response.status === 401) {
      // Se não for uma requisição de login, fazer logout
      if (!error.config.url.includes('/auth/login')) {
        console.log('Sessão expirada. Redirecionando para login...');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Serviço de autenticação
export const authService = {
  login: async (usuario, senha) => {
    try {
      console.log('AUTH_SERVICE_LOGIN: Tentando obter token CSRF...'); // NOVO LOG
      const csrfResponse = await api.get('/csrf-token');
      console.log('AUTH_SERVICE_LOGIN: Token CSRF obtido:', csrfResponse.data); // NOVO LOG
      localStorage.setItem('csrf_token', csrfResponse.data.csrf_token);
      
      console.log('AUTH_SERVICE_LOGIN: Tentando fazer login...'); // NOVO LOG
      // Fazer login com o token CSRF
      const response = await api.post('/auth/login', { usuario, senha });
      console.log('AUTH_SERVICE_LOGIN: Resposta do login:', response.data); // NOVO LOG
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      // Armazenar o token CSRF da resposta de login
      if (response.data.csrf_token) {
        localStorage.setItem('csrf_token', response.data.csrf_token);
      }
      
      return response.data;
    } catch (error) {
      console.error('AUTH_SERVICE_LOGIN: Erro no processo de login:', error); // LOG ATUALIZADO
      if (error.response) {
        console.error('AUTH_SERVICE_LOGIN: Dados do erro da resposta:', error.response.data);
        throw error.response.data;
      } else if (error.request) {
        console.error('AUTH_SERVICE_LOGIN: Nenhuma resposta recebida:', error.request);
        throw { error: 'Erro de conexão ou nenhuma resposta do servidor.' };
      } else {
        console.error('AUTH_SERVICE_LOGIN: Erro ao configurar requisição:', error.message);
        throw { error: 'Erro ao configurar requisição.' };
      }
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
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('csrf_token');
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
      const response = await api.get(`/pacientes/${id}`);
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
  },
  
  compartilhar: async (pacienteId, profissionalId, nivelAcesso) => {
    try {
      const response = await api.post(`/pacientes/${pacienteId}/compartilhar`, {
        profissional_id: profissionalId,
        nivel_acesso: nivelAcesso
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  listarCompartilhamentos: async (pacienteId) => {
    try {
      const response = await api.get(`/pacientes/${pacienteId}/compartilhamentos`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  removerCompartilhamento: async (pacienteId, compartilhamentoId) => {
    try {
      const response = await api.delete(`/pacientes/${pacienteId}/compartilhamentos/${compartilhamentoId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  listarProfissionais: async () => {
    try {
      const response = await api.get('/pacientes/profissionais');
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
      const response = await api.get(`/sintomas/paciente/${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (sintoma) => {
    try {
      const response = await api.post(`/sintomas/paciente/${sintoma.paciente_id}`, sintoma);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  excluir: async (id) => {
    try {
      const response = await api.delete(`/sintomas/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  listarPadrao: async () => {
    try {
      const response = await api.get('/sintomas/sintomas-padrao');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criarPersonalizado: async (nomeSintoma) => {
    try {
      const response = await api.post('/sintomas/sintoma-personalizado', { nome_sintoma: nomeSintoma });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obterDadosGrafico: async (pacienteId, period = 'integral') => {
    try {
      const response = await api.get(`/sintomas/grafico/paciente/${pacienteId}?periodo=${period}`);
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
      const response = await api.get(`/dosagens/paciente/${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (dosagem) => {
    try {
      const response = await api.post(`/dosagens/paciente/${dosagem.paciente_id}`, dosagem);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  excluir: async (id) => {
    try {
      const response = await api.delete(`/dosagens/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obterDadosGrafico: async (pacienteId, period = 'integral') => {
    try {
      const response = await api.get(`/dosagens/grafico/paciente/${pacienteId}?periodo=${period}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de evoluções
export const evolucoesService = {
  listar: async (pacienteId, termoBusca = '') => {
    try {
      let url = `/evolucoes/paciente/${pacienteId}`;
      
      // Adicionar parâmetro de busca se fornecido
      if (termoBusca) {
        url += `?busca=${encodeURIComponent(termoBusca)}`;
      }
      
      const response = await api.get(url);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  buscarGlobal: async (termo) => {
    try {
      const response = await api.get(`/evolucoes/busca?termo=${encodeURIComponent(termo)}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (evolucao) => {
    try {
      const response = await api.post(`/evolucoes/paciente/${evolucao.paciente_id}`, evolucao);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obter: async (id) => {
    try {
      const response = await api.get(`/evolucoes/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  atualizar: async (id, evolucao) => {
    try {
      const response = await api.put(`/evolucoes/${id}`, evolucao);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  excluir: async (id) => {
    try {
      const response = await api.delete(`/evolucoes/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  uploadArquivo: async (pacienteId, arquivo) => {
    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      
      const response = await api.post(`/evolucoes/upload-arquivo/${pacienteId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de LGPD
export const lgpdService = {
  obterConsentimento: async (pacienteId) => {
    try {
      const response = await api.get(`/lgpd/consentimento/${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  registrarConsentimento: async (pacienteId, consentimento) => {
    try {
      const response = await api.post(`/lgpd/consentimento/${pacienteId}`, { consentimento });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obterPoliticaPrivacidade: async () => {
    try {
      const response = await api.get('/lgpd/politica-privacidade');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  solicitarDireitosTitular: async (pacienteId, tipoSolicitacao, detalhes) => {
    try {
      const response = await api.post(`/lgpd/direitos-titular/${pacienteId}`, {
        tipo_solicitacao: tipoSolicitacao,
        detalhes
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de consultas
export const consultasService = {
  listar: async (filtros = {}) => {
    try {
      const params = new URLSearchParams();
      if (filtros.data_inicio) params.append('data_inicio', filtros.data_inicio);
      if (filtros.data_fim) params.append('data_fim', filtros.data_fim);
      if (filtros.paciente_id) params.append('paciente_id', filtros.paciente_id);
      if (filtros.status) params.append('status', filtros.status);
      
      const response = await api.get(`/consultas/?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  criar: async (consulta) => {
    try {
      const response = await api.post('/consultas/', consulta);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  atualizar: async (id, consulta) => {
    try {
      const response = await api.put(`/consultas/${id}`, consulta);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  cancelar: async (id) => {
    try {
      const response = await api.delete(`/consultas/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obterCalendario: async (ano, mes) => {
    try {
      const response = await api.get(`/consultas/calendario/${ano}/${mes}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  enviarLembretes: async () => {
    try {
      const response = await api.post('/consultas/lembretes/enviar');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de configuração de IA
export const aiConfigService = {
  obterProvedores: async () => {
    try {
      const response = await api.get('/ai-config/providers');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obterConfiguracao: async () => {
    try {
      const response = await api.get('/ai-config/config');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  atualizarConfiguracao: async (config) => {
    try {
      const response = await api.post('/ai-config/config', config);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  testarConfiguracao: async (config) => {
    try {
      const response = await api.post('/ai-config/test', config);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  obterModelosProvedor: async (provider) => {
    try {
      const response = await api.get(`/ai-config/models/${provider}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de importação e exportação
export const importExportService = {
  exportarPaciente: async (pacienteId, formato = 'json') => {
    try {
      const response = await api.get(`/import-export/export/patient/${pacienteId}`, {
        responseType: 'blob'
      });
      
      // Criar URL para download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Definir nome do arquivo baseado no formato
      const timestamp = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `paciente_${pacienteId}_${timestamp}.${formato}`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return { success: true, message: 'Exportação realizada com sucesso' };
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  exportarCSV: async (pacienteId, tipo = 'all') => {
    try {
      const response = await api.get(`/import-export/export/csv/patient/${pacienteId}?type=${tipo}`, {
        responseType: 'blob'
      });
      
      // Criar URL para download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Definir nome do arquivo
      const timestamp = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `${tipo}_paciente_${pacienteId}_${timestamp}.csv`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return { success: true, message: 'Exportação CSV realizada com sucesso' };
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  importarArquivo: async (pacienteId, arquivo) => {
    try {
      const formData = new FormData();
      formData.append('file', arquivo);
      
      const response = await api.post(`/import-export/import/patient/${pacienteId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  
  chatComDados: async (pacienteId, pergunta) => {
    try {
      const response = await api.post(`/import-export/chat/patient/${pacienteId}`, {
        question: pergunta
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

export default api;
