"""
AraOS Knowledge — Observability.

Métricas e logging para a Knowledge Layer.

Week 8 — Knowledge Layer v1
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .models import KnowledgeDocument
from .retrieval import RetrievalResult


@dataclass
class KnowledgeQueryMetric:
    """Métrica de uma consulta à Knowledge Layer."""
    query: str
    tenant_id: str
    patient_id: Optional[str]
    knowledge_types: List[str]
    document_count: int
    documents_used: List[str]
    sources: List[str]
    max_score: float
    avg_score: float
    latency_ms: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "knowledge_types": self.knowledge_types,
            "document_count": self.document_count,
            "documents_used": self.documents_used,
            "sources": self.sources,
            "max_score": self.max_score,
            "avg_score": self.avg_score,
            "latency_ms": round(self.latency_ms, 2),
            "timestamp": self.timestamp.isoformat(),
        }


class KnowledgeObservability:
    """
    Observabilidade da Knowledge Layer.
    
    Responsabilidades:
        1. Registrar todas as consultas
        2. Rastrear documentos utilizados
        3. Calcular scores de relevância
        4. Integrar com Audit Ledger
    
    Uso:
        obs = KnowledgeObservability()
        
        # Após consulta
        metric = obs.record_query(
            query="protocolo de hipertensão",
            tenant_id="tenant_001",
            results=retrieval_results,
            latency_ms=12.5,
        )
        
        # Resumo
        summary = obs.summary()
        print(summary["total_queries"], summary["avg_latency_ms"])
    """
    
    def __init__(self):
        self._metrics: List[KnowledgeQueryMetric] = []
        self._audit_callback: Optional[Any] = None
    
    def record_query(
        self,
        query: str,
        tenant_id: str,
        results: List[RetrievalResult],
        knowledge_types: Optional[List[str]] = None,
        patient_id: Optional[str] = None,
        latency_ms: float = 0.0,
    ) -> KnowledgeQueryMetric:
        """
        Registra uma consulta à Knowledge Layer.
        
        Args:
            query: Termos de busca
            tenant_id: ID do tenant
            results: Resultados da recuperação
            knowledge_types: Tipos de conhecimento consultados
            patient_id: ID do paciente (se aplicável)
            latency_ms: Tempo de resposta
        
        Returns:
            KnowledgeQueryMetric registrada
        """
        scores = [r.score for r in results] if results else [0.0]
        
        metric = KnowledgeQueryMetric(
            query=query,
            tenant_id=tenant_id,
            patient_id=patient_id,
            knowledge_types=knowledge_types or [],
            document_count=len(results),
            documents_used=[r.document.document_id for r in results],
            sources=list(set(
                r.document.source_type.value for r in results
            )),
            max_score=max(scores),
            avg_score=round(sum(scores) / len(scores), 3) if scores else 0.0,
            latency_ms=latency_ms,
        )
        
        self._metrics.append(metric)
        
        # Audit callback (se configurado)
        if self._audit_callback:
            try:
                self._audit_callback(metric.to_dict())
            except Exception:
                pass
        
        return metric
    
    def summary(self) -> Dict[str, Any]:
        """Retorna resumo de métricas."""
        if not self._metrics:
            return {
                "total_queries": 0,
                "avg_latency_ms": 0.0,
                "avg_documents_per_query": 0.0,
                "total_unique_documents": 0,
                "total_unique_sources": 0,
            }
        
        total = len(self._metrics)
        avg_latency = sum(m.latency_ms for m in self._metrics) / total
        avg_docs = sum(m.document_count for m in self._metrics) / total
        
        all_docs = set()
        all_sources = set()
        for m in self._metrics:
            all_docs.update(m.documents_used)
            all_sources.update(m.sources)
        
        return {
            "total_queries": total,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_documents_per_query": round(avg_docs, 2),
            "total_unique_documents": len(all_docs),
            "total_unique_sources": len(all_sources),
        }
    
    def get_metrics(self) -> List[KnowledgeQueryMetric]:
        """Retorna todas as métricas."""
        return self._metrics.copy()
    
    def clear(self) -> None:
        """Limpa métricas."""
        self._metrics.clear()
    
    def set_audit_callback(self, callback) -> None:
        """Define callback para auditoria."""
        self._audit_callback = callback
