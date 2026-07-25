"""
Sprint 4.4 — Research Workspace.

Testes cobrindo:
    - 4 AnalysisTypes (CORRELATIONS, HYPOTHESES, GRAPH, STATS).
    - ResearchQuery → ResearchSession reproduzível.
    - Replay byte-idêntico (state_hash, result_json).
    - URN canônico (urn:araos:research:{tenant}:{session}).
"""

from __future__ import annotations

import pytest

from araos.clinical.knowledge.domain.research import (
    AnalysisType,
    ResearchQuery,
    ResearchSession,
    ResearchWorkspace,
)


class TestAnalysisType:
    """4 AnalysisTypes canônicos."""

    @pytest.mark.parametrize("t", list(AnalysisType))
    def test_all_types(self, t):
        assert t.value in {"correlations", "hypotheses", "graph", "stats"}


class TestResearchWorkspace:
    """Contract tests."""

    def test_execute_returns_session(self):
        # Act
        ws = ResearchWorkspace()
        query = ResearchQuery(
            query_id="q1",
            cohort_id="cohort_test_1",
            analysis_type=AnalysisType.STATS,
            params={},
            version=1,
        )
        session = ws.execute(query, patients=(), genes_by_patient={})
        # Assert
        assert isinstance(session, ResearchSession)
        assert session.state_hash

    def test_urn_format(self):
        # Act
        ws = ResearchWorkspace()
        query = ResearchQuery(
            query_id="q1",
            cohort_id="cohort_test_1",
            analysis_type=AnalysisType.STATS,
            params={},
            version=1,
        )
        session = ws.execute(query, patients=(), genes_by_patient={})
        # Assert
        assert session.urn.startswith("urn:araos:research:")

    def test_replay_byte_equal(self):
        # Act
        ws = ResearchWorkspace()
        query = ResearchQuery(
            query_id="q1",
            cohort_id="cohort_test_1",
            analysis_type=AnalysisType.STATS,
            params={},
            version=1,
        )
        s1 = ws.execute(query, patients=(), genes_by_patient={})
        s2 = ws.replay(s1.query, patients=(), genes_by_patient={})
        # Assert
        assert s1.state_hash == s2.state_hash
        assert s1.result_json == s2.result_json

    def test_replay_three_runs_same_hash(self):
        # Act
        ws = ResearchWorkspace()
        query = ResearchQuery(
            query_id="q1",
            cohort_id="cohort_test_1",
            analysis_type=AnalysisType.STATS,
            params={},
            version=1,
        )
        s1 = ws.execute(query, patients=(), genes_by_patient={})
        s2 = ws.replay(s1.query, patients=(), genes_by_patient={})
        s3 = ws.replay(s1.query, patients=(), genes_by_patient={})
        # Assert
        hashes = [s.state_hash for s in (s1, s2, s3)]
        assert hashes[0] == hashes[1] == hashes[2]

    def test_session_immutable(self):
        # Act
        ws = ResearchWorkspace()
        query = ResearchQuery(
            query_id="q1",
            cohort_id="cohort_test_1",
            analysis_type=AnalysisType.STATS,
            params={},
            version=1,
        )
        s = ws.execute(query, patients=(), genes_by_patient={})
        # Assert — frozen
        with pytest.raises((AttributeError, Exception)):
            s.state_hash = "x"
