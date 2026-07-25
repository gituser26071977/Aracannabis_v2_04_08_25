/**
 * neuroService — Módulo NEURODESENVOLVIMENTO (Sprint 1)
 *
 * Cliente HTTP para o subsistema plugin-based de escalas neuropsicológicas.
 * Consome `/api/neuro/scales/*` (Flask backend).
 *
 * Integra com a instância axios principal (`api.js`) para herdar
 * automaticamente JWT + X-Association-ID + CSRF.
 */

import api from './api';

const BASE = '/neuro/scales';

/**
 * Lista todas as escalas disponíveis no registry.
 *
 * @param {Object} options
 * @param {number} [options.ageMonths] - filtra por idade em meses
 * @returns {Promise<{scales: Array, total: number}>}
 */
export const listCatalog = async ({ ageMonths } = {}) => {
  const params = {};
  if (ageMonths !== undefined && ageMonths !== null) {
    params.age_months = ageMonths;
  }
  const res = await api.get(`${BASE}/catalog`, { params });
  return res.data;
};

/**
 * Retorna spec completo de uma escala (incluindo JSON Schema).
 *
 * @param {string} code - ex: "GAD7", "PHQ9"
 * @param {string} [version="latest"]
 * @returns {Promise<Object>} ScaleSpec serializado
 */
export const getScaleSpec = async (code, version = 'latest') => {
  const res = await api.get(`${BASE}/${code}`, { params: { version } });
  return res.data;
};

/**
 * Aplica uma escala a um paciente.
 *
 * @param {string} code
 * @param {Object} payload
 * @param {string} payload.patient_id
 * @param {Object} payload.raw_responses
 * @param {Object} [payload.metadata]
 * @param {string} [payload.source="ui"]
 * @param {string} [payload.status="final"]
 * @param {string} [payload.version="latest"]
 * @returns {Promise<Object>} StoredScaleResponse
 */
export const applyScale = async (code, payload) => {
  const res = await api.post(`${BASE}/${code}/apply`, payload);
  return res.data;
};

/**
 * Lista respostas de escalas de um paciente.
 *
 * @param {Object} params
 * @param {string} params.patient_id
 * @param {string} [params.scale_code]
 * @param {number} [params.limit=100]
 * @returns {Promise<{responses: Array, total: number}>}
 */
export const listResponses = async ({ patient_id, scale_code, limit = 100 }) => {
  const res = await api.get(`${BASE}/responses`, {
    params: { patient_id, scale_code, limit },
  });
  return res.data;
};

/**
 * Recupera uma resposta específica por id.
 *
 * @param {string} responseId
 * @returns {Promise<Object>}
 */
export const getResponse = async (responseId) => {
  const res = await api.get(`${BASE}/responses/${responseId}`);
  return res.data;
};

const neuroService = {
  listCatalog,
  getScaleSpec,
  applyScale,
  listResponses,
  getResponse,
};

export default neuroService;