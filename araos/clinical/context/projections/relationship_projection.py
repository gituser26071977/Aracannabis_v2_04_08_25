"""
RelationshipProjection — projeção read-side do grafo de relacionamentos.

Permite queries eficientes:
    - "quais contextos são influenciados por X?"
    - "qual rede forma este contexto?"
    - "pagerank topológico básico"

Mantém a tabela materializada `REDACTED`,
idempotente e rebuildable.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import text
from sqlalchemy.orm import Session

from .handlers import (
    handle_clinical_context_linked,
    handle_clinical_context_unlinked,
)


class RelationshipProjection:
    """Projeção read-side do grafo ClinicalContext."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def apply(self, event: Dict[str, Any]) -> bool:
        event_type = event.get("event_type")
        if event_type not in (
            "CLINICAL_CONTEXT_LINKED",
            "CLINICAL_CONTEXT_UNLINKED",
        ):
            return False
        with self._session_factory() as session:
            if event_type == "CLINICAL_CONTEXT_LINKED":
                handle_clinical_context_linked(session, event)
            else:
                handle_clinical_context_unlinked(session, event)
            session.commit()
        return True

    # ─── Read ──────────────────────────────────────────────────────

    def list_for_context(
        self,
        tenant_id: str,
        context_id: str,
    ) -> List[Dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                text(
                    "SELECT relationship_id, source_context_id, target_context_id, "
                    "relationship_type, confidence, created_at, created_by "
                    "FROM clinical_context_relationships "
                    "WHERE tenant_id = :tid AND "
                    "(source_context_id = :cid OR target_context_id = :cid) "
                    "ORDER BY created_at ASC"
                ),
                {"tid": tenant_id, "cid": context_id},
            ).all()
            return [dict(r._mapping) for r in rows]

    def neighbors(
        self,
        tenant_id: str,
        context_id: str,
        depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """BFS até `depth` hops a partir de context_id."""
        adjacency = self._build_adjacency(tenant_id)
        visited: Set[str] = set()
        queue = deque([(context_id, 0)])
        result: List[Dict[str, Any]] = []
        while queue:
            node, d = queue.popleft()
            if node in visited or d > depth:
                continue
            visited.add(node)
            if node != context_id:
                result.append({
                    "context_id": node,
                    "depth": d,
                    "n_edges": len(adjacency.get(node, [])),
                })
            for nb in adjacency.get(node, []):
                if nb not in visited:
                    queue.append((nb, d + 1))
        return result

    def _build_adjacency(self, tenant_id: str) -> Dict[str, Set[str]]:
        adj: Dict[str, Set[str]] = defaultdict(set)
        with self._session_factory() as session:
            rows = session.execute(
                text(
                    "SELECT source_context_id, target_context_id "
                    "FROM clinical_context_relationships WHERE tenant_id = :tid"
                ),
                {"tid": tenant_id},
            ).all()
            for r in rows:
                s = r[0]
                t = r[1]
                adj[s].add(t)
                adj[t].add(s)
        return adj

    # ─── Aggregations ──────────────────────────────────────────────

    def top_connected(self, tenant_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        with self._session_factory() as session:
            rows = session.execute(
                text(
                    "SELECT source_context_id AS cid, COUNT(*) AS out_degree "
                    "FROM clinical_context_relationships "
                    "WHERE tenant_id = :tid "
                    "GROUP BY source_context_id "
                    "ORDER BY out_degree DESC LIMIT :lim"
                ),
                {"tid": tenant_id, "lim": limit},
            ).all()
            return [{"context_id": r[0], "out_degree": int(r[1])} for r in rows]
