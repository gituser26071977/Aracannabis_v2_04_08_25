"""Extrator heurístico de Clinical Genes a partir de texto clínico (F2 replay).

Converte anamnese/evolução histórica em Expressões de Clinical Genes
(0-10 + direção), para que o replay alimente o genome com histórico.

NÃO é IA — é uma heurística explícita e rastreável: para cada gene da CKO,
procura palavras-chave no texto e deriva um valor 0-10 com direção. O
resultado é uma **hipótese de interpretação**, nunca diagnóstico.

Cada gene carrega `evidence_text` (o trecho que sustentou a expressão) —
explicabilidade (Constituição art. 15).

Genes suportados (CKO v0.1): sono, energia, humor, ansiedade, estresse,
dor, saude, comunicacao_social, funcao_executiva, linguagem, aprendizagem.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Gene → {keyword: (valor 0-10, better_is_higher)}
# Valores seguem a mesma régua do gene_mapper do intake (7+ = bom, 4- = ruim).
_KEYWORD_MAP: dict[str, dict[str, tuple[float, bool]]] = {
    "sono": {
        "insônia": (2.0, True), "insonia": (2.0, True),
        "acordo cansado": (4.0, True), "dormindo mal": (3.0, True),
        "dorme bem": (8.0, True), "boa qualidade de sono": (8.0, True),
        "acorda à noite": (3.0, True), "acorda a noite": (3.0, True),
        "muito bom": (9.0, True),
    },
    "energia": {
        "cansaço": (3.0, True), "cansaco": (3.0, True), "fadiga": (2.0, True),
        "sem energia": (2.0, True), "baixa energia": (2.0, True),
        "disposição": (7.0, True), "disposicao": (7.0, True),
        "energia boa": (7.0, True), "bem disposto": (8.0, True),
    },
    "humor": {
        "irritabilidade": (3.0, True), "irritado": (3.0, True),
        "tristeza": (2.0, True), "triste": (2.0, True),
        "humor deprimido": (2.0, True), "bom humor": (8.0, True),
        "eutímico": (8.0, True), "eutimico": (8.0, True),
    },
    "ansiedade": {
        "ansiedade": (3.0, False), "ansioso": (3.0, False),
        "crise de ansiedade": (2.0, False), "preocupação": (4.0, False),
        "preocupacao": (4.0, False), "calmo": (8.0, False),
        "sem ansiedade": (8.0, False),
    },
    "estresse": {
        "estresse": (3.0, False), "estressado": (3.0, False),
        "tenso": (3.0, False), "stress": (3.0, False),
        "tranquilo": (8.0, False),
    },
    "dor": {
        # Escala dor: valor alto = mais dor (lower_is_better). Ausência = 1.0.
        "sem dor": (1.0, False), "assintomático": (1.0, False),
        "assintomatico": (1.0, False),
        "dor leve": (3.0, False),
        "dor intensa": (8.0, False), "dores": (6.0, False), "dor": (6.0, False),
    },
    "saude": {
        "melhora": (7.0, True), "melhorando": (7.0, True),
        "boa evolução": (8.0, True), "boa evolucao": (8.0, True),
        "piora": (3.0, True), "piorando": (3.0, True),
        "estável": (6.0, True), "estavel": (6.0, True), "sem queixas": (8.0, True),
    },
    "comunicacao_social": {
        "comunicação social": (6.0, True), "comunicacao social": (6.0, True),
        "interação social": (6.0, True), "interacao social": (6.0, True),
    },
    "funcao_executiva": {
        "função executiva": (6.0, True), "funcao executiva": (6.0, True),
        "atenção": (6.0, True), "atencao": (6.0, True),
    },
    "linguagem": {
        "linguagem": (6.0, True), "fala": (6.0, True),
        "vocabulário": (6.0, True), "vocabulario": (6.0, True),
    },
    "aprendizagem": {
        "aprendizagem": (6.0, True), "aprendendo": (6.0, True),
        "escola": (6.0, True),
    },
}


@dataclass(frozen=True)
class ExtractedGene:
    gene: str
    value: float
    label: str
    direction: str
    evidence_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gene": self.gene,
            "value": self.value,
            "label": self.label,
            "direction": self.direction,
        }


def _direction(value: float, *, better_is_higher: bool) -> str:
    """Mesma régua do intake: 7+ = bom, 4- = ruim (segundo a semântica)."""
    if value >= 7.0:
        return "better" if better_is_higher else "worse"
    if value <= 4.0:
        return "worse" if better_is_higher else "better"
    return "neutral"


def extract_genes_from_text(text: str) -> tuple[ExtractedGene, ...]:
    """Deriva Expressões de genes a partir de um texto clínico.

    Para cada gene, procura a primeira palavra-chave presente no texto
    (lowercase, sem acentos para robustez) e deriva o valor + direção.
    """
    if not text:
        return ()
    normalized = _normalize(text)
    found: list[ExtractedGene] = []
    for gene, keywords in _KEYWORD_MAP.items():
        for keyword, (value, better_is_higher) in keywords.items():
            if _normalize(keyword) in normalized:
                found.append(
                    ExtractedGene(
                        gene=gene,
                        value=value,
                        label=keyword.title(),
                        direction=_direction(value, better_is_higher=better_is_higher),
                        evidence_text=keyword,
                    )
                )
                break  # um gene = uma expressão (primeira keyword que casa)
    return tuple(found)


def _normalize(text: str) -> str:
    """Lowercase e remove acentos (busca robusta de keywords)."""
    text = text.lower()
    # remove acentos
    text = (
        text.replace("ã", "a").replace("á", "a").replace("â", "a").replace("à", "a")
        .replace("é", "e").replace("ê", "e").replace("í", "i")
        .replace("ó", "o").replace("ô", "o").replace("õ", "o")
        .replace("ú", "u").replace("ç", "c")
    )
    return re.sub(r"\s+", " ", text)
