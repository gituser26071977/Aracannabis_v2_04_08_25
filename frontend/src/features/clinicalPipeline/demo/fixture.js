// Demo Mode fixture — deterministic dataset that mirrors the API response shape.
// Used only when the URL contains ?demo=1. Never persisted; never reaches the backend.
//
// This is the *only* place Demo data lives. The fixture flows through the same
// composePipelineVm() pipeline as a real API response, so mappers and components
// exercise exactly the same code path. Zero changes to domain, REST, DTOs, or SQL.

const t0 = '2026-07-22T08:31:02.000Z';
const t1 = '2026-07-22T08:31:02.250Z';
const t2 = '2026-07-22T08:31:02.850Z';
const t3 = '2026-07-22T08:31:03.420Z';
const t4 = '2026-07-22T08:31:03.980Z';
const t5 = '2026-07-22T08:31:04.250Z';

const GENES = [
  { id: 'g_sleep_latency', label: 'Latência do sono' },
  { id: 'g_sleep_efficiency', label: 'Eficiência do sono' },
  { id: 'g_anxiety_baseline', label: 'Ansiedade basal' },
  { id: 'g_anxiety_arousal', label: 'Hiperarousal' },
  { id: 'g_mood_valence', label: 'Valência afetiva' },
  { id: 'g_mood_arousal', label: 'Ativação emocional' },
  { id: 'g_cognitive_focus', label: 'Foco atencional' },
  { id: 'g_cognitive_load', label: 'Carga cognitiva' },
  { id: 'g_social_engagement', label: 'Engajamento social' },
  { id: 'g_social_withdrawal', label: 'Retraimento social' },
  { id: 'g_somatic_tension', label: 'Tensão somática' },
  { id: 'g_energy_level', label: 'Nível de energia' },
];

const STATE_HASH = 'sha256:REDACTED';

// 12-node circular graph: each gene connects to two neighbors with a typed edge.
const NODES = GENES.map((g, idx) => ({
  node_id: `n_${g.id}`,
  node_type: 'GENE',
  label: g.label,
  urn: `urn:araos:gene:rc1-demo:${g.id}`,
}));

const EDGES = [];
for (let i = 0; i < GENES.length; i++) {
  const a = NODES[i];
  const b = NODES[(i + 1) % GENES.length];
  EDGES.push({
    edge_id: `e_${i}_${(i + 1) % GENES.length}`,
    source_node_id: a.node_id,
    target_node_id: b.node_id,
    edge_type: i % 2 === 0 ? 'CORRELATION' : 'INFLUENCE',
    weight: 0.4 + (i * 0.04),
  });
}
EDGES.push({
  edge_id: 'e_long_0_6',
  source_node_id: NODES[0].node_id,
  target_node_id: NODES[6].node_id,
  edge_type: 'CORRELATION',
  weight: 0.82,
});

const GRAPH = {
  graph_id: 'graph_rc1_demo_001',
  state_hash: STATE_HASH,
  built_at: t4,
  urn: 'urn:araos:graph:rc1-demo:001',
  nodes: NODES,
  edges: EDGES,
};

const CORRELATIONS = [
  { correlation_id: 'c_001', gene_x_id: 'g_sleep_latency', gene_y_id: 'g_anxiety_arousal', method: 'pearson', coefficient: -0.82, confidence: 0.94, computed_at: t2 },
  { correlation_id: 'c_002', gene_x_id: 'g_sleep_efficiency', gene_y_id: 'g_cognitive_focus', method: 'pearson', coefficient: 0.76, confidence: 0.91, computed_at: t2 },
  { correlation_id: 'c_003', gene_x_id: 'g_anxiety_baseline', gene_y_id: 'g_somatic_tension', method: 'pearson', coefficient: 0.71, confidence: 0.88, computed_at: t2 },
  { correlation_id: 'c_004', gene_x_id: 'g_mood_valence', gene_y_id: 'g_social_engagement', method: 'pearson', coefficient: 0.66, confidence: 0.83, computed_at: t2 },
  { correlation_id: 'c_005', gene_x_id: 'g_cognitive_load', gene_y_id: 'g_energy_level', method: 'pearson', coefficient: -0.61, confidence: 0.79, computed_at: t2 },
  { correlation_id: 'c_006', gene_x_id: 'g_social_withdrawal', gene_y_id: 'g_anxiety_arousal', method: 'pearson', coefficient: 0.58, confidence: 0.77, computed_at: t2 },
  { correlation_id: 'c_007', gene_x_id: 'g_sleep_latency', gene_y_id: 'g_somatic_tension', method: 'spearman', coefficient: 0.47, confidence: 0.72, computed_at: t2 },
  { correlation_id: 'c_008', gene_x_id: 'g_mood_arousal', gene_y_id: 'g_anxiety_baseline', method: 'spearman', coefficient: 0.44, confidence: 0.69, computed_at: t2 },
];

const HYPOTHESES = [
  {
    hypothesis_id: 'h_001',
    claim: 'Latência do sono elevada está associada a hiperarousal autonômico (ρ=-0.82, p<0.001).',
    confidence: 0.91,
    rule_id: 'R-SLEEP-ANXIETY-001',
    status: 'CONFIRMED',
    supporting_genes: ['g_sleep_latency', 'g_anxiety_arousal', 'g_somatic_tension'],
    contradicting_genes: [],
  },
  {
    hypothesis_id: 'h_002',
    claim: 'Eficiência do sono prediz foco atencional na janela analisada (ρ=0.76).',
    confidence: 0.84,
    rule_id: 'R-SLEEP-COG-002',
    status: 'CONFIRMED',
    supporting_genes: ['g_sleep_efficiency', 'g_cognitive_focus'],
    contradicting_genes: [],
  },
  {
    hypothesis_id: 'h_003',
    claim: 'Retraimento social correlaciona-se com hiperarousal (ρ=0.58).',
    confidence: 0.72,
    rule_id: 'R-SOCIAL-ANXIETY-003',
    status: 'CONFIRMED',
    supporting_genes: ['g_social_withdrawal', 'g_anxiety_arousal'],
    contradicting_genes: [],
  },
];

const GENOME = {
  genome_id: 'genome_rc1_demo_a1',
  patient_id: 'patient_demo_a1',
  state_hash: STATE_HASH,
  built_at: t1,
  urn: 'urn:araos:genome:rc1-demo:a1',
  window_label: '6_months',
  window_start: '2026-01-01T00:00:00Z',
  window_end: '2026-07-01T00:00:00Z',
  gene_count: GENES.length,
  gene_ids: GENES.map((g) => g.id),
  correlation_count: CORRELATIONS.length,
  hypothesis_count: HYPOTHESES.length,
  has_graph: true,
  graph_snapshot_id: GRAPH.graph_id,
};

export const DEMO_RUN_RESPONSE = {
  success: true,
  data: {
    genome: GENOME,
    correlations: CORRELATIONS,
    hypotheses: HYPOTHESES,
    graph: GRAPH,
    started_at: t0,
    completed_at: t5,
    duration_seconds: 2.25,
  },
  meta: {
    request_id: 'req_rc1_demo_a1',
    correlation_id: 'corr_rc1_demo_a1',
    latency_ms: 2250,
    timestamp: t5,
    demo: true,
  },
};

export const DEMO_SESSIONS = [
  { session_id: 'sess_rc1_demo_a1', analysis_type: 'PIPELINE_RUN', created_at: t5 },
  { session_id: 'sess_rc1_demo_b1', analysis_type: 'PIPELINE_RUN', created_at: '2026-07-22T07:14:11.000Z' },
];

export const DEMO_REPLAY_RESPONSE = {
  success: true,
  data: {
    session_id: 'sess_rc1_demo_a1_replayed',
    state_hash: STATE_HASH, // identical → reproducible
    reproducible: true,
    started_at: '2026-07-22T08:32:01.000Z',
    completed_at: '2026-07-22T08:32:02.300Z',
    duration_seconds: 1.30,
  },
  meta: {
    request_id: 'req_rc1_replay_a1',
    correlation_id: 'corr_rc1_replay_a1',
    latency_ms: 1300,
    timestamp: '2026-07-22T08:32:02.300Z',
    demo: true,
  },
};