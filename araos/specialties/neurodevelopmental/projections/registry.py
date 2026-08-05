"""
AraOS Neurodevelopmental — Registry Projection Engine.

Materializa o Registry (read model) a partir do Event Store.

Operações:
    apply(event)               — aplica 1 evento (idempotente)
    replay_all(tenant_id)      — wipe + replay desde genesis
    replay_from(tenant_id, N)  — replay incremental desde sequence N
    get_clinical_identity(...) — query no Registry

Garantias:
    1. Idempotência — checa `processed_events` antes de aplicar.
    2. Ordenação — sempre por sequence ASC (canônica, não event_datetime).
    3. Replay bit-identical — wipe + replay produz mesmo estado.
    4. Atomicidade — operação toda em 1 transação.

Convenção:
    - O Projection NÃO escreve no Event Store. Só lê.
    - Registry é descartável. Pode ser apagado e reconstruído a qualquer momento.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from araos.clinical.event_store import ClinicalEventStore
from araos.clinical.observability import (
    METRIC_DEAD_EVENTS,
    METRIC_PENDING_EVENTS,
    METRIC_PROCESSED_EVENTS,
    METRIC_PROJECTION_LAG,
    METRIC_PUBLISHED_EVENTS,
    METRIC_REPLAY_COUNT,
    METRIC_REPLAY_DURATION,
    get_logger,
    get_metrics,
)

from .db_models import (
    NeuroRegistryAssessmentModel,
    NeuroRegistryClinicalIdentityModel,
    NeuroRegistryDiagnosisModel,
    NeuroRegistryInterventionModel,
    NeuroRegistryOutcomeModel,
    NeuroRegistryPhenotypeModel,
    NeuroRegistryProcessedEventModel,
)
from .handlers import HANDLERS, get_handler

logger = get_logger("neurodevelopmental.projection")
_metrics = get_metrics()


def _to_datetime(value: Any) -> Optional[datetime]:
    """Normaliza event_datetime para datetime object (SQLite-friendly)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


class REDACTED:
    """
    Engine de projeção do Neurodevelopmental Registry.

    Args:
        event_store: ClinicalEventStore (InMemory ou SqlAlchemy).
        session_factory: SQLAlchemy sessionmaker.
    """

    def __init__(
        self,
        event_store: ClinicalEventStore,
        session_factory: sessionmaker[Session],
    ) -> None:
        self._event_store = event_store
        self._session_factory = session_factory

    # ─── Single-event apply (idempotent) ────────────────────────────────

    def apply(self, event: Dict[str, Any]) -> bool:
        """
        Aplica 1 evento ao Registry. Idempotente.

        Returns:
            True se evento foi aplicado, False se já havia sido processado.
        """
        # Eventos do store usam 'id' (não 'event_id') — normalizamos aqui.
        event_id = event.get("id") or event.get("event_id")
        if not event_id:
            raise ValueError("Event must have id/event_id")

        handler = get_handler(event["event_type"])
        if handler is None:
            # Evento desconhecido para a projection — não é erro,
            # apenas não há handler (ex.: evento cross-specialty).
            logger.debug(
                "dead_event_no_handler",
                extra={
                    "event_type": event["event_type"],
                    "event_id": event_id,
                },
            )
            _metrics.counter_inc(METRIC_DEAD_EVENTS)
            return False

        with self._session_factory() as session:
            # Idempotência: checa se já processado
            existing = session.get(NeuroRegistryProcessedEventModel, event_id)
            if existing is not None:
                logger.debug(
                    "event_already_processed",
                    extra={"event_id": event_id, "event_type": event["event_type"]},
                )
                return False

            # Aplica handler
            handler(session, event)

            # Marca como processado
            processed = NeuroRegistryProcessedEventModel(
                event_id=event_id,
                tenant_id=event["tenant_id"],
                patient_id=event.get("patient_id", ""),
                event_type=event["event_type"],
                aggregate_type=event.get("aggregate_type"),
                aggregate_id=event.get("aggregate_id"),
                sequence=event["sequence"],
                event_datetime=_to_datetime(event.get("event_datetime")),
            )
            session.add(processed)
            session.commit()

            # Métricas
            _metrics.counter_inc(METRIC_PROCESSED_EVENTS)
            self._update_projection_lag()

            logger.info(
                "event_applied",
                extra={
                    "event_id": event_id,
                    "event_type": event["event_type"],
                    "aggregate_type": event.get("aggregate_type"),
                    "aggregate_id": event.get("aggregate_id"),
                    "tenant_id": event["tenant_id"],
                    "sequence": event.get("sequence"),
                },
            )
            return True

    # ─── Bulk apply (for replay) ────────────────────────────────────────

    def apply_batch(self, events: List[Dict[str, Any]]) -> int:
        """
        Aplica lista de eventos em ordem de sequence ASC.
        Idempotente — eventos já processados são pulados.

        Returns:
            Número de eventos efetivamente aplicados.
        """
        # Garante ordenação canônica por sequence
        sorted_events = sorted(events, key=lambda e: e["sequence"])
        applied_count = 0
        with self._session_factory() as session:
            try:
                for event in sorted_events:
                    event_id = event.get("id") or event.get("event_id")
                    if not event_id:
                        continue
                    existing = session.get(NeuroRegistryProcessedEventModel, event_id)
                    if existing is not None:
                        continue
                    handler = get_handler(event["event_type"])
                    if handler is None:
                        _metrics.counter_inc(METRIC_DEAD_EVENTS)
                        continue
                    handler(session, event)
                    processed = NeuroRegistryProcessedEventModel(
                        event_id=event_id,
                        tenant_id=event["tenant_id"],
                        patient_id=event.get("patient_id", ""),
                        event_type=event["event_type"],
                        aggregate_type=event.get("aggregate_type"),
                        aggregate_id=event.get("aggregate_id"),
                        sequence=event["sequence"],
                        event_datetime=_to_datetime(event.get("event_datetime")),
                    )
                    session.add(processed)
                    applied_count += 1
                    _metrics.counter_inc(METRIC_PROCESSED_EVENTS)
                session.commit()
                self._update_projection_lag()
            except Exception:
                session.rollback()
                raise
        return applied_count

    # ─── Observability helpers ──────────────────────────────────────────

    def _update_projection_lag(self) -> None:
        """
        Atualiza métricas de lag (published - processed).

        Lag é aproximado: conta eventos no store vs eventos processados.
        Em produção, usar source-of-truth do Event Store para `published`.
        """
        try:
            # Conta processados (todas as tabelas processed_events somam)
            total_processed = 0
            with self._session_factory() as session:
                total_processed = session.query(
                    NeuroRegistryProcessedEventModel
                ).count()

            # Estimativa: eventos no store (cross-tenant)
            store_count = len(getattr(self._event_store, "_events", []))

            _metrics.gauge_set(METRIC_PROCESSED_EVENTS, float(total_processed))
            lag = max(0, store_count - total_processed)
            _metrics.gauge_set(METRIC_PROJECTION_LAG, float(lag))
            _metrics.gauge_set(METRIC_PENDING_EVENTS, float(lag))
        except Exception:
            # Métricas não devem quebrar o flow principal
            pass

    # ─── Replay operations ──────────────────────────────────────────────

    def replay_all(self, tenant_id: str) -> int:
        """
        Wipe Registry + replay desde genesis.

        DESTRUCTIVE — apaga todas as tabelas projection do tenant.
        Re-aplica todos os eventos do Event Store na ordem canônica.

        Returns:
            Número de eventos aplicados.
        """
        with _metrics.timer(METRIC_REPLAY_DURATION):
            _metrics.counter_inc(METRIC_REPLAY_COUNT)
            logger.info(
                "replay_all_started",
                extra={"tenant_id": tenant_id},
            )
            with self._session_factory() as session:
                # Wipe — apaga tabelas do tenant
                for model in (
                    NeuroRegistryDiagnosisModel,
                    NeuroRegistryPhenotypeModel,
                    NeuroRegistryAssessmentModel,
                    NeuroRegistryInterventionModel,
                    NeuroRegistryOutcomeModel,
                    NeuroRegistryClinicalIdentityModel,
                    NeuroRegistryProcessedEventModel,
                ):
                    stmt = delete(model).where(model.tenant_id == tenant_id)
                    session.execute(stmt)
                session.commit()

            # Replay todos os eventos do tenant
            all_events = self._event_store.query(tenant_id, order_by="sequence ASC")
            applied = self.apply_batch(all_events)

            logger.info(
                "replay_all_completed",
                extra={
                    "tenant_id": tenant_id,
                    "events_applied": applied,
                },
            )
            return applied

    def replay_from(
        self,
        tenant_id: str,
        since_sequence: int,
    ) -> int:
        """
        Replay incremental desde `since_sequence` (exclusive).

        Aplica eventos com sequence > since_sequence.
        Idempotente — eventos já processados são pulados.

        Returns:
            Número de eventos aplicados.
        """
        all_events = self._event_store.query(
            tenant_id, order_by="sequence ASC"
        )
        new_events = [e for e in all_events if e["sequence"] > since_sequence]
        return self.apply_batch(new_events)

    # ─── Read operations ────────────────────────────────────────────────

    def get_clinical_identity(
        self, tenant_id: str, identity_id: str
    ) -> Optional[NeuroRegistryClinicalIdentityModel]:
        with self._session_factory() as session:
            stmt = select(NeuroRegistryClinicalIdentityModel).where(
                NeuroRegistryClinicalIdentityModel.tenant_id == tenant_id,
                NeuroRegistryClinicalIdentityModel.id == identity_id,
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_clinical_identity_by_patient(
        self, tenant_id: str, patient_id: str
    ) -> Optional[NeuroRegistryClinicalIdentityModel]:
        with self._session_factory() as session:
            stmt = select(NeuroRegistryClinicalIdentityModel).where(
                NeuroRegistryClinicalIdentityModel.tenant_id == tenant_id,
                NeuroRegistryClinicalIdentityModel.patient_id == patient_id,
            )
            return session.execute(stmt).scalar_one_or_none()

    def list_diagnoses(
        self, tenant_id: str, identity_id: str
    ) -> List[NeuroRegistryDiagnosisModel]:
        with self._session_factory() as session:
            stmt = (
                select(NeuroRegistryDiagnosisModel)
                .where(
                    NeuroRegistryDiagnosisModel.tenant_id == tenant_id,
                    NeuroRegistryDiagnosisModel.identity_id == identity_id,
                )
                .order_by(NeuroRegistryDiagnosisModel.hypothesised_at)
            )
            return list(session.execute(stmt).scalars())

    def list_phenotypes(
        self, tenant_id: str, identity_id: str
    ) -> List[NeuroRegistryPhenotypeModel]:
        with self._session_factory() as session:
            stmt = (
                select(NeuroRegistryPhenotypeModel)
                .where(
                    NeuroRegistryPhenotypeModel.tenant_id == tenant_id,
                    NeuroRegistryPhenotypeModel.identity_id == identity_id,
                )
                .order_by(NeuroRegistryPhenotypeModel.observed_at)
            )
            return list(session.execute(stmt).scalars())

    def list_assessments(
        self, tenant_id: str, identity_id: str
    ) -> List[NeuroRegistryAssessmentModel]:
        with self._session_factory() as session:
            stmt = (
                select(NeuroRegistryAssessmentModel)
                .where(
                    NeuroRegistryAssessmentModel.tenant_id == tenant_id,
                    NeuroRegistryAssessmentModel.identity_id == identity_id,
                )
                .order_by(NeuroRegistryAssessmentModel.applied_at)
            )
            return list(session.execute(stmt).scalars())

    def list_interventions(
        self, tenant_id: str, identity_id: str
    ) -> List[NeuroRegistryInterventionModel]:
        with self._session_factory() as session:
            stmt = (
                select(NeuroRegistryInterventionModel)
                .where(
                    NeuroRegistryInterventionModel.tenant_id == tenant_id,
                    NeuroRegistryInterventionModel.identity_id == identity_id,
                )
                .order_by(NeuroRegistryInterventionModel.start_date)
            )
            return list(session.execute(stmt).scalars())

    def list_outcomes(
        self, tenant_id: str, identity_id: str
    ) -> List[NeuroRegistryOutcomeModel]:
        with self._session_factory() as session:
            stmt = (
                select(NeuroRegistryOutcomeModel)
                .where(
                    NeuroRegistryOutcomeModel.tenant_id == tenant_id,
                    NeuroRegistryOutcomeModel.identity_id == identity_id,
                )
                .order_by(NeuroRegistryOutcomeModel.observed_at)
            )
            return list(session.execute(stmt).scalars())

    def get_processed_count(self, tenant_id: str) -> int:
        """Quantos eventos já foram processados pelo Registry para este tenant."""
        with self._session_factory() as session:
            stmt = (
                select(NeuroRegistryProcessedEventModel)
                .where(NeuroRegistryProcessedEventModel.tenant_id == tenant_id)
            )
            return len(list(session.execute(stmt).scalars()))

    def get_phenotype(
        self, tenant_id: str, phenotype_id: str
    ) -> Optional[NeuroRegistryPhenotypeModel]:
        """Lookup phenotype por id (cross-tenant safe)."""
        with self._session_factory() as session:
            stmt = select(NeuroRegistryPhenotypeModel).where(
                NeuroRegistryPhenotypeModel.tenant_id == tenant_id,
                NeuroRegistryPhenotypeModel.id == phenotype_id,
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_diagnosis(
        self, tenant_id: str, diagnosis_id: str
    ) -> Optional[NeuroRegistryDiagnosisModel]:
        """Lookup diagnosis por id (cross-tenant safe)."""
        with self._session_factory() as session:
            stmt = select(NeuroRegistryDiagnosisModel).where(
                NeuroRegistryDiagnosisModel.tenant_id == tenant_id,
                NeuroRegistryDiagnosisModel.id == diagnosis_id,
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_intervention(
        self, tenant_id: str, intervention_id: str
    ) -> Optional[NeuroRegistryInterventionModel]:
        """Lookup intervention por id (cross-tenant safe)."""
        with self._session_factory() as session:
            stmt = select(NeuroRegistryInterventionModel).where(
                NeuroRegistryInterventionModel.tenant_id == tenant_id,
                NeuroRegistryInterventionModel.id == intervention_id,
            )
            return session.execute(stmt).scalar_one_or_none()

    def get_assessment(
        self, tenant_id: str, assessment_id: str
    ) -> Optional[NeuroRegistryAssessmentModel]:
        """Lookup assessment por id (cross-tenant safe)."""
        with self._session_factory() as session:
            stmt = select(NeuroRegistryAssessmentModel).where(
                NeuroRegistryAssessmentModel.tenant_id == tenant_id,
                NeuroRegistryAssessmentModel.id == assessment_id,
            )
            return session.execute(stmt).scalar_one_or_none()