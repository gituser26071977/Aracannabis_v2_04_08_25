import axios from 'axios';

// Definir a URL base da API
const API_BASE_URL = process.env.REACT_APP_API_URL ? `${process.env.REACT_APP_API_URL}/api` : 'http://localhost:5002/api';

// Criar uma instância do axios com a URL base da API
const api = axios.create({
  baseURL: API_BASE_URL,
});

console.log('API Service configurado com URL:', API_BASE_URL);

// Interceptor para adicionar o token de autenticação e CSRF em todas as requisições
api.interceptors.request.use(
  (config) => {
    // Adicionar token JWT
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Adicionar ID da associação ativa para isolamento multi-tenant
    const selectedAssocId = localStorage.getItem('selectedAssociationId');
    if (selectedAssocId) {
      config.headers['X-Association-ID'] = selectedAssocId;
    }

    // Adicionar token CSRF para métodos não seguros
    // const csrfToken = localStorage.getItem('csrf_token');
    // if (csrfToken && ['post', 'put', 'delete', 'patch'].includes(config.method)) {
    //   config.headers['X-CSRF-Token'] = csrfToken;
    // }

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
    // if (response.data && response.data.csrf_token) {
    //   localStorage.setItem('csrf_token', response.data.csrf_token);
    // }
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
      // console.log('AUTH_SERVICE_LOGIN: Tentando obter token CSRF...'); // NOVO LOG
      // const csrfResponse = await api.get('/csrf-token');
      // console.log('AUTH_SERVICE_LOGIN: Token CSRF obtido:', csrfResponse.data); // NOVO LOG
      // localStorage.setItem('csrf_token', csrfResponse.data.csrf_token);

      console.log('AUTH_SERVICE_LOGIN: Tentando fazer login...'); // NOVO LOG
      // Fazer login com o token CSRF
      const payload = usuario && usuario.includes('@')
        ? { email: usuario, senha }
        : { usuario, senha };
      const response = await api.post('/auth/login', payload);
      console.log('AUTH_SERVICE_LOGIN: Resposta do login:', response.data); // NOVO LOG
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      // Armazenar o token CSRF da resposta de login
      // if (response.data.csrf_token) {
      //   localStorage.setItem('csrf_token', response.data.csrf_token);
      // }

      return response.data;
    } catch (error) {
      console.error('AUTH_SERVICE_LOGIN: Erro no processo de login:', error);
      if (error.response) {
        console.error('AUTH_SERVICE_LOGIN: Dados do erro da resposta:', error.response.data);
        throw new Error(JSON.stringify(error.response.data));
      } else if (error.request) {
        console.error('AUTH_SERVICE_LOGIN: Nenhuma resposta recebida:', error.request);
        throw new Error('Erro de conexão ou nenhuma resposta do servidor.');
      } else {
        console.error('AUTH_SERVICE_LOGIN: Erro ao configurar requisição:', error.message);
        throw new Error('Erro ao configurar requisição.');
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

  requestPasswordSetup: async (email) => {
    try {
      const response = await api.post('/auth/request-password-setup', { email });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  definePassword: async ({ user_id, token, nova_senha }) => {
    try {
      const response = await api.post('/auth/define-password', { user_id, token, nova_senha });
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
  listar: async (filtros = {}) => {
    try {
      const params = new URLSearchParams();
      if (filtros.nome) params.append('nome', filtros.nome);
      if (filtros.associacao) params.append('associacao', filtros.associacao);
      if (filtros.periodo_cadastro) params.append('periodo_cadastro', filtros.periodo_cadastro);

      const response = await api.get(`/pacientes/?${params.toString()}`);
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

      // Verificar se é FormData (com foto) ou objeto JSON
      const isFormData = paciente instanceof FormData;
      const config = isFormData ? {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      } : {};

      const response = await api.post('/pacientes/', paciente, config);
      console.log('Resposta da API:', response);
      return response.data;
    } catch (error) {
      console.error('Erro completo da API:', error);
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  atualizar: async (id, paciente) => {
    try {
      // Verificar se é FormData (com foto) ou objeto JSON
      const isFormData = paciente instanceof FormData;
      const config = isFormData ? {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      } : {};

      const response = await api.put(`/pacientes/${id}`, paciente, config);
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

  criarPersonalizado: async (nomeSintoma, pacienteId) => {
    try {
      const response = await api.post('/sintomas/sintoma-personalizado', {
        nome_sintoma: nomeSintoma,
        paciente_id: pacienteId
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  excluirPersonalizado: async (nomeSintoma) => {
    try {
      const response = await api.delete(`/sintomas/sintoma-personalizado`, {
        data: { nome_sintoma: nomeSintoma }
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  removerPersonalizado: async (sintomaId) => {
    try {
      const response = await api.delete(`/sintomas/sintoma-personalizado/${sintomaId}`);
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
      const response = await api.get(`/dosagens/grafico/paciente/${pacienteId}`, {
        params: { periodo: period }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Erro ao obter dados do gráfico: ${error.response?.data?.error || error.message}`);
    }
  },

  obterDadosGraficoNovo: async (pacienteId, period = 'integral') => {
    try {
      const response = await api.get(`/dosagens/grafico/paciente/${pacienteId}`, {
        params: { periodo: period }
      });
      return response.data;
    } catch (error) {
      throw new Error(`Erro ao obter dados do gráfico: ${error.response?.data?.error || error.message}`);
    }
  }
};

// Serviço de exames
export const exameService = {
  listarPorPaciente: async (pacienteId) => {
    try {
      const response = await api.get(`/pacientes/${pacienteId}/exames`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  criar: async (formData) => {
    try {
      const response = await api.post('/exames', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      // Extrair dados do exame da resposta (ignorando email_status)
      const { email_status, ...examData } = response.data;
      return examData;
    } catch (error) {
      const errorMessage = error.response?.data?.error ||
        error.response?.data?.message ||
        'Erro ao criar exame';
      throw new Error(errorMessage);
    }
  },

  excluir: async (id) => {
    try {
      const response = await api.delete(`/exames/${id}`);
      return response.data; // Retorna o objeto de resposta completo
    } catch (error) {
      const errorMessage = error.response?.data?.error ||
        error.response?.data?.message ||
        'Erro ao excluir exame';
      throw new Error(errorMessage);
    }
  },

  obter: async (id) => {
    try {
      const response = await api.get(`/exames/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  listarImagens: async (exameId) => {
    try {
      const response = await api.get(`/exames/${exameId}/imagens`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterUrlImagem: (filename) => {
    return `${API_BASE_URL}/exames/arquivos/${filename}`;
  },

  processarOCR: async (exameId) => {
    try {
      const response = await api.post(`/exames/${exameId}/ocr`);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.error ||
        error.response?.data?.message ||
        'Erro ao processar OCR';
      throw new Error(errorMessage);
    }
  },

  obterDadosGrafico: async (pacienteId, period = 'integral') => {
    try {
      const response = await api.get(`/pacientes/${pacienteId}/exames`);
      const exames = response.data;

      // Filtrar apenas exames numéricos
      const examesNumericos = exames.filter(exame =>
        exame.tipo_exame === 'numerico' && exame.valor !== null
      );

      // Agrupar por título e ordenar por data
      const dadosGrafico = {};
      examesNumericos.forEach(exame => {
        const titulo = exame.titulo;
        if (!dadosGrafico[titulo]) {
          dadosGrafico[titulo] = [];
        }
        dadosGrafico[titulo].push({
          data: exame.data_exame,
          valor: parseFloat(exame.valor),
          unidade: exame.unidade || ''
        });
      });

      // Ordenar cada série por data
      Object.keys(dadosGrafico).forEach(titulo => {
        dadosGrafico[titulo].sort((a, b) => new Date(a.data) - new Date(b.data));
      });

      return dadosGrafico;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterNomesExamesUnicos: async () => {
    try {
      const response = await api.get('/exames/nomes-unicos');
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

// Serviço GAD-7
export const gad7Service = {
  criarTeste: async (pacienteId, testeData) => {
    try {
      const response = await api.post(`/gad7/paciente/${pacienteId}`, testeData);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterUltimoTeste: async (pacienteId) => {
    try {
      const response = await api.get(`/gad7/paciente/${pacienteId}/ultimo`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  listar: async (pacienteId) => {
    try {
      const response = await api.get(`/gad7/paciente/${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  excluir: async (testeId) => {
    try {
      const response = await api.delete(`/gad7/${testeId}`);
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



// Serviço de Configuração IA (SDR Multi-Tenant)
export const configIaTenantService = {
  obter: async () => {
    try {
      const response = await api.get('/tenant-config/ia');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  salvar: async (configData) => {
    try {
      const response = await api.post('/tenant-config/ia', configData);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de produtos
export const produtosService = {
  listar: async () => {
    try {
      const response = await api.get('/produtos');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obter: async (id) => {
    try {
      const response = await api.get(`/produtos/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  criar: async (produto) => {
    try {
      const response = await api.post('/produtos', produto);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  assistente: async (payload) => {
    try {
      const isFormData = payload instanceof FormData;
      const config = isFormData ? {
        headers: { 'Content-Type': 'multipart/form-data' }
      } : {};
      const response = await api.post('/produtos/assistente', payload, config);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  atualizar: async (id, produto) => {
    try {
      const response = await api.put(`/produtos/${id}`, produto);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  excluir: async (id) => {
    try {
      const response = await api.delete(`/produtos/${id}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de billing/planos
export const billingService = {
  listarPlanos: async () => {
    try {
      const response = await api.get('/billing/plans');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  criarPlano: async (plano) => {
    try {
      const response = await api.post('/billing/plans', plano);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  assinarPlano: async ({ plano_id, metodo = 'pix' }) => {
    try {
      const response = await api.post('/billing/subscribe', { plano_id, metodo });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  listarFaturas: async () => {
    try {
      const response = await api.get('/billing/invoices');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  pagarFatura: async (faturaId) => {
    try {
      const response = await api.post(`/billing/invoices/${faturaId}/pay`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  statusPagamento: async (cobrancaId) => {
    try {
      const response = await api.get(`/billing/payments/${cobrancaId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  atualizarStatusPagamento: async (cobrancaId, status) => {
    try {
      const response = await api.put(`/billing/payments/${cobrancaId}/status`, { status });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

export const mercadopagoService = {
  criarPreferenciaPublica: async (payload) => {
    try {
      const response = await api.post('/mercadopago/criar-preferencia-publica', payload);
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


};

export const snapIVService = {
  listarTestes: async (pacienteId) => {
    try {
      const response = await api.get(`/snap-iv/paciente/${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  criarTeste: async (pacienteId, respostas) => {
    try {
      const response = await api.post(`/snap-iv/paciente/${pacienteId}`, respostas);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterTeste: async (testeId) => {
    try {
      const response = await api.get(`/snap-iv/${testeId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterUltimoTeste: async (pacienteId) => {
    try {
      const response = await api.get(`/snap-iv/paciente/${pacienteId}/ultimo`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de chat multiagente (Crew)
export const crewAIService = {
  chat: async ({ mensagem, paciente_id = null, contexto = {} }) => {
    try {
      const response = await api.post(
        '/crew-ai/chat',
        {
          mensagem,
          paciente_id,
          contexto
        },
        {
          timeout: 0
        }
      );
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de chat simples (funciona melhor com modelos locais pequenos)
export const chatSimplesService = {
  chat: async ({ mensagem, paciente_id = null }) => {
    try {
      const response = await api.post(
        '/chat-simples',
        {
          mensagem,
          paciente_id
        },
        {
          timeout: 120000 // 2 minutos
        }
      );
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  stt: async (audioBase64) => {
    try {
      const response = await api.post('/chat-simples/stt', { audio: audioBase64 });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de transcrição' };
    }
  },
  tts: async (text) => {
    try {
      const response = await api.post('/chat-simples/tts', { text }, { timeout: 60000 });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de síntese de voz' };
    }
  }
};

export const beckDepressionService = {
  listarTestes: async (pacienteId) => {
    try {
      const response = await api.get(`/beck-depression/paciente/${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  criarTeste: async (pacienteId, respostas) => {
    try {
      const response = await api.post(`/beck-depression/paciente/${pacienteId}`, respostas);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterTeste: async (testeId) => {
    try {
      const response = await api.get(`/beck-depression/${testeId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterUltimoTeste: async (pacienteId) => {
    try {
      const response = await api.get(`/beck-depression/paciente/${pacienteId}/ultimo`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de IA Management
export const aiManagementService = {
  getDashboardStats: async () => {
    try {
      const response = await api.get('/ai-management/dashboard-stats');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  getLLMConfigs: async () => {
    try {
      const response = await api.get('/ai-management/llm-configs');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  createLLMConfig: async (config) => {
    try {
      const response = await api.post('/ai-management/llm-configs', config);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  updateLLMConfig: async (configId, config) => {
    try {
      const response = await api.put(`/ai-management/llm-configs/${configId}`, config);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  deleteLLMConfig: async (configId) => {
    try {
      const response = await api.delete(`/ai-management/llm-configs/${configId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  getAgents: async () => {
    try {
      const response = await api.get('/ai-management/agents');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  createAgent: async (agent) => {
    try {
      const response = await api.post('/ai-management/agents', agent);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  updateAgent: async (agentId, agent) => {
    try {
      const response = await api.put(`/ai-management/agents/${agentId}`, agent);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  deleteAgent: async (agentId) => {
    try {
      const response = await api.delete(`/ai-management/agents/${agentId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  getPrompts: async () => {
    try {
      const response = await api.get('/ai-management/prompts');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  createPrompt: async (prompt) => {
    try {
      const response = await api.post('/ai-management/prompts', prompt);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  updatePrompt: async (promptId, prompt) => {
    try {
      const response = await api.put(`/ai-management/prompts/${promptId}`, prompt);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  deletePrompt: async (promptId) => {
    try {
      const response = await api.delete(`/ai-management/prompts/${promptId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  getCrews: async () => {
    try {
      const response = await api.get('/ai-management/crews');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  createCrew: async (crew) => {
    try {
      const response = await api.post('/ai-management/crews', crew);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  updateCrew: async (crewId, crew) => {
    try {
      const response = await api.put(`/ai-management/crews/${crewId}`, crew);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  deleteCrew: async (crewId) => {
    try {
      const response = await api.delete(`/ai-management/crews/${crewId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  getExecutionLogs: async () => {
    try {
      const response = await api.get('/ai-management/execution-logs');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  getAvailableProviders: async () => {
    try {
      const response = await api.get('/ai-management/providers/available');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  testProvider: async (providerData) => {
    try {
      const response = await api.post('/ai-management/providers/test', providerData);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço PHQ-9
export const phq9Service = {
  criarTeste: async (pacienteId, testeData) => {
    try {
      const response = await api.post(`/phq9/paciente/${pacienteId}`, testeData);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  listar: async (pacienteId) => {
    try {
      const response = await api.get(`/phq9/paciente/${pacienteId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  obterUltimoTeste: async (pacienteId) => {
    try {
      const response = await api.get(`/phq9/paciente/${pacienteId}/ultimo`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  excluir: async (testeId) => {
    try {
      const response = await api.delete(`/phq9/${testeId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de configuração geral de IA (provedor/modelo padrão)
export const aiConfigService = {
  obterProvedores: async () => {
    try {
      const response = await api.get('/ai-config/providers');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  atualizarConfiguracao: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post(`/ai-config/providers/${provider}`, {
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  testarConfiguracao: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post('/ai-config/test', {
        provider,
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  atualizarConfiguracaoVision: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post(`/ai-config/providers/vision/${provider}`, {
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  atualizarConfiguracaoMultimodal: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post(`/ai-config/providers/multimodal/${provider}`, {
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  // Novos métodos para configuração por função
  atualizarConfiguracaoChat: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post(`/ai-config/providers/chat/${provider}`, {
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  atualizarConfiguracaoAudio: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post(`/ai-config/providers/audio/${provider}`, {
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  atualizarConfiguracaoSpreadsheet: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post(`/ai-config/providers/spreadsheet/${provider}`, {
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },

  atualizarConfiguracaoPDF: async ({ provider, model, api_key, base_url }) => {
    try {
      const response = await api.post(`/ai-config/providers/pdf/${provider}`, {
        model,
        api_key,
        base_url
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

export const dashboardService = {
  getStats: async () => {
    try {
      const response = await api.get('/dashboard/stats');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

export const prescricaoConfigService = {
  obter: async () => {
    try {
      const response = await api.get('/prescricao-config/');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  salvar: async (payload) => {
    try {
      const isFormData = payload instanceof FormData;
      const config = isFormData ? { headers: { 'Content-Type': 'multipart/form-data' } } : {};
      const response = await api.post('/prescricao-config/', payload, config);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de Onboarding
export const onboardingService = {
  status: async () => {
    try {
      const response = await api.get('/onboarding/status');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  saveStep: async (stepNumber, data) => {
    try {
      const response = await api.post(`/onboarding/step/${stepNumber}`, { data });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  skip: async () => {
    try {
      const response = await api.post('/onboarding/skip');
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// Serviço de Verificação de Email
export const emailVerificationService = {
  verify: async (token) => {
    try {
      const response = await api.get(`/auth/verify-email/${token}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  resend: async (email) => {
    try {
      const response = await api.post('/auth/resend-verification', { email });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// ═══════════════════════════════════════════════════════════════
// AraOS Week 11D — Digital Twin API
// ═══════════════════════════════════════════════════════════════
export const twinService = {
  obterTwin: async (patientId) => {
    try {
      const response = await api.get(`/twin/${patientId}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  obterResumo: async (patientId) => {
    try {
      const response = await api.get(`/twin/${patientId}/summary`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  obterTimeline: async (patientId) => {
    try {
      const response = await api.get(`/twin/${patientId}/timeline`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  obterOutcomes: async (patientId) => {
    try {
      const response = await api.get(`/twin/${patientId}/outcomes`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  obterDashboard: async (patientId) => {
    try {
      const response = await api.get(`/twin/${patientId}/dashboard`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// ═══════════════════════════════════════════════════════════════
// AraOS Week 11D — Cannabis Module API
// ═══════════════════════════════════════════════════════════════
export const cannabisService = {
  obterPerfil: async (patientId) => {
    try {
      const response = await api.get(`/cannabis/profiles/${patientId}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  criarPerfil: async (payload) => {
    try {
      const response = await api.post('/cannabis/profiles', payload);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  atualizarPerfil: async (patientId, payload) => {
    try {
      const response = await api.put(`/cannabis/profiles/${patientId}`, payload);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarProdutos: async () => {
    try {
      const response = await api.get('/cannabis/products');
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  criarProduto: async (payload) => {
    try {
      const response = await api.post('/cannabis/products', payload);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarDoses: async (patientId) => {
    try {
      const response = await api.get(`/cannabis/doses/${patientId}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  criarDose: async (payload) => {
    try {
      const response = await api.post('/cannabis/doses', payload);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarOutcomes: async (patientId, metric = null) => {
    try {
      const url = metric
        ? `/cannabis/outcomes/${patientId}?metric=${encodeURIComponent(metric)}`
        : `/cannabis/outcomes/${patientId}`;
      const response = await api.get(url);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  criarOutcome: async (payload) => {
    try {
      const response = await api.post('/cannabis/outcomes', payload);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarAlertas: async (params = {}) => {
    try {
      const query = new URLSearchParams();
      if (params.patient_id) query.append('patient_id', params.patient_id);
      if (params.status) query.append('status', params.status);
      if (params.severity) query.append('severity', params.severity);
      const response = await api.get(`/cannabis/alerts?${query.toString()}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  resolverAlerta: async (alertId) => {
    try {
      const response = await api.post(`/cannabis/alerts/${alertId}/resolve`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

// ═══════════════════════════════════════════════════════════════
// AraOS Week 11D — Follow-up Engine API
// ═══════════════════════════════════════════════════════════════
export const followupService = {
  listarProgramas: async (patientId = null) => {
    try {
      const url = patientId ? `/followup/programs?patient_id=${patientId}` : '/followup/programs';
      const response = await api.get(url);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  criarPrograma: async (payload) => {
    try {
      const response = await api.post('/followup/programs', payload);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  obterPrograma: async (programId) => {
    try {
      const response = await api.get(`/followup/programs/${programId}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarFases: async (programId = null) => {
    try {
      const url = programId ? `/followup/phases?program_id=${programId}` : '/followup/phases';
      const response = await api.get(url);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarCheckpoints: async (params = {}) => {
    try {
      const query = new URLSearchParams();
      if (params.program_id) query.append('program_id', params.program_id);
      if (params.status) query.append('status', params.status);
      const response = await api.get(`/followup/checkpoints?${query.toString()}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarQuestionarios: async (programId = null) => {
    try {
      const url = programId ? `/followup/questionnaires?program_id=${programId}` : '/followup/questionnaires';
      const response = await api.get(url);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarRespostas: async (params = {}) => {
    try {
      const query = new URLSearchParams();
      if (params.patient_id) query.append('patient_id', params.patient_id);
      if (params.questionnaire_id) query.append('questionnaire_id', params.questionnaire_id);
      const response = await api.get(`/followup/responses?${query.toString()}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  criarResposta: async (payload) => {
    try {
      const response = await api.post('/followup/responses', payload);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  listarAlertas: async (params = {}) => {
    try {
      const query = new URLSearchParams();
      if (params.patient_id) query.append('patient_id', params.patient_id);
      if (params.status) query.append('status', params.status);
      const response = await api.get(`/followup/alerts?${query.toString()}`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  },
  resolverAlerta: async (alertId) => {
    try {
      const response = await api.post(`/followup/alerts/${alertId}/resolve`);
      return response.data.data || response.data;
    } catch (error) {
      throw error.response ? error.response.data : { error: 'Erro de conexão' };
    }
  }
};

export default api;
