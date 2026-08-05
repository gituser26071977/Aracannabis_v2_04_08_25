// DTO → ViewModel mappers. The UI never imports DTO types directly.
// Pure functions, no React, no side effects.

const NUMERIC_PRECISION = 4;

function fmtNum(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return null;
  return Number(Number(n).toFixed(NUMERIC_PRECISION));
}

/**
 * Map a PipelineRun envelope payload (the `data` field) into a composed
 * ViewModel used by the Clinical Pipeline Explorer page.
 */
export function pipelineRunDataToViewModel(data) {
  if (!data) return null;
  const { genome, correlations = [], hypotheses = [], graph, started_at, completed_at, duration_seconds } = data;

  const coefficients = correlations.map((c) => Number(c.coefficient)).filter((n) => !Number.isNaN(n));
  const confidences = hypotheses.map((h) => Number(h.confidence)).filter((n) => !Number.isNaN(n));

  const topCorrelations = [...correlations]
    .sort((a, b) => Math.abs(Number(b.coefficient)) - Math.abs(Number(a.coefficient)))
    .slice(0, 5)
    .map((c) => ({
      id: c.correlation_id,
      geneX: c.gene_x_id,
      geneY: c.gene_y_id,
      method: c.method,
      coefficient: fmtNum(c.coefficient),
      confidence: fmtNum(c.confidence),
    }));

  const topHypotheses = [...hypotheses]
    .sort((a, b) => Number(b.confidence) - Number(a.confidence))
    .slice(0, 3)
    .map((h) => ({
      id: h.hypothesis_id,
      claim: h.claim,
      confidence: fmtNum(h.confidence),
      supportingGenes: h.supporting_genes || [],
      contradictingGenes: h.contradicting_genes || [],
      ruleId: h.rule_id,
      status: h.status,
    }));

  const methods = Array.from(new Set(correlations.map((c) => c.method)));

  return {
    patient: {
      id: genome?.patient_id || null,
      windowLabel: genome?.window_label || null,
      windowStart: genome?.window_start || null,
      windowEnd: genome?.window_end || null,
    },
    pipeline: {
      startedAt: started_at || null,
      completedAt: completed_at || null,
      durationSeconds: duration_seconds ?? null,
      version: '1.0.0',
    },
    genome: genome
      ? {
          id: genome.genome_id,
          stateHash: genome.state_hash,
          builtAt: genome.built_at,
          urn: genome.urn,
          geneCount: genome.gene_count || 0,
          geneIds: genome.gene_ids || [],
          correlationCount: genome.correlation_count || 0,
          hypothesisCount: genome.hypothesis_count || 0,
          hasGraph: !!genome.has_graph,
          graphSnapshotId: genome.graph_snapshot_id || null,
        }
      : null,
    correlations: {
      count: correlations.length,
      top5: topCorrelations,
      methods,
      max: coefficients.length ? fmtNum(Math.max(...coefficients.map(Math.abs))) : null,
      mean:
        coefficients.length
          ? fmtNum(coefficients.reduce((s, n) => s + Math.abs(n), 0) / coefficients.length)
          : null,
      all: correlations,
    },
    hypotheses: {
      count: hypotheses.length,
      top3: topHypotheses,
      maxConfidence: confidences.length ? fmtNum(Math.max(...confidences)) : null,
      meanConfidence: confidences.length
        ? fmtNum(confidences.reduce((s, n) => s + n, 0) / confidences.length)
        : null,
      all: hypotheses,
    },
    graph: graph
      ? {
          id: graph.graph_id,
          stateHash: graph.state_hash,
          builtAt: graph.built_at,
          urn: graph.urn,
          nodeCount: (graph.nodes || []).length,
          edgeCount: (graph.edges || []).length,
          nodes: (graph.nodes || []).map((n) => ({
            id: n.node_id,
            type: n.node_type,
            label: n.label,
            urn: n.urn,
          })),
          edges: (graph.edges || []).map((e) => ({
            id: e.edge_id,
            source: e.source_node_id,
            target: e.target_node_id,
            type: e.edge_type,
            weight: fmtNum(e.weight),
          })),
        }
      : null,
  };
}

/** A new pipeline run produces a single timeline entry. */
export function buildTimelineFromVm(vm, requestId, correlationId) {
  if (!vm) return [];
  const steps = [
    { label: 'Pipeline iniciado', at: vm.pipeline.startedAt },
    { label: `Genome criado (${vm.genome?.id || '—'})`, at: vm.genome?.builtAt },
    { label: `Correlações: ${vm.correlations.count}`, at: vm.pipeline.startedAt },
    { label: `Hipóteses: ${vm.hypotheses.count}`, at: vm.pipeline.startedAt },
  ];
  if (vm.graph) {
    steps.push({ label: `Graph persistido (${vm.graph.nodeCount} nós, ${vm.graph.edgeCount} arestas)`, at: vm.graph.builtAt });
  }
  steps.push({ label: 'Pipeline concluído', at: vm.pipeline.completedAt });
  return steps
    .filter((s) => s.at)
    .map((s, idx) => ({
      id: `step-${idx}`,
      label: s.label,
      at: s.at,
      requestId,
      correlationId,
    }))
    .sort((a, b) => new Date(a.at).getTime() - new Date(b.at).getTime());
}

/** Map a research-session replay result to a small VM with diff info. */
export function replayResultToViewModel(replayed, originalStateHash) {
  if (!replayed) return null;
  const match = (replayed.state_hash || null) === (originalStateHash || null);
  return {
    sessionId: replayed.session_id,
    stateHash: replayed.state_hash,
    reproducible: replayed.reproducible,
    startedAt: replayed.started_at,
    completedAt: replayed.completed_at,
    durationSeconds: replayed.duration_seconds,
    match,
    diff: match
      ? null
      : {
          original: originalStateHash,
          replay: replayed.state_hash,
        },
  };
}

/** Map a GenomeDetail (from GET /genomes/{id}) to a VM focused on summary fields. */
export function genomeDetailToViewModel(detail) {
  if (!detail) return null;
  return {
    id: detail.genome_id,
    patientId: detail.patient_id,
    stateHash: detail.state_hash,
    builtAt: detail.built_at,
    urn: detail.urn,
    geneCount: detail.gene_count || 0,
    correlationCount: detail.correlation_count || 0,
    hypothesisCount: detail.hypothesis_count || 0,
    hasGraph: !!detail.has_graph,
    windowStart: detail.window_start,
    windowEnd: detail.window_end,
    windowLabel: detail.window_label || null,
  };
}
