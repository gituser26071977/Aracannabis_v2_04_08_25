// Knowledge API — thin wrapper over the shared axios `api` instance.
// Consumes ONLY /api/v1/knowledge/* (per RC1 Gate 2 frozen contract).
// No direct backend access, no domain access, no other endpoints.

import api from '../../../services/api';

const BASE = '/v1/knowledge';

/**
 * Unwrap a Gate 2 envelope into its `data` payload, attaching meta.
 * Throws an Error annotated with the envelope's error code so hooks
 * can surface a stable `error.code` to the UI.
 *
 * Returns `{ payload, meta }` so the UI can access request_id / correlation_id
 * for the Timeline rail without losing the envelope semantics.
 */
function unwrap(envelope) {
  if (!envelope || envelope.success !== true) {
    const err = new Error(envelope?.error?.message || 'API request failed');
    err.code = envelope?.error?.code || 'INTERNAL_ERROR';
    err.details = envelope?.error?.details;
    err.meta = envelope?.meta;
    throw err;
  }
  return { payload: envelope.data, meta: envelope.meta || null };
}

export const knowledgeApi = {
  /** GET /knowledge/health — public, no auth required. */
  async health() {
    const r = await api.get(`${BASE}/health`);
    return unwrap(r.data);
  },

  /** POST /knowledge/pipelines/run */
  async runPipeline(request) {
    const r = await api.post(`${BASE}/pipelines/run`, request);
    return unwrap(r.data);
  },

  /** GET /knowledge/genomes */
  async listGenomes() {
    const r = await api.get(`${BASE}/genomes`);
    return unwrap(r.data);
  },

  /** GET /knowledge/genomes/{id} */
  async getGenome(genomeId) {
    const r = await api.get(`${BASE}/genomes/${encodeURIComponent(genomeId)}`);
    return unwrap(r.data);
  },

  /** GET /knowledge/cohorts */
  async listCohorts() {
    const r = await api.get(`${BASE}/cohorts`);
    return unwrap(r.data);
  },

  /** GET /knowledge/cohorts/{id} */
  async getCohort(cohortId) {
    const r = await api.get(`${BASE}/cohorts/${encodeURIComponent(cohortId)}`);
    return unwrap(r.data);
  },

  /** GET /knowledge/research/sessions */
  async listSessions() {
    const r = await api.get(`${BASE}/research/sessions`);
    return unwrap(r.data);
  },

  /** GET /knowledge/research/sessions/{id} */
  async getSession(sessionId) {
    const r = await api.get(
      `${BASE}/research/sessions/${encodeURIComponent(sessionId)}`
    );
    return unwrap(r.data);
  },

  /** POST /knowledge/research/sessions/{id}/replay */
  async replaySession(sessionId) {
    const r = await api.post(
      `${BASE}/research/sessions/${encodeURIComponent(sessionId)}/replay`
    );
    return unwrap(r.data);
  },
};

export default knowledgeApi;
