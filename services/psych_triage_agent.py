"""Agente entrevistador da triagem psiquiátrica.

Fluxo controlado por software (determinístico); a IA apenas melhora o texto
das perguntas e da devolutiva. O agente conduz uma pergunta por vez, aceita
respostas livres e as normaliza para o contrato de `raw_responses` do
instrumento `PSYCH_TRIAGE`.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from araos.specialties.psychiatry import InstrumentConfig


@dataclass(frozen=True)
class Question:
    id: str
    prompt: str
    kind: str
    section: str
    data: Dict[str, Any] = field(default_factory=dict)
    choices: tuple = ()
    show_if: Optional[Dict[str, Any]] = None


@dataclass
class AgentResult:
    prompt: str
    question_id: Optional[str]
    done: bool
    progress: float


_SECTIONS: List[Dict[str, Any]] = [
    {"id": "depressao", "title": "humor e interesse", "temporal": "ultimos_30_dias", "change": True},
    {"id": "ansiedade", "title": "ansiedade", "temporal": "ultimos_30_dias", "change": True},
    {"id": "bipolaridade", "title": "períodos de energia e humor", "temporal": "episodico", "change": False},
    {"id": "psicose", "title": "experiências incomuns", "temporal": "hoje", "change": False},
    {"id": "tea", "title": "socialização e rotina desde a infância", "temporal": "passado_remoto", "change": False},
    {"id": "tdah", "title": "atenção e organização desde a infância", "temporal": "passado_remoto", "change": False},
]

_BASELINE_FIELDS = [
    ("sociabilidade", "Como você é ao se relacionar com as pessoas, no seu estado habitual?"),
    ("comunicacao", "Como é a sua comunicação no dia a dia, quando está bem?"),
    ("rotina", "Como costuma ser a sua rotina?"),
    ("sono", "Como costuma ser o seu sono?"),
    ("energia", "Como costuma estar a sua energia?"),
    ("concentracao", "Como costuma ser a sua concentração?"),
]


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c)
    ).lower()


class PsychTriageAgent:
    def __init__(self, cfg: InstrumentConfig) -> None:
        self._cfg = cfg
        self._questions: List[Question] = self._build_script()

    @property
    def config(self) -> InstrumentConfig:
        return self._cfg

    @property
    def questions(self) -> List[Question]:
        return self._questions

    def _build_script(self) -> List[Question]:
        questions: List[Question] = []
        questions.append(
            Question(
                "gate_infancia",
                "Pensando na sua infância e adolescência: você já tinha dificuldades de socialização, "
                "interesses muito intensos ou necessidade de rotina desde aquela época?",
                "yesno",
                "desenvolvimento",
                {"kind": "development", "field": "childhood_onset"},
            )
        )
        for key, prompt in _BASELINE_FIELDS:
            questions.append(
                Question(
                    f"base_{key}", prompt, "intensity", "funcionamento_habitual",
                    {"kind": "baseline", "field": key},
                )
            )
        questions.append(
            Question(
                "gate_episodios",
                "Já houve períodos, com vários dias de duração, em que você ficou claramente diferente "
                "do seu funcionamento habitual (energia, humor ou atividade)?",
                "yesno",
                "bipolaridade",
                {"kind": "episodes_gate"},
            )
        )
        questions.append(
            Question(
                "sleep_change",
                "Nesses períodos, você dormia menos porque não conseguia dormir (com cansaço), ou porque "
                "sentia que não precisava dormir? (A = insônia com cansaço / B = precisava menos de sono / "
                "C = não sei)",
                "choice",
                "bipolaridade",
                {"kind": "sleep_change"},
                choices=("A", "B", "C"),
                show_if={"field": "gate_episodios", "equals": "sim"},
            )
        )
        questions.append(
            Question(
                "reality_impairment",
                "Sobre experiências incomuns: você reconhece a possibilidade de que possam não "
                "corresponder à realidade? (preservado / parcial / ausente)",
                "choice",
                "psicose",
                {"kind": "psychosis_reality"},
                choices=("preservado", "parcial", "ausente"),
            )
        )

        for section in _SECTIONS:
            domain = section["id"]
            if section["change"]:
                questions.append(
                    Question(
                        f"change_{domain}",
                        f"Considerando as próximas respostas sobre {section['title']}, isso representa "
                        "mudança em relação ao seu funcionamento habitual? (nao / discretamente / "
                        "moderadamente / claramente / drasticamente)",
                        "choice",
                        section["id"],
                        {"kind": "section_change"},
                        choices=("nao", "discretamente", "moderadamente", "claramente", "drasticamente"),
                    )
                )
            for item in self._cfg.items:
                if item.domains[0] != domain:
                    continue
                show_if = None
                if "reducao_necessidade_sono" in item.requires_context:
                    show_if = {"field": "sleep_change", "equals": "B"}
                elif "inicio_infancia" in item.requires_context:
                    show_if = {"field": "gate_infancia", "equals": "sim"}
                elif "psicose_alteracao_realidade" in item.requires_context:
                    show_if = {"field": "reality_impairment", "not_in": ["preservado"]}
                questions.append(
                    Question(
                        f"item_{item.id}",
                        f"De 0 a 4 (0 = ausente, 4 = muito intenso), quanto você tem notado: {item.label}?",
                        "intensity",
                        section["id"],
                        {"kind": "item", "item_id": item.id},
                        show_if=show_if,
                    )
                )

        questions.append(
            Question(
                "psychosis_temporal_relation",
                "Essas experiências incomuns aparecem somente durante períodos de alteração importante "
                "do humor? (nunca / somente_depressao / somente_mania / ambos / nao_sabe)",
                "choice",
                "psicose",
                {"kind": "psychosis_temporal"},
                choices=("nunca", "somente_depressao", "somente_mania", "ambos", "nao_sabe"),
            )
        )

        for item in self._cfg.suicide.get("items", []):
            questions.append(
                Question(
                    f"sui_{item['id']}",
                    f"Com sinceridade, para cuidarmos da sua segurança: {item['label']}? (sim/não)",
                    "yesno",
                    "risco_suicida",
                    {"kind": "suicide", "item_id": item["id"]},
                )
            )
        questions.append(
            Question(
                "sui_capacidade_seguranca",
                "Você consegue se comprometer com um plano de segurança e pedir ajuda hoje, se precisar? "
                "(sim/não)",
                "yesno",
                "risco_suicida",
                {"kind": "suicide", "item_id": "capacidade_seguranca"},
            )
        )
        return questions

    def greeting(self) -> str:
        return (
            "Olá! Eu vou te acompanhar nesta triagem com calma e sem pressa. "
            "Não existem respostas certas ou erradas — responda do seu jeito. "
            "Isso nos ajuda a entender o que você está sentindo. Vamos começar?"
        )

    def _visible(self, question: Question, answers: Dict[str, Any]) -> bool:
        condition = question.show_if
        if not condition:
            return True
        value = answers.get(condition["field"])
        if condition.get("equals") is not None and value != condition["equals"]:
            return False
        if condition.get("not_in") and value in condition["not_in"]:
            return False
        return True

    def next_question(self, answers: Dict[str, Any]) -> Optional[Question]:
        for question in self._questions:
            if not self._visible(question, answers):
                continue
            if question.id not in answers:
                return question
        return None

    def progress(self, answers: Dict[str, Any]) -> float:
        total = sum(1 for q in self._questions if self._visible(q, answers))
        if total == 0:
            return 1.0
        return round(len(answers) / total, 3)

    def normalize(self, question: Question, raw: str) -> Optional[Any]:
        text = _strip_accents(raw or "").strip()
        if question.kind == "yesno":
            positive = text in ("sim", "s", "true", "1", "afirmativo", "isso", "ja", "quero", "tenho")
            negative = text in ("nao", "n", "false", "0", "nunca", "negativo", "nenhum")
            if question.data.get("invert"):
                if positive:
                    return False
                if negative:
                    return True
                return None
            if positive:
                return "sim"
            if negative:
                return "nao"
            return None
        if question.kind == "intensity":
            digit = re.search(r"[0-4]", text)
            if digit:
                return int(digit.group())
            for word, value in (("ausente", 0), ("leve", 1), ("moderado", 2), ("intenso", 3), ("muito intenso", 4)):
                if word in text:
                    return value
            return None
        if question.kind == "choice":
            for choice in question.choices:
                if _strip_accents(choice) == text or _strip_accents(choice) in text:
                    return choice
            return None
        return raw.strip()

    def build_raw(self, answers: Dict[str, Any]) -> Dict[str, Any]:  # noqa: C901
        raw: Dict[str, Any] = {
            "items": {},
            "baseline": {},
            "episodes": [],
            "development": {},
            "psychosis": {},
            "substances": [],
            "suicide": {},
        }
        section_temporal = {s["id"]: s["temporal"] for s in _SECTIONS}
        section_change = {s["id"]: "moderadamente" for s in _SECTIONS if s["change"]}
        for section in _SECTIONS:
            if not section["change"]:
                section_change[section["id"]] = "nao"

        for question in self._questions:
            if question.id not in answers:
                continue
            value = answers[question.id]
            data = question.data
            kind = data.get("kind")
            if kind == "item":
                section = question.section
                raw["items"][data["item_id"]] = {
                    "intensity": int(value),
                    "temporal": section_temporal.get(section, "ultimos_30_dias"),
                    "change": section_change.get(section, "moderadamente"),
                }
            elif kind == "section_change":
                section_change[question.section] = value
                for item_id, entry in raw["items"].items():
                    item = self._cfg.item_by_id(item_id)
                    if item and item.domains[0] == question.section:
                        entry["change"] = value
            elif kind == "development":
                raw["development"]["childhood_onset"] = bool(value)
            elif kind == "baseline":
                raw["baseline"][data["field"]] = value
            elif kind == "psychosis_reality":
                raw["psychosis"]["reality_impairment"] = value
            elif kind == "psychosis_temporal":
                raw["psychosis"]["temporal_relation"] = value
            elif kind == "sleep_change":
                pass
            elif kind == "suicide":
                is_true = value is True or value == "sim"
                raw["suicide"][data["item_id"]] = is_true

        if answers.get("gate_episodios") == "sim":
            episode: Dict[str, Any] = {"duration_days": 5, "observed_by_others": True}
            if answers.get("sleep_change"):
                episode["sleep_change"] = answers["sleep_change"]
            raw["episodes"].append(episode)
        return raw

    def ask(self, answers: Dict[str, Any], llm_polish: Optional[Callable[[str], str]] = None) -> AgentResult:
        question = self.next_question(answers)
        if question is None:
            return AgentResult(prompt="Triagem concluída.", question_id=None, done=True, progress=1.0)
        prompt = question.prompt
        if llm_polish is not None:
            prompt = llm_polish(prompt)
        return AgentResult(prompt=prompt, question_id=question.id, done=False, progress=self.progress(answers))


def build_agent(cfg: InstrumentConfig) -> PsychTriageAgent:
    return PsychTriageAgent(cfg)
