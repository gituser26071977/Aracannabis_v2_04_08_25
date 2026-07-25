# RC1 Gate 2 — DTO Specification

> **Status:** FROZEN at v1.0 (2026-07-23).
> **Companion documents:** `docs/OPENAPI.yaml`, `docs/RC1_GATE_2_ENDPOINT_MATRIX.md`, `docs/RC1_GATE_2_REPORT.md`.

This document defines every Data Transfer Object exposed by the AraOS Clinical Intelligence **Knowledge API** at `/api/v1/knowledge/*`.

## 0. Design Invariants

1. **DTOs are pure** — no SQLAlchemy, no domain entity imports in non-comment lines.
2. **DTOs are frozen dataclasses** — `to_dict()` produces a JSON-safe mapping.
3. **All time fields are ISO 8601 strings** — never raw `datetime`.
4. **All IDs are strings** — even when the underlying value is an integer.
5. **Stable key names** — V1 keys are FROZEN; additive growth only; breaking changes require V2 launch.
6. **No business logic in DTOs** — DTOs are shapes, not behavior.

## 1. Request DTOs

### 1.1 `PipelineRunRequest`

Body for `POST /api/v1/knowledge/pipelines/run`.

```python
@dataclass(frozen=True)
class PipelineRunRequest:
    patient_id: str                # required
    window_start: str              # required, ISO 8601 with timezone
    window_end: str                # required, ISO 8601 with timezone, strictly after start
    window_label: str | None = None
    methods: tuple[str, ...] = ()  # empty = use all CorrelationMethod
    include_graph: bool = True
```

**JSON example:**

```json
{
  "patient_id": "patient_a1",
  "window_start": "2026-01-01T00:00:00+00:00",
  "window_end":   "2026-06-01T00:00:00+00:00",
  "window_label": "6_months",
  "methods": [],
  "include_graph": true
}
```

**Validation rules (enforced in `parse_pipeline_run`):**

- `patient_id`, `window_start`, `window_end` required.
- `window_end` must be strictly after `window_start` (raises 400 `VALIDATION_ERROR` otherwise).
- `methods` must be an array of strings (empty allowed).
- `include_graph` defaults to `true`.
- `tenant_id` is NEVER accepted from the body — derived from JWT only.

## 2. Response DTOs

### 2.1 `HealthData`

Response for `GET /api/v1/knowledge/health`.

```python
@dataclass(frozen=True)
class HealthData:
    status: str        # "ok"
    version: str       # API version
    timestamp: str     # ISO 8601
```

```json
{ "status": "ok", "version": "1.0.0", "timestamp": "2026-07-23T10:00:00+00:00" }
```

### 2.2 `GenomeSummary`

Embedded inside list items of `GET /api/v1/knowledge/genomes`.

```python
@dataclass(frozen=True)
class GenomeSummary:
    genome_id: str
    tenant_id: str
    patient_id: str
    window_start: str
    window_end: str
    window_label: str | None
    state_hash: str
    built_at: str
    graph_snapshot_id: str | None
    gene_count: int
    has_graph: bool
```

### 2.3 `GenomeDetail`

Response for `GET /api/v1/knowledge/genomes/{genome_id}` and embedded in pipeline result.

```python
@dataclass(frozen=True)
class GenomeDetail:
    genome_id: str
    tenant_id: str
    patient_id: str
    window_start: str
    window_end: str
    window_label: str | None
    state_hash: str
    built_at: str
    graph_snapshot_id: str | None
    gene_ids: tuple[str, ...]
    gene_count: int
    correlation_count: int
    hypothesis_count: int
    has_graph: bool
    urn: str
```

### 2.4 `Correlation`

Embedded in pipeline result.

```python
@dataclass(frozen=True)
class Correlation:
    correlation_id: str
    method: str
    gene_x_id: str
    gene_y_id: str
    coefficient: float
    p_value: float | None
    n_observations: int
    confidence: float
    computed_at: str
    explanation_id: str | None
```

### 2.5 `Hypothesis`

Embedded in pipeline result.

```python
@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    claim: str
    confidence: float
    supporting_genes: tuple[str, ...]
    contradicting_genes: tuple[str, ...]
    evidence: tuple[str, ...]
    correlations_used: tuple[str, ...]
    status: str
    rule_id: str
    created_at: str
    explanation_id: str | None
```

### 2.6 `KnowledgeGraph`

Embedded in pipeline result.

```python
@dataclass(frozen=True)
class GraphNodePayload:
    node_id: str
    node_type: str
    label: str
    urn: str

@dataclass(frozen=True)
class GraphEdgePayload:
    edge_id: str
    source_node_id: str
    target_node_id: str
    edge_type: str
    weight: float

@dataclass(frozen=True)
class KnowledgeGraph:
    graph_id: str
    tenant_id: str
    patient_id: str
    nodes: tuple[GraphNodePayload, ...]
    edges: tuple[GraphEdgePayload, ...]
    built_at: str
    state_hash: str
    urn: str
```

### 2.7 `Cohort`

Response for `GET /api/v1/knowledge/cohorts/{cohort_id}` and list items.

```python
@dataclass(frozen=True)
class Cohort:
    cohort_id: str
    tenant_id: str
    name: str
    criteria: tuple[dict, ...]   # free-form criteria expressions
    matched_patient_ids: tuple[str, ...]
    count: int
    built_at: str
    state_hash: str
```

### 2.8 `ResearchSessionSummary` / `ResearchSessionDetail`

```python
@dataclass(frozen=True)
class ResearchSessionSummary:
    session_id: str
    tenant_id: str
    query_id: str
    cohort_id: str
    analysis_type: str
    started_at: str
    completed_at: str
    duration_seconds: float
    state_hash: str
    reproducible: bool

@dataclass(frozen=True)
class ResearchSessionDetail:
    session_id: str
    tenant_id: str
    query_id: str
    cohort_id: str
    analysis_type: str
    started_at: str
    completed_at: str
    duration_seconds: float
    state_hash: str
    reproducible: bool
    result_json: str          # canonical JSON string; not parsed server-side
    explanation_id: str | None
```

### 2.9 `PipelineRunData`

Top-level response for `POST /api/v1/knowledge/pipelines/run`.

```python
@dataclass(frozen=True)
class PipelineRunData:
    genome: GenomeDetail
    correlations: tuple[Correlation, ...]
    hypotheses: tuple[Hypothesis, ...]
    graph: KnowledgeGraph | None
    started_at: str
    completed_at: str
    duration_seconds: float
```

## 3. Envelope

Every endpoint returns the standard envelope:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "timestamp": "2026-07-23T10:00:00+00:00",
    "request_id": "uuid-v4",
    "correlation_id": "uuid-v4-or-inbound-header",
    "latency_ms": 12.34
  }
}
```

On failure:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "GENOME_NOT_FOUND",
    "message": "Genome not found",
    "details": {}
  },
  "meta": { "timestamp": "...", "request_id": "...", "correlation_id": "...", "latency_ms": 1.2 }
}
```

## 4. Error codes

| HTTP | Code | Trigger |
|------|------|---------|
| 400 | `INVALID_REQUEST` | Body shape OK but semantically wrong (no genes for patient, etc.) |
| 400 | `VALIDATION_ERROR` | Body failed validation (missing fields, bad dates, etc.) |
| 401 | `AUTH_REQUIRED` | Missing/invalid JWT |
| 401 | `TENANT_REQUIRED` | JWT valid but no active association |
| 403 | `PERMISSION_DENIED` | User lacks the required permission |
| 404 | `GENOME_NOT_FOUND` | Genome not found in this tenant |
| 404 | `COHORT_NOT_FOUND` | Cohort not found in this tenant |
| 404 | `RESEARCH_SESSION_NOT_FOUND` | Session not found in this tenant |
| 404 | `PATIENT_NOT_FOUND` | Patient not found |
| 500 | `INTERNAL_ERROR` | Unhandled exception |
| 503 | `SERVICE_UNAVAILABLE` | Persistence backend not configured |

## 5. Versioning

- **V1** (current) is FROZEN.
- New **optional** fields may be appended in additive manner; existing field names MUST NOT change.
- Breaking changes (renaming, removing fields, changing types) require **V2 launch** at `/api/v2/`.

## 6. Anti-leak audit

The DTO module MUST NOT contain:

- `import sqlalchemy` (verified — 0 matches)
- `import models_extra` (verified — 0 matches)
- Direct imports from `araos.clinical.knowledge.domain.*` (verified — only via `mappers.py`)

The REST layer (`interfaces/rest/v1/`) is verified pure: no SQLAlchemy, no domain mutation functions (`create_gene`, `replace_expression`, `apply_event`).

---

*See also: `docs/OPENAPI.yaml` for full OpenAPI 3.0.3 spec and `docs/RC1_GATE_2_ENDPOINT_MATRIX.md` for endpoint decisions.*
