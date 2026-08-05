"""
araos.clinical.genome.infrastructure.serialization — Serialização canônica.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from .canonical_json import (
    compute_state_hash,
    event_to_canonical_json,
    events_to_canonical_json,
    gene_from_canonical_json,
    gene_to_canonical_json,
    serialize_clinical_expression,
    serialize_clinical_gene,
    serialize_confidence,
    serialize_context_dependency,
    serialize_domain_event,
    serialize_evidence,
    serialize_history_entry,
    serialize_hypothesis,
    serialize_metadata_record,
    serialize_observed_value,
    serialize_relationship,
    serialize_snapshot,
    serialize_trajectory_point,
)

__all__ = [
    "compute_state_hash",
    "event_to_canonical_json",
    "events_to_canonical_json",
    "gene_from_canonical_json",
    "gene_to_canonical_json",
    "serialize_clinical_expression",
    "serialize_clinical_gene",
    "serialize_confidence",
    "serialize_context_dependency",
    "serialize_domain_event",
    "serialize_evidence",
    "serialize_history_entry",
    "serialize_hypothesis",
    "serialize_metadata_record",
    "serialize_observed_value",
    "serialize_relationship",
    "serialize_snapshot",
    "serialize_trajectory_point",
]