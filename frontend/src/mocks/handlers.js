// MSW handlers for the Knowledge API — mirrors Gate 2 envelope.
// Enable per-test via `server.listen()` in setup; defaults to off in prod.

import { http, HttpResponse } from 'msw';

const BASE = '/api/v1/knowledge';

const envelope = (data, meta = {}) => ({
  success: true,
  data,
  error: null,
  meta: { timestamp: new Date().toISOString(), request_id: 'req_test', correlation_id: 'corr_test', ...meta },
});

export const handlers = [
  http.post(`${BASE}/pipelines/run`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(
      envelope({
        genome: {
          genome_id: 'genome_test_001',
          tenant_id: 'tenant_test',
          patient_id: body.patient_id,
          window_start: body.window_start,
          window_end: body.window_end,
          window_label: body.window_label || null,
          state_hash: 'h_test',
          built_at: new Date().toISOString(),
          graph_snapshot_id: 'graph_test_001',
          gene_ids: ['gene_1', 'gene_2', 'gene_3'],
          gene_count: 3,
          correlation_count: 2,
          hypothesis_count: 2,
          has_graph: true,
          urn: 'urn:araos:test:genome:001',
        },
        correlations: [
          { correlation_id: 'c1', method: 'POSITIVE', gene_x_id: 'gene_1', gene_y_id: 'gene_2', coefficient: 0.8, p_value: 0.01, n_observations: 30, confidence: 0.9, computed_at: new Date().toISOString(), explanation_id: null },
          { correlation_id: 'c2', method: 'NEGATIVE', gene_x_id: 'gene_2', gene_y_id: 'gene_3', coefficient: -0.4, p_value: 0.05, n_observations: 30, confidence: 0.7, computed_at: new Date().toISOString(), explanation_id: null },
        ],
        hypotheses: [
          { hypothesis_id: 'h1', claim: 'G1 correlaciona com G2', confidence: 0.92, supporting_genes: ['gene_1', 'gene_2'], contradicting_genes: [], evidence: [], correlations_used: ['c1'], status: 'ACTIVE', rule_id: 'R1', created_at: new Date().toISOString(), explanation_id: null },
          { hypothesis_id: 'h2', claim: 'G2 inverte correlação com G3', confidence: 0.6, supporting_genes: ['gene_2'], contradicting_genes: ['gene_3'], evidence: [], correlations_used: ['c2'], status: 'PROBABLE', rule_id: 'R2', created_at: new Date().toISOString(), explanation_id: null },
        ],
        graph: {
          graph_id: 'graph_test_001',
          tenant_id: 'tenant_test',
          patient_id: body.patient_id,
          nodes: [
            { node_id: 'gene_1', node_type: 'gene', label: 'Gene 1', urn: 'urn:araos:gene:1' },
            { node_id: 'gene_2', node_type: 'gene', label: 'Gene 2', urn: 'urn:araos:gene:2' },
            { node_id: 'gene_3', node_type: 'gene', label: 'Gene 3', urn: 'urn:araos:gene:3' },
          ],
          edges: [
            { edge_id: 'e1', source_node_id: 'gene_1', target_node_id: 'gene_2', edge_type: 'POSITIVE', weight: 0.8 },
            { edge_id: 'e2', source_node_id: 'gene_2', target_node_id: 'gene_3', edge_type: 'NEGATIVE', weight: 0.4 },
          ],
          built_at: new Date().toISOString(),
          state_hash: 'h_graph_test',
          urn: 'urn:araos:graph:001',
        },
        started_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
        duration_seconds: 1.234,
      })
    );
  }),

  http.get(`${BASE}/research/sessions`, () =>
    HttpResponse.json(envelope({ items: [
      { session_id: 'sess_alpha', tenant_id: 'tenant_test', query_id: 'q1', cohort_id: 'cohort_a', analysis_type: 'CORRELATIONS', started_at: new Date().toISOString(), completed_at: new Date().toISOString(), duration_seconds: 0.9, state_hash: 'h_test', reproducible: true },
      { session_id: 'sess_beta', tenant_id: 'tenant_test', query_id: 'q2', cohort_id: 'cohort_b', analysis_type: 'HYPOTHESES', started_at: new Date().toISOString(), completed_at: new Date().toISOString(), duration_seconds: 1.1, state_hash: 'h_test', reproducible: true },
    ], count: 2 }))
  ),

  http.post(`${BASE}/research/sessions/:sid/replay`, ({ params }) =>
    HttpResponse.json(envelope({
      session_id: `${params.sid}_replayed`,
      tenant_id: 'tenant_test',
      query_id: 'q1',
      cohort_id: 'cohort_a',
      analysis_type: 'CORRELATIONS',
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
      duration_seconds: 1.0,
      state_hash: 'h_test',
      reproducible: true,
      result_json: '{}',
      explanation_id: null,
    }))
  ),
];
