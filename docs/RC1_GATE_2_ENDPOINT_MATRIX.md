# RC1 Gate 2 — Endpoint Matrix (Frozen v1.0)

> **Status:** FROZEN at v1.0 (2026-07-23).
> **Companion documents:** `docs/OPENAPI.yaml`, `docs/RC1_GATE_2_DTO_SPEC.md`, `docs/RC1_GATE_2_REPORT.md`.

This is the canonical list of public endpoints for the AraOS Clinical Intelligence **Knowledge API**.

## 1. Three Elimination Questions — Answered (Plan §A)

### Q1 — Which endpoints did we eliminate?

**Eliminated** (with reasons):

| Candidate | Verdict | Reason |
|-----------|---------|--------|
| `POST /correlations` | ❌ | Correlations are derived sub-resources of a genome. The pipeline already produces them. |
| `POST /hypotheses` | ❌ | Hypotheses are derived sub-resources. No standalone persistence semantic. |
| `POST /graphs` | ❌ | Graphs are derived. Would duplicate the pipeline's job. |
| `PUT /graphs/{id}` | ❌ | No business use case (graphs are computed, not edited). |
| `DELETE /genomes/{id}` | ❌ | Out of scope for RC1 (audit implications deferred). |
| `POST /cohorts` | ❌ | Cohort construction belongs in research session replay; deferred to Wave 4 (Dashboard). |
| `PATCH /research/sessions/{id}` | ❌ | Sessions are immutable after completion. |

### Q2 — Which endpoints were redundant?

| Candidate pair | Resolution |
|----------------|------------|
| `GET /genomes/{id}` vs `GET /genomes/{id}/graph` | **Merged** — graph is a field inside the genome response. Avoids N+1. |
| `GET /research/sessions/{id}` vs `GET /research/sessions/{id}/result` | **Merged** — `result_json` is a field on the detail response. |
| `GET /cohorts/{id}/patients` vs `GET /cohorts/{id}` | **Merged** — `matched_patient_ids` is a field on the cohort DTO. |

### Q3 — Which endpoints were aggregated?

- `POST /pipelines/run` aggregates **Correlation + Hypothesis + Graph** into a single capability. The client POSTs one body, gets one envelope. No separate write endpoints for sub-resources.

## 2. Final Endpoint Matrix — 9 Endpoints

| # | Method | Path | Capability | Domain Service | Permission | Auth Required |
|---|--------|------|-----------|----------------|-----------|--------------|
| 1 | `GET`  | `/api/v1/knowledge/health` | Liveness probe | (none) | none | ❌ |
| 2 | `POST` | `/api/v1/knowledge/pipelines/run` | Run correlation→hypothesis→graph | `KnowledgeService.run_pipeline` | `INTELLIGENCE_CORRELATION_COMPUTE` | ✅ |
| 3 | `GET`  | `/api/v1/knowledge/genomes` | List genomes for tenant | `KnowledgeRepository.list_genomes` | `INTELLIGENCE_CORRELATION_READ` | ✅ |
| 4 | `GET`  | `/api/v1/knowledge/genomes/{genome_id}` | Read single genome + graph | `KnowledgeRepository.load_genome` | `INTELLIGENCE_CORRELATION_READ` | ✅ |
| 5 | `GET`  | `/api/v1/knowledge/cohorts` | List cohorts | `KnowledgeRepository.list_cohorts` | `INTELLIGENCE_COHORT_READ` | ✅ |
| 6 | `GET`  | `/api/v1/knowledge/cohorts/{cohort_id}` | Read cohort detail | `KnowledgeRepository.load_cohort` | `INTELLIGENCE_COHORT_READ` | ✅ |
| 7 | `GET`  | `/api/v1/knowledge/research/sessions` | List research sessions | `KnowledgeRepository.list_sessions` | `INTELLIGENCE_RESEARCH_READ` | ✅ |
| 8 | `GET`  | `/api/v1/knowledge/research/sessions/{session_id}` | Read session canonical JSON | `KnowledgeRepository.load_session` | `INTELLIGENCE_RESEARCH_READ` | ✅ |
| 9 | `POST` | `/api/v1/knowledge/research/sessions/{session_id}/replay` | Replay prior session | `ResearchService.replay` | `INTELLIGENCE_REPLAY_EXECUTE` | ✅ |

**Note on permissions `INTELLIGENCE_RESEARCH_READ` and `INTELLIGENCE_REPLAY_EXECUTE`:**

These two constants were added to `araos/platform/identity/permissions.py` as a metadata-only extension (no domain change). The `Permission` class is a string registry; adding constants does not modify behavior. This was done to keep the endpoint matrix aligned with the contract from §B of the plan.

## 3. Path Prefix and Versioning

- All endpoints live under `/api/v1/knowledge/*`.
- The blueprint url_prefix is `/api/v1/knowledge`.
- Versioning strategy: V1 is frozen; V2 launches at `/api/v2/` with breaking changes.
- Health endpoint is the only public (no-auth) endpoint.

## 4. Response Envelope (FROZEN)

All endpoints — success and failure — return:

```json
{
  "success": true | false,
  "data": <object|array|null>,
  "error": null | { "code": "...", "message": "...", "details": <dict|list> },
  "meta": {
    "timestamp": "<ISO 8601>",
    "request_id": "<uuid v4>",
    "correlation_id": "<inbound header or request_id>",
    "latency_ms": <float>
  }
}
```

## 5. HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | OK (read, list) |
| 201 | Created (POST that produces a genome/session) |
| 400 | Body validation failed (`VALIDATION_ERROR`) or semantic input error (`INVALID_REQUEST`) |
| 401 | Missing/invalid JWT (`AUTH_REQUIRED`) or no association (`TENANT_REQUIRED`) |
| 403 | Permission denied (`PERMISSION_DENIED`) |
| 404 | Resource not found in this tenant (no existence leak) |
| 500 | Unhandled internal error |
| 503 | Persistence backend not configured |

## 6. Cross-Tenant Behavior (FROZEN)

- Cross-tenant access ALWAYS returns **404** (never 403).
- Rationale: 403 leaks existence of the resource. 404 says "not in your tenant" without revealing whether it exists elsewhere.
- This applies to genomes, cohorts, sessions.

## 7. Observability Headers (Always Present)

| Header | Direction | Content |
|--------|-----------|---------|
| `X-Request-ID` | Response | UUID v4 generated server-side |
| `X-Correlation-ID` | Bidirectional | Echoed inbound header, or fallback to request_id |
| `X-Latency-MS` | Response | Float, server-measured wall time |

## 8. What is NOT in this matrix (deferred)

- `POST /cohorts` (creation) — deferred to Wave 4 (Dashboard).
- `DELETE /genomes/{id}` — deferred (audit implications).
- `PATCH /research/sessions/{id}` — sessions are immutable.
- Pagination, filtering, sort — deferred to V2.
- Rate limiting, throttling — platform concern, not REST concern.
- GraphQL, gRPC — out of scope.
- Background job queues — replay is sync.

## 9. Wire Contract Compliance

| Requirement | Implementation | Verified |
|-------------|---------------|---------|
| `tenant_id` never from request body | `g.tenant_id` set only by `@tenant_required` from JWT | ✅ |
| DTOs independent of ORM/domain | `interfaces/rest/v1/dto.py` imports zero SQLAlchemy/domain | ✅ |
| Error envelope standardized | `success_envelope`/`error_envelope` wrappers in `interfaces/rest/v1/errors.py` | ✅ |
| Every route auth-prepared | All business routes use `@tenant_required` | ✅ |
| Every route tenant-prepared | `g.tenant_id` from JWT, never from body | ✅ |
| Every route audit-prepared | `observability.register_request_hooks` calls `create_audit_entry` best-effort | ✅ |
| Cross-tenant → 404 | `KnowledgeRepository.load_*` is tenant-bound; cross-tenant returns None | ✅ |
| Versioned (`/api/v1/`) | `Blueprint(url_prefix="/api/v1/knowledge")` | ✅ |
| 10 acceptance criteria per endpoint | Each test file covers contract + error + isolation + audit + envelope | ✅ |

---

*See also: `docs/OPENAPI.yaml`, `docs/RC1_GATE_2_DTO_SPEC.md`, `docs/RC1_GATE_2_REPORT.md`.*
