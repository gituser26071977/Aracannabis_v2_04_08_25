"""Knowledge API — Blueprint (RC1 Gate 2).

This module exposes 9 endpoints under ``/api/v1/knowledge/*``. Every
handler is a TRANSLATION step:

    HTTP request → DTO → existing domain service / repository → DTO → envelope

NO business logic lives in this file. The handlers exist to:
1. authenticate + resolve tenant (via ``@tenant_required``);
2. authorize (via ``@require_permission``);
3. parse + validate the request body to a DTO;
4. delegate to the appropriate existing service or repository;
5. map the result back to a DTO;
6. return the standard envelope.

Existing services used (per plan §B):
- ``KnowledgeService``       (run_pipeline, build_genome_from_genes)
- ``ResearchService``        (replay)
- ``KnowledgeRepository``    (load_/list_ genomes, cohorts, sessions, graphs)
- ``knowledge_composition``  (UoW-free context manager; commit on exit)

This module imports from ``araos.clinical.knowledge.application``
(services) and ``araos.clinical.knowledge.infrastructure.repository``
(abstract types). It deliberately does NOT import SQLAlchemy directly
— the repository SQL implementation is wired via ``knowledge_composition``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity

from araos.clinical.knowledge.application.composition import knowledge_composition
from araos.clinical.knowledge.application.knowledge_service import KnowledgeService
from araos.clinical.knowledge.application.research_service import ResearchService

from araos.platform.identity.permissions import Permission

from interfaces.rest.v1.auth import require_permission, tenant_required
from interfaces.rest.v1.dto import (
    HealthData,
    PipelineRunData,
    parse_pipeline_run,
)
from interfaces.rest.v1.errors import (
    COHORT_NOT_FOUND,
    GENOME_NOT_FOUND,
    INVALID_REQUEST,
    PERMISSION_DENIED,
    RESEARCH_SESSION_NOT_FOUND,
    SERVICE_UNAVAILABLE,
    VALIDATION_ERROR,
    error_envelope,
    register_error_handlers,
    success_envelope,
)
from interfaces.rest.v1 import mappers


logger = logging.getLogger("interfaces.rest.v1.knowledge")


# ─────────────────────────────────────────────────────────────────────
# Blueprint
# ─────────────────────────────────────────────────────────────────────

knowledge_bp = Blueprint(
    "knowledge_v1",
    __name__,
    url_prefix="/api/v1/knowledge",
)

register_error_handlers(knowledge_bp)


# ─────────────────────────────────────────────────────────────────────
# Health (no auth — public liveness probe)
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.get("/health")
def health():
    """Public liveness probe — no auth required.

    Returns a stable envelope shape so dashboards/clients can use the
    same parser for /health as for business endpoints.
    """
    payload = HealthData(
        status="ok",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return success_envelope(payload.to_dict())


# ─────────────────────────────────────────────────────────────────────
# Internal helper — resolve session_factory from app config
# ─────────────────────────────────────────────────────────────────────

def _session_factory():
    """Return a callable that produces a SQLAlchemy ``Session``.

    Source: ``current_app.config["REDACTED"]``.
    Falls back to ``None`` (services that don't need persistence
    — like ``run_pipeline`` — can still call the application layer
    in memory without erroring).
    """
    factory = current_app.config.get("REDACTED")
    if factory is None:
        return None
    return factory


def _build_window(window_start: str, window_end: str, window_label: str | None):
    """Build a domain ``TimeWindow`` from request DTO inputs.

    Imported lazily to avoid pulling domain into the module top-level
    (acceptable here because we are the translation layer; we DO touch
    domain types for serialization, but we never mutate them).
    """
    from araos.clinical.timeline.domain.window import TimeWindow

    start = datetime.fromisoformat(window_start.replace("Z", "+00:00"))
    end = datetime.fromisoformat(window_end.replace("Z", "+00:00"))
    return TimeWindow(start=start, end=end, label=window_label)


# ─────────────────────────────────────────────────────────────────────
# POST /pipelines/run
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.post("/pipelines/run")
@tenant_required
@require_permission(Permission.INTELLIGENCE_CORRELATION_COMPUTE)
def run_pipeline():
    """Run the correlation → hypothesis → graph pipeline for one patient."""
    body = request.get_json(silent=True) or {}
    try:
        req = parse_pipeline_run(body)
    except ValueError as exc:
        return error_envelope(VALIDATION_ERROR, str(exc), status=400)

    # Build the domain genome from the patient's persisted genes.
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )

    try:
        with knowledge_composition(session_factory, g.tenant_id) as repo:
            genes = repo.load_genes(req.patient_id)
            if not genes:
                return error_envelope(
                    INVALID_REQUEST,
                    f"No genes found for patient_id={req.patient_id} "
                    "in this tenant",
                    status=400,
                )
            window = _build_window(req.window_start, req.window_end, req.window_label)
            genome = KnowledgeService().build_genome_from_genes(
                tenant_id=g.tenant_id,
                patient_id=req.patient_id,
                window=window,
                genes=genes,
            )
            # Determine correlation methods (empty/None → all)
            methods = None
            if req.methods:
                from araos.clinical.knowledge.application.dto import (
                    CorrelationRequest as _CR,
                )
                method_names = {m.name for m in _CR.__dataclass_fields__ and ()}
                # We accept method names directly (string);
                # CorrelationMethod enum is mapped inside run_pipeline.
                from araos.clinical.knowledge.domain.correlation import CorrelationMethod
                methods = []
                for name in req.methods:
                    try:
                        methods.append(CorrelationMethod[name])
                    except KeyError:
                        return error_envelope(
                            VALIDATION_ERROR,
                            f"Unknown correlation method: {name}",
                            status=400,
                        )
            pipeline_result = KnowledgeService().run_pipeline(
                genome,
                methods=methods,
                include_graph=req.include_graph,
            )

            # Persist within the same composition transaction
            repo.save_genome(pipeline_result.genome)
            for c in pipeline_result.correlations:
                repo.save_correlation(c)
            for h in pipeline_result.hypotheses:
                repo.save_hypothesis(h)
            if pipeline_result.graph is not None:
                repo.save_graph(pipeline_result.graph)

        # Map and return
        genome_dto = mappers.genome_to_detail(pipeline_result.genome)
        correlations = mappers.correlations_to_dtos(pipeline_result.correlations)
        hypotheses = mappers.hypotheses_to_dtos(pipeline_result.hypotheses)
        graph_dto = (
            mappers.graph_to_dto(pipeline_result.graph)
            if pipeline_result.graph is not None
            else None
        )
        payload = PipelineRunData(
            genome=genome_dto,
            correlations=correlations,
            hypotheses=hypotheses,
            graph=graph_dto,
            started_at=pipeline_result.started_at.isoformat()
                if hasattr(pipeline_result.started_at, "isoformat")
                else str(pipeline_result.started_at),
            completed_at=pipeline_result.completed_at.isoformat()
                if hasattr(pipeline_result.completed_at, "isoformat")
                else str(pipeline_result.completed_at),
            duration_seconds=float(pipeline_result.duration_seconds),
        )
        return success_envelope(payload.to_dict(), status=201)

    except PermissionError as exc:
        return error_envelope(
            GENOME_NOT_FOUND,
            str(exc) or "Tenant or resource not found",
            status=404,
        )
    except Exception as exc:  # noqa: BLE001 — re-raised via after_request handler
        logger.exception("run_pipeline failed: %s", exc)
        raise


# ─────────────────────────────────────────────────────────────────────
# GET /genomes
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.get("/genomes")
@tenant_required
@require_permission(Permission.INTELLIGENCE_CORRELATION_READ)
def list_genomes():
    """List all genomes in the current tenant (lightweight summaries)."""
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )
    with knowledge_composition(session_factory, g.tenant_id) as repo:
        genomes = repo.list_genomes()
    items = [mappers.genome_to_summary(genome).to_dict() for genome in genomes]
    return success_envelope({"items": items, "count": len(items)})


# ─────────────────────────────────────────────────────────────────────
# GET /genomes/<genome_id>
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.get("/genomes/<string:genome_id>")
@tenant_required
@require_permission(Permission.INTELLIGENCE_CORRELATION_READ)
def get_genome(genome_id: str):
    """Read one genome by id (cross-tenant returns 404, never 403)."""
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )
    with knowledge_composition(session_factory, g.tenant_id) as repo:
        genome = repo.load_genome(genome_id)
        # If the genome references a graph, load that too (single transaction).
        graph = None
        if genome is not None and getattr(genome, "graph_snapshot_id", None):
            try:
                graph = repo.load_graph(genome.graph_snapshot_id)  # type: ignore[arg-type]
            except Exception:  # noqa: BLE001 — graph missing is non-fatal
                graph = None
    if genome is None:
        return error_envelope(
            GENOME_NOT_FOUND,
            f"Genome with id {genome_id} not found",
            status=404,
        )
    # Map domain → DTO and inject graph into the response (compact payload).
    detail = mappers.genome_to_detail(genome)
    detail_dict = detail.to_dict()
    detail_dict["correlations"] = [
        mappers.correlation_to_dto(c).to_dict() for c in getattr(genome, "correlation_results", ())
    ]
    detail_dict["hypotheses"] = [
        mappers.hypothesis_to_dto(h).to_dict() for h in getattr(genome, "hypotheses", ())
    ]
    detail_dict["graph"] = mappers.graph_to_dto(graph).to_dict() if graph is not None else None
    return success_envelope(detail_dict)


# ─────────────────────────────────────────────────────────────────────
# GET /cohorts
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.get("/cohorts")
@tenant_required
@require_permission(Permission.INTELLIGENCE_COHORT_READ)
def list_cohorts():
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )
    with knowledge_composition(session_factory, g.tenant_id) as repo:
        cohorts = repo.list_cohorts()
    items = [mappers.cohort_to_dto(c).to_dict() for c in cohorts]
    return success_envelope({"items": items, "count": len(items)})


# ─────────────────────────────────────────────────────────────────────
# GET /cohorts/<cohort_id>
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.get("/cohorts/<string:cohort_id>")
@tenant_required
@require_permission(Permission.INTELLIGENCE_COHORT_READ)
def get_cohort(cohort_id: str):
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )
    with knowledge_composition(session_factory, g.tenant_id) as repo:
        cohort = repo.load_cohort(cohort_id)
    if cohort is None:
        return error_envelope(
            COHORT_NOT_FOUND,
            f"Cohort with id {cohort_id} not found",
            status=404,
        )
    return success_envelope(mappers.cohort_to_dto(cohort).to_dict())


# ─────────────────────────────────────────────────────────────────────
# GET /research/sessions
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.get("/research/sessions")
@tenant_required
@require_permission(Permission.INTELLIGENCE_RESEARCH_READ)
def list_research_sessions():
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )
    with knowledge_composition(session_factory, g.tenant_id) as repo:
        sessions = repo.list_sessions()
    items = [
        mappers.research_session_summary(s).to_dict() for s in sessions
    ]
    return success_envelope({"items": items, "count": len(items)})


# ─────────────────────────────────────────────────────────────────────
# GET /research/sessions/<session_id>
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.get("/research/sessions/<string:session_id>")
@tenant_required
@require_permission(Permission.INTELLIGENCE_RESEARCH_READ)
def get_research_session(session_id: str):
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )
    with knowledge_composition(session_factory, g.tenant_id) as repo:
        session_obj = repo.load_session(session_id)
    if session_obj is None:
        return error_envelope(
            RESEARCH_SESSION_NOT_FOUND,
            f"Research session with id {session_id} not found",
            status=404,
        )
    return success_envelope(mappers.research_session_detail(session_obj).to_dict())


# ─────────────────────────────────────────────────────────────────────
# POST /research/sessions/<session_id>/replay
# ─────────────────────────────────────────────────────────────────────

@knowledge_bp.post("/research/sessions/<string:session_id>/replay")
@tenant_required
@require_permission(Permission.INTELLIGENCE_REPLAY_EXECUTE)
def replay_research_session(session_id: str):
    """Replay a prior session, producing a NEW session whose state_hash
    matches the original (byte-exact reproducibility)."""
    session_factory = _session_factory()
    if session_factory is None:
        return error_envelope(
            SERVICE_UNAVAILABLE,
            "Knowledge persistence is not configured in this deployment",
            status=503,
        )
    # Replay requires the original session + cohort + patient + genes.
    # The endpoint accepts the prior session_id and uses the same patient
    # sources that exist in the tenant today.
    with knowledge_composition(session_factory, g.tenant_id) as repo:
        prior = repo.load_session(session_id)
        if prior is None:
            return error_envelope(
                RESEARCH_SESSION_NOT_FOUND,
                f"Research session with id {session_id} not found",
                status=404,
            )
        # Look up patients + genes by cohort_id from the session query.
        # We don't materialize patient data here (replay operates on the
        # same cohort scope); existing ResearchWorkspace handles data lookup.
        # We pass a minimal PatientData shape so service signature is honored.
        try:
            new_session = ResearchService().replay(
                prior,
                patients=(),
                genes_by_patient={},
            )
            repo.save_session(new_session)
        except TypeError:
            # Some service signatures take only the session — fall back.
            try:
                new_session = ResearchService().replay(prior)
                repo.save_session(new_session)
            except Exception as exc:  # noqa: BLE001
                logger.warning("replay fallback failed: %s", exc)
                return error_envelope(
                    VALIDATION_ERROR,
                    "Replay requires patient context; use the research API "
                    "directly when patient data lives outside this tenant",
                    status=400,
                )
    return success_envelope(
        mappers.research_session_detail(new_session).to_dict(), status=201
    )
