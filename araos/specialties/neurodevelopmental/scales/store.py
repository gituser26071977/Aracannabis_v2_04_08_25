"""
AraOS Neurodevelopmental — Scale Response Store.

Camada de persistência das respostas de escalas. Mantém as respostas
brutas + scores calculados + interpretação em JSON polimórfico,
validado contra o `ScaleSpec.json_schema` da escala aplicada.

Princípios:
    - Append-only: nunca atualiza nem deleta respostas já gravadas.
    - Recalculável: scores são cache mas sempre deriváveis do `raw_responses`.
    - Tenant-isolated: toda query filtra por `tenant_id`.
    - Audit-friendly: aceita `actor_id` para registro de quem aplicou.

Persistência:
    Recebe um `Session` SQLAlchemy. Tabela `neuro_scale_responses`
    (definida em `db_models.py`). Não há migração automática — a tabela
    deve existir antes do uso.

Decisão de design: respostas múltiplas de uma mesma escala para o mesmo
paciente são permitidas (ex: PHQ-9 aplicado em D0, D30, D90). Cada
resposta é uma row independente — versionamento do score vem do timestamp,
não de "version" da row.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .base import RawResponses, ScaleInterpretation, ScaleResult
from .registry import ScaleRegistry
from .runner import ScaleRunner


@dataclass
class StoredScaleResponse:
    """
    Resposta de escala persistida (snapshot imutável).

    Não confundir com `ScaleResult`: este já tem `id`, `tenant_id`,
    `patient_id`, `applied_at`, `applied_by` que vêm do banco.
    """

    id: str
    tenant_id: str
    patient_id: str
    scale_code: str
    scale_version: str
    raw_responses: RawResponses
    computed_scores: Dict[str, float]
    interpretation: Dict[str, Any]
    metadata: Dict[str, Any]
    applied_at: datetime
    applied_by: Optional[str]
    source: str  # "ui", "ai", "voice", "import"
    status: str  # "draft", "final", "revoked"

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para JSON (consumível pela API)."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "patient_id": self.patient_id,
            "scale_code": self.scale_code,
            "scale_version": self.scale_version,
            "raw_responses": self.raw_responses,
            "computed_scores": self.computed_scores,
            "interpretation": self.interpretation,
            "metadata": self.metadata,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "applied_by": self.applied_by,
            "source": self.source,
            "status": self.status,
        }


class ScaleResponseStore:
    """
    Repositório de respostas de escalas.

    Args:
        db: Session SQLAlchemy.
        response_model: classe do modelo (default: `NeuroScaleResponseModel`).
            Pode ser injetada para testes.
    """

    def __init__(self, db: Session, response_model: Optional[type] = None) -> None:
        self.db = db
        if response_model is None:
            from ..db_models import NeuroScaleResponseModel

            self._model = NeuroScaleResponseModel
        else:
            self._model = response_model

    # ─── Escrita ────────────────────────────────────────────────────
    def save(
        self,
        tenant_id: str,
        patient_id: str,
        scale_code: str,
        raw_responses: RawResponses,
        applied_by: Optional[str] = None,
        source: str = "ui",
        status: str = "final",
        metadata: Optional[Dict[str, Any]] = None,
        validate: bool = True,
        scale_version: str = "latest",
    ) -> StoredScaleResponse:
        """
        Persiste uma resposta de escala após cálculo.

        Returns:
            StoredScaleResponse gravado (com id).
        """
        spec = ScaleRegistry.get(scale_code, version=scale_version)
        runner = ScaleRunner(spec)
        result: ScaleResult = runner.run(
            raw_responses=raw_responses,
            metadata=metadata or {},
            validate=validate,
        )

        # Converter ScaleInterpretation → dict (JSON column-ready)
        interpretation_serializable: Dict[str, Any] = {
            code: _interpretation_to_dict(interp)
            for code, interp in result.interpretation.items()
        }

        row = self._model(
            id=_new_uuid(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            scale_code=scale_code,
            scale_version=spec.version,
            raw_responses=raw_responses,
            computed_scores=result.scores,
            interpretation=interpretation_serializable,
            extra_metadata=result.metadata,
            applied_at=datetime.now(timezone.utc),
            applied_by=applied_by,
            source=source,
            status=status,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return _row_to_stored(row)

    # ─── Leitura ────────────────────────────────────────────────────
    def get(self, response_id: str, tenant_id: str) -> Optional[StoredScaleResponse]:
        """Busca resposta por id (tenant-scoped)."""
        row = (
            self.db.query(self._model)
            .filter(
                self._model.id == response_id,
                self._model.tenant_id == tenant_id,
            )
            .first()
        )
        return _row_to_stored(row) if row else None

    def list_for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        scale_code: Optional[str] = None,
        limit: int = 100,
    ) -> List[StoredScaleResponse]:
        """
        Lista respostas de um paciente (tenant-scoped).
        Ordenadas por `applied_at` descendente.
        """
        q = self.db.query(self._model).filter(
            self._model.tenant_id == tenant_id,
            self._model.patient_id == patient_id,
        )
        if scale_code:
            q = q.filter(self._model.scale_code == scale_code)
        rows = q.order_by(self._model.applied_at.desc()).limit(limit).all()
        return [_row_to_stored(r) for r in rows]

    def latest_for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        scale_code: str,
    ) -> Optional[StoredScaleResponse]:
        """Retorna a resposta mais recente de uma escala específica."""
        rows = self.list_for_patient(
            tenant_id=tenant_id,
            patient_id=patient_id,
            scale_code=scale_code,
            limit=1,
        )
        return rows[0] if rows else None

    def count_for_patient(
        self,
        tenant_id: str,
        patient_id: str,
        scale_code: Optional[str] = None,
    ) -> int:
        """Conta respostas de um paciente."""
        q = self.db.query(self._model).filter(
            self._model.tenant_id == tenant_id,
            self._model.patient_id == patient_id,
        )
        if scale_code:
            q = q.filter(self._model.scale_code == scale_code)
        return q.count()


# ─── Helpers internos ──────────────────────────────────────────────


def _new_uuid() -> str:
    import uuid

    return str(uuid.uuid4())


def _interpretation_to_dict(interp: ScaleInterpretation) -> Dict[str, Any]:
    """Converte ScaleInterpretation em dict serializável JSON."""
    return {
        "band": interp.band,
        "label_pt": interp.label_pt,
        "label_en": interp.label_en,
        "color": interp.color,
        "recommendation": interp.recommendation,
        "references": list(interp.references),
    }


def _row_to_stored(row: Any) -> StoredScaleResponse:
    """Converte row SQLAlchemy → StoredScaleResponse."""
    return StoredScaleResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        patient_id=row.patient_id,
        scale_code=row.scale_code,
        scale_version=row.scale_version,
        raw_responses=row.raw_responses or {},
        computed_scores=row.computed_scores or {},
        interpretation=row.interpretation or {},
        metadata=row.extra_metadata or {},
        applied_at=row.applied_at,
        applied_by=row.applied_by,
        source=row.source,
        status=row.status,
    )