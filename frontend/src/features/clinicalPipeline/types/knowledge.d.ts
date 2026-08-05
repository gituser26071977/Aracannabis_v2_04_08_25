// Knowledge API DTOs — typed via JSDoc since the project is JavaScript.
// Mirror of docs/OPENAPI.yaml (frozen at Gate 2).
// These types are consumed ONLY by the mapper layer; UI components import ViewModels.

/**
 * @typedef {Object} Meta
 * @property {string} timestamp
 * @property {string} request_id
 * @property {string} [correlation_id]
 * @property {number} [latency_ms]
 */

/**
 * @typedef {Object} ApiError
 * @property {string} code        e.g. GENOME_NOT_FOUND
 * @property {string} message
 * @property {Array<{field?: string, error?: string, value?: any}>} [details]
 */

/**
 * @typedef {Object} Envelope
 * @property {boolean} success
 * @property {*} data
 * @property {ApiError|null} error
 * @property {Meta} meta
 */

/**
 * @typedef {Object} HealthData
 * @property {string} status
 * @property {string} version
 * @property {string} timestamp
 */

/**
 * @typedef {Object} GenomeSummary
 * @property {string} genome_id
 * @property {string} tenant_id
 * @property {string} patient_id
 * @property {string} window_start
 * @property {string} window_end
 * @property {string|null} window_label
 * @property {string} state_hash
 * @property {string} built_at
 * @property {number} gene_count
 * @property {boolean} has_graph
 */

/**
 * @typedef {Object} GenomeDetail
 * @property {string} genome_id
 * @property {string} tenant_id
 * @property {string} patient_id
 * @property {string} window_start
 * @property {string} window_end
 * @property {string|null} window_label
 * @property {string} state_hash
 * @property {string} built_at
 * @property {string|null} graph_snapshot_id
 * @property {string[]} gene_ids
 * @property {number} gene_count
 * @property {number} correlation_count
 * @property {number} hypothesis_count
 * @property {boolean} has_graph
 * @property {string} urn
 */

/**
 * @typedef {Object} Correlation
 * @property {string} correlation_id
 * @property {string} method
 * @property {string} gene_x_id
 * @property {string} gene_y_id
 * @property {number} coefficient
 * @property {number|null} p_value
 * @property {number} n_observations
 * @property {number} confidence
 * @property {string} computed_at
 * @property {string|null} explanation_id
 */

/**
 * @typedef {Object} Hypothesis
 * @property {string} hypothesis_id
 * @property {string} claim
 * @property {number} confidence
 * @property {string[]} supporting_genes
 * @property {string[]} contradicting_genes
 * @property {string[]} evidence
 * @property {string[]} correlations_used
 * @property {string} status
 * @property {string} rule_id
 * @property {string} created_at
 * @property {string|null} explanation_id
 */

/**
 * @typedef {Object} GraphNode
 * @property {string} node_id
 * @property {string} node_type
 * @property {string} label
 * @property {string} urn
 */

/**
 * @typedef {Object} GraphEdge
 * @property {string} edge_id
 * @property {string} source_node_id
 * @property {string} target_node_id
 * @property {string} edge_type
 * @property {number} weight
 */

/**
 * @typedef {Object} KnowledgeGraph
 * @property {string} graph_id
 * @property {string} tenant_id
 * @property {string} patient_id
 * @property {GraphNode[]} nodes
 * @property {GraphEdge[]} edges
 * @property {string} built_at
 * @property {string} state_hash
 * @property {string} urn
 */

/**
 * @typedef {Object} Cohort
 * @property {string} cohort_id
 * @property {string} tenant_id
 * @property {string} name
 * @property {Array<Object>} criteria
 * @property {string[]} matched_patient_ids
 * @property {number} count
 * @property {string} built_at
 * @property {string} state_hash
 */

/**
 * @typedef {Object} ResearchSessionSummary
 * @property {string} session_id
 * @property {string} tenant_id
 * @property {string} query_id
 * @property {string} cohort_id
 * @property {string} analysis_type
 * @property {string} started_at
 * @property {string} completed_at
 * @property {number} duration_seconds
 * @property {string} state_hash
 * @property {boolean} reproducible
 */

/**
 * @typedef {Object} ResearchSessionDetail
 * @property {string} session_id
 * @property {string} tenant_id
 * @property {string} query_id
 * @property {string} cohort_id
 * @property {string} analysis_type
 * @property {string} started_at
 * @property {string} completed_at
 * @property {number} duration_seconds
 * @property {string} state_hash
 * @property {boolean} reproducible
 * @property {string} result_json
 * @property {string|null} explanation_id
 */

/**
 * @typedef {Object} PipelineRunData
 * @property {GenomeDetail} genome
 * @property {Correlation[]} correlations
 * @property {Hypothesis[]} hypotheses
 * @property {KnowledgeGraph|null} graph
 * @property {string} started_at
 * @property {string} completed_at
 * @property {number} duration_seconds
 */

/**
 * @typedef {Object} PipelineRunRequest
 * @property {string} patient_id
 * @property {string} window_start
 * @property {string} window_end
 * @property {string|null} [window_label]
 * @property {string[]} [methods]
 * @property {boolean} [include_graph]
 */

export {};
