"""
araos.clinical.genome.domain.aggregate — Aggregate Root + componentes.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from .clinical_gene import ClinicalGene, GeneStatus, build_urn
from .clinical_gene_factory import create_gene
from .context_dependency import ContextDependency
from .evidence import EvidenceReference
from .history import History, HistoryEntry
from .hypothesis import Hypothesis
from .metadata_record import MetadataRecord
from .relationship import Relationship
from .snapshot import Snapshot
from .snapshot_policy import SnapshotPolicy
from .trajectory import Trajectory, TrajectoryPoint

__all__ = [
    "ClinicalGene",
    "GeneStatus",
    "build_urn",
    "create_gene",
    "ContextDependency",
    "EvidenceReference",
    "History",
    "HistoryEntry",
    "Hypothesis",
    "MetadataRecord",
    "Relationship",
    "Snapshot",
    "SnapshotPolicy",
    "Trajectory",
    "TrajectoryPoint",
]