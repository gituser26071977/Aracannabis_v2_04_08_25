"""
AraOS Neurodevelopmental — Plugin Base para Escalas Neuropsicológicas.

Define os contratos imutáveis (dataclasses frozen) que toda escala
deve implementar para ser registrada no `ScaleRegistry`.

Princípios:
    - Plugin-based: cada escala é um arquivo independente.
    - Imutabilidade: `ScaleSpec` é frozen e registrado uma única vez.
    - Reprodutibilidade científica: cada spec traz referência bibliográfica
      ABNT + JSON Schema validável + funções puras de cálculo/interpretação.
    - Descoberta dinâmica: adicionar nova escala = criar 1 arquivo em
      `builtins/` (ou em pasta custom) e importar no `builtins/__init__.py`.
      Zero alteração do código central.

Exemplo de uso:

    from araos.specialties.neurodevelopmental.scales.base import ScaleSpec, ScaleSubscale
    from araos.specialties.neurodevelopmental.scales.registry import ScaleRegistry

    spec = ScaleSpec(
        code="GAD7",
        name="Generalized Anxiety Disorder 7-item",
        version="1.0",
        author="Spitzer et al. (2006)",
        scientific_reference="Spitzer RL, Kroenke K, Williams JBW, Löwe B. "
                             "A brief measure for assessing generalized anxiety disorder. "
                             "Arch Intern Med. 2006;166(10):1092-1097.",
        target_age_months=(168, None),  # ≥14 anos (168 meses)
        administration_time_min=3,
        json_schema={...},
        subscales=[ScaleSubscale(code="total", label="Escore Total", min=0, max=21)],
        score_function=_score_gad7,
        interpretation_function=_interpret_gad7,
    )
    ScaleRegistry.register(spec)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# Type aliases — uma resposta bruta de escala é um dict arbitrário validado
# pelo JSON Schema. Um escore computado é um dict {subscale_code: number}.
RawResponses = Dict[str, Any]
ComputedScores = Dict[str, float]


@dataclass(frozen=True)
class ScaleSubscale:
    """
    Subescala de uma escala neuropsicológica.

    Muitas escalas (Vineland, Conners, ATEC, SRS-2) têm subescalas
    (comunicação, socialização, motor, etc.). Outras (GAD-7, PHQ-9)
    têm um escore total único.
    """

    code: str
    label: str
    min: float
    max: float
    description: str = ""
    higher_is_worse: bool = True


@dataclass(frozen=True)
class ScaleInterpretation:
    """
    Interpretação padronizada de uma pontuação.
    """

    band: str  # "minimo", "leve", "moderado", "severo", "muito_severo"
    label_pt: str
    label_en: str = ""
    color: str = ""  # hex color para UI (ex: "#0d7377")
    recommendation: str = ""
    references: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScaleResult:
    """
    Resultado da aplicação de uma escala.

    `scores` mapeia `subscale_code -> score`.
    `interpretation` lista ordenada por subescala.
    `metadata` aceita campos extras (ex: idade do paciente, observador).
    """

    scale_code: str
    scale_version: str
    scores: ComputedScores
    interpretation: Dict[str, ScaleInterpretation]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para JSON."""
        return {
            "scale_code": self.scale_code,
            "scale_version": self.scale_version,
            "scores": self.scores,
            "interpretation": {
                code: {
                    "band": interp.band,
                    "label_pt": interp.label_pt,
                    "label_en": interp.label_en,
                    "color": interp.color,
                    "recommendation": interp.recommendation,
                    "references": interp.references,
                }
                for code, interp in self.interpretation.items()
            },
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ScaleSpec:
    """
    Especificação completa de uma escala neuropsicológica.

    Todos os campos são obrigatórios exceto `is_public` e `description`.
    `score_function` e `interpretation_function` devem ser funções **puras**
    (sem side-effects, sem I/O) para garantir reprodutibilidade e testabilidade.
    """

    code: str  # ex: "GAD7", "PHQ9", "MCHAT", "CARS"
    name: str
    version: str  # semver-like "1.0", "2.0-R"
    author: str
    scientific_reference: str  # citação ABNT ou DOI
    target_age_months: Tuple[Optional[int], Optional[int]]
    administration_time_min: int
    json_schema: Dict[str, Any]  # JSON Schema Draft 7
    subscales: List[ScaleSubscale]
    score_function: Callable[[RawResponses], ComputedScores]
    interpretation_function: Callable[[ComputedScores, RawResponses], Dict[str, ScaleInterpretation]]
    description: str = ""
    is_public: bool = True  # visível no catálogo público do tenant
    requires_training: bool = False  # exige profissional treinado
    languages: Tuple[str, ...] = ("pt-BR", "en-US")

    def __post_init__(self) -> None:
        """Valida invariantes estruturais do spec."""
        if not self.code or not self.code.strip():
            raise ValueError("ScaleSpec.code não pode ser vazio")
        if not self.code.replace("_", "").isalnum():
            raise ValueError(
                f"ScaleSpec.code deve ser alfanumérico (maiúsculas recomendado): {self.code!r}"
            )
        if not self.subscales:
            raise ValueError(f"ScaleSpec {self.code} deve ter ao menos uma subescala")
        if not isinstance(self.target_age_months, tuple) or len(self.target_age_months) != 2:
            raise ValueError(
                f"ScaleSpec.target_age_months deve ser (min, max) em meses: {self.target_age_months!r}"
            )
        if "type" not in self.json_schema:
            raise ValueError(
                f"ScaleSpec {self.code} precisa de json_schema com chave 'type'"
            )

    def is_applicable_for_age(self, age_months: Optional[int]) -> bool:
        """
        Verifica se a escala é aplicável para uma idade em meses.

        None = idade desconhecida → True (decisão do profissional).
        """
        if age_months is None:
            return True
        min_age, max_age = self.target_age_months
        if min_age is not None and age_months < min_age:
            return False
        if max_age is not None and age_months > max_age:
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serializa o spec para JSON (sem as callables)."""
        return {
            "code": self.code,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "scientific_reference": self.scientific_reference,
            "target_age_months": {
                "min": self.target_age_months[0],
                "max": self.target_age_months[1],
            },
            "administration_time_min": self.administration_time_min,
            "json_schema": self.json_schema,
            "subscales": [
                {
                    "code": ss.code,
                    "label": ss.label,
                    "min": ss.min,
                    "max": ss.max,
                    "description": ss.description,
                    "higher_is_worse": ss.higher_is_worse,
                }
                for ss in self.subscales
            ],
            "description": self.description,
            "is_public": self.is_public,
            "requires_training": self.requires_training,
            "languages": list(self.languages),
        }