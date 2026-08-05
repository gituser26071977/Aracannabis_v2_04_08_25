"""
Sprint 4.4.5 — Coverage Hardening: Research all 4 AnalysisTypes.

Cobre:
    - ResearchWorkspace.execute com AnalysisType.CORRELATIONS
    - ResearchWorkspace.execute com AnalysisType.HYPOTHESES
    - ResearchWorkspace.execute com AnalysisType.GRAPH
    - ResearchWorkspace.execute com AnalysisType.STATS
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from araos.clinical.knowledge.domain.clinical_genome import build_clinical_genome
from araos.clinical.knowledge.domain.cohort import CohortBuilder, PatientData
from araos.clinical.knowledge.domain.research import (
    AnalysisType,
    ResearchQuery,
    ResearchWorkspace,
)
from araos.clinical.timeline.domain.window import TimeWindow

from tests.sprint_4_4_5.conftest import _build_gene_with_trajectory


UTC = timezone.utc


def _setup_session(analysis_type: AnalysisType):
    """Helper: cria cohort + query + workspace para testar cada AnalysisType."""
    patient = PatientData(patient_id="p1", tenant_id="t1", age=14, sex="F")
    cohort = CohortBuilder().evaluate(
        patients=[patient],
        tenant_id="t1",
        name="r",
        criteria=(),
    )
    query = ResearchQuery(
        query_id=f"q_{analysis_type.value}",
        cohort_id=cohort.cohort_id,
        analysis_type=analysis_type,
        params={},
    )
    genes = (
        _build_gene_with_trajectory(
            tenant_id="t1", patient_id="p1", gene_id="GENE_SLEEP",
            values=((4.0, 0.4, 0), (5.0, 0.5, 30), (6.0, 0.6, 60)),
        ),
        _build_gene_with_trajectory(
            tenant_id="t1", patient_id="p1", gene_id="GENE_ANXIETY",
            values=((7.0, 0.7, 0), (5.5, 0.55, 30), (4.0, 0.4, 60)),
        ),
    )
    return patient, cohort, query, genes


class TestAllAnalysisTypes:
    """Cada um dos 4 AnalysisTypes deve ser executável."""

    @pytest.mark.parametrize("analysis_type", list(AnalysisType))
    def test_each_analysis_type_executes(self, analysis_type):
        patient, _, query, genes = _setup_session(analysis_type)
        workspace = ResearchWorkspace()
        session = workspace.execute(
            query,
            patients=[patient],
            genes_by_patient={"p1": list(genes)},
        )
        assert session is not None
        assert session.query.analysis_type == analysis_type
        assert len(session.state_hash) == 64
        assert session.result_json  # Tem result_json (string canônico)

    def REDACTED(self):
        patient, _, query, genes = _setup_session(AnalysisType.CORRELATIONS)
        session = ResearchWorkspace().execute(
            query, patients=[patient], genes_by_patient={"p1": list(genes)},
        )
        # result_json contém "correlations" para este AnalysisType
        assert "correlations" in session.result_json

    def REDACTED(self):
        patient, _, query, genes = _setup_session(AnalysisType.HYPOTHESES)
        session = ResearchWorkspace().execute(
            query, patients=[patient], genes_by_patient={"p1": list(genes)},
        )
        assert "hypotheses" in session.result_json

    def test_graph_analysis_returns_graph(self):
        patient, _, query, genes = _setup_session(AnalysisType.GRAPH)
        session = ResearchWorkspace().execute(
            query, patients=[patient], genes_by_patient={"p1": list(genes)},
        )
        assert "graph" in session.result_json

    def test_stats_analysis_returns_stats(self):
        patient, _, query, genes = _setup_session(AnalysisType.STATS)
        session = ResearchWorkspace().execute(
            query, patients=[patient], genes_by_patient={"p1": list(genes)},
        )
        assert "stats" in session.result_json

    def REDACTED(self):
        """Mesmo input → mesmo state_hash (replay determinístico)."""
        patient, _, query, genes = _setup_session(AnalysisType.STATS)
        workspace = ResearchWorkspace()
        s1 = workspace.execute(
            query, patients=[patient], genes_by_patient={"p1": list(genes)},
        )
        s2 = workspace.execute(
            query, patients=[patient], genes_by_patient={"p1": list(genes)},
        )
        assert s1.state_hash == s2.state_hash


class TestResearchSessionStructure:
    """Estrutura de ResearchSession."""

    def REDACTED(self):
        from araos.clinical.knowledge.domain.research import ResearchSession
        from dataclasses import fields
        field_names = {f.name for f in fields(ResearchSession)}
        assert "session_id" in field_names
        assert "query" in field_names  # Encapsula ResearchQuery
        assert "version" in field_names
        assert "started_at" in field_names
        assert "completed_at" in field_names
        assert "result_json" in field_names
        assert "state_hash" in field_names
        assert "reproducible" in field_names
        assert "explanation" in field_names

    def REDACTED(self):
        """state_hash = SHA-256 hex 64 chars."""
        patient, _, query, genes = _setup_session(AnalysisType.STATS)
        session = ResearchWorkspace().execute(
            query, patients=[patient], genes_by_patient={"p1": list(genes)},
        )
        assert len(session.state_hash) == 64
        # hex válido
        int(session.state_hash, 16)