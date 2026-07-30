"""
6 Regras Built-in do Rule Engine (Sprint 4.2 / ADR-0003).

Cada regra mapeia padrões de eventos do catalog (Sprint 3.1) em
sugestões de ClinicalContext. Pure functions, sem I/O.

Regras:
    1. MedicationStartRule        — MEDICATION_STARTED → MedicationContext
    2. SchoolTransitionRule       — SCHOOL_CHANGED → SchoolContext
    3. FamilyEngagementRule       — FAMILY_MEETING → FamilyContext
    4. CrisisEpisodeRule          — CRISIS_RECORDED|HOSPITALIZATION|SURGERY → ClinicalEpisode
    5. BehavioralCrisisRule       — 2+ OUTCOME_WORSENING em 14d → ClinicalEpisode (behavioral)
    6. SleepPatternRule           — 3+ SLEEP_CHANGED em 30d → SleepPattern
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from araos.clinical.context.domain.clinical_context import ClinicalContext
from araos.clinical.context.domain.context_type import ContextType
from araos.clinical.context.domain.rule import ContextSuggestion, Rule
from araos.clinical.timeline.domain.window import TimeWindow


def _new_suggestion_id() -> str:
    return f"sug_{uuid.uuid4().hex[:16]}"


def _parse_dt(v: Any) -> Optional[datetime]:
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    if isinstance(v, str):
        s = v.rstrip("Z") + ("+00:00" if v.endswith("Z") else "")
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
    return None


# ─── Rule 1: MedicationStartRule ─────────────────────────────────────


class MedicationStartRule(Rule):
    rule_id = "medication_start"
    description = "Sugere MedicationContext quando nova medicação é iniciada."
    min_confidence = 0.85

    def evaluate(
        self,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> List[ContextSuggestion]:
        suggestions: List[ContextSuggestion] = []
        for ev in events:
            if ev.get("event_type") != "MEDICATION_STARTED":
                continue
            payload = ev.get("payload") or {}
            med_name = payload.get("medication_name") or payload.get("name") or "medicação"
            ev_dt = _parse_dt(ev.get("event_datetime"))
            if not ev_dt:
                continue
            # Dedup: se já existe MedicationContext com este aggregate_id
            ev_id = ev.get("event_id") or ev.get("id")
            if any(
                c.context_type == ContextType.MEDICATION_CONTEXT
                and ev_id in c.source_event_ids
                for c in existing_contexts
            ):
                continue

            suggestions.append(ContextSuggestion(
                suggestion_id=_new_suggestion_id(),
                context_type=ContextType.MEDICATION_CONTEXT,
                title=f"Início de {med_name}",
                description=f"Paciente iniciou {med_name}. Contexto de medicação sugerido.",
                reason=f"Evento MEDICATION_STARTED para {med_name}",
                confidence=0.95,
                rule_id=self.rule_id,
                contributing_event_ids=[ev_id],
                suggested_window=TimeWindow(
                    start=ev_dt,
                    end=ev_dt + timedelta(days=180),
                    label="medication_period_default",
                ),
                supporting_data={
                    "medication_name": med_name,
                    "dose": payload.get("dose"),
                    "frequency": payload.get("frequency"),
                },
                assumptions=[
                    "Medicação tipicamente tem período de uso ≥ 30 dias",
                    "Sem evidência de descontinuação no momento da sugestão",
                ],
                limitations=[
                    "Não sabemos se a medicação será mantida ou descontinuada",
                    "Período de 180d é default — pode ser ajustado após confirmação",
                ],
            ))
        return suggestions


# ─── Rule 2: SchoolTransitionRule ────────────────────────────────────


class SchoolTransitionRule(Rule):
    rule_id = "school_change"
    description = "Sugere SchoolContext quando paciente muda de escola."
    min_confidence = 0.85

    def evaluate(
        self,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> List[ContextSuggestion]:
        suggestions: List[ContextSuggestion] = []
        for ev in events:
            if ev.get("event_type") != "SCHOOL_CHANGED":
                continue
            payload = ev.get("payload") or {}
            ev_dt = _parse_dt(ev.get("event_datetime"))
            if not ev_dt:
                continue
            ev_id = ev.get("event_id") or ev.get("id")
            if any(
                c.context_type == ContextType.SCHOOL_CONTEXT
                and ev_id in c.source_event_ids
                for c in existing_contexts
            ):
                continue

            old = payload.get("from_school") or payload.get("previous_school")
            new = payload.get("to_school") or payload.get("new_school") or "nova escola"
            title = f"Mudança escolar para {new}"
            desc = f"Paciente mudou de {old or 'escola anterior'} para {new}."
            suggestions.append(ContextSuggestion(
                suggestion_id=_new_suggestion_id(),
                context_type=ContextType.SCHOOL_CONTEXT,
                title=title,
                description=desc,
                reason="Mudança de escola é preditor de desajuste comportamental/adaptativo",
                confidence=0.90,
                rule_id=self.rule_id,
                contributing_event_ids=[ev_id],
                suggested_window=TimeWindow(
                    start=ev_dt,
                    end=ev_dt + timedelta(days=90),
                    label="school_adaptation",
                ),
                supporting_data={
                    "from_school": old,
                    "to_school": new,
                },
                assumptions=[
                    "Adaptação escolar tipicamente leva até 90 dias",
                ],
                limitations=[
                    "Mudança pode ser rotineira (sem impacto clínico)",
                    "Período de 90d é heurístico — duração real varia",
                ],
            ))
        return suggestions


# ─── Rule 3: FamilyEngagementRule ────────────────────────────────────


class FamilyEngagementRule(Rule):
    rule_id = "family_meeting"
    description = "Sugere FamilyContext quando reunião familiar é registrada."
    min_confidence = 0.80

    def evaluate(
        self,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> List[ContextSuggestion]:
        suggestions: List[ContextSuggestion] = []
        for ev in events:
            if ev.get("event_type") != "FAMILY_MEETING":
                continue
            payload = ev.get("payload") or {}
            ev_dt = _parse_dt(ev.get("event_datetime"))
            if not ev_dt:
                continue
            ev_id = ev.get("event_id") or ev.get("id")
            if any(
                c.context_type == ContextType.FAMILY_CONTEXT
                and ev_id in c.source_event_ids
                for c in existing_contexts
            ):
                continue

            topic = payload.get("topic") or "engajamento familiar"
            suggestions.append(ContextSuggestion(
                suggestion_id=_new_suggestion_id(),
                context_type=ContextType.FAMILY_CONTEXT,
                title=f"Reunião familiar — {topic}",
                description=f"Reunião familiar registrada com tema: {topic}.",
                reason="Engajamento familiar é contexto relevante para evolução clínica.",
                confidence=0.85,
                rule_id=self.rule_id,
                contributing_event_ids=[ev_id],
                suggested_window=TimeWindow(
                    start=ev_dt,
                    end=ev_dt + timedelta(days=30),
                    label="family_engagement_period",
                ),
                supporting_data={"topic": topic},
                assumptions=[
                    "Reuniões familiares sinalizam contexto familiar ativo",
                ],
                limitations=[
                    "Reunião única não indica padrão — múltiplas reuniões confirmam contexto",
                    "Não sabemos se há conflito familiar ou alinhamento",
                ],
            ))
        return suggestions


# ─── Rule 4: CrisisEpisodeRule ───────────────────────────────────────


CRISIS_EVENTS = {"CRISIS_RECORDED", "HOSPITALIZATION", "SURGERY"}


class CrisisEpisodeRule(Rule):
    rule_id = "crisis_event"
    description = "Sugere ClinicalEpisode para CRISIS_RECORDED/HOSPITALIZATION/SURGERY."
    min_confidence = 0.90

    def evaluate(
        self,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> List[ContextSuggestion]:
        suggestions: List[ContextSuggestion] = []
        for ev in events:
            et = ev.get("event_type")
            if et not in CRISIS_EVENTS:
                continue
            payload = ev.get("payload") or {}
            ev_dt = _parse_dt(ev.get("event_datetime"))
            if not ev_dt:
                continue
            ev_id = ev.get("event_id") or ev.get("id")
            if any(
                c.context_type == ContextType.CLINICAL_EPISODE
                and ev_id in c.source_event_ids
                for c in existing_contexts
            ):
                continue

            subtype_map = {
                "CRISIS_RECORDED": "behavioral_crisis",
                "HOSPITALIZATION": "hospitalization",
                "SURGERY": "surgical",
            }
            subtype = subtype_map[et]
            title_map = {
                "CRISIS_RECORDED": "Crise clínica registrada",
                "HOSPITALIZATION": "Hospitalização",
                "SURGERY": "Cirurgia realizada",
            }

            suggestions.append(ContextSuggestion(
                suggestion_id=_new_suggestion_id(),
                context_type=ContextType.CLINICAL_EPISODE,
                title=title_map[et],
                description=f"Evento clínico crítico: {et}.",
                reason=f"Evento {et} dispara abertura automática de episódio clínico.",
                confidence=0.95,
                rule_id=self.rule_id,
                contributing_event_ids=[ev_id],
                suggested_window=TimeWindow(
                    start=ev_dt,
                    end=ev_dt + timedelta(days=14),
                    label=f"{subtype}_period",
                ),
                supporting_data={"subtype": subtype, "payload": payload},
                assumptions=[
                    "Evento clínico crítico sempre gera contexto de episódio",
                ],
                limitations=[
                    "Janela de 14d é heurística — duração real pode variar",
                    "Não classificamos gravidade — requer revisão humana",
                ],
            ))
        return suggestions


# ─── Rule 5: BehavioralCrisisRule ────────────────────────────────────


class BehavioralCrisisRule(Rule):
    rule_id = "behavioral_crisis"
    description = (
        "Sugere ClinicalEpisode (subtipo behavioral) quando 2+ OUTCOME_WORSENING "
        "ocorrem em janela de 14 dias."
    )
    min_confidence = 0.70

    def evaluate(
        self,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> List[ContextSuggestion]:
        window_days = 14
        min_count = 2
        worsening: List[Dict[str, Any]] = []
        for ev in events:
            if ev.get("event_type") != "OUTCOME_WORSENING":
                continue
            ev_dt = _parse_dt(ev.get("event_datetime"))
            if not ev_dt:
                continue
            worsening.append({"event": ev, "dt": ev_dt})
        worsening.sort(key=lambda x: x["dt"])
        if len(worsening) < min_count:
            return []

        # Detecta clusters em janela
        suggestions: List[ContextSuggestion] = []
        used_ids: set = set()
        i = 0
        while i < len(worsening):
            cluster = [worsening[i]]
            j = i + 1
            while j < len(worsening) and (worsening[j]["dt"] - cluster[0]["dt"]).days <= window_days:
                cluster.append(worsening[j])
                j += 1
            if len(cluster) >= min_count:
                cluster_ids = [c["event"].get("event_id") or c["event"].get("id") for c in cluster]
                if any(uid in cluster_ids for uid in used_ids):
                    pass  # já sugerido — segue
                # Dedup
                if any(
                    c.context_type == ContextType.CLINICAL_EPISODE
                    and any(eid in c.source_event_ids for eid in cluster_ids)
                    for c in existing_contexts
                ):
                    i = j
                    continue

                start_dt = cluster[0]["dt"]
                end_dt = cluster[-1]["dt"]
                confidence = min(0.85, 0.6 + 0.05 * len(cluster))
                suggestions.append(ContextSuggestion(
                    suggestion_id=_new_suggestion_id(),
                    context_type=ContextType.CLINICAL_EPISODE,
                    title=f"Possível crise comportamental ({len(cluster)} pioras em {window_days}d)",
                    description=(
                        f"Detectadas {len(cluster)} pioras de outcome em {window_days} dias. "
                        "Pode indicar crise comportamental."
                    ),
                    reason=f"{len(cluster)} eventos OUTCOME_WORSENING em janela de {window_days}d",
                    confidence=confidence,
                    rule_id=self.rule_id,
                    contributing_event_ids=cluster_ids,
                    suggested_window=TimeWindow(
                        start=start_dt,
                        end=end_dt + timedelta(days=7),
                        label="behavioral_crisis_cluster",
                    ),
                    supporting_data={
                        "cluster_size": len(cluster),
                        "window_days": window_days,
                    },
                    assumptions=[
                        "Múltiplas pioras em janela curta indicam padrão",
                        "OUTCOME_WORSENING é indicador confiável",
                    ],
                    limitations=[
                        "Pioras podem ter causas independentes (não correlacionadas)",
                        "Sem informação sobre gravidade — todos OUTCOME_WORSENING pesam igual",
                        f"Threshold de {min_count} eventos em {window_days}d é heurístico",
                    ],
                ))
                used_ids.update(cluster_ids)
            i = j
        return suggestions


# ─── Rule 6: SleepPatternRule ────────────────────────────────────────


class SleepPatternRule(Rule):
    rule_id = "sleep_pattern"
    description = (
        "Sugere SleepPattern quando 3+ eventos SLEEP_CHANGED em janela de 30 dias."
    )
    min_confidence = 0.65

    def evaluate(
        self,
        events: List[Dict[str, Any]],
        existing_contexts: List[ClinicalContext],
    ) -> List[ContextSuggestion]:
        window_days = 30
        min_count = 3
        sleep_events: List[Dict[str, Any]] = []
        for ev in events:
            if ev.get("event_type") != "SLEEP_CHANGED":
                continue
            ev_dt = _parse_dt(ev.get("event_datetime"))
            if not ev_dt:
                continue
            sleep_events.append({"event": ev, "dt": ev_dt})
        if len(sleep_events) < min_count:
            return []

        sleep_events.sort(key=lambda x: x["dt"])
        # Verifica cluster em janela
        first = sleep_events[0]["dt"]
        last = sleep_events[-1]["dt"]
        if (last - first).days > window_days:
            return []

        ids = [s["event"].get("event_id") or s["event"].get("id") for s in sleep_events]
        if any(
            c.context_type == ContextType.SLEEP_PATTERN
            and any(eid in c.source_event_ids for eid in ids)
            for c in existing_contexts
        ):
            return []

        confidence = min(0.85, 0.55 + 0.05 * len(sleep_events))
        return [ContextSuggestion(
            suggestion_id=_new_suggestion_id(),
            context_type=ContextType.SLEEP_PATTERN,
            title=f"Padrão de sono instável ({len(sleep_events)} mudanças em {window_days}d)",
            description=(
                f"Detectadas {len(sleep_events)} alterações de sono em {window_days} dias. "
                "Pode indicar padrão de sono disruptivo."
            ),
            reason=f"{len(sleep_events)} eventos SLEEP_CHANGED em {window_days}d",
            confidence=confidence,
            rule_id=self.rule_id,
            contributing_event_ids=ids,
            suggested_window=TimeWindow(
                start=first,
                end=last + timedelta(days=14),
                label="sleep_pattern_window",
            ),
            supporting_data={
                "n_changes": len(sleep_events),
                "window_days": window_days,
            },
            assumptions=[
                "Múltiplas mudanças de sono em janela curta indicam padrão",
            ],
            limitations=[
                "Sem informação sobre qualidade vs quantidade",
                "Não distingue causa médica vs comportamental",
                f"Threshold de {min_count} em {window_days}d é heurístico",
            ],
        )]


# ─── Aggregate registry ──────────────────────────────────────────────


DEFAULT_RULES: List[Rule] = [
    MedicationStartRule(),
    SchoolTransitionRule(),
    FamilyEngagementRule(),
    CrisisEpisodeRule(),
    BehavioralCrisisRule(),
    SleepPatternRule(),
]


def default_rules() -> List[Rule]:
    """Retorna lista das regras built-in (cópia rasa)."""
    return list(DEFAULT_RULES)
