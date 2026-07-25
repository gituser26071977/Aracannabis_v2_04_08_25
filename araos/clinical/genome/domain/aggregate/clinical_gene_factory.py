"""
Factory para ClinicalGene — usado na criação inicial do AR.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .clinical_gene import ClinicalGene, GeneStatus
from .history import History
from .metadata_record import MetadataRecord
from .snapshot_policy import SnapshotPolicy
from .trajectory import Trajectory


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_gene(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    version: str,
    origin: str = "system",
    snapshot_policy: SnapshotPolicy | None = None,
    created_at: datetime | None = None,
) -> ClinicalGene:
    """Cria um novo ClinicalGene vazio (sem Expression)."""
    if not tenant_id:
        raise ValueError("tenant_id obrigatório")
    if not patient_id:
        raise ValueError("patient_id obrigatório")
    if not gene_id:
        raise ValueError("gene_id obrigatório")
    if not version:
        raise ValueError("version (SemVer) obrigatório")
    if created_at is None:
        created_at = _utcnow()
    if created_at.tzinfo is None:
        raise ValueError("created_at deve ser timezone-aware (UTC)")

    event_id = f"creation_{gene_id}"
    initial_metadata = (
        MetadataRecord(
            record_id=f"creation_record_{gene_id}",
            content={
                "kind": "created",
                "version": version,
                "origin": origin,
            },
            created_at=created_at,
            origin_event_id=event_id,
        ),
    )

    return ClinicalGene(
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        version=version,
        status=GeneStatus.ACTIVE,
        created_at=created_at,
        updated_at=created_at,
        trajectory=Trajectory(),
        history=History(),
        metadata=initial_metadata,
        snapshot_policy=snapshot_policy or SnapshotPolicy.never(),
        last_event_id=event_id,
        last_sequence=-1,
    )