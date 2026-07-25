"""
ClinicalContextService — CRUD + state transitions + relationships.

Sprint 4.2 — ADR-0003. Application layer puro (sem HTTP).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.context_origin import ContextOrigin
from araos.clinical.context.domain.context_relationship import (
    ContextRelationship,
    RelationshipType,
)
from araos.clinical.context.domain.context_status import ContextStatus
from araos.clinical.context.domain.context_type import ContextType


_logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_context_id() -> str:
    return f"ctx_{uuid.uuid4().hex[:16]}"


def _new_relationship_id() -> str:
    return f"rel_{uuid.uuid4().hex[:16]}"


class _EventPublisher(Protocol):
    def publish(self, **kwargs: Any) -> str: ...


@dataclass(frozen=True)
class CreateContextCommand:
    tenant_id: str
    patient_id: str
    context_type: ContextType
    title: str
    start_date: datetime
    created_by: str
    description: str = ""
    reason: str = ""
    observations: Optional[List[str]] = None
    end_date: Optional[datetime] = None
    origin: ContextOrigin = ContextOrigin.MANUAL
    confidence_score: float = 1.0
    source_event_ids: Optional[List[str]] = None
    professionals: Optional[List[str]] = None
    suggestion_id: Optional[str] = None
    explanation_id: Optional[str] = None


class ClinicalContextService:
    """Service puro (sem I/O). Persistência via SQL impl."""

    def __init__(self, event_publisher: Optional[_EventPublisher] = None) -> None:
        self._publisher = event_publisher

    # ─── Create ────────────────────────────────────────────────────

    def create(self, cmd: CreateContextCommand) -> ClinicalContext:
        """Cria um ClinicalContext em estado Planned (ou Suggested se automatizado)."""
        if cmd.origin.is_automated and cmd.confidence_score >= 1.0:
            raise ValueError(
                f"origin={cmd.origin.value} requires confidence_score < 1.0"
            )
        status = (
            ContextStatus.SUGGESTED
            if cmd.origin.is_automated
            else ContextStatus.PLANNED
        )
        now = _utcnow()
        ctx = ClinicalContext(
            context_id=_new_context_id(),
            tenant_id=cmd.tenant_id,
            patient_id=cmd.patient_id,
            context_type=cmd.context_type,
            status=status,
            origin=cmd.origin,
            title=cmd.title,
            description=cmd.description,
            reason=cmd.reason,
            observations=list(cmd.observations or []),
            start_date=cmd.start_date,
            end_date=cmd.end_date,
            confidence_score=cmd.confidence_score,
            source_event_ids=list(cmd.source_event_ids or []),
            professionals=list(cmd.professionals or []),
            suggestion_id=cmd.suggestion_id,
            explanation_id=cmd.explanation_id,
            created_at=now,
            created_by=cmd.created_by,
            updated_at=now,
            aggregate_version=1,
        )
        self._publish_event(
            "CLINICAL_CONTEXT_CREATED",
            ctx,
            from_status=None,
        )
        return ctx

    def create_from_suggestion(
        self,
        suggestion: Any,    # ContextSuggestion (avoid circular import)
        tenant_id: str,
        patient_id: str,
        created_by: str,
        title_override: Optional[str] = None,
    ) -> ClinicalContext:
        cmd = CreateContextCommand(
            tenant_id=tenant_id,
            patient_id=patient_id,
            context_type=suggestion.context_type,
            title=title_override or suggestion.title,
            description=suggestion.description,
            reason=suggestion.reason,
            start_date=suggestion.suggested_window.start,
            end_date=suggestion.suggested_window.end,
            created_by=created_by,
            origin=ContextOrigin.RULE_ENGINE,
            confidence_score=suggestion.confidence,
            source_event_ids=list(suggestion.contributing_event_ids),
            suggestion_id=suggestion.suggestion_id,
        )
        return self.create(cmd)

    # ─── State transitions ─────────────────────────────────────────

    def activate(
        self,
        context: ClinicalContext,
        actor_id: str,
    ) -> ClinicalContext:
        if context.status not in (ContextStatus.PLANNED, ContextStatus.SUGGESTED):
            raise ValueError(
                f"cannot activate context with status={context.status.value}"
            )
        new_ctx = context.transition_to(
            ContextStatus.ACTIVE,
            actor_id=actor_id,
        )
        self._publish_event(
            "CLINICAL_CONTEXT_ACTIVATED", new_ctx,
            from_status=context.status.value,
        )
        return new_ctx

    def close(
        self,
        context: ClinicalContext,
        actor_id: str,
        new_status: ContextStatus,
        end_date: Optional[datetime] = None,
        summary: Optional[str] = None,
    ) -> ClinicalContext:
        if new_status not in (
            ContextStatus.COMPLETED,
            ContextStatus.CANCELLED,
            ContextStatus.ARCHIVED,
        ):
            raise ValueError(f"invalid close status: {new_status.value}")
        effective_end = end_date or _utcnow()
        new_ctx = context.transition_to(
            new_status,
            actor_id=actor_id,
            end_date=effective_end,
        )
        # Adiciona summary como observation
        if summary:
            obs = list(new_ctx.observations) + [f"closed: {summary}"]
            new_ctx = new_ctx._replace(observations=obs)
        self._publish_event(
            "CLINICAL_CONTEXT_CLOSED", new_ctx,
            from_status=context.status.value,
            new_status=new_status.value,
            summary=summary,
        )
        return new_ctx

    def reopen(
        self,
        context: ClinicalContext,
        actor_id: str,
        reason: str = "",
    ) -> ClinicalContext:
        if context.status != ContextStatus.COMPLETED:
            raise ValueError(
                f"can only reopen COMPLETED contexts, got {context.status.value}"
            )
        new_ctx = context.transition_to(
            ContextStatus.ACTIVE,
            actor_id=actor_id,
        )
        if reason:
            new_ctx = new_ctx._replace(reason=reason)
        self._publish_event(
            "CLINICAL_CONTEXT_REOPENED", new_ctx,
            from_status=context.status.value,
        )
        return new_ctx

    def reject(
        self,
        context: ClinicalContext,
        actor_id: str,
        reason: str,
    ) -> ClinicalContext:
        if context.status != ContextStatus.SUGGESTED:
            raise ValueError(
                f"can only reject SUGGESTED contexts, got {context.status.value}"
            )
        new_ctx = context.transition_to(
            ContextStatus.REJECTED,
            actor_id=actor_id,
            reason=reason,
        )
        self._publish_event(
            "CLINICAL_CONTEXT_REJECTED", new_ctx,
            reason=reason,
        )
        return new_ctx

    def confirm_suggestion(
        self,
        context: ClinicalContext,
        actor_id: str,
        confirmed_type: Optional[ContextType] = None,
    ) -> ClinicalContext:
        if context.status != ContextStatus.SUGGESTED:
            raise ValueError(
                f"can only confirm SUGGESTED contexts, got {context.status.value}"
            )
        new_ctx = self.activate(context, actor_id)
        if confirmed_type and confirmed_type != new_ctx.context_type:
            # Type override
            new_ctx = new_ctx._replace(context_type=confirmed_type)
            self._publish_event(
                "CLINICAL_CONTEXT_TYPE_CONFIRMED", new_ctx,
                suggested_type=context.context_type.value,
                confirmed_type=confirmed_type.value,
            )
        return new_ctx

    def update(
        self,
        context: ClinicalContext,
        actor_id: str,
        changes: Dict[str, Any],
    ) -> ClinicalContext:
        """Atualiza metadados (title, description, observations, professionals)."""
        if context.status.is_terminal:
            raise ValueError(
                f"cannot update context in terminal status {context.status.value}"
            )
        allowed = {"title", "description", "observations", "professionals",
                  "linked_event_ids", "linked_diagnosis_ids",
                  "linked_phenotype_ids", "linked_intervention_ids",
                  "linked_outcome_ids", "linked_assessment_ids"}
        clean = {k: v for k, v in changes.items() if k in allowed}
        if not clean:
            return context
        clean["updated_at"] = _utcnow()
        new_ctx = context._replace(**clean)
        self._publish_event(
            "CLINICAL_CONTEXT_UPDATED", new_ctx,
            actor_id=actor_id,
            changed_fields=list(clean.keys()),
        )
        return new_ctx

    # ─── Relationships ─────────────────────────────────────────────

    def link(
        self,
        tenant_id: str,
        source_context_id: str,
        target_context_id: str,
        relationship_type: RelationshipType,
        created_by: str,
        confidence: float = 1.0,
        evidence_event_ids: Optional[List[str]] = None,
        patient_id: str = "",
    ) -> ContextRelationship:
        rel = ContextRelationship(
            relationship_id=_new_relationship_id(),
            tenant_id=tenant_id,
            source_context_id=source_context_id,
            target_context_id=target_context_id,
            relationship_type=relationship_type,
            confidence=confidence,
            evidence_event_ids=list(evidence_event_ids or []),
            created_at=_utcnow(),
            created_by=created_by,
        )
        if self._publisher:
            self._publisher.publish(
                tenant_id=tenant_id,
                patient_id=patient_id,
                event_type="CLINICAL_CONTEXT_LINKED",
                event_datetime=_utcnow(),
                source_module="intelligence",
                payload={
                    "relationship_id": rel.relationship_id,
                    "source_context_id": source_context_id,
                    "target_context_id": target_context_id,
                    "relationship_type": relationship_type.value,
                    "confidence": confidence,
                    "evidence_event_ids": rel.evidence_event_ids,
                },
                created_by=created_by,
            )
        return rel

    def unlink(
        self,
        relationship: ContextRelationship,
        actor_id: str,
        patient_id: str = "",
    ) -> None:
        if self._publisher:
            self._publisher.publish(
                tenant_id=relationship.tenant_id,
                patient_id=patient_id,
                event_type="CLINICAL_CONTEXT_UNLINKED",
                event_datetime=_utcnow(),
                source_module="intelligence",
                payload={
                    "relationship_id": relationship.relationship_id,
                },
                created_by=actor_id,
            )

    # ─── Event publishing helper ───────────────────────────────────

    def _publish_event(
        self,
        event_type: str,
        ctx: ClinicalContext,
        actor_id: Optional[str] = None,
        from_status: Optional[str] = None,
        new_status: Optional[str] = None,
        summary: Optional[str] = None,
        reason: Optional[str] = None,
        changed_fields: Optional[List[str]] = None,
        suggested_type: Optional[str] = None,
        confirmed_type: Optional[str] = None,
    ) -> None:
        if self._publisher is None:
            return
        try:
            payload: Dict[str, Any] = {
                "context_id": ctx.context_id,
                "context_type": ctx.context_type.value,
                "status": ctx.status.value,
                "patient_id": ctx.patient_id,
                "tenant_id": ctx.tenant_id,
            }
            if actor_id:
                payload["actor_id"] = actor_id
            if from_status:
                payload["from_status"] = from_status
            if new_status:
                payload["new_status"] = new_status
            if summary:
                payload["summary"] = summary
            if reason:
                payload["reason"] = reason
            if changed_fields:
                payload["changed_fields"] = changed_fields
            if suggested_type:
                payload["suggested_type"] = suggested_type
            if confirmed_type:
                payload["confirmed_type"] = confirmed_type
            self._publisher.publish(
                tenant_id=ctx.tenant_id,
                patient_id=ctx.patient_id,
                event_type=event_type,
                event_datetime=_utcnow(),
                source_module="intelligence",
                payload=payload,
                created_by=actor_id or ctx.created_by,
            )
        except Exception as e:    # pragma: no cover
            _logger.warning(
                "context_event_publish_failed",
                extra={"event_type": event_type, "error": str(e)},
            )
