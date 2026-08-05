"""
Fábricas de Domain Events específicos.

Cada fábrica constrói um DomainEvent com ``event_type`` canônico
e ``payload`` específico.

Reference Implementation — Sprint 4.3 Phase 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping

from .domain_event import (
    DomainEvent,
    GENE_CREATED,
    EXPRESSION_OBSERVED,
    EXPRESSION_REPLACED,
    EXPRESSION_UNKNOWN_RECORDED,
    EXPRESSION_UNAVAILABLE_RECORDED,
    EXPRESSION_DERIVED_COMPUTED,
    HYPOTHESIS_ADDED,
    HYPOTHESIS_DEACTIVATED,
    RELATIONSHIP_ADDED,
    RELATIONSHIP_DEACTIVATED,
    CONTEXT_ADDED,
    CONTEXT_REMOVED,
    EVIDENCE_RECORDED,
    METADATA_RECORDED,
    SNAPSHOT_TAKEN,
    GENE_ARCHIVED,
)


def make_gene_created(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    registry_version: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    """Emitted quando um novo Clinical Gene é criado."""
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=GENE_CREATED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({
            "registry_version": registry_version,
        }),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_expression_observed(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    expression_payload: Mapping[str, Any],
    explanation_reference: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    """Emitted quando uma nova Expression substitui a anterior (incluindo criação)."""
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=EXPRESSION_OBSERVED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({
            "expression": dict(expression_payload),
            "explanation_reference": explanation_reference,
            "is_initial": True,
        }),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_expression_replaced(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    expression_payload: Mapping[str, Any],
    explanation_reference: str,
    prior_expression_id_marker: str | None = None,
    correlation_id: str | None = None,
) -> DomainEvent:
    """Emitted quando uma Expression existente é substituída (AS-002 §6.5)."""
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=EXPRESSION_REPLACED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({
            "expression": dict(expression_payload),
            "explanation_reference": explanation_reference,
            "prior_marker": prior_expression_id_marker or "",
        }),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_expression_unknown_recorded(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    explanation_reference: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    """Emitted quando uma Expression entra em Unknown State (§3.14)."""
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=EXPRESSION_UNKNOWN_RECORDED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({
            "explanation_reference": explanation_reference,
        }),
        origin=origin,
        correlation_id=correlation_id,
    )


def REDACTED(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    explanation_reference: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=EXPRESSION_UNAVAILABLE_RECORDED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({
            "explanation_reference": explanation_reference,
        }),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_expression_derived_computed(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    expression_payload: Mapping[str, Any],
    explanation_reference: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    """Emitted quando uma Derived Expression é computada (§3.16)."""
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=EXPRESSION_DERIVED_COMPUTED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({
            "expression": dict(expression_payload),
            "explanation_reference": explanation_reference,
        }),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_hypothesis_added(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    hypothesis_payload: Mapping[str, Any],
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=HYPOTHESIS_ADDED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType(dict(hypothesis_payload)),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_hypothesis_deactivated(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    hypothesis_id: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=HYPOTHESIS_DEACTIVATED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({"hypothesis_id": hypothesis_id}),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_relationship_added(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    relationship_payload: Mapping[str, Any],
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=RELATIONSHIP_ADDED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType(dict(relationship_payload)),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_relationship_deactivated(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    target_gene_id: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=RELATIONSHIP_DEACTIVATED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({"target_gene_id": target_gene_id}),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_context_added(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    context_payload: Mapping[str, Any],
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=CONTEXT_ADDED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType(dict(context_payload)),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_context_removed(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    context_id: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=CONTEXT_REMOVED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({"context_id": context_id}),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_evidence_recorded(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    evidence_payload: Mapping[str, Any],
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=EVIDENCE_RECORDED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType(dict(evidence_payload)),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_metadata_recorded(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    metadata_payload: Mapping[str, Any],
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=METADATA_RECORDED,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType(dict(metadata_payload)),
        origin=origin,
        correlation_id=correlation_id,
    )


def make_snapshot_taken(
    *,
    tenant_id: str,
    patient_id: str,
    gene_id: str,
    sequence: int,
    valid_time: datetime,
    origin: str,
    snapshot_id: str,
    state_hash: str,
    correlation_id: str | None = None,
) -> DomainEvent:
    if valid_time.tzinfo is None:
        raise ValueError("valid_time deve ser timezone-aware (UTC)")
    return DomainEvent(
        event_id=DomainEvent.new_event_id(),
        event_type=SNAPSHOT_TAKEN,
        tenant_id=tenant_id,
        patient_id=patient_id,
        gene_id=gene_id,
        sequence=sequence,
        valid_time=valid_time,
        transaction_time=datetime.now(timezone.utc),
        payload=MappingProxyType({
            "snapshot_id": snapshot_id,
            "state_hash": state_hash,
        }),
        origin=origin,
        correlation_id=correlation_id,
    )
