import {
  pipelineRunDataToViewModel,
  buildTimelineFromVm,
  replayResultToViewModel,
} from './dtoToViewModel';

describe('pipelineRunDataToViewModel', () => {
  it('returns null for empty input', () => {
    expect(pipelineRunDataToViewModel(null)).toBeNull();
  });

  it('maps a complete pipeline response', () => {
    const data = {
      genome: {
        genome_id: 'g1',
        patient_id: 'p1',
        state_hash: 'h',
        built_at: '2026-01-01T00:00:00+00:00',
        urn: 'urn:x',
        gene_count: 3,
        gene_ids: ['g1', 'g2', 'g3'],
        correlation_count: 2,
        hypothesis_count: 2,
        has_graph: true,
        graph_snapshot_id: 'gs',
        window_start: '2026-01-01T00:00:00+00:00',
        window_end: '2026-06-01T00:00:00+00:00',
        window_label: '6_months',
      },
      correlations: [
        { correlation_id: 'c1', method: 'POSITIVE', gene_x_id: 'g1', gene_y_id: 'g2', coefficient: 0.9, confidence: 0.95, computed_at: 't', explanation_id: null },
        { correlation_id: 'c2', method: 'NEGATIVE', gene_x_id: 'g2', gene_y_id: 'g3', coefficient: -0.3, confidence: 0.6, computed_at: 't', explanation_id: null },
      ],
      hypotheses: [
        { hypothesis_id: 'h1', claim: 'A', confidence: 0.9, supporting_genes: ['g1'], contradicting_genes: [], rule_id: 'R1', status: 'ACTIVE', evidence: [], correlations_used: [], created_at: 't', explanation_id: null },
        { hypothesis_id: 'h2', claim: 'B', confidence: 0.5, supporting_genes: [], contradicting_genes: [], rule_id: 'R2', status: 'PROBABLE', evidence: [], correlations_used: [], created_at: 't', explanation_id: null },
      ],
      graph: {
        graph_id: 'graph_1',
        state_hash: 'hg',
        built_at: 't',
        urn: 'urn:g',
        nodes: [
          { node_id: 'g1', node_type: 'gene', label: 'G1', urn: 'urn:g1' },
          { node_id: 'g2', node_type: 'gene', label: 'G2', urn: 'urn:g2' },
          { node_id: 'g3', node_type: 'gene', label: 'G3', urn: 'urn:g3' },
        ],
        edges: [
          { edge_id: 'e1', source_node_id: 'g1', target_node_id: 'g2', edge_type: 'POSITIVE', weight: 0.9 },
        ],
      },
      started_at: '2026-01-01T00:00:00+00:00',
      completed_at: '2026-01-01T00:00:01+00:00',
      duration_seconds: 1.0,
    };

    const vm = pipelineRunDataToViewModel(data);
    expect(vm.genome.id).toBe('g1');
    expect(vm.correlations.count).toBe(2);
    expect(vm.correlations.top5).toHaveLength(2);
    expect(vm.correlations.top5[0].coefficient).toBe(0.9); // absolute sorted
    expect(vm.correlations.max).toBe(0.9);
    expect(vm.correlations.methods.sort()).toEqual(['NEGATIVE', 'POSITIVE']);
    expect(vm.hypotheses.count).toBe(2);
    expect(vm.hypotheses.top3[0].id).toBe('h1'); // highest confidence first
    expect(vm.graph.nodeCount).toBe(3);
    expect(vm.graph.edgeCount).toBe(1);
  });

  it('handles missing graph', () => {
    const vm = pipelineRunDataToViewModel({ genome: { gene_count: 0, gene_ids: [], correlation_count: 0, hypothesis_count: 0, has_graph: false }, correlations: [], hypotheses: [] });
    expect(vm.graph).toBeNull();
  });
});

describe('buildTimelineFromVm', () => {
  it('returns chronological entries', () => {
    const vm = pipelineRunDataToViewModel({
      genome: { patient_id: 'p', gene_count: 1, gene_ids: ['g'], correlation_count: 0, hypothesis_count: 0, has_graph: false, built_at: '2026-01-01T00:00:01+00:00' },
      correlations: [], hypotheses: [],
      started_at: '2026-01-01T00:00:00+00:00',
      completed_at: '2026-01-01T00:00:02+00:00',
      duration_seconds: 2,
    });
    const tl = buildTimelineFromVm(vm, 'req_1', 'corr_1');
    expect(tl.length).toBeGreaterThanOrEqual(4);
    expect(new Date(tl[tl.length - 1].at).getTime()).toBeGreaterThanOrEqual(new Date(tl[0].at).getTime());
  });
});

describe('replayResultToViewModel', () => {
  it('matches identical state_hash', () => {
    const out = replayResultToViewModel({ session_id: 'r', state_hash: 'h', reproducible: true, started_at: 't', completed_at: 't', duration_seconds: 1 }, 'h');
    expect(out.match).toBe(true);
    expect(out.diff).toBeNull();
  });
  it('detects mismatch', () => {
    const out = replayResultToViewModel({ session_id: 'r', state_hash: 'h_new', reproducible: true, started_at: 't', completed_at: 't', duration_seconds: 1 }, 'h_old');
    expect(out.match).toBe(false);
    expect(out.diff).toEqual({ original: 'h_old', replay: 'h_new' });
  });
});
