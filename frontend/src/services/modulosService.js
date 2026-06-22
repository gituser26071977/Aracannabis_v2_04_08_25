/**
 * modulosService.js — Cliente de API para os Módulos de Especialidade.
 *
 * Endpoints consumidos:
 *   GET    /api/modulos                       — Catálogo
 *   GET    /api/meus-modulos                  — Minhas assinaturas
 *   GET    /api/meus-modulos/<slug>           — Detalhe
 *   POST   /api/modulos/<slug>/ativar-trial   — Inicia trial de 14 dias
 *   POST   /api/modulos/<slug>/checkout       — Gera link MercadoPago
 *   POST   /api/modulos/<slug>/revogar-consentimento
 *   GET    /api/meus-modulos/export           — Export LGPD
 */

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const authHeaders = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('token') || ''}`,
});

async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: authHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { raw: text }; }
  if (!res.ok) {
    const err = new Error((data && data.error) || `HTTP ${res.status}`);
    err.status = res.status;
    err.payload = data;
    throw err;
  }
  return data;
}

export const listarCatalogo = () => request('/api/modulos');

export const listarMinhas = () => request('/api/meus-modulos');

export const detalheMinha = (slug) => request(`/api/meus-modulos/${slug}`);

export const ativarTrial = (slug, consentimentoAceito = true) =>
  request(`/api/modulos/${slug}/ativar-trial`, {
    method: 'POST',
    body: { consentimento_aceito: consentimentoAceito },
  });

export const iniciarCheckout = (slug, consentimentoAceito = true) =>
  request(`/api/modulos/${slug}/checkout`, {
    method: 'POST',
    body: { consentimento_aceito: consentimentoAceito },
  });

export const revogarConsentimento = (slug) =>
  request(`/api/modulos/${slug}/revogar-consentimento`, { method: 'POST' });

export const exportarLgpd = () => request('/api/meus-modulos/export');

/**
 * Helper: retorna um Map slug -> assinatura (acesso_ativo) para checagem rápida
 * em componentes que precisarem gatear funcionalidades (ex.: mostrar /cannabis
 * só se a assinatura de cannabis-medicinal estiver ativa).
 */
export const indexarAssinaturasAtivas = (assinaturas = []) => {
  const map = {};
  for (const a of assinaturas) {
    if (a.modulo && a.acesso_ativo) {
      map[a.modulo.slug] = a;
    }
  }
  return map;
};

export default {
  listarCatalogo,
  listarMinhas,
  detalheMinha,
  ativarTrial,
  iniciarCheckout,
  revogarConsentimento,
  exportarLgpd,
  indexarAssinaturasAtivas,
};
