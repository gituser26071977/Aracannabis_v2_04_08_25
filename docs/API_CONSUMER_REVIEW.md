# API Consumer Review — RC1 Gate 2.5

> **Perspective:** external third-party integrator.
> **Inputs:** `docs/OPENAPI.yaml`, `docs/RC1_GATE_2_DTO_SPEC.md`, `docs/RC1_GATE_2_ENDPOINT_MATRIX.md`.
> **Out of scope:** SQL, SQLAlchemy, services, domain, repository — all approved upstream.
> **Goal:** evaluate the experience of consuming the API, *not* the implementation underneath.

---

## 1. Primeira impressão

Open the OpenAPI. The first thing the integrator reads is:

> "RC1 public API for the Clinical Knowledge Engine. The API is a translation layer only — all business logic lives in the Knowledge Service. … Cross-tenant access returns 404 (no existence leak) — never 403."

That sentence is gold. In three lines it tells me:

1. The API is intentional (translation layer, not a leaky abstraction).
2. There is a tenant model (JWT-linked association).
3. The error semantics are opinionated (404 instead of 403).

The URL structure is clean: `/knowledge/health`, `/knowledge/pipelines/run`, `/knowledge/genomes`, `/knowledge/cohorts`, `/knowledge/research/sessions`. Five nouns/verbs, four read patterns, one write. The naming tells me there is a *clinical knowledge* domain; it does not dump me into a generic CRUD.

The envelope is documented in the description AND shown in every error example. By the time I write my first `curl`, I already know `success / data / error / meta`.

**Verdict of first impression:** This *feels* like a product. Not a backend that was exposed later.

---

## 2. Clareza

### 2.1 The five-minute test

A new integrator needs to answer:

- *What can I do?* → list of operations, grouped by tag.
- *What do I send?* → request schema + example.
- *What do I get back?* → response schema + envelope.
- *What can go wrong?* → `components.responses` with examples.
- *How is authentication handled?* → `security: bearerAuth` + examples on `Unauthorized`.

The OpenAPI delivers all five without me leaving the file.

### 2.2 The domain vocabulary is consistent

| Term | Used consistently as |
|------|---------------------|
| `genome` | A computed projection for a patient + window |
| `pipeline` | The orchestration that produces correlations → hypotheses → graph |
| `correlation` | Pairwise gene relationship |
| `hypothesis` | A clinical claim supported by correlations |
| `knowledge graph` | Nodes (genes) + edges (correlations/hypotheses) |
| `cohort` | A matched-patient set |
| `research session` | A reproducible query execution |
| `replay` | Deterministic re-execution of a session |

Every noun maps to a tag, a path prefix, or a DTO. No surprising synonymy.

### 2.3 The pipeline story

The `pipelines/run` description names the stages in order: *"correlations (Pearson/Spearman/etc.), generates hypotheses, and optionally builds the knowledge graph"*. This is the only place the integrator needs to read to understand the computation model. The output schema mirrors it 1:1 (`genome`, `correlations`, `hypotheses`, `graph`).

The story is clear. ✅

---

## 3. Consistência

### 3.1 URL grammar

| Pattern | Used in | Verdict |
|---------|---------|---------|
| `/knowledge/<resource>` (list) | genomes, cohorts, research/sessions | ✅ consistent |
| `/knowledge/<resource>/{id}` (detail) | genomes/{id}, cohorts/{id}, research/sessions/{id} | ✅ consistent |
| `/knowledge/<resource>/{id}/<verb>` (action) | research/sessions/{id}/replay | ✅ consistent |
| `/knowledge/<resource>/<verb>` (command) | pipelines/run | ✅ consistent (only POST-as-action outside REST conventions; clearly intentional because pipelines are commands, not resources) |
| `/knowledge/health` | health | ✅ consistent (one-off) |

The `pipelines/run` is the one slight outlier (verb in path, no resource ID), but it is the only POST besides replay, and its naming tells you exactly that.

### 3.2 HTTP method usage

| Operation | Method | Justification |
|-----------|--------|---------------|
| List | GET | ✅ |
| Detail | GET | ✅ |
| Run pipeline | POST | ✅ (creates a new genome + graph) |
| Replay | POST | ✅ (creates a new session) |
| Update | — | intentionally absent |
| Delete | — | intentionally absent |

The platform returns `201` for both creation endpoints (`pipelines/run`, `replay`). That is correct REST for *new resources created by an action*.

### 3.3 DTO naming

| Suffix | Used for | Verdict |
|--------|----------|---------|
| `*Request` | request body | ✅ (only `PipelineRunRequest`) |
| `*Response` | response envelope wrappers | ✅ |
| `*Summary` | list items | ✅ (`GenomeSummary`, `ResearchSessionSummary`) |
| `*Detail` | detail items | ✅ (`GenomeDetail`, `ResearchSessionDetail`) |
| (no suffix) | embedded entities | ✅ (`Correlation`, `Hypothesis`, `Cohort`, `KnowledgeGraph`) |

The summary/detail split is exactly the pattern every API consumer recognizes from GitHub, Stripe, GitLab. Nothing to relearn.

### 3.4 Field naming convention

All fields are `snake_case`. All timestamps are ISO 8601 with offset. All IDs are strings. These three invariants are documented in the DTO spec §0 ("Design Invariants") and honored throughout. ✅

### 3.5 Error envelope shape

Every error example in `components.responses` uses the exact same envelope:

```json
{
  "success": false,
  "data": null,
  "error": { "code": "...", "message": "...", "details": [...] },
  "meta": { "timestamp": "...", "request_id": "...", "correlation_id": "...", "latency_ms": ... }
}
```

Identical shape across `BadRequest`, `Unauthorized`, `Forbidden`, `NotFound`, `InternalError`, `ServiceUnavailable`. ✅

---

## 4. Descoberta de funcionalidades

### 4.1 Five tags tell the story

`Health`, `Knowledge: Pipelines`, `Knowledge: Genomes`, `Knowledge: Cohorts`, `Knowledge: Research`. Each tag has 1–3 operations. An integrator scanning the OpenAPI in a code generator sees the entire product surface in one screen.

### 4.2 What I wish I could find but cannot

- **No "getting started" / quickstart in the OpenAPI description.** I would add 2–3 sentences after the envelope example: "1) `POST /api/auth/login` to get a JWT. 2) `POST /api/v1/knowledge/pipelines/run` to compute. 3) `GET /api/v1/knowledge/genomes/{id}` to inspect."
- **No example of how to obtain a JWT.** The integrator is told `security: bearerAuth` but is not told *where the token comes from*. (The legacy `/api/auth/login` endpoint is not documented anywhere in the new doc set.)
- **No example of the `methods` enum values.** The enum is in the schema, but a sentence like "valid values: POSITIVE, NEGATIVE, PARTIAL, NONLINEAR (empty = use all)" appears only as a description string, not as a code-friendly constant table.
- **No "what IDs look like" guidance.** `genome_id`, `cohort_id`, `session_id` are documented as `string`. There is no example value pattern (UUID? hash? composite?). An integrator building a UI has no way to predict display length.

### 4.3 OpenAPI quality

The file validates as `openapi: 3.0.3`. All schemas declare `required`. Enums are used where appropriate. `allOf` is used to compose `GenomeDetail = GenomeSummary + extra fields` and `ResearchSessionDetail = ResearchSessionSummary + result_json` — a clean DRY pattern that codegen tools (openapi-generator, orval, etc.) honor correctly.

---

## 5. Fluxos de integração

### 5.1 Typical consumer flow

> "1. execute pipeline; 2. obtain genome; 3. consult cohort; 4. recover replay."

Does the API make that flow evident?

| Step | Endpoint | Available? | Discoverable? |
|------|----------|-----------|---------------|
| 1. Run pipeline | `POST /pipelines/run` | ✅ | ✅ (`operationId: runPipeline`) |
| 2a. List genomes | `GET /genomes` | ✅ | ✅ (`listGenomes`) |
| 2b. Get genome detail | `GET /genomes/{id}` | ✅ | ✅ (`getGenome`) |
| 3. List cohorts | `GET /cohorts` | ✅ | ✅ (`listCohorts`) |
| 3b. Cohort detail | `GET /cohorts/{id}` | ✅ | ✅ (`getCohort`) |
| 4. List sessions | `GET /research/sessions` | ✅ | ✅ (`listResearchSessions`) |
| 4b. Session detail | `GET /research/sessions/{id}` | ✅ | ✅ (`getResearchSession`) |
| 4c. Replay | `POST /research/sessions/{id}/replay` | ✅ | ✅ (`replayResearchSession`) |

The flow is *possible*. It is not *narrated*. There is no "cookbook" section in the OpenAPI description; the integrator has to reconstruct it from the operation IDs.

### 5.2 Hidden coupling the integrator will discover late

- The pipeline response includes `genome.genome_id`. To list genomes, the integrator reads `data.items[].genome_id` from `GET /genomes`. The pipeline does *not* return a `Location` header pointing to that genome — they must remember to call `GET /genomes/{id}` themselves.
- The session replay returns a *new* session with a *new* `session_id`. There is no way to know in advance which session was the latest — the integrator must compare `started_at` timestamps.
- The genome detail endpoint embeds correlations/hypotheses but **not** the graph. The graph is *only* available from the `pipelines/run` response. If the integrator runs the pipeline, loses the response, and later calls `GET /genomes/{id}`, they will not get the graph back — they will see `has_graph: true` and no `graph` field.

That last point is the biggest discovery friction. The PipelineRunData has a graph; the GenomeDetail has `has_graph: bool` but not the graph itself. The consumer has to know to inspect the pipeline response OR call an unspecified-by-this-API alternative.

---

## 6. Dificuldades encontradas

### 6.1 Top five questions a new integrator will ask (in order)

1. **"Where do I get a JWT?"** — Not in this doc set. The integrator must hunt in the legacy SIAP docs (`/api/auth/login`) or read source.
2. **"Why is `state_hash` everywhere, and what do I do with it?"** — Mentioned in many places, but no narrative: "It is a deterministic SHA-256 over the entity's canonical content; identical inputs ⇒ identical hash; useful for cache validation and replay reproducibility."
3. **"Why does the pipeline response include a graph but `GET /genomes/{id}` does not?"** — Asymmetry between two endpoints that nominally return the same thing.
4. **"What does `urn` mean, and where does it come from?"** — `urn` appears on `GenomeDetail`, `KnowledgeGraph`. It is not explained. The integrator does not know if it is required, if it is stable across tenants, or if it can be used to cross-reference other systems.
5. **"Why are some IDs formatted as plain strings with no documented pattern?"** — `genome_id`, `cohort_id`, `session_id` are `string` but the spec does not say whether they are UUIDs, hashes, or composable. An integrator building a UI cannot decide whether to display them in full or truncate them safely.

### 6.2 Frictions I did *not* experience

- **No surprise 403s.** Every forbidden-like response is documented as 404 ("no existence leak"). A consumer writing "if status >= 400, show error toast" is safe.
- **No hidden pagination surprise.** Pagination is intentionally absent for RC1; the API returns `items + count`. The integrator who ignores pagination will not be broken in V1.
- **No silent type drift.** All IDs are strings, all times are ISO 8601 strings, all numbers are numbers. No "sometimes it's a string, sometimes it's an int".
- **No inconsistent envelope.** Every single response (success and error) goes through the same wrapper. A consumer can write one helper and reuse it.

---

## 7. Sugestões de melhoria (sem alterar o domínio)

These are **documentation / OpenAPI enrichment** only. No endpoints change. No DTOs change. No domain changes.

### 7.1 Add a "Quickstart" section to `OPENAPI.yaml` `info.description`

Two paragraphs after the envelope:

> **Quickstart**
> 1. Authenticate via `POST /api/auth/login` to receive a JWT (documented separately).
> 2. `POST /api/v1/knowledge/pipelines/run` with `{patient_id, window_start, window_end}` to compute correlations, hypotheses, and (optionally) the knowledge graph.
> 3. Persist `data.genome.genome_id` from the response. Use `GET /api/v1/knowledge/genomes/{genome_id}` to retrieve detail.

### 7.2 Document the JWT acquisition path

Either:

- Add a one-liner in the OpenAPI description: "JWTs are issued by `POST /api/auth/login` (legacy SIAP authentication endpoint). See `docs/SIAP_AUTH.md`."
- Or create a new minimal `docs/API_AUTH.md` referenced from the OpenAPI.

### 7.3 Make the graph asymmetry explicit

Either:

- Update `GenomeDetail` to embed the graph (matches `PipelineRunData`).
- Or update the `GET /genomes/{id}` description: *"Returns the genome record and correlation/hypothesis lists; the knowledge graph is **not** included here. To obtain the graph, inspect the original `pipelines/run` response or call replay of the corresponding research session."*

### 7.4 Add a "Field reference" subsection to the DTO spec

A two-column table mapping each ID type to its format:

| Field | Format | Example | Notes |
|-------|--------|---------|-------|
| `genome_id` | deterministic hash | `genome_a3f9b2...` | content-derived |
| `cohort_id` | deterministic hash | `cohort_5e21c4...` | content-derived |
| `session_id` | UUID v4 | `sess_5e21c4...` | server-assigned |

### 7.5 Add `result_json` semantics

The `ResearchSessionDetail.result_json` is documented as *"Canonical JSON (no parse on server)."* Add one sentence: *"The value is a serialized JSON STRING (not an embedded object). Consumers MUST parse it themselves if they need structured access."* This avoids the silent bug where an integrator assumes it is already an object.

### 7.6 Add a `description` example showing the envelope on success

The error responses have example envelopes. The success responses should too, at least for `PipelineRunResponse` and `GenomeDetailResponse`. Right now the success schema has no example; the integrator has to guess the envelope.

### 7.7 Add 1–2 sentence narrative to each tag

E.g. `"Knowledge: Pipelines"` currently has: *"Pipeline orchestration (run correlation to hypothesis to graph)."* Good. But `"Knowledge: Research"` says only *"Research sessions and reproducibility (replay)."* Extend with: *"Use list+detail to inspect prior analyses; use the replay endpoint to re-execute a session deterministically (the new session's state_hash will match the original)."*

### 7.8 ID format and prefix

Consider exposing a documented prefix convention (`genome_*`, `cohort_*`, `sess_*`). This is harmless to add to descriptions and makes log scrubbing / grep easier.

### 7.9 What I am NOT proposing

- ❌ New endpoints.
- ❌ Removed endpoints.
- ❌ Modified DTOs.
- ❌ Domain changes.
- ❌ Service signature changes.
- ❌ Error code changes.

---

## 8. Veredito

The API **is** a product. It tells a story (pipeline → genome → correlation → hypothesis → graph → replay), it has opinionated and consistent semantics (envelope, tenant via JWT, cross-tenant 404), and it ships an OpenAPI that a code generator can consume end-to-end without help.

The frictions are entirely **documentation-level**:

- The pipeline response asymmetry with `GET /genomes/{id}` (graph present vs absent) is the one substantive consumer-facing gap.
- The remaining 7 items are copy-edit / example additions to `OPENAPI.yaml` and the DTO spec.

None of these require any endpoint, DTO, domain, or service change.

### 🟡 Pequenos ajustes de usabilidade.

The API is **ready** in shape, frozen in contract, and consistent in semantics. It needs **a documentation pass** to become *pleasant* to integrate. Specifically:

1. Quickstart section in OpenAPI `info.description`.
2. JWT acquisition documented.
3. Graph asymmetry explained (not removed).
4. Field reference table for ID formats.
5. `result_json` semantics spelled out.
6. Success-example payloads for the two creation endpoints.

These are 1–2 hours of documentation work. After that, the API can be re-reviewed and the verdict moves to 🟢.

---

*Reviewed from the integrator's chair. No domain was touched. No endpoint was touched. The contract is frozen; only its presentation is being asked to improve.*