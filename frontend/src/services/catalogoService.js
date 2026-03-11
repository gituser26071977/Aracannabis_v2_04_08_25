/**
 * Serviço de API para o Catálogo de Produtos de Cannabis
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Helper para fazer requisições autenticadas
const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  
  const defaultOptions = {
    headers: {
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  };
  
  const response = await fetch(`${API_URL}${url}`, { ...defaultOptions, ...options });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Erro na requisição');
  }
  
  return response.json();
};

// Upload de catálogo
export const uploadCatalogo = async (file, empresaOrigem = '') => {
  const formData = new FormData();
  formData.append('arquivo', file);
  if (empresaOrigem) {
    formData.append('empresa_origem', empresaOrigem);
  }
  
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_URL}/api/catalogo/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Erro no upload');
  }
  
  return response.json();
};

// Buscar produtos com filtros
export const buscarProdutos = async (filtros = {}) => {
  const params = new URLSearchParams();
  
  Object.entries(filtros).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params.append(key, value);
    }
  });
  
  const queryString = params.toString();
  const url = `/api/catalogo/produtos${queryString ? `?${queryString}` : ''}`;
  
  return fetchWithAuth(url);
};

// Obter produto por ID
export const obterProduto = async (produtoId) => {
  return fetchWithAuth(`/api/catalogo/produtos/${produtoId}`);
};

// Criar produto manualmente
export const criarProduto = async (produtoData) => {
  return fetchWithAuth('/api/catalogo/produtos', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(produtoData),
  });
};

// Atualizar produto
export const atualizarProduto = async (produtoId, produtoData) => {
  return fetchWithAuth(`/api/catalogo/produtos/${produtoId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(produtoData),
  });
};

// Deletar produto (inativar)
export const deletarProduto = async (produtoId) => {
  return fetchWithAuth(`/api/catalogo/produtos/${produtoId}`, {
    method: 'DELETE',
  });
};

// Sugerir produtos para prescrição
export const sugerirProdutos = async (pacienteId, condicao, sintomas, preferencias = {}) => {
  return fetchWithAuth('/api/catalogo/sugerir', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      paciente_id: pacienteId,
      condicao,
      sintomas,
      preferencias,
    }),
  });
};

// Validar produto com farmacêutico
export const validarProduto = async (produtoId) => {
  return fetchWithAuth(`/api/catalogo/produtos/${produtoId}/validar`, {
    method: 'POST',
  });
};

// Comparar produtos
export const compararProdutos = async (produtoIds) => {
  return fetchWithAuth('/api/catalogo/produtos/comparar', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ produto_ids: produtoIds }),
  });
};

// Listar marcas
export const listarMarcas = async () => {
  return fetchWithAuth('/api/catalogo/marcas');
};

// Listar categorias
export const listarCategorias = async () => {
  return fetchWithAuth('/api/catalogo/categorias');
};

// Estatísticas do catálogo
export const obterEstatisticas = async () => {
  return fetchWithAuth('/api/catalogo/estatisticas');
};

// Listar importações
export const listarImportacoes = async (page = 1, perPage = 20) => {
  return fetchWithAuth(`/api/catalogo/importacoes?page=${page}&per_page=${perPage}`);
};

// Listar sugestões históricas
export const listarSugestoes = async (pacienteId = null, page = 1, perPage = 20) => {
  let url = `/api/catalogo/sugestoes?page=${page}&per_page=${perPage}`;
  if (pacienteId) {
    url += `&paciente_id=${pacienteId}`;
  }
  return fetchWithAuth(url);
};

// Buscar atualizações na web
export const buscarAtualizacoesWeb = async (marca = '') => {
  const url = marca 
    ? `/api/catalogo/atualizacoes-web?marca=${encodeURIComponent(marca)}`
    : '/api/catalogo/atualizacoes-web';
  return fetchWithAuth(url);
};