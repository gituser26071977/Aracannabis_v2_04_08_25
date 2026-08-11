"""Replay histórico do SIAP → AraOS (F2, retrofit).

Alimenta o genome com histórico: lê anamneses e evoluções já existentes
no SIAP, extrai Expressões de genes (heurística) e emite Clinical Events
canônicos para o AraOS com `occurred_at` retroativo (data real do registro).

Princípios:
    - **Idempotente**: cada anamnese/evolução vira um evento com
      `source_id = <id do registro>`; o AraOS ignora/aggrega por evento.
    - **Never-throw**: falha de integração não interrompe o replay.
    - **Hipótese, não diagnóstico**: as Expressões derivadas são heurística
      explícita (Constituição art. 15) — a cadeia de evidências fica no
      label/evidence de cada gene.

Uso:
    from services.historical_replay import HistoricalReplayService
    replay = HistoricalReplayService(session)
    result = replay.run(tenant="vittalis", limit=100)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Tipos canônicos por fonte
_EVENT_TYPE_BY_MODEL = {
    "anamnese": "ANAMNESIS_RECORDED",
    "evolucao": "EVOLUTION_RECORDED",
}


@dataclass
class ReplayResult:
    total: int = 0
    emitted: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "emitted": self.emitted,
            "failed": self.failed,
            "errors": self.errors[:20],
        }


class HistoricalReplayService:
    """Replay idempotente de anamneses/evoluções do SIAP para o AraOS."""

    def __init__(self, session: Any, *, emitter: Any | None = None) -> None:
        self._session = session
        self._emitter = emitter

    def _get_emitter(self):
        if self._emitter is not None:
            return self._emitter
        from services.araos_event_emitter import default_emitter

        return default_emitter()

    def run(self, *, tenant: str | None = None, limit: int | None = None) -> ReplayResult:
        """Replaya anamneses + evoluções (mais antigas primeiro)."""
        from models import Anamnese, Evolucao, Paciente

        result = ReplayResult()

        anamneses = (
            self._session.query(Anamnese)
            .order_by(Anamnese.data_anamnese.asc())
            .all()
        )
        evolutions = (
            self._session.query(Evolucao)
            .order_by(Evolucao.data_evolucao.asc())
            .all()
        )

        records: list[tuple[str, Any, datetime, int | None]] = []
        for a in anamneses:
            records.append(("anamnese", a, a.data_anamnese, a.paciente_id))
        for e in evolutions:
            records.append(("evolucao", e, e.data_evolucao, e.paciente_id))

        if limit is not None:
            records = records[:limit]

        result.total = len(records)
        emitter = self._get_emitter()

        for model_type, record, occurred_at, paciente_id in records:
            try:
                paciente = self._session.get(Paciente, paciente_id) if paciente_id else None
                tenant_id = (
                    str(paciente.associacao_id)
                    if paciente is not None and paciente.associacao_id
                    else (tenant or "default")
                )
                payload = self._build_payload(model_type, record)
                if not payload:
                    continue
                ok = emitter.emit(
                    event_type=_EVENT_TYPE_BY_MODEL[model_type],
                    patient_id=paciente_id,
                    tenant_id=tenant_id,
                    source_id=record.id,
                    payload=payload,
                    metadata={"replay": True, "source_model": model_type},
                )
                if ok:
                    result.emitted += 1
                else:
                    result.failed += 1
            except Exception as exc:  # noqa: BLE001 — never-throw
                result.failed += 1
                result.errors.append(
                    f"{model_type}#{getattr(record, 'id', '?')}: {exc}"
                )
                logger.warning("replay_failed %s %s: %s", model_type, record.id, exc)

        return result

    def _build_payload(self, model_type: str, record: Any) -> dict[str, Any]:
        """Monta o payload canônico + gene_expressions derivadas do texto."""
        from services.historical_gene_extractor import extract_genes_from_text

        if model_type == "anamnese":
            text = _join_text(
                getattr(record, "condicao_principal", None),
                getattr(record, "sintomas_atuais", None),
                getattr(record, "medicamentos_uso", None),
            )
            payload: dict[str, Any] = {
                "anamnesis_id": record.id,
                "paciente_id": record.paciente_id,
                "condicao_principal": record.condicao_principal,
                "sintomas_atuais": record.sintomas_atuais,
                "medicamentos_uso": record.medicamentos_uso,
                "fonte": getattr(record, "fonte", "replay"),
            }
        else:  # evolucao
            text = getattr(record, "nota_evolucao", "") or ""
            payload = {
                "evolucao_id": record.id,
                "paciente_id": record.paciente_id,
                "nota_evolucao": text,
                "data_evolucao": (
                    record.data_evolucao.strftime("%Y-%m-%d")
                    if getattr(record, "data_evolucao", None)
                    else None
                ),
            }

        genes = extract_genes_from_text(text)
        payload["gene_expressions"] = [g.to_dict() for g in genes]
        return payload


def _join_text(*parts: str | None) -> str:
    """Junta campos de texto, ignorando vazios."""
    return " ".join(str(p) for p in parts if p)
